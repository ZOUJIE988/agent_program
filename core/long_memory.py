import json
import threading
from utils.config import *
from utils.prompt_config import *
from core.cache import cache

class LongMemory:
    def __init__(self):
        self.long_redis=cache.redis
    def _key(self, user_id: str) -> str:
        """生成 Redis key"""
        return f"long_mem:{user_id}:data"

    def set(self, user_id: str, key: str, value: str, ttl: int = None):
        """保存记忆（存到哈希表）"""
        full_key = self._key(user_id)
        self.long_redis.hset(full_key, key, value)
        if ttl:
            self.long_redis.expire(full_key, ttl)

    def get(self, user_id: str, key: str) :
        """获取记忆"""
        return self.long_redis.hget(self._key(user_id), key)

    def get_all(self, user_id: str):
        """获取所有记忆"""
        return self.long_redis.hgetall(self._key(user_id))

    def delete(self, user_id: str, key: str):
        """删除单条记忆"""
        self.long_redis.hdel(self._key(user_id), key)

    def delete_all(self,user_id:str):
        """删除用户的所有记忆"""
        self.long_redis.delete(self._key(user_id))

    def get_context(self, user_id: str) -> str:
        """获取所有记忆，用于注入 prompt"""
        all_data = self.get_all(user_id)
        if not all_data:
            return ""

        parts = [f"- {k}: {v}" for k, v in all_data.items()]
        return "## 长期记忆\n" + "\n".join(parts)
    def need_extract(self,user_query:str):
        """规则快速判断是否需要提取"""
        for kw in personal_keywords:
            if kw in user_query:
                return True
        return False

    def extract_from_conversation(self,user_id:str,
                                  user_query: str,
                                  ai_response: str,
                                  llm_client):

        """规则过滤 + LLM 精确提取"""
        if not self.need_extract(user_query):
            return
        prompt=long_prompt.format(user_query=user_query,ai_response=ai_response)
        def background_task():
            """后台任务：调用 LLM 提取并保存"""
            try:
                result = llm_client.run_with_tools(prompt)
                if not result:
                    print(f"解析失败: {result[:100]}")
                items = json.loads(result)
                for key, value in items:
                    self.set(user_id, key, value)
            except Exception as e:
                print(f"提取失败: {e}")

        thread=threading.Thread(target=background_task, daemon=False)
        thread.start()


long_memory=LongMemory()