from agent.base_agent import Base_Agent
from utils.prompt_config import *
from typing import List, Dict, Any
from utils.config import *
from tools.base_tool import reflect_tool, reflect_handlers
from core.cache import cache
from core.session import Session


class Memory:
    """短期记忆，存储反思轨迹"""
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        self.records.append({"type": record_type, "content": content})
        print(f"记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self):
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- 上一轮尝试 (代码) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self):
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None


class ReflectionAgent:
    def __init__(self, tools=None, handlers=None):
        self.base_agent = Base_Agent(
            tools=tools or [],
            handlers=handlers or {}
        )
        self.max_iterations = 2
        self.memory = Memory()
        self.cache = cache
        self.session = Session()

    def run(self, 
            task: str,
            user_id: str = "default",
            session_id: str = None,
            system_prompt: str = "") -> str:

        initial_system_prompt = initial_prompt.format(task=task)

        cached = self.cache.get(task, user_id=user_id,system_prompt=system_prompt)
        if cached:
            print(f"命中缓存，直接返回最终答案")
            return cached

        if system_prompt:
            system_prompt = f"{system_prompt}\n\n{initial_system_prompt}"
        else:
            system_prompt = initial_system_prompt

        # 初始执行
        print("--- 初始尝试 ---")
        initial_answer = self.base_agent.run_with_tools(
            query=task,
            user_id=user_id,
            system_prompt=system_prompt
        )
        self.memory.add_record("execution", initial_answer)
        print(initial_answer)

        # 迭代优化
        for i in range(self.max_iterations):
            print(f"--- 第 {i + 1}/{self.max_iterations} 轮迭代 ---")

            # 反思
            print("-> 正在反思...")
            last_answer = self.memory.get_last_execution()
            reflect_system_prompt = reflect_prompt.format(task=task, answer=last_answer)
            feedback = self.base_agent.run_with_tools(
                query=task,
                user_id=user_id,
                system_prompt=reflect_system_prompt
            )
            self.memory.add_record("reflection", feedback)
            print(feedback)

            if "无需改进" in feedback:
                print("\n反思认为回答已无需改进，任务完成。")
                break

            # 优化
            print("\n-> 正在优化...")
            refine_system_prompt = refine_prompt.format(
                task=task,
                last_answer=last_answer,
                feedback=feedback
            )
            refined_answer = self.base_agent.run_with_tools(
                query=task,
                user_id=user_id,
                system_prompt=refine_system_prompt
            )
            self.memory.add_record("execution", refined_answer)
            print(refined_answer)

        final_answer = self.memory.get_last_execution()
        if final_answer:
            self.cache.set(task, final_answer, user_id=user_id)

        if session_id and final_answer:
            history = self.session.load_session(user_id, session_id)
            history.append({"role": "user", "content": task})
            history.append({"role": "assistant", "content": final_answer})
            self.session.save_session(user_id, session_id, history)

        print(f"\n--- 任务完成 ---\n最终答案:\n{final_answer}")
        return final_answer


# 全局实例
reflection_agent = ReflectionAgent(tools=reflect_tool, handlers=reflect_handlers)