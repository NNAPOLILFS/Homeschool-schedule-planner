"""
Homeschool Planner - Version 0.4
Changes:
- Added a generic starting checklist of subjects per child
- Users can untick any subjects they don’t want
- Shared tick box remains next to each subject
- Preserves all previous functionality: children names, fixed commitments, autofill button
- Generates full daily schedule reflecting selected subjects, shared flags, and fixed commitments
"""

import streamlit as st
from datetime import datetime, timedelta

# --- Helper Functions ---
def get_default_subjects():
    """Return a generic starting checklist of subjects."""
    return ["Math", "English", "Science", "Art", "Music", "PE", "History", "Geography"]

def create_subjects_for_child(child_name):
    """Create subject dict for a child with selected and shared flags."""
    subjects = get_default_subjects()
    subject_dict = {}
    for subj in subjects:
        subject_dict[subj] = {"selected": True, "shared": False}  # selected by default
    return subject_dict

def generate_schedule(subject_dict, start_hour, end_hour, fixed_commitments):
    """
    Generate a simple hourly schedule.
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
st.sidebar.title("Homeschool Planner - Version 0.4")

# Children names input
children = st.sidebar.text_area("Enter children names (comma-separated)", "Child 1,Child 2").split(",")
children = [c.strip() for c in children if c.strip()]

# Dictionary to store subjects per child
child_subjects = {}
for child in children:
    st.sidebar.subheader(child)
    if child not in child_subjects:
        child_subjects[child] = create_subjects_for_child(child)
    for subj, vals in child_subjects[child].items():
        col1, col2 = st.sidebar.columns([3,1])
        with col1:
            vals["selected"] = st.checkbox(subj, value=vals["selected"], key=f"{child}_{subj}_select")
        with col2:
            vals["shared"] = st.checkbox("Shared", value=vals["shared"], key=f"{child}_{subj}_shared")

# Fixed commitments
st.sidebar.subheader("Fixed Commitments")
fixed_commitments_input = st.sidebar.text_area(
    "Enter fixed commitments as 'hour,name,shared' per line. Example: 8,Assembly,True",
    "8,Assembly,True\n12,Lunch,False"
)
fixed_commitments = []
for line in fixed_commitments_input.split("\n"):
    if line.strip():
        parts = line.split(",")
        if len(parts) == 3:
            try:
                fc_hour = int(parts[0])
                fc_name = parts[1].strip()
                fc_shared = parts[2].strip().lower() == "true"
                fixed_commitments.append((fc_hour, fc_name, fc_shared))
            except:
                pass

# Schedule settings
st.sidebar.subheader("Schedule Settings")
start_hour = st.sidebar.number_input("Day start hour", min_value=6, max_value=12, value=7)
end_hour = 17  # Fixed

# Autofill button (keeps current selections)
autofill = st.sidebar.button("Autofill Schedule")

# --- Main Schedule View ---
st.title("Weekly Homeschool Schedule")
st.write(f"Schedule from {start_hour}:00 to {end_hour}:00")

for child in children:
    st.header(child)
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

