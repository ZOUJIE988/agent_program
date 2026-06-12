from typing import TypedDict,Literal
from agent.plan_agent import plan_agent
from agent.react_agent import react_agent
from agent.reflect_agent import reflection_agent
from langgraph.graph import StateGraph, END
class SchedulerState(TypedDict):
    """调度器状态"""
    query: str
    user_id: str
    session_id: str
    system_prompt: str
    selected_agent: str             # react / plan / reflect
    result: str

AGENTS_CONFIG = {
    "react": {
        "func": react_agent.run,
        "keywords": ["你好", "是什么", "为什么"]
    },
    "plan": {
        "func": plan_agent.run,
        "keywords": ["然后", "接着", "先", "再", "最后", "和", "分别", "总共"]
    },
    "reflect": {
        "func": reflection_agent.run,
        "keywords": ["写", "创作", "文章", "优化", "改进", "总结", "报告"]
    }
}

def select_agent_by_keywords(query: str) -> str:
    """
    根据关键词选择最合适的 Agent
    完全保持你原有的 _select 逻辑
    """
    best_name = "react"
    best_score = 0

    for name, info in AGENTS_CONFIG.items():
        score = sum(1 for kw in info["keywords"] if kw in query)
        if score > best_score:
            best_score = score
            best_name = name

    # print(f"选择: {best_name} (分数: {best_score})")
    return best_name

def handle_manual_specification(query: str):
    """
    处理手动指定的 Agent
    返回: (agent_name, cleaned_query)
    """
    if "用react_agent" in query or "使用react" in query:
        agent_name = "react"
        query = query.replace("用react_agent", "").replace("使用react", "").strip()
        return agent_name, query
    elif "用reflect_agent" in query or "使用reflect" in query:
        agent_name = "reflect"
        query = query.replace("用reflect_agent", "").replace("使用reflect", "").strip()
        return agent_name, query
    elif "用plan_agent" in query or "使用plan" in query:
        agent_name = "plan"
        query = query.replace("用plan_agent", "").replace("使用plan", "").strip()
        return agent_name, query
    else:
        return None, query

# ========== LangGraph 节点 ==========
def router_node(state: SchedulerState) -> dict:
    """
    路由节点：决定使用哪个 Agent
    """
    query = state["query"]

    # 1. 检查手动指定
    agent_name, cleaned_query = handle_manual_specification(query)

    # 2. 如果没有手动指定，自动选择
    if agent_name is None:
        agent_name = select_agent_by_keywords(cleaned_query)

    # print(f"选择 Agent: {agent_name}")

    return {
        "selected_agent": agent_name,
        "query": cleaned_query
    }

def react_node(state: SchedulerState) -> dict:
    """ReAct Agent 执行节点"""
    print(f"执行 React Agent")

    result = react_agent.run(
        query=state["query"],
        user_id=state["user_id"],
        session_id=state["session_id"],
        system_prompt=state["system_prompt"]
    )

    return {"result": result}

def plan_node(state: SchedulerState) -> dict:
    """Plan Agent 执行节点"""
    print(f"执行 Plan Agent")

    result = plan_agent.run(
        question=state["query"],
        user_id=state["user_id"],
        session_id=state["session_id"],
        system_prompt=state["system_prompt"]
    )

    return {"result": result}

def reflect_node(state: SchedulerState) -> dict:
    """Reflect Agent 执行节点"""
    print(f"执行 Reflect Agent")

    result = reflection_agent.run(
        task=state["query"],
        user_id=state["user_id"],
        session_id=state["session_id"],
        system_prompt=state["system_prompt"]
    )

    return {"result": result}

def route_after_router(state: SchedulerState) -> Literal["react", "plan", "reflect"]:
    """根据选中的 agent 路由到对应节点"""
    return state["selected_agent"]

# ========== 构建图 ==========
def build_scheduler_graph():
    """
    构建调度器图结构
    图结构：
    START → router → [react / plan / reflect] → END
    """
    builder = StateGraph(SchedulerState)

    # 添加节点
    builder.add_node("router", router_node)
    builder.add_node("react", react_node)
    builder.add_node("plan", plan_node)
    builder.add_node("reflect", reflect_node)

    # 设置入口
    builder.set_entry_point("router")

    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "react": "react",
            "plan": "plan",
            "reflect": "reflect"
        }
    )
    builder.add_edge("react", END)
    builder.add_edge("plan", END)
    builder.add_edge("reflect", END)

    return builder.compile()


class Scheduler:
    """任务调度器 - 使用 LangGraph 图结构"""

    def __init__(self):
        self.graph = build_scheduler_graph()

    def run(self, query: str, user_id: str = "default",
            session_id: str = None, system_prompt: str = "") -> str:
        """执行调度 - 接口与原版完全一致"""

        # 初始化状态
        initial_state: SchedulerState = {
            "query": query,
            "user_id": user_id,
            "session_id": session_id or "",
            "system_prompt": system_prompt,
            "selected_agent": "",
            "result": ""
        }

        # 执行图
        final_state = self.graph.invoke(initial_state)

        return final_state.get("result", "")


# 全局实例（兼容原有导入）
scheduler = Scheduler()


def run(query: str, user_id: str = "default",
        session_id: str = None, system_prompt: str = "") -> str:
    """便捷调用函数"""
    return scheduler.run(query, user_id, session_id, system_prompt)






