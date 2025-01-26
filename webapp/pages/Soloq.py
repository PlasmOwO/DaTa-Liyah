import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
from footer import footer
load_dotenv()
sys.path.append("../")
import streamlit as st
import soloq_tracking



#title
st.title("SoloQ Tracking")

#Chart
fig= soloq_tracking.plot_soloq_tracking()
st.plotly_chart(fig,use_container_width=True)
footer()