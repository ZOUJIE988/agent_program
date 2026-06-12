import json
from openai import OpenAI

from core.rate_limiter import rate_limiter
from utils.config import *
from core.cache import cache
from core.error_recovery import with_retry
from core.session import Session
from core.long_memory import long_memory
from core.sensitive_filter import sensitive_filter
from core.compress import estimate_tokens,apply_compression

class Base_Agent:
    def __init__(self,tools=None, handlers=None):
        self.client=OpenAI(
            api_key=open_api_key,
            base_url=openai_base_url,
        )
        self.model = model_name
        self.tool = tools or []
        self.handlers = handlers or {}
        self.cache = cache

        self.session=Session()
        self.current_session_id=None
        self.current_user_id = None
        self.conversation_history = []

        self.long_memory=long_memory

    @with_retry
    def answer(self,messages:list):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tool if self.tool else None,
            tool_choice="auto" if self.tool else None,
        )
        return response.choices[0].message

    def execute_tool(self,tool_call)->str:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        handler = self.handlers.get(tool_name)

        print(f"正在执行工具: {tool_name}")

        if handler:
            try:
                s=handler(**tool_args)
                print(f"结果:{s}")
                return s
            except Exception as e:
                return f"工具执行失败: {e}"
        else:
            return f"未知工具: {tool_name}"

    def run_with_tools(self, query: str,
                       system_prompt: str = None,
                       max_rounds: int =max_rounds,
                       session_id: str = None,
                       user_id: str = "default",
                       use_cache: bool = False,
                       use_session:bool = False,
                       use_long_memory: bool = False) -> str:

        # 频率限制（检查提问是否过于频繁）==========
        allowed, msg = rate_limiter.check_and_record(user_id)
        if not allowed:
            return msg

        # 检查用户输入是否包含敏感词
        if sensitive_filter.contains(query):
            # 如果包含敏感词，直接拒绝，不调用 LLM
            return "抱歉，您的输入包含敏感内容，无法处理。"

        #注入长期记忆
        if use_long_memory:
            memory_context = self.long_memory.get_context(user_id)
            if memory_context:
                system_prompt = f"{memory_context}\n\n{system_prompt}" if system_prompt else memory_context

        # 注入自定义提示（如果有）
        if system_prompt and not system_prompt.startswith("##"):
            # 如果没有标记，加上 ## 自定义
            system_prompt = f"## 自定义\n{system_prompt}"

        #会话处理
        if use_session:
            if session_id:
                if not self.current_session_id or self.current_session_id != session_id:
                    self.load_session(user_id, session_id)
            elif not self.current_session_id:
                self.new_session(user_id)

            # 压缩会话历史（在构建 prompt 之前）
        if use_session and self.conversation_history:
            # 先估算 token
            estimated_tokens = estimate_tokens(self.conversation_history)
            if estimated_tokens > TOKEN_THRESHOLD:
                print(f"会话历史 token 超标 ({estimated_tokens} > {TOKEN_THRESHOLD})，开始压缩...")
                self.conversation_history, compressed = apply_compression(
                    self.conversation_history,
                    self.client,
                    self.model
                )
                if compressed:
                    self.save_current_session()
                    print(f"会话历史已压缩并保存")
            else:
                print(f"会话历史 token 正常 ({estimated_tokens} <= {TOKEN_THRESHOLD})")

        # ========== 构建历史 prompt ==========
        if use_session and self.conversation_history:
            history_prompt = self._build_history_prompt()
            if history_prompt:
                system_prompt = f"{history_prompt}\n\n{system_prompt}" if system_prompt else history_prompt

        #检查缓存
        if use_cache:
            cached = self.cache.get(query, user_id=user_id,system_prompt=system_prompt or "")
            if cached:
                # print(f"命中缓存: {query[:50]}...")
                # print(f"命中缓存！")
                return cached

            else:
                pass
                # print(f"未命中缓存")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})
        for _ in range(max_rounds):
            message = self.answer(messages)
            if message is None:
                return "LLM 调用失败"
            messages.append(message.model_dump())

            # 没有工具调用 → 返回结果
            if not message.tool_calls:
                result= message.content or "无回复"

                #保存缓存
                if use_cache and result:
                    self.cache.set(query, result, user_id=user_id,system_prompt=system_prompt or "")
                    # print(f"已缓存: {query}")

                #保存会话
                if use_session and result:
                    self.conversation_history.append({"role": "user", "content": query})
                    self.conversation_history.append({"role": "assistant", "content": result})
                    self.save_current_session()

                #自动保存长期记忆
                if use_long_memory and result:
                    self.long_memory.extract_from_conversation(
                        user_id=user_id,
                        user_query=query,
                        ai_response=result,
                        llm_client=self
                    )
                return result

            # 有工具调用 → 执行工具
            for tool_call in message.tool_calls:
                result = self.execute_tool(tool_call)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        return "执行超时（超过最大工具调用轮数）"

    def new_session(self,user_id: str, session_id: str = None) -> str:
        """创建新会话"""
        import time
        if session_id is None:
            session_id = f"session_{int(time.time())}"

        self.current_user_id = user_id
        self.current_session_id = session_id
        self.conversation_history = []
        # print(f"新会话已创建: {session_id}")
        return session_id

    def save_current_session(self):
        """保存当前会话"""
        if self.current_session_id and self.conversation_history:
            self.session.save_session(
                self.current_user_id,
                self.current_session_id,
                self.conversation_history
            )
            # print(f"会话已保存: {self.current_session_id}")

    def list_sessions(self, user_id: str) -> list:
        """列出所有会话"""
        return self.session.list_sessions(user_id)

    def load_session(self, user_id: str, session_id: str) -> list:
        """加载已有会话"""
        self.current_user_id = user_id
        self.current_session_id = session_id
        self.conversation_history = self.session.load_session(user_id, session_id)
        print(f"已加载会话 {session_id}，共 {len(self.conversation_history)} 条历史")
        return self.conversation_history

    def _build_history_prompt(self) -> str:
        """构建历史对话的 prompt"""
        if not self.conversation_history:
            return ""

        history_text = "## 对话历史\n"
        for msg in self.conversation_history:
            role = "用户" if msg["role"] == "user" else "助手"
            history_text += f"{role}: {msg['content']}\n"

        return history_text

