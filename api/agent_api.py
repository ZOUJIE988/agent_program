import uvicorn
from fastapi import FastAPI, HTTPException
from api.models import *
from core.langgraph_scheduler import scheduler

app=FastAPI(description="多智能体调度系统 - 支持 React、Plan、Reflect 三种 Agent")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    根据用户问题自动选择 Agent 并返回回答
    """
    try:
        # 调用调度器
        result = scheduler.run(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            system_prompt=request.system_prompt or ""
        )

        return ChatResponse(
            message="success",
            data=result,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/{agent_name}", response_model=ChatResponse)
async def chat_with_agent(
        agent_name: str,
        request: ChatRequest
):
    """
    指定 Agent 的聊天接口
    路径参数:
    - agent_name: react / plan / reflect
    示例: POST /chat/react
    """
    if agent_name not in ["react", "plan", "reflect"]:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 agent_name: {agent_name}，可选值: react, plan, reflect"
        )

    try:
        # 手动指定 Agent
        query = request.query
        if agent_name == "react":
            query = f"用react_agent {query}"
        elif agent_name == "plan":
            query = f"用plan_agent {query}"
        else:
            query = f"用reflect_agent {query}"

        result = scheduler.run(
            query=query,
            user_id=request.user_id,
            session_id=request.session_id,
            system_prompt=request.system_prompt or ""
        )

        return ChatResponse(
            message="success",
            data=result,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "agent_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # 开发模式，代码修改后自动重启
        log_level="info"
    )