import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
from footer import footer

import streamlit as st


# Check user connection
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import soloq_tracking

#title
st.title("SoloQ Tracking")

#Chart
fig= soloq_tracking.plot_soloq_tracking()
st.plotly_chart(fig,use_container_width=True)
footer()