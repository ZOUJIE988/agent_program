from core.long_memory import long_memory

# 获取用户的所有记忆
user_id = "default"
all_memories = long_memory.get_all(user_id)

print(all_memories)
# 输出：{'name': '张三', 'age': '25', 'hobby': 'Python'}