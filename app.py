# app.py – Homeschool Planner v0.4
# Features added in v0.4:
# - Optional starting checklist of generic subjects per child
# - User can untick any subjects they don’t want
# - Shared tick box remains next to each subject
# Previous features from v0.3 retained

import streamlit as st

# --- Sample data: Children and default subjects ---
children = ["Child 1", "Child 2", "Child 3"]
generic_subjects = ["Math", "English", "Science", "History", "Art", "Music", "PE"]

# --- Sidebar / top settings ---
st.sidebar.header("Homeschool Planner Settings")

# Select children (for simplicity, all selected)
selected_children = st.sidebar.multiselect("Select Children", children, default=children)

# --- Subject selection per child ---
st.sidebar.subheader("Subjects per Child")
subjects_per_child = {}

for child in selected_children:
    st.sidebar.markdown(f"**{child}**")
    
    # v0.4: Optional starting checklist of generic subjects
    use_default = st.sidebar.checkbox(f"Use default subjects for {child}", value=True, key=f"default_{child}")
    
    # Display subjects with checkboxes
    if use_default:
        subjects = []
        for subj in generic_subjects:
            checked = st.sidebar.checkbox(subj, value=True, key=f"{child}_{subj}")
            subjects.append(subj if checked else None)
        subjects_per_child[child] = [s for s in subjects if s is not None]
    else:
        # Allow user to input custom subjects
        custom_subjects = st.sidebar.text_area(f"Enter subjects for {child}, comma-separated", key=f"custom_{child}")
        subjects_per_child[child] = [s.strip() for s in custom_subjects.split(",") if s.strip()]

# --- Shared tick box example ---
st.sidebar.subheader("Shared Options")
shared_option = st.sidebar.checkbox("Shared Tick Box Example")

# --- Main Schedule Display ---
st.header("Weekly Schedule")

for child in selected_children:
    st.subheader(f"{child}'s Subjects")
    st.write(subjects_per_child[child])

# Placeholder for schedule grid (to be expanded in future versions)
st.info("Schedule grid will be implemented in future versions (v0.5+).")

