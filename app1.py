import streamlit as st
from datetime import datetime, time
import pandas as pd

st.set_page_config(page_title="Homeschool Planner", layout="wide")

# --------------------------
# Default Data
# --------------------------
DEFAULT_SUBJECTS = [
    {'name': 'Math', 'emoji': '🔢', 'sessions': 3, 'duration': 60, 'kids': []},
    {'name': 'Reading', 'emoji': '📖', 'sessions': 3, 'duration': 45, 'kids': []},
    {'name': 'Writing', 'emoji': '✍️', 'sessions': 2, 'duration': 45, 'kids': []},
    {'name': 'Science', 'emoji': '🔬', 'sessions': 2, 'duration': 60, 'kids': []},
]

# --------------------------
# Session State Initialization
# --------------------------
if 'kids' not in st.session_state:
    st.session_state.kids = ['Child 1']
if 'subjects' not in st.session_state:
    st.session_state.subjects = DEFAULT_SUBJECTS.copy()
if 'commitments' not in st.session_state:
    st.session_state.commitments = []
if 'generated_schedule' not in st.session_state:
    st.session_state.generated_schedule = None

# --------------------------
# Sidebar Settings
# --------------------------
with st.sidebar:
    st.header("Schedule Settings")
    start_time = st.time_input("Start Time", value=time(8,0))
    end_time = st.time_input("End Time", value=time(15,0))
    block_size = st.selectbox("Block Size (minutes)", [15, 30, 60], index=1)
    include_weekend = st.checkbox("Include Weekends", value=False)

# --------------------------
# Page Header
# --------------------------
st.title("🏫 Homeschool Planner")

# --------------------------
# Children Section
# --------------------------
st.subheader("👨‍👩‍👧‍👦 Children")
for i, kid in enumerate(st.session_state.kids):
    col1, col2 = st.columns([4,1])
    with col1:
        st.session_state.kids[i] = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}", label_visibility="collapsed")
    with col2:
        if st.button("🗑️", key=f"rm_kid_{i}") and len(st.session_state.kids) > 1:
            st.session_state.kids.pop(i)
            st.experimental_rerun()

if st.button("➕ Add Child"):
    st.session_state.kids.append(f"Child {len(st.session_state.kids)+1}")
    st.experimental_rerun()

# --------------------------
# Subjects Section
# --------------------------
st.subheader("📚 Subjects")
for i, subj in enumerate(st.session_state.subjects):
    st.markdown(f"**{subj['emoji']} {subj['name']}**")
    col1, col2, col3, col4 = st.columns([3,1,1,1])
    with col1:
        st.session_state.subjects[i]['name'] = st.text_input("Subject Name", value=subj['name'], key=f"subj_name_{i}", label_visibility="collapsed")
    with col2:
        st.session_state.subjects[i]['emoji'] = st.text_input("Emoji", value=subj['emoji'], max_chars=2, key=f"subj_emoji_{i}", label_visibility="collapsed")
    with col3:
        st.session_state.subjects[i]['sessions'] = st.number_input("Sessions/Wk", min_value=1, value=subj['sessions'], key=f"subj_sess_{i}", label_visibility="collapsed")
    with col4:
        st.session_state.subjects[i]['duration'] = st.number_input("Duration (min)", min_value=15, step=15, value=subj['duration'], key=f"subj_dur_{i}", label_visibility="collapsed")
    
    # Assign kids
    kid_cols = st.columns(len(st.session_state.kids))
    assigned_kids = []
    for idx, kid in enumerate(st.session_state.kids):
        with kid_cols[idx]:
            if st.checkbox(kid, value=kid in subj['kids'], key=f"subj_{i}_kid_{kid}"):
                assigned_kids.append(kid)
    st.session_state.subjects[i]['kids'] = assigned_kids
    
    if st.button("🗑️ Remove Subject", key=f"rm_subj_{i}") and len(st.session_state.subjects) > 1:
        st.session_state.subjects.pop(i)
        st.experimental_rerun()

if st.button("➕ Add Subject"):
    st.session_state.subjects.append({'name': '', 'emoji':'📚','sessions':2,'duration':45,'kids':[]})
    st.experimental_rerun()

# --------------------------
# Generate Schedule
# --------------------------
def generate_schedule(kids, subjects, start_time, end_time, block_size, include_weekend):
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday']
    if include_weekend:
        days += ['Saturday','Sunday']
    
    time_slots = []
    start_minutes = start_time.hour*60 + start_time.minute
    end_minutes = end_time.hour*60 + end_time.minute
    for m in range(start_minutes, end_minutes, block_size):
        h = m // 60
        min_val = m % 60
        time_slots.append(f"{h:02d}:{min_val:02d}")
    
    grid = {day:{kid:{time_slot:None for time_slot in time_slots} for kid in kids} for day in days}
    
    for subj in subjects:
        for kid in subj['kids']:
            sessions_scheduled = 0
            day_idx = 0
            while sessions_scheduled < subj['sessions']:
                day = days[day_idx%len(days)]
                # Find first available slot
                for t_idx in range(len(time_slots)):
                    if all(grid[day][kid][time_slots[t_idx + b]] is None for b in range(min(len(time_slots)-t_idx, subj['duration']//block_size))):
                        for b in range(min(len(time_slots)-t_idx, subj['duration']//block_size)):
                            grid[day][kid][time_slots[t_idx+b]] = subj
                        sessions_scheduled += 1
                        break
                day_idx += 1
    return {'grid':grid,'time_slots':time_slots,'days':days,'kids':kids}

if st.button("🎯 Generate Schedule"):
    if st.session_state.kids and st.session_state.subjects:
        st.session_state.generated_schedule = generate_schedule(
            st.session_state.kids,
            st.session_state.subjects,
            start_time, end_time, block_size, include_weekend
        )
        st.success("✅ Schedule generated!")

# --------------------------
# Display Schedule
# --------------------------
if st.session_state.generated_schedule:
    sched = st.session_state.generated_schedule
    st.subheader("📅 Weekly Schedule")
    selected_day = st.selectbox("Select Day", sched['days'])
    
    for kid in sched['kids']:
        st.markdown(f"### 👤 {kid}")
        for time in sched['time_slots']:
            subj = sched['grid'][selected_day][kid][time]
            if subj and subj['emoji'] and subj['name']:
                st.markdown(f"<div style='padding:8px; margin:2px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-radius:6px;'>{time} {subj['emoji']} {subj['name']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"{time} - Free")
