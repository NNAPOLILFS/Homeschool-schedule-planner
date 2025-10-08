import streamlit as st
import pandas as pd

st.set_page_config(page_title="Homeschool Timetable Builder", layout="wide")
st.title("🏡 Homeschool Timetable Builder")
st.markdown("""
Flexible homeschool timetable with fixed commitments, 15-minute blocks, weekend support, auto-filled lessons, and color-coded subjects.
""")

# --- Sidebar: Configuration ---
st.sidebar.header("Configuration")
num_children = st.sidebar.number_input("Number of children", min_value=1, max_value=8, value=3)
time_start = st.sidebar.time_input("Start time", value=pd.Timestamp("08:00").time())
time_end = st.sidebar.time_input("End time", value=pd.Timestamp("15:00").time())
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

time_slots = pd.date_range(start=str(time_start), end=str(time_end), freq="15min").strftime("%H:%M").tolist()

# --- Sidebar: Subjects & Preferences ---
st.sidebar.subheader("Subjects & Preferences")
subjects = {}
colors = {}  # Assign colors for each subject
default_colors = ["#FFCDD2","#C8E6C9","#BBDEFB","#FFF9C4","#D1C4E9"]
for i in range(5):
    subj = st.sidebar.text_input(f"Subject {i+1}", value=f"Subject {i+1}")
    pref = st.sidebar.selectbox(f"{subj} preference", ["Any", "Morning", "Afternoon"], key=f"pref_{i}")
    subjects[subj] = pref
    colors[subj] = default_colors[i % len(default_colors)]

# --- Sidebar: Fixed Commitments ---
st.sidebar.subheader("Fixed Commitments")
commitments = {}
for i in range(5):
    name = st.sidebar.text_input(f"Commitment {i+1} name", key=f"cname_{i}")
    day = st.sidebar.selectbox(f"Day", days, key=f"cday_{i}")
    time = st.sidebar.time_input(f"Time", value=pd.Timestamp("09:00").time(), key=f"ctime_{i}")
    if name:
        commitments[(day, time.strftime("%H:%M"))] = name

# --- Build empty timetable ---
def create_empty_timetable():
    data = []
    for day in days:
        for time in time_slots:
            row = {"Day": day, "Time": time}
            for child_idx in range(1, num_children + 1):
                row[f"Child {child_idx}"] = ""
            data.append(row)
    return pd.DataFrame(data)

timetable = create_empty_timetable()

# --- Fill in fixed commitments ---
for (day, time), name in commitments.items():
    for child_idx in range(1, num_children + 1):
        idx = timetable[(timetable["Day"] == day) & (timetable["Time"] == time)].index
        timetable.at[idx, f"Child {child_idx}"] = name

# --- Auto-populate lessons ---
st.sidebar.subheader("Auto-populate Lessons")
if st.sidebar.button("Auto-Populate"):
    for child_idx in range(1, num_children + 1):
        lesson_pool = []
        for subj, pref in subjects.items():
            lesson_pool.extend([{"subject": subj, "pref": pref}] * len(days))
        pool_idx = 0
        for day in days:
            day_slots = timetable[timetable["Day"] == day].index.tolist()
            for idx in day_slots:
                if timetable.at[idx, f"Child {child_idx}"] == "":
                    subj_info = lesson_pool[pool_idx % len(lesson_pool)]
                    hour = int(timetable.at[idx, "Time"].split(":")[0])
                    if (subj_info["pref"] == "Any" or
                        (subj_info["pref"] == "Morning" and hour < 12) or
                        (subj_info["pref"] == "Afternoon" and hour >= 12)):
                        timetable.at[idx, f"Child {child_idx}"] = subj_info["subject"]
                        pool_idx += 1

# --- Display timetable with color coding ---
st.subheader("🗓️ Timetable")

for day in days:
    st.markdown(f"### {day}")
    df_day = timetable[timetable["Day"] == day].drop(columns=["Day"]).set_index("Time")
    
    # Apply colors
    def colorize(val):
        return f'background-color: {colors.get(val,"")}' if val in colors else ''
    
    # Highlight weekends
    if day in ["Saturday", "Sunday"]:
        df_day_styled = df_day.style.applymap(lambda _: 'background-color: #ECEFF1')
        df_day_styled = df_day_styled.applymap(colorize)
    else:
        df_day_styled = df_day.style.applymap(colorize)
    
    st.dataframe(df_day_styled, use_container_width=True)

# --- Download CSV ---
csv = timetable.to_csv(index=False).encode("utf-8")
st.download_button(
    label="💾 Download Timetable as CSV",
    data=csv,
    file_name="homeschool_timetable.csv",
    mime="text/csv",
)
