"""
Homeschool Planner - Version 0.6.e
Changes:
- Duration options fixed to 15, 30, 60 minutes
- Schedule displayed in table format (like baseline v0.3)
- Preserves all previous functionality:
    - Children names input
    - Subject rows (name, duration, sessions, shared)
    - Fixed commitments with shared tick box
    - Autofill button
    - Weekday/weekend toggles
    - Full schedule generation from start to 5 PM
"""

import streamlit as st
import pandas as pd
import math

# --- Helper Functions ---
def generate_schedule(subject_list, start_hour, end_hour, fixed_commitments):
    """
    Generate schedule for a day using duration in minutes.
    Returns list of dicts: [{"time": "HH:MM", "subject": name, "shared": bool}]
    """
    # Build a list of time slots
    slots = []
    for hour in range(start_hour, end_hour):
        for minute in [0, 15, 30, 45]:
            slots.append(hour*60 + minute)  # minutes since midnight

    # Apply fixed commitments
    schedule_dict = {}  # key: slot in minutes, value: (name, shared)
    for fc_hour, fc_name, fc_shared in fixed_commitments:
        slot = fc_hour*60
        if slot in slots:
            schedule_dict[slot] = (fc_name, fc_shared)

    # Flatten subjects into repeated blocks according to sessions
    flat_subjects = []
    for subj in subject_list:
        if subj["name"] and subj["sessions"] > 0 and subj["duration"] > 0:
            for _ in range(subj["sessions"]):
                flat_subjects.append(subj)

    # Fill remaining slots
    idx = 0
    for slot in slots:
        if slot not in schedule_dict and flat_subjects:
            subj = flat_subjects[idx % len(flat_subjects)]
            duration = subj["duration"]
            schedule_dict[slot] = (subj["name"], subj["shared"])
            idx += 1
    # Convert to table-friendly list
    schedule_table = []
    for slot in sorted(schedule_dict.keys()):
        hour = slot // 60
        minute = slot % 60
        time_str = f"{hour:02d}:{minute:02d}"
        name, shared = schedule_dict[slot]
        shared_text = " (Shared)" if shared else ""
        schedule_table.append({"Time": time_str, "Subject": name + shared_text})
    return schedule_table

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.6.e")

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
    # Adjust list
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
end_hour = 17

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

for day in days:
    st.subheader(day)
    for child in children:
        st.markdown(f"**{child}**")
        schedule_table = generate_schedule(child_subjects[child], start_hour, end_hour, fixed_commitments)
        if schedule_table:
            df = pd.DataFrame(schedule_table)
            st.table(df)
        else:
            st.write("No subjects defined for this child.")
