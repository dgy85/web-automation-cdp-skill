#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Automation via Chrome DevTools Protocol (CDP)
通过 CDP 控制浏览器执行自动化任务
"""

import os
import sys
import json
import time
import argparse
import websocket
from urllib.parse import urljoin


class CDPClient:
    """Chrome DevTools Protocol 客户端"""

    def __init__(self, host="127.0.0.1", port=9222):
        self.host = host
        self.port = port
        self.ws = None
        self.target_id = None
        self.msg_id = 0

    def connect(self):
        """获取 CDP WebSocket URL 并连接"""
        import requests

        # 获取 targets
        resp = requests.get(f"http://{self.host}:{self.port}/json")
        targets = resp.json()

        if not targets:
            raise Exception("No targets found")

        # 使用第一个空白页
        for t in targets:
            if t.get("type") == "page":
                self.target_id = t["id"]
                ws_url = t["webSocketDebuggerUrl"]
                break

        if not self.target_id:
            self.target_id = targets[0]["id"]
            ws_url = targets[0]["webSocketDebuggerUrl"]

        print(f"🔗 连接目标: {self.target_id}")
        self.ws = websocket.create_connection(ws_url)
        return True

    def send(self, method, params=None):
        """发送 CDP 命令"""
        if params is None:
            params = {}

        self.msg_id += 1
        msg = json.dumps({"id": self.msg_id, "method": method, "params": params})

        self.ws.send(msg)

        # 接收响应
        while True:
            resp = self.ws.recv()
            data = json.loads(resp)
            if "id" in data and data["id"] == self.msg_id:
                if "result" in data:
                    return data["result"]
                elif "error" in data:
                    raise Exception(data["error"])
            elif "method" in data:
                # 忽略其他消息
                pass

    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()

    # ========== 浏览器操作 ==========

    def navigate(self, url):
        """导航到 URL"""
        result = self.send("Page.navigate", {"url": url})
        print(f"🌐 导航: {url}")
        # 等待页面加载完成
        try:
            self.send("Page.waitForLoadState", {"state": "networkidle"})
        except Exception:
            pass  # 如果不支持则忽略
        return result

    def reload(self):
        """刷新页面"""
        return self.send("Page.reload")

    def go_back(self):
        """后退"""
        return self.send("Page.goBack")

    def go_forward(self):
        """前进"""
        return self.send("Page.goForward")

    def get_url(self):
        """获取当前 URL"""
        result = self.send(
            "Runtime.evaluate",
            {"expression": "window.location.href", "returnByValue": True},
        )
        return result.get("result", {}).get("value", "")

    def get_title(self):
        """获取页面标题"""
        result = self.send(
            "Runtime.evaluate", {"expression": "document.title", "returnByValue": True}
        )
        return result.get("result", {}).get("value", "")

    def get_html(self):
        """获取页面 HTML"""
        result = self.send(
            "Runtime.evaluate",
            {"expression": "document.documentElement.outerHTML", "returnByValue": True},
        )
        return result.get("result", {}).get("value", "")

    def get_text(self):
        """获取页面文本"""
        result = self.send(
            "Runtime.evaluate",
            {"expression": "document.body.innerText", "returnByValue": True},
        )
        return result.get("result", {}).get("value", "")

    def snapshot(self, full=False):
        """获取页面快照"""
        # 获取 DOM
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": """
            (function() {
                function buildTree(node, depth) {
                    if (depth > 3) return null;
                    var result = {node: node.nodeType === 1 ? node.tagName.toLowerCase() : '#text'};
                    if (node.textContent && node.textContent.trim()) {
                        result.text = node.textContent.trim().substring(0, 100);
                    }
                    if (node.children) {
                        var children = [];
                        for (var i = 0; i < node.children.length; i++) {
                            var child = buildTree(node.children[i], depth + 1);
                            if (child) children.push(child);
                        }
                        if (children.length) result.children = children;
                    }
                    return result;
                }
                return buildTree(document.body, 0);
            })()
            """,
                "returnByValue": True,
                "format": "json",
            },
        )
        return result.get("result", {}).get("value", {})

    def screenshot(self, path="screenshot.png", full_page=False):
        """截图"""
        result = self.send(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": full_page},
        )

        import base64

        img_data = base64.b64decode(result["data"])
        with open(path, "wb") as f:
            f.write(img_data)

        print(f"📸 截图保存: {path}")
        return path

    def click(self, selector):
        """点击元素"""
        # 获取元素的边界矩形和点击坐标
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": f'''
            (function() {{
                const el = document.querySelector("{selector}");
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                }};
            }})()
            ''',
                "returnByValue": True,
            },
        )

        coords = result.get("result", {}).get("value")
        if not coords:
            raise Exception(f"元素未找到: {selector}")

        x, y = coords["x"], coords["y"]

        # 点击指定位置
        self.send(
            "Input.dispatchMouseEvent",
            {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
        )
        self.send(
            "Input.dispatchMouseEvent",
            {
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            },
        )

        print(f"🖱️ 点击: {selector} at ({x}, {y})")
        return True

    def type(self, selector, text, clear_first=True):
        """输入文本"""
        # 获取焦点
        self.send(
            "Runtime.evaluate",
            {"expression": f'document.querySelector("{selector}").focus()'},
        )

        if clear_first:
            self.send(
                "Input.dispatchKeyEvent",
                {
                    "type": "keyDown",
                    "key": "a",
                    "modifiers": 2,  # Control
                },
            )

        # 输入
        self.send("Input.insertText", {"text": text})
        print(f"⌨️ 输入: {text[:20]}...")
        return True

    def submit(self, selector):
        """提交表单"""
        self.send(
            "Runtime.evaluate",
            {"expression": f'document.querySelector("{selector}").submit()'},
        )
        return True

    def wait(self, seconds):
        """等待"""
        time.sleep(seconds)
        return True

    def wait_for_selector(self, selector, timeout=10):
        """等待元素出现"""
        start = time.time()
        while time.time() - start < timeout:
            result = self.send(
                "Runtime.evaluate",
                {
                    "expression": f'document.querySelector("{selector}") !== null',
                    "returnByValue": True,
                },
            )
            if result.get("result", {}).get("value"):
                return True
            time.sleep(0.5)
        raise Exception(f"等待元素超时: {selector}")

    def eval(self, js):
        """执行 JavaScript"""
        result = self.send(
            "Runtime.evaluate", {"expression": js, "returnByValue": True}
        )
        return result.get("result", {}).get("value")

    def cookies(self):
        """获取 cookies"""
        result = self.send("Network.getAllCookies")
        return result.get("cookies", [])

    def set_cookie(self, name, value, domain=None):
        """设置 cookie"""
        params = {"name": name, "value": value}
        if domain:
            params["domain"] = domain
        self.send("Network.setCookie", params)
        return True

    def console(self, level="log"):
        """获取 console 日志"""
        # 需要先启用
        self.send("Log.enable")
        return []

    def errors(self):
        """获取页面错误"""
        return []


def main():
    parser = argparse.ArgumentParser(description="Web Automation via CDP")
    parser.add_argument(
        "action", help="操作: navigate, snapshot, screenshot, click, type, etc."
    )
    parser.add_argument("params", nargs="*", help="参数")
    parser.add_argument("--host", default="127.0.0.1", help="CDP 主机")
    parser.add_argument("--port", type=int, default=9222, help="CDP 端口")

    args = parser.parse_args()

    client = CDPClient(args.host, args.port)
    client.connect()

    try:
        action = args.action
        params = args.params

        if action == "navigate":
            url = params[0] if params else "https://example.com"
            client.navigate(url)

        elif action == "snapshot":
            result = client.snapshot()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif action == "screenshot":
            path = params[0] if params else "screenshot.png"
            client.screenshot(path)

        elif action == "title":
            print(client.get_title())

        elif action == "html":
            print(client.get_html())

        elif action == "text":
            print(client.get_text())

        elif action == "url":
            print(client.get_url())

        elif action == "click":
            selector = params[0] if params else "body"
            client.click(selector)

        elif action == "type":
            selector = params[0] if params else "input"
            text = params[1] if len(params) > 1 else "test"
            client.type(selector, text)

        elif action == "wait":
            seconds = float(params[0]) if params else 1
            client.wait(seconds)

        elif action == "eval":
            js = " ".join(params) if params else "1+1"
            print(client.eval(js))

        elif action == "cookies":
            print(json.dumps(client.cookies(), indent=2))

        else:
            print(f"❌ 未知操作: {action}")
            print(
                "可用操作: navigate, snapshot, screenshot, title, html, text, url, click, type, wait, eval, cookies"
            )
            sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
