from core.langgraph_scheduler import scheduler

if __name__ == '__main__':
    print("AI Agent 系统启动")
    print("输入q,退出系统")
    print("=" * 50)
    user_id = input("请输入用户ID (直接回车使用 default): ").strip()
    if not user_id:
        user_id = "default"
    system_prompt = input("请输入智能体的设定 (直接回车跳过): ").strip()

    session_id=input("请输入此次会话的名字(方便下次回到此次会话，如果不需要，直接回车跳过):").strip()

    while True:
        user_input = input("你: ").strip()
        if not user_input:
            print("请输入内容")
            continue

        if user_input.lower() in ["q"]:
            print("再见！")
            break

        result = scheduler.run(user_input, user_id=user_id,session_id=session_id,system_prompt=system_prompt)
        print(f"助手: {result}")