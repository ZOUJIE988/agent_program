import ast
from utils.prompt_config import *
from utils.config import *
from agent.base_agent import Base_Agent
from tools.base_tool import plan_tool,plan_handlers,executor_tool,executor_handlers
from core.cache import cache
from core.session import Session

class PlanAgent:
    def __init__(self, tools=None, handlers=None):
        self.base_agent = Base_Agent(
            tools=tools or [],
            handlers=handlers or {}
        )

    def plan(self,query:str,system:str="",
            user_id: str = "default",
            session_id: str = None,):
        """将问题拆解成步骤列表"""

        system_prompt = PLANNER_PROMPT.format(question=query)
        final_system_prompt = f"{system}\n\n{system_prompt}" if system else system_prompt

        response = self.base_agent.run_with_tools(
            query=query,
            system_prompt=final_system_prompt,
            user_id=user_id,
            session_id=session_id
        )
        plan_str = response.split("```python")[1].split("```")[0].strip()
        plan = ast.literal_eval(plan_str)
        return plan

class ExecutorAgent:
    def __init__(self, tools=None, handlers=None):
        self.base_agent = Base_Agent(
            tools=tools or [],
            handlers=handlers or {}
        )


    def execute_step(self,
                     question:str,
                     plan:list,
                     step:str,
                     history:str,
                     system:str="",
                     user_id: str = "default",
                     session_id: str = None,
                     ):
        """执行单个步骤"""
        system_prompt=EXECUTOR_PROMPT.format(question=question,
                                             plan=plan,
                                             history=history,
                                             current_step=step)
        if system:
            final_system_prompt = f"{system}\n\n{system_prompt}"
        else:
            final_system_prompt = system_prompt

        result=self.base_agent.run_with_tools(
            query=step,
            system_prompt=final_system_prompt,
            user_id=user_id,
            max_rounds=5
        )
        return result

    def execute(self,question:str,
                plan:list,
                user_id: str = "default",
                session_id: str = None,
                system: str = ""):
        """执行整个计划"""
        print(f"\n开始执行计划，共 {len(plan)} 个步骤")
        history = ""
        final_answer = ""
        for i, step in enumerate(plan, 1):
            print(f"\n步骤 {i}/{len(plan)}: {step}")

            step_result=self.execute_step(
                question=question,
                plan=plan,
                step=step,
                history=history,
                system=system,
                user_id=user_id,
            )

            history += f"步骤{i}: {step}\n结果: {step_result}\n\n"
            final_answer = step_result

            print(f"结果: {step_result[:100]}...")

        return final_answer

class PlanAndSolveAgent:
    def __init__(self, plan_tools=None, plan_handlers=None,
                 executor_tools=None, executor_handlers=None):

        self.planner = PlanAgent(tools=plan_tools, handlers=plan_handlers)
        self.executor = ExecutorAgent(tools=executor_tools, handlers=executor_handlers)

        self.cache = cache
        self.session = Session()

    def run(self,question:str,
            user_id: str = "default",
            session_id: str = None,
            system_prompt: str = ""):

        # ========== 检查最终答案缓存 ==========
        cached = self.cache.get(question, user_id=user_id,system_prompt=system_prompt)
        if cached:
            print(f"命中缓存")
            return cached


        print("\n正在规划...")
        plan=self.planner.plan(query=question,system=system_prompt,
                               user_id=user_id,session_id=session_id)

        if not plan:
            return "无法生成有效计划"
        print(f"\n 计划:")
        for i, step in enumerate(plan, 1):
            print(f"第{i}步:{step}")
        answer=self.executor.execute(
            question=question,
            plan=plan,
            user_id=user_id,
            system=system_prompt)

        #保存缓存
        if answer:
            self.cache.set(question, answer, user_id=user_id,system_prompt=system_prompt)

        if session_id and answer:
            history=self.session.load_session(user_id=user_id,session_id=session_id)
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            self.session.save_session(user_id, session_id, history)
        return answer

plan_agent=PlanAndSolveAgent(plan_tools=plan_tool,
                             plan_handlers=plan_handlers,
                             executor_tools=executor_tool,
                             executor_handlers=executor_handlers)




