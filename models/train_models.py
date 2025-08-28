import os
from dotenv import load_dotenv
import json
import pandas as pd
import numpy as np
from bson import ObjectId
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from sklearn.metrics import f1_score
import pickle
import sys
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json_scrim

connect = json_scrim.connect_database('lol_match_database', host=os.getenv("MONGO_RO_CONNECTION_STRING"))
scrim_matches = json_scrim.get_collection(connect, "scrim_matches")
data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

team_dico = json.loads(os.getenv("TEAM_SCRIM_ID"))
team_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=team_dico)
enemies_games = data_scrim_matches[~data_scrim_matches.index.isin(team_games.index)]

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
    res_df = pd.DataFrame(columns=['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY','WIN'],index=unique_game_id)
    for match_id in unique_game_id :
        res_df.loc[ObjectId(match_id), "WIN"] = data.loc[data["_id"] == ObjectId(match_id), "WIN"].values[0]
        for position_role in true_position_list:
            gold_value = data.loc[(data["_id"] == ObjectId(match_id)) & (data["TRUE_POSITION"] == position_role), "GOLD_EARNED"].values
            if gold_value.size <= 0 :
                res_df.loc[ObjectId(match_id), position_role] = np.nan
            else :
                res_df.loc[ObjectId(match_id),position_role] = int(gold_value[0])
                
    res_df["SUM_GOLD"] = res_df.drop("WIN",axis=1).sum(axis=1)
    for position_role in true_position_list:
        res_df[position_role] = res_df[position_role] / res_df["SUM_GOLD"]
    return res_df.dropna(axis=0)



def get_gold_percent_2(data : pd.DataFrame) -> pd.DataFrame:
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
            print(gold_value)
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
    res_df = pd.DataFrame(columns=['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY','WIN'],index=unique_game_id)
    ally_df = json_scrim.filter_data_on_team(data, team_dict=team_dico)
    enemy_df = data[~data.index.isin(ally_df.index)]
    for match_id in unique_game_id :
        res_df.loc[ObjectId(match_id), "WIN"] = ally_df.loc[ally_df["_id"] == ObjectId(match_id), "WIN"].values[0]

        for position_role in true_position_list:
            ally_gold = ally_df.loc[(ally_df["_id"]==ObjectId(match_id)) & (ally_df["TRUE_POSITION"]==position_role),"GOLD_EARNED"].values
            enemies_gold = enemy_df.loc[(enemy_df["_id"]==ObjectId(match_id)) & (enemy_df["TRUE_POSITION"]==position_role),"GOLD_EARNED"].values

            
            if ally_gold.size > 0 :

                res_df.loc[ObjectId(match_id),position_role] = int(ally_gold[0]) - int(enemies_gold[0])

    return res_df.dropna(axis=0)

gold_diff_df= get_gold_diff(data_scrim_matches,team_dico=team_dico)
gold_df = get_gold_percent(team_games)
enemies_gold = get_gold_percent(enemies_games)
gold_percent_all = gold_df.merge(enemies_gold, suffixes=('_ALLY','_ENEMY'), right_index=True, left_index=True).drop(columns=["WIN_ENEMY","SUM_GOLD_ALLY","SUM_GOLD_ENEMY"])
gold_percent_and_diff = gold_percent_all.merge(gold_diff_df, right_index=True, left_index=True).drop(columns=["WIN"]).rename(columns={"TOP" : "TOP_DIFF", "JUNGLE" : "JUNGLE_DIFF", "MIDDLE" : "MIDDLE_DIFF", "BOTTOM" : "BOTTOM_DIFF", "UTILITY" : "UTILITY_DIFF"})
gold_percent_and_diff["SUM_DIFF"] = gold_percent_and_diff[["TOP_DIFF", "JUNGLE_DIFF", "MIDDLE_DIFF", "BOTTOM_DIFF", "UTILITY_DIFF"]].sum(axis=1)
gold_percent_and_diff_ratio = gold_percent_and_diff.copy()
#Ratio d'avantage de gold

for diff_col in ["TOP_DIFF", "JUNGLE_DIFF", "MIDDLE_DIFF", "BOTTOM_DIFF", "UTILITY_DIFF"]:
    gold_percent_and_diff_ratio[diff_col] = np.abs(gold_percent_and_diff_ratio[diff_col]) / np.abs(gold_percent_and_diff_ratio["SUM_DIFF"])
gold_percent_and_diff_ratio.drop(columns=["SUM_DIFF"],inplace=True)
gold_percent_and_diff_ratio["WIN_ALLY"] =gold_percent_and_diff_ratio["WIN_ALLY"].map({"Win": 1, "Fail": 0})

#MODELS

##SANS PCA
x_train, x_test, y_train, y_test = train_test_split(gold_percent_and_diff_ratio.drop(columns=["WIN_ALLY"]), gold_percent_and_diff_ratio["WIN_ALLY"], test_size=0.3, random_state=42)

pipeline = Pipeline([
    ("smote", SMOTE(random_state=40,k_neighbors=4)),
    ("clf", DecisionTreeClassifier(random_state=42,criterion="entropy",max_depth=10,min_samples_split=2))
])

pipeline.fit(x_train, y_train)
y_pred_test = pipeline.predict(x_test)
test_f1 = f1_score(y_test, y_pred_test, pos_label=1)
print("Decision tree on ratio, Score on test set:", test_f1)
pickle.dump(pipeline,open("decision_tree_ratio.pickle","wb"))


##Avec PCA
pipeline = Pipeline([
    ("pca", PCA(n_components=4)),
    ("smote", SMOTE(k_neighbors=4,random_state=47)),
    ("clf", LogisticRegression(solver='liblinear',random_state=42,warm_start=True,penalty='l2',C=0.9))
])

pipeline.fit(x_train, y_train)
y_pred_test = pipeline.predict(x_test)
test_f1 = f1_score(y_test, y_pred_test, pos_label=1)
print("pca_log_reg F1, Score on test set:", test_f1)
pickle.dump(pipeline, open("pca_log_reg.pickle", "wb"))
