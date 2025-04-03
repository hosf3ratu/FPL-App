import pandas as pd
import numpy as np
from predicted_points_scraper import PredictedPointsScraper

class DataProcessor:
    def __init__(self, fpl_api):
        self.fpl_api = fpl_api
        self.players_df = None
        self.predicted_points_scraper = PredictedPointsScraper()
        self.load_players()

    def load_players(self):
        """Load and process all players data"""
        self.players_df = self.fpl_api.get_all_players()

    def calculate_player_points(self, player_id):
        """Calculate point aggregations for a player"""
        try:
            history = self.fpl_api.get_player_history(player_id)
            if history.empty:
                return 0, 0, 0

            # Sort by gameweek descending
            history = history.sort_values('round', ascending=False)

            last_1 = history.iloc[0]['total_points'] if len(history) >= 1 else 0
            last_3 = history.iloc[:3]['total_points'].sum() if len(history) >= 3 else history['total_points'].sum()
            last_5 = history.iloc[:5]['total_points'].sum() if len(history) >= 5 else history['total_points'].sum()

            return last_5, last_3, last_1
        except Exception:
            return 0, 0, 0

    def get_player_name_variations(self, player):
        """Generate different variations of a player's name for matching"""
        variations = []

        # Full name
        first_name = player['first_name'].strip()
        second_name = player['second_name'].strip()
        variations.append(f"{first_name} {second_name}")

        # Web name
        variations.append(player['web_name'].strip())

        # Last name only
        variations.append(second_name)

        # First initial + last name
        if first_name:
            variations.append(f"{first_name[0]}. {second_name}")

        # Remove duplicates and empty strings
        return list(set(var for var in variations if var))

    def get_players_with_points(self):
        """Get all players with their point aggregations"""
        if self.players_df is None:
            self.load_players()

        # Fetch predicted points
        predicted_points = self.predicted_points_scraper.fetch_predictions()
        print(f"Fetched {len(predicted_points)} predicted points")
        print("Sample of predicted points:")
        sample_items = list(predicted_points.items())[:5]
        for name, points in sample_items:
            print(f"  {name}: {points}")

        result_data = []
        for _, player in self.players_df.iterrows():
            last_5, last_3, last_1 = self.calculate_player_points(player['id'])

            # Try different name variations for matching
            predicted = 0.0
            name_variations = self.get_player_name_variations(player)

            for name in name_variations:
                if name in predicted_points:
                    predicted = predicted_points[name]
                    print(f"Matched {player['web_name']} using name variation: {name}")
                    break

            result_data.append({
                'Name': player['web_name'],
                'Team': player['team'],
                'Position': player['element_type'],
                'Total Points': player['total_points'],
                'Last 5 Games': last_5,
                'Last 3 Games': last_3,
                'Last Game': last_1,
                'Price': player['now_cost'] / 10.0,
                'Predicted Points': predicted
            })

        return pd.DataFrame(result_data)

    def get_team_players(self, team_id):
        """Get point aggregations for team players"""
        try:
            team_data = self.fpl_api.get_user_team(team_id)
            team_players = []

            # Fetch predicted points
            predicted_points = self.predicted_points_scraper.fetch_predictions()

            for pick in team_data['picks']:
                player = self.players_df[self.players_df['id'] == pick['element']].iloc[0]
                last_5, last_3, last_1 = self.calculate_player_points(player['id'])

                # Try different name variations for matching
                predicted = 0.0
                name_variations = self.get_player_name_variations(player)

                for name in name_variations:
                    if name in predicted_points:
                        predicted = predicted_points[name]
                        break

                team_players.append({
                    'Name': player['web_name'],
                    'Position': player['element_type'],
                    'Last 5 Games': last_5,
                    'Last 3 Games': last_3,
                    'Last Game': last_1,
                    'Predicted Points': predicted,
                    'Total Expected Points': last_5 + predicted
                })

            return pd.DataFrame(team_players)
        except Exception as e:
            raise Exception(f"Failed to process team data: {str(e)}")