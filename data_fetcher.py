import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


def fetch_route_data(dep_iata="SYD", limit=100, flight_date=None):
    """
    Fetches scheduled flight data from AviationStack API.
    Supports optional filtering by departure IATA and date.
    """
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "limit": limit,
        "flight_status": "scheduled",
        "dep_iata": dep_iata
    }

    if flight_date:
        params["flight_date"] = flight_date  # Format: YYYY-MM-DD

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        flights = data.get("data", [])
        records = []

        for flight in flights:
            records.append({
                "flight_number": flight.get("flight", {}).get("iata"),
                "airline": flight.get("airline", {}).get("name"),
                "departure_airport": flight.get("departure", {}).get("airport"),
                "departure_iata": flight.get("departure", {}).get("iata"),
                "arrival_airport": flight.get("arrival", {}).get("airport"),
                "arrival_iata": flight.get("arrival", {}).get("iata"),
                "scheduled_departure": flight.get("departure", {}).get("scheduled"),
                "scheduled_arrival": flight.get("arrival", {}).get("scheduled"),
            })

        return pd.DataFrame(records)

    except Exception as e:
        print("❌ Error fetching route data:", e)
        return pd.DataFrame()


def get_route_insights(df):
    """
    Processes route data to extract summary insights.
    """
    insights = {
        "popular_routes": df.groupby(["departure_airport", "arrival_airport"]).size().sort_values(ascending=False).head(10),
        "flight_count": len(df),
        "airlines": df["airline"].value_counts().head(5)
    }
    return insights
