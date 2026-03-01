import streamlit as st
import plotly.express as plty
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb
from footer import footer
import yaml
from yaml import SafeLoader
import streamlit_authenticator as stauth
import pandas as pd
import os
import sys

#Import config :
st.set_page_config(layout="wide")



## Welcome message
# st.title(f"Welcome to the League of Legends Dashboard")

#Import scrim data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import json_scrim

connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
scrim_matches = json_scrim.get_collection(connect, "scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

team_dico = st.secrets["TEAM_SCRIM_ID"]
team_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=team_dico)

default_team_dict = st.secrets["TEAM_SCRIM_ID"]

#sidebar
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
    


# History
st.title("Historique des parties")
history_columns_order = ["Win","Ally side"] + list(st.secrets["TEAM_DICT_NAME"].keys()) + ["TOTAL_ALLY_KILL","enemy_TOP","enemy_JUNGLE","enemy_MIDDLE","enemy_BOTTOM","enemy_UTILITY","TOTAL_ENEMY_KILL","enemyTeamName","gameDuration","patchVersion","datetime"]
history_columns_config = {
    **{
        f"{name}": st.column_config.ImageColumn()
        for name in st.secrets["TEAM_DICT_NAME"].keys()
    },
    **{
        f"enemy_{role}": st.column_config.ImageColumn()
        for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    },
    "datetime" : st.column_config.DatetimeColumn(
        "datetime", format="YYYY-MM-DD"
    ),
}

st.dataframe(json_scrim.history(data_scrim_matches, dict_name=st.secrets["TEAM_DICT_NAME"],), hide_index=True,  column_order=history_columns_order,column_config=history_columns_config
)


# Winrate by side group by week
# st.header("Winrate by side through time")
st.header("Winrate par side au fil du temps")
winrate_by_side_time = json_scrim.get_winrate_by_side_every_two_weeks(team_games, True)
st.plotly_chart(winrate_by_side_time,use_container_width=True)

# Winrate by side bar
st.header("Winrate par side")

winrate_by_side = json_scrim.get_winrate_by_side(team_games, True)
st.plotly_chart(winrate_by_side, use_container_width=True)



footer()



