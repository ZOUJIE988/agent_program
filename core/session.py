import json
from utils.config import day
from core.cache import cache

class Session:
    def __init__(self):
        self.redis=cache.redis

    def save_session(self, user_id: str,session_id:str,history:list):
        """保存会话历史"""
        key = f"session:{user_id}:{session_id}:history"

        # 去重：移除相同消息
        seen = set()
        deduplicated = []
        for msg in history:
            # 用 (role, content) 作为唯一标识
            msg_key = (msg.get("role"), msg.get("content"))
            if msg_key not in seen:
                seen.add(msg_key)
                deduplicated.append(msg)
            else:
                print(f"⏭️ 去重: 跳过重复消息 {msg.get('role')}: {msg.get('content')[:30]}...")

        self.redis.setex(key, day , json.dumps(deduplicated))  # 保存1天

    def load_session(self, user_id: str, session_id: str) -> list:
        """加载会话历史"""
        key = f"session:{user_id}:{session_id}:history"
        data = self.redis.get(key)
        return json.loads(data) if data else []

    def list_sessions(self, user_id: str = "default") -> list:
        """列出用户的所有会话"""
        pattern = f"session:{user_id}:*:history"
        session_ids = []
        for key in self.redis.scan_iter(match=pattern):
            # 从 key 中提取 session_id
            # key 格式：session:user123:abc123:history
            parts = key.split(":")
            if len(parts) >= 3:
                session_ids.append(parts[2])  # 提取 session_id
        return session_ids

    def delete_session(self, session_id: str,user_id: str="default") -> bool:
        """删除指定会话"""
        key = f"session:{user_id}:{session_id}:history"
        result = self.redis.delete(key)
        if result:
            print(f"已删除会话: {session_id}")
        else:
            print(f"会话不存在: {session_id}")
        return result > 0

    def delete_user_sessions(self, user_id: str="default") -> int:
        """删除用户的所有会话"""
        pattern = f"session:{user_id}:*:history"
        count = 0
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
            count += 1
        print(f"已删除用户 {user_id} 的 {count} 个会话")
        return count