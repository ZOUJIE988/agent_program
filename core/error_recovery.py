import time
import random
from typing import Tuple, Callable
from functools import wraps

class ErrorRecovery:
    def __init__(self):
        self.max_retries = 3      # 最大重试次数
        self.base_delay = 1       # 基础等待时间（秒）

    def should_retry(self, error: Exception, retry_count: int) -> Tuple[bool, float]:
        """判断是否应该重试，返回 (是否重试, 等待秒数)"""
        error_msg = str(error).lower()

        # 临时故障 - 重试（指数退避）
        if any(kw in error_msg for kw in ["429", "529", "overloaded", "rate", "timeout", "connection"]):
            if retry_count < self.max_retries:
                wait = self.base_delay * (2 ** retry_count) + random.uniform(0, 1)
                return True, wait
            return False, 0

        # 上下文超限 - 不重试
        if any(kw in error_msg for kw in ["prompt_too_long", "context_length"]):
            return False, 0

        # 其他错误 - 最多重试2次
        if retry_count < 2:
            return True, 1

        return False, 0


# 全局实例
error_recovery = ErrorRecovery()


def with_retry(func: Callable):
    """自动重试装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_error = None
        for i in range(error_recovery.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                should_retry, wait = error_recovery.should_retry(e, i)
                if should_retry:
                    print(f"第 {i+1} 次失败，{wait:.1f}秒后重试... 错误: {str(e)[:50]}")
                    time.sleep(wait)
                else:
                    raise e
        raise last_error
    return wrapper