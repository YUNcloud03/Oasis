ZH_TW_RULE = """
你是熟悉台灣職場語境的 OASIS AI 職涯助理。所有輸出都必須使用繁體中文 zh-TW，
用台灣常見履歷、求職信與企業表單用語，避免中國大陸用語與簡體字。
日期、地址、職稱、學經歷描述需符合台灣求職市場習慣。
"""

NO_FABRICATION_RULE = """
事實安全規則：
- 只能使用使用者背景、JD、補答 supplements 中明確提供的資訊。
- 不可捏造公司、學校、證照、專案、年份、成果或數字。
- 有明確數字就使用原數字；沒有數字時，不可自行估算，請在該句或 bullet 標記「⚠️ 建議補量化成果」。
- 若需要補資料，請用提問或提醒呈現，不要把未知資訊寫成已發生事實。
"""

TONE_RULE = """
語氣調整：
- 根據 JD 與公司文化訊號調整語氣。大型企業、金融、顧問：正式穩健；新創、產品、行銷：清楚有主動性；設計、內容：保留創意但維持專業。
- 若 JD 強調 ownership / impact / data-driven，內容需凸顯主動性、成果與資料證據。
- 若 JD 強調 collaboration / communication，內容需凸顯跨部門溝通與利害關係人協作。
"""

OUTPUT_FORMAT_RULE = """
輸出格式規則（產生履歷正文時必須遵守）：
- 背景項目的 ID 標籤（例如 [education-1]、[courses-2]、[experiences-1]）只是給你內部對應使用，不要把它們寫進履歷正文。
- 履歷正文不要出現任何方括號 ID、不要保留來源標記，讀起來要像一份成品履歷。
- 補答內容（supplements）也是同樣處理，整合進敘述即可，不要保留 requirement_id / background_id 這類標記。
- 只在「對齊說明」段落可以引用 JD 的需求名稱說明對應關係，不要透露 ID 系統。
"""

BACKGROUND_SECTION_LABELS = {
    "education": "學歷",
    "courses": "修過的課",
    "experiences": "工作經驗",
    "projects": "專案",
    "certifications": "證照",
    "languages": "語言",
    "others": "其他",
}

SECTION_SPECS = {
    "self_intro": ("自我介紹", "default：80-150 字，聚焦和 JD 最相關的 2-3 個亮點"),
    "motivation": ("應徵動機", "default：120-180 字，連結公司/職務需求與個人背景"),
    "education": ("學歷", "default：列出最相關學歷與課程，每項 1-2 行"),
    "experience": ("工作經驗", "default：每段經歷 2-4 個 bullet，優先 STAR 與成果"),
    "projects": ("專案", "default：2-3 個 bullet，凸顯技術、行動、成果"),
    "skills": ("技能", "default：依 JD 分組列出硬技能/軟技能"),
    "certifications": ("證照", "default：列出與職務相關證照"),
    "languages": ("語言", "default：列出語言與程度"),
    "custom": ("自訂區塊", "default：依使用者指定主題撰寫"),
}


def format_background(structured) -> str:
    """Convert structured background into ID-addressable markdown.

    Expected:
    {
      "education": [{"id": "education-1", "name": "...", "description": "..."}],
      "courses": [{"id": "courses-1", "name": "...", "description": "..."}],
      ...
    }
    """
    if not structured:
        return ""
    if isinstance(structured, str):
        return structured.strip()

    parts: list[str] = []
    for key, label in BACKGROUND_SECTION_LABELS.items():
        items = structured.get(key) or []
        valid_items = [item for item in items if isinstance(item, dict) and (item.get("name") or "").strip()]
        if not valid_items:
            continue
        parts.append(f"## {label}")
        for index, item in enumerate(valid_items, 1):
            item_id = (item.get("id") or f"{key}-{index}").strip()
            name = (item.get("name") or "").strip()
            description = (item.get("description") or item.get("summary") or "").strip()
            line = f"- [{item_id}] **{name}**"
            if description:
                line += f"：{description}"
            parts.append(line)
        parts.append("")
    return "\n".join(parts).strip()


def _format_section_briefs(sections: list[str], custom_section: str = "", length_overrides: dict | None = None) -> str:
    length_overrides = length_overrides or {}
    rows = []
    for index, key in enumerate(sections or ["self_intro", "experience", "projects", "skills"], 1):
        label, default_spec = SECTION_SPECS.get(key, (key, "default：依內容重要性控制篇幅"))
        if key == "custom" and custom_section:
            label = custom_section
        spec = length_overrides.get(key) or default_spec
        rows.append(f"{index}. **{label}**：{spec}")
    return "\n".join(rows)


def _format_supplements(supplements: list[dict] | None) -> str:
    if not supplements:
        return ""
    rows = []
    for item in supplements:
        answer = (item.get("user_answer") or item.get("answer") or "").strip()
        if not answer:
            continue
        requirement_id = (item.get("requirement_id") or "").strip()
        background_id = (item.get("background_id") or "").strip()
        rows.append(f"- requirement={requirement_id}; background={background_id}; 補答：{answer}")
    if not rows:
        return ""
    return "## 使用者針對 JD implicit 問題的補答（生成時優先採用）\n" + "\n".join(rows)


def build_match_prompt(*, structured_background=None, background=None, target_role: str = "", company: str = "", jd: str = ""):
    bg_text = format_background(structured_background if structured_background is not None else background)
    system = f"""
{ZH_TW_RULE}
你要分析 JD 與使用者結構化背景的匹配狀況，輸出必須是合法 JSON，不要包 markdown code fence。
請辨識 direct / implicit / gap：
- direct：背景已明確證明符合要求。
- implicit：背景可能相關，但需要使用者補充證據或量化成果。
- gap：背景中找不到可支撐的材料。
{NO_FABRICATION_RULE}
"""
    user = f"""
目標職務：{target_role or "未指定"}
公司：{company or "未指定"}

JD：
{jd}

結構化背景：
{bg_text or "使用者尚未提供背景。"}

請輸出 JSON：
{{
  "jd_summary": "1-2 句 JD 摘要",
  "tone_inference": "根據 JD 推測公司文化與履歷語氣",
  "key_requirements": [
    {{"id": "R1", "text": "需求文字", "type": "hard_skill | soft_skill | experience | education | culture"}}
  ],
  "direct": [
    {{"requirement_id": "R1", "background_id": "projects-1", "background_name": "名稱", "rationale": "為什麼直接符合"}}
  ],
  "implicit": [
    {{"requirement_id": "R2", "background_id": "experiences-1", "background_name": "名稱", "rationale": "可能符合但證據不足", "supplement_question": "請使用者補答的具體問題"}}
  ],
  "gap": [
    {{"requirement_id": "R3", "note": "缺口說明", "suggested_action": "補強建議"}}
  ],
  "supplement_questions": [
    {{"requirement_id": "R2", "background_id": "experiences-1", "question": "具體補答問題"}}
  ],
  "encouragement": "一句繁中鼓勵"
}}
"""
    return system, user


def build_resume_prompt(
    *,
    background,
    target_role: str = "",
    company: str = "",
    jd: str = "",
    sections: list[str] | None = None,
    custom_section: str = "",
    length_overrides: dict | None = None,
    supplements: list[dict] | None = None,
    target_style: str = "formal",
):
    bg_text = format_background(background)
    section_briefs = _format_section_briefs(sections or [], custom_section, length_overrides)
    supplements_text = _format_supplements(supplements)
    system = f"""
{ZH_TW_RULE}
你要根據結構化背景、JD、使用者補答，生成可直接放入台灣求職履歷/表單的內容。
{NO_FABRICATION_RULE}
{TONE_RULE}
{OUTPUT_FORMAT_RULE}
若有 supplements，代表使用者已補答 JD implicit 問題，必須優先採用並整合進最相關區塊。
每個區塊需遵守使用者提供的篇幅控制；未提供則使用 default。
輸出尾端必須附上「📌 對齊說明」，用 3-5 點說明內容如何對齊 JD。
"""
    user = f"""
目標職務：{target_role or "未指定"}
公司：{company or "未指定"}
目標語氣：{target_style}

JD：
{jd or "未提供 JD，請根據目標職務與背景保守撰寫。"}

結構化背景：
{bg_text or "使用者尚未提供完整背景。"}

{supplements_text}

請生成下列履歷區塊：
{section_briefs}
"""
    return system, user


def build_one_page_prompt(*, background, target_role: str = "", company: str = "", jd: str = "", supplements=None):
    system = f"{ZH_TW_RULE}\n{NO_FABRICATION_RULE}\n{TONE_RULE}\n{OUTPUT_FORMAT_RULE}"
    user = f"""
請根據職缺相關性取捨資訊，生成一頁式 CV。未提供數字時標記「⚠️ 建議補量化成果」。

目標職務：{target_role or "未指定"}
公司：{company or "未指定"}
JD：{jd or "未提供"}

結構化背景：
{format_background(background)}

{_format_supplements(supplements)}

輸出結構：
## 履歷標題
## 3 行職涯摘要
## 核心技能
## 精選經歷
## 精選專案
## 學歷、證照與語言
## 📌 對齊說明
"""
    return system, user


def build_star_prompt(*, background, target_role: str = "", jd: str = ""):
    system = f"{ZH_TW_RULE}\n{NO_FABRICATION_RULE}\n{OUTPUT_FORMAT_RULE}"
    user = f"""
請從下列背景中挑選最適合目標職務與 JD 的經歷，改寫為 STAR 架構。

目標職務：{target_role or "未指定"}
JD：{jd or "未提供"}

背景：
{format_background(background)}

輸出：
## Situation
## Task
## Action
## Result
## 履歷 bullet 版本
## 還需要補充的量化問題
"""
    return system, user


def build_convert_translate_prompt(*, original_resume, from_domain: str = "", to_domain: str = "", target_jd: str = "", background=""):
    system = f"{ZH_TW_RULE}\n{NO_FABRICATION_RULE}\n{TONE_RULE}\n{OUTPUT_FORMAT_RULE}"
    user = f"""
請將原履歷轉換為新領域可用的繁體中文版本，不只是翻譯詞彙，而是重新框定經驗價值。

原領域：{from_domain or "未指定"}
目標領域：{to_domain or "未指定"}
目標 JD：{target_jd or "未提供"}

原履歷：
{original_resume}

可參考背景：
{format_background(background)}

請輸出轉換後履歷，尾端附「📌 對齊說明」。
"""
    return system, user


def build_convert_rewrite_prompt(*, background, original_resume, from_domain: str = "", to_domain: str = "", target_jd: str = ""):
    system = f"{ZH_TW_RULE}\n{NO_FABRICATION_RULE}\n{TONE_RULE}\n{OUTPUT_FORMAT_RULE}"
    user = f"""
請根據結構化背景重寫原履歷，使它更適合目標領域與 JD。不可加入背景沒有的事實。

原領域：{from_domain or "未指定"}
目標領域：{to_domain or "未指定"}
目標 JD：{target_jd or "未提供"}

結構化背景：
{format_background(background)}

原履歷：
{original_resume}

請輸出重寫版本，尾端附「📌 對齊說明」。
"""
    return system, user


def build_convert_prompt(text: str, mode: str, target_role: str = "", jd: str = ""):
    if mode == "translate":
        return build_convert_translate_prompt(original_resume=text, to_domain=target_role, target_jd=jd)
    return build_convert_rewrite_prompt(background="", original_resume=text, to_domain=target_role, target_jd=jd)
