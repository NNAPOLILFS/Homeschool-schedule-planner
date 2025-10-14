"""
Homeschool Planner - Version 0.7.d
Changes:
- Clean layout with consistent compact rows for subjects, better mobile/desktop view
- Persistent st.session_state for all inputs (children, subjects, durations, sessions, shared flags, fixed commitments)
- Children schedules displayed side-by-side per day
- Color-coded subjects based on subject name
- Full schedule generation preserved
"""

import streamlit as st
import pandas as pd

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
        for minute in [0,15,30,45]:
            slots.append(hour*60 + minute)
    schedule_dict = {s: None for s in slots}
    # Fixed commitments
    for fc_hour, fc_name, fc_shared in fixed_commitments:
        slot = fc_hour*60
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
                        schedule_dict[current_slot+b*15] = (subj["name"], subj["shared"])
                    slot_idx += blocks
                    break
            slot_idx +=1
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
if "children_text" not in st.session_state:
    st.session_state.children_text = "Child 1,Child 2"
if "start_hour" not in st.session_state:
    st.session_state.start_hour = 7
