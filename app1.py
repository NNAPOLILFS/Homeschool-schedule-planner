# app_v1_3.py
"""
Streamlit homeschool planner v1.3
- In-memory "lessons/resources" store (no DB required yet)
- Smart Semantic Search (OpenLibrary + optional YouTube + local lessons)
- Schedule generation logic (v0.6b-inspired)
- Uses OpenAI embeddings and chat for explanations (set OPENAI_API_KEY)
"""

import os
import time
from typing import List, Dict, Tuple
import streamlit as st
import requests
import numpy as np

# Optional: try to import faiss, but code works without it (fallback dot-product)
try:
    import faiss
except Exception:
    faiss = None

# OpenAI
import openai

# -------------------------
# Config & models
# -------------------------
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-3.5-turbo"
DEFAULT_TOP_K = 6

# -------------------------
# Helper utilities
# -------------------------
def set_openai_key_from_env_or_input():
    # Prefer environment variable; allow letting user paste key into sidebar
    key = os.getenv("OPENAI_API_KEY", "")
    typed = st.sidebar.text_input("OPENAI_API_KEY (paste here to set for session)", type="password", value="")
    if typed:
        key = typed
    if not key:
        st.sidebar.warning("Set OPENAI_API_KEY (required for embeddings/explanations).")
    openai.api_key = key
    return bool(key)

def require_openai_key_or_stop():
    if not openai.api_key:
        st.error("OpenAI API key is missing. Add it in the sidebar or as env var OPENAI_API_KEY.")
        st.stop()

# -------------------------
# Simple in-memory data store (session_state)
# -------------------------
def init_store():
    if "lessons" not in st.session_state:
        st.session_state["lessons"] = []  # each lesson: dict id,title,content,subject,estimated_minutes
    if "embeddings_cache" not in st.session_state:
        # mapping id -> embedding vector (numpy array)
        st.session_state["embeddings_cache"] = {}
    if "last_index_build" not in st.session_state:
        st.session_state["last_index_build"] = None

init_store()

def add_lesson(title: str, content: str, subject: str, minutes: int):
    doc_id = f"local_{len(st.session_state['lessons'])+1}"
    item = {"id": doc_id, "title": title, "content": content, "subject": subject, "minutes": minutes}
    st.session_state["lessons"].append(item)
    return item

# -------------------------
# External fetchers
# -------------------------
def fetch_openlibrary(query: str, limit: int = 6) -> List[Dict]:
    url = "https://openlibrary.org/search.json"
    try:
        r = requests.get(url, params={"q": query, "limit": limit}, timeout=10)
        data = r.json()
    except Exception:
        return []
    items = []
    for doc in data.get("docs", [])[:limit]:
        title = doc.get("title", "Untitled")
        authors = doc.get("author_name", [])
        year = doc.get("first_publish_year", "")
        snippet = doc.get("first_sentence") or doc.get("subtitle") or ""
        text = f"{title} by {', '.join(authors)}. First published {year}. {snippet}"
        items.append({"id": f"ol_{doc.get('key')}", "title": title, "source": "OpenLibrary",
                      "url": f"https://openlibrary.org{doc.get('key')}" if doc.get("key") else "",
                      "text": text})
    return items

def fetch_youtube(query: str, api_key: str, limit: int = 6) -> List[Dict]:
    if not api_key:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    try:
        r = requests.get(url, params={"part":"snippet","q":query,"type":"video","maxResults":limit,"key":api_key}, timeout=10)
        data = r.json()
    except Exception:
        return []
    items = []
    for it in data.get("items", [])[:limit]:
        snip = it["snippet"]
        title = snip.get("title")
        desc = snip.get("description","")
        vid = it["id"]["videoId"]
        text = f"{title}. {desc}"
        items.append({"id": f"yt_{vid}", "title": title, "source":"YouTube", "url": f"https://youtu.be/{vid}", "text": text})
    return items

# -------------------------
# Embedding helpers + cachin
