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
# OpenAI setup (new SDK syntax)
# -------------------------
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
except Exception:
    client = None

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"  # fast + free-tier friendly
DEFAULT_TOP_K = 6

# -------------------------
# Helper: get/set API key
# -------------------------
def ensure_openai_key():
    global client
    sidebar_key = st.sidebar.text_input("🔑 OpenAI API key (optional)", type="password")
    if sidebar_key:
        os.environ["OPENAI_API_KEY"] = sidebar_key
        client = OpenAI(api_key=sidebar_key)
    if not os.getenv("OPENAI_API_KEY"):
        st.sidebar.info("App still works without AI — but smart search & explanations need a key.")
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
