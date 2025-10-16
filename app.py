import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Homeschool Planner Builder", layout="wide")

st.title("📘 Homeschool Planner Builder")
st.caption("Prototype Master Version — stable baseline. Do not modify without explicit instruction.")

# Pastel colour palette for subjects
PASTEL_COLOURS = [
    "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
    "#D7BAFF", "#FFBADD", "#FFD6BA", "#B5EAD7", "#E2F0CB"
]

# --- Sidebar (top bar style container simulation) ---
with st.container():
    st.subheader("👧 Children Setup")
    num_children = st.number_input("Number of Children", 1, 5, 2, key="num_children")

    if "children" not in st.session_state:
        st.session_state.children = [f"Child {i+1}" for i in range(num_children)]
    else:
        if len(st.session_state.children) != num_children:
            st.session_state.children = [f"Child {i+1}" for i in range(num_children)]

    for i in range(num_children):
        st.session_state.children[i] = st.text_input(f"Name of Child {i+1}", st.session_state.children[i])

st.markdown("---")

# --- Subject Setup ---
st.subheader("📚 Subject Setup")

if "subjects" not in st.session_state:
    st.session_state.subjects = {}

for child in st.session_state.children:
    st.write(f"**{child}**")
    cols = st.columns(2)
    with cols[0]:
        num_subjects = st.number_input(f"How many subjects for {child}?", 1, 8, 3, key=f"num_subj_{child}")
    with cols[1]:
        num_sessions = st.number_input(f"How many total sessions across week for {child}?", 1, 20, 5, key=f"num_sess_{child}")

    subjects = []
    for s in range(num_subjects):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        subj_name = st.text_input(f"Subject {s+1} name for {child}", f"Subject {s+1}", key=f"{child}_subj_{s}_name")
        subj_time = st.time_input(f"Start time for {subj_name}", key=f"{child}_subj_{s}_time")
        subj_duration = st.number_input(f"Duration (min) for {subj_name}", 15, 180, 45, key=f"{child}_subj_{s}_dur")
        shared = st.checkbox("Shared", key=f"{child}_subj_{s}_shared")
        subjects.append({
            "name": subj_name,
            "time": subj_time,
            "duration": subj_duration,
            "shared": shared,
            "colour": random.choice(PASTEL_COLOURS)
        })
    st.session_state.subjects[child] = {"subjects": subjects, "sessions": num_sessions}

st.markdown("---")

# --- Schedule Generation ---
st.subheader("📅 Weekly Schedule Preview")

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

schedule = []
for child in st.session_state.children:
    child_data = st.session_state.subjects.get(child, {})
    subjects = child_data.get("subjects", [])
    num_sessions = child_data.get("sessions", 5)

    if not subjects:
        continue

    # Distribute sessions across days
    for i in range(num_sessions):
        day = days[i % len(days)]
        subj = subjects[i % len(subjects)]
        schedule.append({
            "Child": child,
            "Day": day,
            "Subject": subj["name"],
            "Start Time": subj["time"].strftime("%H:%M"),
            "Duration (min)": subj["duration"],
            "Shared": "Yes" if subj["shared"] else "No",
            "Colour": subj["colour"]
        })

df = pd.DataFrame(schedule)
if not df.empty:
    for day in days:
        st.write(f"### {day}")
        day_df = df[df["Day"] == day]
        cols = st.columns(len(st.session_state.children))
        for idx, child in enumerate(st.session_state.children):
            with cols[idx]:
                st.markdown(f"**{child}**")
                child_df = day_df[day_df["Child"] == child]
                for _, row in child_df.iterrows():
                    st.markdown(
                        f"<div style='background-color:{row['Colour']}; padding:6px; border-radius:8px; margin-bottom:4px;'>"
                        f"{row['Subject']} ({row['Start Time']}, {row['Duration (min)']} min)"
                        + (" 🟢 Shared" if row['Shared']=='Yes' else "") +
                        "</div>", unsafe_allow_html=True
                    )
else:
    st.info("Please add subjects and sessions to view your weekly schedule.")
