# --- code_all.py ---
# Optimized geocoding script with caching and fast local reverse geocoding

# --- 1. Bibliotheken importieren ---
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os
import pickle
from shapely.geometry import Point

# --- 2. Konfiguration ---
TEST_MODE = False  # Set to False for full dataset
TEST_SIZE = 100   # Number of rows to test with
CACHE_FILE = 'data/geocoding/geocoding_cache.pkl'
OUTPUT_FILE = 'data/geocoding/pfa_geocoded.xlsx'
SHOW_PLOT = True  # Set to False to skip interactive plot

# --- 3. Excel einlesen ---
print("📖 Loading Excel file...")
excel_path = 'data/pfa_datentabelle_excel Kopie.xlsx'
df = pd.read_excel(excel_path, sheet_name='Abwärmepotentiale')

# Use the first row as headers (it contains the actual column names)
df.columns = df.iloc[0]
df = df[1:]  # Skip the header row
df.reset_index(drop=True, inplace=True)

# --- 4. Relevante Spalten auswählen ---
# Clean up column names by removing line breaks and extra characters
df.columns = df.columns.str.replace('\n', ' ').str.replace('_x000d_', '').str.strip()

# Select relevant columns (accounting for column name variations)
relevant_cols = ['Straße und Hausnummer', 'PLZ', 'Ort', 'Wärmemenge pro Jahr (in kWh/a)']
df = df[relevant_cols]
df.dropna(subset=['Straße und Hausnummer', 'PLZ', 'Ort'], inplace=True)

# Test mode
if TEST_MODE:
    print(f"⚡ TEST MODE: Using first {TEST_SIZE} rows")
    df = df.head(TEST_SIZE)

print(f"📊 Working with {len(df)} records")

# --- 5. Adressen zusammenführen ---
df['Adresse'] = df['Straße und Hausnummer'] + ', ' + df['PLZ'].astype(str) + ' ' + df['Ort']

# --- 6. Load geocoding cache if exists ---
geocoding_cache = {}
if os.path.exists(CACHE_FILE):
    print("💾 Loading geocoding cache...")
    try:
        geocoding_cache = pickle.load(open(CACHE_FILE, 'rb'))
        print(f"   Found {len(geocoding_cache)} cached results")
    except:
        print("   Cache corrupted, starting fresh")
        geocoding_cache = {}

# --- 7. Geocoding with Nominatim (only for uncached addresses) ---
print("🌍 Starting geocoding...")
geolocator = Nominatim(user_agent="wasteheat_geocoder", timeout=10)  # Increased timeout
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)  # Back to 1 second for stability

def geocode_address(address):
    """Geocode with caching"""
    if address in geocoding_cache:
        return geocoding_cache[address]
    
    try:
        location = geocode(address, timeout=10)
        result = (location.latitude, location.longitude) if location else (None, None)
    except Exception as e:
        # Silently handle errors - address will get (None, None)
        result = (None, None)
    
    geocoding_cache[address] = result
    return result

# Apply geocoding with progress tracking
print(f"   Processing {len(df)} addresses...")
results = []
for idx, address in enumerate(df['Adresse'], 1):
    result = geocode_address(address)
    results.append(result)
    if idx % 50 == 0:
        print(f"   Progress: {idx}/{len(df)} ({100*idx/len(df):.1f}%)")

df[['Latitude', 'Longitude']] = pd.DataFrame(results)

# --- 8. Save cache ---
print("💾 Saving geocoding cache...")
os.makedirs('data/geocoding', exist_ok=True)
pickle.dump(geocoding_cache, open(CACHE_FILE, 'wb'))

# --- 9. Remove rows without coordinates ---
initial_count = len(df)
df = df.dropna(subset=['Latitude', 'Longitude'])
final_count = len(df)
print(f"✓ {final_count}/{initial_count} addresses successfully geocoded")

if final_count == 0:
    print("❌ No addresses were geocoded. Exiting.")
    exit(1)

# --- 10. GeoDataFrame erstellen ---
print("🗺️  Creating GeoDataFrame...")
gdf = gpd.GeoDataFrame(
    df, 
    geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
    crs='EPSG:4326'
)

# --- 11. KMeans-Clustering ---
print("🎯 Performing K-Means clustering...")
coords = df[['Longitude', 'Latitude']].values
n_clusters = min(5, len(df))  # Ensure n_clusters <= n_samples
kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
gdf['Cluster'] = kmeans.fit_predict(coords)
print(f"   Clustering complete: {n_clusters} clusters created")

# --- 12. Visualisierung ---
print("📈 Creating visualization...")
try:
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(ax=ax, column='Cluster', cmap='Set1', legend=True, markersize=50, alpha=0.7)
    ax.set_title(f"Geocodierte Standorte ({len(gdf)} records, {n_clusters} clusters)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    plt.savefig('data/geocoding/clustering_map.png', dpi=100)
    print("   Map saved to clustering_map.png")
    if SHOW_PLOT:
        plt.show()
except Exception as e:
    print(f"   ⚠️  Could not create plot: {e}")

# --- 13. Ergebnisse anzeigen ---
print("\n📋 Sample results:")
print(gdf[['Adresse', 'Latitude', 'Longitude', 'Cluster', 'Wärmemenge pro Jahr (in kWh/a)']].head(10))

# --- 14. In Excel speichern ---
print(f"💾 Saving results to {OUTPUT_FILE}...")
gdf.to_excel(OUTPUT_FILE, index=False)
print("✅ Done! Results saved.")

# --- 15. Print statistics ---
print(f"\n📊 Statistics:")
print(f"   Total records: {len(gdf)}")
print(f"   Unique clusters: {gdf['Cluster'].nunique()}")
print(f"   Heat per cluster: \n{gdf.groupby('Cluster')['Wärmemenge pro Jahr (in kWh/a)'].sum()}")
# --- Ende des Codes ---
