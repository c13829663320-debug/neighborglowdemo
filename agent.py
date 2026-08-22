import re
from datetime import datetime

TRIGGER_RULES = [
    {"keywords": ["@调解员", "调解", "吵架", "冲突", "争吵", "闹矛盾"], "agent": "mediator", "explicit": True},
    {"keywords": ["@顾问", "怎么办", "如何", "建议", "方案", "求助", "帮忙"], "agent": "advisor", "explicit": True},
    {"keywords": ["@公告员", "通知", "公告", "提醒大家"], "agent": "announcer", "explicit": True},
    {"keywords": ["@记录员", "总结", "纪要", "记录"], "agent": "recorder", "explicit": True},
    {"keywords": ["@指导员", "练习", "模拟", "技巧", "怎么说"], "agent": "coach", "explicit": True},
    {"keywords": ["吵", "闹", "烦", "讨厌", "投诉", "吵架", "气", "怒", "忍不了", "受不了", "疯了", "恨"], "agent": "mediator", "explicit": False},
    {"keywords": ["怎么办", "如何", "建议", "方案", "求助", "不知道", "困惑"], "agent": "advisor", "explicit": False},
]


def match_trigger(text):
    text_lower = text.lower()
    for rule in TRIGGER_RULES:
        for kw in rule["keywords"]:
            if kw.lower() in text_lower:
                return {"agent": rule["agent"], "explicit": rule["explicit"], "matched_keyword": kw}
    return None


AGENT_INFO = {
    "mediator": {"name": "调解员", "emoji": "🛟", "description": "帮助冷静双方、引导对话、化解冲突"},
    "advisor": {"name": "顾问", "emoji": "💡", "description": "提供事实梳理和解决方案建议"},
    "announcer": {"name": "公告员", "emoji": "📢", "description": "生成社区公告和通知"},
    "recorder": {"name": "记录员", "emoji": "📝", "description": "自动记录讨论要点、生成纪要"},
    "coach": {"name": "指导员", "emoji": "🎓", "description": "提供沟通技巧指导和角色扮演"},
}


class BaseAgent:
    def __init__(self, agent_name, db_session=None):
        self.agent_name = agent_name
        self.info = AGENT_INFO.get(agent_name, {"name": "助手", "emoji": "🤖", "description": ""})
        self.db = db_session

    def respond(self, user_message, context=None):
        raise NotImplementedError

    def _format_message(self, text):
        return f"{self.info['emoji']} {self.info['name']}：{text}"


class MediatorAgent(BaseAgent):
    def __init__(self, db_session=None):
        super().__init__("mediator", db_session)

    def respond(self, user_message, context=None):
        recent_msgs = (context or {}).get("recent_messages", [])
        emotions = self._detect_emotions(user_message)
        if "anger" in emotions:
            return self._format_message(
                "我感受到你现在很生气。在情绪激动的时候沟通往往达不到最好的效果。"
                + "建议先做几个深呼吸，等情绪平复后再考虑如何沟通。"
                + "你愿意告诉我具体发生了什么事吗？我可以帮你梳理事实。"
            )
        elif "frustration" in emotions:
            return self._format_message(
                "看来这个问题已经困扰你很久了。反复处理确实让人疲惫。"
                + "我们可以一起整理一下事情的经过，看看问题到底出在哪里。"
                + "请用几句话描述一下：什么时间、什么行为、对你有什么影响？"
            )
        elif "anxiety" in emotions:
            return self._format_message(
                "你似乎有些焦虑，担心事情处理不好。这是很正常的感受。"
                + "请放心，我们可以一步步来。你能先告诉我你最担心的是什么吗？"
            )
        else:
            return self._format_message(
                "我注意到你正在讨论一个可能存在的邻里问题。"
                + "我可以帮助你：梳理事实、分析双方立场、引导建设性对话。"
                + "需要我帮你什么呢？"
            )

    def _detect_emotions(self, text):
        emotions = []
        if any(w in text for w in ["气", "怒", "烦", "讨厌", "恨", "吵"]):
            emotions.append("anger")
        if any(w in text for w in ["焦虑", "担心", "怕", "紧张"]):
            emotions.append("anxiety")
        if any(w in text for w in ["一直", "总是", "每次", "反复", "够了"]):
            emotions.append("frustration")
        if any(w in text for w in ["不知道", "怎么办", "求助无门"]):
            emotions.append("helplessness")
        return emotions


class AdvisorAgent(BaseAgent):
    def __init__(self, db_session=None):
        super().__init__("advisor", db_session)

    def respond(self, user_message, context=None):
        category = self._classify_issue(user_message)
        if category == "noise":
            return self._format_message(
                "关于噪音问题，建议这样处理：\n"
                "1. 先确认噪音的具体时间和来源\n"
                "2. 选择合适的时间礼貌沟通\n"
                "3. 可以说：'您好，最近晚上X点后我听到一些声音，影响休息，能否帮忙注意一下？'\n"
                "4. 如无改善，再请物业协助\n"
                "需要我帮你生成一段具体的沟通文案吗？"
            )
        elif category == "pet":
            return self._format_message(
                "关于宠物问题，建议：\n"
                "1. 宠物叫声可能是主人没意识到，先友善提醒\n"
                "2. 如果沟通无效再找物业介入\n"
            )
        else:
            return self._format_message(
                "我可以帮你分析问题并提供建议。\n"
                "请告诉我：1. 具体发生了什么事？ 2. 从什么时候开始的？ 3. 你已经尝试过什么？ 4. 你理想的解决结果是什么？"
            )

    def _classify_issue(self, text):
        if any(w in text for w in ["噪音", "吵", "声音", "装修"]):
            return "noise"
        if any(w in text for w in ["停车", "车位"]):
            return "parking"
        if any(w in text for w in ["狗", "猫", "宠物"]):
            return "pet"
        if any(w in text for w in ["漏水", "渗水"]):
            return "leak"
        return "other"


class AnnouncerAgent(BaseAgent):
    def __init__(self, db_session=None):
        super().__init__("announcer", db_session)

    def respond(self, user_message, context=None):
        return self._format_message(
            "我可以帮你生成社区公告。请告诉我：\n1. 公告主题 2. 目标受众 3. 关键信息 4. 期望的语气"
        )


class RecorderAgent(BaseAgent):
    def __init__(self, db_session=None):
        super().__init__("recorder", db_session)

    def respond(self, user_message, context=None):
        recent = (context or {}).get("recent_messages", [])
        if not recent:
            return self._format_message("目前还没有讨论内容可供总结。")
        key_points = []
        for msg in recent[-20:]:
            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
            if any(kw in content for kw in ["决定", "问题", "行动", "时间", "负责"]):
                key_points.append(content[:80])
        if key_points:
            return self._format_message("📋 讨论要点：\n" + "\n".join(f"• {p}" for p in key_points))
        return self._format_message("暂时没有提取到明确的要点。")


class CoachAgent(BaseAgent):
    def __init__(self, db_session=None):
        super().__init__("coach", db_session)

    def respond(self, user_message, context=None):
        if any(w in user_message for w in ["练习", "模拟", "角色扮演"]):
            return self._format_message(
                "好的！我们来练习沟通。请告诉我：\n1. 你想模拟的场景 2. 对方可能的态度 3. 你想表达的核心内容\n我会扮演对方，你练习沟通，我会逐轮给出反馈。"
            )
        else:
            return self._format_message(
                "沟通技巧建议：\n"
                "1. 用'我'开头表达感受\n"
                "2. 描述具体行为\n"
                "3. 提出明确请求\n"
                "4. 给对方回应空间\n"
                "想针对某个具体场景练习吗？"
            )


AGENT_MAP = {
    "mediator": MediatorAgent,
    "advisor": AdvisorAgent,
    "announcer": AnnouncerAgent,
    "recorder": RecorderAgent,
    "coach": CoachAgent,
}


def get_agent(agent_name, db_session=None):
    agent_class = AGENT_MAP.get(agent_name, BaseAgent)
    return agent_class(agent_name, db_session) if agent_name in AGENT_MAP else BaseAgent(agent_name, db_session)


def create_agent_response(user_message, context=None, db_session=None):
    trigger = match_trigger(user_message)
    if not trigger:
        return None, None
    agent = get_agent(trigger["agent"], db_session)
    response = agent.respond(user_message, context)
    return agent, response
