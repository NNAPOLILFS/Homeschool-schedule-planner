"""
Homeschool Planner - Version 0.7.a
Changes:
- Redesigned layout: top-bar replaces left sidebar
- Children, subjects, fixed commitments, start hour, weekday/weekend toggles, and autofill button all at top
- Schedule tables remain below
- All schedule generation logic from v0.6.h preserved
- Subject sessions distributed by type across week
- Durations, shared flags, fixed commitments, and table layout maintained
"""

import streamlit as st
import pandas as pd
import math

# --- Helper Functions ---
def assign_subjects_to_days(subject_list, days):
    """Assign each subject's sessions evenly across the available days"""
    day_assignments = {day: [] for day in days}
    for subj in subject_list:
        session_count = subj["sessions"]
        interval = max(1, len(days) // session_count)
        day_indices = [(i*interval) % len(days) for i in range(session_count)]
        for idx in day_indices:
            day = days[idx]
            day_assignments[day].append(subj)
    return day_assignments

def generate_daily_schedule(day_subjects, start_hour, end_hour, fixed_commitments):
    """Generate a schedule table for a single day"""
    slots = []
    for hour in range(start_hour, end_hour):
        for minute in [0, 15, 30, 45]:
            slots.append(hour*60 + minute)
    schedule_dict = {s: None for s in slots}
    # Fixed commitments
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
    """Generate weekly schedule tables per child"""
    day_assignments = assign_subjects_to_days(subject_list, days)
    weekly_tables = {}
    for day in days:
        weekly_tables[day] = generate_daily_schedule(day_assignments[day], start_hour, end_hour, fixed_commitments)
    return weekly_tables

# --- Top-Bar Inputs ---
st.title("Homeschool Planner - Version 0.7.a")
top_cols = st.columns([2,2,2,2])

with top_cols[0]:
    children_text = st.text_area("Children names (comma-separated)", "Child 1,Child 2")
    children = [c.strip() for c in children_text.split(",") if c.strip()]

with top_cols[1]:
    start_hour = st.number_input("Day start hour", min_value=6, max_value=12, value=7, format="%d")
    end_hour = 17  # fixed

with top_cols[2]:
    include_weekdays = st.checkbox("Include Weekdays (Mon-Fri)", value=True)
    include_saturday = st.checkbox("Include Saturday", value=True)
    include_sunday = st.checkbox("Include Sunday", value=True)
    days = []
    if include_weekdays:
        days += ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    if include_saturday:
        days.append("Saturday")
    if include_sunday:
        days.append("Sunday")

with top_cols[3]:
    autofill = st.button("Autofill Schedule")

# --- Subjects and Fixed Commitments per Child ---
child_subjects = {}
for child in children:
    st.subheader(child)
    num_subjects = st.number_input(
        f"Number of subjects for {child}", min_value=1, max_value=20, value=4, key=f"num_subj_{child}", format="%d"
    )
    if child not in child_subjects:
        child_subjects[child] = []
    while len(child_subjects[child]) < num_subjects:
        child_subjects[child].append({"name":"", "duration":15, "sessions":1, "shared":False})
    while len(child_subjects[child]) > num_subjects:
        child_subjects[child].pop()
    for i, subj in enumerate(child_subjects[child]):
        col1, col2, col3, col4 = st.columns([4,2,2,1])
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

# --- Fixed Commitments ---
st.subheader("Fixed Commitments")
fixed_commitments = []
for i in range(5):
    col1, col2, col3 = st.columns([2,3,1])
    with col1:
        hour = st.number_input(f"Start Hour {i+1}", min_value=6, max_value=17, value=8, key=f"fc_hour_{i}", format="%d")
    with col2:
        name = st.text_input(f"Name {i+1}", key=f"fc_name_{i}")
    with col3:
        shared = st.checkbox("Shared", key=f"fc_shared_{i}")
    if name.strip() != "":
        fixed_commitments.append((hour, name.strip(), shared))

# --- Schedule Display ---
st.header("Weekly Homeschool Schedule")
for child in children:
    st.subheader(child)
    weekly_tables = generate_weekly_schedule(child_subjects[child], days, start_hour, end_hour, fixed_commitments)
    for day in days:
        st.subheader(day)
        df = pd.DataFrame(weekly_tables[day])
        st.table(df)
