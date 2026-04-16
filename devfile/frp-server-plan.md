# frp 服务端部署计划

## 概述

**目标**：在公网服务器上部署 frp 服务端，为 OpenCode Web 提供外网访问能力。

**服务器信息**：
- 公网 IP：`64.188.27.227`
- 操作系统：Linux（需确认具体发行版）

**架构**：
```
外网用户 → 64.188.27.227:39500 → frps → frpc(客户端) → localhost:4096
```

**端口规划**（范围 39000-40000）：

| 用途 | 首选端口 | Fallback 范围 |
|------|----------|---------------|
| frp 通信端口 | 39700 | 39701-39710 |
| Dashboard 端口 | 39800 | 39801-39810 |
| 外网访问端口 | 39500 | 39501-39510 |

**认证信息**：

| 系统 | 用途 | 用户名 | 密码 |
|------|------|--------|------|
| frp Dashboard | 管理 frp 代理状态 | `opencode` | `1234` |
| frp Token | 客户端连接认证 | - | `OpencodeFRP2026SecureToken!@#` |

---

## Task 1: 环境检查

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

4. 检查已占用端口
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

## Task 2: 端口可用性检测与选择

**目标**：检测端口可用性，选择可用端口

**步骤**：

1. 创建工作目录
   ```bash
   mkdir -p /opt/frp
   ```

2. 创建端口检测脚本
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

3. 运行端口检测
   ```bash
   bash /opt/frp/check_ports.sh
   ```

4. 保存检测结果到文件
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

## Task 3: 下载 frp

**目标**：下载并安装 frp 服务端

**步骤**：

1. 进入工作目录
   ```bash
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

## Task 4: 配置 frps

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

## Task 5: 创建日志文件

**步骤**：
```bash
touch /var/log/frps.log
chmod 644 /var/log/frps.log
```

---

## Task 6: 配置防火墙

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

## Task 7: 创建 systemd 服务

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

## Task 8: 验证服务运行

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

5. 测试 Dashboard
   ```bash
   curl -v http://127.0.0.1:${DASHBOARD_PORT}
   ```

**成功标准**：
- frps 进程正在运行
- 端口 ${FRP_PORT}、${DASHBOARD_PORT} 正在监听
- 日志无错误信息

---

## Task 9: 外网连通性测试

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

**成功标准**：
- 外网可以访问 ${PROXY_PORT} 端口（连接被拒绝或返回错误是正常的，等待客户端连接）

---

## Task 10: 输出端口信息给客户端

**目标**：生成客户端需要的配置信息

**步骤**：

1. 显示端口信息文件内容
   ```bash
   cat /opt/frp/port_info.json
   ```

2. 输出最终配置信息
   ```bash
   source /opt/frp/selected_ports.conf
   
   echo ""
   echo "=========================================="
   echo "服务端配置完成！"
   echo "=========================================="
   echo ""
   echo "请将以下 JSON 信息发送给客户端："
   echo ""
   cat /opt/frp/port_info.json
   echo ""
   echo "=========================================="
   echo "客户端需要的信息："
   echo "  - FRP_PORT: ${FRP_PORT}"
   echo "  - PROXY_PORT: ${PROXY_PORT}"
   echo "  - DASHBOARD_PORT: ${DASHBOARD_PORT}"
   echo "  - 外网访问地址: http://64.188.27.227:${PROXY_PORT}"
   echo "=========================================="
   ```

**成功标准**：
- 端口信息已输出
- 客户端可以使用这些信息进行配置

---

## 故障排查

### 问题 1：端口被占用

```bash
# 检查端口占用
netstat -tlnp | grep -E ':(39[0-9]{3})'

# 如果端口被占用，重新运行端口检测
bash /opt/frp/check_ports.sh

# 更新配置后重启服务
systemctl restart frps
```

### 问题 2：frps 无法启动

```bash
# 检查配置语法
/opt/frp/frps verify -c /opt/frp/frps.toml

# 检查端口占用
source /opt/frp/selected_ports.conf
netstat -tlnp | grep -E ":(${FRP_PORT}|${DASHBOARD_PORT}|${PROXY_PORT})"

# 查看详细日志
journalctl -u frps -f
```

### 问题 3：外网无法访问

1. 检查防火墙
   ```bash
   ufw status
   # 或
   firewall-cmd --list-all
   ```

2. 检查云服务商安全组
   - 确认安全组规则允许入站流量到相应端口

---

## 执行顺序

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9 → Task 10
```

**完成后**：将 Task 10 输出的 JSON 信息发送给客户端。
