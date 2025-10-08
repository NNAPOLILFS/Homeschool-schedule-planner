import streamlit as st
from datetime import time, timedelta, datetime
import pandas as pd
import numpy as np

st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("Homeschool Weekly Planner")

# =========================
# Session state for children
# =========================
if "children" not in st.session_state:
    st.session_state.children = []

# =========================
# Step 0: Planner settings
# =========================
st.header("Planner Settings")
day_start_hour = st.number_input("Start of Day (hour in 24h format)", min_value=0, max_value=23, value=7, step=1)
include_saturday = st.checkbox("Include Saturday?", value=False)
include_sunday = st.checkbox("Include Sunday?", value=False)

# Build days list
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
if include_saturday:
    days.append("Saturday")
if include_sunday:
    days.append("Sunday")

# =========================
# Step 1: Enter children
# =========================
num_children = st.number_input("Number of children", min_value=1, step=1, key="num_children_input")
st.header("Enter Children's Names")
for i in range(num_children):
    if len(st.session_state.children) < num_children:
        st.session_state.children.append("")
    st.session_state.children[i] = st.text_input(f"Child {i+1} Name", value=st.session_state.children[i], key=f"child_name_{i}")

# =========================
# Step 2: Fixed Commitments
# =========================
st.header("Fixed Commitments")
num_commitments = st.number_input("How many fixed commitments?", min_value=0, step=1, key="num_commitments")
commitments = []

for i in range(num_commitments):
    st.subheader(f"Commitment {i+1}")
    child = st.selectbox(f"Child (Commitment {i+1})", st.session_state.children, key=f"commit_child_{i}")
    name = st.text_input(f"Commitment Name {i+1}", key=f"commit_name_{i}")
    day = st.selectbox(f"Day for Commitment {i+1}", days, key=f"commit_day_{i}")
    start_time = st.time_input(f"Start Time {i+1}", key=f"commit_start_{i}")
    end_time = st.time_input(f"End Time {i+1}", key=f"commit_end_{i}")
    if child and name:
        commitments.append({"Child": child, "Commitment": name, "Day": day, "Start": start_time, "End": end_time})

# =========================
# Step 3: Subjects per Child
# =========================
st.header("Subjects per Child")
subjects_info = {}
for idx, child_name in enumerate(st.session_state.children):
    st.subheader(f"Subjects for {child_name}")
    num_subjects = st.number_input(f"Number of subjects for {child_name}", min_value=1, step=1, key=f"num_subjects_{idx}")
    subjects = []
    for s in range(num_subjects):
        subject_name = st.text_input(f"{child_name} - Subject {s+1} Name", key=f"subject_{idx}_{s}")
        frequency = st.number_input(f"{child_name} - {subject_name} times per week", min_value=1, max_value=len(days), step=1, key=f"freq_{idx}_{s}")
        duration = st.number_input(f"{child_name} - {subject_name} duration (minutes, multiple of 15)", min_value=15, max_value=480, step=15, key=f"duration_{idx}_{s}")
        if subject_name:
            subjects.append({"Subject": subject_name, "Frequency": frequency, "Duration": duration})
    subjects_info[child_name] = subjects

# =========================
# Step 4: Scheduler
# =========================
st.header("Weekly Schedule")
schedule = {day: [] for day in days}

# Helper: convert time to minutes
def time_to_minutes(t):
    return t.hour * 60 + t.minute

# Helper: convert minutes to time
def minutes_to_time(m):
    h = m // 60
    min_ = m % 60
    return time(h, min_)

# Create daily availability for each child
availability = {child: {day: [] for day in days} for child in st.session_state.children}
for child in st.session_state.children:
    for day in days:
        # Start of day in minutes
        day_start = day_start_hour * 60
        # End of day = 18:00 by default
        day_end = 18 * 60
        # start with full day
        availability[child][day].append([day_start, day_end])

# Remove fixed commitments from availability
for c in commitments:
    start_min = time_to_minutes(c["Start"])
    end_min = time_to_minutes(c["End"])
    slots = availability[c["Child"]][c["Day"]]
    new_slots = []
    for slot in slots:
        # slot = [slot_start, slot_end]
        if end_min <= slot[0] or start_min >= slot[1]:
            # no overlap
            new_slots.append(slot)
        else:
            if start_min > slot[0]:
                new_slots.append([slot[0], start_min])
            if end_min < slot[1]:
                new_slots.append([end_min, slot[1]])
    availability[c["Child"]][c["Day"]] = new_slots

# Assign subjects
import random
for child, subs in subjects_info.items():
    for sub in subs:
        freq = sub["Frequency"]
        duration = sub["Duration"]
        # pick days randomly from available days
        assigned_days = random.sample(days, freq)
        for day in assigned_days:
            slots = availability[child][day]
            # find first slot that can fit duration
            placed = False
            for i, slot in enumerate(slots):
                slot_start, slot_end = slot
                if slot_end - slot_start >= duration:
                    # assign subject
                    start_time = slot_start
                    end_time = slot_start + duration
                    schedule[day].append(f"{child}: {sub['Subject']} ({minutes_to_time(start_time).strftime('%H:%M')}-{minutes_to_time(end_time).strftime('%H:%M')})")
                    # update availability
                    new_slots = []
                    if start_time > slot_start:
                        new_slots.append([slot_start, start_time])
                    if end_time < slot_end:
                        new_slots.append([end_time, slot_end])
                    slots.pop(i)
                    slots[i:i] = new_slots
                    placed = True
                    break
            if not placed:
                schedule[day].append(f"{child}: {sub['Subject']} (Could not schedule)")

# Add fixed commitments to schedule display
for c in commitments:
    schedule[c["Day"]].append(f"{c['Child']} - {c['Commitment']} ({c['Start'].strftime('%H:%M')}-{c['End'].strftime('%H:%M')})")

# Sort schedule by start time
def sort_schedule(items):
    def key_fn(item):
        parts = item.split("(")
        if len(parts) > 1:
            times = parts[1].replace(")","").split("-")
            return int(times[0].split(":")[0])*60 + int(times[0].split(":")[1])
        else:
            return 0
    return sorted(items, key=key_fn)

# Display schedule
for day in days:
    st.subheader(day)
    day_items = sort_schedule(schedule[day])
    for item in day_items:
        st.write(f"- {item}")
