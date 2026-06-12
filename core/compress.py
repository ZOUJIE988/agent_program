"""
上下文压缩 - 四层压缩
设计原则：便宜的先跑，贵的后跑
"""
import json
import time
from typing import List, Dict
from utils.config import *
from utils.prompt_config import *


def estimate_tokens(messages: List[Dict]) -> int:
    """粗略估算 token 数"""
    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total_chars += len(part["text"])
    return int(total_chars * 0.4)

def get_message_importance(msg: Dict) -> float:
    """获取消息重要性分数"""
    if "importance" in msg:
        return msg["importance"]

    role = msg.get("role", "")
    content = msg.get("content", "")

    if role == "system":
        return 1.0

    if role == "user":
        for kw in IMPORTANT_KEYWORDS:
            if kw in content:
                return 0.9
        for kw in FEEDBACK_KEYWORDS:
            if kw in content:
                return 0.85
        for kw in COMMAND_KEYWORDS:
            if kw in content:
                return 0.8
        return 0.7

    if role == "assistant":
        if any(kw in content for kw in ["记住", "你的名字是", "你叫"]):
            return 0.8
        return 0.5

    if role == "tool":
        if "error" in content.lower() or "失败" in content:
            return 0.1
        return 0.4

    return 0.5

#L1: 按重要性裁剪（成对保留）
def snip_compact(messages: List[Dict]) -> List[Dict]:
    """按轮次保留（用户+助手成对），保留高重要性的轮次"""
    if len(messages) <= MAX_MESSAGES:
        return messages

    # 按轮次分组
    rounds = []
    current_round = []
    current_importance = 0.0
    for msg in messages:
        importance = get_message_importance(msg)
        current_round.append(msg)
        current_importance = max(current_importance, importance)

        if msg.get("role") == "assistant":
            rounds.append((current_importance, current_round))
            current_round = []
            current_importance = 0.0

    if current_round:
        rounds.append((current_importance, current_round))

    if not rounds:
        return messages

    # 保留最近 5 轮
    keep_recent = 5
    recent_rounds = rounds[-keep_recent:] if len(rounds) > keep_recent else rounds

    # 历史轮次按重要性保留
    history_rounds = rounds[:-keep_recent] if len(rounds) > keep_recent else []
    history_rounds.sort(key=lambda x: x[0], reverse=True)

    max_rounds = MAX_MESSAGES // 2
    keep_history_count = max(0, max_rounds - len(recent_rounds))
    keep_history = history_rounds[:keep_history_count]

    # 合并并保持原始顺序
    all_keep = keep_history + recent_rounds
    all_keep.sort(key=lambda x: messages.index(x[1][0]) if x[1] else 0)

    result = []
    for _, round_msgs in all_keep:
        result.extend(round_msgs)

    return result

#L2: tool_result 变占位符
def micro_compact(messages: List[Dict]) -> List[Dict]:
    """只保留最近 N 条 tool_result，旧的替换为占位符"""
    tool_count = 0

    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") == "tool":
            tool_count += 1
            if tool_count > KEEP_RECENT_TOOL_RESULTS:
                content = msg.get("content", "")
                if len(content) > 200:
                    msg["content"] = f"[已压缩] 工具返回了 {len(content)} 字符"

    return messages

#L3: 大结果落盘
def tool_result_budget(messages: List[Dict]) -> List[Dict]:
    """大结果保存到磁盘"""
    tool_messages = []
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if msg.get("role") == "tool":
            tool_messages.insert(0, (i, msg))
        else:
            break

    if not tool_messages:
        return messages

    total_size = 0
    for idx, msg in tool_messages:
        total_size += len(msg.get("content", ""))

    if total_size <= MAX_TOOL_RESULT_BYTES:
        return messages

    tool_messages.sort(key=lambda x: len(x[1].get("content", "")), reverse=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, msg in tool_messages:
        if total_size <= MAX_TOOL_RESULT_BYTES:
            break

        content = msg.get("content", "")
        size = len(content)
        timestamp = int(time.time())
        filename = OUTPUT_DIR / f"tool_result_{timestamp}_{idx}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"content": content}, f, ensure_ascii=False)

        preview = content[:500] + "..." if len(content) > 500 else content
        msg["content"] = f"[已落盘] 完整内容保存到 {filename}\n预览:\n{preview}"
        total_size -= size

    return messages

#L4: LLM 摘要
def auto_compact(messages: List[Dict], client, model_name: str) -> List[Dict]:
    """LLM 总结整个对话"""
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.json"

    with open(transcript_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    recent = messages[-20:] if len(messages) > 20 else messages

    summary_prompt =SUMMARY_PROMPT.format( recent_messages=json.dumps(recent, ensure_ascii=False, indent=2)[:20000])
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=500
        )

        usage = response.usage
        print(f"[L4] 摘要生成成功，消耗 tokens: {usage.total_tokens}")

        summary = response.choices[0].message.content

    except Exception as e:
        summary = f"摘要失败: {e}"
        print(f"[L4] 摘要失败: {e}")

    return [
        {"role": "system", "content": f"对话摘要：\n\n{summary}", "importance": 0.9},
        {"role": "user", "content": "请继续完成任务", "importance": 0.8}
    ]


def apply_compression(messages: List[Dict], client=None, model_name=None) :
    """按顺序应用压缩：L2 → L1 → L3 → L4"""
    if not messages:
        return messages, False

    # 先统计原始消息
    original_tokens = estimate_tokens(messages)
    print(f"原始 tokens: {original_tokens}, 阈值: {TOKEN_THRESHOLD}")

    # 没超标，直接返回
    if original_tokens <= TOKEN_THRESHOLD:
        print(f"token 未超标，无需压缩")
        return messages, False

    print(f"token 超标，开始压缩...")

    # ========== L2: 旧结果变占位符 ==========
    messages = micro_compact(messages)

    # ========== L1: 按重要性裁剪 ==========
    old_len = len(messages)
    messages = snip_compact(messages)
    print(f"[L1] 裁剪: {old_len} → {len(messages)} 条消息")

    # ========== L3: 大结果落盘 ==========
    messages = tool_result_budget(messages)

    # 统计压缩后的 token
    new_tokens = estimate_tokens(messages)
    print(f"压缩后 tokens: {new_tokens}")

    # ========== L4: 还超标则 LLM 摘要 ==========
    if new_tokens > TOKEN_THRESHOLD and client and model_name:
        print(f"压缩后仍超标 ({new_tokens} > {TOKEN_THRESHOLD})，执行 L4...")
        messages = auto_compact(messages, client, model_name)
        return messages, True

    return messages, True
