# -*- coding: utf-8 -*-
"""Cric_pre_2.0.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19FgxpykuUDtlk3DT92bxR6lbV9OLJerp
"""

# Install necessary libraries

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import re
import warnings
from pyngrok import ngrok
from flask import Flask, render_template_string, request
import io
import base64

# Warning Management
warnings.simplefilter(action='ignore', category=FutureWarning)

# Flask app setup
app = Flask(__name__)

# Set ngrok authentication token correctly
ngrok.set_auth_token("2oWXpOlDL2jTPUQywop9KXgUlfb_4yLbAntGG4UbfW8VjknsK")  # Use your actual token here

def get_player_statistics(player_name):
    """
    Fetches player statistics from Cricbuzz based on the player's name.
    """
    search_url = f"https://www.google.com/search?q={player_name}%20cricbuzz"
    search_response = requests.get(search_url).text
    search_soup = BeautifulSoup(search_response, "lxml")

    try:
        search_result = search_soup.find("div", class_="kCrYT")
        link = search_result.find("a", href=re.compile(r"[/]([a-z]|[A-Z])\w+")).attrs["href"]
        cricbuzz_url = link[7:]  # Clean up the link to get the actual URL
    except Exception as e:
        print(f"Error: {e}. Could not find Cricbuzz page. Check player name spelling.")
        return None

    # Fetch the player's profile page from Cricbuzz
    response = requests.get(cricbuzz_url).text
    soup = BeautifulSoup(response, "lxml")

    profile_section = soup.find("div", id="playerProfile")
    if not profile_section:
        print("Error: Could not fetch player profile details.")
        return None

    player_info = {}

    try:
        player_info['Name'] = profile_section.find("h1", class_="cb-font-40").text.strip()
        player_info['Country'] = profile_section.find("h3", class_="cb-font-18 text-gray").text.strip()
    except Exception as e:
        print(f"Error: {e}. Could not find basic player information.")

    summary_section = soup.find_all("div", class_="cb-plyr-tbl")
    if len(summary_section) < 2:
        print("Error: Could not find player statistics.")
        return None

    batting_stats = summary_section[0].find_all("td", class_="text-right")
    bowling_stats = summary_section[1].find_all("td", class_="text-right")

    # Store batting stats for different formats
    player_info['Test Matches'] = batting_stats[0].text.strip()
    player_info['Test Runs'] = batting_stats[3].text.strip()
    player_info['Test Average'] = batting_stats[5].text.strip()
    player_info['ODI Matches'] = batting_stats[13].text.strip()
    player_info['ODI Runs'] = batting_stats[16].text.strip()
    player_info['ODI Average'] = batting_stats[18].text.strip()
    player_info['T20 Matches'] = batting_stats[26].text.strip()
    player_info['T20 Runs'] = batting_stats[29].text.strip()
    player_info['T20 Average'] = batting_stats[31].text.strip()

    # Store bowling stats for different formats
    player_info['Test Wickets'] = bowling_stats[4].text.strip()
    player_info['Test Economy'] = bowling_stats[7].text.strip()
    player_info['ODI Wickets'] = bowling_stats[16].text.strip()
    player_info['ODI Economy'] = bowling_stats[19].text.strip()
    player_info['T20 Wickets'] = bowling_stats[28].text.strip()
    player_info['T20 Economy'] = bowling_stats[31].text.strip()

    df = pd.DataFrame([player_info])

    # Convert relevant columns to numeric types, handling any errors
    numeric_columns = ['Test Matches', 'Test Runs', 'Test Average', 'ODI Matches', 'ODI Runs', 'ODI Average',
                       'T20 Matches', 'T20 Runs', 'T20 Average', 'Test Wickets', 'Test Economy', 'ODI Wickets',
                       'ODI Economy', 'T20 Wickets', 'T20 Economy']

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')  # Coerce errors to NaN

    df.fillna("N/A", inplace=True)

    return df

def generate_visualizations(player_df):
    """Generates visualizations for player statistics and returns as base64 image."""
    formats = ['Test', 'ODI', 'T20']
    runs = [player_df[f'{format} Runs'].values[0] for format in formats]
    wickets = [player_df[f'{format} Wickets'].values[0] for format in formats]

    # Bar plots for runs and wickets
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    sns.barplot(x=formats, y=runs, ax=ax[0], palette="viridis")
    ax[0].set_title('Runs Scored in Different Formats')
    ax[0].set_ylabel('Runs')

    sns.barplot(x=formats, y=wickets, ax=ax[1], palette="viridis")
    ax[1].set_title('Wickets Taken in Different Formats')
    ax[1].set_ylabel('Wickets')

    plt.tight_layout()

    # Save the plot to a BytesIO object and encode it in base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return img_base64

@app.route("/", methods=["GET", "POST"])
def index():
    html_template = """
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            color: #495057;
            padding: 20px;
            flex-direction: column;
        }

        .container {
            width: 100%;
            max-width: 500px;
            background-color: #ffffff;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
            text-align: center;
            margin-bottom: 20px;
        }

        h1, h2 {
            font-weight: 600;
            color: #343a40;
            margin-bottom: 15px;
        }

        form {
            margin-bottom: 20px;
        }

        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin: 12px 0;
            border: 1px solid #ced4da;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        input[type="text"]:focus {
            border-color: #80bdff;
            outline: none;
            box-shadow: 0 0 8px rgba(128, 189, 255, 0.5);
        }

        button {
            width: 100%;
            padding: 12px;
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button:hover {
            background-color: #0056b3;
        }

        .statistics-container {
            background-color: #f1f3f5;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }

        ul {
            list-style: none;
            padding: 0;
            text-align: left;
        }

        ul li {
            padding: 8px 0;
            font-size: 1rem;
            border-bottom: 1px solid #dee2e6;
        }

        .visualization-container {
            width: 100%;
            max-width: 900px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
            text-align: center;
        }

        .visualization-container img {
            width: 100%;
            height: auto;
            max-height: 600px;
            border-radius: 8px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }

        .error-message {
            color: #dc3545;
            font-size: 0.9rem;
            margin-top: 15px;
            font-weight: bold;
        }
    </style>

    <div class="container">
        <h1>Player Statistics</h1>
        <form method="post">
            <input type="text" name="player_name" placeholder="Enter Player Name" required>
            <button type="submit">Get Statistics</button>
        </form>

        {% if player_info %}
            <div class="statistics-container">
                <h2>{{ player_info['Name'] }}</h2>
                <ul>
                    {% for key, value in player_info.items() %}
                        <li><strong>{{ key }}:</strong> {{ value }}</li>
                    {% endfor %}
                </ul>
            </div>
        {% endif %}

        {% if error %}
            <p class="error-message">{{ error }}</p>
        {% endif %}
    </div>

    {% if player_info %}
        <div class="visualization-container">
            <h2>Visualizations</h2>
            <img src="data:image/png;base64,{{ plot_url }}" alt="Player Statistics Visualization">
        </div>
    {% endif %}
    """

    if request.method == "POST":
        player_name = request.form["player_name"]
        player_df = get_player_statistics(player_name)
        if player_df is not None:
            plot_url = generate_visualizations(player_df)
            player_info = player_df.to_dict(orient="records")[0]
            return render_template_string(html_template, player_info=player_info, plot_url=plot_url)
        else:
            return render_template_string(html_template, error="Could not retrieve player statistics.")
    return render_template_string(html_template)

# Expose the Flask app to the public using ngrok
public_url = ngrok.connect(5000)
print(f"Public URL: {public_url}")

# Run the app
app.run(port=5000)