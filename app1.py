import streamlit as st
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="Homeschool Wizard Planner", layout="wide", initial_sidebar_state="collapsed")

# ---------------- Custom CSS ----------------
st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; color: #4A90E2; text-align: center; margin-bottom: 1rem; }
.sub-header { font-size: 1.3rem; font-weight: 600; color: #2C3E50; margin-top: 1rem; margin-bottom: 0.5rem; }
.schedule-cell { padding: 10px; border-radius: 10px; margin: 3px 0; color: white; font-weight: 500; text-align:center; }
.schedule-math { background: #667eea; }
.schedule-reading { background: #38b2ac; }
.schedule-writing { background: #f6ad55; }
.schedule-science { background: #68d391; }
.schedule-other { background: #a0aec0; }
.stButton>button { border-radius: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------- Session State ----------------
if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 0
if "kids" not in st.session_state:
    st.session_state.kids = [""]  # Default 1 child
if "subjects" not in st.session_state:
    # Predefined subjects
    st.session_state.subjects = [
        {"name":"Math","sessions":3,"duration":60,"kids":[],"emoji":"🔢"},
        {"name":"Reading","sessions":3,"duration":45,"kids":[],"emoji":"📖"},
        {"name":"Writing","sessions":2,"duration":45,"kids":[],"emoji":"✍️"},
        {"name":"Science","sessions":2,"duration":60,"kids":[],"emoji":"🔬"},
    ]
if "commitments" not in st.session_state:
    st.session_state.commitments = []
if "schedule" not in st.session_state:
    st.session_state.schedule = None
if "pressure" not in st.session_state:
    st.session_state.pressure = "Standard"
if "start_time" not in st.session_state:
    st.session_state.start_time = time(8,0)
if "end_time" not in st.session_state:
    st.session_state.end_time = time(15,0)
if "block_size" not in st.session_state:
    st.session_state.block_size = 30

# ---------------- Wizard Navigation ----------------
def next_step():
    st.session_state.wizard_step += 1
def prev_step():
    st.session_state.wizard_step -= 1

st.markdown('<div class="main-header">🏫 Homeschool Wizard Planner</div>', unsafe_allow_html=True)

# ---------------- Step 0: Welcome ----------------
if st.session_state.wizard_step == 0:
    st.write("Welcome! Let’s create a beautiful homeschool schedule in a few easy steps. Press Next to begin.")
    if st.button("➡️ Start Setup"):
        next_step()

# ---------------- Step 1: Children ----------------
if st.session_state.wizard_step == 1:
    st.markdown('<div class="sub-header">👨‍👩‍👧‍👦 Children</div>', unsafe_allow_html=True)
    for i, kid in enumerate(st.session_state.kids):
        col1, col2 = st.columns([4,1])
        with col1:
            st.session_state.kids[i] = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}")
        with col2:
            if st.button("🗑️", key=f"rm_kid_{i}") and len(st.session_state.kids)>1:
                st.session_state.kids.pop(i)
                st.experimental_rerun()
    if st.button("➕ Add Child"):
        st.session_state.kids.append("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            prev_step()
    with col2:
        if st.button("➡️ Next"):
            if any(k.strip() for k in st.session_state.kids):
                next_step()
            else:
                st.error("Please enter at least one child.")

# ---------------- Step 2: Subjects ----------------
if st.session_state.wizard_step == 2:
    st.markdown('<div class="sub-header">📚 Subjects</div>', unsafe_allow_html=True)
    for i, subj in enumerate(st.session_state.subjects):
        st.write(f"**{subj['emoji']} {subj['name']}**")
        col1, col2, col3, col4 = st.columns([3,1,1,3])
        with col1:
            st.session_state.subjects[i]['name'] = st.text_input("Subject Name", subj['name'], key=f"subj_name_{i}")
        with col2:
            st.session_state.subjects[i]['emoji'] = st.text_input("Emoji", subj['emoji'], key=f"subj_emoji_{i}", max_chars=2)
        with col3:
            st.session_state.subjects[i]['sessions'] = st.number_input("Sessions/week", min_value=1, value=subj['sessions'], key=f"subj_sessions_{i}")
        with col4:
            st.session_state.subjects[i]['duration'] = st.number_input("Duration (min)", min_value=15, step=15, value=subj['duration'], key=f"subj_dur_{i}")
        st.write("Select children for this subject:")
        kid_cols = st.columns(min(len(st.session_state.kids),5))
        selected_kids = []
        for idx, kid in enumerate(st.session_state.kids):
            with kid_cols[idx % len(kid_cols)]:
                if st.checkbox(kid, key=f"subj_{i}_kid_{kid}", value=kid in subj['kids']):
                    selected_kids.append(kid)
        st.session_state.subjects[i]['kids'] = selected_kids
        st.markdown("---")
    if st.button("➕ Add Custom Subject"):
        st.session_state.subjects.append({"name":"New Subject","sessions":1,"duration":30,"kids":[],"emoji":"📚"})
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            prev_step()
    with col2:
        if st.button("➡️ Next"):
            next_step()

# ---------------- Step 3: Commitments ----------------
if st.session_state.wizard_step == 3:
    st.markdown('<div class="sub-header">📅 Commitments (Optional)</div>', unsafe_allow_html=True)
    for i, c in enumerate(st.session_state.commitments):
        col1, col2, col3, col4, col5 = st.columns([2,2,1,2,3])
        with col1:
            c['day'] = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"], index=["Monday","Tuesday","Wednesday","Thursday","Friday"].index(c.get('day','Monday')), key=f"comm_day_{i}")
        with col2:
            c['time'] = st.time_input("Time", value=c.get('time',time(14,0)), key=f"comm_time_{i}")
        with col3:
            c['duration'] = st.number_input("Duration", min_value=15, step=15, value=c.get('duration',60), key=f"comm_dur_{i}")
        with col4:
            c['activity'] = st.text_input("Activity", c.get('activity',''), key=f"comm_act_{i}")
        with col5:
            st.write("Children:")
            kid_cols = st.columns(min(len(st.session_state.kids),5))
            selected_kids=[]
            for idx, kid in enumerate(st.session_state.kids):
                with kid_cols[idx % len(kid_cols)]:
                    if st.checkbox(kid, key=f"comm_{i}_kid_{kid}", value=kid in c.get('kids',[])):
                        selected_kids.append(kid)
            c['kids'] = selected_kids
    if st.button("➕ Add Commitment"):
        st.session_state.commitments.append({'day':'Monday','time':time(14,0),'duration':60,'activity':'','kids':[]})
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            prev_step()
    with col2:
        if st.button("➡️ Next"):
            next_step()

# ---------------- Step 4: Schedule Settings ----------------
if st.session_state.wizard_step == 4:
    st.markdown('<div class="sub-header">⚙️ Schedule Settings</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.session_state.start_time = st.time_input("Start Time", st.session_state.start_time)
    with col2:
        st.session_state.end_time = st.time_input("End Time", st.session_state.end_time)
    with col3:
        st.session_state.block_size = st.selectbox("Block Size (min)", [15,30,60], index=[15,30,60].index(st.session_state.block_size))
    with col4:
        st.session_state.pressure = st.selectbox("Schedule Pressure", ["Gentle","Standard","Ambitious"], index=["Gentle","Standard","Ambitious"].index(st.session_state.pressure))
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back"):
            prev_step()
    with col2:
        if st.button("➡️ Generate Schedule"):
            next_step()

# ---------------- Step 5: Generate Schedule ----------------
def generate_schedule():
    start_minutes = st.session_state.start_time.hour*60+st.session_state.start_time.minute
    end_minutes = st.session_state.end_time.hour*60+st.session_state.end_time.minute
    slots = list(range(start_minutes, end_minutes, st.session_state.block_size))
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    grid = {day:{kid:{s:None for s in slots} for kid in st.session_state.kids} for day in days}

    # Place commitments
    for c in st.session_state.commitments:
        kids = c['kids'] if c['kids'] else st.session_state.kids
        blocks = max(1, c['duration']//st.session_state.block_size)
        time_block = c['time'].hour*60+c['time'].minute
        for b in range(blocks):
            for kid in kids:
                if time_block+b*st.session_state.block_size in grid[c['day']][kid]:
                    grid[c['day']][kid][time_block+b*st.session_state.block_size] = {"subject":c['activity'],"fixed":True}
    # Place subjects
    for subj in st.session_state.subjects:
        kids = subj['kids'] if subj['kids'] else st.session_state.kids
        blocks = max(1, subj['duration']//st.session_state.block_size)
        # Determine number of sessions based on pressure
        if st.session_state.pressure=="Gentle":
            sessions = max(1, subj['sessions']-1)
        elif st.session_state.pressure=="Ambitious":
            sessions = subj['sessions']+1
        else:
            sessions = subj['sessions']
        day_idx=0
        for _ in range(sessions):
            while day_idx<len(days):
                day=days[day_idx]
                for i in range(len(slots)-blocks+1):
                    available = all(grid[day][kid][slots[i]+b*st.session_state.block_size] is None for kid in kids for b in range(blocks))
                    if available:
                        for kid in kids:
                            for b in range(blocks):
                                grid[day][kid][slots[i]+b*st.session_state.block_size]={"subject":subj['name'],"shared":len(kids)>1}
                        day_idx+=1
                        break
                day_idx+=1
    return {"grid":grid,"slots":slots,"days":days,"kids":st.session_state.kids}

if st.session_state.wizard_step == 5:
    st.session_state.schedule = generate_schedule()
    st.markdown('<div class="sub-header">📆 Weekly Schedule</div>', unsafe_allow_html=True)
    schedule = st.session_state.schedule
    for day in schedule['days']:
        st.markdown(f"### {day}")
        for kid in schedule['kids']:
            st.markdown(f"**{kid}**")
            row=[]
            for s in schedule['slots']:
                cell = schedule['grid'][day][kid][s]
                if cell:
                    subj = cell['subject']
                    cls="schedule-other"
                    if subj.lower()=="math": cls="schedule-math"
                    elif subj.lower()=="reading": cls="schedule-reading"
                    elif subj.lower()=="writing": cls="schedule-writing"
                    elif subj.lower()=="science": cls="schedule-science"
                    row.append(f"<div class='schedule-cell {cls}'>{subj}</div>")
                else:
                    row.append("<div class='schedule-cell schedule-other' style='background:#e2e8f0'> </div>")
            st.markdown("".join(row), unsafe_allow_html=True)
    if st.button("⬅️ Back to Settings"):
        st.session_state.wizard_step=4
