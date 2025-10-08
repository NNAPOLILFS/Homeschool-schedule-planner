import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import io

st.set_page_config(layout="wide", page_title="Homeschool Planner")

# -------------------------
# --- Sidebar Settings ---
# -------------------------
st.sidebar.title("Planner Settings")

# Children
kids_input = st.sidebar.text_input("Enter children’s names (comma-separated)", "Winter, Micah")
kids = [k.strip() for k in kids_input.split(",") if k.strip()]

# Include/exclude weekend
include_saturday = st.sidebar.checkbox("Include Saturday?", value=True)
include_sunday = st.sidebar.checkbox("Include Sunday?", value=False)
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
if include_saturday: days_of_week.append("Saturday")
if include_sunday: days_of_week.append("Sunday")

# Time increment
time_increment = st.sidebar.selectbox("Schedule increment (minutes)", [15, 30, 60], index=0)

# Day start/end times
st.sidebar.subheader("School Hours")
default_start = datetime.strptime("07:00", "%H:%M").time()
default_end = datetime.strptime("16:00", "%H:%M").time()
start_time_input = st.sidebar.time_input("Day start time", value=default_start)
end_time_input = st.sidebar.time_input("Day end time", value=default_end)
try:
    start_time = timedelta(hours=start_time_input.hour, minutes=start_time_input.minute)
    end_time = timedelta(hours=end_time_input.hour, minutes=end_time_input.minute)
except:
    start_time = timedelta(hours=7)
    end_time = timedelta(hours=16)

# Theme selection
theme = st.sidebar.selectbox("Choose theme", ["Pastel", "Dark", "Bright"])

# -------------------------
# --- Session State Initialization ---
# -------------------------
if "subjects" not in st.session_state:
    st.session_state.subjects = {kid: [] for kid in kids}
if "fixed" not in st.session_state:
    st.session_state.fixed = {kid: [] for kid in kids}

# -------------------------
# --- Dynamic Inputs per Child ---
# -------------------------
st.subheader("Subjects & Fixed Commitments per Child")

for kid in kids:
    st.markdown(f"### {kid}'s Subjects")
    if kid not in st.session_state.subjects:
        st.session_state.subjects[kid] = []
    for i, subj in enumerate(st.session_state.subjects[kid]):
        col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
        with col1:
            subj["name"] = st.text_input(f"Name ({kid})", value=subj.get("name",""), key=f"name_{kid}_{i}")
        with col2:
            subj["sessions"] = st.number_input(f"Sessions/week ({kid})", min_value=1, value=subj.get("sessions",1), key=f"sessions_{kid}_{i}")
        with col3:
            subj["length"] = st.number_input(f"Length (min) ({kid})", min_value=time_increment, step=time_increment, value=subj.get("length",45), key=f"length_{kid}_{i}")
        with col4:
            subj["shared"] = st.checkbox("Shared?", value=subj.get("shared", False), key=f"shared_{kid}_{i}")
        with col5:
            subj["icon"] = st.text_input("Emoji", value=subj.get("icon","📚"), max_chars=2, key=f"icon_{kid}_{i}")
    if st.button(f"Add Subject for {kid}"):
        st.session_state.subjects[kid].append({"name":"","sessions":1,"length":45,"shared":False,"icon":"📚"})

    st.markdown(f"### {kid}'s Fixed Commitments")
    if kid not in st.session_state.fixed:
        st.session_state.fixed[kid] = []
    for i, fc in enumerate(st.session_state.fixed[kid]):
        col1, col2, col3, col4 = st.columns([2,2,1,1])
        with col1:
            fc["name"] = st.text_input(f"Commitment Name ({kid})", value=fc.get("name",""), key=f"fc_name_{kid}_{i}")
        with col2:
            fc["day"] = st.selectbox(f"Day ({kid})", days_of_week, index=days_of_week.index(fc.get("day",days_of_week[0])), key=f"fc_day_{kid}_{i}")
        with col3:
            fc_start = fc.get("start", start_time)
            fc_start_input = st.time_input(f"Start ({kid})", value=(datetime.min + fc_start).time(), key=f"fc_start_{kid}_{i}")
            fc["start"] = timedelta(hours=fc_start_input.hour, minutes=fc_start_input.minute)
        with col4:
            fc["length"] = st.number_input(f"Length (min) ({kid})", min_value=time_increment, step=time_increment, value=fc.get("length", time_increment), key=f"fc_length_{kid}_{i}")
    if st.button(f"Add Fixed Commitment for {kid}"):
        st.session_state.fixed[kid].append({"name":"","day":days_of_week[0],"start":start_time,"length":time_increment})

# -------------------------
# --- Optimized Scheduling Function ---
# -------------------------
def schedule_planner(subjects, fixed, kids, days_of_week, start_time, end_time, time_increment):
    schedule = {day: {kid: [] for kid in kids} for day in days_of_week}
    unscheduled_subjects = []

    # Fixed commitments
    for kid in kids:
        for fc in fixed[kid]:
            day = fc["day"]
            start = fc["start"]
            end_fc = start + timedelta(minutes=fc["length"])
            schedule[day][kid].append((start, end_fc, fc["name"], "fixed", "⏰"))

    # Helper: free slots
    def get_free_slots(blocks, start_time, end_time, length, increment):
        slots = []
        current = start_time
        while current + timedelta(minutes=length) <= end_time:
            conflict = any(not (current + timedelta(minutes=length) <= b[0] or current >= b[1]) for b in blocks)
            if not conflict:
                slots.append(current)
            current += timedelta(minutes=increment)
        return slots

    # Subjects
    for kid in kids:
        for subj in subjects[kid]:
            name = subj["name"]
            length = subj["length"]
            sessions_needed = subj["sessions"]
            shared = subj["shared"]
            icon = subj["icon"]

            if shared:
                placed_count = 0
                for day in days_of_week:
                    free_per_kid = [set(get_free_slots(schedule[day][k], start_time, end_time, length, time_increment)) for k in kids]
                    common_slots = sorted(list(set.intersection(*free_per_kid)))
                    while common_slots and placed_count < sessions_needed:
                        slot = common_slots.pop(0)
                        for k in kids:
                            schedule[day][k].append((slot, slot + timedelta(minutes=length), name, "shared", icon))
                        placed_count += 1
                    if placed_count >= sessions_needed:
                        break
                if placed_count < sessions_needed:
                    unscheduled_subjects.append(f"{name} (shared)")

            else:
                placed_count = 0
                for day in days_of_week:
                    free_slots = get_free_slots(schedule[day][kid], start_time, end_time, length, time_increment)
                    while free_slots and placed_count < sessions_needed:
                        slot = free_slots.pop(0)
                        schedule[day][kid].append((slot, slot + timedelta(minutes=length), name, "individual", icon))
                        placed_count += 1
                    if placed_count >= sessions_needed:
                        break
                if placed_count < sessions_needed:
                    unscheduled_subjects.append(f"{name} ({kid})")

    # Sort each day's schedule
    for day in days_of_week:
        for kid in kids:
            schedule[day][kid].sort(key=lambda x: x[0])
    return schedule, unscheduled_subjects

# -------------------------
# --- Autofill Button ---
# -------------------------
if st.button("Autofill Schedule"):
    try:
        schedule, unscheduled_subjects = schedule_planner(
            st.session_state.subjects,
            st.session_state.fixed,
            kids,
            days_of_week,
            start_time,
            end_time,
            time_increment
        )
    except Exception as e:
        st.error(f"Error generating schedule: {e}")
        st.stop()

    # -------------------------
    # --- Plot Schedule ---
    # -------------------------
    def plot_schedule(schedule, kids, days_of_week, theme, week_view=True):
        df_plot = []
        palettes = {
            "Pastel": px.colors.qualitative.Pastel,
            "Dark": px.colors.qualitative.Dark24,
            "Bright": px.colors.qualitative.Set1
        }
        colors = palettes.get(theme, px.colors.qualitative.Pastel)
        color_map = {}
        color_idx = 0

        for day in days_of_week:
            for kid in kids:
                for block in schedule[day][kid]:
                    name, block_type, icon = block[2], block[3], block[4]
                    if name not in color_map:
                        color_map[name] = colors[color_idx % len(colors)]
                        color_idx += 1
                    df_plot.append({
                        "Day": day,
                        "Kid": kid,
                        "Start": block[0].total_seconds() / 3600,
                        "End": block[1].total_seconds() / 3600,
                        "Subject": f"{icon} {name}",
                        "Color": color_map[name],
                        "Type": block_type
                    })

        if not df_plot:
            st.write("No sessions scheduled yet.")
            return

        df_plot = pd.DataFrame(df_plot)
        facet_col = "Day" if week_view else None
        facet_col_wrap = 2 if week_view else None

        fig = px.timeline(
            df_plot,
            x_start="Start",
            x_end="End",
            y="Kid",
            color="Subject",
            color_discrete_map={row["Subject"]: row["Color"] for idx, row in df_plot.iterrows()},
            facet_col=facet_col,
            facet_col_wrap=facet_col_wrap
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(title="Hour of Day", tick0=0, dtick=1, tickformat="%I:%M %p")
        fig.update_layout(height=400 + len(kids)*60)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Visual Schedule")
    week_view_toggle = st.checkbox("Week view (uncheck for single day)", value=True)

    for kid in kids:
        with st.expander(f"{kid}'s Schedule", expanded=True):
            plot_schedule({day: {kid: schedule[day][kid] for kid in [kid]} for day in days_of_week}, [kid], days_of_week, theme, week_view_toggle)

    # -------------------------
    # --- Weekly Summary ---
    # -------------------------
    st.subheader("Weekly Summary")
    summary_rows = []
    for kid in kids:
        total_minutes = 0
        for day in days_of_week:
            for block in schedule[day][kid]:
                if block[3] != "fixed":
                    total_minutes += (block[1]-block[0]).total_seconds()/60
        summary_rows.append({"Kid": kid, "Total Hours": round(total_minutes/60,2)})
    st.table(pd.DataFrame(summary_rows))

    # -------------------------
    # --- Unscheduled Subjects ---
    # -------------------------
    if unscheduled_subjects:
        st.warning("Some subjects could not be scheduled due to time conflicts:")
        for s in unscheduled_subjects:
            st.write(f"- {s}")
