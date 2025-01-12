# %%
import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append("../")

import json_scrim
import streamlit as st



# %% [markdown]
# ### Dictionnary of teams

# %%
team_scald_dico = {
    "TOP" : ["a2f2aa07-9633-5e7a-9f38-7c16c69a9e21"],
    "JUNGLE" : ["273ae685-12da-5942-9e93-46dd2620f8ff"],
    "MIDDLE" : ["df39f5ef-6758-5669-82fe-f7d96aac3d2c"],
    "BOTTOM": ["9af56d81-a4c0-5447-b465-dd203dd80c6f"],
    "UTILITY" : ["3b463f3c-f0b3-5063-89dd-fe763bc3d4a2"]
}


# %%
#Connect to database
connect = json_scrim.connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
scrim_matches = json_scrim.get_collection(connect,"scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)
#Filter data
scl_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=team_scald_dico)

# %%
#Winrate table
columns = st.columns(5)

winrate_table_scl = json_scrim.table_winrate_champs(scl_games)
role_title = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
for role in range (0,5):
    with columns[role]:
        st.subheader(role_title[role])
        st.dataframe(winrate_table_scl[role])

# %%
#Winrate duomatch
st.write("Duo winrate ADC/SUP")
botlane_winrate = json_scrim.calculate_duo_winrate(scl_games,roles=["BOTTOM","UTILITY"])
st.dataframe(botlane_winrate)

# %%

# %%
