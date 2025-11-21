# src/clustering.py
import numpy as np
from sklearn.cluster import DBSCAN

def cluster_hotspots(grid_gdf, score_col='combined_score', eps=300, min_samples=3):
    # filter candidate cells
    cand = grid_gdf[grid_gdf[score_col] > 0.2].copy()  # threshold anpassen
    coords = np.array(list(zip(cand.geometry.centroid.x, cand.geometry.centroid.y)))
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    cand['cluster'] = db.labels_
    # -1 = noise
    return cand

# Export clusters as polygons by dissolving grid cells per cluster
# clusters = cluster_hotspots(grid)
# cluster_polys = clusters[clusters.cluster!=-1].dissolve(by='cluster')
