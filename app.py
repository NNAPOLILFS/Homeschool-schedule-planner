# app_v1_5.py
"""
Streamlit Homeschool Planner v1.5
- Kids, Subjects, Lessons
- Fixed Commitments
- Weekly schedule generator with dynamic time blocks (default 30 min)
- Smart TF-IDF + OpenLibrary search
- Fully free; no API keys required
"""

import streamlit as st
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------
# Session store init
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
# Add entities
# -------------------------
def add_kid(name, age):
    kid_id = f"kid_{len(st.session_state['kids'])+1}"
    st.session_state["kids"].append({"id": kid_id, "name": name, "age": age})
    return kid_id

def add_subject(subject_name):
    if subject_name not in st.session_state["subjects"]:
        st.session_state["subjects"].append(subject_name)

def add_lesson(title, text, subject, minutes, kid_id=None):
    if not title:
        title = "Untitled"
    if not text:
        text = ""
    if not minutes or minutes <= 0:
        minutes = 30
    lesson_id = f"lesson_{len(st.session_state['lessons'])+1}"
    st.session_state["lessons"].append({
        "id": lesson_id, "title": title, "text": text,
        "subject": subject, "minutes": minutes, "kid_id": kid_id
    })
    return lesson_id

def add_commitment(kid_id, day, start, end, description):
    commit_id = f"commit_{len(st.session_state['commitments'])+1}"
    st.session_state["commitments"].append({
        "id": commit_id, "kid_id": kid_id, "day": day,
        "start": start, "end": end, "description": description
    })
    return commit_id

# -------------------------
# OpenLibrary fetcher
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
# TF-IDF semantic search
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
# Weekly schedule helper
# -------------------------
def create_time_blocks(start_hour=6, end_hour=18, block_minutes=30):
    times = []
    for h in range(start_hour, end_hour):
        for m in range(0, 60, block_minutes):
            times.append(f"{h:02d}:{m:02d}")
    return times

def generate_weekly_schedule(kid_id, start_hour=6, end_hour=18, block_minutes=30):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_blocks = create_time_blocks(start_hour, end_hour, block_minutes)
    grid = {day: {t: None for t in time_blocks} for day in days}

    # place fixed commitments
    for c in st.session_state["commitments"]:
        if c["kid_id"] != kid_id:
            continue
        for t in time_blocks:
            if c["start"] <= t < c["end"]:
                grid[c["day"]][t] = f"Fixed: {c['description']}"

    # place lessons
    lessons = [l for l in st.session_state["lessons"] if l.get("kid_id")==kid_id]
    for l in lessons:
        blocks_needed = max(1, l["minutes"] // block_minutes)
        placed = False
        for day in days:
            day_blocks = list(grid[day].items())
            for i in range(len(day_blocks) - blocks_needed + 1):
                if all(v is None for _, v in day_blocks[i:i+blocks_needed]):
                    for j, (t, _) in enumerate(day_blocks[i:i+blocks_needed]):
                        grid[day][t] = f"Lesson: {l['title']} ({l['subject']})"
                    placed = True
                    break
            if placed:
                break
    return grid

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Homeschool Planner v1.5", layout="wide")
st.title("🎓 Homeschool Planner v1.5")

tabs = st.tabs(["👶 Kids", "📚 Subjects", "➕ Lessons", "⏰ Commitments", "🔍 Smart Search", "🗓️ Weekly Schedule"])

# -------------------------
# Kids tab
# -------------------------
with tabs[0]:
    st.header("Manage Kids")
    with st.form("add_kid_form"):
        name = st.text_input("Kid's name")
        age = st.number_input("Age", min_value=3, max_value=18, value=7)
        submitted = st.form_submit_button("Add Kid")
        if submitted:
            kid_id = add_kid(name, age)
            st.success(f"Added kid: {name}")

    if st.session_state["kids"]:
        st.subheader("Current Kids")
        for k in st.session_state["kids"]:
            st.write(f"- {k['name']} ({k['age']} years)")

# -------------------------
# Subjects tab
# -------------------------
with tabs[1]:
    st.header("Manage Subjects")
    with st.form("add_subject_form"):
        subj = st.text_input("Subject name")
        submitted = st.form_submit_button("Add Subject")
        if submitted and subj.strip():
            add_subject(subj)
            st.success(f"Added subject: {subj}")

    if st.session_state["subjects"]:
        st.subheader("Current Subjects")
        st.write(", ".join(st.session_state["subjects"]))

# -------------------------
# Lessons tab
# -------------------------
with tabs[2]:
    st.header("Add Lesson")
    if not st.session_state["kids"]:
        st.info("Add at least one kid first!")
    elif not st.session_state["subjects"]:
        st.info("Add at least one subject first!")
    else:
        with st.form("add_lesson_form"):
            title = st.text_input("Title")
            text = st.text_area("Content / Notes")
            subject = st.selectbox("Subject", st.session_state["subjects"])
            kid = st.selectbox("Kid", st.session_state["kids"], format_func=lambda k: k["name"])
            minutes = st.number_input("Estimated Minutes", min_value=10, max_value=180, value=30)
            submitted = st.form_submit_button("Add Lesson")
            if submitted:
                add_lesson(title, text, subject, minutes, kid_id=kid["id"])
                st.success(f"Added lesson for {kid['name']}: {title}")

# -------------------------
# Commitments tab
# -------------------------
with tabs[3]:
    st.header("Add Fixed Commitment")
    if not st.session_state["kids"]:
        st.info("Add at least one kid first!")
    else:
        with st.form("add_commit_form"):
            kid = st.selectbox("Kid", st.session_state["kids"], format_func=lambda k: k["name"])
            day = st.selectbox("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday"])
            start = st.time_input("Start Time")
            end = st.time_input("End Time")
            desc = st.text_input("Description")
            submitted = st.form_submit_button("Add Commitment")
            if submitted and desc.strip():
                add_commitment(kid["id"], day, start.strftime("%H:%M"), end.strftime("%H:%M"), desc)
                st.success(f"Added commitment: {desc} for {kid['name']} on {day}")

# -------------------------
# Smart Search tab
# -------------------------
with tabs[4]:
    st.header("Smart Search for Lessons")
    query = st.text_input("Enter topic or keyword")
    if query.strip():
        local_items = [{"id": l["id"], "title": l["title"], "text": l["text"], "source": "Local", "url": ""} 
                       for l in st.session_state["lessons"]]
        ranked_local = local_semantic_search(query, local_items, top_k=6)
        ol_items = fetch_openlibrary(query)
        results = ranked_local + ol_items

        if not results:
            st.info("No results found.")
        else:
            st.subheader(f"Results for '{query}'")
            for r in results:
                st.markdown(f"**{r['title']}** ({r['source']})  \n{r['text'][:150]}...")
                if r.get("url"):
                    st.markdown(f"[View more]({r['url']})")

# -------------------------
# Weekly Schedule tab
# -------------------------
with tabs[5]:
    st.header("Weekly Schedule")
    if not st.session_state["kids"]:
        st.info("Add at least one kid first!")
    else:
        kid = st.selectbox("Select Kid", st.session_state["kids"], format_func=lambda k: k["name"])
        start_hour = st.number_input("Day Start Hour", min_value=0, max_value=12, value=6)
        end_hour = st.number_input("Day End Hour", min_value=12, max_value=24, value=18)
        block_minutes = st.number_input("Block Duration (min)", min_value=5, max_value=120, value=30)
        if st.button("Generate Schedule"):
            grid = generate_weekly_schedule(kid["id"], start_hour, end_hour, block_minutes)
            for day, slots in grid.items():
                st.subheader(day)
                for t, val in slots.items():
                    if val:
                        st.write(f"{t} → {val}")
