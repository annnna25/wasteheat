# Wasteheat Bremen - ArcGIS Pro Integration Guide

## 🎯 Project Overview

This project analyzes waste heat sources and heat demand across Bremen to identify optimal locations where waste heat can be efficiently utilized.

**Goal:** Find where waste heat supply matches heat demand most efficiently

---

## 📊 Generated Data Layers

### **Layer 1: Wasteheat Supply** ⚙️
**File:** `data/arcgis_exports/wasteheat_supply.geojson`

- **24,683 wasteheat source locations**
- **Total capacity:** 5.2 million kWh/a
- **Attributes:**
  - Address
  - Heat supply (kWh/a)
  - Cluster assignment
  - City

**How to use in ArcGIS Pro:**
1. Add GeoJSON layer
2. Symbolize by Heat_Supply_kWh_Year (larger symbols = more heat)
3. Use graduated colors (Green → Orange → Red) for heat intensity

---

### **Layer 2: Heat Demand** 🏢
**File:** `data/arcgis_exports/heat_demand.geojson`

- **357 demand grid cells** (1km × 1km resolution)
- **Total estimated demand:** 1.3 billion kWh/a
- **Attributes:**
  - Longitude, Latitude
  - Building count per cell
  - Building area (m²)
  - Estimated heat demand (kWh/a)

**Calculation:** Building area × 50 kWh/m²/year (standard heating demand)

**How to use in ArcGIS Pro:**
1. Add GeoJSON layer
2. Symbolize by Building_Area_m2 or Estimated_Heat_Demand_kWh_Year
3. Use heat map visualization (Blue gradient for demand intensity)

---

### **Layer 3: Efficiency Potential** 📈
**File:** `data/arcgis_exports/efficiency_potential.geojson`

- **All 357 demand cells with efficiency scores**
- **Efficiency Score Formula:** (Supply Heat Capacity) / (Distance to Nearest Supply)
- **Attributes:**
  - Distance to nearest supply (km)
  - Efficiency potential score
  - Heat demand
  - Building count

**Interpretation:**
- ✅ Higher score = Better match (close to supply + high demand)
- ❌ Lower score = Worse match (far from supply or low demand)

**How to use in ArcGIS Pro:**
1. Add GeoJSON layer
2. Symbolize by Efficiency_Potential_Score
3. Use 3-color gradient: Green (low) → Yellow (medium) → Purple (high)

---

### **Layer 4: High-Potential Zones** 🎯
**File:** `data/arcgis_exports/high_potential_zones.geojson`

- **Top 25% of efficiency locations** (55 zones)
- **Total potential demand:** 294 million kWh/a
- **Average distance to supply:** 3.85 km

**These are the priority areas for waste heat recovery projects!**

**How to use in ArcGIS Pro:**
1. Add GeoJSON layer
2. Highlight with bright colors (Hot Pink/Magenta)
3. Use for focus analysis and planning

---

## 🗺️ ArcGIS Pro Import Instructions

### Step 1: Create a New Project
```
File → New → Project
```

### Step 2: Add GeoJSON Layers
For each GeoJSON file:
```
Insert → Import → Feature Class from GeoJSON
```

**Add in this order:**
1. Base map (already included: OpenStreetMap)
2. `wasteheat_supply.geojson` (Supply)
3. `heat_demand.geojson` (Demand)
4. `efficiency_potential.geojson` (Efficiency)
5. `high_potential_zones.geojson` (High Priority)

### Step 3: Symbolize Each Layer
- **Supply:** Red/Orange circles, size by heat capacity
- **Demand:** Blue gradient, size by building area
- **Efficiency:** Purple gradient, size by potential
- **High-Potential:** Magenta/Pink, largest symbols

### Step 4: Layer Transparency
Adjust transparency to see overlaps:
- Supply: 70%
- Demand: 50%
- Efficiency: 60%
- High-Potential: 100%

### Step 5: Analyze Overlaps
Look for areas where:
1. **Red (supply) overlaps with Blue (demand)** = Direct connection possible
2. **Purple/Magenta zones** = Priority for development
3. **Close distance + high efficiency** = Quick wins

---

## 💡 Key Insights from Data

### Supply-Demand Balance:
- **Supply:** 5.2M kWh/a
- **Demand:** 1.3B kWh/a
- **Ratio:** Demand is 250× higher than current supply
- **Opportunity:** Huge potential for heat recovery infrastructure

### Geographic Distribution:
- **Average distance** from demand to nearest supply: **3.85 km**
- **This is feasible** for district heating networks (typically 10+ km)

### High-Potential Zones (55 locations):
- Located where building density is high
- Close to waste heat sources
- Estimated to use 294M kWh/a (23% of total demand)

---

## 📋 Next Steps in ArcGIS Pro

### 1. Network Analysis
- Draw lines connecting supply to nearby demand
- Calculate transport distances
- Estimate piping costs

### 2. Buffer Analysis
- Create 2km buffers around wasteheat sources
- See how many buildings are within reach

### 3. Cluster Analysis
- Group high-potential zones by proximity
- Plan district heating networks

### 4. Heat Routing
- Identify optimal paths for heat pipes
- Avoid obstacles (water, dense traffic, etc.)

### 5. Economic Analysis
- Calculate ROI for connecting demand zones
- Estimate payback periods
- Compare to alternative heating solutions

---

## 📊 Data Quality Notes

### Assumptions Made:
1. **Heat demand estimation:** 50 kWh/m²/year (standard for German buildings)
2. **Wasteheat location:** City-level coordinates with small random offsets
   - For precise street-level geocoding, run `data/geocoding/code_all.py` (takes 7+ hours)
3. **Grid cells:** 1km × 1km resolution
   - Can be refined to 500m × 500m for more detail

### Accuracy:
- ✅ Demand estimates are reasonably accurate (building data from OSM)
- ⚠️ Wasteheat locations use city-level precision (good for district planning)
- ⚠️ Distance calculations are approximations (actual routing would be more accurate)

---

## 🔄 Running the Analysis Again

If you need to update the analysis:

```bash
# Regenerate all layers
cd /Users/annasiemer/wasteheat/wasteheat
python data/arcgis_prepare.py

# This will update all GeoJSON files in data/arcgis_exports/
```

---

## 📁 File Locations

```
/Users/annasiemer/wasteheat/wasteheat/
├── data/
│   ├── arcgis_exports/                    # ← ArcGIS Pro imports go here
│   │   ├── wasteheat_supply.geojson      (6.5 MB, 24,683 points)
│   │   ├── heat_demand.geojson           (91 KB, 357 cells)
│   │   ├── efficiency_potential.geojson  (105 KB, 357 cells)
│   │   ├── high_potential_zones.geojson  (16 KB, 55 zones)
│   ├── geocoding/
│   │   ├── pfa_geocoded_local.xlsx       (Geocoded data source)
│   │   ├── clustering_map_local.png      (Preview map)
│   ├── geofabrik bremen/                 (OSM building data)
│   └── pfa_datentabelle_excel Kopie.xlsx (Original wasteheat data)
├── index_wasteheat.html                   (Web preview - open in browser!)
└── data/arcgis_prepare.py                (Script that created all layers)
```

---

## 🚀 Quick Start Checklist

- [ ] Open `index_wasteheat.html` in your browser to see the web preview
- [ ] Review the layer structure and understand each layer
- [ ] Open ArcGIS Pro and create a new project
- [ ] Import all 4 GeoJSON files
- [ ] Symbolize each layer according to the guide
- [ ] Analyze overlaps and identify opportunities
- [ ] Create buffer zones around high-potential areas
- [ ] Calculate distances and network feasibility
- [ ] Export results for presentation

---

## 💬 Questions or Issues?

- **Files missing?** Run `python data/arcgis_prepare.py` again
- **Data needs refinement?** Edit the city_coords in `data/geocoding/code_local.py`
- **Need real addresses?** Run `data/geocoding/code_all.py` (warning: takes many hours)
- **Different demand model?** Edit the `50 kWh/m²/year` assumption in `arcgis_prepare.py`

---

Generated: November 21, 2025
Project: Wasteheat Bremen Analysis for ArcGIS Pro
