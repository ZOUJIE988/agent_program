基于 LangGraph 的多智能体调度系统，支持 ReAct、Plan-and-Solve、Reflection 三种 Agent 模式自动路由，集成 RAG、文件操作、浏览器自动化等能力。

## 技术栈

- **框架**：LangGraph、FastAPI
- **AI**：OpenAI API、MCP（浏览器自动化）
- **存储**：Redis（缓存、限流、会话、长期记忆）

## 核心特性

| 特性 | 说明 |
|------|------|
| **三种 Agent 模式** | ReAct（工具调用）、Plan-and-Solve（多步拆解）、Reflection（执行→反思→优化） |
| **智能路由** | 关键词匹配自动选择 Agent，支持手动指定降级，路由延迟 <1ms |
| **四层上下文压缩** | 裁剪 → 占位符 → 落盘 → LLM 摘要，长对话 token 从 8000+ 降至 2000 以内 |
| **分层记忆** | 短期记忆（会话历史）+ 长期记忆（Redis Hash，规则过滤 + LLM 异步提取） |
| **工程化** | Redis 缓存、分布式限流、敏感词过滤、指数退避重试 |

## 快速开始

### 环境要求

- Python 3.10+
- Redis
- 
### 安装依赖

```bash
pip install -r requirements.txt