import requests
import pandas as pd
from dotenv import load_dotenv
import os
import sqlite3
import datetime
import sqlitecloud
load_dotenv()

API_KEY = os.getenv("API_KEY")
DB_CONNECTION_STRING = os.getenv("SOLOQ_DB_ADMIN_CONNECTION_STRING")
tiers = {
    'IRON': 0,
    'BRONZE': 400,
    'SILVER': 800,
    'GOLD': 1200,
    'PLATINUM': 1600,
    'EMERALD' : 2000,
    'DIAMOND': 2400,
    'MASTER': 2800
}

divisions = {
    'IV': 0,
    'III': 100,
    'II': 200,
    'I': 300
}
def adapt_datetime(val):
    """Convert datetime.datetime object to ISO 8601 string."""
    return val.isoformat()

def convert_datetime(val):
    """Convert ISO 8601 string to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

# Register the adapter and converter with sqlite3
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

sqlitecloud.register_adapter(datetime.datetime, adapt_datetime)
sqlitecloud.register_converter("datetime", convert_datetime)

def lol_rank_to_numeric(player_tier : str ,player_lp : int ,player_division : str = '' ) -> int : 
    """Transform the rank of a player into a numeric value

    Args:
        player_tier (str): Tier of the player. For example : "GOLD"
        player_lp (int): LP of the player.
        player_division (str, optional): Division of the player, for example : "II". Defaults to ''. No Division for MASTER+

    Returns:
        int: The numerical value of the rank of a player.
    """
    print(player_lp)
    if player_tier =='MASTER' or player_tier == 'GRANDMASTER' or player_tier == 'CHALLENGER':
        return 2800 + player_lp
    if player_division is None or player_tier is None or player_tier is None :
        return None
    return tiers[player_tier] + divisions[player_division] + player_lp

player_puuid = os.environ['LIST_PLAYER_PUUID'].split(",")

list_tracking_player = []
keys_dict = ["tier","rank","leaguePoints"]
for puuid in player_puuid :
    try :
        id_request = requests.get(f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={API_KEY}")
        id = id_request.json()['id']
    except Exception as  e:
        print("Erreur dans la récupération de l'id", id_request)
        exit()

    try :
        tracking_player_request = requests.get(f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/{id}?api_key={API_KEY}")
        tracking_player_json = tracking_player_request.json()
    except Exception as e:
        print("Erreur dans la récupération des informations du joueur", tracking_player_request)
        exit()
    
    rank_player = []
    for key in keys_dict:
        if len(tracking_player_json) ==0 :
            rank_player.append(None)
        else :
            rank_player.append(tracking_player_json[0].get(key))

    #FIXME when Master will be reached
    list_tracking_player.append(lol_rank_to_numeric(rank_player[0],rank_player[2],rank_player[1]))
print(list_tracking_player)


#Write in local (backup for the moment)
con = sqlite3.connect('soloq_tracking.db')
cursor = con.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS soloq_tracking (date TIMESTAMP PRIMARY KEY, TOP_RANK TEXT, JNG_RANK TEXT, MID_RANK TEXT, ADC_RANK TEXT, SUP_RANK TEXT)")
date_now = datetime.datetime.now()
cursor.execute("INSERT INTO soloq_tracking (date, TOP_RANK, JNG_RANK, MID_RANK, ADC_RANK, SUP_RANK) VALUES (?,?,?,?,?,?)",(date_now,list_tracking_player[0],list_tracking_player[1],list_tracking_player[2],list_tracking_player[3],list_tracking_player[4]))
con.commit()
con.close()


#Write in sqlitecloud
con = sqlitecloud.connect(DB_CONNECTION_STRING)
cursor = con.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS soloq_tracking (date TIMESTAMP PRIMARY KEY, TOP_RANK TEXT, JNG_RANK TEXT, MID_RANK TEXT, ADC_RANK TEXT, SUP_RANK TEXT)")
date_now = datetime.datetime.now()
cursor.execute("INSERT INTO soloq_tracking (date, TOP_RANK, JNG_RANK, MID_RANK, ADC_RANK, SUP_RANK) VALUES (?,?,?,?,?,?)",(date_now,list_tracking_player[0],list_tracking_player[1],list_tracking_player[2],list_tracking_player[3],list_tracking_player[4]))
con.commit()
con.close()