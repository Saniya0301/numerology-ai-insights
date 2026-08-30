import streamlit as st
from services.numerology import (
    get_full_numerology_profile,
    get_life_path_breakdown,
    calculate_pinnacles,
    calculate_challenges,
    calculate_karmic_lessons,
    calculate_compatibility,
    calculate_maturity_number,
)
from services.gemini_service import (
    generate_life_areas_profile,
    answer_numerology_question,
    generate_compatibility_explanation,
)
from services.report_generator import generate_pdf_report

st.set_page_config(page_title="Numerology AI Insights", page_icon="🔮")

st.title("🔮 Numerology AI Insights")

# --- Session state setup ---
if "profile" not in st.session_state:
    st.session_state.profile = None
if "full_name" not in st.session_state:
    st.session_state.full_name = None
if "day" not in st.session_state:
    st.session_state.day = None
if "month" not in st.session_state:
    st.session_state.month = None
if "year" not in st.session_state:
    st.session_state.year = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "compatibility_result" not in st.session_state:
    st.session_state.compatibility_result = None
if "life_areas" not in st.session_state:
    st.session_state.life_areas = None

main_tab1, main_tab2, main_tab3 = st.tabs(["🔢 My Profile", "💕 Compatibility", "🛍️ Shop"])

# ============================================================
# TAB 1: Individual Profile
# ============================================================
with main_tab1:
    st.write("Enter your details to generate your numerology profile.")

    with st.form("numerology_form"):
        full_name = st.text_input("Full Birth Name")
        col1, col2, col3 = st.columns(3)
        with col1:
            day = st.number_input("Day", min_value=1, max_value=31, step=1)
        with col2:
            month = st.number_input("Month", min_value=1, max_value=12, step=1)
        with col3:
            year = st.number_input("Year", min_value=1900, max_value=2026, step=1)

        submitted = st.form_submit_button("Generate My Profile")

    if submitted:
        if not full_name.strip():
            st.error("Please enter your full name.")
        else:
            st.session_state.profile = get_full_numerology_profile(full_name, day, month, year)
            st.session_state.profile["maturity_number"] = calculate_maturity_number(
                day, month, year, full_name
            )
            st.session_state.full_name = full_name
            st.session_state.day = day
            st.session_state.month = month
            st.session_state.year = year
            st.session_state.chat_history = []
            st.session_state.life_areas = None  # reset so it regenerates below

    if st.session_state.profile:
        profile = st.session_state.profile
        full_name = st.session_state.full_name
        day = st.session_state.day
        month = st.session_state.month
        year = st.session_state.year

        st.subheader("Your Numerology Profile")
        cols = st.columns(3)
        labels = {
            "life_path_number": "Life Path",
            "expression_number": "Expression",
            "soul_urge_number": "Soul Urge",
            "personality_number": "Personality",
            "birthday_number": "Birthday",
            "personal_year_number": "Personal Year",
        }
        display_keys = [k for k in profile.keys() if k != "maturity_number"]
        for i, key in enumerate(display_keys):
            with cols[i % 3]:
                st.metric(labels.get(key, key), profile[key])

        st.divider()
        with st.expander("🔍 How was my Life Path Number calculated?"):
            breakdown = get_life_path_breakdown(day, month, year)
            st.write(f"**Your birth date:** {breakdown['input']}")
            st.write(f"**Day →** {' → '.join(breakdown['day_steps'])}")
            st.write(f"**Month →** {' → '.join(breakdown['month_steps'])}")
            st.write(f"**Year →** {' → '.join(breakdown['year_steps'])}")
            st.write(f"**Sum:** {breakdown['sum_line']}")
            if len(breakdown['final_steps']) > 1:
                st.write(f"**Final reduction:** {' → '.join(breakdown['final_steps'])}")
            st.success(f"**Life Path Number = {breakdown['result']}**")

        st.divider()
        st.subheader("⭐ Your Pinnacle Cycles")
        st.caption("Four life phases, each with a dominant theme to build on.")
        pinnacles = calculate_pinnacles(day, month, year)
        pin_cols = st.columns(4)
        pin_labels = ["1st Pinnacle", "2nd Pinnacle", "3rd Pinnacle", "4th Pinnacle"]
        for i, (key, value) in enumerate(pinnacles.items()):
            with pin_cols[i]:
                st.metric(pin_labels[i], value["number"])
                st.caption(f"Ages {value['age_range']}")

        st.subheader("⚡ Your Challenge Cycles")
        st.caption("Recurring lessons or obstacles across the same life phases.")
        challenges = calculate_challenges(day, month, year)
        chal_cols = st.columns(4)
        chal_labels = ["1st Challenge", "2nd Challenge", "3rd Challenge", "4th Challenge"]
        for i, (key, value) in enumerate(challenges.items()):
            with chal_cols[i]:
                st.metric(chal_labels[i], value["number"])
                st.caption(f"Ages {value['age_range']}")

        st.subheader("🧭 Karmic Lessons")
        karmic_lessons = calculate_karmic_lessons(full_name)
        if karmic_lessons:
            st.write(
                f"These numbers are missing from your name, suggesting traits "
                f"that may need conscious development: **{', '.join(map(str, karmic_lessons))}**"
            )
        else:
            st.write("All numbers 1–9 are present in your name — no missing Karmic Lessons.")

        # --- AI Life Areas (generated once, cached in session state) ---
        if st.session_state.life_areas is None:
            with st.spinner("Generating your personalized life areas..."):
                st.session_state.life_areas = generate_life_areas_profile(full_name, profile)

        life_areas = st.session_state.life_areas

        st.divider()
        st.subheader("✨ Your AI-Powered Life Areas")

        area_tabs = st.tabs([
            "🌟 Overview", "🧠 Personality", "💪 Strengths", "🌱 Challenges",
            "💼 Career", "❤️ Love", "👥 Relationships", "💰 Money",
            "📅 This Year", "🌿 Growth", "🍀 Lucky Elements"
        ])
        area_keys = [
            "Overview", "Personality", "Strengths", "Challenges", "Career",
            "Love", "Relationships", "Money", "This Year's Theme", "Growth",
            "Lucky Elements",
        ]

        for tab, key in zip(area_tabs, area_keys):
            with tab:
                content = life_areas.get(key, "No content generated for this section.")
                st.markdown(content)

        st.caption(
            "Numerology is an interpretive, reflective practice for self-discovery — "
            "not a scientific or predictive science, nor a substitute for professional "
            "medical, legal, or financial advice."
        )

        st.divider()
        # Combine life areas into one text block for the PDF report
        combined_interpretation = "\n\n".join(
            f"## {key}\n{life_areas.get(key, '')}" for key in area_keys
        )
        pdf_bytes = generate_pdf_report(
            full_name, profile, combined_interpretation,
            pinnacles=pinnacles, challenges=challenges, karmic_lessons=karmic_lessons,
        )
        st.download_button(
            label="📄 Download Full PDF Report",
            data=pdf_bytes,
            file_name=f"{full_name.replace(' ', '_')}_numerology_report.pdf",
            mime="application/pdf",
        )

        st.divider()
        st.subheader("💬 Ask Your Numbers")
        st.write("Ask a follow-up question about your profile — career, relationships, this year, anything.")

        for turn in st.session_state.chat_history:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])

        user_question = st.chat_input("Ask something about your numbers...")

        if user_question:
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = answer_numerology_question(
                        full_name, profile, user_question, st.session_state.chat_history[:-1]
                    )
                st.markdown(answer)

            st.session_state.chat_history.append({"role": "assistant", "content": answer})

# ============================================================
# TAB 2: Compatibility Calculator
# ============================================================
with main_tab2:
    st.write("Compare two people's numerology profiles to see how they may complement each other.")

    with st.form("compatibility_form"):
        st.markdown("**Person A**")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            name_a = st.text_input("Full Birth Name (A)", key="name_a")
        with col_a2:
            date_a = st.date_input(
                "Date of Birth (A)", min_value="1900-01-01", key="date_a"
            )

        st.markdown("**Person B**")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            name_b = st.text_input("Full Birth Name (B)", key="name_b")
        with col_b2:
            date_b = st.date_input(
                "Date of Birth (B)", min_value="1900-01-01", key="date_b"
            )

        compat_submitted = st.form_submit_button("Check Compatibility")

    if compat_submitted:
        if not name_a.strip() or not name_b.strip():
            st.error("Please enter both names.")
        else:
            st.session_state.compatibility_result = calculate_compatibility(
                name_a, date_a.day, date_a.month, date_a.year,
                name_b, date_b.day, date_b.month, date_b.year,
            )

    if st.session_state.compatibility_result:
        compat = st.session_state.compatibility_result

        st.divider()
        st.subheader(f"💞 {compat['overall_score']}% Overall Compatibility")
        st.progress(compat["overall_score"] / 100)

        score_cols = st.columns(3)
        with score_cols[0]:
            st.metric("Life Path", f"{compat['life_path_score']}%")
        with score_cols[1]:
            st.metric("Expression", f"{compat['expression_score']}%")
        with score_cols[2]:
            st.metric("Soul Urge", f"{compat['soul_urge_score']}%")

        st.divider()
        with st.spinner("Generating compatibility insight..."):
            explanation = generate_compatibility_explanation(compat)
        st.markdown(explanation)

        st.caption(
            "Numerology compatibility is an interpretive, reflective practice — "
            "not a definitive measure of relationship success or failure."
        )

# ============================================================
# TAB 3: Shop
# ============================================================
with main_tab3:
    st.write(
        "Spiritual tools to support your numerology practice — rudraksha, "
        "crystals, and yantras."
    )
    st.info(
        "📸 Product photos below are placeholders. Real product images will "
        "be added once sourced from suppliers or original photography.",
        icon="ℹ️",
    )

    if "enquiry_product" not in st.session_state:
        st.session_state.enquiry_product = None

    PRODUCTS = {
        "🟤 Rudraksha": [
            {
                "name": "5 Mukhi Rudraksha Bead",
                "price": "₹499",
                "description": "The most common and widely worn rudraksha, "
                                "associated with calm and focus.",
            },
            {
                "name": "Rudraksha Mala (108 Beads)",
                "price": "₹1,899",
                "description": "A traditional strand used for japa meditation "
                                "and daily wear.",
            },
            {
                "name": "1 Mukhi Rudraksha Pendant",
                "price": "₹3,499",
                "description": "A rare single-faced bead, set as a pendant "
                                "for daily wear.",
            },
        ],
        "💎 Crystals": [
            {
                "name": "Amethyst Cluster",
                "price": "₹899",
                "description": "A natural raw cluster, often placed for calm, "
                                "reflective spaces.",
            },
            {
                "name": "Rose Quartz Tumbled Set",
                "price": "₹599",
                "description": "A set of 5 polished stones, popular for "
                                "personal or gifting use.",
            },
            {
                "name": "Clear Quartz Point",
                "price": "₹749",
                "description": "A single terminated point, commonly used in "
                                "personal crystal practice.",
            },
        ],
        "🔺 Yantras": [
            {
                "name": "Sri Yantra (Copper)",
                "price": "₹1,299",
                "description": "A hand-finished copper Sri Yantra for home "
                                "or altar placement.",
            },
            {
                "name": "Numerology Yantra Card",
                "price": "₹349",
                "description": "A compact printed yantra paired with your "
                                "personal number, easy to carry.",
            },
        ],
    }

    for category, items in PRODUCTS.items():
        st.subheader(category)
        cols = st.columns(3)
        for i, product in enumerate(items):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f3ecfa;
                        border-radius: 10px;
                        height: 140px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #9b8bb4;
                        font-size: 13px;
                        margin-bottom: 8px;
                    ">
                        Product Photo<br/>Coming Soon
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{product['name']}**")
                st.write(product["price"])
                st.caption(product["description"])
                if st.button("Enquire", key=f"enquire_{category}_{product['name']}"):
                    st.session_state.enquiry_product = product["name"]
        st.divider()

    # --- Enquiry capture form ---
    if st.session_state.enquiry_product:
        st.subheader(f"📩 Enquire about: {st.session_state.enquiry_product}")
        with st.form("enquiry_form"):
            enquiry_name = st.text_input("Your Name")
            enquiry_contact = st.text_input("Phone or Email")
            enquiry_message = st.text_area("Message (optional)", placeholder="Any specific questions?")
            enquiry_submitted = st.form_submit_button("Submit Enquiry")

        if enquiry_submitted:
            if not enquiry_name.strip() or not enquiry_contact.strip():
                st.error("Please provide your name and a way to contact you.")
            else:
                import csv
                from pathlib import Path
                from datetime import datetime

                leads_file = Path("shop_enquiries.csv")
                is_new_file = not leads_file.exists()
                with open(leads_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if is_new_file:
                        writer.writerow(["timestamp", "product", "name", "contact", "message"])
                    writer.writerow([
                        datetime.now().isoformat(timespec="seconds"),
                        st.session_state.enquiry_product,
                        enquiry_name,
                        enquiry_contact,
                        enquiry_message,
                    ])

                st.success("Thank you! Your enquiry has been recorded — we'll be in touch soon.")
                st.session_state.enquiry_product = None

    st.caption(
        "This shop section is in early setup. Product availability, pricing, "
        "and images are subject to change."
    )