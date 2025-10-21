# app_v1_3_fixed.py
"""
Streamlit Homeschool Planner v1.3 (fixed)
- In-memory store (no DB yet)
- Smart AI Search (OpenLibrary + optional YouTube)
- Schedule generator logic (v0.6b-inspired)
- Uses OpenAI new SDK syntax with fallback for missing key
"""

import os
import time
from typing import List, Dict
import streamlit as st
import requests
import numpy as np

# Optional FAISS for vector search
try:
    import faiss
except Exception:
    faiss = None

# -------------------------
# Config / Constants
# -------------------------
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"  # fast + free-tier friendly
DEFAULT_TOP_K = 6  # must be defined before functions

# -------------------------
# OpenAI setup (new SDK)
# -------------------------
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
except Exception:
    client = None

# -------------------------
# Helper: get/set API key
# -------------------------
def ensure_openai_key():
    global client
    sidebar_key = st.sidebar.text_input("🔑 OpenAI API key (optional)", type="password")
    if sidebar_key:
        os.environ["OPENAI_API_KEY"] = sidebar_key
        try:
            client = OpenAI(api_key=sidebar_key)
        except Exception:
            client = None
    if not os.getenv("OPENAI_API_KEY"):
        st.sidebar.info("App still works without AI — smart search & explanations require a key.")
    return client is not None

# -------------------------
# Session store
# -------------------------
def init_store():
    if "lessons" not in st.session_state:
        st.session_state["lessons"] = []
    if "embeddings_cache" not in st.session_state:
        st.session_state["embeddings_cache"] = {}

init_store()

def add_lesson(title, content, subject, minutes):
    doc_id = f"local_{len(st.session_state['lessons']) + 1}"
    item = {"id": doc_id, "title": title, "content": content, "subject": subject, "minutes": minutes}
    st.session_state["lessons"].append(item)
    return item

# -------------------------
# External fetchers
# -------------------------
def fetch_openlibrary(query, limit=6):
    url = "https://openlibrary.org/search.json"
    try:
        r = requests.get(url, params={"q": query, "limit": limit}, timeout=10)
        data = r.json()
    except Exception:
        return []
    items = []
    for doc in data.get("docs", [])[:limit]:
        title = doc.get("title", "Untitled")
        authors = ", ".join(doc.get("author_name", []) or [])
        year = doc.get("first_publish_year", "")
        snippet = doc.get("first_sentence") or doc.get("subtitle") or ""
        text = f"{title} by {authors}. Published {year}. {snippet}"
        items.append({
            "id": f"ol_{doc.get('key')}",
            "title": title,
            "source": "OpenLibrary",
            "url": f"https://openlibrary.org{doc.get('key')}" if doc.get("key") else "",
            "text": text
        })
    return items

def fetch_youtube(query, api_key, limit=6):
    if not api_key:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    try:
        r = requests.get(url, params={"part": "snippet", "q": query, "type": "video",
                                      "maxResults": limit, "key": api_key}, timeout=10)
        data = r.json()
    except Exception:
        return []
    items = []
    for it in data.get("items", [])[:limit]:
        snip = it["snippet"]
        title = snip.get("title", "")
        desc = snip.get("description", "")
        vid = it["id"]["videoId"]
        text = f"{title}. {desc}"
        items.append({
            "id": f"yt_{vid}",
            "title": title,
            "source": "YouTube",
            "url": f"https://youtu.be/{vid}",
            "text": text
        })
    return items

# -------------------------
# Embeddings & semantic similarity
# -------------------------
def get_embedding(text: str):
    if not client:
        return np.zeros(1536, dtype=np.float32)
    try:
        resp = client.embeddings.create(model=EMBED_MODEL, input=text)
        return np.array(resp.data[0].embedding, dtype=np.float32)
    except Exception:
        return np.zeros(1536, dtype=np.float32)

def semantic_search(query, items, top_k=None):
    if top_k is None:
        top_k = DEFAULT_TOP_K
    if not items:
        return []
    q_emb = get_embedding(query)
    all_vecs = [
        st.session_state["embeddings_cache"].get(it["id"], get_embedding(it["text"]))
        for it in items
    ]
    for i, it in enumerate(items):
        st.session_state["embeddings_cache"][it["id"]] = all_vecs[i]
    mat = np.vstack(all_vecs)
    scores = np.dot(mat, q_emb)
    top_idx = np.argsort(scores)[::-1][:top_k]
    return [items[i] for i in top_idx]

# -------------------------
# Schedule generator logic (v0.6b-inspired)
# -------------------------
def generate_schedule(lessons, available_minutes=120):
    schedule = []
    total = 0
    for l in lessons:
        if total + l["minutes"] <= available_minutes:
            schedule.append(l)
            total += l["minutes"]
    return schedule

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Homeschool Planner", layout="wide")
st.title("🎓 Homeschool Planner v1.3")

ensure_openai_key()

tabs = st.tabs(["📚 Add Lesson", "🔍 Smart Search", "🗓️ Generate Schedule"])

with tabs[0]:
    st.header("Add a Lesson")
    with st.form("add_lesson_form"):
        title = st.text_input("Title")
        content = st.text_area("Content / Notes")
        subject = st.text_input("Subject")
        minutes = st.number_input("Estimated Minutes", 10, 120, 30)
        submitted = st.form_submit_button("Add Lesson")
        if submitted:
            item = add_lesson(title, content, subject, minutes)
            st.success(f"Added: {item['title']}")

with tabs[1]:
    st.header("Smart Search")
    query = st.text_input("Search your lessons + OpenLibrary", "")
    if query:
        local_items = [
            {"id": l["id"], "title": l["title"], "text": l["content"], "source": "Local"}
            for l in st.session_state["lessons"]
        ]
        ol_items = fetch_openlibrary(query)
        items = local_items + ol_items

        results = semantic_search(query, items)
        st.subheader(f"Top results for '{query}'")
        for r in results:
            st.markdown(f"**{r['title']}** ({r['source']})  \n{r['text'][:150]}...")
            if "url" in r and r["url"]:
                st.markdown(f"[View more]({r['url']})")

        # Optional AI explanation
        if client:
            with st.spinner("Generating AI explanation..."):
                try:
                    chat_resp = client.chat.completions.create(
                        model=CHAT_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a helpful homeschool planner assistant."},
                            {"role": "user", "content": f"Explain why these resources would help with '{query}'."}
                        ],
                    )
                    reply = chat_resp.choices[0].message.content
                    st.markdown("**AI Insight:** " + reply)
                except Exception:
                    st.info("AI explanation unavailable at the moment.")

with tabs[2]:
    st.header("Generate a Schedule")
    if not st.session_state["lessons"]:
        st.info("Add a few lessons first!")
    else:
        mins = st.slider("Available time (minutes)", 30, 300, 120, 15)
        plan = generate_schedule(st.session_state["lessons"], mins)
        st.subheader("Suggested Plan")
        for p in plan:
            st.markdown(f"- **{p['title']}** ({p['minutes']} min) — {p['subject']}")
