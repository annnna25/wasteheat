"""
ArcGIS Pro Integration Script
Exports wasteheat supply and demand data as GeoJSON layers
"""

import pandas as pd
import geopandas as gpd
import json
import os
from shapely.geometry import Point, box
import numpy as np

print("=" * 80)
print("ARCGIS PRO DATA PREPARATION - WASTEHEAT MAPPING FOR BREMEN")
print("=" * 80)

# --- 1. LOAD WASTEHEAT DATA ---
print("\n📖 Step 1: Loading wasteheat supply data...")
df_supply = pd.read_excel('data/geocoding/pfa_geocoded_local.xlsx')
print(f"   ✓ Loaded {len(df_supply)} wasteheat locations")

# Convert to GeoDataFrame
gdf_supply = gpd.GeoDataFrame(
    df_supply,
    geometry=gpd.points_from_xy(df_supply['Longitude'], df_supply['Latitude']),
    crs='EPSG:4326'
)

gdf_supply['Heat_kWh_Year'] = pd.to_numeric(
    gdf_supply['Wärmemenge pro Jahr (in kWh/a)'].astype(str).str.replace(',', '.'),
    errors='coerce'
)
total_capacity = gdf_supply['Heat_kWh_Year'].sum()
print(f"   ✓ Total capacity: {total_capacity:,.0f} kWh/a")

# --- 2. DEFINE BREMEN STUDY AREA ---
print("\n🗺️  Step 2: Defining Bremen study area...")
# Bremen city boundaries (approximate)
bremen_bounds = {
    'north': 53.14,
    'south': 53.02,
    'east': 8.94,
    'west': 8.65
}
bremen_bbox = box(bremen_bounds['west'], bremen_bounds['south'], 
                   bremen_bounds['east'], bremen_bounds['north'])
print(f"   ✓ Bremen bounding box defined")

# Filter supply within/near Bremen
gdf_supply['in_bremen'] = gdf_supply.geometry.within(bremen_bbox.buffer(0.02))
supply_in_bremen = gdf_supply[gdf_supply['in_bremen']].copy()
print(f"   ✓ Found {len(supply_in_bremen)} wasteheat sources in/near Bremen")

# --- 3. LOAD OSM DATA FOR DEMAND ANALYSIS ---
print("\n🏭 Step 3: Identifying heat demand areas...")

# Load building data
buildings_path = 'geofabrik bremen/gis_osm_buildings_a_free_1.shp'
if os.path.exists(buildings_path):
    print("   Loading buildings...")
    buildings = gpd.read_file(buildings_path)
    buildings = buildings.to_crs('EPSG:4326')
    # Filter to Bremen area
    buildings = buildings[buildings.geometry.intersects(bremen_bbox.buffer(0.02))]
    print(f"   ✓ Loaded {len(buildings)} buildings in Bremen")
else:
    print("   ⚠️  Buildings file not found")
    buildings = None

# --- 4. CLASSIFY HEAT DEMAND ---
print("\n🔥 Step 4: Classifying heat demand areas...")

# Create demand categories
demand_categories = {
    'industrial': ['factory', 'industrial', 'warehouse', 'manufacturing'],
    'commercial': ['commercial', 'retail', 'office', 'hotel', 'restaurant'],
    'residential': ['residential', 'apartment', 'house', 'building'],
    'institutional': ['hospital', 'school', 'government', 'public'],
}

# Simple demand estimation based on building types and density
if buildings is not None:
    # Project to projected CRS for accurate area calculation
    buildings = buildings.to_crs('EPSG:31256')  # UTM zone 33N for Germany
    
    # Calculate building area
    buildings['building_area'] = buildings.geometry.area
    
    # Get centroids for grid analysis
    buildings_centroids = buildings.copy()
    buildings_centroids['geometry'] = buildings_centroids.geometry.centroid
    buildings_centroids = buildings_centroids.to_crs('EPSG:4326')
    
    # Aggregate by 0.01 degree grid cells (roughly 1km x 1km)
    buildings_centroids['grid_x'] = (buildings_centroids.geometry.x // 0.01 * 0.01).round(2)
    buildings_centroids['grid_y'] = (buildings_centroids.geometry.y // 0.01 * 0.01).round(2)
    
    # Demand estimation: total building area per grid cell
    demand_grid = buildings_centroids.groupby(['grid_x', 'grid_y']).agg({
        'building_area': 'sum',
        'geometry': 'count'
    }).reset_index()
    demand_grid.columns = ['lon', 'lat', 'building_area_m2', 'building_count']
    
    # Convert building area to estimated heat demand (rough estimate: 50 kWh/m²/year for heating)
    demand_grid['estimated_heat_demand_kWh_year'] = demand_grid['building_area_m2'] * 50
    
    # Create GeoDataFrame
    demand_grid['geometry'] = [Point(x, y) for x, y in zip(demand_grid['lon'], demand_grid['lat'])]
    gdf_demand = gpd.GeoDataFrame(demand_grid, geometry='geometry', crs='EPSG:4326')
    
    print(f"   ✓ Identified {len(gdf_demand)} demand grid cells")
    total_demand = gdf_demand['estimated_heat_demand_kWh_year'].sum()
    print(f"   ✓ Total estimated heat demand: {total_demand:,.0f} kWh/a")
else:
    print("   ⚠️  Could not analyze demand")
    gdf_demand = None

# --- 5. EXPORT GEOJSON FOR ARCGIS PRO ---
print("\n💾 Step 5: Exporting GeoJSON files for ArcGIS Pro...")

output_dir = 'data/arcgis_exports'
os.makedirs(output_dir, exist_ok=True)

# Export wasteheat supply
supply_export = supply_in_bremen[[
    'Adresse', 'PLZ', 'Ort', 'Heat_kWh_Year', 'Cluster', 'geometry'
]].copy()
supply_export.columns = ['Address', 'PostalCode', 'City', 'Heat_Supply_kWh_Year', 'Supply_Cluster', 'geometry']

supply_geojson_path = f'{output_dir}/wasteheat_supply.geojson'
supply_export.to_file(supply_geojson_path, driver='GeoJSON')
print(f"   ✓ Supply layer: {supply_geojson_path} ({len(supply_export)} points)")

# Export demand
if gdf_demand is not None:
    demand_export = gdf_demand[[
        'lon', 'lat', 'building_count', 'building_area_m2', 
        'estimated_heat_demand_kWh_year', 'geometry'
    ]].copy()
    demand_export.columns = ['Longitude', 'Latitude', 'Building_Count', 'Building_Area_m2', 
                             'Estimated_Heat_Demand_kWh_Year', 'geometry']
    
    demand_geojson_path = f'{output_dir}/heat_demand.geojson'
    demand_export.to_file(demand_geojson_path, driver='GeoJSON')
    print(f"   ✓ Demand layer: {demand_geojson_path} ({len(demand_export)} grid cells)")

# --- 6. CALCULATE EFFICIENCY POTENTIAL ---
print("\n📊 Step 6: Calculating efficiency potential...")

if gdf_demand is not None and len(supply_in_bremen) > 0:
    # For each demand point, find nearest supply
    from scipy.spatial.distance import cdist
    
    supply_coords = np.array([[p.x, p.y] for p in supply_in_bremen.geometry])
    demand_coords = np.array([[p.x, p.y] for p in gdf_demand.geometry])
    
    # Calculate distances (in degrees, rough approximation)
    distances = cdist(demand_coords, supply_coords, metric='euclidean')
    
    # Find nearest supply for each demand
    nearest_supply_idx = np.argmin(distances, axis=1)
    nearest_distances_km = distances[np.arange(len(distances)), nearest_supply_idx] * 111  # Convert degrees to km
    
    gdf_demand['nearest_supply_distance_km'] = nearest_distances_km
    gdf_demand['nearest_supply_idx'] = nearest_supply_idx
    
    # Calculate efficiency score (higher = better match)
    # Efficiency = Supply capacity / Distance (closer and more supply = better)
    gdf_demand['efficiency_score'] = np.zeros(len(gdf_demand))
    for i in range(len(gdf_demand)):
        supply_heat = supply_in_bremen.iloc[nearest_supply_idx[i]]['Heat_kWh_Year']
        distance = nearest_distances_km[i]
        if distance > 0:
            gdf_demand.loc[i, 'efficiency_score'] = supply_heat / distance
        else:
            gdf_demand.loc[i, 'efficiency_score'] = supply_heat
    
    print(f"   ✓ Efficiency analysis complete")
    print(f"   ✓ Average distance to nearest supply: {nearest_distances_km.mean():.2f} km")
    
    # Export with efficiency scores
    potential_export = gdf_demand[[
        'lon', 'lat', 'building_count', 'estimated_heat_demand_kWh_year',
        'nearest_supply_distance_km', 'efficiency_score', 'geometry'
    ]].copy()
    potential_export.columns = [
        'Longitude', 'Latitude', 'Building_Count', 'Heat_Demand_kWh_Year',
        'Distance_to_Supply_km', 'Efficiency_Potential_Score', 'geometry'
    ]
    
    potential_geojson_path = f'{output_dir}/efficiency_potential.geojson'
    potential_export.to_file(potential_geojson_path, driver='GeoJSON')
    print(f"   ✓ Efficiency layer: {potential_geojson_path}")

# --- 7. CREATE HIGH-POTENTIAL ZONES ---
print("\n🎯 Step 7: Identifying high-potential zones...")

if gdf_demand is not None:
    # Define high-potential as top 25% efficiency scores
    threshold = gdf_demand['efficiency_score'].quantile(0.75)
    high_potential = gdf_demand[gdf_demand['efficiency_score'] >= threshold].copy()
    
    high_potential_export = high_potential[[
        'lon', 'lat', 'building_count', 'estimated_heat_demand_kWh_year',
        'nearest_supply_distance_km', 'efficiency_score', 'geometry'
    ]].copy()
    
    high_potential_path = f'{output_dir}/high_potential_zones.geojson'
    high_potential_export.to_file(high_potential_path, driver='GeoJSON')
    
    print(f"   ✓ High-potential zones: {high_potential_path}")
    print(f"   ✓ Found {len(high_potential)} high-potential locations")
    total_potential = high_potential['estimated_heat_demand_kWh_year'].sum()
    print(f"   ✓ Total potential demand in high zones: {total_potential:,.0f} kWh/a")

# --- 8. SUMMARY REPORT ---
print("\n" + "=" * 80)
print("SUMMARY FOR ARCGIS PRO")
print("=" * 80)

print(f"\n📍 WASTEHEAT SUPPLY:")
print(f"   • Locations: {len(supply_in_bremen)}")
print(f"   • Total capacity: {supply_in_bremen['Heat_kWh_Year'].sum():,.0f} kWh/a")
print(f"   • Top cluster: Cluster {supply_in_bremen['Cluster'].mode()[0]} with {(supply_in_bremen[supply_in_bremen['Cluster']==supply_in_bremen['Cluster'].mode()[0]]['Heat_kWh_Year'].sum()):,.0f} kWh/a")

if gdf_demand is not None:
    print(f"\n🏢 HEAT DEMAND:")
    print(f"   • Demand grid cells: {len(gdf_demand)}")
    demand_sum = gdf_demand['estimated_heat_demand_kWh_year'].sum()
    print(f"   • Total estimated demand: {demand_sum:,.0f} kWh/a")
    building_count = buildings_centroids['geometry'].count()
    print(f"   • Buildings analyzed: {building_count}")
    
    print(f"\n⚡ EFFICIENCY POTENTIAL:")
    print(f"   • High-potential zones: {len(high_potential)}")
    print(f"   • Avg distance to supply: {gdf_demand['nearest_supply_distance_km'].mean():.2f} km")
    print(f"   • Best efficiency zone: {gdf_demand['efficiency_score'].max():.0f}")

print(f"\n📁 OUTPUT FILES:")
print(f"   1. {supply_geojson_path}")
print(f"   2. {demand_geojson_path if gdf_demand is not None else 'N/A'}")
print(f"   3. {potential_geojson_path if gdf_demand is not None else 'N/A'}")
print(f"   4. {high_potential_path if gdf_demand is not None else 'N/A'}")

print(f"\n✅ Ready for ArcGIS Pro!")
print(f"   Import these GeoJSON files as layers in your ArcGIS Pro project")
print(f"   Overlay them to visualize supply-demand matching and optimization potential")
print("=" * 80)
