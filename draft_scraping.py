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

import pandas as pd 
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import time
import unicodedata
import re
from pymongo import MongoClient
import gspread
from dotenv import load_dotenv
import os
from itertools import chain


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


# -

# Team name constants

team_tags_dico = {
    "SCL" : ["scl","scald"],
    "IWG" : ["iwg"]
}

# Instanciate Selenium web browser

driver_options = webdriver.FirefoxOptions()
driver_options.add_argument("--headless")
driver = webdriver.Firefox(options=driver_options)


# ## Scraping functions

def getBlue_picks_bans(soup : BeautifulSoup ,name : str) -> tuple:
    """Scrap the blue picks and bans from the soup

    Args:
        soup (BeautifulSoup): The soup scraped from an URL
        name (str): The name of the team

    Returns:
        tuple: Tuple containing :
        - An ordenated list of picks
        - An ordenated list of bans
        - The name of the team
    """
    picks = soup.find(attrs={"class": "roomPickColumn blue"}).get_text("|")
    picks = picks.split("|")
    bans = [x['alt'] if 'alt' in x.attrs else "None" for x in soup.find(attrs={"class": "roomBanRow blue"}).find_all('img')]
    return picks,bans, name


def getRed_picks_bans(soup : BeautifulSoup ,name : str) -> tuple :
    """Scrap the red picks and bans from the soup

    Args:
        soup (BeautifulSoup): The soup scraped from an URL
        name (str): The name of the team

    Returns:
        tuple: Tuple containing :
        - An ordenated list of picks
        - An ordenated list of bans
        - The name of the team
    """
    picks = soup.find(attrs={"class": "roomPickColumn red"}).get_text("|")
    picks = picks.split("|")
    bans = [x['alt'] if 'alt' in x.attrs else "None" for x in soup.find(attrs={"class": "roomBanRow red"}).find_all('img')]
    return picks, bans, name


def detect_team_in_name(name : str,team_reference_dict : dict) -> str : 
    """Check if a name of a team side is recorded in the dictionnary

    Args:
        name (str): The scraped name of a team used in the URL.
        team_reference_dict (dict): The dict containing all the teams names.

    Returns:
        str: The tag of the team if it's already in the dictionnary.
            Otherwise, just the name
    """
    for tag, keywords in team_reference_dict.items():
        for  word in keywords :
            if word in name.lower()  :
                return tag
    return name


def extract_date(name : str) -> str:
    """Check in the team name scraped if there is a date and return it.

    Args:
        name (str): The scraped name of the ally team used in the URL.

    Returns:
        str: If there is a date, the date format : ddmmyyyy_nbgame
            Otherwise, NaT
    """
    match = re.search(r'\d', name)
    if match :
        digit_index = match.start()
        return name[digit_index:]
    return "NaT"


def get_side_by_tag(soup : BeautifulSoup ,team_reference_dict : dict) -> tuple :
    """Scrap the name of both team, get the tag if possible, the date and the side of each team.

    Args:
        soup (BeautifulSoup): The soup.
        team_reference_dict (dict): The dict containing all the teams names.

    Returns:
        tuple: Tuple containing :
            - Tag or name of the blue team
            - Tag or name of the red team
            - Date of the draft
    """

    blue_text = unicodedata.normalize("NFKD",soup.find(attrs={"class" : "roomReadyBackground roomReadyBackgroundblue"}).previous_sibling.get_text())
    red_text = unicodedata.normalize("NFKD",soup.find(attrs={"class" : "roomReadyBackground roomReadyBackgroundred"}).previous_sibling.get_text())
    blue_team = detect_team_in_name(blue_text, team_reference_dict)
    red_team = detect_team_in_name(red_text,team_reference_dict)

    if blue_team == "SCL" :
        game_date = extract_date(blue_text)
    elif red_team == "SCL" :
        game_date = extract_date(red_text)
    else :
        game_date = "NaT"
    return blue_team, red_team, game_date


def scraping_draft(draft_url : str,team_reference_dict : dict , mongo_collection):
    """Scrap a URL and get all the draft data. Insert data into a mongodb collection.

    Args:
        draft_url (str): Url of the draft (from https://draftlol.dawe.gg/)
        team_reference_dict (dict): The dict containing all the teams names.
        mongo_collection : The collection of where you store the drafts data

    Returns: The ID of the new object inserted in the database
    """
    driver.get(draft_url)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html,"html.parser")
    
    teams_names = get_side_by_tag(soup,team_reference_dict)

    blue = getBlue_picks_bans(soup,teams_names[0])
    red = getRed_picks_bans(soup,teams_names[1])

    draft_json = {
        "link" : draft_url,
        "date" : teams_names[2],
        "blue" : 
            {
                "picks" : blue[0],
                "bans"  : blue[1],
                "team"  : blue[2]
            },
        "red" :
            {
                "picks" : red[0],
                "bans"  : red[1],
                "team"  : red[2]
            }
        }

    return mongo_collection.insert_one(draft_json).inserted_id


def document_exist(draft_url : str, mongo_collection) -> bool :
    """Check if the URL already exist in one of the object of the collection.

    Args:
        draft_url (str): The URL of the draft.
        mongo_collection : The mongodb collection

    Returns:
        bool : Return True if the document exist
            False in the other case.
    """
    document = mongo_collection.find_one({"link" : draft_url})
    if document !=None :
        return True
    return False


# ## Main
# Get URL drafts from gsheets and check if the document already exist in the database

# +
load_dotenv()
gc = gspread.service_account(filename=os.getenv("GOOGLE_CREDENTIALS_PATH"))

sh = gc.open_by_key(os.getenv("SPREADSHEET_KEY"))

list_draft_url = list(chain.from_iterable(sh.worksheet("Historique de Scrim").get("L2:P")))

connect = connect_database('lol_match_database', host=os.getenv("ATLAS_CONNEXION_STRING"))
drafts_collection = get_collection(connect,"drafts")
list_draft_url = [x for x in list_draft_url if x != ""]
# -

#zip the list with URL and a list containing the result of DOCUMENT_EXIST function for that list
for url, exists in zip(list_draft_url, [document_exist(draft_url=url,mongo_collection=drafts_collection) for url in list_draft_url]) :
    if not exists :
        print(scraping_draft(draft_url=url,team_reference_dict=team_tags_dico, mongo_collection=drafts_collection))
        print(url)


