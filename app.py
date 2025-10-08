import streamlit as st
import pandas as pd

st.set_page_config(page_title="Homeschool Timetable Builder", layout="wide")

st.title("🏡 Homeschool Timetable Builder")

st.markdown("""
Easily build a flexible timetable with 15-minute lesson blocks.  
Parents can add or edit subjects freely, specify morning/afternoon preferences, and manage up to 8 children.
""")

# Sidebar setup
st.sidebar.header("Configuration")
num_children = st.sidebar.number_input("Number of children", min_value=1, max_value=8, value=3)
time_start = st.sidebar.time_input("Start time", value=pd.Timestamp("08:00").time())
time_end = st.sidebar.time_input("End time", value=pd.Timestamp("15:00").time())

# Generate 15-minute time blocks
time_slots = pd.date_range(start=str(time_start), end=str(time_end), freq="15min").strftime("%H:%M").tolist()

# Subject input
st.sidebar.subheader("Subjects & Preferences")
subjects = {}
for i in range(5):  # 5 subjects by default
    subj = st.sidebar.text_input(f"Subject {i+1}", value=f"Subject {i+1}")
    pref = st.sidebar.selectbox(f"{subj} preference", ["Any", "Morning", "Afternoon"], key=f"pref_{i}")
    subjects[subj] = pref

# Build timetable grid
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
st.subheader("🗓️ Timetable")

def create_empty_timetable():
    data = []
    for day in days:
        for time in time_slots:
            data.append({"Day": day, "Time": time, "Lesson": ""})
    return pd.DataFrame(data)

timetable = create_empty_timetable()

# Lesson allocation
st.sidebar.subheader("Auto-populate Flexible Lessons")
if st.sidebar.button("Auto-Populate"):
    for subj, pref in subjects.items():
        for idx in timetable.index:
            hour = int(timetable.loc[idx, "Time"].split(":")[0])
            if timetable.loc[idx, "Lesson"] == "":
                if pref == "Morning" and hour < 12:
                    timetable.at[idx, "Lesson"] = subj
                elif pref == "Afternoon" and hour >= 12:
                    timetable.at[idx, "Lesson"] = subj
                elif pref == "Any":
                    timetable.at[idx, "Lesson"] = subj

# Display timetable
for day in days:
    st.markdown(f"### {day}")
    df_day = timetable[timetable["Day"] == day][["Time", "Lesson"]]
    st.dataframe(df_day, hide_index=True, use_container_width=True)

# Download timetable
csv = timetable.to_csv(index=False).encode("utf-8")
st.download_button(
    label="💾 Download Timetable as CSV",
    data=csv,
    file_name="homeschool_timetable.csv",
    mime="text/csv",
)
