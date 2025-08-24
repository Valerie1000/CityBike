import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from datetime import datetime as dt

# -----------------
# Page config
# -----------------
st.set_page_config(
    page_title="NYC CitiBike Dashboard",
    page_icon="🚴",
    layout="wide",          # "centered" or "wide"
    initial_sidebar_state="expanded"
)

# -----------------
# Dashboard Header
# -----------------
st.title("🚴 NYC CityBike Dashboard")
st.subheader("Exploring trip patterns, weather impact, and station activity")

st.markdown("""
This dashboard provides insights into **New York City CityBike trips**.  
Key objectives:
- Daily usage trends
- Impact of weather (temperature, precipitation)  
- Start and end station activity  
- Spatial patterns on the city map  

Use the sidebar to filter the data and interact with the visuals.
""")

# -----------------
# Import data
# -----------------
df = pd.read_parquet(r"C:\Users\valev\CityBike\reduced_data_to_plot.parquet")
top20 = pd.read_parquet(r"C:\Users\valev\CityBike\top20stations.parquet")
daily_trips = pd.read_parquet(r"C:\Users\valev\CityBike\daily_trips.parquet")

# -----------------
# Define the Charts
# -----------------

## Bar chart

fig_popularstation1 = go.Figure(go.Bar(x = top20['start_station_name'], y = top20['value'], marker={'color': top20['value'],'colorscale': 'Blues'}))
fig_popularstation1.update_layout(
    title = 'Top 20 most popular bike stations in NYC',
    xaxis_title = 'Start stations',
    yaxis_title ='Sum of trips',
    width = 900, height = 600
)
st.plotly_chart(fig_popularstation1, use_container_width=True)

## Line chart

fig_dailytrips_temp = go.Figure()

fig_dailytrips_temp.add_trace(go.Scatter(x=daily_trips["date"], y=daily_trips["trip_count"],
                         mode="lines", name="Trips"))

fig_dailytrips_temp.add_trace(go.Scatter(x=df.groupby("date")["TAVG"].mean().index,
                         y=df.groupby("date")["TAVG"].mean().values,
                         mode="lines", name="Avg Temp", yaxis="y2"))

fig_dailytrips_temp.update_layout(
    title="Daily Trips vs Temperature",
    yaxis=dict(title="Trips"),
    yaxis2=dict(title="Avg Temp (°F)", overlaying="y", side="right")
)
st.plotly_chart(fig_dailytrips_temp, use_container_width=True)

# -----------------
# Add the map
# -----------------


path_to_html = r"C:\Users\valev\CityBike\bike_trips_map.html"


# Read file and keep in variable

with open(path_to_html, 'r', encoding='utf-8') as f:
    html_data = f.read()
    
## Show in webpage
st.header("Aggregated Bike Trips in NYC")
st.components.v1.html(html_data,height=1000)



