"""
Homeschool Planner - Version 0.7.b
Changes:
- Compressed subject input rows: "Subject X" label inline with name, duration, sessions, shared
- Side-by-side daily schedule view: all children visible for each day
- Top-bar layout preserved
- All schedule generation logic from v0.6.h maintained
- Durations (15/30/60), shared flags, fixed commitments, autofill, weekday/weekend toggles intact
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

def generate_weekly_schedule(child_subjects_dict, days, start_hour, end_hour, fixed_commitments):
    """Generate weekly schedule tables per child per day"""
    weekly_tables = {}
    for child, subjects in child_subjects_dict.items():
        day_assignments = assign_subjects_to_days(subjects, days)
        weekly_tables[child] = {}
        for day in days:
            weekly_tables[child][day] = generate_daily_schedule(day_assignments[day], start_hour, end_hour, fixed_commitments)
    return weekly_tables

# --- Top-Bar Inputs ---
st.title("Homeschool Planner - Version 0.7.b")
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
        cols = st.columns([1,4,2,2,1])  # compact columns
        with cols[0]:
            st.markdown(f"**S{i+1}**")
        with cols[1]:
            subj["name"] = st.text_input("", value=subj.get("name",""), key=f"{child}_name_{i}")
        with cols[2]:
            subj["duration"] = st.selectbox("", options=[15,30,60],
                                            index=[15,30,60].index(subj.get("duration",15)),
                                            key=f"{child}_dur_{i}")
        with cols[3]:
            subj["sessions"] = st.number_input("", min_value=1, max_value=8,
                                               value=int(subj.get("sessions",1)),
                                               key=f"{child}_sess_{i}", format="%d")
        with cols[4]:
            subj["shared"] = st.checkbox("", value=subj.get("shared",False), key=f"{child}_shared_{i}")

# --- Fixed Commitments ---
st.subheader("Fixed Commitments")
fixed_commitments = []
for i in range(5):
    cols = st.columns([2,3,1])
    with cols[0]:
        hour = st.number_input(f"Start Hour {i+1}", min_value=6, max_value=17, value=8, key=f"fc_hour_{i}", format="%d")
    with cols[1]:
        name = st.text_input(f"Name {i+1}", key=f"fc_name_{i}")
    with cols[2]:
        shared = st.checkbox("Shared", key=f"fc_shared_{i}")
    if name.strip() != "":
        fixed_commitments.append((hour, name.strip(), shared))

# --- Generate Weekly Schedule ---
weekly_tables = generate_weekly_schedule(child_subjects, days, start_hour, end_hour, fixed_commitments)

# --- Display Side-by-Side Daily Schedules ---
st.header("Weekly Homeschool Schedule")
for day in days:
    st.subheader(day)
    cols = st.columns(len(children))
    for idx, child in enumerate(children):
        with cols[idx]:
            st.subheader(child)
            df = pd.DataFrame(weekly_tables[child][day])
            st.table(df)
