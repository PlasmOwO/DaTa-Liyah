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
import os
from dotenv import load_dotenv
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
    df['VISION_WARDS_BOUGHT_IN_GAME'] = df['VISION_WARDS_BOUGHT_IN_GAME'].astype('int')
    df['datetime'] = pd.to_datetime(df['jsonFileName'].apply(lambda x : x.split('_')[0]), format='%d%m%Y')
    return df


# %%
# connect = connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
# scrim_matches = get_collection(connect,"scrim_matches")
# data_scrim_matches = read_and_create_dataframe(scrim_matches)


# %%
def filter_data_on_team(data : pd.DataFrame,team_dict : dict) -> pd.DataFrame :
    """Filter data based on a team PUUID dictionnary

    Args:
        data (pd.DataFrame): Input data
        team_dict (dict): Dictionnary containing PUUID. Example = {"TOP" : ["9df5d86"], "JUNGLE" : ...}

    Returns:
        pd.DataFrame: The filtered DataFrame
    """
    return data.loc[data['PUUID'].apply(lambda puuid: any(puuid in sublist for sublist in team_dict.values()))]





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

    if chart : 
        fig = plty.bar(x=['Blue','Red'], y=[winrate_blue,winrate_red], labels={"x" : "Side", "y" : "Winrate (%)"})
        fig.show()
    return {"blue" : float(winrate_blue) , "red" : float(winrate_red)}


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
        df_player['Winrate'] = ((df_player['Win'] / df_player['Count']) * 100).round(2)
        

        top_to_bot_champs.append(df_player)    
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
        fig.show()
    return top_to_bot_pink_median


# %%
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
    matchup_stats['WINRATE'] = (matchup_stats['WINS'] / matchup_stats['GAMES']) * 100

    # Sort ny number of games played
    matchup_stats = matchup_stats.sort_values(by='GAMES', ascending=False)
    # display(matchup_stats) 

    return matchup_stats



# %%
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
    duo_stats['WINRATE'] = (duo_stats['WINS'] / duo_stats['GAMES']) * 100

    # Sort by the number of games played
    duo_stats = duo_stats.sort_values(by='GAMES', ascending=False)
    

    return duo_stats
