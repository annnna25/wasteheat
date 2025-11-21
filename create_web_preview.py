"""
Interactive Web Preview for Wasteheat Bremen Analysis
Creates an HTML visualization showing all layers before ArcGIS Pro import
"""

import json
import geopandas as gpd
import pandas as pd

print("Creating interactive web preview...")

# --- LOAD DATA ---
gdf_supply = gpd.read_file('data/arcgis_exports/wasteheat_supply.geojson')
gdf_demand = gpd.read_file('data/arcgis_exports/heat_demand.geojson')
gdf_efficiency = gpd.read_file('data/arcgis_exports/efficiency_potential.geojson')
gdf_high_potential = gpd.read_file('data/arcgis_exports/high_potential_zones.geojson')

# --- HTML TEMPLATE ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8' />
    <title>Wasteheat Analysis - Bremen</title>
    <meta name='viewport' content='initial-scale=1,maximum-scale=1,user-scalable=no' />
    <script src='https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js'></script>
    <link href='https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css' rel='stylesheet' />
    <script src='https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.0/dist/leaflet.markercluster.js'></script>
    <link href='https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.0/dist/MarkerCluster.css' rel='stylesheet' />
    <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        .legend {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        .legend h3 { margin: 0 0 10px 0; font-size: 14px; }
        .legend-item { margin: 5px 0; }
        .legend-color { 
            display: inline-block; 
            width: 15px; 
            height: 15px; 
            margin-right: 5px;
            border-radius: 50%;
        }
        .info {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }
        .layer-control {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }
        .layer-control label { display: block; margin: 5px 0; }
    </style>
</head>
<body>
    <div id='map'></div>
    
    <div style='position: absolute; top: 10px; right: 10px; z-index: 1000; width: 250px;'>
        <div class='layer-control'>
            <h4 style='margin-top: 0;'>Layer Control</h4>
            <label><input type='checkbox' id='supply-toggle' checked> Heat Supply (Wasteheat)</label>
            <label><input type='checkbox' id='demand-toggle' checked> Heat Demand</label>
            <label><input type='checkbox' id='efficiency-toggle' checked> Efficiency Potential</label>
            <label><input type='checkbox' id='high-potential-toggle' checked> High-Potential Zones</label>
        </div>
        
        <div class='legend' style='margin-top: 10px;'>
            <h3>Statistics</h3>
            <div style='font-size: 11px;'>
                <strong>Supply:</strong><br>
                Locations: 24,683<br>
                Capacity: 5.2M kWh/a<br><br>
                <strong>Demand:</strong><br>
                Cells: 357<br>
                Estimated: 1.3B kWh/a<br><br>
                <strong>Potential:</strong><br>
                High-zones: 55<br>
                Avg Distance: 3.85 km
            </div>
        </div>
    </div>

    <script>
        // Initialize map
        const map = L.map('map').setView([53.08, 8.80], 11);
        
        // Base layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Layer groups
        const supplyLayer = L.layerGroup();
        const demandLayer = L.layerGroup();
        const efficiencyLayer = L.layerGroup();
        const highPotentialLayer = L.layerGroup();

        // Add to map by default
        supplyLayer.addTo(map);
        demandLayer.addTo(map);
        efficiencyLayer.addTo(map);
        highPotentialLayer.addTo(map);

        // Layer toggles
        document.getElementById('supply-toggle').addEventListener('change', (e) => {
            if (e.target.checked) map.addLayer(supplyLayer);
            else map.removeLayer(supplyLayer);
        });
        document.getElementById('demand-toggle').addEventListener('change', (e) => {
            if (e.target.checked) map.addLayer(demandLayer);
            else map.removeLayer(demandLayer);
        });
        document.getElementById('efficiency-toggle').addEventListener('change', (e) => {
            if (e.target.checked) map.addLayer(efficiencyLayer);
            else map.removeLayer(efficiencyLayer);
        });
        document.getElementById('high-potential-toggle').addEventListener('change', (e) => {
            if (e.target.checked) map.addLayer(highPotentialLayer);
            else map.removeLayer(highPotentialLayer);
        });

        // Supply layer data (clustered)
        const supplyData = SUPPLY_DATA_PLACEHOLDER;
        const supplyCluster = L.markerClusterGroup();
        
        supplyData.features.forEach(feature => {
            const heat = feature.properties.Heat_Supply_kWh_Year || 0;
            const color = heat > 100000 ? '#d62728' : heat > 10000 ? '#ff7f0e' : '#2ca02c';
            
            L.circleMarker([
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
            ], {
                radius: Math.min(heat / 10000, 15),
                color: color,
                weight: 1,
                opacity: 0.7,
                fillOpacity: 0.6
            }).bindPopup(`
                <b>Wasteheat Source</b><br>
                Address: ${feature.properties.Address}<br>
                Heat: ${(heat / 1000).toFixed(0)} MWh/a<br>
                City: ${feature.properties.City}
            `).addTo(supplyCluster);
        });
        supplyLayer.addLayer(supplyCluster);

        // Demand layer
        const demandData = DEMAND_DATA_PLACEHOLDER;
        demandData.features.forEach(feature => {
            const demand = feature.properties.Estimated_Heat_Demand_kWh_Year || 0;
            const buildings = feature.properties.Building_Count || 0;
            
            L.circleMarker([
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
            ], {
                radius: Math.log(demand + 1) / 5,
                color: '#0066cc',
                weight: 1,
                opacity: 0.5,
                fillOpacity: 0.3
            }).bindPopup(`
                <b>Heat Demand Zone</b><br>
                Buildings: ${buildings}<br>
                Estimated Demand: ${(demand / 1000000).toFixed(1)} GWh/a
            `).addTo(demandLayer);
        });

        // Efficiency layer
        const efficiencyData = EFFICIENCY_DATA_PLACEHOLDER;
        efficiencyData.features.forEach(feature => {
            const efficiency = feature.properties.Efficiency_Potential_Score || 0;
            const distance = feature.properties.Distance_to_Supply_km || 0;
            
            L.circleMarker([
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
            ], {
                radius: 6,
                color: efficiency > 200000 ? '#8B008B' : efficiency > 100000 ? '#4B0082' : '#9370DB',
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.6
            }).bindPopup(`
                <b>Efficiency Potential</b><br>
                Score: ${efficiency.toFixed(0)}<br>
                Distance: ${distance.toFixed(1)} km
            `).addTo(efficiencyLayer);
        });

        // High potential zones
        const highPotentialData = HIGH_POTENTIAL_DATA_PLACEHOLDER;
        highPotentialData.features.forEach(feature => {
            const efficiency = feature.properties.Efficiency_Potential_Score || 0;
            
            L.circleMarker([
                feature.geometry.coordinates[1],
                feature.geometry.coordinates[0]
            ], {
                radius: 8,
                color: '#FF1493',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.7
            }).bindPopup(`
                <b>HIGH POTENTIAL ZONE</b><br>
                Efficiency Score: ${efficiency.toFixed(0)}<br>
                Demand: ${(feature.properties.Heat_Demand_kWh_Year / 1000000).toFixed(1)} GWh/a<br>
                Buildings: ${feature.properties.Building_Count}
            `).addTo(highPotentialLayer);
        });
    </script>
</body>
</html>
"""

# Convert GeoJSON to JSON strings for embedding
import json
supply_geojson = json.loads(gdf_supply.to_json())
demand_geojson = json.loads(gdf_demand.to_json())
efficiency_geojson = json.loads(gdf_efficiency.to_json())
high_potential_geojson = json.loads(gdf_high_potential.to_json())

# Replace placeholders
html_content = html_content.replace('SUPPLY_DATA_PLACEHOLDER', json.dumps(supply_geojson))
html_content = html_content.replace('DEMAND_DATA_PLACEHOLDER', json.dumps(demand_geojson))
html_content = html_content.replace('EFFICIENCY_DATA_PLACEHOLDER', json.dumps(efficiency_geojson))
html_content = html_content.replace('HIGH_POTENTIAL_DATA_PLACEHOLDER', json.dumps(high_potential_geojson))

# Write HTML file
output_file = 'index_wasteheat.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ Web preview created: {output_file}")
print(f"   Open in browser to preview all layers before ArcGIS Pro import")
