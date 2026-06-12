import hashlib
import re

import redis

from utils.config import *


class RedisCache:
    def __init__(self):
        self.redis=redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=decode_responses
        )
        self.ttl=ttl

    def _extract_base_system_prompt(self, system_prompt: str) -> str:
        if not system_prompt:
            return ""

        # 删除 "## 对话历史" 到 "## 自定义" 之间的所有内容
        pattern = r'## 对话历史.*?(?=## 自定义|\Z)'
        result = re.sub(pattern, '', system_prompt, flags=re.DOTALL)

        # 删除 "## 长期记忆" 到 "## 自定义" 之间的所有内容
        pattern = r'## 长期记忆.*?(?=## 自定义|\Z)'
        result = re.sub(pattern, '', result, flags=re.DOTALL)

        return result.strip()
    def _generate_key(self, query: str, user_id: str = "default", system_prompt: str = "") -> str:
        """生成缓存, key所有用户共享"""
        base_prompt = self._extract_base_system_prompt(system_prompt)
        content = f"{query}|{user_id}|{base_prompt}"
        return f"request_cache:{hashlib.md5(content.encode()).hexdigest()}"

    def get(self, query: str,user_id: str = "default", system_prompt: str = ""):
        """获取缓存结果"""
        key = self._generate_key(query,user_id,system_prompt)
        result = self.redis.get(key)
        if result:
            return result
        return None

    def set(self, query: str, result: str, user_id:str="default",system_prompt: str = "") -> None:
        """保存缓存（所有用户共享）"""
        key = self._generate_key(query,user_id,system_prompt)
        self.redis.setex(key, self.ttl, result)
        # print(f"已缓存: {query}")

    def clear_all(self) -> int:
        """清空所有缓存"""
        keys = self.redis.keys("request_cache:*")
        if keys:
            count = self.redis.delete(*keys)
            print(f"清空 {count} 条缓存")
            return count
        return 0

cache = RedisCache()
