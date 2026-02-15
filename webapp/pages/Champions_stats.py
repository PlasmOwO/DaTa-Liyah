# %%
import pandas as pd
import numpy as np
from footer import footer
import os
import sys
from dotenv import load_dotenv
import datetime
import json_scrim
import streamlit as st

# Check user connection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

load_dotenv()
# %% [markdown]
# ### Dictionnary of teams

# %%
default_team_dict = st.secrets["TEAM_SCRIM_ID"]
# %%
#Connect to database
connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
scrim_matches = json_scrim.get_collection(connect,"scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

#app config
st.set_page_config(layout="wide")

#Filter official matches sidebar
with st.sidebar :
    ## Filter data on patch
    patch_filter = st.multiselect("Patch",options=data_scrim_matches["patchVersion"].unique().tolist(), default=[], key="patch_filter")
    data_scrim_matches = json_scrim.filter_data_patch(data_scrim_matches, patch_filter)

    ## Filter on enemyTeam
    enemyTeam_filter = st.multiselect("Enemy Team",options=data_scrim_matches["enemyTeamName"].unique().tolist(), default=[], key="enemyTeam_filter")
    data_scrim_matches = json_scrim.filter_data_enemy_team(data_scrim_matches, enemyTeam_filter)

    ## Filter on typeGame
    game_types = data_scrim_matches["gameType"].unique().tolist()
    display_mapping = {gt.capitalize(): gt for gt in game_types}
    typeGame_filter_display = st.multiselect("Type of game",options=list(display_mapping.keys()), default=[], key="typeGame_filter")
    typeGame_filter = [display_mapping[val] for val in typeGame_filter_display]
    data_scrim_matches = json_scrim.filter_data_typeGame(data_scrim_matches, typeGame_filter)

    ## Filter on side
    side_filter = st.multiselect("Side",options=["Blue","Red"], default=[], key="side_filter")
    data_scrim_matches = json_scrim.filter_data_team_side(data_scrim_matches, side_filter,team_dict=default_team_dict)

    ## Filter on date
    date_filter = st.date_input(
        "Select your date filter",
        [],
        None,
        "today",
        format="DD.MM.YYYY"
    )
    data_scrim_matches = (json_scrim.filter_data_date(data_scrim_matches, date_filter[0], date_filter[1])     if len(date_filter) == 2 else data_scrim_matches)
    



    ## Filter official matches
    official_filter = st.multiselect("Offical matches",options=[0,1,2,3,4,5,6],default=[],key="official_match",disabled=True)
    data_scrim_matches = json_scrim.filter_data_official_matches(data_scrim_matches, official_filter)
    
    

    ## Filter on  jungler
    jungler_swap = st.toggle("Swap Jungler", value=False,disabled=True)
    if jungler_swap:
        st.write("🟢 Jungler changé en **New Jungler**")
        jungler_filter = ["New Jungler"]
    else :
        st.write("⚪️ Jungler par défaut **Old Jungler**")
        jungler_filter = ["Old Jungler"]
    data_scrim_matches = json_scrim.get_jungler_puuid(
        data_scrim_matches,
        jungler_filter,
        team_dict=default_team_dict
    )
#Filter data
team_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict)

#KPIs
games, winrate, duration, side_winrate = st.columns([0.15,0.15,0.15,0.55])
games.metric("![sword](https://github.githubassets.com/images/icons/emoji/unicode/2694.png?v8) Number of games", len(team_filtered_games['_id'].unique()), border=True)
winrate.metric("![crown](https://github.githubassets.com/images/icons/emoji/unicode/1f451.png?v8) Winrate (%)", json_scrim.get_mean_winrate(team_filtered_games).round(2), border=True)
duration.metric("![time](https://github.githubassets.com/images/icons/emoji/unicode/1f551.png?v8) Mean duration (min)",json_scrim.get_mean_duration(team_filtered_games),border=True)
#Side winrate
winrate_by_side = json_scrim.get_winrate_by_side(team_filtered_games, True)
side_winrate.plotly_chart(winrate_by_side, height=175,width="content",config={"displayModeBar": False})



#Winrate table
columns = st.columns(5)

default_winrate_table = json_scrim.table_winrate_champs(team_filtered_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","SUPPORT"]
for role in range (0,5):
    with columns[role]:
        st.subheader(role_title[role])
        st.dataframe(default_winrate_table[role], width="stretch", column_config={
            "SKIN": st.column_config.ImageColumn("Champion"),
        })

# %%
#Winrate duomatch
st.write("Duo winrate")
ROLE_MAP = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "MIDDLE": "MIDDLE",
    "BOTTOM": "BOTTOM",
    "SUPPORT": "UTILITY", #BACK -> value
}

selected_roles_display = st.multiselect("Select roles", list(ROLE_MAP.keys()), default=["BOTTOM","SUPPORT"], max_selections=2)
selected_roles = [ROLE_MAP[r] for r in selected_roles_display]
if len(selected_roles) <2 :
    st.info("You need to select 2 roles.", icon="ℹ️")
else :
    duo_winrate = json_scrim.calculate_duo_winrate(team_filtered_games,roles=selected_roles)
    st.dataframe(duo_winrate, width="stretch",height="stretch",hide_index=True, column_config={
        f"{selected_roles[0]}_CHAMPION" : st.column_config.ImageColumn(),
        f"{selected_roles[1]}_CHAMPION" : st.column_config.ImageColumn(),

    })


#Winrate ennemies champs
st.write("Enemies winrate")
enemies_columns = st.columns(5)
enemies_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict,enemies=True)
enemies_winrate_table = json_scrim.table_winrate_champs(enemies_filtered_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","SUPPORT"]
for role in range (0,5):
    with enemies_columns[role]:
        st.subheader(role_title[role])
        st.dataframe(enemies_winrate_table[role], width="stretch", column_config={
            "SKIN": st.column_config.ImageColumn("Champion"),
        })



# %%
footer()

# %%
