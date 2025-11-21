# src/ingest.py
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def load_bremen_boundary(path_to_shapefile):
    gdf = gpd.read_file(path_to_shapefile).to_crs(epsg=3857)  # WebMercator für Meter
    return gdf

def load_osm_buildings(shp_path):
    buildings = gpd.read_file(shp_path).to_crs(epsg=3857)
    return buildings

def load_firm_excel(xlsx_path):
    df = pd.read_excel(xlsx_path)
    # Erwartete Spalten: name, lat, lon, abwaerme_mw, temperatur_c, waermebedarf_mw (optional)
    df = df.dropna(subset=['lat','lon'])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326").to_crs(epsg=3857)
    return gdf

# Beispiel Verwendung
if __name__ == "__main__":
    bremen = load_bremen_boundary("data/bremen_boundary.shp")
    buildings = load_osm_buildings("data/bremen-buildings.shp")
    firms = load_firm_excel("data/companies_heat.xlsx")
    print(bremen.total_bounds, len(buildings), len(firms))
