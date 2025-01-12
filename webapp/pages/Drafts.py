# %%
import sys
import os
sys.path.append("../")
import draft_analyze
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
draft_df = draft_analyze.read_and_create_dataframe(drafts)

figure_bans= draft_analyze.count_champs_bans(draft_df,chart=True)



st.plotly_chart(figure_bans,theme=None)

client=MongoClient(host=os.getenv("ATLAS_CONNEXION_STRING"))
db = client["lol_match_database"]
draft_collection = db["drafts"]
df = pd.DataFrame()
for game in draft_collection.find() :
        df = pd.concat([df,pd.json_normalize(game)])

st.write(df)

a = []
for game_bans in df['blue.bans'] :
        a = a + game_bans

test = pd.DataFrame.from_dict(Counter(a), orient='index').reset_index()
bar_blue_bans = plty.bar(test, x="index",y=0)
st.plotly_chart(bar_blue_bans)
st.write(test)
