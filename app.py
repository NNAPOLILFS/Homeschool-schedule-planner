"""
Homeschool Planner - Version 0.6.g
Changes:
- Restored week-level session distribution from v0.3
- Subjects distributed evenly across selected days
- Each session respects duration (15/30/60) and fills correct 15-min slots
- Fixed commitments respected per day
- Table layout preserved
- All previous features maintained:
    - Children names input
    - Subject rows (name, duration, sessions, shared)
    - Fixed commitments with shared tick box
    - Autofill button
    - Weekday/weekend toggles
"""

import streamlit as st
import pandas as pd
import math

# --- Helper Functions ---
def generate_weekly_schedule(subject_list, days, start_hour, end_hour, fixed_commitments):
    """
    Distribute subjects across selected days, respecting sessions and durations.
    Returns dict {day: schedule_table}.
    """
    schedule_per_day = {day: [] for day in days}
    
    # Track remaining sessions per subject
    remaining_sessions = []
    for subj in subject_list:
        remaining_sessions.append({"subj": subj, "remaining": subj["sessions"]})

    # Assign subjects to days evenly
    day_idx = 0
    while any(rs["remaining"] > 0 for rs in remaining_sessions):
        for rs in remaining_sessions:
            if rs["remaining"] > 0:
                day = days[day_idx % len(days)]
                schedule_per_day[day].append(rs["subj"])
                rs["remaining"] -= 1
                day_idx += 1

    # Generate daily schedule table
    daily_tables = {}
    for day in days:
        # Create all 15-min slots
        slots = []
        for hour in range(start_hour, end_hour):
            for minute in [0, 15, 30, 45]:
                slots.append(hour*60 + minute)
        schedule_dict = {s: None for s in slots}

        # Apply fixed commitments
        for fc_hour, fc_name, fc_shared in fixed_commitments:
            slot = fc_hour * 60
            if slot in schedule_dict:
                schedule_dict[slot] = (fc_name, fc_shared)

        # Fill subjects for the day
        day_subjects = schedule_per_day[day]
        slot_idx = 0
        for subj in day_subjects:
            blocks = subj["duration"] // 15
            # Find next available slots
            while slot_idx < len(slots):
                current_slot = slots[slot_idx]
                if schedule_dict[current_slot] is None:
                    # Fill consecutive blocks
                    can_place = True
                    for b in range(blocks):
                        next_slot = current_slot + b*15
                        if next_slot not in schedule_dict or schedule_dict[next_slot] is not None:
                            can_place = False
                            break
                    if can_place:
                        for b in range(blocks):
                            schedule_dict[current_slot + b*15] = (subj["name"], subj["shared"])
                        slot_idx += blocks
                        break
                slot_idx += 1

        # Convert to table format
        schedule_table = []
        for slot in sorted(slots):
            hour = slot // 60
            minute = slot % 60
            time_str = f"{hour:02d}:{minute:02d}"
            entry = schedule_dict[slot]
            if entry:
                name, shared = entry
                shared_text = " (Shared)" if shared else ""
                schedule_table.append({"Time": time_str, "Subject": name + shared_text})
            else:
                schedule_table.append({"Time": time_str, "Subject": "Free"})
        daily_tables[day] = schedule_table
    return daily_tables

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.6.g")

# Children names input
children = st.sidebar.text_area("Enter children names (comma-separated)", "Child 1,Child 2").split(",")
children = [c.strip() for c in children if c.strip()]

# Dictionary to store subjects per child
child_subjects = {}
for child in children:
    st.sidebar.subheader(child)
    if child not in child_subjects:
        child_subjects[child] = []

    num_subjects = st.sidebar.number_input(
        f"Number of subjects for {child}", min_value=1, max_value=20, value=4, key=f"num_subj_{child}", format="%d"
    )
    while len(child_subjects[child]) < num_subjects:
        child_subjects[child].append({"name":"", "duration":15, "sessions":1, "shared":False})
    while len(child_subjects[child]) > num_subjects:
        child_subjects[child].pop()

    for i, subj in enumerate(child_subjects[child]):
        col1, col2, col3, col4 = st.sidebar.columns([4,2,2,1])
        with col1:
            subj["name"] = st.text_input(f"Subject {i+1}", value=subj.get("name",""), key=f"{child}_name_{i}")
        with col2:
            subj["duration"] = st.selectbox(
                "Duration (mins)", options=[15,30,60], index=[15,30,60].index(subj.get("duration",15)),
                key=f"{child}_dur_{i}"
            )
        with col3:
            subj["sessions"] = st.number_input(
                "Sessions", min_value=1, max_value=8, value=int(subj.get("sessions",1)), key=f"{child}_sess_{i}", format="%d"
            )
        with col4:
            subj["shared"] = st.checkbox("Shared", value=subj.get("shared",False), key=f"{child}_shared_{i}")

# --- Fixed Commitments Input ---
st.sidebar.subheader("Fixed Commitments (Select Hour & Shared)")
fixed_commitments = []
for i in range(5):
    cols = st.sidebar.columns([2,3,1])
    with cols[0]:
        hour = st.number_input(f"Start Hour {i+1}", min_value=6, max_value=17, value=8, key=f"fc_hour_{i}", format="%d")
    with cols[1]:
        name = st.text_input(f"Name {i+1}", key=f"fc_name_{i}")
    with cols[2]:
        shared = st.checkbox("Shared", key=f"fc_shared_{i}")
    if name.strip() != "":
        fixed_commitments.append((hour, name.strip(), shared))

# Schedule settings
st.sidebar.subheader("Schedule Settings")
start_hour = st.sidebar.number_input("Day start hour", min_value=6, max_value=12, value=7, format="%d")
end_hour = 17  # Fixed

# Autofill button
autofill = st.sidebar.button("Autofill Schedule")

# Weekday/Weekend toggles
st.sidebar.subheader("Select Days to Include in Schedule")
include_weekdays = st.sidebar.checkbox("Include Weekdays (Mon-Fri)", value=True)
include_saturday = st.sidebar.checkbox("Include Saturday", value=True)
include_sunday = st.sidebar.checkbox("Include Sunday", value=True)

days = []
if include_weekdays:
    days += ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
if include_saturday:
    days.append("Saturday")
if include_sunday:
    days.append("Sunday")

# --- Main Schedule View ---
st.title("Weekly Homeschool Schedule")
st.write(f"Schedule from {start_hour}:00 to {end_hour}:00")

for child in children:
    st.header(child)
    daily_tables = generate_weekly_schedule(child_subjects[child], days, start_hour, end_hour, fixed_commitments)
    for day in days:
        st.subheader(day)
        df = pd.DataFrame(daily_tables[day])
        st.table(df)
