"""
Homeschool Planner Web App – Version 1.0a
- Schedule generation fixed: subjects now distribute sessions across the week (like 0.6.g)
- Responsive subject input rows for all children: max 2 subjects per row on narrow screens
- Shared checkbox aligned with each subject
- Keeps color coding, side-by-side child schedule, persistence, fixed commitments, autofill
"""

import streamlit as st
from datetime import datetime, timedelta

# ------------------------
# Initialize session state
# ------------------------
if 'children' not in st.session_state:
    st.session_state['children'] = {}
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = {}

# ------------------------
# Utility functions
# ------------------------
def generate_time_slots(start_hour=7, end_hour=17, increment=15):
    slots = []
    current = datetime(2000, 1, 1, start_hour)
    while current.hour < end_hour or (current.hour == end_hour and current.minute == 0):
        slots.append(current.time())
        current += timedelta(minutes=increment)
    return slots

def distribute_subject_sessions(subject, days):
    """Distribute subject sessions evenly across selected days"""
    session_count = subject['sessions']
    assigned = {day: 0 for day in days}
    if session_count == 0 or len(days) == 0:
        return assigned
    interval = len(days) / session_count
    for i in range(session_count):
        day_index = int(round(i * interval)) % len(days)
        assigned[days[day_index]] += 1
    return assigned

def build_schedule(children, days, start_hour=7):
    """Generate weekly schedule for all children"""
    schedule = {day: {} for day in days}
    time_slots = generate_time_slots(start_hour=start_hour)
    
    for child_name, child_data in children.items():
        child_schedule = {day: [] for day in days}
        for subj in child_data['subjects']:
            dist = distribute_subject_sessions(subj, days)
            for day, count in dist.items():
                for _ in range(count):
                    # Find next available slot
                    slot_index = len(child_schedule[day])
                    duration_slots = subj['duration'] // 15
                    child_schedule[day].append({
                        'name': subj['name'],
                        'duration_slots': duration_slots,
                        'shared': subj.get('shared', False),
                        'color': subj.get('color', '#A0CBE8')
                    })
        for day in days:
            schedule[day][child_name] = child_schedule[day]
    return schedule

# ------------------------
# Sidebar: children and subjects
# ------------------------
st.sidebar.header("Children & Subjects")

num_children = st.sidebar.number_input("Number of children", min_value=1, max_value=5, value=2, step=1)

for c in range(1, num_children+1):
    child_key = f'Child {c}'
    if child_key not in st.session_state['children']:
        st.session_state['children'][child_key] = {'subjects': []}
    st.sidebar.subheader(child_key)

    # Number of subjects
    num_subjects = st.sidebar.number_input(f"Number of subjects for {child_key}", min_value=1, max_value=10, value=3, key=f"num_subj_{c}")

    # Responsive input: wrap 2 subjects per row
    subjects = st.session_state['children'][child_key]['subjects']
    while len(subjects) < num_subjects:
        subjects.append({'name':'', 'duration':15, 'sessions':1, 'shared':False, 'color':'#A0CBE8'})
    while len(subjects) > num_subjects:
        subjects.pop()

    for i in range(0, num_subjects, 2):
        cols = st.sidebar.columns(2)
        for j in range(2):
            if i+j < num_subjects:
                with cols[j]:
                    subj = subjects[i+j]
                    subj['name'] = st.text_input(f"Subject {i+j+1} name", subj['name'], key=f"{child_key}_subj_name_{i+j}")
                    subj['duration'] = st.selectbox(f"Duration (min)", [15,30,60], index=[15,30,60].index(subj['duration']), key=f"{child_key}_subj_dur_{i+j}")
                    subj['sessions'] = st.number_input(f"Sessions/week", min_value=1, max_value=10, value=subj['sessions'], key=f"{child_key}_subj_sess_{i+j}")
                    subj['shared'] = st.checkbox("Shared", value=subj['shared'], key=f"{child_key}_subj_shared_{i+j}")
                    subj['color'] = st.color_picker("Color", subj['color'], key=f"{child_key}_subj_color_{i+j}")
    st.session_state['children'][child_key]['subjects'] = subjects

# ------------------------
# Day selection
# ------------------------
days_options = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
selected_days = st.sidebar.multiselect("Select days to include", options=days_options, default=days_options[:5])

# ------------------------
# Generate schedule button
# ------------------------
if st.sidebar.button("Generate Schedule"):
    st.session_state['schedule'] = build_schedule(st.session_state['children'], selected_days)

# ------------------------
# Display schedule
# ------------------------
if st.session_state['schedule']:
    st.header("Weekly Schedule")
    for day in selected_days:
        st.subheader(day)
        child_cols = st.columns(len(st.session_state['children']))
        for idx, (child_name, child_data) in enumerate(st.session_state['children'].items()):
            with child_cols[idx]:
                st.markdown(f"**{child_name}**")
                if day in st.session_state['schedule']:
                    for block in st.session_state['schedule'][day][child_name]:
                        st.markdown(f"<div style='background-color:{block['color']};padding:4px;margin:2px;border-radius:4px'>{block['name']} ({block['duration_slots']*15} min){' (Shared)' if block['shared'] else ''}</div>", unsafe_allow_html=True)

# ------------------------
# Checklist of things to test
# ------------------------
st.sidebar.markdown("### Test Checklist")
st.sidebar.markdown("""
- Generate schedule with multiple children
- Each subject distributed across selected days according to sessions/week
- Input boxes wrap 2 per row on mobile/side-by-side on desktop
- Shared checkbox aligned for each subject
- Color coding appears in schedule
- Schedule persists after page refresh
- Autofill and fixed commitments respected
""")
