# src/optimization.py
import pulp
import numpy as np

def optimize_allocation(sources, sinks):
    # sources: GeoDataFrame with columns ['id','supply_mw','geometry']
    # sinks: GeoDataFrame with columns ['id','demand_mw','geometry']
    # Build cost matrix = distance (m) converted to cost €/MW
    src_ids = sources['id'].tolist()
    sink_ids = sinks['id'].tolist()
    dist = {}
    for i, s in sources.iterrows():
        for j, t in sinks.iterrows():
            d = s.geometry.centroid.distance(t.geometry.centroid)
            dist[(s.id, t.id)] = d/1000.0  # km as proxy
    # Problem
    prob = pulp.LpProblem("heat_alloc", pulp.LpMinimize)
    # Variables flow[(i,j)]
    flow = pulp.LpVariable.dicts("flow", (src_ids, sink_ids), lowBound=0, cat='Continuous')
    # Objective
    prob += pulp.lpSum([flow[i][j] * dist[(i,j)] for i in src_ids for j in sink_ids])
    # supply constraints
    for i in src_ids:
        prob += pulp.lpSum([flow[i][j] for j in sink_ids]) <= float(sources.loc[sources.id==i,'supply_mw'])
    # demand constraints
    for j in sink_ids:
        prob += pulp.lpSum([flow[i][j] for i in src_ids]) >= float(sinks.loc[sinks.id==j,'demand_mw'])
    prob.solve()
    # Collect results
    results = []
    for i in src_ids:
        for j in sink_ids:
            val = pulp.value(flow[i][j])
            if val and val>0:
                results.append({'source':i,'sink':j,'flow_mw':val})
    return results
