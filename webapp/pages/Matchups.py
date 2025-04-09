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
st.dataframe(json_scrim.calculate_matchup_winrate(data_scrim_matches,default_team_dict,role=role_filter), hide_index=True)

#Footer
footer()