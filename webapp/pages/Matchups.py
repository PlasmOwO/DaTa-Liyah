import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
from footer import footer

import streamlit as st
st.set_page_config(layout="wide")
# Check user connection
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.error('Please login to access this page')
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import json_scrim
load_dotenv()
#Connect database
default_team_dict = st.secrets["TEAM_SCRIM_ID"]
connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
scrim_matches = json_scrim.get_collection(connect,"scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

#Matchups by role
st.subheader("Matchups par role")
roles = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
role_filter = st.segmented_control("Role filter",options=roles,default="TOP", selection_mode="single")
matchup_table, matchup_style = json_scrim.calculate_matchup_winrate(data_scrim_matches,default_team_dict,role=role_filter)
st.dataframe(matchup_style, hide_index=True)

#Detail d'un matchup
st.subheader("Matchup details")
print(np.sort(matchup_table["ALLY_CHAMPION"].unique()))
ally_champ = st.selectbox("Champion",options = np.sort(matchup_table["ALLY_CHAMPION"].unique()),index=None, placeholder="Select a champion")
possible_enemies_champs = np.sort(matchup_table[matchup_table["ALLY_CHAMPION"]==ally_champ]["ENEMY_CHAMPION"].unique())
disable_enemy = True
if ally_champ != None :
    disable_enemy = False
enemy_champ = st.selectbox("Enemy champion",options = possible_enemies_champs,index=None, placeholder="Select a champion",disabled=disable_enemy)


#Footer
footer()