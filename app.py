import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Homeschool Planner v0.2", layout="wide")
st.title("🎨 Homeschool Planner v0.2")

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("Settings")

# Children
new_children = [c.strip() for c in st.sidebar.text_input("Enter children's names (comma separated):", "Winter, Micah").split(",")]

# Reset subjects/commitments if children changed
if "children" not in st.session_state or st.session_state["children"] != new_children:
    st.session_state["children"] = new_children
    st.session_state["subjects"] = {kid:[{"name":"","sessions":0,"length":60,"shared":False}] for kid in new_children}
    st.session_state["commitments"] = {kid: [] for kid in new_children}

children = st.session_state["children"]

# School day
day_start_time = st.sidebar.time_input("School day start time:", datetime.strptime("08:00", "%H:%M").time())
day_end_time = st.sidebar.time_input("School day end time:", datetime.strptime("15:00", "%H:%M").time())
time_increment = st.sidebar.selectbox("Schedule increment (minutes):", [15,30,60], index=2)

# Pastel colors and emojis
pastel_palette = ["#F9D5E5","#FCE2CE","#D5E1DF","#E2F0CB","#C5D5E4","#F7D8BA","#EAD5E6","#D0E6A5","#FFB7B2","#B5EAD7"]
subject_emojis = ["📚","🔢","🌏","🎨","🧪"]

# ------------------------
# Subjects Input
# ------------------------
st.sidebar.subheader("Subjects")
for kid in children:
    st.sidebar.markdown(f"**{kid}'s Subjects**")
    for i, subj in enumerate(st.session_state["subjects"][kid]):
        subj["name"] = st.sidebar.text_input(f"Name ({kid})", value=subj["name"], key=f"{kid}_name_{i}")
        subj["sessions"] = st.sidebar.number_input(f"Sessions/week", min_value=0, max_value=10, value=subj["sessions"], step=1, key=f"{kid}_sess_{i}")
        subj["length"] = st.sidebar.number_input(f"Length (min)", min_value=time_increment, step=time_increment, value=subj["length"], key=f"{kid}_len_{i}")
        subj["shared"] = st.sidebar.checkbox("Shared", value=subj["shared"], key=f"{kid}_shared_{i}")
    if st.sidebar.button(f"Add Subject for {kid}"):
        if len(st.session_state["subjects"][kid]) < 5:
            st.session_state["subjects"][kid].append({"name":"","sessions":0,"length":60,"shared":False})

# ------------------------
# Fixed Commitments Input
# ------------------------
add_commitments = st.sidebar.checkbox("Add fixed commitments for children?")
days_of_week = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

if not add_commitments:
    st.session_state["commitments"] = {kid: [] for kid in children}

if add_commitments:
    st.sidebar.subheader("Fixed Commitments")
    for kid in children:
        st.sidebar.markdown(f"**{kid}'s Commitments**")
        for i in range(2):  # max 2 commitments for speed
            name = st.sidebar.text_input(f"Commitment {i+1} Name ({kid})", key=f"{kid}_commit_name_{i}")
            day = st.sidebar.selectbox(f"Day ({kid})", days_of_week, key=f"{kid}_commit_day_{i}")
            start = st.sidebar.time_input(f"Start time ({kid})", key=f"{kid}_commit_start_{i}", value=day_start_time)
            end = st.sidebar.time_input(f"End time ({kid})", key=f"{kid}_commit_end_{i}", value=(datetime.combine(datetime.today(), start) + timedelta(minutes=60)).time())
            if name and start < end:
                if len(st.session_state["commitments"][kid]) <= i:
                    st.session_state["commitments"][kid].append({})
                st.session_state["commitments"][kid][i] = {
                    "name": name,
                    "day": day,
                    "start": timedelta(hours=start.hour, minutes=start.minute),
                    "end": timedelta(hours=end.hour, minutes=end.minute)
                }

# ------------------------
# Autofill Schedule Function
# ------------------------
def autofill_schedule(subjects, commitments, children, start_time, end_time, increment):
    schedule = {kid:{day:[] for day in days_of_week} for kid in children}
    unscheduled = []

    # Assign emoji and color
    for kid in children:
        for subj in subjects[kid]:
            if "emoji" not in subj or not subj["emoji"]:
                subj["emoji"] = random.choice(subject_emojis)
            if "color" not in subj or not subj["color"]:
                subj["color"] = random.choice(pastel_palette)

    # Create time slots
    slots = []
    cur = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_delta = timedelta(hours=end_time.hour, minutes=end_time.minute)
    while cur + timedelta(minutes=increment) <= end_delta:
        slots.append(cur)
        cur += timedelta(minutes=increment)

    # Place fixed commitments
    for kid in children:
        for c in commitments[kid]:
            schedule[kid][c["day"]].append({
                "start": c["start"],
                "end": c["end"],
                "label": f"🕒 {c['name']}",
                "color": "#CCCCCC"
            })

    # Place subjects with even distribution
    for kid in children:
        for subj in subjects[kid]:
            if subj["sessions"]==0 or not subj["name"]:
                continue
            length_delta = timedelta(minutes=subj["length"])
            placed_sessions = 0
            num_sessions = subj["sessions"]

            # Determine target days
            if num_sessions <= len(days_of_week):
                target_days = random.sample(days_of_week, num_sessions)
            else:
                times, remainder = divmod(num_sessions, len(days_of_week))
                target_days = days_of_week * times + random.sample(days_of_week, remainder)

            for day in target_days:
                for slot in slots:
                    overlap = any(not(slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[kid][day])
                    if not overlap:
                        if subj["shared"]:
                            overlap_all = False
                            for k in children:
                                if any(not(slot + length_delta <= s["start"] or slot >= s["end"]) for s in schedule[k][day]):
                                    overlap_all = True
                                    break
                            if overlap_all:
                                continue
                            for k in children:
                                schedule[k][day].append({
                                    "start": slot,
                                    "end": slot + length_delta,
                                    "label": f"{subj['emoji']} {subj['name']}",
                                    "color": subj["color"],
                                    "shared": True
                                })
                        else:
                            schedule[kid][day].append({
                                "start": slot,
                                "end": slot + length_delta,
                                "label": f"{subj['emoji']} {subj['name']}",
                                "color": subj["color"],
                                "shared": False
                            })
                        placed_sessions += 1
                        break
                if placed_sessions >= subj["sessions"]:
                    break
            if placed_sessions < subj["sessions"]:
                unscheduled.append(f"{subj['name']} ({kid})" if not subj["shared"] else f"{subj['name']} (shared)")

    # Sort schedules
    for kid in children:
        for day in days_of_week:
            schedule[kid][day] = sorted(schedule[kid][day], key=lambda x: x["start"])
    return schedule, unscheduled

# ------------------------
# Display Timetable
# ------------------------
if st.sidebar.button("✨ Autofill Schedule"):
    schedule, unscheduled = autofill_schedule(st.session_state["subjects"], st.session_state["commitments"], children, day_start_time, day_end_time, time_increment)
    st.subheader("📅 Daily Schedule")

    time_slots = []
    cur = timedelta(hours=day_start_time.hour, minutes=day_start_time.minute)
    end_delta = timedelta(hours=day_end_time.hour, minutes=day_end_time.minute)
    while cur < end_delta:
        time_slots.append(cur)
        cur += timedelta(minutes=time_increment)

    # Render table with merged shared subjects
    for day in days_of_week:
        st.markdown(f"### {day}")
        table_html = "<table style='border-collapse: collapse; width: 100%;'>"
        # Header
        table_html += "<tr style='background-color:#ddd'><th>Time</th>"
        for kid in children:
            table_html += f"<th>{kid}</th>"
        table_html += "</tr>"
        # Rows
        for t in time_slots:
            table_html += f"<tr><td>{(datetime.min + t).strftime('%H:%M')}</td>"
            skip_next = {kid:0 for kid in children}
            for kid in children:
                if skip_next[kid]>0:
                    skip_next[kid]-=1
                    continue
                label = ""
                cell_color = "#fff"
                for s in schedule[kid][day]:
                    if s["start"] <= t < s["end"]:
                        label = s["label"]
                        cell_color = s["color"]
                        # Count how many increments it spans
                        row_span = int((s["end"]-s["start"]).total_seconds()/(60*time_increment))
                        skip_next[kid] = row_span-1
                        break
                table_html += f"<td style='background-color:{cell_color}; text-align:center'>{label}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)

    # Summary
    st.subheader("📊 Weekly Summary")
    summary = []
    for kid in children:
        total_minutes = 0
        for day in days_of_week:
            total_minutes += sum((s["end"]-s["start"]).total_seconds()/60 for s in schedule[kid][day] if not s["label"].startswith("🕒"))
        summary.append({"Child": kid, "Total Hours": round(total_minutes/60,2)})
    st.table(pd.DataFrame(summary))

    if unscheduled:
        st.warning("Some subjects couldn’t be scheduled:")
        for u in unscheduled:
            st.write(f"- {u}")
