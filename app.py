# app_v1_6_2.py
"""
Homeschool Planner v1.6.2
- Book Search (renamed)
- Clock-style inputs for start/end times
- Grid-style weekly schedule (day boxes with kids and times)
- Dynamic kids, subjects, lessons, commitments
"""

import streamlit as st
import requests
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta, time

# -------------------------
# Session state initialization
# -------------------------
def init_store():
    if "kids" not in st.session_state:
        st.session_state["kids"] = []
    if "subjects" not in st.session_state:
        st.session_state["subjects"] = []
    if "lessons" not in st.session_state:
        st.session_state["lessons"] = []
    if "commitments" not in st.session_state:
        st.session_state["commitments"] = []
init_store()

# -------------------------
# Helper functions
# -------------------------
def add_kid(name, age):
    kid_id = f"kid_{len(st.session_state['kids'])+1}"
    st.session_state["kids"].append({"id": kid_id, "name": name, "age": age})
    return kid_id

def add_subject(name, duration=30, sessions_per_week=1, kids=[]):
    subj_id = f"subj_{len(st.session_state['subjects'])+1}"
    st.session_state["subjects"].append({
        "id": subj_id,
        "name": name,
        "duration": duration,
        "sessions_per_week": sessions_per_week,
        "kids": kids
    })
    return subj_id

def add_lesson(title, text, subject_id, kid_id=None):
    lesson_id = f"lesson_{len(st.session_state['lessons'])+1}"
    st.session_state["lessons"].append({
        "id": lesson_id,
        "title": title,
        "text": text,
        "subject_id": subject_id,
        "kid_id": kid_id
    })
    return lesson_id

def add_commitment(kid_id, day, start, end, description):
    commit_id = f"commit_{len(st.session_state['commitments'])+1}"
    st.session_state["commitments"].append({
        "id": commit_id,
        "kid_id": kid_id,
        "day": day,
        "start": start,
        "end": end,
        "description": description
    })
    return commit_id

# -------------------------
# OpenLibrary search
# -------------------------
def fetch_openlibrary(query, limit=6):
    try:
        r = requests.get("https://openlibrary.org/search.json", params={"q": query, "limit": limit}, timeout=10)
        data = r.json()
    except Exception:
        return []
    items = []
    for doc in data.get("docs", [])[:limit]:
        title = doc.get("title") or "Untitled"
        authors = ", ".join(doc.get("author_name") or [])
        year = doc.get("first_publish_year") or ""
        snippet = doc.get("first_sentence") or doc.get("subtitle") or ""
        text = f"{title} by {authors}. Published {year}. {snippet}"
        items.append({
            "id": f"ol_{doc.get('key')}",
            "title": title,
            "text": text,
            "source": "OpenLibrary",
            "url": f"https://openlibrary.org{doc.get('key')}" if doc.get("key") else ""
        })
    return items

# -------------------------
# Local TF-IDF search
# -------------------------
def local_semantic_search(query, lessons, top_k=6):
    if not lessons or not query.strip():
        return []
    texts = [l.get("text","") for l in lessons]
    vectorizer = TfidfVectorizer().fit(texts + [query])
    text_vectors = vectorizer.transform(texts)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, text_vectors)[0]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [lessons[i] for i in top_idx]

# -------------------------
# Grid schedule helpers
# -------------------------
def create_time_blocks(start_hour=6, end_hour=18, block_minutes=30):
    blocks = []
    for h in range(start_hour, end_hour):
        for m in range(0, 60, block_minutes):
            blocks.append(time(h, m))
    return blocks

def generate_weekly_grid_schedule(block_minutes=30):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_blocks = create_time_blocks(block_minutes=block_minutes)
    schedule_grid = {day: {k["name"]: [] for k in st.session_state["kids"]} for day in days}
    
    for kid in st.session_state["kids"]:
        kid_name = kid["name"]
        # Fixed commitments
        for c in st.session_state["commitments"]:
            if c["kid_id"] != kid["id"]:
                continue
            start_dt = c["start"]
            end_dt = c["end"]
            schedule_grid[c["day"]][kid_name].append({"start": start_dt, "end": end_dt, "event": f"Fixed: {c['description']}"})
        # Lessons
        for subj in st.session_state["subjects"]:
            if kid["id"] not in subj["kids"]:
                continue
            assigned_sessions = 0
            for day in days:
                if assigned_sessions >= subj["sessions_per_week"]:
                    break
                start_time = time(6 + assigned_sessions*subj["duration"]//60, 0)
                end_hour = start_time.hour + subj["duration"]//60
                end_minute = start_time.minute + subj["duration"]%60
                end_time = time(end_hour, end_minute)
                schedule_grid[day][kid_name].append({"start": start_time, "end": end_time, "event": f"Lesson: {subj['name']}"})
                assigned_sessions += 1
    return schedule_grid

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Homeschool Planner v1.6.2", layout="wide")
st.title("🎓 Homeschool Planner v1.6.2")

tabs = st.tabs(["👶 Kids","📚 Subjects","➕ Lessons","⏰ Commitments","📖 Book Search","🗓️ Weekly Calendar"])

# -------------------------
# Commitments tab with clock-style input
# -------------------------
with tabs[3]:
    st.header("Add Fixed Commitments")
    if st.session_state["kids"]:
        with st.form("commit_form", clear_on_submit=True):
            kid = st.selectbox("Kid", st.session_state["kids"], format_func=lambda k: k["name"], key="commit_kid")
            day = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"], key="commit_day")
            start = st.time_input("Start Time", value=time(8,0), key="commit_start")
            end = st.time_input("End Time", value=time(9,0), key="commit_end")
            desc = st.text_input("Description", key="commit_desc")
            submit = st.form_submit_button("Add Commitment")
            if submit:
                add_commitment(kid["id"], day, start, end, desc)
                st.success(f"Commitment '{desc}' added!")

# -------------------------
# Book Search tab
# -------------------------
with tabs[4]:
    st.header("Book Search")
    query = st.text_input("Enter search query", key="search_query")
    results = []
    if query:
        local_results = local_semantic_search(query, st.session_state["lessons"], top_k=6)
        lib_results = fetch_openlibrary(query, limit=6)
        results = local_results + lib_results
        for r in results:
            st.markdown(f"**{r.get('title','')}** ({r.get('source','Local')})")
            st.write(r.get("text",""))
            if r.get("url"):
                st.markdown(f"[Link]({r['url']})")

# -------------------------
# Weekly Calendar Grid tab
# -------------------------
with tabs[5]:
    st.header("Weekly Schedule (Grid)")
    grid = generate_weekly_grid_schedule()
    for day, kid_blocks in grid.items():
        st.subheader(day)
        for kid_name, events in kid_blocks.items():
            st.markdown(f"**{kid_name}**")
            if events:
                for e in events:
                    st.markdown(f"- {e['start'].strftime('%H:%M')} - {e['end'].strftime('%H:%M')}: {e['event']}")
            else:
                st.markdown("- Free")
