
"""
Homeschool Planner - Version 0.4
Changes:
- Added a generic starting checklist of subjects per child
- Users can untick any subjects they don’t want
- Shared tick box remains next to each subject
- Generates a full daily schedule from start hour to 5 PM using selected subjects
"""

import streamlit as st
from datetime import time

# --- Helper functions ---
def get_default_subjects():
    """Return a generic starting checklist of subjects."""
    return ["Math", "English", "Science", "Art", "Music", "PE", "History", "Geography"]

def create_subjects_for_child(child_name):
    """Create a subject selection dictionary for a child."""
    subjects = get_default_subjects()
    subject_dict = {}
    for subj in subjects:
        # Each subject has a shared tick option and selected by default
        subject_dict[subj] = {"shared": False, "selected": True}
    return subject_dict

def generate_schedule(subject_dict, start_hour, end_hour):
    """
    Generate a simple schedule based on selected subjects.
    Loops subjects in order until the day end.
    Returns a list of tuples: (hour, subject, shared_flag)
    """
    schedule = []
    selected_subjects = [s for s, v in subject_dict.items() if v["selected"]]
    shared_flags = [subject_dict[s]["shared"] for s in selected_subjects]
    
    if not selected_subjects:
        return schedule

    hour = start_hour
    idx = 0
    while hour < end_hour:
        subj = selected_subjects[idx % len(selected_subjects)]
        shared = shared_flags[idx % len(shared_flags)]
        schedule.append((hour, subj, shared))
        hour += 1
        idx += 1
    return schedule

# --- Sidebar Configuration ---
st.sidebar.title("Homeschool Planner - Version 0.4")

# List of children
children = st.sidebar.multiselect("Select children", ["Child 1", "Child 2", "Child 3"], default=["Child 1"])

# Dictionary to store subjects per child
child_subjects = {}

for child in children:
    st.sidebar.subheader(child)
    
    # Initialize subjects if not already
    if child not in child_subjects:
        child_subjects[child] = create_subjects_for_child(child)
    
    for subj, vals in child_subjects[child].items():
        col1, col2 = st.sidebar.columns([3,1])
        with col1:
            # Checkbox for selecting subject
            vals["selected"] = st.checkbox(subj, value=vals["selected"], key=f"{child}_{subj}_select")
        with col2:
            # Shared checkbox for subject
            vals["shared"] = st.checkbox("Shared", value=vals["shared"], key=f"{child}_{subj}_shared")

# --- Schedule Configuration ---
st.sidebar.subheader("Schedule Settings")
start_hour = st.sidebar.number_input("Day start hour", min_value=6, max_value=12, value=7)
end_hour = 17  # Fixed end hour for now

# --- Main Schedule View ---
st.title("Weekly Homeschool Schedule")
st.write(f"Schedule from {start_hour}:00 to {end_hour}:00")

# Generate schedule per child
for child in children:
    st.header(child)
    schedule = generate_schedule(child_subjects[child], start_hour, end_hour)
    if schedule:
        for hour, subj, shared in schedule:
            shared_text = " (Shared)" if shared else ""
            st.write(f"{hour}:00 - {subj}{shared_text}")
    else:
        st.write("No subjects selected for this child.")

