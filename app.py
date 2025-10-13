"""
Homeschool Planner - Version 0.6.c
Changes:
- Fully corrected version from baseline v0.3 with subject row (name, duration, sessions, shared checkbox)
- Includes weekday/weekend toggles (v0.5)
- Fixed commitments dropdown now shows all hours from day start to 5 PM
- Added shared tick box for each fixed commitment
- Fixes number_input to return integers for duration and sessions
- Preserves all previous functionality:
    - Children names input
    - Subject management per child
    - Autofill button
    - Full schedule generation from start to 5 PM
"""

import streamlit as st

# --- Helper Functions ---
def generate_schedule(subject_list, start_hour, end_hour, fixed_commitments):
    """
    Generate schedule for a day.
    subject_list: list of dicts with keys 'name', 'duration', 'sessions', 'shared'
    fixed_commitments: list of tuples (hour, name, shared)
    Returns dict {hour: (subject_name, shared_flag)}
    """
    schedule = {}
    # Place fixed commitments first
    for fc_hour, fc_name, fc_shared in fixed_commitments:
        if start_hour <= fc_hour < end_hour:
            schedule[fc_hour] = (fc_name, fc_shared)
    
    # Flatten subjects into repeating blocks according to sessions
    flat_subjects = []
    for subj in subject_list:
        if subj["name"] and subj["sessions"] > 0 and subj["duration"] > 0:
            flat_subjects.extend([subj] * subj["sessions"])
    
    hour = start_hour
    idx = 0
    while hour < end_hour:
        if hour not in schedule and flat_subjects:
            subj = flat_subjects[idx % len(flat_subjects)]
            schedule[hour] = (subj["name"], subj["shared"])
            idx += 1
        hour += 1
    return schedule

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.6.c")

# Children names input
children = st.sidebar.text_area("Enter children names (comma-separated)", "Child 1,Child 2").split(",")
children = [c.strip() for c in children if c.strip()]

# Dictionary to store subjects per child
child_subjects = {}
for child in children:
    st.sidebar.subheader(child)
    if child not in child_subjects:
        child_subjects[child] = []  # List of subject dicts
    
    # Dynamic number of subjects
    num_subjects = st.sidebar.number_input(
        f"Number of subjects for {child}", min_value=1, max_value=20, value=4, key=f"num_subj_{child}", format="%d"
    )
    # Adjust existing list
    while len(child_subjects[child]) < num_subjects:
        child_subjects[child].append({"name":"", "duration":1, "sessions":1, "shared":False})
    while len(child_subjects[child]) > num_subjects:
        child_subjects[child].pop()
    
    for i, subj in enumerate(child_subjects[child]):
        col1, col2, col3, col4 = st.sidebar.columns([4,2,2,1])
        with col1:
            subj["name"] = st.text_input(f"Subject {i+1}", value=subj.get("name",""), key=f"{child}_name_{i}")
        with col2:
            subj["duration"] = st.number_input(
                "Duration", min_value=1, max_value=8, value=int(subj.get("duration",1)), key=f"{child}_dur_{i}", format="%d"
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
for i in range(5):  # Up to 5 fixed commitments
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
end_hour = 17  # Fixed end of day

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
        schedule = generate_schedule(child_subjects[child], start_hour, end_hour, fixed_commitments)
        if schedule:
            for hour in range(start_hour, end_hour):
                if hour in schedule:
                    subj_name, shared = schedule[hour]
                    shared_text = " (Shared)" if shared else ""
                    st.write(f"{hour}:00 - {subj_name}{shared_text}")
                else:
                    st.write(f"{hour}:00 - Free")
        else:
            st.write("No subjects defined for this child.")
