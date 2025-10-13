"""
Homeschool Planner - Version 0.5.a
Changes:
- Added weekday/weekend toggles in the sidebar
- Users can include/exclude Monday-Friday, Saturday, Sunday in the schedule
- Preserves all previous functionality from v0.3:
    - Children names input
    - Subject management per child
    - Shared tick boxes
    - Fixed commitments
    - Autofill button
    - Full schedule generation from start to 5 PM
"""

import streamlit as st

# --- Helper Functions ---
def generate_schedule(subject_dict, start_hour, end_hour, fixed_commitments):
    """
    Generate a simple hourly schedule for a day.
    Fixed commitments are placed at their hour, remaining subjects fill other hours.
    Returns a dict {hour: (subject, shared_flag)}.
    """
