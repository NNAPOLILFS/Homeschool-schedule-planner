# -------------------------------------------------------------
# Homeschool Planner – v1.1b & v1.2 Proportional Fractional Blocks
# -------------------------------------------------------------
# Version selector at top: choose between
# v1.1b – Classic table with start times
# v1.2 – Outlook-style shaded grid with proportional heights
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🏠 Homeschool Planner")

# -------------------
# Version Selector
# -------------------
if "selected_version" not in st.session_state:
    st.session_state.selected_version = None

if st.session_state.selected_version is None:
    st.write("Select the app version to test:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("v1.1b – Classic Schedule with Times"):
            st.session_state.selected_version = "v1.1b"
    with col2:
        if st.button("v1.2 – Outlook-style Fractional Blocks"):
            st.session_state.selected_version = "v1.2"
    st.stop()

# -------------------
# Shared Data Setup
# -------------------
PASTEL_COLOURS = [
    "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
    "#D7BAFF", "#FFBADD", "#FFD6BA", "#B5EAD7", "#E2F0CB"
]

if "children" not in st.session_state:
    st.session_state.children = {}
if "child_counter" not in st.session_state:
    st.session_state.child_counter = 1

# -------------------
# Child Setup
# -------------------
st.subheader("👧 Children Setup")
num_children = st.number_input("Number of Children", 1, 5, max(1, len(st.session_state.children) or 2))

while len(st.session_state.children) < num_children:
    cid = f"child_{st.session_state.child_counter}"
    st.session_state.children[cid] = {
        "display_name": f"Child {len(st.session_state.children)+1}",
        "subjects": [],
        "color_seed": random.randint(0, 9999)
    }
    st.session_state.child_counter += 1
while len(st.session_state.children) > num_children:
    st.session_state.children.popitem()

for cid, cdata in st.session_state.children.items():
    new_name = st.text_input(f"Name for {cdata['display_name']}", cdata["display_name"], key=f"name_{cid}")
    st.session_state.children[cid]["display_name"] = new_name

# -------------------
# Subject Setup
# -------------------
st.subheader("📚 Subjects Setup")
for cid, cdata in st.session_state.children.items():
    st.markdown(f"**{cdata['display_name']}**")
    add_subj = st.button(f"➕ Add subject for {cdata['display_name']}", key=f"addsubj_{cid}")
    if add_subj:
        subj_id = f"{cid}_subj{len(cdata['subjects'])+1}"
        st.session_state.children[cid]["subjects"].append({
            "id": subj_id,
            "name": f"Subject {len(cdata['subjects'])+1}",
            "duration": 30,
            "sessions": 3,
            "shared": False
        })
    for subj in cdata["subjects"]:
        cols = st.columns([2, 1, 1, 1])
        subj["name"] = cols[0].text_input("Subject", subj["name"], key=f"name_{subj['id']}")
        subj["duration"] = cols[1].selectbox("Duration (min)", [15, 30, 60], index=[15,30,60].index(subj["duration"]), key=f"dur_{subj['id']}")
        subj["sessions"] = cols[2].number_input("Sessions", 1, 7, subj["sessions"], key=f"sess_{subj['id']}")
        subj["shared"] = cols[3].checkbox("Shared", subj["shared"], key=f"share_{subj['id']}")

# -------------------
# Helper Functions
# -------------------
def distribute_subject_sessions(subject, days):
    sessions = subject["sessions"]
    distributed = []
    for i in range(sessions):
        distributed.append(days[i % len(days)])
    return distributed

def generate_pastel_color(seed):
    random.seed(seed)
    base = random.randint(100, 200)
    r = (base + random.randint(0, 55)) % 256
    g = (base + random.randint(0, 55)) % 256
    b = (base + random.randint(0, 55)) % 256
    return f'rgb({r},{g},{b})'

# -------------------
# Schedule Generation
# -------------------
if st.button("🧩 Generate Weekly Schedule"):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule = {day:{} for day in days}
    for day in days:
        for cid in st.session_state.children.keys():
            schedule[day][cid] = []

    for cid, cdata in st.session_state.children.items():
        for subj in cdata["subjects"]:
            distributed_days = distribute_subject_sessions(subj, days)
            for d in distributed_days:
                schedule[d][cid].append(subj)

    # -------------------
    # Display Logic
    # -------------------
    if st.session_state.selected_version == "v1.1b":
        st.subheader("📅 Weekly Schedule – v1.1b")
        for day in days:
            st.markdown(f"### {day}")
            cols = st.columns(len(st.session_state.children))
            for i, (cid, cdata) in enumerate(st.session_state.children.items()):
                with cols[i]:
                    st.markdown(f"**{cdata['display_name']}**")
                    df = []
                    for subj in schedule[day][cid]:
                        df.append({
                            "Subject": subj["name"],
                            "Duration (min)": subj["duration"],
                            "Sessions": subj["sessions"]
                        })
                    st.dataframe(pd.DataFrame(df), use_container_width=True, hide_index=True)

    elif st.session_state.selected_version == "v1.2":
        st.subheader("📅 Weekly Schedule – v1.2 Outlook-style Proportional Blocks")
        for day in days:
            st.markdown(f"### {day}")
            start_hour, end_hour = 7, 17
            min_slot = 60
            # Determine minimum slot for fractional display
            for cid, cdata in st.session_state.children.items():
                for subj in schedule[day][cid]:
                    min_slot = min(min_slot, subj["duration"])
            total_slots = int((end_hour - start_hour)*60 / min_slot)
            cols = st.columns(len(st.session_state.children)+1)
            # Time labels
            with cols[0]:
                st.write("Time")
                current_time = datetime.strptime("07:00", "%H:%M")
                for _ in range(total_slots):
                    st.markdown(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=min_slot)
            # Child schedules
            for i, (cid, cdata) in enumerate(st.session_state.children.items()):
                with cols[i+1]:
                    st.markdown(f"**{cdata['display_name']}**")
                    current_time = datetime.strptime("07:00", "%H:%M")
                    for slot in range(total_slots):
                        cell_html = ""
                        for subj in schedule[day][cid]:
                            # fractional height proportional to 60-min block
                            height_pct = (subj["duration"]/60)*60  # 60px per hour block
                            color = generate_pastel_color(cdata["color_seed"])
                            cell_html += f"<div style='background-color:{color}; width:100%; height:{height_pct}px; border-radius:4px; margin-bottom:2px;'>{subj['name']}</div>"
                        st.markdown(cell_html or "&nbsp;", unsafe_allow_html=True)
                        current_time += timedelta(minutes=min_slot)
