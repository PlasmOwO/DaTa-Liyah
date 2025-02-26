# %%
import pandas as pd
import numpy as np
from footer import footer
import os
import sys
from dotenv import load_dotenv

import streamlit as st

# Check user connection
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.error('Please login to access this page')
    st.stop()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import json_scrim
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
#Filter data
team_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict)

# %%
#app config
st.set_page_config(layout="wide")
#Winrate table
columns = st.columns(5)

default_winrate_table = json_scrim.table_winrate_champs(team_filtered_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
for role in range (0,5):
    with columns[role]:
        st.subheader(role_title[role])
        st.dataframe(default_winrate_table[role], use_container_width=True)

# %%
#Winrate duomatch
st.write("Duo winrate ADC/SUP")
botlane_winrate = json_scrim.calculate_duo_winrate(team_filtered_games,roles=["BOTTOM","UTILITY"])
st.dataframe(botlane_winrate, use_container_width=True)

# %%
footer()

# %%
