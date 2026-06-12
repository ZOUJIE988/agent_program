from core.session import Session

s = Session()
history = s.load_session("default", "1")  # 你用的 session_id 是 "1"
role=""
for d in history:
    role=d["role"]
    content=d["content"].strip().replace("\n"," ")
    print(role,":",content)
    if role=="assistant":
        print()


