# --- code_fast.py ---
# Fast parallel geocoding script with geopy

# --- 1. Bibliotheken importieren ---
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import os
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# --- 2. Konfiguration ---
TEST_MODE = False  # Set to False for full dataset
TEST_SIZE = 100   # Number of rows to test with
CACHE_FILE = 'data/geocoding/geocoding_cache.pkl'
OUTPUT_FILE = 'data/geocoding/pfa_geocoded.xlsx'
SHOW_PLOT = False  # Set to True to show interactive plot
MAX_WORKERS = 4   # Number of parallel geocoding threads

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

# Select relevant columns
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

# --- 7. Prepare addresses to geocode ---
addresses = df['Adresse'].unique()
uncached_addresses = [a for a in addresses if a not in geocoding_cache]
print(f"🔍 {len(addresses)} unique addresses, {len(uncached_addresses)} need geocoding")

# --- 8. Parallel Geocoding with thread pool ---
print(f"🌍 Starting parallel geocoding with {MAX_WORKERS} workers...")

def geocode_single(address):
    """Geocode a single address"""
    try:
        geolocator = Nominatim(user_agent="wasteheat_geocoder", timeout=10)
        location = geolocator.geocode(address, timeout=10)
        return (address, (location.latitude, location.longitude) if location else (None, None))
    except Exception as e:
        return (address, (None, None))

start_time = time.time()
processed = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all uncached addresses
    futures = {executor.submit(geocode_single, addr): addr for addr in uncached_addresses}
    
    # Process results as they complete
    for future in as_completed(futures):
        address, result = future.result()
        geocoding_cache[address] = result
        processed += 1
        
        if processed % 100 == 0:
            elapsed = time.time() - start_time
            rate = processed / elapsed
            remaining = len(uncached_addresses) - processed
            eta = remaining / rate if rate > 0 else 0
            print(f"   Progress: {processed}/{len(uncached_addresses)} ({100*processed/len(uncached_addresses):.1f}%) - ETA: {eta/60:.0f}min")

print(f"✓ Geocoding complete in {(time.time()-start_time)/60:.1f} minutes")

# --- 9. Apply cached results to dataframe ---
df[['Latitude', 'Longitude']] = df['Adresse'].apply(
    lambda x: pd.Series(geocoding_cache.get(x, (None, None)))
)

# --- 10. Save cache ---
print("💾 Saving geocoding cache...")
os.makedirs('data/geocoding', exist_ok=True)
pickle.dump(geocoding_cache, open(CACHE_FILE, 'wb'))

# --- 11. Remove rows without coordinates ---
initial_count = len(df)
df = df.dropna(subset=['Latitude', 'Longitude'])
final_count = len(df)
print(f"✓ {final_count}/{initial_count} addresses successfully geocoded")

if final_count == 0:
    print("❌ No addresses were geocoded. Exiting.")
    exit(1)

# --- 12. GeoDataFrame erstellen ---
print("🗺️  Creating GeoDataFrame...")
gdf = gpd.GeoDataFrame(
    df, 
    geometry=gpd.points_from_xy(df['Longitude'], df['Latitude']),
    crs='EPSG:4326'
)

# --- 13. KMeans-Clustering ---
print("🎯 Performing K-Means clustering...")
coords = df[['Longitude', 'Latitude']].values
n_clusters = min(5, len(df))  # Ensure n_clusters <= n_samples
kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
gdf['Cluster'] = kmeans.fit_predict(coords)
print(f"   Clustering complete: {n_clusters} clusters created")

# --- 14. Visualisierung ---
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

# --- 15. Ergebnisse anzeigen ---
print("\n📋 Sample results:")
print(gdf[['Adresse', 'Latitude', 'Longitude', 'Cluster', 'Wärmemenge pro Jahr (in kWh/a)']].head(10))

# --- 16. In Excel speichern ---
print(f"💾 Saving results to {OUTPUT_FILE}...")
gdf.to_excel(OUTPUT_FILE, index=False)
print("✅ Done! Results saved.")

# --- 17. Print statistics ---
print(f"\n📊 Statistics:")
print(f"   Total records: {len(gdf)}")
print(f"   Unique clusters: {gdf['Cluster'].nunique()}")
print(f"   Heat per cluster (kWh/a): ")
heat_stats = gdf.groupby('Cluster')['Wärmemenge pro Jahr (in kWh/a)'].sum()
for cluster, heat in heat_stats.items():
    print(f"      Cluster {cluster}: {heat:,.0f}")
print(f"   Total heat: {heat_stats.sum():,.0f} kWh/a")
# --- Ende des Codes ---
