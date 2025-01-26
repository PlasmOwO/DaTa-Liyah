# %%
import sys
import os
from footer import footer
sys.path.append("../")
import draft_analyze
import json_scrim
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
from collections import Counter
import plotly.express as plty


load_dotenv()

# %%
## Draft analyze
connect = draft_analyze.connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
drafts = draft_analyze.get_collection(connect,"drafts")
drafts_df = draft_analyze.read_and_create_dataframe(drafts)
scrims = json_scrim.get_collection(connect, "scrim_matches")
scrims_df = json_scrim.read_and_create_dataframe(scrims)

merged_data = draft_analyze.merge_scrim_with_draft(scrims_df,drafts_df)


## Bans chart
figure_bans= draft_analyze.count_champs_bans(drafts_df,chart=True)
st.plotly_chart(figure_bans,theme=None)

st.subheader("Number of bans")
figure_bansv2= draft_analyze.count_champs_bansv2(drafts_df,chart=True)

## DataFrame
st.dataframe(drafts_df)

st.dataframe(merged_data)
footer()