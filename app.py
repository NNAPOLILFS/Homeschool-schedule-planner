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
start_time = timedelta(hours=start_time_input.hour, minutes=start_time_input.minute)
end_time = timedelta(hours=end_time_input.hour, minutes=end_time_input.minute)

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
    # Subjects
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
# --- Autofill Schedule ---
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

    # Subjects
    for kid in kids:
        for subj in subjects[kid]:
            name = subj["name"]
            length = subj["length"]
            sessions_needed = subj["sessions"]
            shared = subj["shared"]
            icon = subj["icon"]
            for s in range(sessions_needed):
                placed = False
                for day in days_of_week:
                    if shared:
                        # Try to place for all kids
                        current_time = start_time
                        while current_time + timedelta(minutes=length) <= end_time:
                            conflict = False
                            for k in kids:
                                for b in schedule[day][k]:
                                    if not (current_time + timedelta(minutes=length) <= b[0] or current_time >= b[1]):
                                        conflict = True
                                        break
                                if conflict: break
                            if not conflict:
                                for k in kids:
                                    schedule[day][k].append((current_time, current_time + timedelta(minutes=length), name, "shared", icon))
                                placed = True
                                break
                            current_time += timedelta(minutes=time_increment)
                    else:
                        # Individual
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
                    unscheduled_subjects.append(f"{name} ({kid})")
    return schedule, unscheduled_subjects

# Autofill button
if st.button("Autofill Schedule"):
    schedule, unscheduled_subjects = schedule_planner(st.session_state.subjects, st.session_state.fixed, kids, days_of_week, start_time, end_time, time_increment)

    # -------------------------
    # --- Plotting Function ---
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

    # -------------------------
    # --- Display Schedule ---
    # -------------------------
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
        subj_hours = {}
        for day in days_of_week:
            for block in schedule[day][kid]:
                name = block[2]
                length_hours = block[1].total_seconds()/3600 - block[0].total_seconds()/3600
                subj_hours[name] = subj_hours.get(name, 0) + length_hours
        for name, hours in subj_hours.items():
            summary_rows.append({"Kid": kid, "Subject": name, "Hours": round(hours,2)})
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
    st.info("PDF export coming soon!")
