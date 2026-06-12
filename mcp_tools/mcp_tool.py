# tools/mcp_tools/mcp_tool.py
import asyncio
import os
import time
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


class MCPClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _ensure_connected(self):
        if not self._initialized:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._connect())
            self._initialized = True

    async def _connect(self):
        env = os.environ.copy()
        env["PATH"] = "C:\\可以删除的\\" + ";" + env.get("PATH", "")

        server_params = StdioServerParameters(
            command=r"C:\可以删除的\npx.cmd",
            args=["@playwright/mcp", "--browser", "msedge"],
            env=env
        )

        self._stdio_context = stdio_client(server_params)
        self._read, self._write = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(self._read, self._write)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()
        print("✅ MCP 浏览器已连接")

    def _call(self, tool_name: str, args: dict = None):
        self._ensure_connected()
        return self._loop.run_until_complete(
            self._session.call_tool(tool_name, args or {})
        )

    def navigate(self, url: str) -> str:
        return str(self._call("browser_navigate", {"url": url}))

    def wait_for_selector(self, selector: str, timeout: int = 10000) -> str:
        """等待元素出现"""
        return str(self._call("browser_wait_for", {"selector": selector, "timeout": timeout}))

    def click(self, target: str) -> str:
        return str(self._call("browser_click", {"target": target}))

    def type(self, target: str, text: str) -> str:
        return str(self._call("browser_type", {"target": target, "text": text}))

    def snapshot(self) -> str:
        return str(self._call("browser_snapshot", {}))

    def screenshot(self, filename: str = "screenshot.png") -> str:
        import os
        output_dir = r"C:\Users\zoujie\Desktop\1\pythonProject2\mcp_tools\mcp_result"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        return str(self._call("browser_take_screenshot", {"filename":full_path}))

    def wait_for(self, text: str = None, time: float = None) -> str:
        args = {}
        if text:
            args["text"] = text
        if time:
            args["time"] = time
        return str(self._call("browser_wait_for", args))

    def evaluate(self, function: str) -> str:
        return str(self._call("browser_evaluate", {"function": function}))


# 全局单例
_client = None


def get_client():
    global _client
    if _client is None:
        _client = MCPClient()
    return _client


def browser_navigate(url: str) -> str:
    return get_client().navigate(url)


def browser_type(target: str, text: str) -> str:
    return get_client().type(target, text)


def browser_click(target: str) -> str:
    return get_client().click(target)


def browser_snapshot() -> str:
    return get_client().snapshot()


def browser_screenshot(filename: str = "screenshot.png") -> str:
    return get_client().screenshot(filename)


def browser_wait_for(text: str = None, time: float = None) -> str:
    return get_client().wait_for(text, time)


def browser_evaluate(function: str) -> str:
    return get_client().evaluate(function)


# 新增：等待元素
def browser_wait_for_selector(selector: str, timeout: int = 10000) -> str:
    return get_client().wait_for_selector(selector, timeout)


# ========== 工具定义（OpenAI Function Calling 格式 - 精简版）==========
BROWSER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "打开网页",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "要打开的网址"}},
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "点击页面元素",
            "parameters": {
                "type": "object",
                "properties": {"target": {"type": "string", "description": "CSS选择器，如 #id 或 .class"}},
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": "在输入框中输入文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "输入框的CSS选择器"},
                    "text": {"type": "string", "description": "要输入的文本"}
                },
                "required": ["target", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_snapshot",
            "description": "获取当前页面的结构快照，用于理解页面内容",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "截取当前页面截图",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string", "description": "截图保存文件名"}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_wait_for",
            "description": "等待文本出现或消失",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要等待的文本"},
                    "time": {"type": "number", "description": "等待秒数"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_evaluate",
            "description": "执行JavaScript代码",
            "parameters": {
                "type": "object",
                "properties": {"function": {"type": "string", "description": "JavaScript函数代码"}},
                "required": ["function"]
            }
        }
    }
]

BROWSER_HANDLERS = {
    "browser_navigate": browser_navigate,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_snapshot": browser_snapshot,
    "browser_screenshot": browser_screenshot,
    "browser_wait_for": browser_wait_for,
    "browser_evaluate": browser_evaluate,
}

# ========== 测试 ==========
if __name__ == "__main__":
    # 测试 httpbin 表单页面（无反爬）
    print("1. 打开测试表单页面...")
    url = "https://jwc.hbeu.edu.cn/"
    result=browser_navigate(url)
    print(f"   结果: {result[:200]}...")  # 打印部分结果

    # 2. 等待页面稳定加载
    import time

    time.sleep(3)

    # 3. 截图
    print("\n2. 正在截图...")
    screenshot_result = browser_screenshot("jwc_hbeu.png")
    print(f"   结果: {screenshot_result}")

    print("\n✅ 测试完成，请检查生成的 jwc_hbeu.png 截图文件。")
