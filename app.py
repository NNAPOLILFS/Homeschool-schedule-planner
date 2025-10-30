import streamlit as st
import pandas as pd
from datetime import datetime
import json
from io import BytesIO

# Optional ReportLab imports for PDF export
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Streamlit app setup
st.set_page_config(page_title="Homeschool Planner", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS (fixed with raw string and all braces closed)
st.markdown(r"""
<style>
    .main { background-color: #F7FAFC; }
    .main-header {
        font-size: 3rem; font-weight: bold; color: #4A90E2;
        text-align: center; margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem; font-weight: 600; color: #2C3E50;
        margin-top: 2rem; margin-bottom: 1rem;
        border-bottom: 3px solid #4A90E2; padding-bottom: 0.5rem;
    }
    .info-box {
        background-color: #EBF8FF; padding: 20px;
        border-radius: 10px; border-left: 5px solid #4299E1;
        margin: 10px 0;
    }
    .success-box {
        background-color: #F0FFF4; padding: 20px;
        border-radius: 10px; border-left: 5px solid #48BB78;
        margin: 10px 0;
    }
    .stButton>button {
        border-radius: 10px; font-weight: 600;
        transition: all 0.3s;
    }
    .preview-container {
        background: white; padding: 20px;
        border-radius: 15px; margin-top: 20px;
        border: 2px dashed #CBD5E0;
    }
    /* Fixed problematic CSS area */
    .time-dot {
        position: absolute;
        left: -38px; /* safe negative value */
    }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

VALID_CODES = ['DEMO2024', 'TRIAL123']

if not st.session_state.authenticated:
    st.markdown('<div class="main-header">🏫 Homeschool Planner</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #2C3E50;">Welcome! 👋</h3>
            <p style="color: #4A5568;">Create beautiful, organized schedules for your homeschool family.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        access_code = st.text_input("🔑 Access Code", type="password", placeholder="Enter your code")

        if st.button("✨ Get Started", use_container_width=True):
            if access_code in VALID_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid code. [Get access here](https://buy.stripe.com/your-payment-link)")
    st.stop()

# --- EMOJI MAP ---
DEFAULT_EMOJI = {
    'math': '🔢', 'reading': '📖', 'writing': '✍️', 'science': '🔬',
    'history': '📜', 'geography': '🌍', 'art': '🎨', 'music': '🎵',
    'pe': '⚽', 'physical education': '⚽', 'spanish': '🇪🇸',
    'french': '🇫🇷', 'language': '💬', 'bible': '✝️', 'nature': '🌿',
    'coding': '💻', 'default': '📚'
}

def get_emoji_for_subject(subject_name):
    name_lower = subject_name.lower()
    for key in DEFAULT_EMOJI:
        if key in name_lower:
            return DEFAULT_EMOJI[key]
    return DEFAULT_EMOJI['default']

# --- SESSION STATE INITIALIZATION ---
if 'kids' not in st.session_state:
    st.session_state.kids = ['']
if 'subjects' not in st.session_state:
    st.session_state.subjects = [{'name': '', 'sessions': 3, 'duration': 60, 'kids': [], 'emoji': '📚'}]
if 'commitments' not in st.session_state:
    st.session_state.commitments = [{'day': 'Monday', 'time': '14:00', 'duration': 60, 'activity': '', 'kids': []}]
if 'generated_schedule' not in st.session_state:
    st.session_state.generated_schedule = None
if 'lesson_details' not in st.session_state:
    st.session_state.lesson_details = {}
# ✅ FIX 1: prevent AttributeError by initializing lesson_completion
if 'lesson_completion' not in st.session_state:
    st.session_state.lesson_completion = {}
if 'scheduling_warnings' not in st.session_state:
    st.session_state.scheduling_warnings = []
if 'saved_schedules' not in st.session_state:
    st.session_state.saved_schedules = {}
if 'current_schedule_name' not in st.session_state:
    st.session_state.current_schedule_name = ""
if 'show_preview' not in st.session_state:
    st.session_state.show_preview = False

# --- HEADER ---
st.markdown('<div class="main-header">🏫 Homeschool Planner</div>', unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📝 Setup & Preview", "📅 Weekly Schedule", "🖨️ Print View"])

# --- REST OF YOUR APP LOGIC ---
# (Your scheduling, preview, and export logic remain unchanged from your docx version.)
# Only the above sections required modification for the reported errors.
