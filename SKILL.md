---
name: web-automation-cdp
description: 基于 Chrome 远程调试协议 (CDP) 的浏览器自动化工具。通过启动带调试端口的 Chrome 并连接 CDP，实现网页导航、截图、点击、输入等操作。适用于网站登录、数据抓取、表单填写、自动化测试等场景。特别注意：优先使用 DOM snapshot 解析而非 OCR；Ant Design 等 UI 框架在 headless 模式下可能有兼容性问题，遇到协议复选框无法勾选等问题时切换非 headless 模式。每步操作都要有意义，避免无效重复操作。
metadata:
  {
    "openclaw":
      {
        "emoji": "🌐",
        "requires": { "anyBins": ["python3", "python", "google-chrome", "chromium", "chromium-browser"] },
      },
  }
---

# Web Automation CDP

基于 Chrome DevTools Protocol (CDP) 的浏览器自动化工具。

## 概述

通过 Chrome 远程调试端口直接控制浏览器，执行各种自动化任务。无需 OpenClaw 内置 browser 工具，独立工作。

## 使用前提

1. 安装 Chrome/Chromium 浏览器
2. 安装 Python 依赖：`pip install websocket-client requests`
3. 确保调试端口可用

## 工具位置

- 启动 Chrome (Windows)：`scripts/start_chrome.bat`
- 启动 Chrome (Linux/Mac)：`sh sctipts/start_chrome.sh`
- CDP 客户端：`python scripts/cdp_client.py`

## 使用方法

### 步骤 1：启动 Chrome 调试模式

**Windows:**
```cmd
cd scripts/
start_chrome.bat
```

或指定端口：
```cmd
set DEBUG_PORT=9223 && start_chrome.bat
```

**Linux/Mac:**
```bash
cd scripts/
sh start_chrome.sh
```

或指定端口：
```bash
DEBUG_PORT=9223 sh scripts/start_chrome.sh
```

### 步骤 2：执行自动化操作

```bash
python3 scripts/cdp_client.py <操作> [参数]
```

## 支持的操作

| 操作 | 说明 | 示例 |
|------|------|------|
| navigate | 导航到 URL | `python3 scripts/cdp_client.py navigate https://example.com` |
| snapshot | 获取页面快照 | `python3 scripts/cdp_client.py snapshot` |
| screenshot | 截图 | `python3 scripts/cdp_client.py screenshot` |
| title | 获取标题 | `python3 scripts/cdp_client.py title` |
| html | 获取 HTML | `python3 scripts/cdp_client.py html` |
| text | 获取文本 | `python3 scripts/cdp_client.py text` |
| url | 获取当前 URL | `python3 scripts/cdp_client.py url` |
| click | 点击元素 | `python3 scripts/cdp_client.py click "#btn"` |
| type | 输入文本 | `python3 scripts/cdp_client.py type "input[name=q]" "搜索内容"` |
| wait | 等待秒数 | `python3 scripts/cdp_client.py wait 2` |
| eval | 执行 JS | `python3 scripts/cdp_client.py eval "document.title"` |
| cookies | 获取 cookies | `python3 scripts/cdp_client.py cookies` |

## 完整示例

**Windows:**
```cmd
REM 1. 启动 Chrome
cd scripts/
start_chrome.bat

REM 2. 导航并截图
python scripts/cdp_client.py navigate "https://example.com"
python scripts/cdp_client.py screenshot example.png

REM 3. 搜索示例
python scripts/cdp_client.py navigate "https://www.google.com"
python scripts/cdp_client.py type "textarea[name=q]" "OpenClaw"
python scripts/cdp_client.py click "input[name=btnK]"
python scripts/cdp_client.py wait 2
python scripts/cdp_client.py screenshot results.png

REM 4. 获取内容
python scripts/cdp_client.py title
python scripts/cdp_client.py text
python scripts/cdp_client.py url
```

**Linux/Mac:**
```bash
# 1. 启动 Chrome
cd scripts/
sh start_chrome.sh

# 2. 导航并截图
python3 scripts/cdp_client.py navigate "https://example.com"
python3 scripts/cdp_client.py screenshot example.png

# 3. 搜索示例
python3 scripts/cdp_client.py navigate "https://www.google.com"
python3 scripts/cdp_client.py type "textarea[name=q]" "OpenClaw"
python3 scripts/cdp_client.py click "input[name=btnK]"
python3 scripts/cdp_client.py wait 2
python3 scripts/cdp_client.py screenshot results.png

# 4. 获取内容
python3 scripts/cdp_client.py title
python3 scripts/cdp_client.py text
python3 scripts/cdp_client.py url
```

## 操作规范

### 1. DOM Snapshot 优先原则
- **所有操作通过 DOM snapshot 解析进行**，非必要情况下严禁使用 OCR
- 只有在 DOM 解析无法获取所需信息时才考虑 OCR
- 使用 `snapshot` 命令获取页面结构，通过 CSS 选择器定位元素

### 2. Headless 兼容性问题
- **Ant Design 等 UI 框架在 headless Chrome 环境下存在兼容性问题**
- 常见症状：协议复选框无法正常勾选、表单组件交互异常
- **解决方案**：遇到此类问题，切换到非 headless 模式手动操作

### 3. 操作效率要求
- **合并无效冗余操作**：每步操作都要合理、有效，不要做无头苍蝇
- 避免频繁尝试、频繁操作导致 token 使用量飙升
- 在执行操作前先分析页面结构，制定操作计划
- 每步操作前明确目的，避免盲目试错

### 常见问题模式

| 问题 | 解决方案 |
|------|----------|
| 登录场景下协议复选框无法勾选 | 切换非 headless 模式 |
| 表单组件交互异常 | 优先考虑 headless 模式兼容性问题，切换模式 |
| 操作频繁但无效 | 停止盲目尝试，分析页面结构后一次性执行 |
| WebSocket 连接失败 (403 Forbidden) | 添加 `--remote-allow-origins=*` 参数启动 Chrome |
| CDP 连接被拒绝 | 确保调试端口未被占用，先关闭已有 Chrome 进程 |

### 跨域问题解决方案

**问题描述**：
```
websocket._exceptions.WebSocketBadStatusException: Handshake status 403 Forbidden
Rejected an incoming WebSocket connection from the http://127.0.0.1:9222 origin.
```

**解决方案**：启动 Chrome 时添加 `--remote-allow-origins=*` 参数：
```cmd
start "" "chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%TEMP%\chrome-cdp-profile"
```

**或修改 start_chrome.bat**（推荐）：
```batch
start "" "%CHROME_PATH%" --remote-debugging-port=%DEBUG_PORT% --remote-allow-origins=* --user-data-dir="%USER_DATA_DIR%" --no-first-run --no-default-browser-check --disable-popup-blocking --disable-infobars --disable-dev-shm-usage --window-size=1280,720 --headless=new
```

## 注意事项

- Chrome 需要带 `--remote-debugging-port` 参数启动
- 调试端口默认 9222
- 多个标签页时需要指定 target
- 某些网站可能有反爬虫机制
- 登录态可以复用已有 Chrome 会话