import streamlit as st
from datetime import datetime, time
import pandas as pd

st.set_page_config(page_title="Homeschool Planner", layout="wide")

# ------------------- SESSION STATE INIT -------------------
if 'wizard_step' not in st.session_state:
    st.session_state.wizard_step = 'kids'  # kids -> subjects -> commitments
if 'kids' not in st.session_state:
    st.session_state.kids = []
if 'subjects' not in st.session_state:
    st.session_state.subjects = []
if 'commitments' not in st.session_state:
    st.session_state.commitments = []
if 'generated_schedule' not in st.session_state:
    st.session_state.generated_schedule = None

# ------------------- DEFAULT EMOJI -------------------
DEFAULT_EMOJI = {
    'math': '🔢', 'reading': '📖', 'writing': '✍️', 'science': '🔬',
    'history': '📜', 'geography': '🌍', 'art': '🎨', 'music': '🎵',
    'pe': '⚽', 'spanish': '🇪🇸', 'french': '🇫🇷', 'language': '💬',
    'bible': '✝️', 'nature': '🌿', 'coding': '💻', 'default': '📚'
}

def get_emoji_for_subject(name):
    name_lower = name.lower()
    for key in DEFAULT_EMOJI:
        if key in name_lower:
            return DEFAULT_EMOJI[key]
    return DEFAULT_EMOJI['default']

# ------------------- SIDEBAR SETTINGS -------------------
st.sidebar.header("⚙️ Schedule Settings")
start_time = st.sidebar.time_input("Start Time", value=time(8,0))
end_time = st.sidebar.time_input("End Time", value=time(15,0))
block_size = st.sidebar.selectbox("Block Size", [15,30,60], index=1)
include_weekend = st.sidebar.checkbox("Include Weekend", value=False)
pressure = st.sidebar.radio("Rhythm Pressure", ["Gentle", "Moderate", "Ambitious"], index=1)

# ------------------- WIZARD -------------------
st.title("🏫 Homeschool Planner")

def wizard_nav(next_step):
    st.session_state.wizard_step = next_step
    st.experimental_rerun()

if st.session_state.wizard_step == 'kids':
    st.header("👨‍👩‍👧‍👦 Add Your Children")
    for i, kid in enumerate(st.session_state.kids):
        col1, col2 = st.columns([3,1])
        with col1:
            st.session_state.kids[i] = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}")
        with col2:
            if st.button("🗑️", key=f"rm_kid_{i}") and len(st.session_state.kids)>0:
                st.session_state.kids.pop(i)
                st.experimental_rerun()
    if st.button("➕ Add Child"):
        st.session_state.kids.append("")
    if st.session_state.kids:
        st.button("➡️ Next: Subjects", on_click=wizard_nav, args=('subjects',))

elif st.session_state.wizard_step == 'subjects':
    st.header("📚 Add Subjects")
    predefined_subjects = ['Math', 'Reading', 'Writing', 'Science', 'History', 'Art', 'Music', 'PE']
    
    for i, subj in enumerate(st.session_state.subjects):
        st.subheader(f"Subject {i+1}")
        col1, col2 = st.columns([3,1])
        with col1:
            name = st.selectbox("Select or type subject", predefined_subjects + [subj.get('name','')], index=predefined_subjects.index(subj['name']) if subj.get('name') in predefined_subjects else 0, key=f"subj_name_{i}")
            st.session_state.subjects[i]['name'] = name
            st.session_state.subjects[i]['emoji'] = get_emoji_for_subject(name)
        with col2:
            if st.button("🗑️", key=f"rm_subj_{i}"):
                st.session_state.subjects.pop(i)
                st.experimental_rerun()
        st.number_input("Sessions per week", min_value=1, value=subj.get('sessions',3), key=f"sess_{i}", help="How many times per week this subject occurs")
        st.number_input("Duration (min)", min_value=15, step=15, value=subj.get('duration',60), key=f"dur_{i}", help="Duration of each session")
        st.multiselect("Children", options=st.session_state.kids, default=subj.get('kids',[]), key=f"kids_{i}", help="Select children taking this subject")
        st.markdown("---")
    if st.button("➕ Add Subject"):
        st.session_state.subjects.append({'name':'', 'sessions':3, 'duration':60, 'kids':[]})
    if st.session_state.subjects:
        st.button("➡️ Next: Commitments", on_click=wizard_nav, args=('commitments',))
        st.button("⬅️ Back", on_click=wizard_nav, args=('kids',))

elif st.session_state.wizard_step == 'commitments':
    st.header("📅 Add Fixed Commitments")
    for i, comm in enumerate(st.session_state.commitments):
        st.subheader(f"Commitment {i+1}")
        col1, col2 = st.columns([3,1])
        with col1:
            comm['activity'] = st.text_input("Activity Name", value=comm.get('activity',''), key=f"comm_name_{i}")
        with col2:
            if st.button("🗑️", key=f"rm_comm_{i}"):
                st.session_state.commitments.pop(i)
                st.experimental_rerun()
        comm['day'] = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], index=0 if comm.get('day') not in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"] else ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(comm['day']), key=f"comm_day_{i}")
        comm['time'] = st.time_input("Time", value=comm.get('time',time(14,0)), key=f"comm_time_{i}")
        comm['duration'] = st.number_input("Duration (min)", min_value=15, step=15, value=comm.get('duration',60), key=f"comm_dur_{i}")
        comm['kids'] = st.multiselect("Children", options=st.session_state.kids, default=comm.get('kids',[]), key=f"comm_kids_{i}")
        st.markdown("---")
    if st.button("➕ Add Commitment"):
        st.session_state.commitments.append({'activity':'','day':'Monday','time':time(14,0),'duration':60,'kids':[]})
    st.button("⬅️ Back", on_click=wizard_nav, args=('subjects',))
    if st.button("🎯 Generate Schedule"):
        st.session_state.wizard_step = 'done'
        st.experimental_rerun()

# ------------------- SCHEDULE GENERATION -------------------
def generate_schedule(kids, subjects, commitments, start_time, end_time, block_size, include_weekend):
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    if include_weekend:
        days += ["Saturday","Sunday"]
    time_slots = pd.date_range(start=datetime.combine(datetime.today(), start_time), end=datetime.combine(datetime.today(), end_time), freq=f"{block_size}min").time
    grid = {day:{kid:{t:None for t in time_slots} for kid in kids} for day in days}

    # Fill commitments
    for c in commitments:
        slots_needed = int(c['duration']/block_size)
        try:
            start_idx = list(time_slots).index(c['time'])
        except ValueError:
            continue
        for kid in c['kids'] if c['kids'] else kids:
            for b in range(slots_needed):
                if start_idx+b < len(time_slots):
                    grid[c['day']][kid][time_slots[start_idx+b]] = {'subject':c['activity'],'fixed':True,'isStart':b==0,'emoji':'📅'}

    # Fill subjects
    for s in subjects:
        slots_needed = int(s['duration']/block_size)
        sessions = s['sessions']
        subj_kids = s['kids'] if s['kids'] else kids
        day_idx = 0
        scheduled = 0
        while scheduled < sessions:
            day = days[day_idx%len(days)]
            for i in range(len(time_slots)-slots_needed+1):
                conflict = False
                for kid in subj_kids:
                    for b in range(slots_needed):
                        if grid[day][kid][time_slots[i+b]] is not None:
                            conflict = True
                            break
                    if conflict:
                        break
                if not conflict:
                    for kid in subj_kids:
                        for b in range(slots_needed):
                            grid[day][kid][time_slots[i+b]] = {'subject':s['name'],'shared':len(subj_kids)>1,'isStart':b==0,'emoji':s['emoji']}
                    scheduled += 1
                    break
            day_idx += 1

    return {'grid':grid,'days':days,'time_slots':time_slots,'kids':kids}

# ------------------- SCHEDULE VIEW -------------------
if st.session_state.wizard_step == 'done':
    st.header("📅 Weekly Schedule")
    schedule = generate_schedule(st.session_state.kids, st.session_state.subjects, st.session_state.commitments, start_time, end_time, block_size, include_weekend)
    for day in schedule['days']:
        st.subheader(day)
        df_data = []
        for t in schedule['time_slots']:
            row = {'Time': t.strftime("%H:%M")}
            for kid in schedule['kids']:
                cell = schedule['grid'][day][kid][t]
                if cell:
                    emoji = cell.get('emoji','📚')
                    row[kid] = f"{emoji} {cell['subject']}" if cell['isStart'] else "↓"
                else:
                    row[kid] = ""
            df_data.append(row)
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
