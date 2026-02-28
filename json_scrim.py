# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
from pymongo import MongoClient
import pandas as pd
import plotly.express as plty
import plotly.graph_objects as go
import plotly.subplots
import os
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import warnings
from bson import ObjectId
import numpy as np
import utils
load_dotenv()


# %%
def connect_database(database_name : str, host : str = 'localhost') :
    """Create connexion to Mongo Database

    Args:
        database_name (str): Name of the database

    Returns:
        Client connexion
    """
    client = MongoClient(host=host)
    return client[database_name]

def get_collection(connection, collection_name : str) :
    """Connect to a Mongo collection

    Args:
        connection : Mongo client connection
        collection_name (str): Name of the collection

    Returns:
        _type_: The collection
    """
    return connection[collection_name]


# %%
def read_and_create_dataframe(collection) -> pd.DataFrame :
    """Read a collection with League of Legends JSON data and create the associated dataframe
    Each row correspond to (match,participant) key.

    Args:
        collection (_type_): Mongo collection

    Returns:
        pd.DataFrame: DataFrame of the JSON data
    """
    df = pd.DataFrame()
    for game in collection.find() :
        df = pd.concat([df,pd.json_normalize(game)])
    df = df.explode('participants').reset_index(drop=True)
    df_participants = pd.json_normalize(df['participants'])
    df = pd.concat([df.drop(columns='participants'),df_participants],axis = 1)
    df['VISION_WARDS_BOUGHT_IN_GAME'] = df['VISION_WARDS_BOUGHT_IN_GAME'].fillna(0).astype('int')
    df['datetime'] = pd.to_datetime(df['jsonFileName'].apply(lambda x : x.split('_')[0]), format='%d%m%Y')
    return df


# %%
# connect = connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
# scrim_matches = get_collection(connect,"scrim_matches")
# data_scrim_matches = read_and_create_dataframe(scrim_matches)


# %%
def filter_data_on_team(data : pd.DataFrame,team_dict : dict, enemies : bool = False) -> pd.DataFrame :
    """Filter data based on a team PUUID dictionnary

    Args:
        data (pd.DataFrame): Input data
        team_dict (dict): Dictionnary containing PUUID. Example = {"TOP" : ["9df5d86"], "JUNGLE" : ...}
        enemies (bool): If you want to negate the filter to retrieve enemies data (Default : False)

    Returns:
        pd.DataFrame: The filtered DataFrame
    """
    try :
        if enemies : 
            return data.loc[~data['PUUID'].apply(lambda puuid: any(puuid in sublist for sublist in team_dict.values()))]
        else :
            return data.loc[data['PUUID'].apply(lambda puuid: any(puuid in sublist for sublist in team_dict.values()))]
    except KeyError :
        warnings.warn("Filter_data_on_team : KeyError, maybe caused by filtering on empty data")
        return pd.DataFrame(columns=data.columns)

# import streamlit as st
# print(data_scrim_matches.shape)
# print(filter_data_on_team(data_scrim_matches,team_dict=st.secrets["TEAM_SCRIM_ID"],enemies=False).iloc[5]['RIOT_ID_GAME_NAME'])

def filter_data_official_matches(data : pd.DataFrame, list_etape : list = []) ->pd.DataFrame :
    """Filter data on the selected official matches (list of nexus tour steps)

    Args:
        data (pd.DataFrame): Input data
        list_etape (list): A list containing the official match steps (for example : [0,1,2,3,...])

    Returns:
        pd.DataFrame: The filtered Data
    """
    if list_etape == [] :
        return data
    return data.loc[data['officialMatch'].isin(list_etape)]

def filter_data_date(data : pd.DataFrame, start_date : datetime.date , end_date : datetime.date) -> pd.DataFrame :

    time_filtered_df = data.loc[(start_date <= data["datetime"].dt.date) & (data["datetime"].dt.date<= end_date)]
    if time_filtered_df.empty :
        time_filtered_df = pd.DataFrame(columns=data.columns)
    return time_filtered_df

def filter_data_patch(data : pd.DataFrame, list_patch : list) -> pd.DataFrame :
    """Filter data on the selected patches

    Args:
        data (pd.DataFrame): Input data
        list_patch (list): A list of patch version

    Returns:
        pd.DataFrame: The filtered data
    """
    if list_patch == [] :
        return data
    return data.loc[data["patchVersion"].isin(list_patch)]


def filter_data_enemy_team(data : pd.DataFrame, list_team_name : list) -> pd.DataFrame :
    """Filter data on the selected teams opponents (to retrieve only matches against these teams)

    Args:
        data (pd.DataFrame): Input data
        list_team_name (list): A list of team names

    Returns:
        pd.DataFrame: The filtered data
    """
    if list_team_name == [] :
        return data
    return data.loc[data["enemyTeamName"].isin(list_team_name)]

def filter_data_typeGame(data : pd.DataFrame, list_type_game : list) -> pd.DataFrame :
    """Filter data on the selected type of game

    Args:
        data (pd.DataFrame): Input data
        list_type_game (list): A list of type of games

    Returns:
        pd.DataFrame: The filtered data
    """
    if list_type_game == [] :
        return data
    return data.loc[data["gameType"].isin(list_type_game)]

def filter_data_team_side(data : pd.DataFrame, team_side : list, team_dict : dict) -> pd.DataFrame :
    """Filter data on the ally team side.

    Args:
        data (pd.DataFrame): The input data
        team_side (list): The side selected example : ["Blue","Red"]
        team_dict (dict): Dictionnary containing PUUID. Example = {"TOP" : ["9df5d86"], "JUNGLE" : ...}

    Returns:
        pd.DataFrame: The filtered data
    """
    if team_side == [] :
        return data
    team_side_mapping = {
        "Blue" : "100",
        "Red" : "200"
    }

    mapped_team_side = [team_side_mapping[side] for side in team_side if side in team_side_mapping]
    team_data = filter_data_on_team(data,team_dict=team_dict)
    team_side_data = team_data.loc[team_data["TEAM"].isin(mapped_team_side)]

    return data.loc[data["_id"].isin(team_side_data["_id"].unique())]

def get_mean_winrate(data : pd.DataFrame) -> float:
    """Get mean of winrate on global team data

    Args:
        data (pd.DataFrame): Filtered team data

    Returns:
        float: The mean winrate of the team
    """
    return data.loc[(data['WIN']=='Win'),"WIN"].count() / len(data) * 100


def get_mean_duration(data : pd.DataFrame) -> int :
    """Get mean duration of games

    Args:
        data (pd.DataFrame): The filtered dataframe

    Returns:
        int: The mean duration of the team's games
    """
    return int(data["gameDuration"].mean() /60000)

# %%
def get_winrate_by_side(data : pd.DataFrame, chart = False) :
    """Compute winrate in blue and red side for a dataFrame (usage with team filter)

    Args:
        data (pd.DataFrame): Filtered team data
        chart : Show the figure plot

    Returns:
        _type_: Return dict of both winrate side
    """
    winrate_blue = data.loc[(data['WIN']=='Win') & (data['TEAM']=='100'),'WIN'].count() / len(data.loc[data['TEAM']=='100']) * 100
    winrate_red = data.loc[(data['WIN']=='Win') & (data['TEAM']=='200'),'WIN'].count() / len(data.loc[data['TEAM']=='200']) * 100
    winrate_blue = round(float(winrate_blue),2)
    winrate_red = round(float(winrate_red),2)

    if chart : 
        fig = plty.bar(x=['Blue','Red'], y=[winrate_blue,winrate_red], labels={"x" : "Side", "y" : "Winrate (%)"}, text_auto=True)
        fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))
        fig.update_traces(marker_color=['#215FAB', '#AB2821'])
        return fig
    return {"blue" : winrate_blue , "red" : winrate_red}


def get_winrate_by_side_every_two_weeks(data : pd.DataFrame, chart = False) :
    """Function to have the winrate by side every to weeks. Teh chart also containg global winrate.

    Args:
        data (pd.DataFrame): The filtered dataframe from team's data
        chart (bool, optional): Chose to display chart or not. Defaults to False.

    Returns:
        A pandas DataFrame or a plolty chart.
    """
    # retrive date_time regexpour clear numero de game tranformen format bien puis boucler dessus
    data = data.copy()
    data['formatted_date'] = data['jsonFileName'].apply(lambda x: datetime.strptime(x.split("_")[0], "%d%m%Y").strftime("%d-%m-%Y"))
    data['week_of_the_year'] = data['formatted_date'].apply(lambda x: datetime.strptime(x, "%d-%m-%Y").isocalendar()[1])

    data['paired_week'] = data['week_of_the_year'].apply(lambda x: x + 1 if x % 2 != 0 else x)
    #print("Semaines disponibles dans data :", data['week_of_the_year'].unique())
    winrate_blue = (
        data.loc[(data['WIN'] == 'Win') & (data['TEAM'] == '100')]
        .groupby('paired_week')['WIN'].count() /
        data.loc[data['TEAM'] == '100'].groupby('paired_week')['WIN'].count() * 100
    ).rename("Blue")

    winrate_red = (
        data.loc[(data['WIN'] == 'Win') & (data['TEAM'] == '200')]
        .groupby('paired_week')['WIN'].count() /
        data.loc[data['TEAM'] == '200'].groupby('paired_week')['WIN'].count() * 100
    ).rename("Red")

    winrate_global = (
        data.loc[(data['WIN'] == 'Win')]
        .groupby('paired_week')['WIN'].count() /
        data.groupby('paired_week')['WIN'].count() * 100
    )

    count_game = data.drop_duplicates(subset="_id",keep="last").groupby(['paired_week'])['WIN'].count()

    df_winrate = pd.concat([winrate_blue, winrate_red], axis=1).reset_index()
    df_winrate.rename(columns={"paired_week": "Week"}, inplace=True)
    df_winrate_long = df_winrate.melt(id_vars=["Week"], var_name="Side", value_name="Winrate (%)").fillna(0)

    if chart:
        color_discrete_map = {"Blue" : "blue", "Red" : "red"}
        fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
        for side, color in color_discrete_map.items():
            fig.add_trace(go.Scatter(
                x=df_winrate_long[df_winrate_long["Side"] == side]["Week"],
                y=df_winrate_long[df_winrate_long["Side"] == side]["Winrate (%)"],
                mode="lines",
                name=side,
                line=dict(color=color),
                zorder=2
            ))
        fig.update_layout(yaxis_range=[0, 100])
        fig.add_trace(go.Scatter(x=winrate_global.index,y=winrate_global.values,mode="lines",name="Global",line=dict(color="purple"),zorder=2))
        fig.add_trace(go.Bar(x=count_game.index, y=count_game.values, name="Number of games", marker_color='rgb(122, 115, 113)',opacity=0.6, zorder=1),secondary_y=True)
        fig.update_yaxes(title_text='Winrate by side (%)')
        fig.update_yaxes(title_text='Number of games', secondary_y=True)

        return fig
    return df_winrate


# %%
# get_winrate_by_side(scl, chart=True)


# %%
def table_winrate_champs(data : pd.DataFrame) :
    """Retrieve and groupby champion from the dataFrame and get number of game and number of win (+winrate). Use this with filtered data.

    Args:
        data (pd.DataFrame): The filtered DataFrame

    Returns:
        list : List from TOP to SUPPORT champions game and winrate
    """
    positions = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
    top_to_bot_champs = []
    for position in positions :

        all = data.loc[data['TRUE_POSITION'] == position].groupby("SKIN")['WIN'].count()
        win = data.loc[(data['TRUE_POSITION'] == position) & (data['WIN'] == 'Win')].groupby("SKIN")['WIN'].count()

        df_player = pd.DataFrame(data= {'Count' : all,'Win' : win}).fillna(0)
        df_player = df_player.astype({'Win' : int})
        df_player['Winrate (%)'] = ((df_player['Win'] / df_player['Count']) * 100).round(2)
        df_player.sort_values(by='Count',ascending=False,inplace=True)
        df_player.index = df_player.index.map(utils.get_champion_image_from_id)
        df_player = df_player.style.format({'Winrate (%)': '{:.2f}'}).background_gradient(subset=['Winrate (%)'], cmap='RdYlGn', vmin=0, vmax=100)
        top_to_bot_champs.append(df_player)   
        #to add conditionnal formatting
    return top_to_bot_champs

# %%
# print(table_winrate_champs(data_scrim_matches))


# %%
def get_nb_pink_bought(data : pd.DataFrame, chart=False) -> list : 
    """Function to get the median number of pink bought in all games role by role.

    Args:
        data (pd.DataFrame): The filtered DataFrame
        chart (boolean) : Display the chart

    Returns:
        list: List role by role (top - supp) of the median of pink
    """
    
    positions = ["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]
    top_to_bot_pink_median = []

    for position in positions :
        top_to_bot_pink_median.append(data.loc[data['TRUE_POSITION'] == position, 'VISION_WARDS_BOUGHT_IN_GAME'].median())
    
    if chart :
        fig = plty.bar(x=positions, y=top_to_bot_pink_median, labels={"x" : "Positions", "y" : "Median nb of pink"})
        fig.update_traces(marker_color='#f2214a',marker_line_color='black', marker_line_width=1.5)
        return fig
    return top_to_bot_pink_median


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


def get_jungler_puuid(data: pd.DataFrame, jungler_filter: list = None, team_dict: dict = None) -> pd.DataFrame:
    """Get the jungler PUUID from the data.

    Args:
        data (pd.DataFrame): The filtered DataFrame.
        jungler_filter (list): List of jungler PUUIDs to keep.
        team_dict (dict): Dictionary containing PUUIDs.

    Returns:
        pd.DataFrame: Filtered DataFrame with original column names if empty.
    """
    if data.empty:
        return pd.DataFrame(columns=data.columns)

    if not jungler_filter or not team_dict:
        return data

    puuids = []
    if "Old Jungler" in jungler_filter:
        puuids += st.secrets["TEAM_SCRIM_ID"]["JUNGLE"]
    if "New Jungler" in jungler_filter:
        puuids += st.secrets["TEAM_SCRIM_ID"]["JUNGLE_2"]

    team_puuids = []
    for v in team_dict.values():
        team_puuids += v

    def keep_row(row):
        if row["TRUE_POSITION"] != "JUNGLE":  # If player is not jungler, return True
            return True
        if row["PUUID"] not in team_puuids:  # If PUUID is not in team, return True (enemy)
            return True
        return row["PUUID"] in puuids  # If jungler is ally, return PUUID

    mask = data.apply(keep_row, axis=1)
    filtered_data = data[mask]

    # Ensure column names are preserved if the result is empty
    return filtered_data if not filtered_data.empty else pd.DataFrame(columns=data.columns)

# get_nb_pink_bought(scl, chart=True)


# %%
def calculate_matchup_winrate(data: pd.DataFrame, team_dict: dict, role: str, enemy_dict: dict = None, position_filter: str = None) -> pd.DataFrame:
    """
    Calculate the winrate of a specific role in matchups.

    Args:
        data (pd.DataFrame): The DataFrame containing the match data.
        team_dict (dict): Dictionary mapping roles to player PUUIDs.
        role (str): Role to analyze (e.g., "TOP", "JUNGLE").
        chart (bool): Whether to display the result as a chart (currently not implemented).
        enemy_dict (dict): Dictionnary mapping role to enemy PUUIDs.
        position_filter (str): Optionally specify a position to filter the allies by (e.g., "TOP"). If None, no position filter is applied.

    Returns:
        pd.DataFrame: A DataFrame containing winrates for each matchup.
    """
    # Retrieve allied data for the specified position
    if position_filter:
        role_data = data[(data['PUUID'].isin(team_dict[role])) & (data['TRUE_POSITION'] == position_filter)][['_id', 'SKIN', 'WIN']]
    else:
        role_data = data[data['PUUID'].isin(team_dict[role])][['_id', 'SKIN', 'WIN']]

    # Retrieve the direct opponents in the specified position
    if enemy_dict :
        opponent_data = data[           
            (data['TRUE_POSITION'] == role) & 
            (data['PUUID'].isin(enemy_dict[role]))  # get the enemy team dict
        ][['_id', 'SKIN']].rename(columns={'SKIN': 'ENEMY_CHAMPION'})
    else :
        opponent_data = data[
            (data['TRUE_POSITION'] == role) & 
            (~data['PUUID'].isin(team_dict[role]))  # Exclude allies
        ][['_id', 'SKIN']].rename(columns={'SKIN': 'ENEMY_CHAMPION'})


    # Merge on "_id"
    merged_data = pd.merge(role_data, opponent_data, on='_id')

    # Group : calculate the number of games played and the wins
    matchup_stats = merged_data.groupby(['SKIN', 'ENEMY_CHAMPION']).agg(
        GAMES=('WIN', 'count'),
        WINS=('WIN', lambda x: (x == 'Win').sum())  # Count the wins
    ).reset_index()

    # Winrate
    matchup_stats['Winrate (%)'] = (matchup_stats['WINS'] / matchup_stats['GAMES']) * 100
    matchup_stats.rename({"SKIN": "ALLY_CHAMPION"},axis=1,inplace=True)
    # Sort ny number of games played
    matchup_stats = matchup_stats.sort_values(by='GAMES', ascending=False)
    matchup_stats_style = matchup_stats.style.background_gradient(subset=['Winrate (%)'], cmap='RdYlGn', vmin=0, vmax=100)

    # display(matchup_stats) 

    return matchup_stats , matchup_stats_style




def calculate_duo_winrate(filtered_data: pd.DataFrame, roles: tuple = ("MIDDLE", "JUNGLE")) -> pd.DataFrame:
    """
    Calculate winrate for champion duos in specified roles using pre-filtered data.

    Args:
        filtered_data (pd.DataFrame): The DataFrame already filtered for the team's matches.
        roles (tuple): Roles to analyze (e.g., ("MIDDLE", "JUNGLE")).

    Returns:
        pd.DataFrame: A DataFrame containing winrates for each duo.
    """
    # Extract the data for each role
    role1_data = filtered_data[filtered_data['TRUE_POSITION'] == roles[0]][['_id', 'SKIN', 'WIN']].rename(
        columns={'SKIN': f"{roles[0]}_CHAMPION"}
    )
    role2_data = filtered_data[filtered_data['TRUE_POSITION'] == roles[1]][['_id', 'SKIN']].rename(
        columns={'SKIN': f"{roles[1]}_CHAMPION"}
    )

    # Merge the two roles' data on '_id' (mongo attribute)
    duo_data = pd.merge(role1_data, role2_data, on="_id")

    # Group by the duo of champions and calculate stats
    duo_stats = duo_data.groupby([f"{roles[0]}_CHAMPION", f"{roles[1]}_CHAMPION"]).agg(
        GAMES=('WIN', 'count'),
        WINS=('WIN', lambda x: (x == 'Win').sum())  # Count the wins
    ).reset_index()

    # Calculate the winrate
    duo_stats['Winrate (%)'] = (duo_stats['WINS'] / duo_stats['GAMES']) * 100
    duo_stats[f"{roles[0]}_CHAMPION"] = duo_stats[f"{roles[0]}_CHAMPION"].map(utils.get_champion_image_from_id)
    duo_stats[f"{roles[1]}_CHAMPION"] = duo_stats[f"{roles[1]}_CHAMPION"].map(utils.get_champion_image_from_id)
    # Sort by the number of games played
    duo_stats = duo_stats.sort_values(by='GAMES', ascending=False)
    duo_stats = duo_stats.style.format({'Winrate (%)': '{:.2f}'}).background_gradient(subset=['Winrate (%)'], cmap='RdYlGn', vmin=0, vmax=100)

    return duo_stats

# def get_unique_ally_champions_by_role(data : pd.DataFrame , ):


## KDA calcul
def compute_kda_team(filtered_data : pd.DataFrame, chart : bool =False) -> pd.DataFrame :
    """Get the KDA for a team for each game

    Args:
        filtered_data (pd.DataFrame): The input filtered dataframe containing team games data
        chart (bool, optional): If true, retrun a figure. Defaults to False.

    Returns:
        pd.DataFrame: The KDA pivot table dataframe
    """
    data = filtered_data.copy()
    data = data.dropna(subset=["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"])
    data.loc[:, ["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"]] = data.loc[:, ["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"]].astype(int)
    data.loc[:,"kda"] = (data["CHAMPIONS_KILLED"] + data["ASSISTS"]) / data["NUM_DEATHS"].replace(0,1)
    kda_team = data.pivot_table(index='_id',columns="TRUE_POSITION",values="kda",aggfunc='mean')[["TOP","JUNGLE","MIDDLE","BOTTOM","UTILITY"]]
    
    if chart :
        kda_team_avg = kda_team.mean()
        kda_team_med = kda_team.median()
        fig = go.Figure(
            data=[
                go.Bar(name='Mean KDA', x=kda_team_avg.index, y=kda_team_avg.values,marker_color="#D5C381"),
                go.Bar(name='Median KDA', x=kda_team_med.index, y=kda_team_med.values,marker_color="#93D581") 
            ],
            layout=go.Layout(
                title="Average and Median KDA by Position",
                xaxis_title="Position",
                yaxis_title="KDA",
            )
        )
        return fig
    return kda_team

def compute_kda_per_champion(filtered_data : pd.DataFrame) -> list :
    """Get the KDA for each role each champion

    Args:
        filtered_data (pd.DataFrame): The input filtered data

    Returns:
        list: A list containing from TOP to UTILITY the pandas dataframe containing the data
    """

    data = filtered_data.copy()
    data = data.dropna(subset=["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"])
    data.loc[:, ["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"]] = data.loc[:, ["CHAMPIONS_KILLED", "NUM_DEATHS", "ASSISTS"]].astype(int)
    data.loc[:,"kda"] = (data["CHAMPIONS_KILLED"] + data["ASSISTS"]) / data["NUM_DEATHS"].replace(0,1)
    
    list_dataframe_kda = [0] * 5
    for idx, position in enumerate(["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]):
        df = data.loc[data["TRUE_POSITION"] == position].groupby("SKIN").agg(
            KDA=( "kda", lambda x: round(x.mean(), 2) ),
            Count=( "kda", "count" )
        )
        df.sort_values(by='Count',ascending=False,inplace=True)
        max_kda = df['KDA'].max()
        avg_kda = df['KDA'].mean()
        df["KDA relatif"] = df["KDA"]/avg_kda

        max_kda_relatif = df['KDA relatif'].max()
        df = df[["Count","KDA","KDA relatif"]]
        df = df.style.format({'KDA': '{:.2f}', 'KDA relatif': '{:.2f}'}).background_gradient(subset=['KDA'], cmap='RdYlGn', vmin=0, vmax=max_kda).background_gradient(subset=['KDA relatif'], cmap='RdYlGn', vmin=0, vmax=max_kda_relatif)
        list_dataframe_kda[idx] = df

    return list_dataframe_kda

def history(data : pd.DataFrame, dict_name : dict) -> pd.DataFrame :
    """Create a pandas table, history of scrim games, game will be filtered when we don"t have all data

    Args:
        data (pd.DataFrame): All data table
        dict_name (dict): Dict of matching Name player with role Example : {Filou : BOTTOM}

    Returns:
        pd.DataFrame: History dataframe
    """
    
    def get_enemy_value(row, role):
        ally_team = int(row["ALLY_TEAM__"])
        enemy_team = 300 - ally_team

        col_name = f"SKIN_{enemy_team}_{role}"

        return row[col_name] if col_name in row else None
    
    def get_enemy_kill(row) :
        ally_team = int(row["ALLY_TEAM__"])
        enemy_team = 300 - ally_team       
        
        col_name = f"TOTALKILL_TEAM_{enemy_team}__"
        return row[col_name] if col_name in row else None

    def detect_ally_team(row, ally_dict):
        puuid_cols = row["PUUID"]

        for team in ["100", "200"]:
            for position in ally_dict.keys():

                col = (team, position)

                if col not in puuid_cols.index:
                    continue

                puuid_value = puuid_cols[col]

                if pd.isna(puuid_value):
                    continue

                if puuid_value in ally_dict[position]:
                    return int(team)

        return None
    
    df_columns = data[["_id","WIN","TEAM","PUUID","TRUE_POSITION","SKIN","CHAMPIONS_KILLED","gameDuration","enemyTeamName","jsonFileName","patchVersion"]].dropna().astype({
        "CHAMPIONS_KILLED" : int
    })
    pivot = df_columns.pivot(
        index="_id",
        columns=["TEAM","TRUE_POSITION"],
        values=["SKIN","PUUID","WIN","CHAMPIONS_KILLED"]
    )


    pivot["TOTALKILL_TEAM_100"] = (
        pivot["CHAMPIONS_KILLED"]
        .loc[:, ("100", slice(None))]
        .sum(axis=1)
    )
    pivot["TOTALKILL_TEAM_200"] = (
        pivot["CHAMPIONS_KILLED"]
        .loc[:, ("200", slice(None))]
        .sum(axis=1)
    )
    pivot["TEAM_WIN_100"] = (
        pivot["WIN"]
        .loc[:, ("100", slice(None))]
        .bfill(axis=1)
        .iloc[:, 0]
    )

    pivot["TEAM_WIN_200"] = (
        pivot["WIN"]
        .loc[:, ("200", slice(None))]
        .bfill(axis=1)
        .iloc[:, 0]
    )

    pivot["ALLY_TEAM"] = pivot.apply(
        detect_ally_team,
        axis=1,
        ally_dict=st.secrets["TEAM_SCRIM_ID"]
    )

    pivot = pivot.drop(["CHAMPIONS_KILLED","WIN"],axis=1)
    pivot.columns = ["_".join(col) for col in pivot.columns]


    merged = pivot.merge(data[["_id","gameDuration","enemyTeamName","datetime","patchVersion"]].drop_duplicates(subset="_id"),on="_id")

    for name,role in dict_name.items() :
        merged[name] = merged.apply(
            lambda row: row[f"SKIN_{int(row['ALLY_TEAM__'])}_{role}"],
            axis=1
        )
        merged[f"enemy_{role}"] = merged.apply(
            lambda row: get_enemy_value(row, role),
            axis=1
        )
        
    merged = merged.drop(
        [col for col in merged.columns if col.startswith("SKIN_")],
        axis=1
    )

    merged = merged.drop(
        [col for col in merged.columns if col.startswith("PUUID_")],
        axis=1
    )

    merged["Win"] = merged.apply(
        lambda row : row[f"TEAM_WIN_{int(row['ALLY_TEAM__'])}__"],
        axis=1
    )

    merged["gameDuration"] = merged["gameDuration"] / 60000

    merged["TOTAL_ALLY_KILL"] = merged.apply(
        lambda row : row[f"TOTALKILL_TEAM_{int(row['ALLY_TEAM__'])}__"],
        axis=1
    )
    
    merged["TOTAL_ENEMY_KILL"] = merged.apply(
        lambda row: get_enemy_kill(row),
        axis=1
    )
    merged = merged.drop(
        [col for col in merged.columns if col.startswith("TEAM_WIN_")],
        axis=1
    )

    merged["gameDuration"] = pd.to_numeric(
        merged["gameDuration"],
        errors="coerce"
    ).round(0)

    merged["ALLY_TEAM__"] = merged["ALLY_TEAM__"].replace({
        100 : "Blue",
        200 : "Red"
    })
    return merged.drop(["_id","TOTALKILL_TEAM_100__","TOTALKILL_TEAM_200__"],axis=1).sort_values("datetime",ascending=False)

