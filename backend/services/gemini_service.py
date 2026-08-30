"""
Gemini AI interpretation service.
Takes a numerology profile (numbers only), retrieves grounding context
from the knowledge base via RAG, and generates a rich, personalized
interpretation organized into Life Areas — each substantial enough to
stand as its own report page. Also supports follow-up chat questions
and two-person compatibility explanations, all grounded in the same
knowledge base.
"""

import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from services.retriever import retrieve_relevant_context

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = """You are a thoughtful numerology interpreter. You explain
numerology numbers in a warm, reflective, and grounded way — never as guaranteed
predictions or fortune-telling. Use phrases like "may suggest", "often points to",
"can indicate" rather than "will" or "you are definitely".

Base your interpretation primarily on the CONTEXT provided to you, rather than
purely on general knowledge. If the context doesn't fully cover something,
you may reasonably extend it, but stay consistent with the tone and content
of the provided material.

Never give medical, legal, financial, or health-related claims. Frame any
money-related content as numerological interpretation and reflection, not
financial advice.

When given multiple numbers together, look for meaningful relationships and
tensions between them (cross-number reasoning), not just isolated definitions.

Write in full, well-developed paragraphs — not single sentences or bullet
fragments — since this content is used in a formal personal report."""

# Ordered list of section titles the app expects back from the AI
LIFE_AREA_SECTIONS = [
    "Overview", "Personality", "Strengths", "Challenges", "Career",
    "Love", "Relationships", "Money", "This Year's Theme", "Growth",
    "Lucky Elements",
]


def _build_retrieval_query(profile: dict) -> str:
    """Builds a search query covering all the person's numbers, to retrieve
    relevant knowledge base content for each of them."""
    return (
        f"Life Path {profile['life_path_number']}, "
        f"Expression {profile['expression_number']}, "
        f"Soul Urge {profile['soul_urge_number']}, "
        f"Personality {profile['personality_number']}"
    )


def _parse_life_areas(text: str) -> dict:
    """
    Splits AI output (with ## Area headers) into a dict of
    {area_name: area_text}.
    """
    parts = re.split(r"\n?##\s*", text)
    sections = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        sections[title] = body
    return sections


def generate_life_areas_profile(full_name: str, profile: dict) -> dict:
    """
    Given a person's name and their calculated numerology profile,
    retrieve relevant knowledge base context, then generate a rich,
    personalized interpretation organized into 11 Life Areas, each
    substantial enough to form its own report page. Returns a dict
    keyed by section name.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    retrieval_query = _build_retrieval_query(profile)
    context = retrieve_relevant_context(retrieval_query, k=8)

    # Dedicated extra retrieval for Career, since career guidance draws
    # specifically on Destiny (Expression) and Personality numbers rather
    # than the full profile — this pulls from the career/ knowledge base
    # files directly instead of relying on the general context above.
    career_query = (
        f"career fields for number {profile['expression_number']} "
        f"and number {profile['personality_number']}"
    )
    career_context = retrieve_relevant_context(career_query, k=6)

    # Dedicated retrieval for Love & Relationships, grounded in Soul Urge
    # (inner desires) and Life Path (core approach to relationships).
    relationships_query = (
        f"romantic relationships and family dynamics for number "
        f"{profile['soul_urge_number']} and number {profile['life_path_number']}"
    )
    relationships_context = retrieve_relevant_context(relationships_query, k=6)

    # Dedicated retrieval for Money, grounded in Life Path and Soul Urge
    # (core mindset and inner motivations around money).
    money_query = (
        f"money and finance mindset for number {profile['life_path_number']} "
        f"and number {profile['soul_urge_number']}"
    )
    money_context = retrieve_relevant_context(money_query, k=6)

    # Dedicated retrieval for Personality (day-to-day traits), Strengths,
    # and Challenges — all grounded primarily in Life Path Number.
    traits_query = f"day-to-day personality traits for Life Path {profile['life_path_number']}"
    traits_context = retrieve_relevant_context(traits_query, k=5)

    strengths_query = f"core strengths for Life Path {profile['life_path_number']}"
    strengths_context = retrieve_relevant_context(strengths_query, k=5)

    challenges_query = f"growth challenges for Life Path {profile['life_path_number']}"
    challenges_context = retrieve_relevant_context(challenges_query, k=5)

    prompt = f"""CONTEXT (from the numerology knowledge base):
{context}

CAREER-SPECIFIC CONTEXT (use this specifically for the Career section):
{career_context}

LOVE & RELATIONSHIPS-SPECIFIC CONTEXT (use this specifically for the Love and Relationships sections):
{relationships_context}

MONEY-SPECIFIC CONTEXT (use this specifically for the Money section):
{money_context}

PERSONALITY TRAITS CONTEXT (use this specifically for the Personality section):
{traits_context}

STRENGTHS-SPECIFIC CONTEXT (use this specifically for the Strengths section):
{strengths_context}

CHALLENGES-SPECIFIC CONTEXT (use this specifically for the Challenges section):
{challenges_context}

---

Generate a detailed numerology interpretation for {full_name}, organized
into distinct Life Areas for a formal personal report.

Their numbers:
- Life Path Number: {profile['life_path_number']}
- Expression (Destiny) Number: {profile['expression_number']}
- Soul Urge Number: {profile['soul_urge_number']}
- Personality Number: {profile['personality_number']}
- Birthday Number: {profile['birthday_number']}
- Personal Year Number: {profile['personal_year_number']}
- Maturity Number: {profile.get('maturity_number', 'N/A')}

Structure your response with EXACTLY these section headers, in this order:

## Overview
## Personality
## Strengths
## Challenges
## Career
## Love
## Relationships
## Money
## This Year's Theme
## Growth
## Lucky Elements

Length and depth guidance per section:

- "Overview": 4-5 sentences weaving together Life Path, Expression, Soul
  Urge, and Personality into a cohesive introduction.
- "Personality": 2 full paragraphs, grounded primarily in the
  PERSONALITY TRAITS CONTEXT above — on how this person shows up
  day-to-day.
- "Strengths": 2 full paragraphs, grounded primarily in the
  STRENGTHS-SPECIFIC CONTEXT above — on their core natural strengths,
  with concrete examples of how these show up in daily life.
- "Challenges": 2 full paragraphs, grounded primarily in the
  CHALLENGES-SPECIFIC CONTEXT above — on growth edges and recurring
  patterns to watch for, framed constructively.
- "Career": 3 full paragraphs, grounded primarily in the CAREER-SPECIFIC
  CONTEXT above — natural work strengths tied to their Expression and
  Personality numbers, 4-6 specific career fields or environments drawn
  from that context with reasoning, and ideal working style (independent
  vs collaborative, structured vs flexible). Note where Destiny (natural
  talent) and Personality (how they're perceived professionally) point in
  the same direction or create interesting nuance.
- "Love": 3 full paragraphs, grounded primarily in the LOVE &
  RELATIONSHIPS-SPECIFIC CONTEXT above — how they approach romantic
  relationships, what they need from a partner, and their growth edge in
  love specifically.
- "Relationships": 2 full paragraphs, grounded primarily in the LOVE &
  RELATIONSHIPS-SPECIFIC CONTEXT above — on friendships and family
  dynamics, distinct from the romantic focus of the Love section.
- "Money": 2 full paragraphs, grounded primarily in the MONEY-SPECIFIC
  CONTEXT above — natural money mindset, earning tendencies, and
  spending/saving patterns — framed as numerological reflection only.
- "This Year's Theme": 2 full paragraphs on their current Personal Year
  and what it may bring.
- "Growth": 2 full paragraphs, using the Maturity Number, on what themes
  become more prominent later in life (late 30s/40s onward).
- "Lucky Elements": a short list — 2-3 lucky numbers, 2-3 colors, and one
  lucky day of the week, traditionally associated with their Life Path and
  Expression numbers. Keep this section brief and light in tone.

Ground every section in the CONTEXT above (Career in the CAREER-SPECIFIC
CONTEXT, Love and Relationships in the LOVE & RELATIONSHIPS-SPECIFIC
CONTEXT, Money in the MONEY-SPECIFIC CONTEXT, Personality in the
PERSONALITY TRAITS CONTEXT, Strengths in the STRENGTHS-SPECIFIC CONTEXT,
and Challenges in the CHALLENGES-SPECIFIC CONTEXT). Write in full,
flowing paragraphs (not bullet points, except in Lucky Elements). Avoid
repeating the same phrasing across sections — each should feel distinct."""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(max_output_tokens=8192),
    )
    return _parse_life_areas(response.text)


def answer_numerology_question(full_name: str, profile: dict, question: str, chat_history: list = None) -> str:
    """
    Answers a follow-up question about the person's numerology profile.
    Retrieves relevant knowledge base context based on the question itself,
    and keeps the person's numbers in context so they don't need to repeat them.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    context = retrieve_relevant_context(question, k=5)

    history_text = ""
    if chat_history:
        for turn in chat_history:
            history_text += f"{turn['role'].capitalize()}: {turn['content']}\n"

    prompt = f"""CONTEXT (from the numerology knowledge base):
{context}

---

You are answering a follow-up question for {full_name}, who already has this
numerology profile:
- Life Path Number: {profile['life_path_number']}
- Expression (Destiny) Number: {profile['expression_number']}
- Soul Urge Number: {profile['soul_urge_number']}
- Personality Number: {profile['personality_number']}
- Birthday Number: {profile['birthday_number']}
- Personal Year Number: {profile['personal_year_number']}

{f"Previous conversation:{chr(10)}{history_text}" if history_text else ""}

Their question: {question}

Answer conversationally in 2-4 sentences, grounded in the CONTEXT above and
their specific numbers. Don't re-explain their whole profile unless relevant
to the question — just answer directly."""

    response = model.generate_content(prompt)
    return response.text


def generate_compatibility_explanation(compatibility_data: dict) -> str:
    """
    Given a compatibility result (two people's numbers + scores), retrieve
    relevant compatibility knowledge base content and generate an AI
    explanation of why the pairing works the way it does.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    person_a = compatibility_data["person_a"]
    person_b = compatibility_data["person_b"]

    retrieval_query = (
        f"compatibility between Life Path {person_a['life_path']} and "
        f"Life Path {person_b['life_path']}"
    )
    context = retrieve_relevant_context(retrieval_query, k=6)

    prompt = f"""CONTEXT (from the numerology compatibility knowledge base):
{context}

---

Generate a numerology compatibility explanation for two people:

{person_a['name']}:
- Life Path: {person_a['life_path']}
- Expression: {person_a['expression']}
- Soul Urge: {person_a['soul_urge']}

{person_b['name']}:
- Life Path: {person_b['life_path']}
- Expression: {person_b['expression']}
- Soul Urge: {person_b['soul_urge']}

Calculated Scores:
- Life Path Compatibility: {compatibility_data['life_path_score']}%
- Expression Compatibility: {compatibility_data['expression_score']}%
- Soul Urge Compatibility: {compatibility_data['soul_urge_score']}%
- Overall Score: {compatibility_data['overall_score']}%

Structure your response with these sections, using markdown headers:
## Why This Pairing Works
## Potential Friction Points
## Advice for This Pairing

Keep each section to 2-3 sentences. Ground your explanation in the CONTEXT
above. Be balanced — don't oversell the match if the scores are moderate,
and don't be overly negative if scores are lower — frame everything as
reflective insight, not a verdict on the relationship's worth."""

    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    # quick manual test — requires GOOGLE_API_KEY in .env
    test_profile = {
        "life_path_number": 7,
        "expression_number": 11,
        "soul_urge_number": 4,
        "personality_number": 7,
        "birthday_number": 1,
        "personal_year_number": 3,
        "maturity_number": 9,
    }
    result = generate_life_areas_profile("Saniya Chhabra", test_profile)
    for area, content in result.items():
        print(f"\n=== {area} ===")
        print(content)
        print(f"[{len(content.split())} words]")