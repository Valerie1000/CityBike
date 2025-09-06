import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl
from numerize.numerize import numerize
from PIL import Image

# -----------------
# Page config
# -----------------
st.set_page_config(
    page_title="NYC CitiBike Dashboard",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------
# Sidebar Navigation
# -----------------
st.sidebar.title("Aspect Selector")
page = st.sidebar.selectbox(
    'Select a section:',
    ["Intro page",
     "Weather & Bike Usage",
     "Most Popular Stations",
     "Map: Top Trips",
     "Station Density",
     "Customer Insights",
     "Recommendations"]
)

# -----------------
# Load Data
# -----------------
df = pd.read_parquet(r"C:\Users\valev\CityBike\reduced_data_to_plot.parquet")
top20 = pd.read_parquet(r"C:\Users\valev\CityBike\top20stations.parquet")
daily_trips = pd.read_parquet(r"C:\Users\valev\CityBike\daily_trips.parquet")
stations = pd.read_parquet(r"C:\Users\valev\CityBike\stations.parquet")

# -----------------
# Pages
# -----------------

### Intro page
if page == "Intro page":
    st.title("🚴 NYC CitiBike Dashboard")
    st.subheader("How New Yorkers and visitors ride CitiBike")

    st.markdown("""
    This dashboard shows:  
    - When people ride the most  
    - How weather affects bike use  
    - The busiest stations  
    - Where bikes are located across NYC  
    - Who uses CitiBike most often  
    - Ideas for improving the system  

    Use the menu on the left to explore each section.
    """)

    try:
        myImage = Image.open("nyc_citibike.jpg")  # optional local image
        st.image(myImage, use_column_width=True)
    except:
        st.info("Upload a NYC CitiBike image named `nyc_citibike.jpg` to display it here.")


# -----------------
# Weather & Bike Usage
# -----------------
elif page == "Weather & Bike Usage":
    st.subheader("📈 Bike Trips & Weather in NYC")

    # Scatterplot with trendline + comfort zone
    fig_scatter = px.scatter(
        daily_trips,
        x="TAVG", y="trip_count",
        trendline="ols",
        title="🚴 Trips vs Temperature (2022)",
        labels={"TAVG": "Average Temp (°F)", "trip_count": "Daily Trips"},
        opacity=0.6
    )
    fig_scatter.add_vline(x=70, line_width=2, line_dash="dash", line_color="red")
    fig_scatter.add_vline(x=80, line_width=2, line_dash="dash", line_color="red")
    fig_scatter.add_vrect(x0=70, x1=80, fillcolor="red", opacity=0.1, line_width=0)

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""
    - Rides rise as weather warms.  
    - Most trips happen between **70–80°F**.  
    - Beyond 80°F, demand flattens out.  
    """)

    # Time Series
    fig_weather = make_subplots(specs=[[{"secondary_y": True}]])
    fig_weather.add_trace(
        go.Scatter(x=daily_trips["date"], y=daily_trips["trip_count"],
                   mode="lines", name="Daily Trips", line=dict(color="green")),
        secondary_y=False
    )
    fig_weather.add_trace(
        go.Scatter(x=daily_trips["date"], y=daily_trips["TAVG"],
                   mode="lines", name="Avg Temp (°F)", line=dict(color="blue")),
        secondary_y=True
    )
    fig_weather.update_layout(
        title="📅 Trips & Temperature Over Time (2022)",
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Avg Temp (°F)", overlaying="y", side="right"),
        height=500
    )

    st.plotly_chart(fig_weather, use_container_width=True)

    st.markdown("""
    - Summer months see the **highest ridership**.  
    - Winter brings a sharp **drop in trips**.  
    - Clear seasonal patterns help plan bike supply.  
    """)


# -----------------
# Most Popular Stations
# -----------------
elif page == "Most Popular Stations":
    total_rides = float(df['ride_id'].count())    
    st.metric(label="Total Bike Rides", value=numerize(total_rides))

    all_stations = pd.concat([df['start_station_name'], df['end_station_name']])
    station_usage = all_stations.value_counts().reset_index()
    station_usage.columns = ["station_name", "trip_count"]
    top10 = station_usage.head(10)

    fig_top10 = px.bar(
        top10, x="station_name", y="trip_count",
        text="trip_count", color="trip_count", color_continuous_scale="Blues",
        title="🚲 Top 10 Busiest Stations"
    )
    fig_top10.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig_top10.update_layout(xaxis_tickangle=45, height=500, showlegend=False)

    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown("""
    - **Manhattan dominates**: Central Park, Midtown, and Downtown lead in rides.  
    - Outer borough stations see **much lower activity**.  
    - A small number of stations account for a large share of trips.  
    """)


# -----------------
# Aggregated Trips Map
# -----------------
elif page == "Map: Top Trips":
    st.subheader("🗺️ Where do people ride most?")

    path_to_html = r"C:\Users\valev\CityBike\kepler.gl.html"  # update filename if needed
    with open(path_to_html, "r", encoding="utf-8") as f: 
        html_data = f.read()

    st.components.v1.html(html_data, height=800)

    st.markdown("""
    - Bright routes show **the most popular trips**.  
    - Green dots are **start** of trips while red are **stop**
        - Lone green dots are both **start and end**
    - Heavy use along **Central Park, the Hudson River, and Midtown**.  
    - Outer boroughs have fewer frequent routes, showing **lower usage**.  
    """)
    

# -----------------
# Station Density
# -----------------
elif page == "Station Density":
    st.subheader("📍 Where are CitiBike stations located?")

    percentile_cutoff = st.sidebar.slider(
        "Top usage percentile to highlight",
        min_value=50, max_value=100, value=80, step=5
    )

    start_usage = df.groupby("start_station_name")["ride_id"].count().reset_index()
    start_usage.columns = ["station_name", "trips"]
    stations_usage = stations.merge(start_usage, on="station_name", how="left").fillna(0)

    threshold = stations_usage["trips"].quantile(percentile_cutoff / 100)
    stations_usage["highlight"] = stations_usage["trips"] >= threshold

    total_stations = len(stations_usage)
    highlighted_stations = stations_usage["highlight"].sum()

    st.sidebar.metric("Stations Highlighted",
                      f"{highlighted_stations:,} / {total_stations:,}")

    col1, col2 = st.columns(2)

    with col1:
        fig_all = px.scatter_mapbox(
            stations_usage, lat="lat", lon="lon",
            hover_name="station_name", hover_data={"trips": True},
            color_discrete_sequence=["skyblue"],
            zoom=11, height=500, mapbox_style="carto-darkmatter",
            title="All Stations"
        )
        st.plotly_chart(fig_all, use_container_width=True)

    with col2:
        fig_highlight = px.scatter_mapbox(
            stations_usage, lat="lat", lon="lon",
            hover_name="station_name", hover_data={"trips": True},
            color="highlight",
            color_discrete_map={True: "red", False: "lightgray"},
            zoom=11, height=500, mapbox_style="carto-darkmatter",
            title=f"Top {100 - percentile_cutoff}% Stations (in red)"
        )
        st.plotly_chart(fig_highlight, use_container_width=True)

    st.markdown(f"""
    - Left: **All {total_stations:,} stations** in blue.  
    - Right: **Top {100 - percentile_cutoff}% busiest stations** in red.  
    - Most activity is centered in **Manhattan and parts of Brooklyn**,  
      while **Queens and Staten Island have fewer stations and lower use**.  
    """)


# -----------------
# Customer Insights
# -----------------
elif page == "Customer Insights":
    st.subheader("👥 Who uses CitiBike?")

    # Trips by bike type
    ride_counts = df['rideable_type'].value_counts().reset_index()
    ride_counts.columns = ["rideable_type", "count"]
    fig_rideable = px.bar(
        ride_counts, x="rideable_type", y="count",
        title="🚲 Trips by Bike Type",
        labels={"count": "Trips", "rideable_type": "Bike Type"},
        color="rideable_type", text="count"
    )
    fig_rideable.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig_rideable.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_rideable, use_container_width=True)

    # Member vs Casual
    member_counts = df['member_casual'].value_counts(normalize=True) * 100
    fig_member = px.pie(
        values=member_counts.values, names=member_counts.index,
        title="👥 Members vs Casual Riders", hole=0.3
    )
    st.plotly_chart(fig_member, use_container_width=True)

    # Avg trip duration by customer & bike type
    avg_duration = (
        df.groupby(["member_casual", "rideable_type"])["tripduration_min"]
          .mean().reset_index()
    )
    fig_grouped = px.bar(
        avg_duration, x="rideable_type", y="tripduration_min",
        color="member_casual", barmode="group",
        title="⏱️ Avg Trip Duration by Rider & Bike Type",
        labels={"rideable_type": "Bike Type", "tripduration_min": "Minutes"}
    )
    st.plotly_chart(fig_grouped, use_container_width=True)

    st.markdown("""
    - **Members (commuters)** take most rides, usually short trips.  
    - **Casual riders** (tourists/leisure) take fewer but **longer rides**.  
    - **Classic bikes** dominate overall, while **e-bikes are used less often** but help with longer or uphill trips.  
    """)


# -----------------
# Recommendations
# -----------------
elif page == "Recommendations":
    st.header("💡 Recommendations for NYC CitiBike")

    try:
        bikes = Image.open("recs_page.png")
        st.image(bikes, width=300, caption="Ideas for expansion", use_column_width=False)
    except:
        st.info("Upload `recs_page.png` to show an illustration here.")

    st.markdown("""
    ### Key Suggestions for the Future  
    - 📉 **Scale supply in winter**: reduce bikes by about **40–60% from Nov–Apr**, then expand again for the busy summer season.  
    - 🗺 **Expand into outer boroughs**: add stations in **Queens and Staten Island** to cover gaps.  
    - 🚉 **Boost central hubs**: keep more bikes available around **Central Park, Midtown, and major subway stations**.  
    - 🚲 **Match rider needs**:  
        - More **classic bikes** for everyday commuters.  
        - More **e-bikes near hilly areas and tourist hotspots** for longer leisure rides.  
    """)