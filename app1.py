import streamlit as st
import pandas as pd
import plotly.express as px
from data_fetcher import fetch_route_data, get_route_insights

# --- CONSTANTS ---
AU_AIRPORTS = [
    ("SYD", "Sydney"), ("MEL", "Melbourne"), ("BNE", "Brisbane"), ("PER", "Perth"),
    ("ADL", "Adelaide"), ("CBR", "Canberra"), ("HBA", "Hobart"), ("DRW", "Darwin"),
    ("OOL", "Gold Coast"), ("CNS", "Cairns"),
]
IATA_TO_NAME = dict(AU_AIRPORTS)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Australian Flight Demand Dashboard", layout="wide")

# --- HEADER ---
st.title("🛫 Australian Flight Demand Dashboard")
st.markdown("Analyze scheduled flight data across Australia using public API data.")

# --- SIDEBAR ---
st.sidebar.header("🔍 Filters")

selected_dep = st.sidebar.selectbox(
    "Departure Airport",
    options=[f"{iata} - {name}" for iata, name in AU_AIRPORTS],
    index=0
)
selected_dep_iata = selected_dep.split(" - ")[0]

limit = st.sidebar.slider("Flights to Fetch", 10, 100, 50, 10)

# --- FETCH DATA ---
with st.spinner("Fetching scheduled flights..."):
    df = fetch_route_data(dep_iata=selected_dep_iata, limit=limit)

if df.empty:
    st.error("No data available. Try another airport.")
    st.stop()

# --- AIRPORT FILTERING ---
available_iata = pd.concat([df["departure_iata"], df["arrival_iata"]]).dropna().unique()
airport_options = [f"{iata} - {IATA_TO_NAME.get(iata, 'Unknown')}" for iata in available_iata]
option_to_iata = {opt: opt.split(" - ")[0] for opt in airport_options}

selected_airports = st.sidebar.multiselect(
    "Filter by Route Airports",
    options=airport_options,
    default=airport_options[:5] if len(airport_options) >= 5 else airport_options
)

selected_iatas = [option_to_iata[opt] for opt in selected_airports]
if selected_iatas:
    df = df[df["departure_iata"].isin(selected_iatas) | df["arrival_iata"].isin(selected_iatas)]

# --- INSIGHT METRICS ---
insights = get_route_insights(df)

col1, col2, col3 = st.columns(3)
col1.metric("✈️ Total Flights", insights["flight_count"])
col2.metric("🏢 Top Airline", insights["airlines"].index[0] if not insights["airlines"].empty else "N/A")
if not insights["popular_routes"].empty:
    top_route = insights["popular_routes"].index[0]
    col3.metric("🔥 Top Route", f"{top_route[0]} → {top_route[1]}")
else:
    col3.metric("🔥 Top Route", "N/A")

st.markdown("---")

# --- ROUTES CHART ---
st.subheader("🛣️ Most Popular Routes")
chart_type = st.radio("Select Chart Type", ["Bar Chart", "Pie Chart"], horizontal=True)

routes = insights["popular_routes"].reset_index()
routes.columns = ["Departure Airport", "Arrival Airport", "Flight Count"]
routes["Route"] = routes["Departure Airport"] + " → " + routes["Arrival Airport"]

if not routes.empty:
    if chart_type == "Bar Chart":
        fig = px.bar(
            routes, x="Flight Count", y="Route", orientation="h",
            title="Popular Flight Routes", text="Flight Count",
            color_discrete_sequence=["#1f77b4"]
        )
        fig.update_layout(showlegend=False, plot_bgcolor="#f9f9f9")
    else:
        fig = px.pie(
            routes, values="Flight Count", names="Route",
            title="Route Share Distribution", hole=0.3
        )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No route data to display.")

# --- AIRLINES CHART ---
st.subheader("✈️ Top Airlines")
airlines = insights["airlines"].reset_index()
airlines.columns = ["Airline", "Flight Count"]

if not airlines.empty:
    fig = px.bar(
        airlines, x="Airline", y="Flight Count", text="Flight Count",
        color_discrete_sequence=["#00a878"]
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No airline data available.")

# --- RAW DATA TABLE ---
with st.expander("📋 View Raw Flight Data"):
    st.dataframe(df)

# --- DOWNLOAD BUTTON ---
csv = df.to_csv(index=False)
st.download_button("📥 Download CSV", csv, file_name="filtered_flight_data.csv", mime="text/csv")

# --- USER GUIDE ---
with st.expander("ℹ️ How to Use This Dashboard"):
    st.markdown("""
    - Select a **departure airport** to pull scheduled flights.
    - Filter routes by airports using the multiselect.
    - View top airlines and most frequent routes.
    - Export the dataset using the **Download CSV** button.
    """)

# --- FOOTER ---
st.caption("Developed by Shruti Sharma | Data Source: AviationStack API")
