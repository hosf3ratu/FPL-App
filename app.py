import streamlit as st
import pandas as pd
from fpl_api import FPLApi
from data_processor import DataProcessor

# Initialize session state
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'all_players'
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

# Position mapping
POSITIONS = {
    1: "Goalkeeper",
    2: "Defender",
    3: "Midfielder",
    4: "Forward"
}

# Initialize API and processor
@st.cache_resource
def get_data_processor():
    return DataProcessor(FPLApi())

def authenticate_user():
    """Handle FPL authentication"""
    with st.sidebar.expander("FPL Login (required for My Team view)"):
        st.info("Login with your Fantasy Premier League credentials")
        email = st.text_input("FPL Email", type="default", key="fpl_email")
        password = st.text_input("FPL Password", type="password", key="fpl_password")

        if st.button("Login"):
            with st.spinner("Logging in..."):
                try:
                    data_processor = get_data_processor()
                    if data_processor.fpl_api.login(email, password):
                        st.session_state.is_authenticated = True
                        st.success("Successfully logged in!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
                    st.info("Please make sure your credentials are correct and try again.")

def display_all_players(data_processor):
    st.header("All Players Statistics")

    try:
        with st.spinner("Loading player data..."):
            df = data_processor.get_players_with_points()

            # Map position numbers to names
            df['Position'] = df['Position'].map(POSITIONS)

            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                min_price = st.number_input("Minimum Price", 0.0, 20.0, 0.0)
            with col2:
                min_points = st.number_input("Minimum Total Points", 0, 500, 0)
            with col3:
                selected_position = st.selectbox(
                    "Filter by Position",
                    ["All"] + list(POSITIONS.values())
                )

            # Calculate total expected points
            df['Total Expected Points'] = df['Last 5 Games'] + df['Predicted Points']
            
            # Filter dataframe
            filtered_df = df[
                (df['Price'] >= min_price) &
                (df['Total Points'] >= min_points)
            ]

            # Apply position filter if not "All"
            if selected_position != "All":
                filtered_df = filtered_df[filtered_df['Position'] == selected_position]

            # Display sortable table
            st.dataframe(
                filtered_df,
                column_config={
                    "Price": st.column_config.NumberColumn(format="£%.1f"),
                    "Last 5 Games": st.column_config.NumberColumn(format="%d"),
                    "Last 3 Games": st.column_config.NumberColumn(format="%d"),
                    "Last Game": st.column_config.NumberColumn(format="%d"),
                    "Predicted Points": st.column_config.NumberColumn(format="%.1f"),
                    "Total Expected Points": st.column_config.NumberColumn(format="%.1f"),
                },
                hide_index=True
            )

    except Exception as e:
        st.error(f"Error loading player data: {str(e)}")

def display_my_team(data_processor):
    st.header("My Team")

    if not st.session_state.is_authenticated:
        st.warning("Please login using your FPL credentials in the sidebar to view your team data.")
        st.info("Click the 'FPL Login' expander in the sidebar to login.")
        return

    with st.expander("How to find your Team ID"):
        st.write("""
        1. Go to the 'Points' tab on the FPL website
        2. Look at the URL in your browser
        3. Your team ID is the number in the URL after '/entry/'
        Example: In 'fantasy.premierleague.com/entry/123456/event/1', your team ID is 123456
        """)

    team_id = st.text_input("Enter your team ID")
    if team_id:
        try:
            with st.spinner("Loading team data..."):
                team_df = data_processor.get_team_players(team_id)

                # Map position numbers to names
                team_df['Position'] = team_df['Position'].map(POSITIONS)

                st.dataframe(
                    team_df,
                    column_config={
                        "Last 5 Games": st.column_config.NumberColumn(format="%d"),
                        "Last 3 Games": st.column_config.NumberColumn(format="%d"),
                        "Last Game": st.column_config.NumberColumn(format="%d"),
                        "Predicted Points": st.column_config.NumberColumn(format="%.1f"),
                        "Total Expected Points": st.column_config.NumberColumn(format="%.1f"),
                    },
                    hide_index=True
                )
        except Exception as e:
            st.error("Failed to load team data. Please check your team ID and ensure you're logged in.")
            st.error(f"Error details: {str(e)}")

def display_player_comparison(data_processor):
    st.header("Player Comparison")
    
    try:
        with st.spinner("Loading player data..."):
            df = data_processor.get_players_with_points()
            df['Position'] = df['Position'].map(POSITIONS)
            
            # Player selection
            players_to_compare = st.multiselect(
                "Select players to compare",
                df['Name'].tolist(),
                max_selections=5
            )
            
            if players_to_compare:
                comparison_df = df[df['Name'].isin(players_to_compare)]
                
                # Display comparison table
                st.dataframe(
                    comparison_df,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="£%.1f"),
                        "Last 5 Games": st.column_config.NumberColumn(format="%d"),
                        "Last 3 Games": st.column_config.NumberColumn(format="%d"),
                        "Last Game": st.column_config.NumberColumn(format="%d"),
                        "Predicted Points": st.column_config.NumberColumn(format="%.1f"),
                    },
                    hide_index=True
                )
                
                # Bar charts for key metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(comparison_df.set_index('Name')['Total Points'])
                    st.caption("Total Points Comparison")
                
                with col2:
                    st.bar_chart(comparison_df.set_index('Name')['Predicted Points'])
                    st.caption("Predicted Points Comparison")
                
    except Exception as e:
        st.error(f"Error loading comparison data: {str(e)}")

def main():
    st.title("Fantasy Premier League Statistics")

    # Authentication in sidebar
    authenticate_user()

    # Navigation
    st.sidebar.title("Navigation")
    view = st.sidebar.radio(
        "Select View",
        ["All Players", "Player Comparison", "My Team"],
        key="nav"
    )

    data_processor = get_data_processor()

    if view == "All Players":
        display_all_players(data_processor)
    elif view == "Player Comparison":
        display_player_comparison(data_processor)
    else:
        display_my_team(data_processor)

if __name__ == "__main__":
    main()