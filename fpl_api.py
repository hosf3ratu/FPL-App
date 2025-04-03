import requests
import pandas as pd

class FPLApi:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self):
        self.session = requests.Session()
        # Set up headers to mimic a browser request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://fantasy.premierleague.com',
            'Referer': 'https://fantasy.premierleague.com/'
        })

    def login(self, email, password):
        """Log in to FPL"""
        try:
            # Get the login page first to get any necessary cookies
            self.session.get("https://users.premierleague.com/")

            login_url = "https://users.premierleague.com/accounts/login/"
            payload = {
                'login': email,
                'password': password,
                'app': 'plfpl-web',
                'redirect_uri': 'https://fantasy.premierleague.com/',
            }

            # Add specific headers for the login request
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = self.session.post(
                login_url,
                data=payload,
                headers=headers,
                allow_redirects=True
            )

            # Check if login was successful by trying to access team data
            test_url = f"{self.BASE_URL}/me/"
            test_response = self.session.get(test_url)
            if test_response.status_code == 200:
                return True
            else:
                raise Exception("Invalid credentials")

        except requests.RequestException as e:
            raise Exception(f"Login failed: {str(e)}")

    def get_all_players(self):
        """Fetch all player data from FPL API"""
        try:
            response = self.session.get(f"{self.BASE_URL}/bootstrap-static/")
            response.raise_for_status()
            data = response.json()
            return pd.DataFrame(data['elements'])
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch player data: {str(e)}")

    def get_player_history(self, player_id):
        """Fetch player's game history"""
        try:
            response = self.session.get(f"{self.BASE_URL}/element-summary/{player_id}/")
            response.raise_for_status()
            data = response.json()
            return pd.DataFrame(data['history'])
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch player history: {str(e)}")

    def get_user_team(self, team_id):
        """Fetch user's team data"""
        try:
            # Get current event (gameweek)
            response = self.session.get(f"{self.BASE_URL}/entry/{team_id}/")
            response.raise_for_status()
            entry_data = response.json()
            current_event = entry_data.get('current_event', 1)

            # Get the team picks for current gameweek
            picks_response = self.session.get(f"{self.BASE_URL}/entry/{team_id}/event/{current_event}/picks/")
            picks_response.raise_for_status()
            return picks_response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch team data. Please verify your team ID is correct: {str(e)}")