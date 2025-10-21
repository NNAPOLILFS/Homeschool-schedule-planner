# app_v1_4.py
"""
Streamlit Homeschool Planner v1.4 (robust, free)
- In-memory lesson store
- Free semantic search (TF-IDF) + OpenLibrary
- Schedule generator
- No API keys required
"""

import streamlit as st
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -------------------------
# Session store
# -------------------------
def init_store():
    if "lessons" not in st.session_state:
        st.session_state["lessons"] = []

init_store()

def add_lesson(title, text, subject, minutes):
    if not text:
        text = ""
    if not title:
        title = "Untitled"
    if minutes is None or minutes <= 0:
        minutes = 30
    doc_id = f"local_{len(st.session_state['lessons']) + 1}"
    lesson = {"id": doc_id, "title": title, "text": text, "subject": subject, "minutes": minutes}
    st.session_state["lessons"].append(lesson)
    return lesson

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
# TF-IDF search
# -------------------------
def local_semantic_search(query, lessons, top_k=6):
    if not lessons or not query.strip():
        return []
    texts = [l.get("text", "") for l in lessons]
    vectorizer = TfidfVectorizer().fit(texts + [query])
    text_vectors = vectorizer.transform(texts)
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, text_vectors)[0]
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [lessons[i] for i in top_idx]

# -------------------------
# Schedule generator
# -------------------------
def generate_schedule(lessons, available_minutes=120):
    schedule = []
    total = 0
    for l in lessons:
        if l.get("minutes") and total + l["minutes"] <= available_minutes:
            schedule.append(l)
            total += l["minutes"]
    return schedule

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🎓 Homeschool Planner v1.4 (Free TF-IDF + OpenLibrary)")

tabs = st.tabs(["📚 Add Lesson", "🔍 Smart Search", "🗓️ Generate Schedule"])

# -------------------------
# Add Lesson Tab
# -------------------------
with tabs[0]:
    st.header("Add a Lesson")
    with st.form("add_lesson_form"):
        title = st.text_input("Title")
        text = st.text_area("Content / Notes")
        subject = st.text_input("Subject")
        minutes = st.number_input("Estimated Minutes", min_value=10, max_value=180, value=30)
        submitted = st.form_submit_button("Add Lesson")
        if submitted:
            lesson = add_lesson(title, text, subject, minutes)
            st.success(f"Added lesson: {lesson['title']}")

# -------------------------
# Smart Search Tab
# -------------------------
with tabs[1]:
    st.header("Smart Search")
    query = st.text_input("Enter topic or lesson keyword")
    if query.strip():
        local_items = [{"id": l["id"], "title": l["title"], "text": l["text"], "source": "Local", "url": ""} 
                       for l in st.session_state["lessons"]]
        ranked_local = local_semantic_search(query, local_items, top_k=6)
        ol_items = fetch_openlibrary(query)
        results = ranked_local + ol_items

        if not results:
            st.info("No results found. Try adding lessons or searching a different topic.")
        else:
            st.subheader(f"Top results for '{query}'")
            for r in results:
                st.markdown(f"**{r['title']}** ({r['source']})  \n{r['text'][:150]}...")
                if r.get("url"):
                    st.markdown(f"[View more]({r['url']})")

# -------------------------
# Generate Schedule Tab
# -------------------------
with tabs[2]:
    st.header("Generate a Schedule")
    if not st.session_state["lessons"]:
        st.info("Add some lessons first!")
    else:
        mins = st.slider("Available time (minutes)", min_value=30, max_value=300, value=120, step=15)
        plan = generate_schedule(st.session_state["lessons"], mins)
        if not plan:
            st.info("No lessons fit in the selected time. Try adding shorter lessons.")
        else:
            st.subheader("Suggested Plan")
            for p in plan:
                st.markdown(f"- **{p['title']}** ({p['minutes']} min) — {p['subject']}")
