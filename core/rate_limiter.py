import time
from collections import defaultdict

class RateLimiter:
    """用户提问频率限制器"""
    def __init__(self, limit: int = 10, window: int = 60):
        """
        参数:
            limit: 时间窗口内最多提问次数（默认10次）
            window: 时间窗口（秒，默认60秒）
        """
        self.limit = limit
        self.window = window
        self.user_history = defaultdict(list)  # {user_id: [timestamp1, timestamp2]}

    def check_and_record(self, user_id: str) -> tuple:
        """
        检查用户是否超限，并记录本次提问
        返回 (是否允许, 提示消息)
        """
        now = time.time()
        history = self.user_history[user_id]

        # 清理过期记录（超过时间窗口的）
        while history and history[0] < now - self.window:
            history.pop(0)

        # 检查是否超限
        if len(history) >= self.limit:
            wait_time = self.window - (now - history[0])
            return False, f"提问过于频繁，请等待 {wait_time:.1f} 秒后再试"

        # 记录本次提问
        history.append(now)
        return True, ""


# 全局实例（每分钟最多10次）
rate_limiter = RateLimiter(limit=10, window=60)