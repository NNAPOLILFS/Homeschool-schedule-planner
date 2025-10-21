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

def semantic_search(query, items, top_k=DEFAULT_TOP_K):
    if not items:
        return []
    q_emb = get_embedding(query)
    all_vecs = [
        st.session_state["embeddings_cache"].get(it["id"], get_embedding(it["text"]))
        for it in items
    ]
    # Cache embeddings
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
