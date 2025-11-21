# --- code_all.py ---

# --- 1. Bibliotheken importieren ---
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# --- 2. Excel einlesen ---
excel_path = 'data/pfa_datentabelle_excel Kopie.xlsx'
df = pd.read_excel(excel_path, sheet_name='Abwärmepotentiale')

# Use the first row as headers (it contains the actual column names)
df.columns = df.iloc[0]
df = df[1:]  # Skip the header row
df.reset_index(drop=True, inplace=True)

# --- 3. Relevante Spalten auswählen ---
# Clean up column names by removing line breaks and extra characters
df.columns = df.columns.str.replace('\n', ' ').str.replace('_x000d_', '').str.strip()

# Select relevant columns (accounting for column name variations)
relevant_cols = ['Straße und Hausnummer', 'PLZ', 'Ort', 'Wärmemenge pro Jahr (in kWh/a)']
df = df[relevant_cols]
df.dropna(subset=['Straße und Hausnummer', 'PLZ', 'Ort'], inplace=True)

# --- 4. Adressen zusammenführen ---
df['Adresse'] = df['Straße und Hausnummer'] + ', ' + df['PLZ'].astype(str) + ' ' + df['Ort']

# --- 5. Geocoding ---
geolocator = Nominatim(user_agent="wasteheat_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

df['location'] = df['Adresse'].apply(geocode)
df['Latitude'] = df['location'].apply(lambda loc: loc.latitude if loc else None)
df['Longitude'] = df['location'].apply(lambda loc: loc.longitude if loc else None)

# --- 6. GeoDataFrame erstellen ---
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']))

# --- 7. Punkte plotten ---
gdf.plot(marker='o', color='red', markersize=5)
plt.title("Geocodierte Standorte")
plt.show()

# --- 8. KMeans-Clustering ---
coords = df[['Latitude', 'Longitude']].dropna()
kmeans = KMeans(n_clusters=5, random_state=0).fit(coords)
df.loc[coords.index, 'Cluster'] = kmeans.labels_

# --- 9. Ergebnisse anzeigen ---
print(df.head())

# --- Optional: In neue Excel speichern ---
df.to_excel('data/geocoding/pfa_geocoded.xlsx', index=False)
# --- Ende des Codes ---
