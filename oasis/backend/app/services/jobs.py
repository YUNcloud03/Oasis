KEYWORD_DICTIONARY = {
    "hard_skills": [
        "Python",
        "SQL",
        "Excel",
        "Tableau",
        "Power BI",
        "React",
        "Next.js",
        "FastAPI",
        "資料視覺化",
        "機器學習",
    ],
    "soft_skills": [
        "跨部門溝通",
        "需求訪談",
        "專案管理",
        "簡報",
        "英文",
        "團隊合作",
        "問題解決",
    ],
    "domains": ["金融", "半導體", "電商", "SaaS", "行銷", "產品", "資料分析"],
}


def extract_job_keywords(text: str) -> dict[str, list[str]]:
    lower_text = text.lower()
    return {
        group: [keyword for keyword in keywords if keyword.lower() in lower_text]
        for group, keywords in KEYWORD_DICTIONARY.items()
    }


def build_ideal_candidate_profile(keywords: dict[str, list[str]]) -> dict:
    hard_skills = keywords.get("hard_skills", [])
    soft_skills = keywords.get("soft_skills", [])
    domains = keywords.get("domains", [])
    return {
        "summary": "能將職缺要求轉化為具體成果證明，並用繁體中文清楚呈現價值的候選人。",
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "domain_signals": domains,
        "resume_focus": [
            "用 STAR 架構描述成果",
            "補上量化指標",
            "將技能與職缺關鍵字對齊",
        ],
    }
