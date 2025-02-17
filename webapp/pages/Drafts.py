# %%
import sys
import os
from footer import footer


from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
from collections import Counter
import plotly.express as plty

# Check user connection
if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.error('Please login to access this page')
    st.stop()
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import draft_analyze
import json_scrim

# %%
## Draft analyze
connect = draft_analyze.connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
drafts = draft_analyze.get_collection(connect,"drafts")
drafts_df = draft_analyze.read_and_create_dataframe(drafts)
scrims = json_scrim.get_collection(connect, "scrim_matches")
scrims_df = json_scrim.read_and_create_dataframe(scrims)

merged_data = draft_analyze.merge_scrim_with_draft(scrims_df,drafts_df)


## Bans chart
# figure_bans= draft_analyze.count_champs_bans(drafts_df,chart=True)
# st.plotly_chart(figure_bans,theme=None)

## Bans chart images
st.subheader("Number of bans")
bans_filter = st.segmented_control("Bans filter",options=["Both","Enemies bans","Allies bans"],default="Both", selection_mode="single")
drafts_df = draft_analyze.filter_drafts(drafts_df,"SCL",bans_filter)
figure_bansv2= draft_analyze.count_champs_bansv2(drafts_df,chart=True)

## DataFrame
st.dataframe(drafts_df)

st.dataframe(merged_data)
footer()