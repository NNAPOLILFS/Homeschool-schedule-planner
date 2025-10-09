import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Homeschool Planner", layout="wide")

st.title("🎨 Homeschool Planner (Daily View)")

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("Settings")

children = [c.strip() for c in st.sidebar.text_input("Enter children's names (comma separated):", "Winter, Micah").split(",")]
day_start = st.sidebar.time_input("School start time", datetime.strptime("08:00", "%H:%M").time())
day_end = st.sidebar.time_input("School end time", datetime.strptime("15:00", "%H:%M").time())
time_increment = st.sidebar.number_input("Time increment (minutes)", min_value=15, max_value=120, step=15, value=30)

# Pastel colour palette
pastel_palette = [
    "#F9D5E5", "#FCE2CE", "#D5E1DF", "#E2F0CB", "#C5D5E4",
    "#F7D8BA", "#EAD5E6", "#D0E6A5", "#FFB7B2", "#B5EAD7"
]
random.shuffle(pastel_palette)

subject_emojis = ["📚", "🔢", "🌏", "🎨", "🧪"]

# ------------------------
# Subject Inputs (5 fixed slots)
# ------------------------
st.header("Subjects")
subjects = []
for i in range(5):
    with st.expander(f"Subject {i+1}"):
        name = st.text_input(f"Name for Subject {i+1}", key=f"name_{i}")
        sessions = st.number_input(f"Sessions per week for {name or 'Subject '+str(i+1)}", min_value=0, max_value=10, value=0, step=1, key=f"sessions_{i}")
        length = st.number_input(f"Session length (minutes)", min_value=time_increment, step=time_increment, value=time_increment*2, key=f"length_{i}")
        shared = st.checkbox("Shared subject across all kids", key=f"shared_{i}")
        if name:
            subjects.append({
                "name": name,
                "sessions": sessions,
                "length": length,
                "shared": shared,
                "emoji": subject_emojis[i % len(subject_emojis)],
                "color": pastel_palette[i % len(pastel_palette)]
            })

# ------------------------
# Fixed Commitments
# ------------------------
st.header("Fixed Commitments")
commitments = {kid: [] for kid in children}
for kid in children:
    st.subheader(f"{kid}'s Commitments")
    for j in range(2):  # Two placeholders per child
        name = st.text_input(f"Commitment {j+1} for {kid}", key=f"commit_name_{kid}_{j}")
        start = st.time_input(f"Start time for {name or f'Commitment {j+1}'} ({kid})", key=f"commit_start_{kid}_{j}", value=day_start)
        end = st.time_input(f"End time for {name or f'Commitment {j+1}'} ({kid})", key=f"commit_end_{kid}_{j}", value=day_start)
        if name and start < end:
            commitments[kid].append({
                "name": name,
                "start": timedelta(hours=start.hour, minutes=start.minute),
                "end": timedelta(hours=end.hour, minutes=end.minute)
            })

# ------------------------
# Autofill Button
# ------------------------
if st.button("✨ Autofill Schedule"):
    st.subheader("📅 Daily Schedule")
    start_delta = timedelta(hours=day_start.hour, minutes=day_start.minute)
    end_delta = timedelta(hours=day_end.hour, minutes=day_end.minute)

    # Time slots
    day_slots = []
    cur = start_delta
    while cur + timedelta(minutes=time_increment) <= end_delta:
        day_slots.append((cur, cur + timedelta(minutes=time_increment)))
        cur += timedelta(minutes=time_increment)

    # Build schedules
    schedule = {kid: [] for kid in children}
    unscheduled = []

    for subj in subjects:
        if subj["sessions"] == 0:
            continue

        subj_len = timedelta(minutes=subj["length"])
        needed_slots = int(subj_len / timedelta(minutes=time_increment))

        if subj["shared"]:
            placed_sessions = 0
            for start, end in day_slots:
                block = (start, start + subj_len)
                if all(
                    all(not (block[0] < c["end"] and block[1] > c["start"]) for c in commitments[k])
                    and all(not (block[0] < s[1] and block[1] > s[0]) for s in schedule[k])
                    for k in children
                ):
                    for k in children:
                        schedule[k].append((block[0], block[1], subj["emoji"] + " " + subj["name"], subj["color"]))
                    placed_sessions += 1
                if placed_sessions >= subj["sessions"]:
                    break
            if placed_sessions < subj["sessions"]:
                unscheduled.append(subj["name"])
        else:
            for kid in children:
                placed_sessions = 0
                for start, end in day_slots:
                    block = (start, start + subj_len)
                    if all(not (block[0] < c["end"] and block[1] > c["start"]) for c in commitments[kid]) and \
                       all(not (block[0] < s[1] and block[1] > s[0]) for s in schedule[kid]):
                        schedule[kid].append((block[0], block[1], subj["emoji"] + " " + subj["name"], subj["color"]))
                        placed_sessions += 1
                    if placed_sessions >= subj["sessions"]:
                        break
                if placed_sessions < subj["sessions"]:
                    unscheduled.append(f"{subj['name']} ({kid})")

    # Plot all kids together
    df_plot = []
    base_date = datetime(2000, 1, 1)
    for kid in children:
        for s in schedule[kid]:
            df_plot.append({
                "Kid": kid,
                "Start": base_date + s[0],
                "End": base_date + s[1],
                "Subject": s[2],
                "Color": s[3]
            })
        for c in commitments[kid]:
            df_plot.append({
                "Kid": kid,
                "Start": base_date + c["start"],
                "End": base_date + c["end"],
                "Subject": "🕒 " + c["name"],
                "Color": "#CCCCCC"
            })

    if df_plot:
        df = pd.DataFrame(df_plot)
        fig = px.timeline(df, x_start="Start", x_end="End", y="Kid", color="Subject", color_discrete_map={r["Subject"]: r["Color"] for _, r in df.iterrows()})
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            title="Daily Schedule (Pastel View)",
            xaxis_title="Time of Day",
            yaxis_title="Children",
            bargap=0.2,
            showlegend=True,
            template="simple_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No schedule data yet. Please fill in subjects and commitments.")

    # Summary
    st.subheader("📊 Summary")
    rows = []
    for kid in children:
        total_mins = sum((s[1]-s[0]).total_seconds()/60 for s in schedule[kid])
        rows.append({"Child": kid, "Total Hours": round(total_mins/60, 2)})
    st.table(pd.DataFrame(rows))

    if unscheduled:
        st.warning("Some subjects couldn’t be scheduled:")
        for u in unscheduled:
            st.write(f"- {u}")
