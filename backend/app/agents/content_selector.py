from app.agents.state import ResumeState

WORD_BUDGET = 450
MIN_SCORE = 0.40
MAX_PROJECTS = 3
MAX_SKILL_CATEGORIES = 6
MAX_SKILLS_PER_CATEGORY = 6
MAX_EXPERIENCE_BULLETS = 6


async def content_selector(state: ResumeState) -> ResumeState:
    scored_chunks = state["scored_chunks"]

    selected: dict = {
        "projects": [],
        "experiences": [],
        "skills": [],
        "education": [],
    }
    word_count = 0

    # Separate chunks by type
    projects = [c for c in scored_chunks if c["type"] == "project" and c["final_score"] >= MIN_SCORE]
    experiences = [c for c in scored_chunks if c["type"] == "experience" and c["final_score"] >= MIN_SCORE]
    skills = [c for c in scored_chunks if c["type"] == "skill"]
    education = [c for c in scored_chunks if c["type"] == "education"]

    # Select projects (greedy by score, respect budget)
    for chunk in projects[:MAX_PROJECTS]:
        chunk_words = chunk.get("word_count", len(chunk["content"].split()))
        if word_count + chunk_words <= WORD_BUDGET:
            selected["projects"].append(chunk)
            word_count += chunk_words

    # Select experience bullets (greedy)
    bullet_count = 0
    for chunk in experiences:
        if bullet_count >= MAX_EXPERIENCE_BULLETS:
            break
        chunk_words = chunk.get("word_count", len(chunk["content"].split()))
        if word_count + chunk_words <= WORD_BUDGET:
            selected["experiences"].append(chunk)
            word_count += chunk_words
            bullet_count += 1

    # Select skills (by category, score threshold 0.5)
    skill_by_category: dict[str, list] = {}
    for chunk in skills:
        if chunk["final_score"] < 0.50:
            continue
        category = chunk.get("metadata", {}).get("category", "General")
        skill_by_category.setdefault(category, []).append(chunk)

    for category, cat_chunks in list(skill_by_category.items())[:MAX_SKILL_CATEGORIES]:
        top_skills = sorted(cat_chunks, key=lambda x: x["final_score"], reverse=True)[:MAX_SKILLS_PER_CATEGORY]
        selected["skills"].extend(top_skills)

    # Always include education (no score filter — always relevant)
    selected["education"] = education

    return {**state, "selected_content": selected, "total_word_count": word_count}
