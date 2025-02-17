import streamlit as st
import plotly.express as plty
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb
from footer import footer
import yaml
from yaml import SafeLoader
import streamlit_authenticator as stauth

#Import config :
st.set_page_config(layout="wide")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None

## Welcome message

if st.session_state['authentication_status'] is None or st.session_state['authentication_status'] is False:
    st.title("Welcome to the League of Legends Dashboard")
else : 
    st.title(f"Welcome to the League of Legends Dashboard : *{st.session_state['name']}*")


## Login form
authenticator = stauth.Authenticate(config['credentials'],
                                    config['cookie']['name'],
                                    config['cookie']['key'],
                                    config['cookie']['expiry_days']
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
    
    ## Page 1 : Tendances
    st.title("Dashboard League of Legends")

footer()



