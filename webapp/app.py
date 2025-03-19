import streamlit as st
import plotly.express as plty
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb
from footer import footer
import yaml
from yaml import SafeLoader
import streamlit_authenticator as stauth
import pandas as pd
import os
import sys
import altair as alt
import datetime

#Import config :
st.set_page_config(layout="wide")

# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

## Welcome message

if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.title("Welcome to the League of Legends Dashboard")
else : 
    st.title(f"Welcome to the League of Legends Dashboard : *{st.session_state['name']}*")


## Login form yaml locally
# authenticator = stauth.Authenticate(config['credentials'],
#                                     config['cookie']['name'],
#                                     config['cookie']['key'],
#                                     config['cookie']['expiry_days']
#                                     )

## Login form with st secrets
authenticator = stauth.Authenticate(st.secrets['credentials'].to_dict(),
                                    st.secrets['cookie']['name'],
                                    st.secrets['cookie']['key'],
                                    st.secrets['cookie']['expiry_days']
                                    )

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
elif st.session_state['authentication_status'] is None:
    st.warning('Please enter your username and password')
elif st.session_state['authentication_status']:
    authenticator.logout(location='sidebar')
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    
    import json_scrim
    connect = json_scrim.connect_database('lol_match_database', host=st.secrets["MONGO_DB"]["RO_connection_string"])
    scrim_matches = json_scrim.get_collection(connect, "scrim_matches")
    data_scrim_matches = json_scrim.read_and_create_dataframe(scrim_matches)

    team_dico = st.secrets["TEAM_SCRIM_ID"]
    team_games = json_scrim.filter_data_on_team(data_scrim_matches, team_dict=team_dico)

    st.title("Dashboard League of Legends")

    # winrate_by_side = json_scrim.get_winrate_by_side(team_games, False)
    winrate_by_side = json_scrim.get_winrate_by_side_every_two_weeks(team_games, False)
    st.write(winrate_by_side)
    # st.write("Winrate by side:")
    # # print(winrate_by_side)
    # df_winrate = pd.DataFrame([winrate_by_side])
    # blue_winrate = df_winrate['blue']
    # red_winrate = df_winrate['red']
    # st.write(df_winrate)
    # st.write(f"Blue winrate: {blue_winrate}")
    # Création du bar chart avec Altair
    # st.bar_chart(df_winrate)
    # df = pd.DataFrame(data_scrim_matches)
    # st.write(df)    
    # st.write(test)
    #Filter data


footer()



