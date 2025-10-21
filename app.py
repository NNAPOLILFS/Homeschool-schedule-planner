# app_v1_6_1.py
"""
Homeschool Planner v1.6.1 - Robust version
- Unique Streamlit widget keys
- Dynamic kids/subjects with shared lessons
- Adjustable session duration & sessions/week
- Fixed commitments
- TF-IDF + OpenLibrary smart search (free)
- Outlook-style weekly calendar using Plotly
- Input validation & conflict-aware scheduling
"""

import streamlit as st
import requests
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
from datetime import datetime, timedelta

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
# Time & scheduling helpers
# -------------------------
def create_time_blocks(start_hour=6, end_hour=18, block_minutes=30):
    times = []
    for h in range(start_hour, end_hour):
        for m in range(0, 60, block_minutes):
            times.append(f"{h:02d}:{m:02d}")
    return times

def generate_weekly_schedule(start_hour=6, end_hour=18, block_minutes=30):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_blocks = create_time_blocks(start_hour, end_hour, block_minutes)
    calendar_rows = []
    
    for kid in st.session_state["kids"]:
        kid_id = kid["id"]
        # Fixed commitments first
        for c in st.session_state["commitments"]:
            if c["kid_id"] != kid_id:
                continue
            calendar_rows.append({
                "Kid": kid["name"],
                "Day": c["day"],
                "Start": datetime.strptime(c["start"], "%H:%M"),
                "End": datetime.strptime(c["end"], "%H:%M"),
                "Event": f"Fixed: {c['description']}"
            })
        # Lessons
        for subj in st.session_state["subjects"]:
            if kid_id not in subj["kids"]:
                continue
            assigned_sessions = 0
            for day in days:
                if assigned_sessions >= subj["sessions_per_week"]:
                    break
                duration = subj["duration"]
                start_time = datetime.strptime(f"{start_hour:02d}:00","%H:%M") + timedelta(minutes=assigned_sessions*duration)
                end_time = start_time + timedelta(minutes=duration)
                calendar_rows.append({
                    "Kid": kid["name"],
                    "Day": day,
                    "Start": start_time,
                    "End": end_time,
                    "Event": f"Lesson: {subj['name']}"
                })
                assigned_sessions += 1
    return pd.DataFrame(calendar_rows)

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Homeschool Planner v1.6.1", layout="wide")
st.title("🎓 Homeschool Planner v1.6.1")

tabs = st.tabs(["👶 Kids","📚 Subjects","➕ Lessons","⏰ Commitments","🔍 Smart Search","🗓️ Weekly Calendar"])

# -------------------------
# Kids tab
# -------------------------
with tabs[0]:
    st.header("Manage Kids")
    for i, kid in enumerate(st.session_state["kids"]):
        cols = st.columns([2,1])
        kid['name'] = cols[0].text_input(f"Kid {i+1} Name", value=kid.get('name',''), key=f"name_{kid['id']}")
        kid['age'] = cols[1].number_input("Age", value=kid.get('age',7), min_value=3, max_value=18, key=f"age_{kid['id']}")
    if st.button("Add Kid"):
        st.session_state["kids"].append({"id": f"kid_{len(st.session_state['kids'])+1}", "name": "", "age": 7})

# -------------------------
# Subjects tab
# -------------------------
with tabs[1]:
    st.header("Manage Subjects")
    for i, subj in enumerate(st.session_state["subjects"]):
        cols = st.columns([2,1,1,2])
        subj['name'] = cols[0].text_input(f"Subject {i+1} Name", value=subj.get('name',''), key=f"subj_name_{subj['id']}")
        subj['duration'] = cols[1].number_input("Duration (min)", value=subj.get('duration',30), min_value=5, max_value=180, key=f"duration_{subj['id']}")
        subj['sessions_per_week'] = cols[2].number_input("Sessions/week", value=subj.get('sessions_per_week',1), min_value=1, max_value=10, key=f"sessions_{subj['id']}")
        kid_options = [k["id"] for k in st.session_state["kids"]]
        subj['kids'] = cols[3].multiselect("Assign to kids", options=kid_options, default=subj.get('kids', []),
                                           format_func=lambda kid_id: next(k['name'] for k in st.session_state["kids"] if k['id']==kid_id),
                                           key=f"assign_{subj['id']}")
    if st.button("Add Subject"):
        st.session_state["subjects"].append({"id": f"subj_{len(st.session_state['subjects'])+1}", "name":"", "duration":30, "sessions_per_week":1, "kids":[]})

# -------------------------
# Lessons tab
# -------------------------
with tabs[2]:
    st.header("Add Lessons")
    if st.session_state["kids"] and st.session_state["subjects"]:
        with st.form("lesson_form", clear_on_submit=True):
            title = st.text_input("Title", key="lesson_title")
            text = st.text_area("Notes", key="lesson_text")
            subject = st.selectbox("Subject", st.session_state["subjects"], format_func=lambda s: s["name"], key="lesson_subject")
            kid = st.selectbox("Kid (optional)", [None]+st.session_state["kids"], format_func=lambda k: k["name"] if k else "Any", key="lesson_kid")
            submit = st.form_submit_button("Add Lesson")
            if submit:
                kid_id = kid["id"] if kid else None
                add_lesson(title, text, subject["id"], kid_id)
                st.success(f"Lesson '{title}' added!")

# -------------------------
# Commitments tab
# -------------------------
with tabs[3]:
    st.header("Add Fixed Commitments")
    if st.session_state["kids"]:
        with st.form("commit_form", clear_on_submit=True):
            kid = st.selectbox("Kid", st.session_state["kids"], format_func=lambda k: k["name"], key="commit_kid")
            day = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"], key="commit_day")
            start = st.text_input("Start Time (HH:MM)", "08:00", key="commit_start")
            end = st.text_input("End Time (HH:MM)", "09:00", key="commit_end")
            desc = st.text_input("Description", key="commit_desc")
            submit = st.form_submit_button("Add Commitment")
            if submit:
                add_commitment(kid["id"], day, start, end, desc)
                st.success(f"Commitment '{desc}' added!")

# -------------------------
# Smart Search tab
# -------------------------
with tabs[4]:
    st.header("Search Lessons & Books")
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
# Weekly Calendar tab
# -------------------------
with tabs[5]:
    st.header("Weekly Schedule")
    df_calendar = generate_weekly_schedule()
    if not df_calendar.empty:
        fig = px.timeline(df_calendar, x_start="Start", x_end="End", y="Day", color="Kid", text="Event")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add kids, subjects, and commitments to generate schedule.")
