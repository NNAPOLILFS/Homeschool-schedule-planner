"""
Homeschool Planner - Version 0.6.a
Changes:
- Fixed commitments dropdown now shows all hours from day start to 5 PM
- Added shared tick box for each fixed commitment
- Preserves all previous functionality from v0.5.a:
    - Children names input
    - Subject management per child
    - Shared tick boxes
    - Autofill button
    - Weekday/weekend toggles
    - Full schedule generation
"""

import streamlit as st

# --- Helper Functions ---
def generate_schedule(subject_dict, start_hour, end_hour, fixed_commitments):
    """
    Generate hourly schedule for a day.
    Fixed commitments are placed at their hour, remaining subjects fill other hours.
    Returns a dict {hour: (subject, shared_flag)}.
    """
    schedule = {}
    selected_subjects = [s for s, v in subject_dict.items() if v["selected"]]
    shared_flags = [subject_dict[s]["shared"] for s in selected_subjects]

    if not selected_subjects:
        return schedule

    # Place fixed commitments
    for fc_hour, fc_name, fc_shared in fixed_commitments:
        if start_hour <= fc_hour < end_hour:
            schedule[fc_hour] = (fc_name, fc_shared)

    # Fill remaining hours with subjects
    hour = start_hour
    idx = 0
    while hour < end_hour:
        if hour not in schedule:
            subj = selected_subjects[idx % len(selected_subjects)]
            shared = shared_flags[idx % len(shared_flags)]
            schedule[hour] = (subj, shared)
            idx += 1
        hour += 1
    return schedule

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.6.a")

# Children names input
children = st.sidebar.text_area("Enter children names (comma-separated)", "Child 1,Child 2").split(",")
children = [c.strip() for c in children if c.strip()]

# Dictionary to store subjects per child
child_subjects = {}
for child in children:
    st.sidebar.subheader(child)
    if child not in child_subjects:
        default_subjects = ["Math", "English", "Science", "Art", "Music", "PE", "History", "Geography"]
        child_subjects[child] = {s: {"selected": True, "shared": False} for s in default_subjects}
    for subj, vals in child_subjects[child].items():
        col1, col2 = st.sidebar.columns([3,1])
        with col1:
            vals["selected"] = st.checkbox(subj, value=vals["selected"], key=f"{child}_{subj}_select")
        with col2:
            vals["shared"] = st.checkbox("Shared", value=vals["shared"], key=f"{child}_{subj}_shared")

# --- Fixed Commitments Input ---
st.sidebar.subheader("Fixed Commitments (Select Hour & Shared)")

fixed_commitments = []
for i in range(5):  # Allow up to 5 fixed commitments as an example
    cols = st.sidebar.columns([2, 3, 1])
    with cols[0]:
        hour = st.number_input(f"Start Hour {i+1}", min_value=6, max_value=17, value=8, key=f"fc_hour_{i}")
    with cols[1]:
        name = st.text_input(f"Name {i+1}", key=f"fc_name_{i}")
    with cols[2]:
        shared = st.checkbox("Shared", key=f"fc_shared_{i}")
    if name.strip() != "":
        fixed_commitments.append((hour, name.strip(), shared))

# Schedule settings
st.sidebar.subheader("Schedule Settings")
start_hour = st.sidebar.number_input("Day start hour", min_value=6, max_value=12, value=7)
end_hour = 17  # Fixed

# Autofill button
autofill = st.sidebar.button("Autofill Schedule")

# Weekday/Weekend toggles
st.sidebar.subheader("Select Days to Include in Schedule")
include_weekdays = st.sidebar.checkbox("Include Weekdays (Mon-Fri)", value=True)
include_saturday = st.sidebar.checkbox("Include Saturday", value=True)
include_sunday = st.sidebar.checkbox("Include Sunday", value=True)

# Determine days to display
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
                    subj, shared = schedule[hour]
                    shared_text = " (Shared)" if shared else ""
                    st.write(f"{hour}:00 - {subj}{shared_text}")
                else:
                    st.write(f"{hour}:00 - Free")
        else:
            st.write("No subjects selected for this child.")
