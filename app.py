```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Homeschool Planner", layout="wide")

# Initialize session state
if 'kids' not in st.session_state:
    st.session_state.kids = ['']
if 'subjects' not in st.session_state:
    st.session_state.subjects = [{'name': '', 'sessions': 3, 'duration': 60, 'kids': []}]
if 'commitments' not in st.session_state:
    st.session_state.commitments = [{'day': 'Monday', 'time': '14:00', 'duration': 60, 'activity': '', 'kids': []}]

st.title("🏫 Homeschool Planner")

# Settings Section
st.header("⚙️ Settings")
col1, col2, col3 = st.columns(3)

with col1:
    start_time = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
with col2:
    end_time = st.time_input("End Time", value=datetime.strptime("15:00", "%H:%M").time())
with col3:
    block_size = st.selectbox("Block Size (minutes)", [15, 30, 60], index=1)

col4, col5 = st.columns(2)
with col4:
    include_weekend = st.checkbox("Include Weekends")
with col5:
    back_to_back = st.checkbox("Back-to-back Sessions")

st.divider()

# Children Section
st.header("👨‍👩‍👧‍👦 Children")

for i, kid in enumerate(st.session_state.kids):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.session_state.kids[i] = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}")
    with col2:
        if len(st.session_state.kids) > 1:
            if st.button("🗑️", key=f"remove_kid_{i}"):
                st.session_state.kids.pop(i)
                st.rerun()

if st.button("➕ Add Child"):
    st.session_state.kids.append('')
    st.rerun()

st.divider()

# Subjects Section
st.header("📚 Subjects")

kids_list = [k for k in st.session_state.kids if k.strip()]

for i, subject in enumerate(st.session_state.subjects):
    with st.expander(f"Subject {i+1}: {subject['name'] or 'New Subject'}", expanded=not subject['name']):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.session_state.subjects[i]['name'] = st.text_input("Subject Name", value=subject['name'], key=f"subj_name_{i}")
        with col2:
            if st.button("🗑️", key=f"remove_subj_{i}"):
                st.session_state.subjects.pop(i)
                st.rerun()
        
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.subjects[i]['sessions'] = st.number_input("Sessions per week", min_value=1, value=subject['sessions'], key=f"subj_sess_{i}")
        with col4:
            st.session_state.subjects[i]['duration'] = st.number_input("Duration (minutes)", min_value=15, step=15, value=subject['duration'], key=f"subj_dur_{i}")
        
        if kids_list:
            st.write("Which children? (leave empty for all)")
            selected_kids = []
            cols = st.columns(min(len(kids_list), 4))
            for idx, kid in enumerate(kids_list):
                with cols[idx % len(cols)]:
                    if st.checkbox(kid, value=kid in subject['kids'], key=f"subj_{i}_kid_{kid}"):
                        selected_kids.append(kid)
            st.session_state.subjects[i]['kids'] = selected_kids

if st.button("➕ Add Subject"):
    st.session_state.subjects.append({'name': '', 'sessions': 3, 'duration': 60, 'kids': []})
    st.rerun()

st.divider()

# Fixed Commitments Section
st.header("📅 Fixed Commitments")

for i, commitment in enumerate(st.session_state.commitments):
    with st.expander(f"Commitment {i+1}: {commitment['activity'] or 'New Commitment'}", expanded=not commitment['activity']):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.session_state.commitments[i]['day'] = st.selectbox("Day", 
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(commitment['day']),
                key=f"comm_day_{i}")
        with col2:
            time_val = datetime.strptime(commitment['time'], "%H:%M").time()
            new_time = st.time_input("Start Time", value=time_val, key=f"comm_time_{i}")
            st.session_state.commitments[i]['time'] = new_time.strftime("%H:%M")
        with col3:
            st.session_state.commitments[i]['duration'] = st.number_input("Duration (min)", min_value=15, step=15, value=commitment['duration'], key=f"comm_dur_{i}")
        with col4:
            if st.button("🗑️", key=f"remove_comm_{i}"):
                st.session_state.commitments.pop(i)
                st.rerun()
        
        st.session_state.commitments[i]['activity'] = st.text_input("Activity Name", value=commitment['activity'], key=f"comm_act_{i}")
        
        if kids_list:
            st.write("Which children? (leave empty for all)")
            selected_kids = []
            cols = st.columns(min(len(kids_list), 4))
            for idx, kid in enumerate(kids_list):
                with cols[idx % len(cols)]:
                    if st.checkbox(kid, value=kid in commitment.get('kids', []), key=f"comm_{i}_kid_{kid}"):
                        selected_kids.append(kid)
            st.session_state.commitments[i]['kids'] = selected_kids

if st.button("➕ Add Commitment"):
    st.session_state.commitments.append({'day': 'Monday', 'time': '14:00', 'duration': 60, 'activity': '', 'kids': []})
    st.rerun()

st.divider()

# Generate Schedule Button
if st.button("🎯 Generate Schedule", type="primary"):
    kids_list = [k for k in st.session_state.kids if k.strip()]
    valid_subjects = [s for s in st.session_state.subjects if s['name'].strip()]
    valid_commitments = [c for c in st.session_state.commitments if c['activity'].strip()]
    
    if not kids_list or not valid_subjects:
        st.error("Please add at least one child and one subject")
    else:
        # Generate time slots
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        
        time_slots = []
        for m in range(start_minutes, end_minutes, block_size):
            h = m // 60
            min_val = m % 60
            time_slots.append(f"{h:02d}:{min_val:02d}")
        
        # Days of week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if include_weekend else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # Initialize schedule grid
        grid = {}
        for day in days:
            grid[day] = {}
            for kid in kids_list:
                grid[day][kid] = {time: None for time in time_slots}
        
        # Block out fixed commitments with duration
        for commitment in valid_commitments:
            day = commitment['day']
            if day not in grid:
                continue
            
            comm_kids = commitment['kids'] if commitment['kids'] else kids_list
            blocks_needed = (commitment['duration'] + block_size - 1) // block_size
            
            try:
                start_idx = time_slots.index(commitment['time'])
                for kid in comm_kids:
                    if kid in kids_list:
                        for b in range(blocks_needed):
                            if start_idx + b < len(time_slots):
                                slot = time_slots[start_idx + b]
                                grid[day][kid][slot] = {
                                    'subject': commitment['activity'],
                                    'fixed': True,
                                    'isStart': b == 0
                                }
            except (ValueError, KeyError):
                pass
        
        # Schedule subjects with distribution
        for subject in valid_subjects:
            subj_kids = subject['kids'] if subject['kids'] else kids_list
            blocks_needed = (subject['duration'] + block_size - 1) // block_size
            days_to_use = min(subject['sessions'], len(days))
            day_interval = max(1, len(days) // days_to_use)
            
            sessions_scheduled = 0
            day_index = 0
            
            while sessions_scheduled < subject['sessions'] and day_index < len(days):
                day = days[day_index]
                scheduled = False
                
                for i in range(len(time_slots) - blocks_needed + 1):
                    # Check availability
                    available = True
                    for kid in subj_kids:
                        if kid not in kids_list:
                            continue
                        for b in range(blocks_needed):
                            slot = time_slots[i + b]
                            if grid[day][kid][slot] is not None:
                                available = False
                                break
                        if not available:
                            break
                    
                    if available:
                        # Schedule session
                        for kid in subj_kids:
                            if kid in kids_list:
                                for b in range(blocks_needed):
                                    slot = time_slots[i + b]
                                    grid[day][kid][slot] = {
                                        'subject': subject['name'],
                                        'shared': len(subj_kids) > 1,
                                        'isStart': b == 0
                                    }
                        sessions_scheduled += 1
                        scheduled = True
                        break
                
                # Move to next day
                if sessions_scheduled < subject['sessions']:
                    if scheduled and day_interval > 0:
                        day_index += day_interval
                    else:
                        day_index += 1
                    
                    if day_index >= len(days) and sessions_scheduled < subject['sessions']:
                        day_index = (day_index % len(days)) + 1
                else:
                    break
        
        # Display schedule
        st.success("Schedule Generated!")
        st.header("📆 Weekly Schedule")
        
        # Create display dataframe
        schedule_data = []
        for time in time_slots:
            row = {'Time': time}
            for day in days:
                for kid in kids_list:
                    cell = grid[day][kid][time]
                    col_name = f"{day}\n{kid}"
                    if cell:
                        if cell['isStart']:
                            row[col_name] = cell['subject']
                        else:
                            row[col_name] = '↓'
                    else:
                        row[col_name] = ''
            schedule_data.append(row)
        
        df = pd.DataFrame(schedule_data)
        
        # Style the dataframe
        def highlight_cells(val):
            if val == '':
                return 'background-color: white'
            elif val == '↓':
                return 'background-color: #e3f2fd; color: #1976d2'
            else:
                return 'background-color: #e8f5e9; font-weight: bold'
        
        styled_df = df.style.applymap(highlight_cells, subset=df.columns[1:])
        
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        st.info("💡 Tip: Green cells show scheduled subjects. The ↓ symbol indicates continuation of the session above.")
```
