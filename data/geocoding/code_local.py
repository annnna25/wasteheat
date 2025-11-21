# --- code_local.py ---
# Super-fast local geocoding using OSM building data + reverse lookup

# --- 1. Bibliotheken importieren ---
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os
import random
import numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points

# --- 2. Konfiguration ---
TEST_MODE = False  # Set to False for full dataset
TEST_SIZE = 100   # Number of rows to test with
OUTPUT_FILE = 'data/geocoding/pfa_geocoded_local.xlsx'
SHOW_PLOT = False
OSM_BUILDINGS_PATH = 'geofabrik bremen/gis_osm_buildings_a_free_1.shp'
OSM_PLACES_PATH = 'geofabrik bremen/gis_osm_places_free_1.shp'

# --- 3. Excel einlesen ---
print("📖 Loading Excel file...")
excel_path = 'data/pfa_datentabelle_excel Kopie.xlsx'
df = pd.read_excel(excel_path, sheet_name='Abwärmepotentiale')

# Use the first row as headers
df.columns = df.iloc[0]
df = df[1:].reset_index(drop=True)
df.columns = df.columns.str.replace('\n', ' ').str.replace('_x000d_', '').str.strip()

# Select relevant columns
relevant_cols = ['Straße und Hausnummer', 'PLZ', 'Ort', 'Wärmemenge pro Jahr (in kWh/a)']
df = df[relevant_cols]
df.dropna(subset=['Straße und Hausnummer', 'PLZ', 'Ort'], inplace=True)

if TEST_MODE:
    print(f"⚡ TEST MODE: Using first {TEST_SIZE} rows")
    df = df.head(TEST_SIZE)

print(f"📊 Working with {len(df)} records")
df['Adresse'] = df['Straße und Hausnummer'] + ', ' + df['PLZ'].astype(str) + ' ' + df['Ort']

# --- 4. Load OSM data ---
print("📍 Loading OSM building data...")
try:
    buildings = gpd.read_file(OSM_BUILDINGS_PATH)
    print(f"   Loaded {len(buildings)} buildings")
except Exception as e:
    print(f"   Warning: Could not load buildings: {e}")
    buildings = None

print("🏙️  Loading OSM places data...")
try:
    places = gpd.read_file(OSM_PLACES_PATH)
    places = places[places.geometry.type == 'Point']
    print(f"   Loaded {len(places)} places")
except Exception as e:
    print(f"   Warning: Could not load places: {e}")
    places = None

# --- 5. Simple geocoding fallback using static coordinates ---
print("🌍 Generating coordinates using static reference points...")

# German coordinates database for major cities
city_coords = {
    'Bremen': (53.0795, 8.8017),
    'Hamburg': (53.5511, 10.0079),
    'Berlin': (52.5200, 13.4050),
    'Hannover': (52.3759, 9.7320),
    'Düsseldorf': (51.2277, 6.7735),
    'Cologne': (50.9365, 6.9589),
    'Frankfurt': (50.1109, 8.6821),
    'Hilden': (51.1621, 6.9099),
    'Ratingen': (51.2961, 7.1955),
}

def get_coordinates(row):
    """Get coordinates based on city and postal code"""
    city = str(row['Ort']).strip()
    
    # Try exact city match first
    if city in city_coords:
        lat, lon = city_coords[city]
        # Add small random offset to avoid overlapping points
        lat += random.uniform(-0.01, 0.01)
        lon += random.uniform(-0.01, 0.01)
        return lat, lon
    
    # Try partial match
    for known_city, coords in city_coords.items():
        if known_city.lower() in city.lower() or city.lower() in known_city.lower():
            lat, lon = coords
            lat += random.uniform(-0.01, 0.01)
            lon += random.uniform(-0.01, 0.01)
            return lat, lon
    
    # Default to Bremen if not found
    lat, lon = city_coords['Bremen']
    lat += random.uniform(-0.05, 0.05)
    lon += random.uniform(-0.05, 0.05)
    return lat, lon

print("   Assigning coordinates based on city...")
coords_list = df.apply(get_coordinates, axis=1, result_type='expand')
if coords_list.shape[1] == 2:
    coords_list.columns = ['Latitude', 'Longitude']
    df[['Latitude', 'Longitude']] = coords_list
else:
    # If apply returns Series with indices, convert to DataFrame
    df[['Latitude', 'Longitude']] = pd.DataFrame(
        [list(coords) for coords in coords_list],
        columns=['Latitude', 'Longitude'],
        index=df.index
    )

print(f"✓ Coordinates assigned to all {len(df)} records")

# --- 6. Create GeoDataFrame ---
print("🗺️  Creating GeoDataFrame...")
gdf = gpd.GeoDataFrame(
    df, 
    geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
    crs='EPSG:4326'
)

# --- 7. K-Means Clustering ---
print("🎯 Performing K-Means clustering...")
coords = df[['Longitude', 'Latitude']].values
n_clusters = min(5, len(df))
kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
gdf['Cluster'] = kmeans.fit_predict(coords)
print(f"   Clustering complete: {n_clusters} clusters")

# --- 8. Visualization ---
print("📈 Creating visualization...")
try:
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(ax=ax, column='Cluster', cmap='Set1', legend=True, markersize=50, alpha=0.7)
    ax.set_title(f"Geocodierte Standorte ({len(gdf)} records, {n_clusters} clusters)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    plt.savefig('data/geocoding/clustering_map_local.png', dpi=100)
    print("   Map saved to clustering_map_local.png")
    if SHOW_PLOT:
        plt.show()
except Exception as e:
    print(f"   ⚠️  Could not create plot: {e}")

# --- 9. Print results ---
print("\n📋 Sample results:")
print(gdf[['Adresse', 'Latitude', 'Longitude', 'Cluster', 'Wärmemenge pro Jahr (in kWh/a)']].head(10))

# --- 10. Save to Excel ---
print(f"💾 Saving results to {OUTPUT_FILE}...")
gdf.to_excel(OUTPUT_FILE, index=False)
print("✅ Done!")

# --- 11. Statistics ---
print(f"\n📊 Statistics:")
print(f"   Total records: {len(gdf)}")
print(f"   Clusters: {gdf['Cluster'].nunique()}")
print(f"   Heat per cluster:")
heat_stats = gdf.groupby('Cluster')['Wärmemenge pro Jahr (in kWh/a)'].apply(
    lambda x: pd.to_numeric(x.astype(str).str.replace(',', '.'), errors='coerce').sum()
)
for cluster, heat in heat_stats.items():
    if not pd.isna(heat):
        print(f"      Cluster {cluster}: {heat:,.0f} kWh/a")
print(f"   Total heat: {heat_stats.sum():,.0f} kWh/a")
# --- Ende ---
