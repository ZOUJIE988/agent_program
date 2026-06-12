"""
Skill 加载系统 - 按需加载知识/规范
"""

import os
from pathlib import Path


class SkillLoader:
    def __init__(self, skills_dir: str = None):
        # 使用相对路径，不硬编码
        if skills_dir is None:
            # 获取当前文件所在目录，然后找 skills 文件夹
            base_dir = Path(__file__).parent
            skills_dir = base_dir / "skills"
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        self._ensure_dir()
        self._load_skills()

    def _ensure_dir(self):
        """确保技能目录存在"""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True)

    def _load_skills(self):
        """加载所有 skill 文件"""
        for file_path in self.skills_dir.glob("*.md"):
            name = file_path.stem
            content = file_path.read_text(encoding='utf-8')
            self.skills[name] = content
            print(f"已加载 Skill: {name}")

    def get_descriptions(self) -> str:
        """获取所有技能描述（用于 System Prompt）"""
        if not self.skills:
            return "暂无可用技能"
        lines = ["可用技能（需要时用 load_skill 加载）："]
        for name in self.skills.keys():
            lines.append(f"  - {name}")
        return "\n".join(lines)

    def get_skill(self, name: str) -> str:
        """获取技能内容"""
        if name not in self.skills:
            return f"❌ 技能 '{name}' 不存在\n可用技能：{', '.join(self.skills.keys())}"
        return self.skills[name]

    def reload(self):
        """重新加载所有技能"""
        self.skills.clear()
        self._load_skills()
        return f"✅ 已重新加载 {len(self.skills)} 个技能"


# 全局实例
skill_loader = SkillLoader()


# ========== 工具定义 ==========
LOAD_SKILL_TOOL = {
    "type": "function",
    "function": {
        "name": "load_skill",
        "description": "加载技能知识。当需要按照特定规范工作时调用此工具，如日程安排、代码审查、会议纪要等。",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "技能名称，如 schedule_assistant、code_review、meeting_minutes"
                }
            },
            "required": ["skill_name"]
        }
    }
}


def handle_load_skill(skill_name: str) -> str:
    """处理 load_skill 工具调用"""
    return skill_loader.get_skill(skill_name)


if __name__ == "__main__":
    # 测试
    print("=" * 40)
    print("可用技能:")
    print(skill_loader.get_descriptions())
    print("\n" + "=" * 40)