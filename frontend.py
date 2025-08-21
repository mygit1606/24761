# frontend.py

import streamlit as st
import pandas as pd
import backend as be
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Personal Fitness Tracker", layout="wide")
MAIN_USER_ID = 1 # The application is designed for a single main user (user_id=1)

def main():
    # --- INITIALIZATION ---
    be.initialize_database()
    # On first run, add some sample data to showcase features
    if 'seeded' not in st.session_state:
        be.seed_data()
        st.session_state['seeded'] = True

    # --- FETCH USER'S NAME FOR PERSONALIZED GREETING ---
    user_profile = be.get_user_profile(MAIN_USER_ID)
    # Get the first name for a friendly greeting
    user_name = user_profile[0].split()[0] if user_profile else "User"

    # --- UPDATED PERSONALIZED TITLE ---
    st.title(f"Hi {user_name}! 👋")
    st.subheader("Welcome to your Personal Fitness Tracker")

    # --- SIDEBAR NAVIGATION ---
    menu = ["My Profile", "Log a New Workout", "My Progress", "Friends & Leaderboard", "Set a Goal", "Business Insights"]
    choice = st.sidebar.selectbox("Menu", menu)
    st.sidebar.markdown("---")
    st.sidebar.info(f"Logged in as: {user_profile[0] if user_profile else 'User'}")

    # --- PAGE ROUTING ---
    if choice == "My Profile":
        profile_page()
    elif choice == "Log a New Workout":
        log_workout_page()
    elif choice == "My Progress":
        progress_page()
    elif choice == "Friends & Leaderboard":
        friends_leaderboard_page()
    elif choice == "Set a Goal":
        goal_page()
    elif choice == "Business Insights":
        insights_page()

# --- UI PAGES ---
def profile_page():
    st.header("👤 My Profile")
    user_data = be.get_user_profile(MAIN_USER_ID)
    if user_data:
        with st.form("update_profile_form"):
            st.write("Update your personal information below.")
            name = st.text_input("Name", value=user_data[0])
            email = st.text_input("Email", value=user_data[1])
            weight = st.number_input("Weight (kg)", value=float(user_data[2]), format="%.2f")
            
            submitted = st.form_submit_button("Update Profile")
            if submitted:
                be.update_user_profile(MAIN_USER_ID, name, email, weight)
                st.success("Profile updated successfully!")
                st.rerun()

def log_workout_page():
    st.header("🏋️ Log a New Workout")

    # Initialize session state for exercises if it doesn't exist
    if 'exercises' not in st.session_state:
        st.session_state.exercises = [{'name': '', 'sets': 3, 'reps': 10, 'weight': 20.0}]

    with st.form("log_workout_form"):
        st.write("Fill in the details of your workout session.")
        date = st.date_input("Workout Date", datetime.today())
        duration = st.number_input("Duration (minutes)", min_value=1, step=1)
        
        st.markdown("---")
        st.subheader("Exercises")

        # Dynamically render exercise input fields based on session state
        for i, ex in enumerate(st.session_state.exercises):
            cols = st.columns([3, 1, 1, 1])
            ex['name'] = cols[0].text_input(f"Exercise Name", value=ex.get('name', ''), key=f"name_{i}")
            ex['sets'] = cols[1].number_input(f"Sets", min_value=1, step=1, value=ex.get('sets', 3), key=f"sets_{i}")
            ex['reps'] = cols[2].number_input(f"Reps", min_value=1, step=1, value=ex.get('reps', 10), key=f"reps_{i}")
            ex['weight'] = cols[3].number_input(f"Weight (kg)", min_value=0.0, step=0.5, format="%.1f", value=ex.get('weight', 20.0), key=f"weight_{i}")

        # The one and only submit button for the form
        submitted = st.form_submit_button("Log Workout")
        if submitted:
            # Filter out empty exercise names before logging
            valid_exercises = [ex for ex in st.session_state.exercises if ex['name'].strip()]
            if not valid_exercises:
                st.warning("Please add at least one exercise.")
            else:
                be.log_workout(MAIN_USER_ID, date, duration, valid_exercises)
                st.success("Workout logged successfully!")
                # Clean up session state for the next entry
                del st.session_state.exercises 
                st.rerun()

    # --- "Add Another Exercise" button is now OUTSIDE the form ---
    if st.button("Add Another Exercise"):
        # Add a new placeholder dictionary to the list in session state
        st.session_state.exercises.append({'name': '', 'sets': 3, 'reps': 10, 'weight': 20.0})
        st.rerun()

def progress_page():
    st.header("📈 My Progress")
    workouts = be.get_user_workouts(MAIN_USER_ID)

    if not workouts:
        st.info("You haven't logged any workouts yet. Go to 'Log a New Workout' to get started!")
        return

    df_workouts = pd.DataFrame(workouts, columns=['ID', 'Date', 'Duration (min)'])
    st.write("Your Workout History:")
    st.dataframe(df_workouts, use_container_width=True, hide_index=True)

    # Visualize progress over time
    if not df_workouts.empty:
        st.subheader("Workout Duration Over Time")
        chart_data = df_workouts.rename(columns={'Date': 'index'}).set_index('index')
        st.line_chart(chart_data['Duration (min)'])

    st.subheader("Workout Details")
    selected_id = st.selectbox("Select a workout to see details:", options=df_workouts['ID'], format_func=lambda x: f"Workout on {df_workouts[df_workouts['ID']==x]['Date'].iloc[0]}")
    if selected_id:
        details = be.get_workout_details(selected_id)
        df_details = pd.DataFrame(details, columns=['Exercise', 'Sets', 'Reps', 'Weight (kg)'])
        st.table(df_details)

def friends_leaderboard_page():
    st.header("🤝 Friends & Leaderboard")
    
    tab1, tab2 = st.tabs(["Leaderboard", "Manage Friends"])

    with tab1:
        st.subheader("🏆 Weekly Leaderboard")
        st.write("Ranking based on total workout minutes for the current week.")
        leaderboard_data = be.get_leaderboard()
        if leaderboard_data:
            df_leaderboard = pd.DataFrame(leaderboard_data, columns=['Name', 'Total Minutes'])
            st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
        else:
            st.info("No workouts logged by anyone this week.")
    
    with tab2:
        st.subheader("Manage Your Friends")
        current_friends = be.get_friends(MAIN_USER_ID)
        friend_ids = [f[0] for f in current_friends]
        
        st.write("Your current friends:")
        if not current_friends:
            st.info("You haven't added any friends yet.")
        else:
            for friend_id, friend_name in current_friends:
                col1, col2 = st.columns([4, 1])
                col1.write(f"- {friend_name}")
                if col2.button("Remove", key=f"remove_{friend_id}"):
                    be.remove_friend(MAIN_USER_ID, friend_id)
                    st.success(f"Removed {friend_name} from your friends.")
                    st.rerun()
        
        st.markdown("---")
        st.write("Add a new friend:")
        all_users = be.get_all_users(exclude_user_id=MAIN_USER_ID)
        # Filter out users who are already friends
        potential_friends = [user for user in all_users if user[0] not in friend_ids]
        
        if not potential_friends:
            st.warning("No new users to add as friends.")
        else:
            friend_to_add_id = st.selectbox("Select a user to add:", options=[u[0] for u in potential_friends], format_func=lambda x: [u[1] for u in potential_friends if u[0] == x][0])
            if st.button("Add Friend"):
                be.add_friend(MAIN_USER_ID, friend_to_add_id)
                st.success("Friend added successfully!")
                st.rerun()

def goal_page():
    st.header("🎯 Set a Goal")
    
    active_goal = be.get_active_goal(MAIN_USER_ID)
    if active_goal:
        st.success(f"Your current goal: **{active_goal[0]}** (Target: {active_goal[1]} workouts per week)")
        workouts_this_week = pd.DataFrame(be.get_leaderboard(), columns=['Name', 'Minutes'])
        user_name = be.get_user_profile(MAIN_USER_ID)[0]
        # This is a simplification; a more robust goal tracker would be needed
        # for more complex goals. For "workouts per week", we can count them.
        st.info("Goal progress tracking can be expanded here based on goal type.")
    
    with st.form("set_goal_form"):
        st.write("Set a new weekly workout goal. This will replace your current one.")
        description = st.text_input("Goal Description", "Workout 5 times a week")
        target_value = st.number_input("How many workouts per week?", min_value=1, value=5, step=1)
        
        if st.form_submit_button("Set New Goal"):
            be.set_goal(MAIN_USER_ID, description, target_value)
            st.success("New goal set!")
            st.rerun()

def insights_page():
    st.header("📊 Business Insights")
    st.info("Here are some key performance indicators based on your activity.")
    
    stats = be.get_workout_statistics(MAIN_USER_ID)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Workouts Logged", f"{stats.get('total_workouts', 0)}")
    col2.metric("Total Workout Time", f"{stats.get('total_duration', 0)} min")
    col3.metric("Avg. Workout Duration", f"{stats.get('avg_duration', 0)} min")
    
    st.markdown("---")
    st.subheader("Exercise Specific Insights")
    col1, col2 = st.columns(2)
    col1.metric("Min Weight (Bench Press)", f"{stats.get('min_bench_press', 0)} kg")
    col2.metric("Max Weight (Bench Press)", f"{stats.get('max_bench_press', 0)} kg")
    st.caption("Note: Weight insights are shown for 'Bench Press' as an example.")

if __name__ == "__main__":
    main()