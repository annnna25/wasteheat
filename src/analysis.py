# src/analysis.py
import geopandas as gpd
import pandas as pd

def aggregate_heat_to_grid(grid_gdf, firms_gdf, heat_col='abwaerme_mw'):
    # spatial join points -> polygons
    joined = gpd.sjoin(firms_gdf[[heat_col,'geometry']], grid_gdf[['cell_id','geometry']], how='inner', predicate='within')
    agg = joined.groupby('cell_id')[heat_col].sum().rename('total_abwaerme_mw').reset_index()
    grid = grid_gdf.merge(agg, on='cell_id', how='left').fillna(0)
    return grid

def aggregate_demand_to_grid(grid_gdf, buildings_gdf, demand_col='waermebedarf_mw'):
    # Option A: wenn Gebäude konkrete Nachfragewerte haben
    joined = gpd.sjoin(buildings_gdf[[demand_col,'geometry']], grid_gdf[['cell_id','geometry']], how='inner', predicate='within')
    agg = joined.groupby('cell_id')[demand_col].sum().rename('total_waermebedarf_mw').reset_index()
    grid = grid_gdf.merge(agg, on='cell_id', how='left').fillna(0)
    return grid
def analyze_heat_demand_balance(grid_gdf):
    grid_gdf['net_heat_mw'] = grid_gdf['total_abwaerme_mw'] - grid_gdf['total_waermebedarf_mw']
    return grid_gdf