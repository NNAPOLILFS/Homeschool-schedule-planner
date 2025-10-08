import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("Homeschool Planner")

# --- Step 1: Basic Inputs ---
kids_input = st.text_input("Enter children’s names separated by commas", "Alice,Bob")
kids = [k.strip() for k in kids_input.split(",")]

start_time_input = st.time_input("Day start time", value=datetime.strptime("07:00", "%H:%M").time())
start_time = timedelta(hours=start_time_input.hour, minutes=start_time_input.minute)

include_saturday = st.checkbox("Include Saturday?", value=True)
include_sunday = st.checkbox("Include Sunday?", value=False)

days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
if include_saturday:
    days_of_week.append("Saturday")
if include_sunday:
    days_of_week.append("Sunday")

time_increment = st.selectbox("Choose schedule increment (minutes)", [15, 30, 60], index=0)

# --- Step 2: Dynamic Subjects & Fixed Commitments ---
if 'subjects' not in st.session_state:
    st.session_state.subjects = []

st.subheader("Subjects")
if st.button("Add Subject"):
    st.session_state.subjects.append({
        "name": "",
        "sessions": 1,
        "length": 45,
        "shared": False
    })

for i, subj in enumerate(st.session_state.subjects):
    st.text_input(f"Subject {i+1} Name", value=subj["name"], key=f"name_{i}", on_change=lambda i=i: st.session_state.subjects.__setitem__(i, {**st.session_state.subjects[i], "name": st.session_state[f"name_{i}"]}))
    st.number_input(f"Sessions per week for {subj['name']}", min_value=1, key=f"sessions_{i}", value=subj["sessions"], on_change=lambda i=i: st.session_state.subjects.__setitem__(i, {**st.session_state.subjects[i], "sessions": st.session_state[f"sessions_{i}"]}))
    st.number_input(f"Length of each session (minutes) for {subj['name']}", min_value=time_increment, step=time_increment, key=f"length_{i}", value=subj["length"], on_change=lambda i=i: st.session_state.subjects.__setitem__(i, {**st.session_state.subjects[i], "length": st.session_state[f"length_{i}"]}))
    st.checkbox(f"Shared across all kids?", value=subj["shared"], key=f"shared_{i}", on_change=lambda i=i: st.session_state.subjects.__setitem__(i, {**st.session_state.subjects[i], "shared": st.session_state[f"shared_{i}"]}))

if 'fixed' not in st.session_state:
    st.session_state.fixed = []

st.subheader("Fixed Commitments")
if st.button("Add Fixed Commitment"):
    st.session_state.fixed.append({
        "name": "",
        "day": days_of_week[0],
        "start": start_time,
        "length": 30
    })

for i, fc in enumerate(st.session_state.fixed):
    st.text_input(f"Fixed Commitment {i+1} Name", value=fc["name"], key=f"fc_name_{i}", on_change=lambda i=i: st.session_state.fixed.__setitem__(i, {**st.session_state.fixed[i], "name": st.session_state[f"fc_name_{i}"]}))
    st.selectbox(f"Day for {fc['name']}", days_of_week, index=0, key=f"fc_day_{i}", on_change=lambda i=i: st.session_state.fixed.__setitem__(i, {**st.session_state.fixed[i], "day": st.session_state[f"fc_day_{i}"]}))
    st.time_input(f"Start time for {fc['name']}", value=datetime.strptime("07:00", "%H:%M").time(), key=f"fc_start_{i}", on_change=lambda i=i: st.session_state.fixed.__setitem__(i, {**st.session_state.fixed[i], "start": timedelta(hours=st.session_state[f"fc_start_{i}"].hour, minutes=st.session_state[f"fc_start_{i}"].minute)}))
    st.number_input(f"Length (minutes) for {fc['name']}", min_value=time_increment, step=time_increment, key=f"fc_length_{i}", value=fc["length"], on_change=lambda i=i: st.session_state.fixed.__setitem__(i, {**st.session_state.fixed[i], "length": st.session_state[f"fc_length_{i}"]}))

# --- Step 3: Helper function to find free slots ---
def find_free_slot(existing_blocks, length, start_day_time, increment):
    # Sort existing blocks
    existing_blocks = sorted(existing_blocks, key=lambda x: x[0])
    current = start_day_time
    for block in existing_blocks:
        if block[0] - current >= timedelta(minutes=length):
            return current
        current = max(current, block[1])
    return current  # returns end of last block if still enough time

# --- Step 4: Scheduling ---
if st.button("Generate Schedule"):
    schedule = {day: {kid: [] for kid in kids} for day in days_of_week}
    unscheduled_subjects = []

    # Place fixed commitments first
    for fc in st.session_state.fixed:
        day = fc["day"]
        start = fc["start"]
        end = start + timedelta(minutes=fc["length"])
        for kid in kids:
            schedule[day][kid].append((start, end, fc["name"]))

    # Schedule subjects
    for subj in st.session_state.subjects:
        name = subj["name"]
        length = subj["length"]
        sessions_needed = subj["sessions"]
        shared = subj["shared"]

        for s in range(sessions_needed):
            placed = False
            for day in days_of_week:
                if shared:
                    # find a slot common to all kids
                    max_start = start_time
                    # Find earliest common free slot
                    while max_start + timedelta(minutes=length) <= timedelta(hours=19):  # arbitrary 19h limit
                        conflict = False
                        for kid in kids:
                            for b in schedule[day][kid]:
                                if not (max_start + timedelta(minutes=length) <= b[0] or max_start >= b[1]):
                                    conflict = True
                                    break
                            if conflict:
                                break
                        if not conflict:
                            # assign slot to all kids
                            for kid in kids:
                                schedule[day][kid].append((max_start, max_start + timedelta(minutes=length), name))
                            placed = True
                            break
                        max_start += timedelta(minutes=time_increment)
                else:
                    # individual placement per kid
                    for kid in kids:
                        max_start = start_time
                        while max_start + timedelta(minutes=length) <= timedelta(hours=19):
                            conflict = False
                            for b in schedule[day][kid]:
                                if not (max_start + timedelta(minutes=length) <= b[0] or max_start >= b[1]):
                                    conflict = True
                                    break
                            if not conflict:
                                schedule[day][kid].append((max_start, max_start + timedelta(minutes=length), name))
                                placed = True
                                break
                            max_start += timedelta(minutes=time_increment)
                if placed:
                    break
            if not placed:
                unscheduled_subjects.append(name)

    # --- Step 5: Display Schedule ---
    st.subheader("Generated Schedule")
    for day in days_of_week:
        st.write(f"### {day}")
        for kid in kids:
            st.write(f"**{kid}**")
            kid_schedule = sorted(schedule[day][kid], key=lambda x: x[0])
            if kid_schedule:
                df = pd.DataFrame([{
                    "Start": str(block[0]),
                    "End": str(block[1]),
                    "Subject": block[2]
                } for block in kid_schedule])
                st.table(df)
            else:
                st.write("No sessions scheduled.")

    if unscheduled_subjects:
        st.warning("⚠️ Could not fit the following subjects into the schedule due to time constraints: " +
                   ", ".join(set(unscheduled_subjects)))
