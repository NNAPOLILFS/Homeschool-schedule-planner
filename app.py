import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Homeschool Planner", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for better UX
st.markdown("""
<style>
    .main {
        background-color: #F7FAFC;
    }
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
        background: white;
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
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #2C3E50;">Welcome! 👋</h3>
            <p style="color: #4A5568;">Create beautiful, organized schedules for your homeschool family.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
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
if 'scheduling_warnings' not in st.session_state:
    st.session_state.scheduling_warnings = []
if 'saved_schedules' not in st.session_state:
    st.session_state.saved_schedules = {}
if 'current_schedule_name' not in st.session_state:
    st.session_state.current_schedule_name = ""
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
        st.markdown('<div class="sub-header">📆 Calendar View</div>', unsafe_allow_html=True)
        st.write("Click on any lesson to add details, resources, and track completion")
        
        # Day selector
        selected_day = st.selectbox("Select Day", schedule['days'], key="day_selector")
        
        st.markdown(f"### {selected_day}")
        
        # Create traditional grid calendar
        # Build a table structure
        st.markdown("""
        <style>
        .calendar-grid {
            display: grid;
            grid-template-columns: 80px repeat(auto-fit, minmax(200px, 1fr));
            gap: 1px;
            background: #e0e0e0;
            border: 1px solid #e0e0e0;
        }
        .calendar-header {
            background: #667eea;
            color: white;
            padding: 15px;
            font-weight: 600;
            text-align: center;
        }
        .time-cell {
            background: #f5f5f5;
            padding: 10px;
            font-weight: 600;
            color: #555;
            text-align: center;
        }
        .lesson-cell {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            min-height: 60px;
        }
        .lesson-cell-shared {
            background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
        }
        .lesson-cell-commitment {
            background: linear-gradient(135deg, #F56565 0%, #C53030 100%);
        }
        .empty-cell {
            background: white;
            padding: 15px;
            min-height: 60px;
        }
        .lesson-emoji {
            font-size: 1.2rem;
            margin-right: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create calendar header row
        cols = st.columns([1] + [3] * len(schedule['kids']))
        cols[0].markdown("**Time**")
        for idx, kid in enumerate(schedule['kids']):
            cols[idx + 1].markdown(f"**👤 {kid}**")
        
        # Create time slot rows
        for time in schedule['time_slots']:
            cols = st.columns([1] + [3] * len(schedule['kids']))
            cols[0].markdown(f"**{time}**")
            
            for kid_idx, kid in enumerate(schedule['kids']):
                cell = schedule['grid'][selected_day][kid][time]
                
                with cols[kid_idx + 1]:
                    if cell and cell['isStart']:
                        lesson_key = f"{selected_day}_{kid}_{time}_{cell['subject']}"
                        emoji = cell.get('emoji', '📚')
                        
                        # Determine background color
                        if cell.get('fixed'):
                            bg_color = "#F56565"
                        elif cell.get('shared'):
                            bg_color = "#48BB78"
                        else:
                            bg_color = "#667eea"
                        
                        with st.expander(f"{emoji} {cell['subject']}", expanded=False):
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
                        st.markdown('<div style="text-align: center; color: #999;">⬇️</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div style="min-height: 20px;"></div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="sub-header">📊 Weekly Summary & Statistics</div>', unsafe_allow_html=True)
        
        # Calculate total hours per subject
        subject_hours = {}
        kid_total_hours = {kid: 0 for kid in schedule['kids']}
        
        for day in schedule['days']:
            for kid in schedule['kids']:
                for time in schedule['time_slots']:
                    cell = schedule['grid'][day][kid][time]
                    if cell and cell['isStart']:
                        # Find duration of this session
                        duration_blocks = 1
                        time_idx = schedule['time_slots'].index(time)
                        for i in range(time_idx + 1, len(schedule['time_slots'])):
                            next_cell = schedule['grid'][day][kid][schedule['time_slots'][i]]
                            if next_cell and next_cell.get('subject') == cell['subject'] and not next_cell.get('isStart'):
                                duration_blocks += 1
                            else:
                                break
                        
                        # Calculate hours
                        block_minutes = (end_time.hour * 60 + end_time.minute - start_time.hour * 60 - start_time.minute) // len(schedule['time_slots'])
                        hours = (duration_blocks * block_minutes) / 60
                        
                        subject = cell['subject']
                        if subject not in subject_hours:
                            subject_hours[subject] = {'total': 0, 'kids': {}}
                        subject_hours[subject]['total'] += hours
                        
                        if kid not in subject_hours[subject]['kids']:
                            subject_hours[subject]['kids'][kid] = 0
                        subject_hours[subject]['kids'][kid] += hours
                        
                        kid_total_hours[kid] += hours
        
        # Display overall stats
        st.markdown("### 📈 Overall Statistics")
        
        cols = st.columns(len(schedule['kids']))
        for idx, kid in enumerate(schedule['kids']):
            with cols[idx]:
                st.metric(
                    label=f"👤 {kid}",
                    value=f"{kid_total_hours[kid]:.1f} hrs/week"
                )
        
        st.divider()
        
        # Hours per subject
        st.markdown("### 📚 Hours per Subject")
        
        # Create a nice table
        subject_data = []
        for subject, data in sorted(subject_hours.items(), key=lambda x: x[1]['total'], reverse=True):
            row = {'Subject': subject, 'Total Hours': f"{data['total']:.1f}"}
            for kid in schedule['kids']:
                row[kid] = f"{data['kids'].get(kid, 0):.1f}"
            subject_data.append(row)
        
        if subject_data:
            df_subjects = pd.DataFrame(subject_data)
            st.dataframe(df_subjects, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Balance check
        st.markdown("### ⚖️ Balance Check")
        
        if len(schedule['kids']) > 1:
            avg_hours = sum(kid_total_hours.values()) / len(kid_total_hours)
            imbalance_found = False
            
            for kid, hours in kid_total_hours.items():
                diff = hours - avg_hours
                if abs(diff) > 2:  # More than 2 hours difference
                    imbalance_found = True
                    if diff > 0:
                        st.warning(f"⚠️ {kid} has {diff:.1f} more hours than average ({avg_hours:.1f} hrs)")
                    else:
                        st.warning(f"⚠️ {kid} has {abs(diff):.1f} fewer hours than average ({avg_hours:.1f} hrs)")
            
            if not imbalance_found:
                st.success("✅ Schedule is well-balanced across all children!")
        else:
            st.info("💡 Add more children to see balance comparison")
        
        st.divider()
        
        # Download stats as CSV
        if subject_data:
            csv_stats = df_subjects.to_csv(index=False)
            st.download_button(
                label="📥 Download Stats (CSV)",
                data=csv_stats,
                file_name="schedule_statistics.csv",
                mime="text/csv",
                use_container_width=True
            )

with tab4:
    if st.session_state.generated_schedule is None:
        st.markdown('<div class="info-box">👈 Generate a schedule in the Setup tab first</div>', unsafe_allow_html=True)
    else:
        schedule = st.session_state.generated_schedule
        st.markdown('<div class="sub-header">🖨️ Print Individual Schedules</div>', unsafe_allow_html=True)
        
        selected_kid = st.selectbox("👤 Select child to print", schedule['kids'])
        
        col1, col2 = st.columns(2)
        with col1:
            print_mode = st.radio("Print view", ["Single Day", "Full Week"], horizontal=True)
        with col2:
            if print_mode == "Single Day":
                selected_print_day = st.selectbox("📅 Select day", schedule['days'], key="print_day_selector")
        
        if st.button("📄 Generate Print View", use_container_width=True, type="primary"):
            # Card-based planner style
            st.markdown(f"""
            <style>
            .print-container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
            }}
            .print-header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #667eea;
            }}
            .print-header h1 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .print-header h2 {{
                color: #667eea;
                font-weight: normal;
            }}
            .timeline {{
                position: relative;
                padding-left: 50px;
            }}
            .timeline::before {{
                content: '';
                position: absolute;
                left: 20px;
                top: 0;
                bottom: 0;
                width: 3px;
                background: #e0e0e0;
            }}
            .time-block {{
                position: relative;
                margin-bottom: 25px;
            }}
            .time-dot {{
                position: absolute;
                left: -38px;
                top: 8px;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #667eea;
                border: 3px solid white;
                box-shadow: 0 0 0 2px #667eea;
            }}
            .time-label {{
                font-size: 0.9rem;
                color: #7f8c8d;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .lesson-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 12px;
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }}
            .lesson-card.shared {{
                background: linear-gradient(135deg, #48BB78 0%, #38A169 100%);
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            }}
            .lesson-card.commitment {{
                background: linear-gradient(135deg, #F56565 0%, #C53030 100%);
                box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);
            }}
            .lesson-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 10px;
            }}
            .lesson-title {{
                font-size: 1.3rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .lesson-emoji {{
                font-size: 1.8rem;
            }}
            .lesson-duration {{
                font-size: 0.9rem;
                opacity: 0.9;
            }}
            .lesson-details {{
                font-size: 0.95rem;
                opacity: 0.95;
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid rgba(255,255,255,0.3);
                line-height: 1.6;
            }}
            .checkbox {{
                font-size: 1.5rem;
                float: right;
            }}
            .break-block {{
                padding: 15px 0;
                margin-bottom: 20px;
                color: #95a5a6;
                font-style: italic;
                font-size: 0.95rem;
                text-align: center;
            }}
            .no-lessons {{
                text-align: center;
                padding: 60px 20px;
                color: #95a5a6;
                font-style: italic;
                font-size: 1.1rem;
            }}
            @media print {{
                .print-container {{
                    box-shadow: none;
                    border-radius: 0;
                }}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Determine which days to show
            days_to_print = [selected_print_day] if print_mode == "Single Day" else schedule['days']
            
            st.markdown(f"""
            <div class="print-container">
                <div class="print-header">
                    <h1>📋 {selected_kid}'s Schedule</h1>
                    <h2>{selected_print_day if print_mode == "Single Day" else "Full Week"}</h2>
                </div>
            """, unsafe_allow_html=True)
            
            for day in days_to_print:
                if print_mode == "Full Week":
                    st.markdown(f'<h3 style="color: #667eea; margin-top: 30px; margin-bottom: 20px;">{day}</h3>', unsafe_allow_html=True)
                
                st.markdown('<div class="timeline">', unsafe_allow_html=True)
            
                # Get all lessons for this day/kid
                lessons_with_times = []
                for time in schedule['time_slots']:
                    cell = schedule['grid'][day][selected_kid][time]
                    if cell and cell['isStart']:
                        lesson_key = f"{day}_{selected_kid}_{time}_{cell['subject']}"
                        details = st.session_state.lesson_details.get(lesson_key, {})
                        
                        # Calculate duration in minutes
                        duration_blocks = 1
                        time_idx = schedule['time_slots'].index(time)
                        for i in range(time_idx + 1, len(schedule['time_slots'])):
                            next_cell = schedule['grid'][day][selected_kid][schedule['time_slots'][i]]
                            if next_cell and next_cell.get('subject') == cell['subject'] and not next_cell.get('isStart'):
                                duration_blocks += 1
                            else:
                                break
                        
                        lessons_with_times.append({
                            'time': time,
                            'time_idx': time_idx,
                            'cell': cell,
                            'details': details,
                            'duration': duration_blocks * (end_time.hour * 60 + end_time.minute - start_time.hour * 60 - start_time.minute) // len(schedule['time_slots'])
                        })
                
                if not lessons_with_times:
                    st.markdown('<div class="no-lessons">No lessons scheduled for this day</div>', unsafe_allow_html=True)
                else:
                    last_end_time = None
                    
                    for lesson in lessons_with_times:
                        # Check for break
                        if last_end_time is not None:
                            current_start_idx = lesson['time_idx']
                            if current_start_idx > last_end_time:
                                break_minutes = (current_start_idx - last_end_time) * (end_time.hour * 60 + end_time.minute - start_time.hour * 60 - start_time.minute) // len(schedule['time_slots'])
                                st.markdown(f'<div class="break-block">☕ Break ({break_minutes} min)</div>', unsafe_allow_html=True)
                        
                        # Determine card class
                        card_class = ""
                        if lesson['cell'].get('fixed'):
                            card_class = "commitment"
                        elif lesson['cell'].get('shared'):
                            card_class = "shared"
                        
                        emoji = lesson['cell'].get('emoji', '📚')
                        subject = lesson['cell']['subject']
                        
                        # Build details HTML with proper escaping
                        details_parts = []
                        if lesson['details'].get('notes'):
                            notes_text = lesson['details']['notes'].replace('<', '&lt;').replace('>', '&gt;')
                            details_parts.append(f"<div>📝 {notes_text}</div>")
                        if lesson['details'].get('link'):
                            link = lesson['details']['link']
                            link_display = link[:50] + "..." if len(link) > 50 else link
                            details_parts.append(f'<div>🔗 <a href="{link}" style="color: white; text-decoration: underline;" target="_blank">{link_display}</a></div>')
                        
                        details_html = ""
                        if details_parts:
                            details_html = f'<div class="lesson-details">{"".join(details_parts)}</div>'
                        
                        lesson_html = f"""
                        <div class="time-block">
                            <div class="time-dot"></div>
                            <div class="time-label">{lesson['time']}</div>
                            <div class="lesson-card {card_class}">
                                <div class="lesson-header">
                                    <div class="lesson-title">
                                        <span class="lesson-emoji">{emoji}</span>
                                        <span>{subject}</span>
                                    </div>
                                    <div class="lesson-duration">{lesson['duration']} min</div>
                                </div>
                                {details_html}
                                <div class="checkbox">☐</div>
                            </div>
                        </div>
                        """
                        st.markdown(lesson_html, unsafe_allow_html=True)
                        
                        last_end_time = lesson['time_idx'] + (lesson['duration'] // ((end_time.hour * 60 + end_time.minute - start_time.hour * 60 - start_time.minute) // len(schedule['time_slots'])))
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                if print_mode == "Full Week" and day != days_to_print[-1]:
                    st.markdown('<div style="page-break-after: always;"></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.info("💡 Use Ctrl+P (or Cmd+P on Mac) to print this beautiful schedule!")
