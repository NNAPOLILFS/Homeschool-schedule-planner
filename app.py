# app.py
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
        # Each subject has a shared tick option (default False)
        subject_dict[subj] = {"shared": False, "selected": True}  # selected=True by default
    return subject_dict

# --- Sidebar / Top Config ---
st.sidebar.title("Homeschool Planner - Version 0.4")

# List of children
children = st.sidebar.multiselect("Select children", ["Child 1", "Child 2", "Child 3"], default=["Child 1"])

# Dictionary to store subjects per child
child_subjects = {}

for child in children:
    st.sidebar.subheader(child)
    
    # If not already created, initialize subjects
    if child not in child_subjects:
        child_subjects[child] = create_subjects_for_child(child)
    
    for subj, vals in child_subjects[child].items():
        col1, col2 = st.sidebar.columns([3,1])
        with col1:
            # Checkbox for selecting subject (default True)
            vals["selected"] = st.checkbox(subj, value=vals["selected"], key=f"{child}_{subj}_select")
        with col2:
            # Shared checkbox for subject
            vals["shared"] = st.checkbox("Shared", value=vals["shared"], key=f"{child}_{subj}_shared")

# --- Schedule Configuration ---
st.sidebar.subheader("Schedule Settings")
start_hour = st.sidebar.number_input("Day start hour", min_value=6, max_value=12, value=7)
end_hour = 17  # Fixed for now

# --- Main Schedule View ---
st.title("Weekly Homeschool Schedule")
st.write(f"Schedule from {start_hour}:00 to {end_hour}:00")

# Generate a simple schedule per child
for child in children:
    st.header(child)
    st.write("Subjects selected for this child:")
    for subj, vals in child_subjects[child].items():
        if vals["selected"]:
            shared_text = " (Shared)" if vals["shared"] else ""
            st.write(f"- {subj}{shared_text}")

st.write("Schedule generation and layout will come in future versions.")
