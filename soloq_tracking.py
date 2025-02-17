import pandas as pd
import sqlite3
import datetime
import plotly.express as plty
import plotly.graph_objects as go
from dotenv import load_dotenv
load_dotenv()
import os
import requests
from typing import Literal
#https://github.com/Allan-Cao

API_KEY = os.getenv("API_KEY")


def get_league_HL_player() -> tuple:
    """Request the API to get all master+ players

    Returns:
        tuple: A list with challenger and GM players and another with master players.
    """

    challenger_call = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}")
    challenger_call.raise_for_status()
    grandmaster_call = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}")
    grandmaster_call.raise_for_status()
    master_call = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5?api_key={API_KEY}")
    master_call.raise_for_status()
    
    return challenger_call.json()['entries'] + grandmaster_call.json()['entries'] , master_call.json()['entries']


def calculate_cutoffs(gm_chall_player : list,master_player : list) -> tuple :
    """Calculate how many lp is needed to be challenger or grandmaster

    Args:
        gm_chall_player (list): List of challenger and grandmaster players
        master_player (list): List of master players

    Returns:
        tuple: Tuple containing the cutoffs (lp needed) for challenger and grandmaster
    """
    
    if len(gm_chall_player) < 1000:
        return 500,200
    hl_player = gm_chall_player + master_player
    hl_player.sort(key=lambda x: x["leaguePoints"], reverse=True)
    chall_player_lbBased = hl_player[0:300]
    gm_player_lbBased = hl_player[300:700+300]

    challenger_cutoff = chall_player_lbBased[-1]["leaguePoints"] + 1
    grandmaster_cutoff = gm_player_lbBased[-1]["leaguePoints"] + 1
    return challenger_cutoff, grandmaster_cutoff

#HL Cutoffs
gm_chall_player,master_player = get_league_HL_player()
challenger_cutoff, grandmaster_cutoff = calculate_cutoffs(gm_chall_player,master_player)

tiers = {
    'IRON': 0,
    'BRONZE': 400,
    'SILVER': 800,
    'GOLD': 1200,
    'PLATINUM': 1600,
    'EMERALD' : 2000,
    'DIAMOND': 2400,
    'MASTER': 2800,
    'GRANDMASTER': 2800+grandmaster_cutoff,
    'CHALLENGER': 2800+challenger_cutoff
}

divisions = {
    'IV': 0,
    'III': 100,
    'II': 200,
    'I': 300
}




def plot_soloq_tracking():
    """Connect to the database and plot evolution of ranks for each players

    Returns:
        A plotly figure
    """
    
    #DB connection
    con = sqlite3.connect('soloq_tracking.db')
    cursor = con.cursor()
    database_table = cursor.execute("SELECT * FROM soloq_tracking").fetchall()
    soloq_df = pd.DataFrame(database_table, columns=["date","TOP_RANK","JNG_RANK","MID_RANK","ADC_RANK","SUP_RANK"])
    soloq_df["date"] = pd.to_datetime(soloq_df["date"])

    #Plot
    images_path = "images/rank_emblems/"
    fig = go.Figure()

    for role in ["TOP_RANK","JNG_RANK","MID_RANK","ADC_RANK","SUP_RANK"] :
        fig.add_trace(go.Scatter(x=soloq_df["date"], y=soloq_df[role],mode='lines+markers',name=role))


    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Rank',
        legend_title_text='Roles',
        yaxis=dict(
            tickmode='array',
            tickvals=list(tiers.values()),
            ticktext=list(tiers.keys()),
            showgrid=True,
            gridwidth=1,
            zeroline=False,
            minor=dict(
                tickmode='linear',
                tick0=0,
                dtick=100,
                gridcolor='LightGray',
                gridwidth=0.5
            )
        )
    )
    con.close()
    return fig

