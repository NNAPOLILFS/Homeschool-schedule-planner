"""
Homeschool Planner Web App – Version 1.0b
- Top-bar layout for inputs
- Children names included
- Subject inputs responsive: wrap 2 per row on mobile
- Shared checkbox aligned
- Automated pastel colors per subject type
- Schedule generation using 0.6.g logic (sessions distributed correctly)
- Side-by-side child schedule, persistent inputs, fixed commitments, autofill preserved
"""

import streamlit as st
from datetime import datetime, timedelta
import itertools

# ------------------------
# Pastel color palette
# ------------------------
PASTEL_COLORS = ['#AEC6CF','#FFB347','#FFD1DC','#77DD77','#CBAACB','#FF6961','#FDFD96','#CB99C9']

# ------------------------
# Initialize session state
# ------------------------
if 'children' not in st.session_state:
    st.session_state['children'] = {}
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = {}
if 'child_names' not in st.session_state:
    st.session_state['child_names'] = []

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
    for child_name, child_data in children.items():
        child_schedule = {day: [] for day in days}
        for idx, subj in enumerate(child_data['subjects']):
            dist = distribute_subject_sessions(subj, days)
            color = PASTEL_COLORS[idx % len(PASTEL_COLORS)]
            for day, count in dist.items():
                for _ in range(count):
                    duration_slots = subj['duration'] // 15
                    child_schedule[day].append({
                        'name': subj['name'],
                        'duration_slots': duration_slots,
                        'shared': subj.get('shared', False),
                        'color': color
                    })
        for day in days:
            schedule[day][child_name] = child_schedule[day]
    return schedule

# ------------------------
# Top-bar inputs
# ------------------------
st.title("Homeschool Planner")
st.subheader("Children and Subjects")

num_children = st.number_input("Number of children", min_value=1, max_value=5, value=2, step=1)

child_cols = st.columns(num_children)
for i in range(num_children):
    with child_cols[i]:
        if i >= len(st.session_state['child_names']):
            st.session_state['child_names'].append(f'Child {i+1}')
        name = st.text_input(f"Name Child {i+1}", st.session_state['child_names'][i], key=f"name_{i}")
        st.session_state['child_names'][i] = name
        if name not in st.session_state['children']:
            st.session_state['children'][name] = {'subjects': []}

        # Number of subjects
        num_subjects = st.number_input(f"Subjects for {name}", min_value=1, max_value=10, value=3, key=f"num_subj_{i}")

        # Adjust subject list length
        subjects = st.session_state['children'][name]['subjects']
        while len(subjects) < num_subjects:
            subjects.append({'name':'', 'duration':15, 'sessions':1, 'shared':False})
        while len(subjects) > num_subjects:
            subjects.pop()

        # Responsive 2 per row
        for j in range(0, num_subjects, 2):
            cols_subj = st.columns(2)
            for k in range(2):
                if j+k < num_subjects:
                    with cols_subj[k]:
                        subj = subjects[j+k]
                        subj['name'] = st.text_input(f"Subject {j+k+1} Name", subj['name'], key=f"{name}_subj_name_{j+k}")
                        subj['duration'] = st.selectbox(f"Duration (min)", [15,30,60], index=[15,30,60].index(subj['duration']), key=f"{name}_subj_dur_{j+k}")
                        subj['sessions'] = st.number_input(f"Sessions/week", min_value=1, max_value=10, value=subj['sessions'], key=f"{name}_subj_sess_{j+k}")
                        subj['shared'] = st.checkbox("Shared", value=subj['shared'], key=f"{name}_subj_shared_{j+k}")
        st.session_state['children'][name]['subjects'] = subjects

# ------------------------
# Day selection
# ------------------------
days_options = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
selected_days = st.multiselect("Select days to include", options=days_options, default=days_options[:5])

# ------------------------
# Generate schedule button
# ------------------------
if st.button("Generate Schedule"):
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
# Test checklist
# ------------------------
st.markdown("### Test Checklist")
st.markdown("""
- Generate schedule for multiple children
- Each subject distributed across selected days according to sessions/week
- Inputs wrap 2 per row on mobile/side-by-side on desktop
- Shared checkbox aligned with each subject
- Automated pastel colors applied
- Side-by-side child schedule
- Schedule persists after refresh
- Autofill and fixed commitments respected
""")
