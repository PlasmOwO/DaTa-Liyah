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
st.title(f"Welcome to the League of Legends Dashboard")

#Import scrim data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import json_scrim


connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
scrim_matches = json_scrim.get_collection(connect, "scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

team_dico = st.secrets["TEAM_SCRIM_ID"]
team_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=team_dico)

print(list(st.secrets["TEAM_DICT_NAME"].keys()))
# History
history_columns_order = ["Win","ALLY_TEAM__"] + list(st.secrets["TEAM_DICT_NAME"].keys()) + ["TOTAL_ALLY_KILL","enemy_TOP","enemy_JUNGLE","enemy_MIDDLE","enemy_BOTTOM","enemy_UTILITY","TOTAL_ENEMY_KILL","gameDuration","patchVersion","datetime"]
st.dataframe(json_scrim.history(data_scrim_matches, dict_name=st.secrets["TEAM_DICT_NAME"],), hide_index=True,  column_order=history_columns_order,column_config={
    "datetime" : st.column_config.DatetimeColumn(
        "datetime", format="YYYY-MM-DD"
    )
}
)


# Winrate by side group by week
st.header("Winrate by side through time")
winrate_by_side_time = json_scrim.get_winrate_by_side_every_two_weeks(team_games, True)
st.plotly_chart(winrate_by_side_time,use_container_width=True)

# Winrate by side bar
st.header("Winrate by side")

winrate_by_side = json_scrim.get_winrate_by_side(team_games, True)
st.plotly_chart(winrate_by_side, use_container_width=True)



footer()



