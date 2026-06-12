from agent.plan_agent import plan_agent


# 运行
result = plan_agent.run(
    question="一个水果店周一卖15个苹果，周二卖周一的两倍，周三卖比周二少5个，三天总共多少个？",
    session_id="1",
)

print(f"最终答案: {result}")