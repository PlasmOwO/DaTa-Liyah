# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import pandas as pd
from collections import Counter
import itertools
import plotly.express as plty
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from skimage import io
import requests
from io import BytesIO
import streamlit as st
from typing import Literal



# +
def connect_database(database_name : str, host : str) :
    """Create connexion to Mongo Database

    Args:
        database_name (str): Name of the database
        host (str) : host string of your database, null for localhost

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
    return df


# -

load_dotenv()
connect = connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
drafts = get_collection(connect,"drafts")
df = read_and_create_dataframe(drafts)


def count_champs_bans(data : pd.DataFrame, chart : bool = False) :
    """Count number of time a champion is banned for each side

    Args:
        data (pd.DataFrame): The dataframe containing the data (filtered or not)
        chart (bool, optional): Choice to display or not the chart. Defaults to False.

    Returns:
        
    """

    blue_bans = Counter(list(itertools.chain.from_iterable(data['blue.bans'])))
    red_bans = Counter(list(itertools.chain.from_iterable(data['red.bans'])))

    champions_bans_df = pd.DataFrame([blue_bans,red_bans]).T.rename(columns={0:'Blue',1:'Red'}).fillna(0)
    champions_bans_df['Blue'] = champions_bans_df['Blue'].astype(int)
    champions_bans_df['Red'] = champions_bans_df['Red'].astype(int)
    champions_bans_df['total'] = champions_bans_df['Blue'] + champions_bans_df['Red']

    champions_bans_df.sort_values(by=['total'],ascending=True,inplace=True)

    if chart :
        fig = plty.histogram(champions_bans_df,y=champions_bans_df.index, x= ["Blue","Red"], orientation='h',title="Champions bans", width=1500, height=800)
        
        #add image champions
        for champion in champions_bans_df.index :
            fig.add_layout_image(
                dict(
                    source="https://cdn.communitydragon.org/latest/champion/"+champion+"/square",
                    xref="x",
                    yref="y",
                    x=0,
                    y=champion,
                    sizex=0.5,
                    sizey=0.5,
                    xanchor="left",
                    yanchor="middle"
                ))
        fig.update_layout(
            xaxis_title="Number of bans",
            yaxis_title="Champions",
            legend_title="Side")
        return fig

    return champions_bans_df


def count_champs_bansv2(data : pd.DataFrame, chart : bool = False) :
    """Count number of time a champion is banned for each side

    Args:
        data (pd.DataFrame): The dataframe containing the data (filtered or not)
        chart (bool, optional): Choice to display or not the chart. Defaults to False.

    Returns:
        
    """

    blue_bans = Counter(list(itertools.chain.from_iterable(data['blue.bans'].dropna())))
    red_bans = Counter(list(itertools.chain.from_iterable(data['red.bans'].dropna())))

    champions_bans_df = pd.DataFrame([blue_bans,red_bans]).T.rename(columns={0:'Blue',1:'Red'}).fillna(0)
    champions_bans_df['Blue'] = champions_bans_df['Blue'].astype(int)
    champions_bans_df['Red'] = champions_bans_df['Red'].astype(int)
    champions_bans_df['total'] = champions_bans_df['Blue'] + champions_bans_df['Red']

    champions_bans_df.sort_values(by='total',ascending=False,inplace=True)

    if chart :
        max_cols = 30  # Maximum number of columns
        num_rows = -(-len(champions_bans_df.index) // max_cols)  
        
        champion_index = 0
        for row in range(num_rows):
            cols = st.columns(max_cols)
            for col in cols:
                if champion_index < len(champions_bans_df.index):
                    champion = champions_bans_df.index[champion_index]
                    champion = champion.replace(" ", "")
                    champion = champion.replace("'", "")
                    if champion == "Wukong":
                        champion = "MonkeyKing"
                    elif champion =="RenataGlasc":
                        champion = "Renata"
                    col.image("https://cdn.communitydragon.org/latest/champion/"+champion+"/square",width=50)
                    col.markdown(f"<p style='text-align: center'>{champions_bans_df['total'].iloc[champion_index]}</p>", unsafe_allow_html=True)
                    champion_index += 1
                else :
                    break
                
        return None

    else : 
        return champions_bans_df


# count_champs_bansv2(df, chart=True)


# Merge function
def merge_scrim_with_draft(df_scrim : pd.DataFrame, df_draft : pd.DataFrame) -> pd.DataFrame :
    """Merge scrim data with draft data based on the date of the match (i.e : 03022025_2)

    Args:
        df_scrim (pd.DataFrame): DataFrame contaning the scrim data (json from rofl)
        df_draft (pd.DataFrame): DataFrame containing the draft data from scraping.

    Returns:
        pd.DataFrame: The merged DataFrame (left merge)
    """
    df_draft['date'] = df_draft['date'].apply(lambda x : x.replace(" ",""))
    return df_scrim.merge(df_draft, how='left', left_on="jsonFileName",right_on="date")
# +
# count_champs_bans(df,chart=True)

# +

def filter_drafts(df_draft : pd.DataFrame, ally_team_tag : str,view : Literal["Both","Enemies Bans","Allies bans"] = "Both") -> pd.DataFrame:
    """Function for filtering drafts bases on the ally or enemy view

    Args:
        df_draft (pd.DataFrame): The dataframe containing draft info
        ally_team_tag (str): The tag of the team considered as ally
        view (Literal[Both;Enemies Bans;Allies bans], optional): The filter, with use with streamlit button. Defaults to "Both".

    Returns:
        pd.DataFrame: DataFrame containing columns with blue bans and columns with red bans, filtered.
    """
    if view == "Both" :
        blue_bans = df_draft[['blue.bans']]
        red_bans = df_draft[['red.bans']]
    elif view == "Enemies bans" :
        #Filter on enemies ban where we played vs them
        blue_bans = df_draft.loc[(df_draft['blue.team']!=ally_team_tag) & (df_draft['red.team']==ally_team_tag),['blue.bans']]
        red_bans = df_draft.loc[(df_draft['red.team']!= ally_team_tag) & (df_draft['blue.team']==ally_team_tag),['red.bans']]

    elif view == "Allies bans" :
        blue_bans = df_draft.loc[df_draft['blue.team']== ally_team_tag,['blue.bans']]
        red_bans = df_draft.loc[df_draft['red.team']== ally_team_tag,['red.bans']]

    return pd.concat([blue_bans,red_bans])

def filter_by_team_and_side(collection, team_name: str, side: str):
    """
    Filters drafts based on team and side (blue/red).

    Args:
        collection: MongoDB collection containing the drafts.
        team_name (str): The name of the team to filter for.
        side (str): 'blue' or 'red'.

    Returns:
        list: A list of drafts matching the specified criteria.
    """
    # Construct the filter query based on the specified side
    if side.lower() == "blue":
        # Filter for drafts where the team is on the blue side
        filter_query = {"blue.team": team_name}
    elif side.lower() == "red":
        # Filter for drafts where the team is on the red side
        filter_query = {"red.team": team_name}
    else:
        # Raise an error if the side is not 'blue' or 'red'
        raise ValueError("Side must be 'blue' or 'red'.")

    # Execute the query and retrieve the drafts matching the filter
    drafts = list(collection.find(filter_query))

    # Return the filtered drafts as a list
    return drafts



# +
# blue_side_scl=filter_by_team_and_side(draft_collection,"SCL","blue")
# red_side_scl=filter_by_team_and_side(draft_collection," Kinder Ratio ","red")
#display(blue_side_scl)
#display(red_side_scl)
# -

def calculate_pick_ban_counts(
    drafts_list, min_picks=None, max_picks=None, min_bans=None,
    max_bans=None, min_presence=None, max_presence=None
):
    """
    Calculates the number of picks, bans, and the total presence of champions,
    sorted by presence, then pick count, and finally alphabetical order.

    Args:
        drafts_list (list or list of lists): List containing one or more sets of drafts.
        min_picks (int): Minimum number of picks to include.
        max_picks (int): Maximum number of picks to include.
        min_bans (int): Minimum number of bans to include.
        max_bans (int): Maximum number of bans to include.
        min_presence (int): Minimum number of presences (picks + bans) to include.
        max_presence (int): Maximum number of presences (picks + bans) to include.

    Returns:
        pd.DataFrame: DataFrame containing filtered champion statistics.
    """
    import pandas as pd
    from collections import Counter

    # If drafts_list is not a list of lists, wrap it in another list for consistency
    if isinstance(drafts_list, list) and not isinstance(drafts_list[0], list):
        drafts_list = [drafts_list]

    # Counters to track picks and bans across all drafts
    pick_counter = Counter()
    ban_counter = Counter()

    # Iterate through each set of drafts
    for drafts in drafts_list:
        for draft in drafts:
            # Count blue and red picks
            pick_counter.update(draft['blue']['picks'])
            pick_counter.update(draft['red']['picks'])
            # Count blue and red bans
            ban_counter.update(draft['blue']['bans'])
            ban_counter.update(draft['red']['bans'])

    # Build a list of champions with their statistics
    champions = set(pick_counter.keys()).union(set(ban_counter.keys()))
    stats = []

    for champ in champions:
        picks = pick_counter[champ]
        bans = ban_counter[champ]
        presence = picks + bans

        stats.append({
            'Champion': champ,       # Name of the champion
            'Presence': presence,    # Total presence (picks + bans)
            'Pick Count': picks,     # Number of times picked
            'Ban Count': bans        # Number of times banned
        })

    # Convert the statistics into a DataFrame
    df = pd.DataFrame(stats)

    # Apply filters for picks, bans, and presence
    if min_picks is not None:
        df = df[df['Pick Count'] >= min_picks]  # Filter champions with at least min_picks
    if max_picks is not None:
        df = df[df['Pick Count'] <= max_picks]  # Filter champions with at most max_picks
    if min_bans is not None:
        df = df[df['Ban Count'] >= min_bans]    # Filter champions with at least min_bans
    if max_bans is not None:
        df = df[df['Ban Count'] <= max_bans]    # Filter champions with at most max_bans
    if min_presence is not None:
        df = df[df['Presence'] >= min_presence] # Filter champions with at least min_presence
    if max_presence is not None:
        df = df[df['Presence'] <= max_presence] # Filter champions with at most max_presence

    # Sort the DataFrame by Presence (descending), Pick Count (descending), and Champion (alphabetically)
    df = df.sort_values(by=['Presence', 'Pick Count', 'Champion'], ascending=[False, False, True])

    return df


# pick_ban_stats=calculate_pick_ban_counts(blue_side_scl)


# def add_champion_icons(df):
#     """
#     Adds URLs for champion icons with correction for champion names.

#     Args:
#         df (pd.DataFrame): DataFrame containing the names of the champions.

#     Returns:
#         pd.DataFrame: DataFrame with an additional column for champion icons.
#     """
#     # Base URL for the champion icons
#     base_url = "https://ddragon.leagueoflegends.com/cdn/14.24.1/img/champion/"
    
#     # Mapping to correct champion names for the API
#     champion_name_corrections = {
#         "Dr. Mundo": "DrMundo",
#         "Cho'Gath": "Chogath",
#         "Kai'Sa": "Kaisa",
#         "Kha'Zix": "Khazix",
#         "LeBlanc": "Leblanc",
#         "Nunu & Willump": "Nunu",
#         "Vel'Koz": "Velkoz",
#         "Wukong": "MonkeyKing",
#         "Rek'Sai": "RekSai",
#         "Tahm Kench": "TahmKench",
#         "Aurelion Sol": "AurelionSol",
#         "Xin Zhao": "XinZhao",
#         "K'Sante": "KSante",
#         "Miss Fortune": "MissFortune"
#         # Add more corrections if needed
#     }
    
#     # Apply corrections to champion names
#     df["Corrected Champion"] = df["Champion"].apply(
#         lambda x: champion_name_corrections.get(x, x)
#     )
    
#     # Create a new column 'Icon' with the corrected URLs
#     df["Icon"] = df["Corrected Champion"].apply(lambda x: f"{base_url}{x}.png")
    
#     # Return the updated DataFrame
#     return df



# +
# pick_ban_stats=add_champion_icons(pick_ban_stats)

# +
# from IPython.display import display, HTML

# def display_champions_table_with_stats(stats):
#     """
#     Displays an HTML table with champion icons, names, and their statistics.

#     Args:
#         stats (pd.DataFrame): DataFrame containing champion statistics.

#     Returns:
#         None: Displays the table directly in a Jupyter Notebook.
#     """
#     # Initialize the HTML content for the table container
#     html = "<div style='display: flex; flex-wrap: wrap;'>"
    
#     # Iterate through each row in the DataFrame
#     for _, row in stats.iterrows():
#         # Add a champion card for each row with icon, name, and stats
#         html += f"""
#         <div style='margin: 5px; text-align: center;'>
#             <img src='{row["Icon"]}' style='width: 50px; height: 50px; border-radius: 5px;'><br>
#             <span style='font-size: 12px; font-weight: bold;'>{row["Champion"]}</span><br>
#             <span style='font-size: 10px;'>Picks: {row["Pick Count"]}</span><br>
#             <span style='font-size: 10px;'>Bans: {row["Ban Count"]}</span><br>
#             <span style='font-size: 10px;'>Presence: {row["Presence"]}</span>
#         </div>
#         """
    
#     # Close the container
#     html += "</div>"
    
#     # Display the generated HTML
#     display(HTML(html))


# +
# display_champions_table_with_stats(pick_ban_stats)
# -

def calculate_pick_priority(drafts, team_name, side):
    """
    Calculates pick priorities for a team, focusing on specific positions:
    B1, B2/B3 for the blue side, and R1/R2 for the red side.

    Args:
        drafts (list): List of drafts (typically filtered by `filter_by_team_and_side`).
        team_name (str): Name of the team for which to calculate priorities.
        side (str): "blue" or "red".

    Returns:
        pd.DataFrame: DataFrame containing champions and their frequencies for specified positions.
    """
    from collections import Counter
    import pandas as pd

    # Validate the side parameter
    if side not in ["blue", "red"]:
        raise ValueError("The 'side' parameter must be 'blue' or 'red'.")

    # Filter drafts to only include those where the team is on the specified side
    team_drafts = [draft for draft in drafts if draft[side]["team"] == team_name]

    # Initialize counters for specific positions
    position_counters = {"B1": Counter(), "B2_B3": Counter(), "R1_R2": Counter()}

    # Iterate through the drafts to collect picks for each position
    for draft in team_drafts:
        picks = draft[side]["picks"]
        if side == "blue":
            # Count picks for B1 (first pick) and B2/B3 (second and third picks)
            if len(picks) > 0:
                position_counters["B1"].update([picks[0]])  # First pick (blue1)
            if len(picks) > 1:
                position_counters["B2_B3"].update(picks[1:3])  # Second and third picks (blue2, blue3)
        elif side == "red":
            # Count picks for R1 (first pick) and R2 (second pick)
            if len(picks) > 0:
                position_counters["R1_R2"].update([picks[0]])  # First pick (red1)
            if len(picks) > 1:
                position_counters["R1_R2"].update([picks[1]])  # Second pick (red2)

    # Build the data for the DataFrame
    data = []
    if side == "blue":
        # Combine data for B1 and B2/B3 positions
        for champ in position_counters["B1"].keys() | position_counters["B2_B3"].keys():
            data.append({
                "Champion": champ,
                "B1": position_counters["B1"][champ],
                "B2_B3": position_counters["B2_B3"][champ],
                "Total": position_counters["B1"][champ] + position_counters["B2_B3"][champ]
            })
    elif side == "red":
        # Only use R1/R2 data for the red side
        for champ in position_counters["R1_R2"].keys():
            data.append({
                "Champion": champ,
                "R1_R2": position_counters["R1_R2"][champ],
                "Total": position_counters["R1_R2"][champ]
            })

    # If no data is available, return an empty DataFrame with the appropriate columns
    if not data:
        return pd.DataFrame(columns=["Champion", "B1", "B2_B3", "R1_R2", "Total"][:3 if side == "red" else 4])

    # Create the DataFrame
    df = pd.DataFrame(data)

    # Sort the data
    if side == "blue":
        # Sort by Total (descending), then by B1 (descending)
        df = df.sort_values(by=["Total", "B1"], ascending=[False, False])
    elif side == "red":
        # Sort by Total (descending)
        df = df.sort_values(by="Total", ascending=False)

    # Return the sorted DataFrame
    return df.fillna(0)



# +
# blue_side=filter_by_team_and_side(draft_collection,"SCL","blue")
# red_side=filter_by_team_and_side(draft_collection," Kinder Ratio ","red")
# calculate_pick_priority(blue_side,"SCL",'blue')
# #calculate_pick_priority(blue_side_scl," Kinder Ratio ","red")
# -

def calculate_ban_priority_by_side(drafts, team_name, side):
    """
    Calculates the priority of the top three bans performed by a team on a specific side (blue or red).

    Args:
        drafts (list): List of drafts (typically filtered by `filter_by_team_and_side`).
        team_name (str): Name of the team for which to calculate ban priorities.
        side (str): "blue" or "red".

    Returns:
        pd.DataFrame: DataFrame containing champions banned by the team and their frequencies.
    """
    from collections import Counter
    import pandas as pd

    # Validate the side parameter
    if side not in ["blue", "red"]:
        raise ValueError("The 'side' parameter must be 'blue' or 'red'.")

    # Filter drafts to only include those where the team is on the specified side
    team_drafts = [draft for draft in drafts if draft[side]["team"] == team_name]

    # Counter for bans performed by the team
    ban_counter = Counter()

    # Iterate through the drafts to collect the top three bans
    for draft in team_drafts:
        bans = draft[side]["bans"][:3]  # Only consider the first three bans
        ban_counter.update(bans)

    # Build a DataFrame from the results
    data = [{"Champion": champ, "Frequency": freq} for champ, freq in ban_counter.items()]
    df = pd.DataFrame(data)

    # Sort by frequency (descending) and champion name (alphabetical order)
    return df.sort_values(by=["Frequency", "Champion"], ascending=[False, True])


# +
# blue_side=filter_by_team_and_side(draft_collection,"SCL","blue")
# red_side=filter_by_team_and_side(draft_collection," Kinder Ratio ","red")
# calculate_ban_priority_by_side(blue_side,"SCL",'blue')
