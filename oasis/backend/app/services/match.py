from app.models import JobPosting, Skill, UserProfile


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def calculate_match_score(
    profile: UserProfile | None,
    skills: list[Skill],
    job: JobPosting,
) -> dict:
    extracted = job.extracted_keywords or {}
    required_skills = set(extracted.get("hard_skills", []))
    user_skills = {skill.skill_name for skill in skills}

    if required_skills:
        matched = {skill for skill in required_skills if skill.lower() in {s.lower() for s in user_skills}}
        skill_score = clamp_score(len(matched) / len(required_skills) * 100)
    else:
        matched = set()
        skill_score = 70

    profile_roles = profile.target_roles if profile else []
    profile_industries = profile.target_industries if profile else []
    job_text = f"{job.job_title} {job.company_type} {job.job_description}".lower()

    experience_hits = sum(1 for role in profile_roles if role.lower() in job_text)
    experience_score = clamp_score(60 + experience_hits * 15)

    domain_hits = sum(1 for domain in profile_industries if domain.lower() in job_text)
    domain_score = clamp_score(55 + domain_hits * 20)

    education_score = 75
    certificate_score = 65

    overall_score = clamp_score(
        skill_score * 0.35
        + experience_score * 0.25
        + education_score * 0.15
        + certificate_score * 0.10
        + domain_score * 0.15
    )

    strengths = []
    weaknesses = []
    suggestions = []

    if matched:
        strengths.append(f"已具備職缺要求技能：{'、'.join(sorted(matched))}。")
    if required_skills - matched:
        missing = "、".join(sorted(required_skills - matched))
        weaknesses.append(f"尚未明確呈現技能：{missing}。")
        suggestions.append(f"建議補上 {missing} 的專案或學習證明。")
    if overall_score >= 75:
        strengths.append("整體適配度良好，可優先投遞並客製化履歷。")
    else:
        suggestions.append("投遞前建議先強化 JD 關鍵字與量化成果。")

    return {
        "overall_score": overall_score,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "certificate_score": certificate_score,
        "domain_score": domain_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
    }
