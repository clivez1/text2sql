# frp 自建部署计划 - OpenCode Web 外网访问

## 概述

**目标**：通过 frp 将本地 OpenCode Web (localhost:4096) 暴露到公网服务器，实现外网访问。

**架构**：
```
外网用户 → 64.188.27.227:39500 → frps → frpc(本地) → localhost:4096
```

**环境信息**：
- 公网服务器 IP：`64.188.27.227`
- 本地 OpenCode Web 端口：`4096`
- 外网访问地址：`http://64.188.27.227:39500`（或 fallback 端口）

**端口规划**（范围 39000-40000）：

| 用途 | 首选端口 | Fallback 范围 |
|------|----------|---------------|
| frp 通信端口 | 39700 | 39701-39710 |
| Dashboard 端口 | 39800 | 39801-39810 |
| 外网访问端口 | 39500 | 39501-39510 |

**认证信息**：

| 系统 | 用途 | 用户名 | 密码 |
|------|------|--------|------|
| OpenCode Web | 用户登录 OpenCode | `opencode` | `1234` |
| frp Dashboard | 管理 frp 代理状态 | `opencode` | `1234` |

---

## 第一部分：服务端任务（公网服务器 64.188.27.227）

### Task 1.1: 环境检查

**执行者**：服务端 LLM Agent

**目标**：确认服务器环境状态

**步骤**：
1. 检查操作系统版本
   ```bash
   cat /etc/os-release
   uname -a
   ```

2. 检查系统架构
   ```bash
   arch
   # 或
   uname -m
   ```
   预期输出：`x86_64` 或 `amd64`

3. 检查防火墙状态
   ```bash
   # Ubuntu/Debian
   ufw status
   
   # CentOS/RHEL
   firewall-cmd --state
   systemctl status firewalld
   ```

4. 检查已占用端口（检查整个端口范围）
   ```bash
   netstat -tlnp | grep -E ':(39[0-9]{3}|40[0-9]{3})'
   # 或
   ss -tlnp | grep -E ':(39[0-9]{3}|40[0-9]{3})'
   ```

**成功标准**：
- 确认系统架构为 x86_64/amd64
- 记录防火墙类型（ufw/firewalld/iptables）
- 记录已占用的端口

---

### Task 1.2: 端口可用性检测与选择

**执行者**：服务端 LLM Agent

**目标**：检测端口可用性，选择可用端口

**步骤**：

1. 创建端口检测脚本
   ```bash
   cat > /opt/frp/check_ports.sh << 'EOF'
#!/bin/bash
# 端口检测脚本

check_port() {
    local port=$1
    if netstat -tlnp 2>/dev/null | grep -q ":${port} " || ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

find_available_port() {
    local start_port=$1
    local end_port=$2
    for port in $(seq $start_port $end_port); do
        if check_port $port; then
            echo $port
            return 0
        fi
    done
    return 1
}

# 查找可用端口
FRP_PORT=$(find_available_port 39700 39710)
DASHBOARD_PORT=$(find_available_port 39800 39810)
PROXY_PORT=$(find_available_port 39500 39510)

if [ -z "$FRP_PORT" ] || [ -z "$DASHBOARD_PORT" ] || [ -z "$PROXY_PORT" ]; then
    echo "ERROR: 无法找到足够的可用端口"
    exit 1
fi

echo "FRP_PORT=$FRP_PORT"
echo "DASHBOARD_PORT=$DASHBOARD_PORT"
echo "PROXY_PORT=$PROXY_PORT"
EOF

chmod +x /opt/frp/check_ports.sh
   ```

2. 运行端口检测
   ```bash
   mkdir -p /opt/frp
   bash /opt/frp/check_ports.sh
   ```

3. 保存检测结果到文件
   ```bash
   bash /opt/frp/check_ports.sh > /opt/frp/selected_ports.conf
   cat /opt/frp/selected_ports.conf
   ```

**预期输出示例**：
```
FRP_PORT=39700
DASHBOARD_PORT=39800
PROXY_PORT=39500
```

**成功标准**：
- 成功找到三个可用端口
- 端口信息已保存到 `/opt/frp/selected_ports.conf`

**Fallback 处理**：
- 如果首选端口被占用，脚本会自动选择下一个可用端口
- 如果整个范围都被占用，报错并要求人工干预

---

### Task 1.3: 下载 frp

**执行者**：服务端 LLM Agent

**目标**：下载并安装 frp 服务端

**步骤**：
1. 创建工作目录
   ```bash
   mkdir -p /opt/frp
   cd /opt/frp
   ```

2. 下载 frp（选择最新稳定版本）
   ```bash
   # 下载
   wget https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_linux_amd64.tar.gz
   
   # 如果 wget 不可用，使用 curl
   curl -LO https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_linux_amd64.tar.gz
   ```

3. 解压
   ```bash
   tar -xzf frp_0.61.1_linux_amd64.tar.gz
   mv frp_0.61.1_linux_amd64/* .
   rm -rf frp_0.61.1_linux_amd64 frp_0.61.1_linux_amd64.tar.gz
   ```

4. 验证文件
   ```bash
   ls -la /opt/frp/
   # 应看到: frps, frps.toml, frpc, frpc.toml
   ```

5. 添加执行权限
   ```bash
   chmod +x /opt/frp/frps
   ```

**成功标准**：
- `/opt/frp/frps` 文件存在且可执行
- `/opt/frp/frps.toml` 文件存在

---

### Task 1.4: 配置 frps（动态端口）

**执行者**：服务端 LLM Agent

**目标**：根据检测到的端口创建 frp 服务端配置文件

**步骤**：

1. 读取选定的端口
   ```bash
   source /opt/frp/selected_ports.conf
   echo "使用端口: FRP_PORT=$FRP_PORT, DASHBOARD_PORT=$DASHBOARD_PORT, PROXY_PORT=$PROXY_PORT"
   ```

2. 备份原配置
   ```bash
   cp /opt/frp/frps.toml /opt/frp/frps.toml.bak
   ```

3. 生成配置文件（使用变量替换）
   ```bash
   cat > /opt/frp/frps.toml << EOF
# frps.toml - 服务端配置
# 生成时间: 2026-04-16
# 端口选择: 自动检测可用端口

# 基础配置
bindPort = ${FRP_PORT}

# 认证配置
auth.method = "token"
auth.token = "OpencodeFRP2026SecureToken!@#"

# Dashboard 配置
webServer.addr = "0.0.0.0"
webServer.port = ${DASHBOARD_PORT}
webServer.user = "opencode"
webServer.password = "1234"

# 日志配置
log.to = "/var/log/frps.log"
log.level = "info"
log.maxDays = 7

# 性能优化
transport.maxPoolCount = 5
transport.tcpMux = true
transport.tcpMuxKeepaliveInterval = 60
EOF
   ```

4. 验证配置
   ```bash
   cat /opt/frp/frps.toml
   ```

5. 创建端口信息文件（供客户端使用）
   ```bash
   cat > /opt/frp/port_info.json << EOF
{
  "server_ip": "64.188.27.227",
  "frp_port": ${FRP_PORT},
  "dashboard_port": ${DASHBOARD_PORT},
  "proxy_port": ${PROXY_PORT},
  "access_url": "http://64.188.27.227:${PROXY_PORT}",
  "dashboard_url": "http://64.188.27.227:${DASHBOARD_PORT}"
}
EOF
   ```

**成功标准**：
- 配置文件创建成功
- 端口变量已正确替换
- `/opt/frp/port_info.json` 文件已创建

---

### Task 1.5: 创建日志文件

**执行者**：服务端 LLM Agent

**步骤**：
```bash
touch /var/log/frps.log
chmod 644 /var/log/frps.log
```

---

### Task 1.6: 配置防火墙

**执行者**：服务端 LLM Agent

**目标**：开放必要端口（使用动态检测的端口）

**步骤**：

1. 读取端口配置
   ```bash
   source /opt/frp/selected_ports.conf
   ```

2. 开放端口

**如果使用 ufw (Ubuntu/Debian)**：
```bash
# 开放端口
ufw allow ${FRP_PORT}/tcp comment 'frp communication'
ufw allow ${DASHBOARD_PORT}/tcp comment 'frp dashboard'
ufw allow ${PROXY_PORT}/tcp comment 'frp proxy'

# 重新加载
ufw reload

# 验证
ufw status
```

**如果使用 firewalld (CentOS/RHEL)**：
```bash
# 开放端口
firewall-cmd --permanent --add-port=${FRP_PORT}/tcp
firewall-cmd --permanent --add-port=${DASHBOARD_PORT}/tcp
firewall-cmd --permanent --add-port=${PROXY_PORT}/tcp

# 重新加载
firewall-cmd --reload

# 验证
firewall-cmd --list-ports
```

**如果使用 iptables**：
```bash
# 开放端口
iptables -I INPUT -p tcp --dport ${FRP_PORT} -j ACCEPT
iptables -I INPUT -p tcp --dport ${DASHBOARD_PORT} -j ACCEPT
iptables -I INPUT -p tcp --dport ${PROXY_PORT} -j ACCEPT

# 保存规则
# Ubuntu/Debian
iptables-save > /etc/iptables/rules.v4

# CentOS/RHEL
service iptables save
```

**成功标准**：
- 三个端口已开放
- 防火墙规则已保存

---

### Task 1.7: 创建 systemd 服务

**执行者**：服务端 LLM Agent

**目标**：将 frps 配置为系统服务，开机自启

**步骤**：

1. 创建服务文件
   ```bash
   cat > /etc/systemd/system/frps.service << 'EOF'
[Unit]
Description=frp server (fast reverse proxy)
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/opt/frp/frps -c /opt/frp/frps.toml
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
   ```

2. 重载 systemd
   ```bash
   systemctl daemon-reload
   ```

3. 启用开机自启
   ```bash
   systemctl enable frps
   ```

4. 启动服务
   ```bash
   systemctl start frps
   ```

5. 检查状态
   ```bash
   systemctl status frps
   ```

**成功标准**：
- 服务状态为 `active (running)`
- 服务已设置为开机自启

---

### Task 1.8: 验证服务运行

**执行者**：服务端 LLM Agent

**步骤**：

1. 读取端口配置
   ```bash
   source /opt/frp/selected_ports.conf
   ```

2. 检查进程
   ```bash
   ps aux | grep frps
   ```

3. 检查端口监听
   ```bash
   netstat -tlnp | grep frps
   # 或
   ss -tlnp | grep frps
   ```
   预期输出应包含端口 ${FRP_PORT} 和 ${DASHBOARD_PORT}

4. 检查日志
   ```bash
   tail -20 /var/log/frps.log
   ```

5. 测试本地连接
   ```bash
   curl -v http://127.0.0.1:${PROXY_PORT}
   ```
   预期：连接被拒绝或返回错误（正常，因为还没有客户端连接）

6. 测试 Dashboard
   ```bash
   curl -v http://127.0.0.1:${DASHBOARD_PORT}
   ```

**成功标准**：
- frps 进程正在运行
- 端口 ${FRP_PORT}、${DASHBOARD_PORT} 正在监听
- 日志无错误信息

---

### Task 1.9: 外网连通性测试

**执行者**：服务端 LLM Agent

**步骤**：

1. 读取端口配置
   ```bash
   source /opt/frp/selected_ports.conf
   ```

2. 从服务器测试外网访问
   ```bash
   curl -v http://64.188.27.227:${PROXY_PORT}
   ```

3. 检查云服务商安全组（如果适用）
   - 如果使用 AWS/阿里云/腾讯云等，需要在控制台安全组中开放端口
   - 检查安全组规则是否允许入站流量到 ${FRP_PORT}、${DASHBOARD_PORT}、${PROXY_PORT} 端口

4. 输出最终配置信息
   ```bash
   echo "=========================================="
   echo "服务端配置完成！"
   echo "=========================================="
   cat /opt/frp/port_info.json
   echo ""
   echo "请将以下信息提供给客户端："
   echo "  - FRP_PORT: ${FRP_PORT}"
   echo "  - PROXY_PORT: ${PROXY_PORT}"
   echo "  - 外网访问地址: http://64.188.27.227:${PROXY_PORT}"
   echo "=========================================="
   ```

**成功标准**：
- 外网可以访问 ${PROXY_PORT} 端口（连接被拒绝或返回错误是正常的，等待客户端连接）
- 端口信息已输出供客户端使用

---

### Task 1.10: 导出端口信息给客户端

**执行者**：服务端 LLM Agent

**目标**：生成客户端需要的配置信息

**步骤**：

1. 显示端口信息文件内容
   ```bash
   cat /opt/frp/port_info.json
   ```

2. 生成客户端配置模板
   ```bash
   source /opt/frp/selected_ports.conf
   
   cat << 'CLIENT_CONFIG'
# ============================================
# 客户端配置信息（请复制到客户端）
# ============================================
# 服务端 IP: 64.188.27.227
# FRP 通信端口: ${FRP_PORT}
# 外网访问端口: ${PROXY_PORT}
# Dashboard 端口: ${DASHBOARD_PORT}
# 
# 外网访问地址: http://64.188.27.227:${PROXY_PORT}
# Dashboard 地址: http://64.188.27.227:${DASHBOARD_PORT}
# ============================================
CLIENT_CONFIG
   ```

**成功标准**：
- 端口信息已输出
- 客户端可以使用这些信息进行配置

---

## 第二部分：客户端任务（本地 Windows 电脑）

### Task 2.1: 获取服务端端口信息

**执行者**：客户端 LLM Agent

**目标**：从服务端获取实际使用的端口

**步骤**：

**方式 1：手动输入（推荐）**

服务端完成 Task 1.10 后会输出端口信息，请记录：
- FRP_PORT: `_______`（frp 通信端口）
- PROXY_PORT: `_______`（外网访问端口）
- DASHBOARD_PORT: `_______`（Dashboard 端口）

**方式 2：从服务端获取配置文件**

如果可以访问服务端，下载端口信息：
```powershell
# 使用 SSH 或其他方式获取
# 文件路径: /opt/frp/port_info.json
```

**设置变量**（根据服务端实际输出填写）：
```powershell
# 请根据服务端输出修改这些值
$FRP_PORT = "39700"        # frp 通信端口
$PROXY_PORT = "39500"      # 外网访问端口
$DASHBOARD_PORT = "39800"  # Dashboard 端口
```

**成功标准**：
- 已获取服务端实际使用的端口
- 变量已正确设置

---

### Task 2.2: 环境检查

**执行者**：客户端 LLM Agent

**目标**：确认本地环境状态

**步骤**：

1. 检查系统架构
   ```powershell
   $env:PROCESSOR_ARCHITECTURE
   ```
   预期输出：`AMD64`

2. 检查 OpenCode Web 是否正常运行
   ```powershell
   # 检查端口 4096 是否被占用
   netstat -ano | findstr :4096
   ```

3. 测试本地 OpenCode Web
   ```powershell
   # 如果 OpenCode Web 正在运行
   Invoke-WebRequest -Uri "http://localhost:4096" -UseBasicParsing
   ```

**成功标准**：
- 系统为 64 位 Windows
- OpenCode Web 在端口 4096 运行正常

---

### Task 2.3: 下载 frp 客户端

**执行者**：客户端 LLM Agent

**目标**：下载 frp Windows 客户端

**步骤**：

1. 创建目录
   ```powershell
   New-Item -ItemType Directory -Force -Path "C:\Tools\frp"
   Set-Location "C:\Tools\frp"
   ```

2. 下载 frp
   ```powershell
   # 使用 Invoke-WebRequest
   $url = "https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_windows_amd64.zip"
   $output = "C:\Tools\frp\frp.zip"
   Invoke-WebRequest -Uri $url -OutFile $output
   ```

   如果 GitHub 下载慢，使用镜像：
   ```powershell
   # 镜像地址（如果需要）
   $url = "https://ghproxy.com/https://github.com/fatedier/frp/releases/download/v0.61.1/frp_0.61.1_windows_amd64.zip"
   ```

3. 解压
   ```powershell
   Expand-Archive -Path "C:\Tools\frp\frp.zip" -DestinationPath "C:\Tools\frp" -Force
   
   # 移动文件到根目录
   Move-Item -Path "C:\Tools\frp\frp_0.61.1_windows_amd64\*" -Destination "C:\Tools\frp\" -Force
   Remove-Item -Path "C:\Tools\frp\frp_0.61.1_windows_amd64" -Recurse -Force
   Remove-Item -Path "C:\Tools\frp\frp.zip" -Force
   ```

4. 验证文件
   ```powershell
   Get-ChildItem "C:\Tools\frp"
   ```
   预期输出：`frpc.exe`, `frpc.toml`, `frps.exe`, `frps.toml`

**成功标准**：
- `C:\Tools\frp\frpc.exe` 文件存在

---

### Task 2.4: 配置 frpc（动态端口）

**执行者**：客户端 LLM Agent

**目标**：根据服务端端口创建 frp 客户端配置文件

**步骤**：

1. 确认端口变量已设置（来自 Task 2.1）
   ```powershell
   Write-Host "FRP_PORT: $FRP_PORT"
   Write-Host "PROXY_PORT: $PROXY_PORT"
   Write-Host "DASHBOARD_PORT: $DASHBOARD_PORT"
   ```

2. 备份原配置
   ```powershell
   Copy-Item "C:\Tools\frp\frpc.toml" "C:\Tools\frp\frpc.toml.bak" -ErrorAction SilentlyContinue
   ```

3. 生成配置文件
   ```powershell
   # 如果变量未设置，使用默认值
   if (-not $FRP_PORT) { $FRP_PORT = "39700" }
   if (-not $PROXY_PORT) { $PROXY_PORT = "39500" }
   
   $config = @"
# frpc.toml - 客户端配置
# 生成时间: 2026-04-16

# 服务器配置
serverAddr = "64.188.27.227"
serverPort = $FRP_PORT

# 认证配置（必须与服务端一致）
auth.method = "token"
auth.token = "OpencodeFRP2026SecureToken!@#"

# OpenCode Web 代理配置
[[proxies]]
name = "opencode-web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 4096
remotePort = $PROXY_PORT

# 日志配置
log.to = "C:\\Tools\\frp\\frpc.log"
log.level = "info"
log.maxDays = 7
"@
   
   Set-Content -Path "C:\Tools\frp\frpc.toml" -Value $config -Encoding UTF8
   ```

4. 验证配置
   ```powershell
   Get-Content "C:\Tools\frp\frpc.toml"
   ```

5. 保存端口信息到本地文件
   ```powershell
   $portInfo = @{
       server_ip = "64.188.27.227"
       frp_port = $FRP_PORT
       proxy_port = $PROXY_PORT
       dashboard_port = $DASHBOARD_PORT
       access_url = "http://64.188.27.227:$PROXY_PORT"
       dashboard_url = "http://64.188.27.227:$DASHBOARD_PORT"
   }
   
   $portInfo | ConvertTo-Json | Set-Content -Path "C:\Tools\frp\port_info.json"
   ```

**成功标准**：
- 配置文件创建成功
- 端口变量已正确替换
- `C:\Tools\frp\port_info.json` 文件已创建

---

### Task 2.5: 启动 OpenCode Web

**执行者**：客户端 LLM Agent

**目标**：确保 OpenCode Web 正在运行

**步骤**：

1. 检查是否已运行
   ```powershell
   netstat -ano | findstr :4096
   ```

2. 如果未运行，启动 OpenCode Web
   ```powershell
   # 设置认证环境变量（用户登录凭证）
   $env:OPENCODE_SERVER_USERNAME = "opencode"
   $env:OPENCODE_SERVER_PASSWORD = "1234"
   
   # 启动 OpenCode Web（在新窗口）
   Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:OPENCODE_SERVER_USERNAME='opencode'; `$env:OPENCODE_SERVER_PASSWORD='1234'; opencode web --port 4096"
   ```

3. 等待启动（约 5 秒）
   ```powershell
   Start-Sleep -Seconds 5
   ```

4. 验证运行状态
   ```powershell
   netstat -ano | findstr :4096
   Invoke-WebRequest -Uri "http://localhost:4096" -UseBasicParsing -TimeoutSec 5
   ```

**成功标准**：
- OpenCode Web 在端口 4096 运行
- 本地可以访问 http://localhost:4096

---

### Task 2.6: 启动 frpc 客户端

**执行者**：客户端 LLM Agent

**目标**：启动 frp 客户端连接服务器

**步骤**：

1. 测试配置
   ```powershell
   & "C:\Tools\frp\frpc.exe" verify -c "C:\Tools\frp\frpc.toml"
   ```

2. 启动 frpc（前台测试）
   ```powershell
   & "C:\Tools\frp\frpc.exe" -c "C:\Tools\frp\frpc.toml"
   ```

   观察输出，预期看到类似：
   ```
   [I] [service.go:XXX] login to server success
   [I] [proxy_manager.go:XXX] [opencode-web] start proxy success
   ```

3. 如果成功，按 Ctrl+C 停止，然后以后台方式启动
   ```powershell
   Start-Process -FilePath "C:\Tools\frp\frpc.exe" -ArgumentList "-c", "C:\Tools\frp\frpc.toml" -WindowStyle Hidden
   ```

**成功标准**：
- frpc 成功连接到服务器
- 日志显示 "login to server success"
- 日志显示 "start proxy success"

---

### Task 2.7: 配置 Windows 服务（可选但推荐）

**执行者**：客户端 LLM Agent

**目标**：将 frpc 配置为 Windows 服务，开机自启

**步骤**：

1. 下载 NSSM（Non-Sucking Service Manager）
   ```powershell
   # 使用 winget 安装
   winget install NSSM.NSSM
   
   # 或手动下载
   # https://nssm.cc/download
   ```

2. 安装服务
   ```powershell
   # 确保 nssm 在 PATH 中
   $env:Path += ";C:\Program Files\nssm\win64"
   
   # 安装 frpc 服务
   nssm install frpc "C:\Tools\frp\frpc.exe" "-c" "C:\Tools\frp\frpc.toml"
   
   # 设置服务描述
   nssm set frpc Description "frp client for OpenCode Web"
   
   # 设置自动重启
   nssm set frpc AppExit Default Restart
   nssm set frpc AppRestartDelay 5000
   ```

3. 启动服务
   ```powershell
   nssm start frpc
   # 或
   net start frpc
   ```

4. 验证服务状态
   ```powershell
   Get-Service frpc
   ```

**成功标准**：
- frpc 服务状态为 Running
- 服务设置为 Automatic 启动类型

---

### Task 2.8: 验证外网访问

**执行者**：客户端 LLM Agent

**目标**：验证外网可以访问 OpenCode Web

**步骤**：

1. 读取端口信息
   ```powershell
   $portInfo = Get-Content "C:\Tools\frp\port_info.json" | ConvertFrom-Json
   $accessUrl = $portInfo.access_url
   Write-Host "外网访问地址: $accessUrl"
   ```

2. 检查 frpc 日志
   ```powershell
   Get-Content "C:\Tools\frp\frpc.log" -Tail 20
   ```

3. 从本地测试外网访问
   ```powershell
   Invoke-WebRequest -Uri $accessUrl -UseBasicParsing -TimeoutSec 10
   ```

4. 使用浏览器测试
   ```powershell
   Start-Process $accessUrl
   ```

**成功标准**：
- 可以通过外网地址访问 OpenCode Web
- 页面正常加载，无错误

---

## 第三部分：验证与测试

### Task 3.1: 端到端测试

**执行者**：任意一方 LLM Agent

**步骤**：

1. 读取端口信息
   ```bash
   # 服务端
   source /opt/frp/selected_ports.conf
   ```
   ```powershell
   # 客户端
   $portInfo = Get-Content "C:\Tools\frp\port_info.json" | ConvertFrom-Json
   ```

2. 从公网服务器测试
   ```bash
   curl -v http://64.188.27.227:${PROXY_PORT}
   ```

3. 从本地测试
   ```powershell
   Invoke-WebRequest -Uri "http://64.188.27.227:$($portInfo.proxy_port)" -UseBasicParsing
   ```

4. 从第三方网络测试（如手机 4G 网络）
   - 用手机浏览器访问外网地址

**成功标准**：
- 所有测试都能正常访问 OpenCode Web

---

### Task 3.2: 查看 Dashboard

**执行者**：任意一方 LLM Agent

**步骤**：

1. 读取端口信息
   ```powershell
   $portInfo = Get-Content "C:\Tools\frp\port_info.json" | ConvertFrom-Json
   $dashboardUrl = $portInfo.dashboard_url
   ```

2. 访问 Dashboard
   ```powershell
   Start-Process $dashboardUrl
   ```

3. 登录凭据：
   - 用户名：`opencode`
   - 密码：`1234`

4. 检查代理状态
   - 应该看到 `opencode-web` 代理状态为 online

**成功标准**：
- Dashboard 可以访问
- 代理状态显示 online

---

## 第四部分：故障排查指南

### 问题 1：端口被占用

**症状**：服务启动失败，日志显示端口绑定错误

**排查步骤**：

**服务端**：
```bash
# 检查端口占用
netstat -tlnp | grep -E ':(39[0-9]{3})'

# 如果端口被占用，重新运行端口检测
bash /opt/frp/check_ports.sh

# 更新配置
source /opt/frp/selected_ports.conf
# 重新生成配置文件（参考 Task 1.4）

# 重启服务
systemctl restart frps
```

**客户端**：
```powershell
# 检查本地端口
netstat -ano | findstr :4096

# 如果 OpenCode Web 端口被占用，修改端口
# 启动时指定其他端口
opencode web --port 4097
```

### 问题 2：frps 无法启动

**排查步骤**：
```bash
# 检查配置语法
/opt/frp/frps verify -c /opt/frp/frps.toml

# 检查端口占用
source /opt/frp/selected_ports.conf
netstat -tlnp | grep -E ":(${FRP_PORT}|${DASHBOARD_PORT}|${PROXY_PORT})"

# 查看详细日志
journalctl -u frps -f
```

### 问题 3：frpc 无法连接服务器

**排查步骤**：
```powershell
# 读取端口信息
$portInfo = Get-Content "C:\Tools\frp\port_info.json" | ConvertFrom-Json

# 测试网络连通性
Test-NetConnection -ComputerName 64.188.27.227 -Port $portInfo.frp_port

# 检查配置
& "C:\Tools\frp\frpc.exe" verify -c "C:\Tools\frp\frpc.toml"

# 查看日志
Get-Content "C:\Tools\frp\frpc.log" -Tail 50
```

### 问题 4：外网无法访问

**排查步骤**：

1. 检查服务器防火墙
   ```bash
   ufw status
   # 或
   firewall-cmd --list-all
   ```

2. 检查云服务商安全组
   - 确认安全组规则允许入站流量到相应端口

3. 检查 frp 代理状态
   - 访问 Dashboard 查看代理状态

4. 验证端口信息一致性
   ```bash
   # 服务端
   cat /opt/frp/port_info.json
   
   # 客户端
   Get-Content "C:\Tools\frp\port_info.json"
   ```

### 问题 5：OpenCode Web 认证问题

**解决方案**：
```powershell
# 当前配置的认证
$env:OPENCODE_SERVER_USERNAME = "opencode"
$env:OPENCODE_SERVER_PASSWORD = "1234"

# 如果需要取消认证（不推荐，外网暴露有安全风险）
$env:OPENCODE_SERVER_PASSWORD = $null
$env:OPENCODE_SERVER_USERNAME = $null
```

---

## 第五部分：端口信息同步机制

### 服务端输出格式

服务端完成配置后，应输出以下格式的信息供客户端使用：

```
==========================================
服务端配置完成！
==========================================
{
  "server_ip": "64.188.27.227",
  "frp_port": 39700,
  "dashboard_port": 39800,
  "proxy_port": 39500,
  "access_url": "http://64.188.27.227:39500",
  "dashboard_url": "http://64.188.27.227:39800"
}
==========================================
```

### 客户端输入格式

客户端应根据服务端输出，设置以下变量：

```powershell
$FRP_PORT = "39700"        # 从服务端获取
$PROXY_PORT = "39500"      # 从服务端获取
$DASHBOARD_PORT = "39800"  # 从服务端获取
```

---

## 附录：配置文件模板

### 服务端配置模板 (`/opt/frp/frps.toml`)

```toml
# frps.toml - 服务端配置
# 注意：实际部署时端口会被替换为检测到的可用端口

bindPort = ${FRP_PORT}

auth.method = "token"
auth.token = "OpencodeFRP2026SecureToken!@#"

webServer.addr = "0.0.0.0"
webServer.port = ${DASHBOARD_PORT}
webServer.user = "opencode"
webServer.password = "1234"

log.to = "/var/log/frps.log"
log.level = "info"
log.maxDays = 7

transport.maxPoolCount = 5
transport.tcpMux = true
transport.tcpMuxKeepaliveInterval = 60
```

### 客户端配置模板 (`C:\Tools\frp\frpc.toml`)

```toml
# frpc.toml - 客户端配置
# 注意：实际部署时端口会被替换为服务端使用的端口

serverAddr = "64.188.27.227"
serverPort = ${FRP_PORT}

auth.method = "token"
auth.token = "OpencodeFRP2026SecureToken!@#"

[[proxies]]
name = "opencode-web"
type = "tcp"
localIP = "127.0.0.1"
localPort = 4096
remotePort = ${PROXY_PORT}

log.to = "C:\\Tools\\frp\\frpc.log"
log.level = "info"
log.maxDays = 7
```

---

## 访问信息汇总（示例）

| 项目 | 地址 |
|------|------|
| OpenCode Web（外网） | http://64.188.27.227:39500 |
| OpenCode Web（本地） | http://localhost:4096 |
| frp Dashboard | http://64.188.27.227:39800 |

**登录凭证**：

| 系统 | 用户名 | 密码 |
|------|--------|------|
| OpenCode Web | `opencode` | `1234` |
| frp Dashboard | `opencode` | `1234` |

**frp 配置**：

| 项目 | 值 |
|------|-----|
| frp Token | `OpencodeFRP2026SecureToken!@#` |

> **注意**：实际端口以服务端检测到的可用端口为准

---

## 安全建议

1. **修改默认密码**：部署完成后立即修改 Dashboard 密码和 Token
2. **限制 Dashboard 访问**：建议只允许特定 IP 访问 Dashboard 端口
3. **启用 HTTPS**：生产环境建议配置 SSL 证书
4. **定期更新**：关注 frp 安全更新，及时升级
5. **监控日志**：定期检查日志文件

---

## 执行顺序

```
服务端: Task 1.1 → Task 1.2 → Task 1.3 → Task 1.4 → Task 1.5 → Task 1.6 → Task 1.7 → Task 1.8 → Task 1.9 → Task 1.10
                                    ↓
                          输出端口信息给客户端
                                    ↓
客户端: Task 2.1 → Task 2.2 → Task 2.3 → Task 2.4 → Task 2.5 → Task 2.6 → Task 2.7 → Task 2.8
                                    ↓
验证: Task 3.1 → Task 3.2
```

**关键依赖**：
- 客户端 Task 2.1 必须等待服务端 Task 1.10 完成
- 客户端需要从服务端获取实际使用的端口信息
