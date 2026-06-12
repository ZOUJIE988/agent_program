import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ========== API 配置（从环境变量读取）==========
open_api_key = os.getenv("OPEN_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
max_rounds = 20

# ========== Redis 配置 ==========
host = os.getenv("REDIS_HOST", "localhost")
port = int(os.getenv("REDIS_PORT", 6379))
db = 0
ttl = 3600
decode_responses = True
day = 86400

# ========== 记忆提取关键词（可保留）==========
personal_keywords = [
    "喜欢", "爱", "身份", "讨厌", "记住",
    "是", "我叫", "岁", "年龄", "职业", "偏好", "习惯",
]

# ========== 敏感词==========
sensitive_words = []

# ========== 路径配置==========
# 原绝对路径改成相对路径
BASE_DIR = Path(__file__).parent.parent  # 项目根目录
OUTPUT_DIR = BASE_DIR / "a_compress" / "L3"
TRANSCRIPT_DIR = BASE_DIR / "a_compress" / "L4"

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)


# ========== 压缩配置 ==========
class MessageType(Enum):
    SYSTEM = "system"
    SYSTEM_SUMMARY = "system_summary"
    USER_QUERY = "user_query"
    USER_FEEDBACK = "user_feedback"
    USER_COMMAND = "user_command"
    ASSISTANT_ANSWER = "assistant_answer"
    ASSISTANT_THINKING = "assistant_thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    IMPORTANT = "important"
    CHECKPOINT = "checkpoint"


MAX_MESSAGES = 30
KEEP_RECENT_TOOL_RESULTS = 3
MAX_TOOL_RESULT_BYTES = 200 * 1024
TOKEN_THRESHOLD = 2000

IMPORTANT_KEYWORDS = ["记住", "重要", "关键", "核心", "必须", "注意"]
FEEDBACK_KEYWORDS = ["不对", "应该是", "纠正", "错了"]
COMMAND_KEYWORDS = ["写", "创建", "生成", "帮我"]

BASE_SCORES = {
    MessageType.SYSTEM: 1.0,
    MessageType.SYSTEM_SUMMARY: 0.9,
    MessageType.USER_FEEDBACK: 0.9,
    MessageType.USER_COMMAND: 0.8,
    MessageType.USER_QUERY: 0.7,
    MessageType.IMPORTANT: 0.9,
    MessageType.CHECKPOINT: 0.8,
    MessageType.ASSISTANT_ANSWER: 0.5,
    MessageType.ASSISTANT_THINKING: 0.3,
    MessageType.TOOL_RESULT: 0.4,
    MessageType.TOOL_CALL: 0.3,
    MessageType.TOOL_ERROR: 0.1,
}