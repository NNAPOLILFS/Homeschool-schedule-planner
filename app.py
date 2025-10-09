import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🎨 Homeschool Planner")

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("Settings")

children = [c.strip() for c in st.sidebar.text_input("Enter children's names (comma separated):", "Winter, Micah").split(",")]
day_start_time = st.sidebar.time_input("School day start time:", datetime.strptime("08:00", "%H:%M").time())
time_increment = 15  # Fixed increment
day_end_time = datetime.strptime("15:00", "%H:%M").time()  # Fixed end time

# Pastel palette
pastel_palette = [
    "#F9D5E5", "#FCE2CE", "#D5E1DF", "#E2F0CB", "#C5D5E4",
    "#F7D8BA", "#EAD5E6", "#D0E6A5", "#FFB7B2", "#B5EAD7"
]

# Possible random emojis
subject_emojis = ["📚", "🔢", "🌏", "🎨", "🧪"]

# ------------------------
# Subject Inputs (2 per child)
# ------------------------
st.header("Subjects")
subjects = {kid: [] for kid in children}
for kid in children:
    st.subheader(f"{kid}'s Subjects")
    for i in range(2):
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            name = st.text_input(f"Subject {i+1} Name ({kid})", key=f"{kid}_subj_name_{i}")
        with col2:
            sessions = st.number_input(f"Sessions/week ({kid})", min_value=0, max_value=10, value=0, step=1, key=f"{kid}_subj_sessions_{i}")
        with col3:
            length = st.number_input(f"Length (min) ({kid})", min_value=15, step=15, value=30, key=f"{kid}_subj_length_{i}")
        shared = st.checkbox(f"Shared subject ({kid})", key=f"{kid}_subj_shared_{i}")
        if name:
            subjects[kid].append({
                "name": name,
                "sessions": sessions,
                "length": length,
                "shared": shared,
                "emoji": random.choice(subject_emojis),
                "color": random.choice(pastel_palette)
            })

# ------------------------
# Fixed Commitments (2 per child)
# ------------------------
st.header("Fixed Commitments")
commitments = {kid: [] for kid in children}
for kid in children:
    st.subheader(f"{kid}'s Commitments")
    for i in range(2):
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            name = st.text_input(f"Commitment {i+1} Name ({kid})", key=f"{kid}_commit_name_{i}")
        with col2:
            start = st.time_input(f"Start time ({kid})", key=f"{kid}_commit_start_{i}", value=day_start_time)
        with col3:
            end = st.time_input(f"End time ({kid})", key=f"{kid}_commit_end_{i}", value=(datetime.combine(datetime.today(), start) + timedelta(minutes=30)).time())
        if name and start < end:
            commitments[kid].append({
                "name": name,
                "start": timedelta(hours=start.hour, minutes=start.minute),
                "end": timedelta(hours=end.hour, minutes=end.minute)
            })

# ------------------------
# Autofill Schedule Logic
# ------------------------
def autofill_schedule(subjects, commitments, children, start_time, end_time, increment):
    schedule = {kid: [] for kid in children}
    unscheduled = []

    # Create time slots
    slots = []
    cur = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_delta = timedelta(hours=end_time.hour, minutes=end_time.minute)
    while cur + timedelta(minutes=increment) <= end_delta:
        slots.append(cur)
        cur += timedelta(minutes=increment)

    # Place commitments first
    for kid in children:
        for c in commitments[kid]:
            schedule[kid].append({
                "start": c["start"],
                "end": c["end"],
                "label": f"🕒 {c['name']}",
                "color": "#CCCCCC"
            })

    # Place subjects
    for kid in children:
        for subj in subjects[kid]:
            if subj["sessions"] == 0:
                continue
            length_delta = timedelta(minutes=subj["length"])
            placed_sessions = 0
            for slot in slots:
                # Check overlap with commitments
                overlap = any(not (slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[kid])
                if not overlap:
                    if subj["shared"]:
                        # Place in all kids
                        overlap_all = False
                        for k in children:
                            if any(not (slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[k]):
                                overlap_all = True
                                break
                        if overlap_all:
                            continue
                        for k in children:
                            schedule[k].append({
                                "start": slot,
                                "end": slot + length_delta,
                                "label": f"{subj['emoji']} {subj['name']}",
                                "color": subj["color"]
                            })
                    else:
                        schedule[kid].append({
                            "start": slot,
                            "end": slot + length_delta,
                            "label": f"{subj['emoji']} {subj['name']}",
                            "color": subj["color"]
                        })
                    placed_sessions += 1
                if placed_sessions >= subj["sessions"]:
                    break
            if placed_sessions < subj["sessions"]:
                unscheduled.append(f"{subj['name']} ({kid})" if not subj["shared"] else f"{subj['name']} (shared)")

    # Sort each kid's schedule
    for kid in children:
        schedule[kid] = sorted(schedule[kid], key=lambda x: x["start"])
    return schedule, unscheduled

# ------------------------
# Display Grid Timetable
# ------------------------
if st.button("✨ Autofill Schedule"):
    schedule, unscheduled = autofill_schedule(subjects, commitments, children, day_start_time, day_end_time, time_increment)
    st.subheader("📅 Daily Schedule")

    time_slots = []
    cur = timedelta(hours=day_start_time.hour, minutes=day_start_time.minute)
    end_delta = timedelta(hours=day_end_time.hour, minutes=day_end_time.minute)
    while cur < end_delta:
        time_slots.append(cur)
        cur += timedelta(minutes=time_increment)

    # Build dataframe for display
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        st.markdown(f"### {day}")
        grid = pd.DataFrame(index=[(datetime.min + t).strftime("%H:%M") for t in time_slots], columns=children)
        for kid in children:
            for t in time_slots:
                label = ""
                for s in schedule[kid]:
                    if s["start"] <= t < s["end"]:
                        label = s["label"]
                        break
                grid.at[(datetime.min + t).strftime("%H:%M"), kid] = label
        st.dataframe(grid.style.apply(lambda x: ['background-color: '+(schedule[kid][i]["color"] if schedule[kid][i]["label"]==x[kid] else "") for kid in children], axis=1))

    # Summary table
    st.subheader("📊 Weekly Summary")
    summary = []
    for kid in children:
        total_minutes = sum((s["end"]-s["start"]).total_seconds()/60 for s in schedule[kid] if not s["label"].startswith("🕒"))
        summary.append({"Child": kid, "Total Hours": round(total_minutes/60, 2)})
    st.table(pd.DataFrame(summary))

    if unscheduled:
        st.warning("Some subjects couldn’t be scheduled:")
        for u in unscheduled:
            st.write(f"- {u}")
