#read in data
import pandas as pd

# Excel-Datei laden
df = pd.read_excel("data/unternehmen.xlsx")

# Prüfen, ob alles richtig eingelesen wurde
print(df.head())



# adress
df["full_address"] = df["Straße"] + " " + df["Hausnummer"].astype(str) + ", " + df["Postleitzahl"].astype(str) + " " + df["Ort"]

print(df[["full_address", "kWh/Jahr"]].head())



# code
from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="waermeprojekt")

latitudes = []
longitudes = []

for address in df["full_address"]:
    try:
        location = geolocator.geocode(address)
        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
        else:
            latitudes.append(None)
            longitudes.append(None)
        time.sleep(1)  # API nicht überlasten
    except:
        latitudes.append(None)
        longitudes.append(None)

df["Latitude"] = latitudes
df["Longitude"] = longitudes

# Prüfen, ob Adressen fehlgeschlagen sind
print(df[df["Latitude"].isnull()])



#geodataframe
import geopandas as gpd
from shapely.geometry import Point

companies = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
    crs="EPSG:4326"
)

# Optional für metrische Berechnungen
companies = companies.to_crs(3857)



# plot
import folium
import pandas as pd
import os

def create_map(df, output_path="results/unternehmen_karte.html"):
    # Zentrum der Karte
    if df is None or df.empty:
        # default to world center if no data
        map_center = [0, 0]
    else:
        map_center = [df["Latitude"].mean(), df["Longitude"].mean()]

    m = folium.Map(location=map_center, zoom_start=10)

    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=5,
            color='red',
            fill=True,
            fill_color='red',
            popup=f"{row['full_address']}\nkWh/Jahr: {row['kWh/Jahr']}"
        ).add_to(m)

    # Speichern
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)
    return m

if __name__ == "__main__":
    csv_path = "results/unternehmen_geocoded.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        create_map(df)
    else:
        print(f"No input DataFrame provided and {csv_path!r} not found. Import your DataFrame and call create_map(df).")



#cluster
from sklearn.cluster import KMeans
import numpy as np

coords = df[["Latitude", "Longitude"]].dropna().to_numpy()

kmeans = KMeans(n_clusters=5, random_state=0).fit(coords)
df.loc[df["Latitude"].notnull(), "Cluster"] = kmeans.labels_
