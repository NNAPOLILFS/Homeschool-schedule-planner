"""
Homeschool Planner - Version 0.6.h
Changes:
- Distributes each subject's sessions evenly across selected days by subject type
- Ensures subjects with multiple sessions do not stack all on one day
- All previous functionality maintained:
    - Durations (15/30/60)
    - Table layout per child per day
    - Fixed commitments with shared flags
    - Weekday/weekend toggles
    - Autofill button
    - Children names input
    - Subject rows (name, duration, sessions, shared)
"""

import streamlit as st
import pandas as pd
import math

# --- Helper Functions ---
def assign_subjects_to_days(subject_list, days):
    """
    Assign each subject's sessions evenly across the available days.
    Returns dict {day: list of subjects for that day}.
    """
    day_assignments = {day: [] for day in days}
    for subj in subject_list:
        session_count = subj["sessions"]
        # Determine which days this subject should appear on
        interval = max(1, len(days) // session_count)
        day_indices = [(i*interval) % len(days) for i in range(session_count)]
        for idx in day_indices:
            day = days[idx]
            day_assignments[day].append(subj)
    return day_assignments

def generate_daily_schedule(day_subjects, start_hour, end_hour, fixed_commitments):
    """
    Generate a schedule table for a single day.
    day_subjects: list of subjects assigned to this day
    """
    # Create all 15-min slots in the day
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

    # Fill subjects
    slot_idx = 0
    for subj in day_subjects:
        blocks = subj["duration"] // 15
        while slot_idx < len(slots):
            current_slot = slots[slot_idx]
            if schedule_dict[current_slot] is None:
                # Check if enough consecutive slots are free
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
    return schedule_table

def generate_weekly_schedule(subject_list, days, start_hour, end_hour, fixed_commitments):
    """
    Generate weekly schedule tables per child.
    """
    day_assignments = assign_subjects_to_days(subject_list, days)
    weekly_tables = {}
    for day in days:
        weekly_tables[day] = generate_daily_schedule(day_assignments[day], start_hour, end_hour, fixed_commitments)
    return weekly_tables

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.6.h")

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
    weekly_tables = generate_weekly_schedule(child_subjects[child], days, start_hour, end_hour, fixed_commitments)
    for day in days:
        st.subheader(day)
        df = pd.DataFrame(weekly_tables[day])
        st.table(df)
