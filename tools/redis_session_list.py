# test/quick_list_sessions.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session import Session

s = Session()

# 查看 default 用户的所有会话
sessions = s.list_sessions("default")
print(f"default 用户的会话: {sessions}")

# 查看每个会话的内容
for sid in sessions:
    history = s.load_session("default", sid)
    print(f"\n{sid}: {len(history)} 条消息")
    for msg in history[-2:]:  # 只显示最后2条
        print(f"  {msg['role']}: {msg['content'][:50]}...")