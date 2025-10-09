import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🎨 Homeschool Planner")

# ------------------------
# Sidebar Settings
# ------------------------
st.sidebar.header("Settings")
children = [c.strip() for c in st.sidebar.text_input("Enter children's names (comma separated):", "Winter, Micah").split(",")]
day_start_time = st.sidebar.time_input("School day start time:", datetime.strptime("08:00", "%H:%M").time())
time_increment = 15  # fixed increment
day_end_time = datetime.strptime("15:00", "%H:%M").time()  # fixed end time

# Pastel palette and emojis
pastel_palette = ["#F9D5E5","#FCE2CE","#D5E1DF","#E2F0CB","#C5D5E4","#F7D8BA","#EAD5E6","#D0E6A5","#FFB7B2","#B5EAD7"]
subject_emojis = ["📚","🔢","🌏","🎨","🧪"]

# ------------------------
# Initialize session state
# ------------------------
if "subjects" not in st.session_state:
    st.session_state["subjects"] = {kid:[{"name":"","sessions":0,"length":30,"shared":False}] for kid in children}

if "commitments" not in st.session_state:
    st.session_state["commitments"] = {kid: [] for kid in children}

# ------------------------
# Subjects Input
# ------------------------
st.header("Subjects")
for kid in children:
    st.subheader(f"{kid}'s Subjects")
    for i, subj in enumerate(st.session_state["subjects"][kid]):
        col1, col2, col3, col4 = st.columns([3,1,1,1])
        with col1:
            subj["name"] = st.text_input(f"Name ({kid})", value=subj["name"], key=f"{kid}_name_{i}")
        with col2:
            subj["sessions"] = st.number_input(f"Sessions/week", min_value=0, max_value=10, value=subj["sessions"], step=1, key=f"{kid}_sess_{i}")
        with col3:
            subj["length"] = st.number_input(f"Length (min)", min_value=time_increment, step=time_increment, value=subj["length"], key=f"{kid}_len_{i}")
        with col4:
            subj["shared"] = st.checkbox("Shared", value=subj["shared"], key=f"{kid}_shared_{i}")

    # Add Subject button
    if st.button(f"Add Subject for {kid}"):
        if len(st.session_state["subjects"][kid]) < 5:
            st.session_state["subjects"][kid].append({"name":"","sessions":0,"length":30,"shared":False})

# ------------------------
# Fixed Commitments Input
# ------------------------
add_commitments = st.checkbox("Add fixed commitments for children?")
days_of_week = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

if add_commitments:
    st.header("Fixed Commitments")
    for kid in children:
        st.subheader(f"{kid}'s Commitments")
        # Max 2 commitments per child for speed
        for i in range(2):
            col1, col2, col3, col4 = st.columns([3,2,1,1])
            with col1:
                name = st.text_input(f"Commitment {i+1} Name ({kid})", key=f"{kid}_commit_name_{i}")
            with col2:
                day = st.selectbox(f"Day ({kid})", days_of_week, key=f"{kid}_commit_day_{i}")
            with col3:
                start = st.time_input(f"Start time ({kid})", key=f"{kid}_commit_start_{i}", value=day_start_time)
            with col4:
                end = st.time_input(f"End time ({kid})", key=f"{kid}_commit_end_{i}", value=(datetime.combine(datetime.today(), start) + timedelta(minutes=30)).time())
            
            # Always update session_state with current input values
            if name and start < end:
                if len(st.session_state["commitments"][kid]) <= i:
                    st.session_state["commitments"][kid].append({})
                st.session_state["commitments"][kid][i] = {
                    "name": name,
                    "day": day,
                    "start": timedelta(hours=start.hour, minutes=start.minute),
                    "end": timedelta(hours=end.hour, minutes=end.minute)
                }

# ------------------------
# Autofill Schedule Function
# ------------------------
def autofill_schedule(subjects, commitments, children, start_time, end_time, increment):
    schedule = {kid:{day:[] for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]} for kid in children}
    unscheduled = []

    # Ensure every subject has emoji and color
    for kid in children:
        for subj in subjects[kid]:
            if "emoji" not in subj:
                subj["emoji"] = random.choice(subject_emojis)
            if "color" not in subj:
                subj["color"] = random.choice(pastel_palette)

    # Create time slots
    slots = []
    cur = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_delta = timedelta(hours=end_time.hour, minutes=end_time.minute)
    while cur + timedelta(minutes=increment) <= end_delta:
        slots.append(cur)
        cur += timedelta(minutes=increment)

    # Place fixed commitments
    for kid in children:
        for c in commitments[kid]:
            schedule[kid][c["day"]].append({
                "start": c["start"],
                "end": c["end"],
                "label": f"🕒 {c['name']}",
                "color": "#CCCCCC"
            })

    # Place subjects
    for kid in children:
        for subj in subjects[kid]:
            if subj["sessions"]==0 or not subj["name"]:
                continue
            length_delta = timedelta(minutes=subj["length"])
            placed_sessions = 0
            for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
                for slot in slots:
                    overlap = any(not(slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[kid][day])
                    if not overlap:
                        if subj["shared"]:
                            overlap_all = False
                            for k in children:
                                if any(not(slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[k][day]):
                                    overlap_all = True
                                    break
                            if overlap_all:
                                continue
                            for k in children:
                                schedule[k][day].append({
                                    "start": slot,
                                    "end": slot + length_delta,
                                    "label": f"{subj['emoji']} {subj['name']}",
                                    "color": subj["color"]
                                })
                        else:
                            schedule[kid][day].append({
                                "start": slot,
                                "end": slot + length_delta,
                                "label": f"{subj['emoji']} {subj['name']}",
                                "color": subj["color"]
                            })
                        placed_sessions += 1
                    if placed_sessions >= subj["sessions"]:
                        break
                if placed_sessions >= subj["sessions"]:
                    break
            if placed_sessions < subj["sessions"]:
                unscheduled.append(f"{subj['name']} ({kid})" if not subj["shared"] else f"{subj['name']} (shared)")

    # Sort schedules
    for kid in children:
        for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
            schedule[kid][day] = sorted(schedule[kid][day], key=lambda x: x["start"])
    return schedule, unscheduled

# ------------------------
# Display Timetable
# ------------------------
if st.button("✨ Autofill Schedule"):
    schedule, unscheduled = autofill_schedule(st.session_state["subjects"], st.session_state["commitments"], children, day_start_time, day_end_time, time_increment)
    st.subheader("📅 Daily Schedule")

    time_slots = []
    cur = timedelta(hours=day_start_time.hour, minutes=day_start_time.minute)
    end_delta = timedelta(hours=day_end_time.hour, minutes=day_end_time.minute)
    while cur < end_delta:
        time_slots.append(cur)
        cur += timedelta(minutes=time_increment)

    for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
        st.markdown(f"### {day}")
        grid = pd.DataFrame(index=[(datetime.min + t).strftime("%H:%M") for t in time_slots], columns=children)
        for kid in children:
            for t in time_slots:
                label = ""
                for s in schedule[kid][day]:
                    if s["start"] <= t < s["end"]:
                        label = s["label"]
                        break
                grid.at[(datetime.min + t).strftime("%H:%M"), kid] = label
        st.dataframe(grid)

    # Summary
    st.subheader("📊 Weekly Summary")
    summary = []
    for kid in children:
        total_minutes = 0
        for day in ["Monday","Tuesday","Wednesday","Thursday","Friday"]:
            total_minutes += sum((s["end"]-s["start"]).total_seconds()/60 for s in schedule[kid][day] if not s["label"].startswith("🕒"))
        summary.append({"Child": kid, "Total Hours": round(total_minutes/60,2)})
    st.table(pd.DataFrame(summary))

    if unscheduled:
        st.warning("Some subjects couldn’t be scheduled:")
        for u in unscheduled:
            st.write(f"- {u}")
