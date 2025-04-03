
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time

class PredictedPointsScraper:
    def __init__(self):
        self.url = "https://fplform.com/fpl-predicted-points"
        self.predicted_points = {}

    def fetch_predictions(self):
        """Fetch and parse predicted points from fplform.com"""
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Origin': 'https://fplform.com',
                'Referer': 'https://fplform.com/'
            }

            print("Fetching data from fplform.com...")
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            print(f"Response status code: {response.status_code}")

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try different table selectors
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables on the page")
            
            if not tables:
                print("No tables found on the page")
                print("Page content preview:")
                print(soup.text[:1000])
                return {}

            # Use the first table that has player data
            table = tables[0]  # Usually the main table is the first one
            
            # Look for rows with player data
            rows = table.find_all('tr')
            print(f"Found {len(rows)} rows in table")
            
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) < 10:  # Make sure we have enough columns
                    continue

                try:
                    # Get player name from the first column
                    player_name = cells[1].text.strip()  # Usually in the second column
                    if not player_name:
                        continue

                    # Get predicted points from the points column (10th column)
                    points_cell = cells[9]  # 10th column (index 9)
                    text_value = points_cell.text.strip()
                    
                    # Clean and convert the predicted points value
                    numeric_value = ''.join(c for c in text_value if c.isdigit() or c == '.')
                    if numeric_value:
                        value = float(numeric_value)
                        if value > 0:  # Valid predicted points
                            self.predicted_points[player_name] = value
                            print(f"Found prediction for {player_name}: {value}")

                except (IndexError, ValueError, AttributeError) as e:
                    print(f"Error processing row: {str(e)}")
                    continue

            print(f"Successfully processed {len(self.predicted_points)} predictions")
            if not self.predicted_points:
                print("Warning: No predictions were found")

            return self.predicted_points

        except Exception as e:
            print(f"Error fetching predicted points: {str(e)}")
            if 'response' in locals():
                print(f"Response content: {response.text[:500]}...")
            return {}
