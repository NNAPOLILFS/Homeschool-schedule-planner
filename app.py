# homeschool_planner_v0_3.py
# Version 0.3 – Compact subject entry layout (horizontal fields)

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- Helper Data ---
PASTEL_COLORS = ["#FFD6A5", "#FFB5E8", "#B5EAD7", "#C7CEEA", "#FFDAC1", "#E2F0CB"]
EMOJIS = ["📚", "🧮", "🧠", "✏️", "🌍", "🔬", "🎨", "🎵", "🦋", "🌈", "💡"]

# --- Page Config ---
st.set_page_config("Homeschool Planner v0.3", layout="wide")
st.title("🎓 Homeschool Planner v0.3")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Setup")

    # Children
    children_input = st.text_input("Enter children's names (comma separated)", "Winter, Micah")
    children = [c.strip() for c in children_input.split(",") if c.strip()]

    # Time settings
    start_time_str = st.time_input("Day start time", value=datetime.strptime("07:00", "%H:%M").time())
    increment = st.selectbox("Schedule increment (minutes)", [15, 30, 60], index=2)

    # Subjects per child
    st.subheader("Subjects")

    if "subjects" not in st.session_state:
        st.session_state.subjects = {kid: [] for kid in children}

    # Reset if children changed
    if set(st.session_state.subjects.keys()) != set(children):
        st.session_state.subjects = {kid: [] for kid in children}

    for kid in children:
        st.markdown(f"**{kid}**")
        cols = st.columns(3)
        for i, col in enumerate(cols):
            pass  # spacing for consistency

        # Preload two subjects per child
        if not st.session_state.subjects[kid]:
            st.session_state.subjects[kid] = [
                {"name": "", "sessions": 0, "length": 60, "shared": False},
                {"name": "", "sessions": 0, "length": 60, "shared": False},
            ]

        new_subjects = []
        for i, subj in enumerate(st.session_state.subjects[kid]):
            col1, col2, col3 = st.columns([2, 1, 1])
            subj["name"] = col1.text_input(f"{kid} Subject {i+1}", subj["name"], key=f"{kid}_subj_{i}_name")
            subj["sessions"] = col2.number_input("Sessions", min_value=0, max_value=10, value=subj["sessions"], key=f"{kid}_subj_{i}_sessions")
            subj["length"] = col3.number_input("Length", min_value=increment, max_value=180, value=subj["length"], step=increment, key=f"{kid}_subj_{i}_length")
            subj["shared"] = st.checkbox("Shared", value=subj["shared"], key=f"{kid}_subj_{i}_shared")
            new_subjects.append(subj)
        st.session_state.subjects[kid] = new_subjects

    # Fixed commitments
    st.subheader("Fixed Commitments")
    use_commitments = st.checkbox("Add fixed commitments?")

    if use_commitments:
        if "commitments" not in st.session_state:
            st.session_state.commitments = {kid: [] for kid in children}

        if set(st.session_state.commitments.keys()) != set(children):
            st.session_state.commitments = {kid: [] for kid in children}

        for kid in children:
            st.markdown(f"**{kid}**")
            day = st.selectbox(f"{kid} Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], key=f"{kid}_day")
            time = st.time_input(f"{kid} Time", value=start_time_str, key=f"{kid}_time")
            label = st.text_input(f"{kid} Commitment name", key=f"{kid}_label")
            if st.button(f"Add {kid} Commitment", key=f"add_{kid}"):
                st.session_state.commitments[kid].append({"day": day, "time": time, "label": label})
    else:
        st.session_state.commitments = {kid: [] for kid in children}

    autofill = st.button("📅 Autofill Schedule")

# --- Schedule Generation ---
def generate_schedule(subjects, commitments, children, start_time, increment):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule = {day: [] for day in days}
    unscheduled = []

    for kid in children:
        for subj in subjects[kid]:
            if subj["sessions"] <= 0 or not subj["name"]:
                continue

            emoji = random.choice(EMOJIS)
            color = random.choice(PASTEL_COLORS)

            possible_days = days.copy()
            for _ in range(subj["sessions"]):
                if not possible_days:
                    possible_days = days.copy()
                day = possible_days.pop(0)
                time = datetime.combine(datetime.today(), start_time)
                label = f"{emoji} {subj['name']}"

                schedule[day].append({
                    "kid": kid,
                    "time": time.strftime("%H:%M"),
                    "length": subj["length"],
                    "label": label,
                    "color": color,
                    "shared": subj["shared"]
                })
    return schedule, unscheduled

# --- Autofill & Display ---
if autofill:
    schedule, unscheduled = generate_schedule(st.session_state.subjects, st.session_state.commitments, children, start_time_str, increment)

    st.subheader("Weekly Schedule")

    for day, items in schedule.items():
        st.markdown(f"### {day}")
        if not items:
            st.info("No sessions scheduled.")
            continue
        df = pd.DataFrame(items)
        df = df.sort_values(by="time")
        for _, row in df.iterrows():
            st.markdown(
                f"<div style='background-color:{row.color};padding:6px;border-radius:8px;margin-bottom:4px;'>"
                f"<b>{row.time}</b> — {row.label} ({row.kid})</div>",
                unsafe_allow_html=True
            )

    if unscheduled:
        st.warning("Some subjects couldn’t be scheduled:")
        for u in unscheduled:
            st.write(f"- {u}")
