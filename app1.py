import streamlit as st
import requests
import random

# --- CONFIG ---
st.set_page_config(page_title="Homeschool Lesson Planner", page_icon="📚", layout="wide")

# --- Helper Data ---
HOMESCHOOL_APPROACHES = [
    "Charlotte Mason", "Montessori", "Classical", "Unschooling",
    "Eclectic", "Unit Studies", "Waldorf", "Reggio Emilia",
    "Traditional School-at-Home", "Project-Based Learning"
]

SUBJECTS = [
    "Math", "English", "Science", "History", "Geography",
    "Art", "Music", "Physical Education", "Nature Study"
]

# --- Google API Info (replace with your credentials if using) ---
API_KEY = "YOUR_GOOGLE_API_KEY"
SEARCH_ENGINE_ID = "YOUR_SEARCH_ENGINE_ID"

def fetch_resources(query, max_results=5):
    """Try Google API first, then DuckDuckGo as fallback."""
    try:
        url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
        )
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = [
                {"title": item["title"], "link": item["link"]}
                for item in data.get("items", [])
            ]
            return results[:max_results]
    except Exception:
        pass  # fallback if no key or API fails

    # --- Fallback to DuckDuckGo ---
    duck_url = f"https://api.duckduckgo.com/?q={query}&format=json"
    ddg = requests.get(duck_url).json()
    related = ddg.get("RelatedTopics", [])
    results = []
    for r in related[:max_results]:
        if "Text" in r and "FirstURL" in r:
            results.append({"title": r["Text"], "link": r["FirstURL"]})
    return results

# --- UI ---
st.title("📚 Homeschool Lesson Plan Generator")

col1, col2, col3 = st.columns(3)
with col1:
    approach = st.selectbox("Choose your homeschool approach:", HOMESCHOOL_APPROACHES)
with col2:
    age = st.selectbox("Select age or year level:", ["Preschool", "Early Primary", "Upper Primary", "Middle School"])
with col3:
    num_kids = st.number_input("Number of children:", min_value=1, max_value=10, step=1)

if st.button("Generate Lesson Plan"):
    st.subheader(f"✨ Weekly Lesson Plan for {approach} ({age}, {num_kids} kid{'s' if num_kids>1 else ''})")

    random_subjects = random.sample(SUBJECTS, k=min(5, len(SUBJECTS)))

    for subject in random_subjects:
        st.markdown(f"### 📘 {subject}")
        query = f"{approach} homeschool {subject} lessons for {age}"
        resources = fetch_resources(query)

        if not resources:
            st.info("No resources found, try a different approach or subject.")
        else:
            for r in resources:
                st.markdown(f"- [{r['title']}]({r['link']})")

    st.success("Lesson plan generated!")

st.caption("💡 Tip: Try switching approaches to see how your subjects and links change.")
