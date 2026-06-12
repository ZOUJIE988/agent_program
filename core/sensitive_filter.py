import re
from utils.config import *


class SensitiveFilter:
    """敏感词过滤类 - 只检查用户输入"""

    def __init__(self):
        """初始化敏感词列表和正则表达式"""
        self.sensitive_words =sensitive_words # 从配置读取敏感词列表
        self.pattern = self._compile_pattern()  # 编译正则表达式，提高匹配效率

    def _compile_pattern(self):
        """将敏感词列表编译成正则表达式"""
        if not self.sensitive_words:
            return None
        # 用 | 连接所有敏感词，re.IGNORECASE 忽略大小写
        pattern = "|".join(re.escape(word) for word in self.sensitive_words)
        return re.compile(pattern, re.IGNORECASE)

    def contains(self, text: str) -> bool:
        """检查文本是否包含敏感词，返回 True/False"""
        if not self.pattern or not text:
            return False
        return bool(self.pattern.search(text))  # search 找到任何匹配就返回 True


# 创建全局实例
sensitive_filter = SensitiveFilter()