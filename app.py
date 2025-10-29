import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Homeschool Planner", layout="wide")

# Access control
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Valid access codes
VALID_CODES = ['DEMO2024', 'TRIAL123']

if not st.session_state.authenticated:
    st.title("🏫 Homeschool Planner")
    st.write("Welcome! Please enter your access code to continue.")
    st.write("Don't have a code? [Get access here](https://buy.stripe.com/your-payment-link)")
    
    access_code = st.text_input("Access Code", type="password")
    
    if st.button("Submit"):
        if access_code in VALID_CODES:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid access code. Please check your email or purchase access.")
    
    st.stop()

# Default emoji mapping for subjects
DEFAULT_EMOJI = {
    'math': '🔢', 'reading': '📖', 'writing': '✍️', 'science': '🔬',
    'history': '📜', 'geography': '🌍', 'art': '🎨', 'music': '🎵',
    'pe': '⚽', 'physical education': '⚽', 'spanish': '🇪🇸', 
    'french': '🇫🇷', 'language': '💬', 'bible': '✝️', 'nature': '🌿',
    'coding': '💻', 'default': '📚'
}

def get_emoji_for_subject(subject_name):
    """Get emoji for a subject based on name"""
    name_lower = subject_name.lower()
    for key in DEFAULT_EMOJI:
        if key in name_lower:
            return DEFAULT_EMOJI[key]
    return DEFAULT_EMOJI['default']

# Initialize session state
if 'kids' not in st.session_state:
    st.session_state.kids = ['']
if 'subjects' not in st.session_state:
    st.session_state.subjects = [{'name': '', 'sessions': 3, 'duration': 60, 'kids': [], 'emoji': '📚'}]
if 'commitments' not in st.session_state:
    st.session_state.commitments = [{'day': 'Monday', 'time': '14:00', 'duration': 60, 'activity': '', 'kids': []}]
if 'generated_schedule' not in st.session_state:
    st.session_state.generated_schedule = None
if 'lesson_details' not in st.session_state:
    st.session_state.lesson_details = {}
if 'lesson_completion' not in st.session_state:
    st.session_state.lesson_completion = {}

st.title("🏫 Homeschool Planner")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 Setup", "📅 Schedule", "🖨️ Print"])

with tab1:
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
        with st.expander(f"Subject {i+1}: {subject.get('emoji', '📚')} {subject['name'] or 'New Subject'}", expanded=not subject['name']):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.session_state.subjects[i]['name'] = st.text_input("Subject Name", value=subject['name'], key=f"subj_name_{i}")
            with col2:
                # Auto-detect emoji when name changes
                if subject['name']:
                    detected_emoji = get_emoji_for_subject(subject['name'])
                    st.session_state.subjects[i]['emoji'] = st.text_input("Icon", value=subject.get('emoji', detected_emoji), key=f"subj_emoji_{i}", max_chars=2)
                else:
                    st.session_state.subjects[i]['emoji'] = st.text_input("Icon", value=subject.get('emoji', '📚'), key=f"subj_emoji_{i}", max_chars=2)
            with col3:
                if st.button("🗑️", key=f"remove_subj_{i}"):
                    st.session_state.subjects.pop(i)
                    st.rerun()
            
            col4, col5 = st.columns(2)
            with col4:
                st.session_state.subjects[i]['sessions'] = st.number_input("Sessions per week", min_value=1, value=subject['sessions'], key=f"subj_sess_{i}")
            with col5:
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
        st.session_state.subjects.append({'name': '', 'sessions': 3, 'duration': 60, 'kids': [], 'emoji': '📚'})
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
                                        'isStart': b == 0,
                                        'emoji': '📅'
                                    }
                except (ValueError, KeyError):
                    pass
            
            # Schedule subjects with distribution
            subject_emoji_map = {s['name']: s.get('emoji', '📚') for s in valid_subjects}
            
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
                                            'isStart': b == 0,
                                            'emoji': subject.get('emoji', '📚')
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
            
            st.session_state.generated_schedule = {
                'grid': grid,
                'time_slots': time_slots,
                'days': days,
                'kids': kids_list
            }
            
            st.success("Schedule Generated! Go to the 'Schedule' tab to view and add lesson details.")

with tab2:
    if st.session_state.generated_schedule is None:
        st.info("👈 Please generate a schedule in the Setup tab first")
    else:
        schedule = st.session_state.generated_schedule
        st.header("📆 Weekly Schedule")
        st.write("Click on any lesson to add details, links, or mark as complete")
        
        # Display schedule with clickable cells
        for day in schedule['days']:
            st.subheader(day)
            
            for time in schedule['time_slots']:
                cols = st.columns([1] + [3] * len(schedule['kids']))
                cols[0].write(f"**{time}**")
                
                for kid_idx, kid in enumerate(schedule['kids']):
                    cell = schedule['grid'][day][kid][time]
                    
                    if cell and cell['isStart']:
                        lesson_key = f"{day}_{kid}_{time}_{cell['subject']}"
                        
                        # Display lesson with emoji
                        emoji = cell.get('emoji', '📚')
                        display_text = f"{emoji} {cell['subject']}"
                        
                        with cols[kid_idx + 1]:
                            with st.expander(display_text):
                                st.write(f"**Child:** {kid}")
                                st.write(f"**Time:** {time}")
                                
                                # Lesson details
                                details = st.session_state.lesson_details.get(lesson_key, {'notes': '', 'link': ''})
                                
                                notes = st.text_area("Lesson notes", value=details.get('notes', ''), 
                                                    key=f"notes_{lesson_key}", 
                                                    placeholder="e.g., Pages 47-49, Do worksheet 3")
                                link = st.text_input("Resource link", value=details.get('link', ''), 
                                                    key=f"link_{lesson_key}",
                                                    placeholder="https://...")
                                
                                if st.button("Save", key=f"save_{lesson_key}"):
                                    st.session_state.lesson_details[lesson_key] = {
                                        'notes': notes,
                                        'link': link
                                    }
                                    st.success("Saved!")
                                
                                # Show saved details
                                if details.get('notes'):
                                    st.info(f"📝 {details['notes']}")
                                if details.get('link'):
                                    st.info(f"🔗 [{details['link']}]({details['link']})")
                                
                                # Completion checkbox
                                completed = st.session_state.lesson_completion.get(lesson_key, False)
                                if st.checkbox("Mark as complete", value=completed, key=f"complete_{lesson_key}"):
                                    st.session_state.lesson_completion[lesson_key] = True
                                else:
                                    st.session_state.lesson_completion[lesson_key] = False
                    
                    elif cell and not cell['isStart']:
                        cols[kid_idx + 1].write("↓")
        
        # CSV Export
        st.divider()
        schedule_data = []
        for time in schedule['time_slots']:
            row = {'Time': time}
            for day in schedule['days']:
                for kid in schedule['kids']:
                    cell = schedule['grid'][day][kid][time]
                    col_name = f"{day}_{kid}"
                    if cell and cell['isStart']:
                        emoji = cell.get('emoji', '📚')
                        row[col_name] = f"{emoji} {cell['subject']}"
                    elif cell:
                        row[col_name] = '↓'
                    else:
                        row[col_name] = ''
            schedule_data.append(row)
        
        df = pd.DataFrame(schedule_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Schedule as CSV",
            data=csv,
            file_name="homeschool_schedule.csv",
            mime="text/csv"
        )

with tab3:
    if st.session_state.generated_schedule is None:
        st.info("👈 Please generate a schedule in the Setup tab first")
    else:
        schedule = st.session_state.generated_schedule
        st.header("🖨️ Print Individual Schedules")
        
        selected_kid = st.selectbox("Select child to print", schedule['kids'])
        
        if st.button("Generate Print View"):
            st.subheader(f"📋 {selected_kid}'s Weekly Schedule")
            
            print_data = []
            for day in schedule['days']:
                st.write(f"### {day}")
                day_lessons = []
                
                for time in schedule['time_slots']:
                    cell = schedule['grid'][day][selected_kid][time]
                    if cell and cell['isStart']:
                        lesson_key = f"{day}_{selected_kid}_{time}_{cell['subject']}"
                        details = st.session_state.lesson_details.get(lesson_key, {})
                        emoji = cell.get('emoji', '📚')
                        
                        lesson_info = {
                            'Time': time,
                            'Subject': f"{emoji} {cell['subject']}",
                            'Details': details.get('notes', ''),
                            'Link': details.get('link', ''),
                            'Done': '☐'
                        }
                        day_lessons.append(lesson_info)
                
                if day_lessons:
                    for lesson in day_lessons:
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            st.write(f"**{lesson['Time']}**")
                        with col2:
                            st.write(f"**{lesson['Subject']}**")
                            if lesson['Details']:
                                st.write(f"_{lesson['Details']}_")
                            if lesson['Link']:
                                st.write(f"🔗 [Link]({lesson['Link']})")
                        with col3:
                            st.write("☐")
                else:
                    st.write("_No lessons scheduled_")
                
                st.divider()
            
            st.info("💡 Use your browser's print function (Ctrl+P or Cmd+P) to print this page")
