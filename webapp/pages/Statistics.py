from footer import footer
import os
import sys
from dotenv import load_dotenv

import streamlit as st

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.error('Please login to access this page')
    st.stop()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import json_scrim
load_dotenv()

default_team_dict = st.secrets["TEAM_SCRIM_ID"]
connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
scrim_matches = json_scrim.get_collection(connect,"scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

st.set_page_config(layout="wide")
team_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict)

#Number of pinks
st.header("Number of pinks bought in game")
pinks_chart = json_scrim.get_nb_pink_bought(team_filtered_games,chart=True)
st.plotly_chart(pinks_chart, use_container_width=True)
footer()
