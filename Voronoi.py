import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np

from scipy.spatial import Voronoi
from shapely.geometry import Polygon
from pathlib import Path


# carregar database
base_path = Path(__file__).parent
file_path = base_path / "opendatabcn_esports_instalacions-esportives.csv"

df = pd.read_csv(file_path, encoding='utf-16', sep=',')

# netejar noms
df.columns = df.columns.str.strip()

# eliminar buits
df = df.dropna(subset=['geo_epgs_4326_lon', 'geo_epgs_4326_lat'])

# centre de Barcelona
center_lat = 41.3851
center_lon = 2.1734

# funció distància (simple)
def distance(lat, lon):
    return np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2)

# calcular distància
df['dist'] = distance(df['geo_epgs_4326_lat'], df['geo_epgs_4326_lon'])

# filtrar punts llunyans
df = df[df['dist'] < 0.3]

# identificar longituds i latituds
gdf = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(
        df['geo_epgs_4326_lon'],
        df['geo_epgs_4326_lat']
    ),
    crs="EPSG:4326"
)

# transformar a sistema mètric
gdf = gdf.to_crs(epsg=3857)

# VORONOI
points = np.array([(geom.x, geom.y) for geom in gdf.geometry])
vor = Voronoi(points)

# límits
min_x, min_y, max_x, max_y = gdf.total_bounds

# bounding box
bbox = Polygon([
    (min_x, min_y),
    (max_x, min_y),
    (max_x, max_y),
    (min_x, max_y)
])

# crear polígons i clip
regions = []

for region in vor.regions:
    if not region or -1 in region:
        continue

    polygon = Polygon([vor.vertices[i] for i in region])

    # CLIP al bounding box
    polygon = polygon.intersection(bbox)

    if not polygon.is_empty:
        regions.append(polygon)


# PLOT
fig, ax = plt.subplots(figsize=(10, 10))

# punts
gdf.plot(ax=ax, color='red', markersize=10, alpha=0.7)

# dibuixar polígons Voronoi 
for poly in regions:
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1)

# mapa base
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)

# ajustar vista
ax.set_xlim(min_x, max_x)
ax.set_ylim(min_y, max_y)

# netejar eixos
ax.axis('off')

# títol
plt.title("Àrees d'influència de les instal·lacions esportives (Voronoi)", fontsize=14)

# guardar
plt.savefig("voronoi_map.png", dpi=300, bbox_inches='tight')

plt.show()
