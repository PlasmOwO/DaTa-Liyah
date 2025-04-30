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

#app config
st.set_page_config(layout="wide")

#Filter official matches sidebar
with st.sidebar :
    st.write("Filter official matches")
    official_filter = st.multiselect("Choose filter",options=[0,1,2,3,4,5,6],default=[],key="official_match")
    data_scrim_matches = json_scrim.filter_data_official_matches(data_scrim_matches, official_filter)

#Filter data
team_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict)

#Winrate table
st.header("Number of games : " + str(len(team_filtered_games['_id'].unique())))
columns = st.columns(5)

default_winrate_table = json_scrim.table_winrate_champs(team_filtered_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
for role in range (0,5):
    with columns[role]:
        st.subheader(role_title[role])
        st.dataframe(default_winrate_table[role], use_container_width=True)

# %%
#Winrate duomatch
st.write("Duo winrate")
selected_roles = st.multiselect("Select roles", ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"], default=["BOTTOM","UTILITY"], max_selections=2)
if len(selected_roles) <2 :
    st.info("You need to select 2 roles.", icon="ℹ️")
else :
    duo_winrate = json_scrim.calculate_duo_winrate(team_filtered_games,roles=selected_roles)
    st.dataframe(duo_winrate, use_container_width=True,hide_index=True)


#Winrate ennemies champs
st.write("Enemies winrate")
enemies_columns = st.columns(5)
enemies_filtered_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=default_team_dict,enemies=True)
enemies_winrate_table = json_scrim.table_winrate_champs(enemies_filtered_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
for role in range (0,5):
    with enemies_columns[role]:
        st.subheader(role_title[role])
        st.dataframe(enemies_winrate_table[role], use_container_width=True)



# %%
footer()

# %%
