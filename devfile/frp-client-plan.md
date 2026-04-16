# frp 客户端部署计划

## 概述

**目标**：在本地 Windows 电脑上部署 frp 客户端，将 OpenCode Web 暴露到公网。

**架构**：
```
外网用户 → 64.188.27.227:PROXY_PORT → frps(服务端) → frpc(本地) → localhost:4096
```

**前置条件**：
- 服务端已完成部署并输出了端口信息
- 本地 OpenCode Web 可以正常运行

**认证信息**：

| 系统 | 用途 | 用户名 | 密码 |
|------|------|--------|------|
| OpenCode Web | 用户登录 OpenCode | `opencode` | `1234` |
| frp Dashboard | 管理 frp 代理状态 | `opencode` | `1234` |
| frp Token | 连接服务端认证 | - | `OpencodeFRP2026SecureToken!@#` |

---

## Task 1: 获取服务端端口信息

**目标**：从服务端获取实际使用的端口

**重要**：此任务需要等待服务端完成部署后才能执行。

**步骤**：

服务端会输出类似以下的 JSON 信息：
```json
{
  "server_ip": "64.188.27.227",
  "frp_port": 39700,
  "dashboard_port": 39800,
  "proxy_port": 39500,
  "access_url": "http://64.188.27.227:39500",
  "dashboard_url": "http://64.188.27.227:39800"
}
```

**设置变量**（根据服务端实际输出填写）：

```powershell
# 请根据服务端输出修改这些值
$FRP_PORT = "39700"        # frp 通信端口（从服务端获取）
$PROXY_PORT = "39500"      # 外网访问端口（从服务端获取）
$DASHBOARD_PORT = "39800"  # Dashboard 端口（从服务端获取）
```

**成功标准**：
- 已获取服务端实际使用的端口
- 变量已正确设置

---

## Task 2: 环境检查

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

**成功标准**：
- 系统为 64 位 Windows

---

## Task 3: 下载 frp 客户端

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
   Invoke-WebRequest -Uri $url -OutFile $output
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

## Task 4: 配置 frpc

**目标**：根据服务端端口创建 frp 客户端配置文件

**步骤**：

1. 确认端口变量已设置（来自 Task 1）
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
   # 如果变量未设置，使用默认值（请根据服务端实际输出修改）
   if (-not $FRP_PORT) { $FRP_PORT = "39700" }
   if (-not $PROXY_PORT) { $PROXY_PORT = "39500" }
   if (-not $DASHBOARD_PORT) { $DASHBOARD_PORT = "39800" }
   
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

## Task 5: 启动 OpenCode Web

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
   ```

5. 测试本地访问
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:4096" -UseBasicParsing -TimeoutSec 5
   ```

**成功标准**：
- OpenCode Web 在端口 4096 运行
- 本地可以访问 http://localhost:4096

---

## Task 6: 启动 frpc 客户端

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

## Task 7: 验证外网访问

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

## Task 8: 配置 Windows 服务（可选但推荐）

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

## 验证与测试

### 测试外网访问

1. 读取端口信息
   ```powershell
   $portInfo = Get-Content "C:\Tools\frp\port_info.json" | ConvertFrom-Json
   ```

2. 从本地测试
   ```powershell
   Invoke-WebRequest -Uri "http://64.188.27.227:$($portInfo.proxy_port)" -UseBasicParsing
   ```

3. 从第三方网络测试（如手机 4G 网络）
   - 用手机浏览器访问外网地址

### 查看 Dashboard

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

---

## 故障排查

### 问题 1：frpc 无法连接服务器

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

### 问题 2：OpenCode Web 无法启动

```powershell
# 检查端口占用
netstat -ano | findstr :4096

# 如果端口被占用，使用其他端口
opencode web --port 4097
```

### 问题 3：外网无法访问

1. 检查 frpc 是否运行
   ```powershell
   Get-Process frpc -ErrorAction SilentlyContinue
   ```

2. 检查 frpc 日志
   ```powershell
   Get-Content "C:\Tools\frp\frpc.log" -Tail 50
   ```

3. 验证端口信息一致性
   ```powershell
   Get-Content "C:\Tools\frp\port_info.json"
   ```

### 问题 4：OpenCode Web 认证问题

```powershell
# 当前配置的认证
$env:OPENCODE_SERVER_USERNAME = "opencode"
$env:OPENCODE_SERVER_PASSWORD = "1234"

# 如果需要取消认证（不推荐，外网暴露有安全风险）
$env:OPENCODE_SERVER_PASSWORD = $null
$env:OPENCODE_SERVER_USERNAME = $null
```

---

## 访问信息汇总

**外网访问地址**：`http://64.188.27.227:PROXY_PORT`（具体端口从服务端获取）

**登录凭证**：

| 系统 | 用户名 | 密码 |
|------|--------|------|
| OpenCode Web | `opencode` | `1234` |
| frp Dashboard | `opencode` | `1234` |

---

## 执行顺序

```
Task 1（获取服务端端口）→ Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8（可选）
```

**关键依赖**：
- Task 1 必须等待服务端完成部署
- 所有端口信息必须与服务端输出一致

---

## 完成后

配置完成后，OpenCode Web 应该可以通过外网地址访问：

1. 浏览器打开 `http://64.188.27.227:PROXY_PORT`
2. 输入用户名 `opencode` 和密码 `1234`
3. 开始使用 OpenCode Web
