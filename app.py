import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import io

st.set_page_config(layout="wide", page_title="Homeschool Planner")

# -------------------------
# --- Sidebar / Inputs ---
# -------------------------
st.sidebar.title("Planner Settings")

# Children
kids_input = st.sidebar.text_input("Enter children’s names (comma-separated)", "Winter,Micah")
kids = [k.strip() for k in kids_input.split(",")]

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
start_time = timedelta(hours=start_time_input.hour, minutes=start_time_input.minute)
end_time = timedelta(hours=end_time_input.hour, minutes=end_time_input.minute)

# Theme selection
theme = st.sidebar.selectbox("Choose theme", ["Pastel", "Dark", "Bright"])

# -------------------------
# --- Subjects Input ---
# -------------------------
st.sidebar.subheader("Subjects (max 5)")
subjects = []
for i in range(5):
    name = st.sidebar.text_input(f"Subject {i+1} Name", key=f"name_{i}")
    if name:
        sessions = st.sidebar.number_input(f"Sessions/week for {name}", min_value=1, value=1, key=f"sessions_{i}")
        length = st.sidebar.number_input(
            f"Length per session (minutes) for {name}",
            min_value=time_increment,
            step=time_increment,
            value=max(time_increment, 45),
            key=f"length_{i}"
        )
        shared = st.sidebar.checkbox(f"Shared across all kids?", key=f"shared_{i}")
        emoji_icon = st.sidebar.text_input(f"Emoji/icon for {name}", value="📚", max_chars=2, key=f"emoji_{i}")
        subjects.append({"name": name, "sessions": sessions, "length": length, "shared": shared, "icon": emoji_icon})

# -------------------------
# --- Fixed Commitments ---
# -------------------------
st.sidebar.subheader("Fixed Commitments (max 3)")
fixed = []
for i in range(3):
    fc_name = st.sidebar.text_input(f"Fixed Commitment {i+1} Name", key=f"fc_name_{i}")
    if fc_name:
        fc_day = st.sidebar.selectbox(f"Day for {fc_name}", days_of_week, key=f"fc_day_{i}")
        fc_start_time = st.sidebar.time_input(f"Start time for {fc_name}", value=default_start, key=f"fc_start_{i}")
        fc_length = st.sidebar.number_input(f"Length (minutes) for {fc_name}", min_value=time_increment, step=time_increment, value=time_increment, key=f"fc_length_{i}")
        fixed.append({
            "name": fc_name,
            "day": fc_day,
            "start": timedelta(hours=fc_start_time.hour, minutes=fc_start_time.minute),
            "length": fc_length
        })

# -------------------------
# --- Scheduling Logic ---
# -------------------------
def schedule_planner(subjects, fixed, kids, days_of_week, start_time, end_time, time_increment):
    schedule = {day: {kid: [] for kid in kids} for day in days_of_week}
    unscheduled_subjects = []

    # Fixed commitments first
    for fc in fixed:
        day = fc["day"]
        start = fc["start"]
        end = start + timedelta(minutes=fc["length"])
        for kid in kids:
            schedule[day][kid].append((start, end, fc["name"], "fixed", "⏰"))

    # Subjects
    for subj in subjects:
        name = subj["name"]
        length = subj["length"]
        sessions_needed = subj["sessions"]
        shared = subj["shared"]
        icon = subj["icon"]

        for s in range(sessions_needed):
            placed = False
            for day in days_of_week:
                if shared:
                    current_time = start_time
                    while current_time + timedelta(minutes=length) <= end_time:
                        conflict = False
                        for kid in kids:
                            for b in schedule[day][kid]:
                                if not (current_time + timedelta(minutes=length) <= b[0] or current_time >= b[1]):
                                    conflict = True
                                    break
                            if conflict: break
                        if not conflict:
                            for kid in kids:
                                schedule[day][kid].append((current_time, current_time + timedelta(minutes=length), name, "shared", icon))
                            placed = True
                            break
                        current_time += timedelta(minutes=time_increment)
                else:
                    for kid in kids:
                        current_time = start_time
                        while current_time + timedelta(minutes=length) <= end_time:
                            conflict = False
                            for b in schedule[day][kid]:
                                if not (current_time + timedelta(minutes=length) <= b[0] or current_time >= b[1]):
                                    conflict = True
                                    break
                            if not conflict:
                                schedule[day][kid].append((current_time, current_time + timedelta(minutes=length), name, "individual", icon))
                                placed = True
                                break
                            current_time += timedelta(minutes=time_increment)
                if placed: break
            if not placed:
                unscheduled_subjects.append(name)
    return schedule, unscheduled_subjects

schedule, unscheduled_subjects = schedule_planner(subjects, fixed, kids, days_of_week, start_time, end_time, time_increment)

# -------------------------
# --- Plotting Function ---
# -------------------------
def plot_schedule(schedule, kids, days_of_week, theme, week_view=True):
    df_plot = []
    # Color palettes
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
    if week_view:
        facet_col = "Day"
        facet_col_wrap = 2
    else:
        facet_col = None
        facet_col_wrap = None

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

# -------------------------
# --- Main Display ---
# -------------------------
st.subheader("Visual Schedule")
week_view_toggle = st.checkbox("Week view (uncheck for single day)", value=True)

# Collapsible sections per kid
for kid in kids:
    with st.expander(f"{kid}'s Schedule", expanded=True):
        plot_schedule({day: {kid: schedule[day][kid] for kid in [kid]} for day in days_of_week}, [kid], days_of_week, theme, week_view_toggle)

# -------------------------
# --- Weekly Summary ---
# -------------------------
st.subheader("Weekly Summary")
summary_rows = []
for kid in kids:
    subj_hours = {}
    for day in days_of_week:
        for block in schedule[day][kid]:
            name = block[2]
            length_hours = block[1].total_seconds() / 3600 - block[0].total_seconds() / 3600
            subj_hours[name] = subj_hours.get(name, 0) + length_hours
    for name, hours in subj_hours.items():
        summary_rows.append({"Kid": kid, "Subject": name, "Hours": round(hours, 2)})

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df)

# -------------------------
# --- Unschedulable Subjects ---
# -------------------------
if unscheduled_subjects:
    st.warning("⚠️ Could not fit the following subjects: " + ", ".join(set(unscheduled_subjects)))

# -------------------------
# --- Export Buttons ---
# -------------------------
st.subheader("Export Schedule")
# CSV export
csv = io.StringIO()
summary_df.to_csv(csv, index=False)
st.download_button("Download Summary CSV", csv.getvalue(), file_name="weekly_summary.csv", mime="text/csv")

# PDF export placeholder (needs additional libraries like FPDF/ReportLab)
st.info("PDF export coming soon!")
