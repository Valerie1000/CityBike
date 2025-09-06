import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
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
st.sidebar.title("Explore the Dashboard")
page = st.sidebar.selectbox(
    "Choose a section:",
    [
        "Intro",
        "Weather & Bike Usage",
        "Popular Stations",
        "Trip Routes Map",
        "Station Distribution",
        "Customer Insights",
        "Recommendations",
    ],
)

# -----------------
# Load sample data (smaller files for demo)
# -----------------
df = pd.read_parquet("data/reduced_data_to_plot_sample.parquet")
top20 = pd.read_parquet("data/top20stations_sample.parquet")
daily_trips = pd.read_parquet("data/daily_trips_sample.parquet")
stations = pd.read_parquet("data/stations_sample.parquet")

# -----------------
# Pages
# -----------------
### Intro
if page == "Intro":
    st.title("🚴 NYC CitiBike Dashboard")
    st.subheader("Exploring patterns in New York City’s bike-sharing system")

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
        img = Image.open("nyc_citibike.jpg")
        st.image(img, use_container_width=True)
    except:
        st.info("Upload a file named `nyc_citibike.jpg` to display an image here.")

# -----------------
# Weather & Bike Usage
# -----------------
elif page == "Weather & Bike Usage":
    st.subheader("📈 CitiBike Trips and Weather")

    # Scatterplot with trendline
    fig_scatter = px.scatter(
        daily_trips,
        x="TAVG",
        y="trip_count",
        trendline="ols",
        title="🚴 Daily Bike Trips vs. Temperature",
        labels={"TAVG": "Avg Temperature (°F)", "trip_count": "Trips"},
        opacity=0.6,
    )

    # Highlight comfort zone 70–80°F
    fig_scatter.add_vline(x=70, line_width=2, line_dash="dash", line_color="red")
    fig_scatter.add_vline(x=80, line_width=2, line_dash="dash", line_color="red")
    fig_scatter.add_vrect(x0=70, x1=80, fillcolor="red", opacity=0.1, line_width=0)

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("""
    - Rides rise as weather warms.  
    - Most trips happen between **70–80°F**.  
    - Beyond 80°F, demand flattens out.  
    """)

    # Time series (Trips vs Temp)
    fig_weather = make_subplots(specs=[[{"secondary_y": True}]])
    fig_weather.add_trace(
        go.Scatter(
            x=daily_trips["date"],
            y=daily_trips["trip_count"],
            mode="lines",
            name="Daily Trips",
            line=dict(color="green"),
        ),
        secondary_y=False,
    )
    fig_weather.add_trace(
        go.Scatter(
            x=daily_trips["date"],
            y=daily_trips["TAVG"],
            mode="lines",
            name="Avg Temp (°F)",
            line=dict(color="blue"),
        ),
        secondary_y=True,
    )
    fig_weather.update_layout(
        title="📅 Trips & Temperature Over Time",
        yaxis=dict(title="Trips"),
        yaxis2=dict(title="Avg Temp (°F)", overlaying="y", side="right"),
        height=500,
    )
    st.plotly_chart(fig_weather, use_container_width=True)

    st.markdown("""
    - Summer months see the **highest ridership**.  
    - Winter brings a sharp **drop in trips**.  
    - Clear seasonal patterns help plan bike supply.  
    """)

# -----------------
# Popular Stations
# -----------------
elif page == "Popular Stations":
    st.subheader("🚲 Most Popular CitiBike Stations")

    all_stations = pd.concat([df["start_station_name"], df["end_station_name"]])
    station_usage = all_stations.value_counts().reset_index()
    station_usage.columns = ["station_name", "trip_count"]
    top10 = station_usage.head(10)

    fig_top10 = px.bar(
        top10,
        x="station_name",
        y="trip_count",
        text="trip_count",
        color="trip_count",
        color_continuous_scale="Blues",
        title="Top 10 Busiest Stations",
    )
    fig_top10.update_traces(texttemplate="%{text:,}", textposition="inside")
    fig_top10.update_layout(
        xaxis_tickangle=45, height=500, showlegend=False, yaxis_title="Trips"
    )

    st.plotly_chart(fig_top10, use_container_width=True)

    st.markdown(
        """
        - The busiest stations are clustered in **Manhattan**, especially near **Central Park**, **Midtown**, and **Downtown transit hubs**.  
        - Outer boroughs show far fewer high-traffic stations, suggesting room for expansion.
        """
    )

# -----------------
# Trip Routes Map
# -----------------
elif page == "Trip Routes Map":
    st.subheader("🗺️ Popular CitiBike Routes in NYC")

    try:
        with open("kepler_map.html", "r", encoding="utf-8") as f:
            html_data = f.read()
        st.components.v1.html(html_data, height=800)
    except:
        st.info("Upload `data/kepler_map.html` to display the interactive map.")

    st.markdown(
        """
        - **Bright lines** show the busiest bike routes.  
        - **Green dots = trip starts**, **red dots = trip ends**.  
        - Single green dots mark stations used as both start & end.  
        - Strong flows are visible around **Central Park**, the **Hudson River Greenway**, and **Midtown**.  
        - Outer boroughs have fewer frequent routes, showing lower usage.
        """
    )

# -----------------
# Station Distribution
# -----------------
elif page == "Station Distribution":
    st.subheader("📍 Where are CitiBike stations located?")

    # Percentile cutoff
    percentile_cutoff = st.sidebar.slider(
        "Highlight top station usage percentile",
        min_value=50,
        max_value=100,
        value=80,
        step=5,
    )

    # Merge usage with stations
    start_usage = df.groupby("start_station_name")["ride_id"].count().reset_index()
    start_usage.columns = ["station_name", "trips"]
    stations_usage = stations.merge(start_usage, on="station_name", how="left").fillna(0)

    threshold = stations_usage["trips"].quantile(percentile_cutoff / 100)
    stations_usage["highlight"] = stations_usage["trips"] >= threshold

    total_stations = len(stations_usage)
    highlighted = stations_usage["highlight"].sum()

    st.sidebar.metric(
        "Stations Highlighted", f"{highlighted:,} / {total_stations:,}"
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_all = px.scatter_mapbox(
            stations_usage,
            lat="lat",
            lon="lon",
            hover_name="station_name",
            hover_data={"trips": True},
            color_discrete_sequence=["skyblue"],
            zoom=11,
            height=500,
            mapbox_style="carto-darkmatter",
            title="All Stations",
        )
        st.plotly_chart(fig_all, use_container_width=True)

    with col2:
        fig_highlight = px.scatter_mapbox(
            stations_usage,
            lat="lat",
            lon="lon",
            hover_name="station_name",
            hover_data={"trips": True},
            color="highlight",
            color_discrete_map={True: "red", False: "lightgray"},
            zoom=11,
            height=500,
            mapbox_style="carto-darkmatter",
            title=f"Top {100 - percentile_cutoff}% Stations",
        )
        st.plotly_chart(fig_highlight, use_container_width=True)

    st.markdown(
        f"""
        - Left: All stations (blue).  
        - Right: Top {100 - percentile_cutoff}% busiest stations (red).  
        - Red stations are concentrated in **Manhattan** and near major hubs.  
        - Outer boroughs have fewer high-usage stations, suggesting expansion opportunities.  
        """
    )

# -----------------
# Customer Insights
# -----------------
elif page == "Customer Insights":
    st.subheader("👥 Who uses CitiBike?")

    # Trips by bike type
    ride_counts = df["rideable_type"].value_counts().reset_index()
    ride_counts.columns = ["rideable_type", "count"]
    fig_rideable = px.bar(
        ride_counts,
        x="rideable_type",
        y="count",
        text="count",
        color="rideable_type",
        title="🚲 Trips by Bike Type",
        labels={"count": "Trips", "rideable_type": "Bike Type"},
    )
    fig_rideable.update_traces(texttemplate="%{text:,}", textposition="inside")
    fig_rideable.update_layout(showlegend=False, yaxis_title="Trips", height=500)
    st.plotly_chart(fig_rideable, use_container_width=True)

    # Members vs casuals
    member_counts = df["member_casual"].value_counts(normalize=True) * 100
    fig_member = px.pie(
        values=member_counts.values,
        names=member_counts.index,
        title="👥 Member vs Casual Riders",
        hole=0.3,
    )
    st.plotly_chart(fig_member, use_container_width=True)

    # Avg trip duration by customer & bike type
    avg_duration = (
        df.groupby(["member_casual", "rideable_type"])["tripduration_min"]
        .mean()
        .reset_index()
    )
    fig_grouped = px.bar(
        avg_duration,
        x="rideable_type",
        y="tripduration_min",
        color="member_casual",
        barmode="group",
        title="⏱️ Avg Trip Duration by Rider & Bike Type",
        labels={
            "rideable_type": "Bike Type",
            "tripduration_min": "Avg Duration (min)",
            "member_casual": "Rider Type",
        },
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
    st.header("💡 Recommendations for CitiBike Expansion")

    try:
        bikes = Image.open("recs_page.png")
        st.markdown(
            "<div style='text-align: center;'>",
            unsafe_allow_html=True,
        )
        st.image(bikes, width=300)
        st.markdown("</div>", unsafe_allow_html=True)
    except:
        st.info("Upload `recs_page.png` to display an image here.")

    st.markdown(
        """
        ### Key Suggestions for the Future  
        - **Scale supply in winter**: reduce bikes by about **40–60% from Nov–Apr**, then expand again for the busy summer season.  
        - **Expand to underserved areas**: add stations in **Queens and Staten Island**.  
        - **Boost busy hubs**: keep more bikes available near **Central Park, Midtown, and major subway stations**.  
        - 🚲 **Match rider needs**:  
            - More **classic bikes** for everyday commuters.  
            - More **e-bikes near hilly areas and tourist hotspots** for longer leisure rides.  
        """ 
    )
