# code_all.py
# Komplettes Script für Geocoding, Clustering und Mapping
# Mit automatischer Speicherung von nicht gefundenen Adressen
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

print(f"Daten eingelesen: {len(df)} Zeilen.")

# --- 3. Adressen zusammenführen ---
df['full_address'] = df['Straße'] + ' ' + df['Hausnummer'] + ', ' + df['PLZ'].astype(str) + ' ' + df['Ort']

# --- 4. Geocoding: Adressen in Koordinaten umwandeln ---
geolocator = Nominatim(user_agent="wasteheat_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)  # Vermeidet Sperren bei vielen Anfragen

print("Starte Geocoding...")
df['location'] = df['full_address'].apply(geocode)

# Latitude und Longitude extrahieren
df['latitude'] = df['location'].apply(lambda loc: loc.latitude if loc else None)
df['longitude'] = df['location'].apply(lambda loc: loc.longitude if loc else None)

# --- 4a. Nicht gefundene Adressen speichern ---
missing_coords = df[df['latitude'].isnull() | df['longitude'].isnull()]
if not missing_coords.empty:
    print(f"{len(missing_coords)} Adressen konnten nicht gefunden werden. Speichere in 'missing_addresses.csv'.")
    missing_coords.to_csv('data/missing_addresses.csv', index=False)
else:
    print("Alle Adressen erfolgreich geocodiert.")

# --- 5. Geodataframe erstellen ---
gdf = gpd.GeoDataFrame(df.dropna(subset=['latitude', 'longitude']),  # Nur gültige Koordinaten
                       geometry=gpd.points_from_xy(df.dropna(subset=['latitude', 'longitude']).longitude,
                                                   df.dropna(subset=['latitude', 'longitude']).latitude))
gdf.crs = "EPSG:4326"  # Standard-Koordinatensystem

# --- 6. Clustering (z. B. KMeans) ---
coords = gdf[['longitude', 'latitude']]
n_clusters = 5  # Anzahl Cluster anpassen, falls gewünscht
kmeans = KMeans(n_clusters=n_clusters, random_state=0)
gdf['cluster'] = kmeans.fit_predict(coords)
print(f"Clustering abgeschlossen: {n_clusters} Cluster erstellt.")

# --- 7. Karte plotten ---
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, column='cluster', cmap='Set1', legend=True, markersize=50)
plt.title("Clustering der Standorte")
plt.show()

# --- 8. Daten speichern ---
gdf.to_file('data/geodataframe.geojson', driver='GeoJSON')  # GeoJSON speichern
df.to_csv('data/output_with_coordinates.csv', index=False)  # CSV speichern

print("Script fertig! Geo-Daten, Cluster und nicht gefundene Adressen wurden gespeichert.")

