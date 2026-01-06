import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Homeschool Planner", layout="wide", initial_sidebar_state="expanded")

# ---------- Helper Functions ----------
DEFAULT_SUBJECTS = [
    {"name": "Math", "emoji": "🔢", "color": "#667eea"},
    {"name": "Reading", "emoji": "📖", "color": "#f6ad55"},
    {"name": "Writing", "emoji": "✍️", "color": "#fc8181"},
    {"name": "Science", "emoji": "🔬", "color": "#48bb78"},
    {"name": "Art", "emoji": "🎨", "color": "#9f7aea"},
    {"name": "Music", "emoji": "🎵", "color": "#ed64a6"},
    {"name": "PE", "emoji": "⚽", "color": "#ed8936"},
    {"name": "History", "emoji": "📜", "color": "#ecc94b"}
]

def generate_time_slots(start_time, end_time, block_minutes):
    slots = []
    current = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)
    while current < end_dt:
        slots.append(current.time().strftime("%H:%M"))
        current += timedelta(minutes=block_minutes)
    return slots

def init_session_state():
    if "kids" not in st.session_state:
        st.session_state.kids = ["Child 1"]
    if "subjects" not in st.session_state:
        st.session_state.subjects = DEFAULT_SUBJECTS.copy()
    if "commitments" not in st.session_state:
        st.session_state.commitments = []  # Fixed activities
    if "generated_schedule" not in st.session_state:
        st.session_state.generated_schedule = None
    if "pressure" not in st.session_state:
        st.session_state.pressure = "Gentle"

def build_schedule():
    kids = st.session_state.kids
    subjects = st.session_state.subjects
    commitments = st.session_state.commitments
    start_time = st.session_state.start_time
    end_time = st.session_state.end_time
    block_minutes = st.session_state.block_size
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    slots = generate_time_slots(start_time, end_time, block_minutes)

    grid = {day: {kid: [None]*len(slots) for kid in kids} for day in days}

    # Insert fixed commitments
    for c in commitments:
        day = c["day"]
        idx = slots.index(c["time"])
        blocks = max(1, c["duration"] // block_minutes)
        for kid in c["kids"] or kids:
            for b in range(blocks):
                if idx + b < len(slots):
                    grid[day][kid][idx+b] = {"subject": c["activity"], "color": "#718096", "shared": len(c["kids"]) > 1, "fixed": True}

    # Insert subjects
    for s in subjects:
        subj_kids = s.get("kids", kids)
        blocks_needed = max(1, s.get("duration", 60) // block_minutes)
        sessions = s.get("sessions", 3)
        interval = max(1, len(days)//sessions)

        day_idx = 0
        sessions_scheduled = 0
        while sessions_scheduled < sessions and day_idx < len(days):
            day = days[day_idx]
            placed = False
            for i in range(len(slots)-blocks_needed+1):
                conflict = any(grid[day][k][i+b] is not None for k in subj_kids for b in range(blocks_needed))
                if not conflict:
                    for k in subj_kids:
                        for b in range(blocks_needed):
                            grid[day][k][i+b] = {"subject": s["name"], "color": s["color"], "shared": len(subj_kids) > 1, "fixed": False}
                    sessions_scheduled += 1
                    placed = True
                    break
            day_idx += interval if placed else 1

    return {"grid": grid, "slots": slots, "days": days, "kids": kids}

# ---------- Initialize ----------
init_session_state()

st.title("🏫 Homeschool Planner")

# ---------- Sidebar Settings ----------
with st.sidebar:
    st.header("🛠 Schedule Settings")
    st.session_state.start_time = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
    st.session_state.end_time = st.time_input("End Time", value=datetime.strptime("15:00", "%H:%M").time())
    st.session_state.block_size = st.selectbox("Block size (minutes)", [15,30,60], index=1)
    st.session_state.pressure = st.selectbox("Schedule Rhythm", ["Gentle","Balanced","Ambitious"], index=0)
    st.markdown("---")
    st.header("👨‍👩‍👧‍👦 Children")
    for i, kid in enumerate(st.session_state.kids):
        new_name = st.text_input(f"Child {i+1}", value=kid, key=f"kid_{i}")
        st.session_state.kids[i] = new_name
        if len(st.session_state.kids) > 1 and st.button(f"Remove", key=f"rm_kid_{i}"):
            st.session_state.kids.pop(i)
            st.experimental_rerun()
    if st.button("➕ Add Child"):
        st.session_state.kids.append(f"Child {len(st.session_state.kids)+1}")
        st.experimental_rerun()
    st.markdown("---")
    st.header("📚 Subjects")
    for i, subj in enumerate(st.session_state.subjects):
        col1, col2 = st.columns([3,1])
        with col1:
            st.session_state.subjects[i]["name"] = st.text_input("Subject", value=subj["name"], key=f"subj_name_{i}")
        with col2:
            st.session_state.subjects[i]["emoji"] = st.text_input("Emoji", value=subj["emoji"], max_chars=2, key=f"subj_emoji_{i}")
        st.session_state.subjects[i]["duration"] = st.number_input("Duration (min)", value=subj.get("duration",60), step=15, key=f"subj_dur_{i}")
        st.session_state.subjects[i]["sessions"] = st.number_input("Sessions per week", value=subj.get("sessions",3), min_value=1, key=f"subj_sess_{i}")
        st.session_state.subjects[i]["kids"] = st.multiselect("Select Kids", options=st.session_state.kids, default=subj.get("kids", st.session_state.kids), key=f"subj_kids_{i}")
        if st.button("🗑 Remove Subject", key=f"rm_subj_{i}"):
            st.session_state.subjects.pop(i)
            st.experimental_rerun()
    if st.button("➕ Add Subject"):
        st.session_state.subjects.append({"name":"","emoji":"📚","color":"#3182ce","duration":60,"sessions":3,"kids":st.session_state.kids.copy()})
        st.experimental_rerun()
    st.markdown("---")
    st.header("📅 Fixed Commitments")
    for i, c in enumerate(st.session_state.commitments):
        st.session_state.commitments[i]["activity"] = st.text_input("Activity", value=c["activity"], key=f"comm_name_{i}")
        st.session_state.commitments[i]["day"] = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"], index=["Monday","Tuesday","Wednesday","Thursday","Friday"].index(c.get("day","Monday")), key=f"comm_day_{i}")
        st.session_state.commitments[i]["time"] = st.time_input("Time", value=datetime.strptime(c.get("time","12:00"), "%H:%M").time(), key=f"comm_time_{i}")
        st.session_state.commitments[i]["duration"] = st.number_input("Duration", value=c.get("duration",60), step=15, key=f"comm_dur_{i}")
        st.session_state.commitments[i]["kids"] = st.multiselect("Kids", options=st.session_state.kids, default=c.get("kids", st.session_state.kids), key=f"comm_kids_{i}")
        if st.button("🗑 Remove Commitment", key=f"rm_comm_{i}"):
            st.session_state.commitments.pop(i)
            st.experimental_rerun()
    if st.button("➕ Add Commitment"):
        st.session_state.commitments.append({"activity":"","day":"Monday","time":"12:00","duration":60,"kids":st.session_state.kids.copy()})
        st.experimental_rerun()

# ---------- Main Tabs ----------
tab1, tab2 = st.tabs(["📆 Weekly Schedule", "🖨️ Print/Export"])

with tab1:
    st.header("Your Weekly Schedule")
    if st.button("Generate Schedule"):
        st.session_state.generated_schedule = build_schedule()
    
    if st.session_state.generated_schedule:
        sched = st.session_state.generated_schedule
        for kid in sched["kids"]:
            st.subheader(f"👤 {kid}")
            for day in sched["days"]:
                st.markdown(f"**{day}**")
                row_html = '<div style="display:flex; flex-wrap:wrap;">'
                for idx, cell in enumerate(sched["grid"][day][kid]):
                    time_label = sched["slots"][idx]
                    if cell:
                        color = cell.get("color","#667eea")
                        emoji = next((s["emoji"] for s in st.session_state.subjects if s["name"]==cell["subject"]), "📚")
                        border = "3px solid #000" if cell.get("shared") else "none"
                        row_html += f'<div style="min-width:80px; margin:2px; padding:5px; background:{color}; border:{border}; color:white; border-radius:8px; text-align:center;">{emoji}<br>{cell["subject"]}<br>{time_label}</div>'
                    else:
                        row_html += f'<div style="min-width:80px; margin:2px; padding:5px; background:#EDF2F7; border-radius:8px; text-align:center;">{time_label}</div>'
                row_html += "</div>"
                st.markdown(row_html, unsafe_allow_html=True)

with tab2:
    st.header("Export Schedule")
    if st.session_state.generated_schedule:
        sched = st.session_state.generated_schedule
        data = []
        for day in sched["days"]:
            for idx, time in enumerate(sched["slots"]):
                row = {"Day": day, "Time": time}
                for kid in sched["kids"]:
                    cell = sched["grid"][day][kid][idx]
                    row[kid] = cell["subject"] if cell else ""
                data.append(row)
        df = pd.DataFrame(data)
        st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="homeschool_schedule.csv")
