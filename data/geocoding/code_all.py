# code_all.py
# Komplettes Script für Geocoding, Clustering und Mapping
# Benötigte Bibliotheken: pandas, geopandas, geopy, matplotlib, sklearn

# --- 1. Bibliotheken importieren ---
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# --- 2. Daten einlesen ---
# Ersetze 'data.csv' mit dem Pfad zu deiner CSV-Datei mit Spalten:
# Straße, Hausnummer, PLZ, Ort, kWh
df = pd.read_csv('data/data.csv')  # Beispielpfad

# --- 3. Adressen zusammenführen ---
# Eine neue Spalte 'full_address' erstellen
df['full_address'] = df['Straße'] + ' ' + df['Hausnummer'] + ', ' + df['PLZ'].astype(str) + ' ' + df['Ort']

# --- 4. Geocoding: Adressen in Koordinaten umwandeln ---
geolocator = Nominatim(user_agent="wasteheat_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)  # Vermeidet Sperren bei vielen Anfragen

df['location'] = df['full_address'].apply(geocode)

# Prüfen, ob Adressen gefunden wurden
df['latitude'] = df['location'].apply(lambda loc: loc.latitude if loc else None)
df['longitude'] = df['location'].apply(lambda loc: loc.longitude if loc else None)

# Optional: Fehlende Koordinaten prüfen
missing_coords = df[df['latitude'].isnull() | df['longitude'].isnull()]
if not missing_coords.empty:
    print("Folgende Adressen konnten nicht gefunden werden:")
    print(missing_coords[['full_address']])

# --- 5. Geodataframe erstellen ---
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
gdf.crs = "EPSG:4326"  # Standard-Koordinatensystem

# --- 6. Clustering (z. B. KMeans) ---
# Wir nehmen hier 5 Cluster als Beispiel, kann angepasst werden
coords = gdf[['longitude', 'latitude']]
kmeans = KMeans(n_clusters=5, random_state=0)
gdf['cluster'] = kmeans.fit_predict(coords)

# --- 7. Karte plotten ---
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, column='cluster', cmap='Set1', legend=True, markersize=50)
plt.title("Clustering der Standorte")
plt.show()

# --- 8. Daten speichern ---
gdf.to_file('data/geodataframe.geojson', driver='GeoJSON')  # als GeoJSON speichern
df.to_csv('data/output_with_coordinates.csv', index=False)  # als CSV speichern

print("Script fertig! Geo-Daten und Cluster wurden erstellt.")
