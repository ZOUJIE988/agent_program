from typing import Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(..., description="用户问题", example="你好，请介绍一下自己")
    user_id: str = Field(default="default", description="用户ID", example="user_001")
    session_id: Optional[str] = Field(default=None, description="会话ID，用于多轮对话", example="session_001")
    system_prompt: Optional[str] = Field(default="", description="系统提示词", example="你是一个专业的AI助手")


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str = Field(default="success", description="状态信息")
    data: Optional[str] = Field(default=None, description="响应内容")