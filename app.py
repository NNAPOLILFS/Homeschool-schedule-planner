# meal_planner_weekly.py

import streamlit as st
import random
import pandas as pd

# -------------------------------
# Helper functions
# -------------------------------

def generate_meal_options(preferences, meals_per_day):
    """
    Generate meal ideas for each day based on user preferences.
    Here we simulate AI-generated suggestions.
    """
    proteins = preferences if preferences else ["Chicken", "Beef", "Vegetarian", "Pork", "Fish"]
    
    # Sample meals per protein
    sample_meals = {
        "Chicken": ["Grilled Chicken Salad", "Chicken Stir Fry", "Baked Chicken with Veggies"],
        "Beef": ["Beef Tacos", "Beef Stir Fry", "Roast Beef with Potatoes"],
        "Vegetarian": ["Veggie Curry", "Pasta Primavera", "Stuffed Peppers"],
        "Pork": ["Pork Schnitzel", "Pulled Pork Sandwich", "Pork Stir Fry"],
        "Fish": ["Grilled Salmon", "Fish Tacos", "Fish & Veggie Bake"]
    }

    weekly_meals = {day: [] for day in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]}
    
    for day in weekly_meals:
        for _ in range(meals_per_day):
            protein = random.choice(proteins)
            meal = random.choice(sample_meals[protein])
            weekly_meals[day].append(meal)
    
    return weekly_meals

def display_weekly_plan(weekly_meals, meals_per_day):
    """
    Convert weekly meals dict into a DataFrame for table display.
    """
    meal_times = [f"Meal {i+1}" for i in range(meals_per_day)]
    df = pd.DataFrame(index=meal_times)
    
    for day, meals in weekly_meals.items():
        df[day] = meals
    return df

# -------------------------------
# Streamlit App
# -------------------------------

st.set_page_config(page_title="Weekly Meal Planner", layout="wide")
st.title("Weekly Meal Rotation Planner")

# Sidebar inputs
st.sidebar.header("Planner Options")
meals_per_day = st.sidebar.slider("Meals per day", min_value=1, max_value=5, value=3)
preferences = st.sidebar.multiselect(
    "Protein/Diet Preferences (leave blank for all)", 
    ["Chicken", "Beef", "Pork", "Fish", "Vegetarian"]
)

# Generate meals button
if st.sidebar.button("Generate Weekly Plan"):
    weekly_meals = generate_meal_options(preferences, meals_per_day)
    df_plan = display_weekly_plan(weekly_meals, meals_per_day)
    
    st.subheader("Your Weekly Meal Plan")
    st.table(df_plan)
    
    # Optional: download as CSV
    csv = df_plan.to_csv().encode('utf-8')
    st.download_button(
        label="Download Meal Plan as CSV",
        data=csv,
        file_name="weekly_meal_plan.csv",
        mime="text/csv",
    )
