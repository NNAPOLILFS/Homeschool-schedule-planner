import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🎨 Homeschool Planner")

# ------------------------
# Sidebar Inputs
# ------------------------
st.sidebar.header("Settings")

children = [c.strip() for c in st.sidebar.text_input("Enter children's names (comma separated):", "Winter, Micah").split(",")]
day_start_time = st.sidebar.time_input("School day start time:", datetime.strptime("08:00", "%H:%M").time())
time_increment = 15  # Fixed increment
day_end_time = datetime.strptime("15:00", "%H:%M").time()  # Fixed end time

# Pastel palette
pastel_palette = [
    "#F9D5E5", "#FCE2CE", "#D5E1DF", "#E2F0CB", "#C5D5E4",
    "#F7D8BA", "#EAD5E6", "#D0E6A5", "#FFB7B2", "#B5EAD7"
]

# Possible random emojis
subject_emojis = ["📚", "🔢", "🌏", "🎨", "🧪"]

# ------------------------
# Subject Inputs (2 per child)
# ------------------------
st.header("Subjects")
subjects = {kid: [] for kid in children}
for kid in children:
    st.subheader(f"{kid}'s Subjects")
    for i in range(2):
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            name = st.text_input(f"Subje_
