"""
Homeschool Planner - Version 1.0
Major UX Prototype
- Persistent inputs with st.session_state (no data loss on refresh)
- Children schedules displayed side-by-side per day
- Color-coded subjects
- Compact, responsive layout
- Autofill button for automatic schedule generation
- Weekday/weekend toggles and fixed commitments included
"""

import streamlit as st
import pandas as pd

# --- Helper Functions ---

def assign_subjects_to_days(subject_list, days):
    """Assign each subject's sessions evenly across available days"""
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
        for minute in [0,15,30,45]:
            slots.append(hour*60 + minute)
    schedule_dict = {s: None for s in slots}

    # Add fixed commitments
    for fc_hour, fc_name, fc_shared in fixed_commitments:
        slot = fc_hour*60
        if slot in schedule_dict:
            schedule_dict[slot] = (fc_name, fc_shared)

    # Fill subjects
    slot_idx = 0
    for subj in day_subjects:
        blocks = subj["duration"] // 15
        placed = 0
        while placed < subj["sessions"]:
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
                            schedule_dict[current_slot+b*15] = (subj["name"], subj["shared"])
                        placed += 1
                        slot_idx += blocks
                        break
                slot_idx += 1
            if slot_idx >= len(slots):
                break  # no more space
    # Convert to table
    schedule_table = []
    for slot in sorted(slots):
        hour = slot//60
        minute = slot%60
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
    weekly_tables = {}
    for child, subjects in child_subjects_dict.items():
        day_assignments = assign_subjects_to_days(subjects, days)
        weekly_tables[child] = {}
        for day in days:
            weekly_tables[child][day] = generate_daily_schedule(day_assignments[day], start_hour, end_hour, fixed_commitments)
    return weekly_tables

def get_subject_color(subject_name):
    """Assign consistent colors based on subject name"""
    colors = ["#FF9999","#99CCFF","#99FF99","#FFCC99","#CC99FF","#FFFF99","#66CC99","#FF66CC"]
    return colors[hash(subject_name)%len(colors)]

# --- Initialize session_state ---

if "children" not in st.session_state:
    st.session_state.children = ["Child 1", "Child 2"]
if "subjects" not in st.session_state:
    st.session_state.subjects = {child: [] for child in st.session_state.children}
if "fixed_commitments" not in st.session_state:
    st.session_state.fixed_commitments = []

# --- Page Layout ---
st.title("📝 Homeschool Planner v1.0 Prototype")

# --- Inputs Section ---
with st.expander("Configure Children & Subjects"):
    # Children
    children_text = st.text_input("Children (comma-separated)", ",".join(st.session_state.children))
    st.session_state.children = [c.strip() for c in children_text.split(",") if c.strip()]

    # Subjects per child
    for child in st.session_state.children:
        st.subheader(f"{child} Subjects")
        if child not in st.session_state.subjects:
            st.session_state.subjects[child] = []
        # Add a new subject
        new_name = st.text_input(f"{child} - New Subject Name", key=f"{child}_new_name")
        new_duration = st.selectbox(f"{child} - Duration", [15,30,60], key=f"{child}_new_duration")
        new_sessions = st.number_input(f"{child} - Sessions per week", min_value=1, max_value=8, value=1, key=f"{child}_new_sessions")
        new_shared = st.checkbox("Shared", key=f"{child}_new_shared")
        if st.button(f"Add Subject to {child}", key=f"{child}_add_btn"):
            st.session_state.subjects[child].append({
                "name": new_name,
                "duration": new_duration,
                "sessions": new_sessions,
                "shared": new_shared
            })

    # Fixed commitments
    st.subheader("Fixed Commitments")
    new_fc_name = st.text_input("Commitment Name", key="fc_name")
    new_fc_hour = st.number_input("Start Hour (24h)", min_value=0, max_value=17, key="fc_hour")
    new_fc_shared = st.checkbox("Shared", key="fc_shared")
    if st.button("Add Fixed Commitment"):
        st.session_state.fixed_commitments.append((new_fc_hour, new_fc_name, new_fc_shared))

    # Day selection and start time
    st.subheader("Schedule Settings")
    start_hour = st.number_input("Day Start Hour", min_value=0, max_value=16, value=7)
    days_options = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    selected_days = st.multiselect("Select Days", days_options, default=days_options[:5])

# --- Autofill / Generate Schedule ---
if st.button("Generate Weekly Schedule"):
    weekly_schedule = generate_weekly_schedule(
        st.session_state.subjects,
        selected_days,
        start_hour,
        17,
        st.session_state.fixed_commitments
    )
    st.session_state.weekly_schedule = weekly_schedule

# --- Schedule Display ---
if "weekly_schedule" in st.session_state:
    st.subheader("Weekly Schedule")
    for day in selected_days:
        st.markdown(f"### {day}")
        cols = st.columns(len(st.session_state.children))
        for i, child in enumerate(st.session_state.children):
            with cols[i]:
                st.markdown(f"**{child}**")
                table = st.session_state.weekly_schedule[child][day]
                for entry in table:
                    subject = entry["Subject"]
                    color = get_subject_color(subject.split(" (")[0])
                    st.markdown(f"<div style='background-color:{color};padding:2px;margin:1px;border-radius:3px;'>{entry['Time']} - {subject}</div>", unsafe_allow_html=True)

# --- End of Prototype ---
