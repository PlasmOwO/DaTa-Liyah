import uvicorn
from fastapi import FastAPI, File, UploadFile
import pickle
import json
import streamlit as st
import pandas as pd
from bson import ObjectId
import numpy as np
from .. import json_scrim
from dotenv import load_dotenv
import os

def get_gold_percent(data : pd.DataFrame) -> pd.DataFrame:
    """Create a dataframe with the percentage of gold by player. Use this function with filtered data on a specific team.
    Drop NAN values to the returned dataframe.

    Args:
        data (pd.DataFrame): The filtered dataframe

    Returns:
        pd.DataFrame: DataFrame with :
            * Rows = Unique game ID
            * Columns = %gold per role and if the game is won or not
    """
    true_position_list = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    unique_game_id = data["_id"].unique()
    res_df = pd.DataFrame(columns=['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'],index=unique_game_id)
    for match_id in unique_game_id :
        for position_role in true_position_list:
            gold_value = data.loc[(data["_id"] == ObjectId(match_id)) & (data["TRUE_POSITION"] == position_role), "GOLD_EARNED"].values
            if gold_value.size <= 0 :
                res_df.loc[ObjectId(match_id), position_role] = np.nan
            else :
                res_df.loc[ObjectId(match_id),position_role] = int(gold_value[0])
                
    res_df["SUM_GOLD"] = res_df.sum(axis=1)
    for position_role in true_position_list:
        res_df[position_role] = res_df[position_role] / res_df["SUM_GOLD"]
    return res_df.dropna(axis=0)

def get_gold_diff(data : pd.DataFrame, team_dico ) -> pd.DataFrame :
    """Compute gold difference between our team for all the game and for each role

    Args:
        data (pd.DataFrame): The global dataframe
        team_dico (_type_): The team dictionnary of your team

    Returns:
        pd.DataFrame: A dataframe containing the gold diff for eeach role at the end of the game
    """

    true_position_list = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    unique_game_id = data["_id"].unique()
    res_df = pd.DataFrame(columns=['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'],index=unique_game_id)
    ally_df = json_scrim.filter_data_on_team(data, team_dict=team_dico)
    enemy_df = data[~data.index.isin(ally_df.index)]
    for match_id in unique_game_id :

        for position_role in true_position_list:
            ally_gold = ally_df.loc[(ally_df["_id"]==ObjectId(match_id)) & (ally_df["TRUE_POSITION"]==position_role),"GOLD_EARNED"].values
            enemies_gold = enemy_df.loc[(enemy_df["_id"]==ObjectId(match_id)) & (enemy_df["TRUE_POSITION"]==position_role),"GOLD_EARNED"].values

            
            if ally_gold.size > 0 :

                res_df.loc[ObjectId(match_id),position_role] = int(ally_gold[0]) - int(enemies_gold[0])

    return res_df.dropna(axis=0)

    


app = FastAPI()

model = pickle.load(open('decision_tree_ratio.pickle', 'rb'))
load_dotenv()
@app.get("/")
def index():
    return {"message": "Welcome to the API !"}

@app.post("/predict/")
async def predict(file: UploadFile):

    team_dico = json.loads(os.getenv("TEAM_SCRIM_ID"))


    df = pd.DataFrame()
    content = await file.read()

    df = pd.concat([df,pd.json_normalize(json.loads(content))])
    df = df.explode('participants').reset_index(drop=True)
    df_participants = pd.json_normalize(df['participants'])
    df = pd.concat([df.drop(columns='participants'),df_participants],axis = 1)
    df['VISION_WARDS_BOUGHT_IN_GAME'] = df['VISION_WARDS_BOUGHT_IN_GAME'].astype('int')
    df['datetime'] = pd.to_datetime(df['jsonFileName'].apply(lambda x : x.split('_')[0]), format='%d%m%Y')
    df['_id'] = df['_id.$oid']
    df.drop(columns=['_id.$oid'],inplace=True)
    df['_id'] = df['_id'].apply(lambda x : ObjectId(x))





    allies = df.loc[df['PUUID'].apply(lambda puuid: any(puuid in sublist for sublist in team_dico.values()))]
    enemies = df.loc[~df['PUUID'].apply(lambda puuid: any(puuid in sublist for sublist in team_dico.values()))]

    
    gold_df = get_gold_percent(allies)
    enemies_gold = get_gold_percent(enemies)

    gold_diff_df = get_gold_diff(df,team_dico)

    gold_percent_all = gold_df.merge(enemies_gold, suffixes=('_ALLY','_ENEMY'), right_index=True, left_index=True).drop(columns=["SUM_GOLD_ALLY","SUM_GOLD_ENEMY"])
    gold_percent_and_diff = gold_percent_all.merge(gold_diff_df, right_index=True, left_index=True).rename(columns={"TOP" : "TOP_DIFF", "JUNGLE" : "JUNGLE_DIFF", "MIDDLE" : "MIDDLE_DIFF", "BOTTOM" : "BOTTOM_DIFF", "UTILITY" : "UTILITY_DIFF"})

    gold_percent_and_diff["SUM_DIFF"] = gold_percent_and_diff[["TOP_DIFF", "JUNGLE_DIFF", "MIDDLE_DIFF", "BOTTOM_DIFF", "UTILITY_DIFF"]].sum(axis=1)
    gold_percent_and_diff_ratio = gold_percent_and_diff.copy()
    for diff_col in ["TOP_DIFF", "JUNGLE_DIFF", "MIDDLE_DIFF", "BOTTOM_DIFF", "UTILITY_DIFF"]:
        gold_percent_and_diff_ratio[diff_col] = np.abs(gold_percent_and_diff_ratio[diff_col]) / np.abs(gold_percent_and_diff_ratio["SUM_DIFF"])
    gold_percent_and_diff_ratio.drop(columns=["SUM_DIFF"],inplace=True)
    

    #pred
    res = model.predict(gold_percent_and_diff_ratio)
    return {"predictions": res.tolist()}
    
        

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)