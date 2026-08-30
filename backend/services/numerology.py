"""
Core numerology calculation engine.
All functions here are pure and deterministic — no AI involved.
This module is the source of truth for every numerology number
used elsewhere in the app (Gemini interpretation, RAG, dashboard, etc).
"""

from datetime import datetime

MASTER_NUMBERS = {11, 22, 33}

# Pythagorean letter-to-number mapping (standard Western numerology system)
LETTER_VALUES = {
    'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
    'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
    'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8
}

VOWELS = {'A', 'E', 'I', 'O', 'U'}


def reduce_number(n: int) -> int:
    """
    Reduce a number to a single digit (1-9), unless it's a Master Number
    (11, 22, 33), which is preserved unreduced.
    """
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(digit) for digit in str(n))
    return n


def reduce_number_with_steps(n: int) -> tuple[int, list[str]]:
    """
    Same as reduce_number(), but also returns a list of human-readable
    strings showing each reduction step.
    """
    steps = [f"{n}"]
    while n > 9 and n not in MASTER_NUMBERS:
        digits = [int(d) for d in str(n)]
        new_n = sum(digits)
        digit_expr = " + ".join(str(d) for d in digits)
        steps.append(f"{digit_expr} = {new_n}")
        n = new_n
    return n, steps


def get_life_path_breakdown(day: int, month: int, year: int) -> dict:
    """
    Returns a structured, step-by-step breakdown of the Life Path calculation.
    """
    day_reduced, day_steps = reduce_number_with_steps(day)
    month_reduced, month_steps = reduce_number_with_steps(month)
    year_reduced, year_steps = reduce_number_with_steps(year)

    total = day_reduced + month_reduced + year_reduced
    final, final_steps = reduce_number_with_steps(total)

    return {
        "input": f"{day:02d} / {month:02d} / {year}",
        "day_steps": day_steps,
        "month_steps": month_steps,
        "year_steps": year_steps,
        "sum_line": f"{day_reduced} + {month_reduced} + {year_reduced} = {total}",
        "final_steps": final_steps,
        "result": final,
    }


def calculate_life_path_number(day: int, month: int, year: int) -> int:
    """
    Life Path Number: derived from the full birth date.
    Reduce day, month, year separately, then sum and reduce the total.
    """
    reduced_day = reduce_number(day)
    reduced_month = reduce_number(month)
    reduced_year = reduce_number(year)
    total = reduced_day + reduced_month + reduced_year
    return reduce_number(total)


def calculate_pinnacles(day: int, month: int, year: int) -> dict:
    """
    Pinnacle Cycles: four numbers representing dominant themes across
    different phases of life, along with the age ranges they cover.
    """
    reduced_day = reduce_number(day)
    reduced_month = reduce_number(month)
    reduced_year = reduce_number(year)

    pinnacle_1 = reduce_number(reduced_month + reduced_day)
    pinnacle_2 = reduce_number(reduced_day + reduced_year)
    pinnacle_3 = reduce_number(pinnacle_1 + pinnacle_2)
    pinnacle_4 = reduce_number(reduced_month + reduced_year)

    life_path = calculate_life_path_number(day, month, year)
    life_path_for_age = (
        life_path if life_path <= 9
        else reduce_number(sum(int(d) for d in str(life_path)))
    )
    first_end_age = 36 - life_path_for_age

    return {
        "pinnacle_1": {
            "number": pinnacle_1,
            "age_range": f"Birth – {first_end_age}",
        },
        "pinnacle_2": {
            "number": pinnacle_2,
            "age_range": f"{first_end_age + 1} – {first_end_age + 9}",
        },
        "pinnacle_3": {
            "number": pinnacle_3,
            "age_range": f"{first_end_age + 10} – {first_end_age + 18}",
        },
        "pinnacle_4": {
            "number": pinnacle_4,
            "age_range": f"{first_end_age + 19}+",
        },
    }


def calculate_challenges(day: int, month: int, year: int) -> dict:
    """
    Challenge Numbers: four numbers representing recurring obstacles or
    lessons across the same life phases as the Pinnacles.
    """
    reduced_day = reduce_number(day)
    reduced_month = reduce_number(month)
    reduced_year = reduce_number(year)

    challenge_1 = abs(reduced_month - reduced_day)
    challenge_2 = abs(reduced_day - reduced_year)
    challenge_3 = abs(challenge_1 - challenge_2)
    challenge_4 = abs(reduced_month - reduced_year)

    life_path = calculate_life_path_number(day, month, year)
    life_path_for_age = (
        life_path if life_path <= 9
        else reduce_number(sum(int(d) for d in str(life_path)))
    )
    first_end_age = 36 - life_path_for_age

    return {
        "challenge_1": {
            "number": challenge_1,
            "age_range": f"Birth – {first_end_age}",
        },
        "challenge_2": {
            "number": challenge_2,
            "age_range": f"{first_end_age + 1} – {first_end_age + 9}",
        },
        "challenge_3": {
            "number": challenge_3,
            "age_range": f"{first_end_age + 10} – {first_end_age + 18}",
        },
        "challenge_4": {
            "number": challenge_4,
            "age_range": f"{first_end_age + 19}+",
        },
    }


def _sum_letter_values(name: str, letters_filter=None) -> int:
    """
    Helper: sums numeric values of letters in a name.
    letters_filter: None = all letters, 'vowels' = only vowels,
                     'consonants' = only consonants
    """
    name = name.upper().replace(" ", "")
    total = 0

    for char in name:
        if char not in LETTER_VALUES:
            continue
        if letters_filter == 'vowels' and char not in VOWELS:
            continue
        if letters_filter == 'consonants' and char in VOWELS:
            continue
        total += LETTER_VALUES[char]

    return total


def calculate_expression_number(full_name: str) -> int:
    """
    Expression (Destiny) Number: derived from ALL letters in the full birth name.
    """
    total = _sum_letter_values(full_name, letters_filter=None)
    return reduce_number(total)


def calculate_soul_urge_number(full_name: str) -> int:
    """
    Soul Urge (Heart's Desire) Number: derived from VOWELS only.
    """
    total = _sum_letter_values(full_name, letters_filter='vowels')
    return reduce_number(total)


def calculate_personality_number(full_name: str) -> int:
    """
    Personality Number: derived from CONSONANTS only.
    """
    total = _sum_letter_values(full_name, letters_filter='consonants')
    return reduce_number(total)


def calculate_karmic_lessons(full_name: str) -> list[int]:
    """
    Karmic Lessons: numbers (1-9) that are completely absent from the
    letters of a person's full name.
    """
    name = full_name.upper().replace(" ", "")
    present_numbers = set()

    for char in name:
        if char in LETTER_VALUES:
            present_numbers.add(LETTER_VALUES[char])

    all_numbers = set(range(1, 10))
    missing_numbers = sorted(all_numbers - present_numbers)

    return missing_numbers


# Traditional numerology compatibility groups
COMPATIBILITY_GROUPS = {
    1: "Leader", 8: "Leader",
    2: "Diplomat", 6: "Diplomat",
    3: "Creative", 5: "Creative",
    4: "Thinker", 7: "Thinker",
    9: "Old Soul", 11: "Old Soul", 22: "Old Soul", 33: "Old Soul",
}

# Compatibility scores between groups (percentage), based on traditional
# numerology compatibility patterns. Same-group pairings score highest.
GROUP_COMPATIBILITY_SCORES = {
    ("Leader", "Leader"): 75, ("Leader", "Diplomat"): 70, ("Leader", "Creative"): 65,
    ("Leader", "Thinker"): 60, ("Leader", "Old Soul"): 68,
    ("Diplomat", "Diplomat"): 85, ("Diplomat", "Creative"): 72, ("Diplomat", "Thinker"): 65,
    ("Diplomat", "Old Soul"): 80,
    ("Creative", "Creative"): 80, ("Creative", "Thinker"): 55, ("Creative", "Old Soul"): 70,
    ("Thinker", "Thinker"): 78, ("Thinker", "Old Soul"): 72,
    ("Old Soul", "Old Soul"): 88,
}


def _get_group_score(group_a: str, group_b: str) -> int:
    """Looks up compatibility score between two groups, regardless of order."""
    key = (group_a, group_b)
    if key in GROUP_COMPATIBILITY_SCORES:
        return GROUP_COMPATIBILITY_SCORES[key]
    return GROUP_COMPATIBILITY_SCORES[(group_b, group_a)]


def calculate_compatibility(
    name_a: str, day_a: int, month_a: int, year_a: int,
    name_b: str, day_b: int, month_b: int, year_b: int,
) -> dict:
    """
    Calculates numerology compatibility between two people, based on their
    Life Path, Expression, and Soul Urge numbers. Returns individual
    dimension scores and an overall average.
    """
    life_path_a = calculate_life_path_number(day_a, month_a, year_a)
    life_path_b = calculate_life_path_number(day_b, month_b, year_b)
    expression_a = calculate_expression_number(name_a)
    expression_b = calculate_expression_number(name_b)
    soul_urge_a = calculate_soul_urge_number(name_a)
    soul_urge_b = calculate_soul_urge_number(name_b)

    life_path_score = _get_group_score(
        COMPATIBILITY_GROUPS[life_path_a], COMPATIBILITY_GROUPS[life_path_b]
    )
    expression_score = _get_group_score(
        COMPATIBILITY_GROUPS[expression_a], COMPATIBILITY_GROUPS[expression_b]
    )
    soul_urge_score = _get_group_score(
        COMPATIBILITY_GROUPS[soul_urge_a], COMPATIBILITY_GROUPS[soul_urge_b]
    )

    overall_score = round((life_path_score + expression_score + soul_urge_score) / 3)

    return {
        "person_a": {
            "name": name_a, "life_path": life_path_a,
            "expression": expression_a, "soul_urge": soul_urge_a,
        },
        "person_b": {
            "name": name_b, "life_path": life_path_b,
            "expression": expression_b, "soul_urge": soul_urge_b,
        },
        "life_path_score": life_path_score,
        "expression_score": expression_score,
        "soul_urge_score": soul_urge_score,
        "overall_score": overall_score,
    }


def calculate_birthday_number(day: int) -> int:
    """
    Birthday Number: simply the day of birth, reduced.
    """
    return reduce_number(day)


def calculate_personal_year_number(
    day: int,
    month: int,
    current_year: int
) -> int:
    """
    Personal Year Number: uses birth day + birth month + current year.
    """
    reduced_day = reduce_number(day)
    reduced_month = reduce_number(month)
    reduced_current_year = reduce_number(current_year)
    total = reduced_day + reduced_month + reduced_current_year
    return reduce_number(total)


def calculate_maturity_number(day: int, month: int, year: int, full_name: str) -> int:
    """
    Maturity Number: combines Life Path + Expression numbers, reduced.
    Represents themes that become more prominent later in life, typically
    from the late 30s/40s onward, once early life experiences have been
    more fully integrated.
    """
    life_path = calculate_life_path_number(day, month, year)
    expression = calculate_expression_number(full_name)
    return reduce_number(life_path + expression)


def get_full_numerology_profile(
    full_name: str,
    day: int,
    month: int,
    year: int
) -> dict:
    """
    Main entry point — returns all core V1 numerology numbers for a person.
    """
    current_year = datetime.now().year

    return {
        "life_path_number": calculate_life_path_number(day, month, year),
        "expression_number": calculate_expression_number(full_name),
        "soul_urge_number": calculate_soul_urge_number(full_name),
        "personality_number": calculate_personality_number(full_name),
        "birthday_number": calculate_birthday_number(day),
        "personal_year_number": calculate_personal_year_number(
            day, month, current_year
        ),
    }


if __name__ == "__main__":
    profile = get_full_numerology_profile("Saniya Chhabra", 1, 1, 2003)

    for key, value in profile.items():
        print(f"{key}: {value}")

    print()

    breakdown = get_life_path_breakdown(1, 1, 2003)
    print("Life Path breakdown:")
    for k, v in breakdown.items():
        print(f"  {k}: {v}")

    print("\nPinnacles:")
    pinnacles = calculate_pinnacles(1, 1, 2003)
    for key, value in pinnacles.items():
        print(
            f"  {key}: Number {value['number']}, "
            f"Ages {value['age_range']}"
        )

    print("\nChallenges:")
    challenges = calculate_challenges(1, 1, 2003)
    for key, value in challenges.items():
        print(
            f"  {key}: Number {value['number']}, "
            f"Ages {value['age_range']}"
        )

    print("\nKarmic Lessons:")
    karmic_lessons = calculate_karmic_lessons("Saniya Chhabra")
    if karmic_lessons:
        print(f"  Missing numbers: {karmic_lessons}")
    else:
        print("  None — all numbers 1-9 present in the name")

    print("\nCompatibility Test:")
    compat = calculate_compatibility(
        "Saniya Chhabra", 1, 1, 2003,
        "Rahul Sharma", 15, 6, 2001,
    )
    print(f"  Overall Score: {compat['overall_score']}%")
    print(f"  Life Path: {compat['life_path_score']}%")
    print(f"  Expression: {compat['expression_score']}%")
    print(f"  Soul Urge: {compat['soul_urge_score']}%")

    print("\nMaturity Number:")
    maturity = calculate_maturity_number(1, 1, 2003, "Saniya Chhabra")
    print(f"  Maturity Number: {maturity}")