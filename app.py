# -------------------------------------------------------------
# Version 1.1a – Added stable internal IDs for children & subjects
# -------------------------------------------------------------
# ✅ Builds on Prototype Master Version (1.0b)
# ✅ Adds internal IDs for children and subjects to ensure data
#    consistency when names are changed or items are reordered.
# ✅ No layout, schedule generation, or colour logic changed.
# -------------------------------------------------------------

import streamlit as st
import pandas as pd
import random

# -------------------
# Helper functions
# -------------------

def generate_pastel_color(seed):
    random.seed(seed)
    base = random.randint(100, 200)
    r = (base + random.randint(0, 55)) % 256
    g = (base + random.randint(0, 55)) % 256
    b = (base + random.randint(0, 55)) % 256
    return f'rgb({r},{g},{b})'

def distribute_subject_sessions(subject, days):
    sessions = subject["sessions"]
    distributed = []
    for i in range(sessions):
        distributed.append(days[i % len(days)])
    return distributed

# -------------------
# Initialization
# -------------------

if "children" not in st.session_state:
    st.session_state.children = {}
if "child_counter" not in st.session_state:
    st.session_state.child_counter = 1

# -------------------
# Top Bar Layout
# -------------------

st.title("🏠 Homeschool Planner")

# Section for adding children
with st.expander("👧 Add or Edit Children"):
    num_children = st.number_input("Number of children", 1, 5, len(st.session_state.children) or 1)
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

# -------------------
# Subjects Section
# -------------------

for cid, cdata in st.session_state.children.items():
    st.subheader(f"🎒 {cdata['display_name']}")
    new_name = st.text_input(f"Enter name for {cdata['display_name']}", cdata["display_name"], key=f"name_{cid}")
    st.session_state.children[cid]["display_name"] = new_name

    add_subj = st.button(f"➕ Add subject for {new_name}", key=f"addsubj_{cid}")
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
        subj["duration"] = cols[1].selectbox("Duration (min)", [15, 30, 60], index=[15, 30, 60].index(subj["duration"]), key=f"dur_{subj['id']}")
        subj["sessions"] = cols[2].number_input("Sessions", 1, 7, subj["sessions"], key=f"sess_{subj['id']}")
        subj["shared"] = cols[3].checkbox("Shared", subj["shared"], key=f"share_{subj['id']}")

# -------------------
# Schedule Generation
# -------------------

if st.button("🧩 Generate Weekly Schedule"):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    start_hour, end_hour = 7, 17
    slot_length = 15

    schedule = {day: {} for day in days}
    for day in days:
        for cid, cdata in st.session_state.children.items():
            schedule[day][cid] = []

    # Fill schedule evenly using internal IDs
    for cid, cdata in st.session_state.children.items():
        for subj in cdata["subjects"]:
            distributed_days = distribute_subject_sessions(subj, days)
            for d in distributed_days:
                schedule[d][cid].append(subj)

    st.subheader("📅 Weekly Schedule")
    for day in days:
        st.markdown(f"### {day}")
        cols = st.columns(len(st.session_state.children))
        for i, (cid, cdata) in enumerate(st.session_state.children.items()):
            df = []
            for subj in schedule[day][cid]:
                df.append({
                    "Subject": subj["name"],
                    "Duration (min)": subj["duration"],
                    "Sessions": subj["sessions"]
                })
            table = pd.DataFrame(df)
            pastel_color = generate_pastel_color(cdata['color_seed'])
            with cols[i]:
                st.markdown(f"**{cdata['display_name']}**")
                st.dataframe(table, use_container_width=True, hide_index=True)

# -------------------
# Checklist
# -------------------

st.markdown("---")
st.markdown("**Checklist for v1.1a Testing:**")
st.markdown("""
- ✅ Edit child names — schedule should show new names correctly  
- ✅ Add or edit subjects — changes persist and display properly  
- ✅ Verify internal IDs remain stable when renaming or reordering subjects  
- ✅ Schedule still distributes sessions evenly  
- ✅ Pastel colors remain per child  
""")
