import time

start=time.time()
from agent.react_agent import ReactAgent

react_agent=ReactAgent()

query=input("请输入：")
result=react_agent.run(query,"你是一个说话甜蜜的助手",session_id="1")
print(result)
print(time.time()-start)


# from agent.react_agent import react_agent
#
#
#w
# print("快速连续提问12次\n")
#
# for i in range(12):
#     result = react_agent.run(f"第{i+1}次提问",session_id="1")
#     if "过于频繁" in result:
#         print(f"第{i+1}次: ❌ {result}")
#     else:
#         print(f"第{i+1}次: ✅ 正常")