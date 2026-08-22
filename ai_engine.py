import re
import json
from datetime import datetime

# === Emotion Detection ===
EMOTION_KEYWORDS = {
    "anger": ["气", "怒", "烦", "讨厌", "恨", "吵", "闹", "投诉", "忍不了", "受不了", "疯"],
    "anxiety": ["担心", "焦虑", "害怕", "紧张", "不安", "怕", "忧虑"],
    "sadness": ["委屈", "难过", "伤心", "无奈", "孤独", "失望"],
    "frustration": ["烦", "累", "够了", "一直", "总是", "每次都", "反复"],
    "helplessness": ["不知道怎么办", "不知道找谁", "没人管", "求助无门", "不知道说什么"],
}

SAFETY_KEYWORDS = {
    "violence": ["打", "杀", "砍", "暴力", "血", "死", "威胁", "弄死"],
    "harassment": ["骚扰", "跟踪", "盯着", "纠缠", "不停"],
    "property": ["砸", "烧", "破坏", "扔", "高空抛物"],
    "self_harm": ["自杀", "自残", "不想活", "活不下去"],
    "crime": ["警察", "报警", "违法", "犯罪", "法律"],
}

RELATIONSHIP_LEVELS = {
    "none": ["不认识", "第一次", "没接触过", "没说过话"],
    "casual": ["认识", "偶尔", "打过招呼", "普通"],
    "familiar": ["熟悉", "经常", "关系好", "邻居很久"],
    "tense": ["紧张", "僵持", "冷战", "不理", "关系不好"],
    "conflict": ["吵过", "闹过", "有矛盾", "之前就有问题", "一直不和"],
}

CATEGORY_MAP = {
    "noise": ["噪音", "吵", "声音", "音乐", "电视", "装修", "锤子", "电钻", "脚步声", "拖椅子"],
    "parking": ["停车", "车位", "挡路", "占道", "乱停"],
    "pet": ["狗", "猫", "宠物", "叫", "粪便", "掉毛"],
    "renovation": ["装修", "施工", "电钻", "锤子", "搬运"],
    "leak": ["漏水", "渗水", "潮湿", "水管", "下水道"],
    "garbage": ["垃圾", "异味", "臭", "堆物", "杂物"],
    "public_space": ["公共区域", "楼道", "电梯", "走廊", "堆东西"],
    "wechat": ["微信群", "群里", "群主", "误会"],
}

# === Action Plan Templates ===
ACTION_TEMPLATES = {
    "green": {
        "target": "建立第一次有效沟通",
        "steps": [
            {"order": 1, "content": "选择对方可能心情平和的时间（如周末下午或晚饭后）", "done": False},
            {"order": 2, "content": "用友善的语气打招呼，避免上来就指责", "done": False},
            {"order": 3, "content": "描述具体可观察的事实（时间+行为），不要说\"总是\"\"一直\"", "done": False},
            {"order": 4, "content": "说明这件事对你的具体影响", "done": False},
            {"order": 5, "content": "提出一个小而明确的请求", "done": False},
            {"order": 6, "content": "邀请对方回应，给对方解释的空间", "done": False},
        ],
        "don't_do": ["不要用\"你总是\"\"每次都\"等绝对化表述", "不要在情绪激动时沟通", "不要通过第三方传话"],
        "escalation": "如果沟通后对方仍不改变，记录事实并观察一周",
    },
    "yellow": {
        "target": "让重复问题进入可跟进流程",
        "steps": [
            {"order": 1, "content": "整理问题发生的时间频率和具体影响", "done": False},
            {"order": 2, "content": "进行一次正式、明确的书面沟通（微信/便条）", "done": False},
            {"order": 3, "content": "设定2周的观察期", "done": False},
            {"order": 4, "content": "如无改善，准备好事实记录联系物业", "done": False},
        ],
        "don't_do": ["不要升级为辱骂", "不要在业主群公开争执", "不要自行采取报复行动"],
        "escalation": "观察期满无改善，联系物业或社区协调",
    },
    "orange": {
        "target": "由第三方建立沟通框架",
        "steps": [
            {"order": 1, "content": "停止与对方的私下直接沟通", "done": False},
            {"order": 2, "content": "整理事件经过的时间线和关键事实", "done": False},
            {"order": 3, "content": "向物业或社区提交结构化的协调申请", "done": False},
            {"order": 4, "content": "在第三方协调下参与沟通，保持冷静", "done": False},
        ],
        "don't_do": ["不要继续反复私下争执", "不要在情绪化状态下做决定", "不要威胁对方"],
        "escalation": "如协调无果，可向上级社区管理部门反映",
    },
    "red": {
        "target": "保护用户安全",
        "steps": [
            {"order": 1, "content": "立即停止与对方的所有直接接触", "done": False},
            {"order": 2, "content": "如有危险，立即离开现场到安全地点", "done": False},
            {"order": 3, "content": "保存所有相关证据（文字/录音/照片）", "done": False},
            {"order": 4, "content": "联系可信任的人告知情况", "done": False},
            {"order": 5, "content": "必要时拨打110或联系社区民警", "done": False},
        ],
        "don't_do": ["不要单独与对方对峙", "不要试图说服对方", "不要删除任何证据"],
        "escalation": "直接寻求安全保护，跳过沟通环节",
    },
}

# === Message Templates ===
MESSAGE_TEMPLATES = {
    "wechat_friendly": [
        "您好~我是住在{direction}的邻居。",
        "最近{time}的时候，我注意到{fact}。",
        "这对我造成了{impact}的影响，想跟您沟通一下。",
        "不知道是否可以调整一下？比如{request}？",
        "谢谢理解！😊",
    ],
    "wechat_direct": [
        "您好，我是{direction}的住户。",
        "关于{time}发生的{fact}，我想直接跟您沟通。",
        "这件事影响到了我的{impact}。",
        "请您能够{request}。",
        "期待您的回复。",
    ],
    "face_to_face_outline": [
        "【开场】您好，占用您一分钟时间",
        "【事实】就是想跟您确认一下，{time}的时候{fact}",
        "【影响】因为这个，我的{impact}受到了影响",
        "【请求】想看看能不能{request}",
        "【收尾】好的，谢谢您的理解",
    ],
    "door_note": [
        "邻居您好：",
        "我是{direction}的住户。",
        "注意到{time}有{fact}的情况。",
        "这对我的{impact}造成了影响。",
        "如能方便，请联系我沟通一下。",
        "——您的邻居",
    ],
    "property_apply": [
        "尊敬的物业：",
        "本人是{direction}住户，反映以下问题：",
        "【时间】{time}",
        "【事实】{fact}",
        "【影响】{impact}",
        "【诉求】希望物业协助协调，{request}",
        "盼复，谢谢。",
    ],
    "coordination_apply": [
        "社区协调申请",
        "申请人：{direction}住户",
        "问题描述：{time}发生{fact}",
        "影响：{impact}",
        "诉求：请社区协助组织双方沟通，寻求解决方案",
        "已尝试的自助沟通：{previous_attempt}",
        "期待回复，谢谢。",
    ],
}


def detect_emotions(text):
    detected = []
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                detected.append(emotion)
                break
    return detected


def detect_safety_risks(text):
    risks = []
    for risk_type, keywords in SAFETY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                risks.append(risk_type)
                break
    return risks


def classify_category(text):
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in text:
                return category
    return "other"


def detect_frequency(text):
    if any(kw in text for kw in ["每天", "一直", "总是", "每次", "天天"]):
        return "constant"
    elif any(kw in text for kw in ["经常", "频繁", "反复"]):
        return "frequent"
    elif any(kw in text for kw in ["偶尔", "有时", "偶尔一次"]):
        return "occasional"
    elif any(kw in text for kw in ["第一次", "刚", "最近才", "首次"]):
        return "first_time"
    return "unknown"


def detect_relationship(text):
    for level, keywords in RELATIONSHIP_LEVELS.items():
        for kw in keywords:
            if kw in text:
                return level
    return "unknown"


def detect_time(text):
    time_patterns = [
        (r"深夜|半夜|凌晨|晚上", "night"),
        (r"早上|早晨|上午", "morning"),
        (r"中午|下午", "afternoon"),
        (r"装修|施工|工作日", "workday"),
        (r"周末|节假日", "weekend"),
    ]
    for pattern, time_type in time_patterns:
        if re.search(pattern, text):
            return time_type
    return "unspecified"


def calculate_risk(symptoms):
    safety_risks = symptoms.get("safety_risks", [])
    if safety_risks:
        return "red"
    emotions = symptoms.get("emotions", [])
    frequency = symptoms.get("frequency", "unknown")
    relationship = symptoms.get("relationship", "unknown")
    score = 0
    if frequency == "constant":
        score += 25
    elif frequency == "frequent":
        score += 15
    elif frequency == "occasional":
        score += 5
    if "anger" in emotions:
        score += 15
    if "frustration" in emotions:
        score += 10
    if "helplessness" in emotions:
        score += 10
    if "anxiety" in emotions:
        score += 5
    if relationship in ("tense", "conflict"):
        score += 20
    elif relationship == "familiar":
        score += 5
    if score >= 70:
        return "orange"
    elif score >= 40:
        return "yellow"
    else:
        return "green"


def analyze_context(text):
    emotions = detect_emotions(text)
    safety_risks = detect_safety_risks(text)
    category = classify_category(text)
    frequency = detect_frequency(text)
    relationship = detect_relationship(text)
    time_of_day = detect_time(text)
    symptoms = {
        "emotions": emotions,
        "safety_risks": safety_risks,
        "category": category,
        "frequency": frequency,
        "relationship": relationship,
        "time": time_of_day,
    }
    risk_level = calculate_risk(symptoms)
    facts = _extract_facts(text)
    assumptions = _extract_assumptions(text)
    needs = _extract_needs(text, emotions)
    confidence = _calculate_confidence(text, symptoms)
    return {
        "symptoms": symptoms,
        "risk_level": risk_level,
        "facts": facts,
        "assumptions": assumptions,
        "emotions": emotions,
        "needs": needs,
        "confidence": confidence,
        "summary": _generate_summary(symptoms, risk_level),
        "insights": _generate_insights(symptoms, risk_level),
        "key_questions": _generate_key_questions(symptoms),
    }


def _extract_facts(text):
    facts = []
    category = classify_category(text)
    time = detect_time(text)
    freq = detect_frequency(text)
    if time != "unspecified":
        time_label = {"night": "深夜/夜间", "morning": "早间", "afternoon": "午间/下午", "workday": "工作时间", "weekend": "周末"}
        facts.append(f"发生时间：{time_label.get(time, time)}")
    if freq != "unknown":
        freq_label = {"constant": "持续发生", "frequent": "频繁发生", "occasional": "偶尔发生", "first_time": "首次发生"}
        facts.append(f"发生频率：{freq_label.get(freq, freq)}")
    if category != "other":
        cat_label = {"noise": "噪音问题", "parking": "停车问题", "pet": "宠物问题", "renovation": "装修施工", "leak": "漏水问题", "garbage": "卫生问题", "public_space": "公共区域", "wechat": "微信群问题"}
        facts.append(f"问题类型：{cat_label.get(category, category)}")
    return facts


def _extract_assumptions(text):
    assumptions = []
    if "觉得" in text or "可能" in text or "应该" in text:
        assumptions.append("对对方动机存在推测，建议沟通时只说观察到的事实")
    if "就是" in text or "肯定" in text or "一定" in text:
        assumptions.append("使用了绝对化表述，可能引发对方防御")
    return assumptions


def _extract_needs(text, emotions):
    needs = []
    if any(w in text for w in ["休息", "睡觉", "安静"]):
        needs.append("需要安静的休息环境")
    if any(w in text for w in ["安全", "放心"]):
        needs.append("需要安全感")
    if any(w in text for w in ["公平", "合理"]):
        needs.append("需要公平合理的对待")
    if any(w in text for w in ["回应", "说法", "解释"]):
        needs.append("需要得到回应和解释")
    if any(w in text for w in ["不想", "不要", "别"]):
        needs.append("需要设定清晰的边界")
    if not needs:
        needs.append("希望问题得到解决，生活不受影响")
    return needs


def _calculate_confidence(text, symptoms):
    score = 0.5
    if len(text) > 50:
        score += 0.1
    if len(symptoms.get("safety_risks", [])) > 0:
        score += 0.1
    if symptoms.get("frequency") != "unknown":
        score += 0.05
    if symptoms.get("relationship") != "unknown":
        score += 0.05
    return min(score, 0.95)


def _generate_summary(symptoms, risk_level):
    cat_map = {"noise": "噪音", "parking": "停车", "pet": "宠物", "renovation": "装修", "leak": "漏水", "garbage": "卫生", "public_space": "公共区域", "wechat": "微信群", "other": "邻里"}
    freq_map = {"constant": "持续发生", "frequent": "反复发生", "occasional": "偶尔发生", "first_time": "首次发生", "unknown": "发生"}
    rel_map = {"none": "双方尚无接触", "casual": "双方为普通邻里关系", "familiar": "双方较为熟悉", "tense": "双方关系略显紧张", "conflict": "双方曾有冲突", "unknown": ""}
    cat = cat_map.get(symptoms["category"], "邻里")
    freq = freq_map.get(symptoms["frequency"], "")
    rel = rel_map.get(symptoms["relationship"], "")
    parts = [f"这是一个{freq}的{cat}问题"]
    if rel:
        parts.append(rel)
    if risk_level == "green":
        parts.append("目前风险等级较低，适合友好沟通")
    elif risk_level == "yellow":
        parts.append("问题有重复倾向，建议进入结构化沟通流程")
    elif risk_level == "orange":
        parts.append("关系已明显紧张，建议第三方协调")
    elif risk_level == "red":
        parts.append("存在安全风险，请优先保护自身安全")
    return "。".join(parts) + "。"


def _generate_insights(symptoms, risk_level):
    insights = []
    emotions = symptoms.get("emotions", [])
    if "anger" in emotions:
        insights.append("你感到愤怒是正常的，重要的是在沟通前让自己冷静下来")
    if "frustration" in emotions:
        insights.append("反复发生的问题容易让人疲惫，结构化记录能帮助你理清事实")
    if "anxiety" in emotions:
        insights.append("担心表达不当很常见，这正是沟通练习的价值所在")
    if symptoms.get("relationship") in ("tense", "conflict"):
        insights.append("双方已有摩擦，建议避免再次直接交锋")
    if risk_level in ("orange", "red"):
        insights.append("在情绪激动时不适合沟通，建议先稳定情绪")
    return insights


def _generate_key_questions(symptoms):
    questions = []
    if symptoms.get("frequency") in ("unknown", "first_time"):
        questions.append("这是第一次发生，还是之前也出现过类似情况？")
    if symptoms.get("relationship") == "unknown":
        questions.append("你和对方之前沟通过这个问题吗？对方态度如何？")
    if not symptoms.get("safety_risks") and symptoms.get("frequency") not in ("constant", "frequent"):
        questions.append("这件事对你日常生活的具体影响是什么？能举一个例子吗？")
    if len(questions) < 3:
        questions.append("你理想中的解决结果是什么样的？")
    return questions[:3]


def generate_action_plan(risk_level, context=None):
    template = ACTION_TEMPLATES.get(risk_level, ACTION_TEMPLATES["green"])
    return {
        "target": template["target"],
        "steps": template["steps"],
        "don't_do": template["don't_do"],
        "escalation": template["escalation"],
        "safety_reminder": "存在安全风险，建议优先保护自身安全" if risk_level == "red" else None,
    }


def generate_message(template_key, replacements):
    template = MESSAGE_TEMPLATES.get(template_key, MESSAGE_TEMPLATES["wechat_friendly"])
    return "\n".join(template).format(**replacements)


def detect_safety(text):
    risks = detect_safety_risks(text)
    if risks:
        return True, risks
    return False, []
