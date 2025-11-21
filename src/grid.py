# src/grid.py
import geopandas as gpd
from shapely.geometry import box
import numpy as np

def create_grid(gdf_boundary, cell_size_m=200):
    # boundary in metric CRS
    bounds = gdf_boundary.total_bounds  # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = bounds
    # generate grid
    x_coords = np.arange(minx, maxx, cell_size_m)
    y_coords = np.arange(miny, maxy, cell_size_m)
    polys = []
    for x in x_coords:
        for y in y_coords:
            polys.append(box(x, y, x+cell_size_m, y+cell_size_m))
    grid = gpd.GeoDataFrame({'geometry':polys}, crs=gdf_boundary.crs)
    # clip to boundary
    grid = gpd.overlay(grid, gdf_boundary, how='intersection')
    grid['cell_id'] = range(len(grid))
    return grid

# Beispiel:
# grid = create_grid(bremen, cell_size_m=200)
# grid.to_file("data/bremen_grid_200m.gpkg", layer="grid", driver="GPKG")