# test/reflection_test.py
import time
from agent.reflect_agent import reflection_agent

start = time.time()

# 测试任务
task = "写一篇关于人工智能发展的简短文章，200字左右。"

print("=" * 50)
print("开始测试 ReflectionAgent")
print("=" * 50)

result = reflection_agent.run(
    task=task,
    session_id="1"
)
print(result)
print("\n" + "=" * 50)
print(f"总耗时: {time.time() - start:.2f}秒")
print("=" * 50)