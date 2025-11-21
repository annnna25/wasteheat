# src/hotspot.py
import libpysal
from esda import G_Local
import numpy as np
import geopandas as gpd

def compute_getis_ord(grid_gdf, value_col='total_abwaerme_mw', k=8):
    # centroid-based spatial weights
    centroids = grid_gdf.copy()
    centroids['x'] = centroids.geometry.centroid.x
    centroids['y'] = centroids.geometry.centroid.y
    coords = list(zip(centroids.x, centroids.y))
    w = libpysal.weights.KNN(coords, k=k)
    # row-standardize
    w.transform = 'r'
    y = grid_gdf[value_col].values
    g_local = G_Local(y, w, transform='r', star=False)
    # g_local.z_sim is z-score, g_local.p_sim p-values
    grid_gdf[f'{value_col}_GiZ'] = g_local.z_sim
    grid_gdf[f'{value_col}_GIp'] = g_local.p_sim
    return grid_gdf

# Beispiel: grid = compute_getis_ord(grid, value_col='total_abwaerme_mw')
