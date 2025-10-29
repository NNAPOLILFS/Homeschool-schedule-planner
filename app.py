import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Homeschool Planner", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for better UX
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #4A90E2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2C3E50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #4A90E2;
        padding-bottom: 0.5rem;
    }
    .schedule-cell {
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 5px solid #4A90E2;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 500;
    }
    .shared-cell {
        border-left: 5px solid #48BB78;
        background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
    }
    .commitment-cell {
        border-left: 5px solid #F56565;
        background: linear-gradient(135deg, #F56565 0%, #C53030 100%);
    }
    .info-box {
        background-color: #EBF8FF;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4299E1;
        margin: 10px 0;
    }
    .success-box {
        background-color: #F0FFF4;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #48BB78;
        margin: 10px 0;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .preview-container {
        background: #F7FAFC;
        padding: 20px;
        border-radius: 15px;
        margin-top: 20px;
        border: 2px dashed #CBD5E0;
    }
</style>
""", unsafe_allow_html=True)

# Access control
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

VALID_CODES = ['DEMO2024', 'TRIAL123']

if not st.session_state.authenticated:
    st.markdown('<div class="main-header">🏫 Homeschool Planner</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.write("### Welcome! 👋")
        st.write("Create beautiful, organized schedules for your homeschool family.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        access_code = st.text_input("🔑 Access Code", type="password", placeholder="Enter your code")
        
        if st.button("✨ Get Started", use_container_width=True):
            if access_code in VALID_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid code. [Get access here](https://buy.stripe.com/your-payment-link)")
    
    st.stop()

# Default emoji mapping
DEFAULT_EMOJI = {
    'math': '🔢', 'reading': '📖', 'writing': '✍️', 'science': '🔬',
    'history': '📜', 'geography': '🌍', 'art': '🎨', 'music': '🎵',
    'pe': '⚽', 'physical education': '⚽', 'spanish': '🇪🇸', 
    'french': '🇫🇷', 'language': '💬', 'bible': '✝️', 'nature': '🌿',
    'coding': '💻', 'default': '📚'
}

def get_emoji_for_subject(subject_name):
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
if 'show_preview' not in st.session_state:
    st.session_state.show_preview = False

# Header
st.markdown('<div class="main-header">🏫 Homeschool Planner</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Setup & Preview", "📅 Weekly Schedule", "🖨️ Print View"])

def generate_schedule_data(start_time, end_time, block_size, include_weekend, back_to_back, kids_list, valid_subjects, valid_commitments):
    """Helper function to generate schedule"""
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    
    time_slots = []
    for m in range(start_minutes, end_minutes, block_size):
        h = m // 60
        min_val = m % 60
        time_slots.append(f"{h:02d}:{min_val:02d}")
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if include_weekend else ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    grid = {}
    for day in days:
        grid[day] = {}
        for kid in kids_list:
            grid[day][kid] = {time: None for time in time_slots}
    
    # Block out commitments
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
    
    # Schedule subjects
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
            
            if sessions_scheduled < subject['sessions']:
                if scheduled and day_interval > 0:
                    day_index += day_interval
                else:
                    day_index += 1
                
                if day_index >= len(days) and sessions_scheduled < subject['sessions']:
                    day_index = (day_index % len(days)) + 1
            else:
                break
    
    return {'grid': grid, 'time_slots': time_slots, 'days': days, 'kids': kids_list}

with tab1:
    # Settings
    st.markdown('<div class="sub-header">⚙️ Schedule Settings</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        start_time = st.time_input("🌅 Start Time", value=datetime.strptime("08:00", "%H:%M").time())
    with col2:
        end_time = st.time_input("🌙 End Time", value=datetime.strptime("15:00", "%H:%M").time())
    with col3:
        block_size = st.selectbox("⏱️ Block Size", [15, 30, 60], index=1, format_func=lambda x: f"{x} min")
    with col4:
        include_weekend = st.checkbox("📅 Weekends", value=False)
    with col5:
        back_to_back = st.checkbox("🔗 Back-to-back", value=False)

    # Children
    st.markdown('<div class="sub-header">👨‍👩‍👧‍👦 Children</div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    for i, kid in enumerate(st.session_state.kids):
        with cols[i % 4]:
            col_input, col_btn = st.columns([4, 1])
            with col_input:
                st.session_state.kids[i] = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}", label_visibility="collapsed", placeholder=f"Child {i+1} name")
            with col_btn:
                if len(st.session_state.kids) > 1 and st.button("🗑️", key=f"rm_kid_{i}"):
                    st.session_state.kids.pop(i)
                    st.rerun()
    
    if st.button("➕ Add Child", use_container_width=False):
        st.session_state.kids.append('')
        st.rerun()

    kids_list = [k for k in st.session_state.kids if k.strip()]

    # Subjects
    st.markdown('<div class="sub-header">📚 Subjects</div>', unsafe_allow_html=True)
    
    for i, subject in enumerate(st.session_state.subjects):
        with st.container():
            emoji_display = subject.get('emoji', '📚')
            name_display = subject['name'] or 'New Subject'
            
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{emoji_display} {name_display}**")
            with col2:
                if st.button("🗑️", key=f"rm_subj_{i}"):
                    st.session_state.subjects.pop(i)
                    st.rerun()
            
            col_name, col_emoji, col_sessions, col_duration = st.columns([3, 1, 1, 1])
            with col_name:
                new_name = st.text_input("Subject", value=subject['name'], key=f"subj_name_{i}", label_visibility="collapsed", placeholder="Subject name")
                st.session_state.subjects[i]['name'] = new_name
                if new_name and not subject.get('emoji_set'):
                    st.session_state.subjects[i]['emoji'] = get_emoji_for_subject(new_name)
            with col_emoji:
                new_emoji = st.text_input("Icon", value=subject.get('emoji', '📚'), key=f"subj_emoji_{i}", max_chars=2, label_visibility="collapsed")
                st.session_state.subjects[i]['emoji'] = new_emoji
                st.session_state.subjects[i]['emoji_set'] = True
            with col_sessions:
                st.session_state.subjects[i]['sessions'] = st.number_input("Sessions/wk", min_value=1, value=subject['sessions'], key=f"subj_sess_{i}", label_visibility="collapsed")
            with col_duration:
                st.session_state.subjects[i]['duration'] = st.number_input("Duration", min_value=15, step=15, value=subject['duration'], key=f"subj_dur_{i}", label_visibility="collapsed")
            
            if kids_list:
                st.write("👥 Children:")
                selected_kids = []
                kid_cols = st.columns(min(len(kids_list), 5))
                for idx, kid in enumerate(kids_list):
                    with kid_cols[idx % len(kid_cols)]:
                        if st.checkbox(kid, value=kid in subject['kids'], key=f"subj_{i}_kid_{kid}"):
                            selected_kids.append(kid)
                st.session_state.subjects[i]['kids'] = selected_kids
            
            st.divider()
    
    if st.button("➕ Add Subject", use_container_width=False):
        st.session_state.subjects.append({'name': '', 'sessions': 3, 'duration': 60, 'kids': [], 'emoji': '📚'})
        st.rerun()

    # Commitments
    st.markdown('<div class="sub-header">📅 Fixed Commitments</div>', unsafe_allow_html=True)
    
    for i, commitment in enumerate(st.session_state.commitments):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{commitment['activity'] or 'New Commitment'}**")
            with col2:
                if st.button("🗑️", key=f"rm_comm_{i}"):
                    st.session_state.commitments.pop(i)
                    st.rerun()
            
            col_day, col_time, col_dur, col_activity = st.columns([2, 2, 1, 3])
            with col_day:
                st.session_state.commitments[i]['day'] = st.selectbox("Day", 
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                    index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(commitment['day']),
                    key=f"comm_day_{i}", label_visibility="collapsed")
            with col_time:
                time_val = datetime.strptime(commitment['time'], "%H:%M").time()
                new_time = st.time_input("Time", value=time_val, key=f"comm_time_{i}", label_visibility="collapsed")
                st.session_state.commitments[i]['time'] = new_time.strftime("%H:%M")
            with col_dur:
                st.session_state.commitments[i]['duration'] = st.number_input("Duration", min_value=15, step=15, value=commitment['duration'], key=f"comm_dur_{i}", label_visibility="collapsed")
            with col_activity:
                st.session_state.commitments[i]['activity'] = st.text_input("Activity", value=commitment['activity'], key=f"comm_act_{i}", label_visibility="collapsed", placeholder="Activity name")
            
            if kids_list:
                st.write("👥 Children:")
                selected_kids = []
                kid_cols = st.columns(min(len(kids_list), 5))
                for idx, kid in enumerate(kids_list):
                    with kid_cols[idx % len(kid_cols)]:
                        if st.checkbox(kid, value=kid in commitment.get('kids', []), key=f"comm_{i}_kid_{kid}"):
                            selected_kids.append(kid)
                st.session_state.commitments[i]['kids'] = selected_kids
            
            st.divider()
    
    if st.button("➕ Add Commitment", use_container_width=False):
        st.session_state.commitments.append({'day': 'Monday', 'time': '14:00', 'duration': 60, 'activity': '', 'kids': []})
        st.rerun()

    st.markdown("---")
    
    # Generate buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👀 Preview Schedule", type="secondary", use_container_width=True):
            st.session_state.show_preview = True
            st.rerun()
    with col2:
        if st.button("🎯 Generate Full Schedule", type="primary", use_container_width=True):
            valid_subjects = [s for s in st.session_state.subjects if s['name'].strip()]
            valid_commitments = [c for c in st.session_state.commitments if c['activity'].strip()]
            
            if not kids_list or not valid_subjects:
                st.error("❌ Please add at least one child and one subject")
            else:
                st.session_state.generated_schedule = generate_schedule_data(
                    start_time, end_time, block_size, include_weekend, back_to_back,
                    kids_list, valid_subjects, valid_commitments
                )
                st.session_state.show_preview = False
                st.success("✅ Schedule generated! Go to 'Weekly Schedule' tab")
                st.rerun()
    
    # Preview section
    if st.session_state.show_preview and kids_list:
        st.markdown('<div class="preview-container">', unsafe_allow_html=True)
        st.markdown("### 👀 Quick Preview")
        
        valid_subjects = [s for s in st.session_state.subjects if s['name'].strip()]
        valid_commitments = [c for c in st.session_state.commitments if c['activity'].strip()]
        
        if valid_subjects:
            preview_schedule = generate_schedule_data(
                start_time, end_time, block_size, include_weekend, back_to_back,
                kids_list, valid_subjects, valid_commitments
            )
            
            # Show summary
            st.write(f"**{len(kids_list)} children** • **{len(valid_subjects)} subjects** • **{len(preview_schedule['days'])} days**")
            
            # Show first day as example
            if preview_schedule['days']:
                first_day = preview_schedule['days'][0]
                st.write(f"**Sample: {first_day}**")
                
                for kid in kids_list[:2]:  # Show max 2 kids in preview
                    st.write(f"*{kid}:*")
                    lessons = []
                    for time in preview_schedule['time_slots']:
                        cell = preview_schedule['grid'][first_day][kid][time]
                        if cell and cell['isStart']:
                            lessons.append(f"{cell.get('emoji', '📚')} {cell['subject']} ({time})")
                    if lessons:
                        st.write(" • ".join(lessons))
                    else:
                        st.write("_No lessons_")
                
                if len(kids_list) > 2:
                    st.write(f"_...and {len(kids_list)-2} more children_")
        
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    if st.session_state.generated_schedule is None:
        st.markdown('<div class="info-box">👈 Generate a schedule in the Setup tab first</div>', unsafe_allow_html=True)
    else:
        schedule = st.session_state.generated_schedule
        st.markdown('<div class="sub-header">📆 Your Weekly Schedule</div>', unsafe_allow_html=True)
        st.write("Click on any lesson to add details, resources, and track completion")
        
        # Day selector
        selected_day = st.selectbox("Select Day", schedule['days'], key="day_selector")
        
        st.markdown(f"### {selected_day}")
        
        # Create columns for each kid
        kid_columns = st.columns(len(schedule['kids']))
        
        for kid_idx, kid in enumerate(schedule['kids']):
            with kid_columns[kid_idx]:
                st.markdown(f"**👤 {kid}**")
                
                for time in schedule['time_slots']:
                    cell = schedule['grid'][selected_day][kid][time]
                    
                    if cell and cell['isStart']:
                        lesson_key = f"{selected_day}_{kid}_{time}_{cell['subject']}"
                        emoji = cell.get('emoji', '📚')
                        
                        # Determine cell style
                        if cell.get('fixed'):
                            cell_class = "commitment-cell"
                        elif cell.get('shared'):
                            cell_class = "shared-cell"
                        else:
                            cell_class = "schedule-cell"
                        
                        with st.expander(f"{emoji} {cell['subject']} - {time}"):
                            details = st.session_state.lesson_details.get(lesson_key, {'notes': '', 'link': ''})
                            
                            notes = st.text_area("📝 Lesson Notes", value=details.get('notes', ''), 
                                                key=f"notes_{lesson_key}", 
                                                placeholder="e.g., Pages 47-49, worksheet 3",
                                                height=80)
                            link = st.text_input("🔗 Resource Link", value=details.get('link', ''), 
                                                key=f"link_{lesson_key}",
                                                placeholder="https://youtube.com/...")
                            
                            col_save, col_complete = st.columns(2)
                            with col_save:
                                if st.button("💾 Save", key=f"save_{lesson_key}", use_container_width=True):
                                    st.session_state.lesson_details[lesson_key] = {
                                        'notes': notes,
                                        'link': link
                                    }
                                    st.success("Saved!")
                            
                            with col_complete:
                                completed = st.session_state.lesson_completion.get(lesson_key, False)
                                if st.checkbox("✅ Done", value=completed, key=f"complete_{lesson_key}"):
                                    st.session_state.lesson_completion[lesson_key] = True
                                else:
                                    st.session_state.lesson_completion[lesson_key] = False
                            
                            if details.get('notes') or details.get('link'):
                                st.markdown("---")
                                if details.get('notes'):
                                    st.info(f"📝 {details['notes']}")
                                if details.get('link'):
                                    st.markdown(f"🔗 [Open Resource]({details['link']})")
                    
                    elif cell and not cell['isStart']:
                        st.write("⬇️")
        
        st.markdown("---")
        
        # Export
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
            label="📥 Download Full Schedule (CSV)",
            data=csv,
            file_name="homeschool_schedule.csv",
            mime="text/csv",
            use_container_width=True
        )

with tab3:
    if st.session_state.generated_schedule is None:
        st.markdown('<div class="info-box">👈 Generate a schedule in the Setup tab first</div>', unsafe_allow_html=True)
    else:
        schedule = st.session_state.generated_schedule
        st.markdown('<div class="sub-header">🖨️ Print Individual Schedules</div>', unsafe_allow_html=True)
        
        selected_kid = st.selectbox("👤 Select child to print", schedule['kids'])
        
        if st.button("📄 Generate Print View", use_container_width=True):
            st.markdown(f"## 📋 {selected_kid}'s Weekly Schedule")
            
            for day in schedule['days']:
                st.markdown(f"### {day}")
                
                has_lessons = False
                for time in schedule['time_slots']:
                    cell = schedule['grid'][day][selected_kid][time]
                    if cell and cell['isStart']:
                        has_lessons = True
                        lesson_key = f"{day}_{selected_kid}_{time}_{cell['subject']}"
                        details = st.session_state.lesson_details.get(lesson_key, {})
                        emoji = cell.get('emoji', '📚')
                        
                        col1, col2, col3 = st.columns([1, 4, 1])
                        with col1:
                            st.markdown(f"**{time}**")
                        with col2:
                            st.markdown(f"**{emoji} {cell['subject']}**")
                            if details.get('notes'):
                                st.write(f"_{details['notes']}_")
                            if details.get('link'):
                                st.write(f"🔗 [Resource Link]({details['link']})")
                        with col3:
                            st.markdown("☐")
                
                if not has_lessons:
                    st.write("_No lessons scheduled_")
                
                st.markdown("---")
            
            st.info("💡 Use Ctrl+P (or Cmd+P on Mac) to print this page")
