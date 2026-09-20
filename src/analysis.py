# %%
# Initialisation

from geopy.distance import geodesic
from shapely.geometry import Point
from datetime import datetime
from utils import *

COORDINATES = (1.67979, 46.24145)
COORDINATES = (1.60495, 46.22789)
DISTANCE = 25000

DISTANCE_TO_STATION = 1500  # meters

GARE_SNCF = (
    "https://ressources.data.sncf.com/api/v2/catalog/datasets/"
    + "referentiel-gares-voyageurs/exports/geojson"
    + "?select=uic_code%2Cgare_alias_libelle_fronton%2Cwgs_84"
    + "&limit=-1&timezone=UTC&pretty=false"
)


OUTPUT_DIR = "../data/outputs/"

if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

# %%
#

poiz_info(990)

# %%
# Read data json data


poiz_gdf = get_poiz()

date = datetime.today().strftime("%Y-%m-%d")

poiz_gdf.to_file(f"../data/outputs/poiz_{date}.geojson", driver="GeoJSON")

# %%
# create buffer from point
points = gpd.GeoSeries([Point(COORDINATES)], crs=4326)

# Buffer the points using a square cap style
# Note cap_style: round = 1, flat = 2, square = 3
buffer = points.to_crs(2154).buffer(DISTANCE, cap_style=1)
buffer_gdf = gpd.GeoDataFrame(
    pd.DataFrame({"col": [0]}), geometry=buffer, crs=2154
).to_crs(4326)

# %%
#

buffer_gdf.to_file("../data/outputs/buffer.geojson", driver="GeoJSON")

cross = gpd.sjoin(poiz_gdf, buffer_gdf)

cross.drop(columns=["field_departments_cities", "field_quests"]).to_file(
    "../data/outputs/cross.geojson", driver="GeoJSON"
)

print("Nombre de poi'z:", len(cross))

# %%
# Read stations
stations = gpd.read_file(GARE_SNCF)
stations["lat"] = stations["geometry"].y
stations["lng"] = stations["geometry"].x
stations = stations.query("lat==lat")
stations["key"] = 1
stations = stations[["uic_code", "gare_alias_libelle_fronton", "lat", "lng", "key"]]

stations_gdf = gpd.GeoDataFrame(
    stations, geometry=gpd.points_from_xy(stations.lng, stations.lat), crs=4326
)
stations_buffer = gpd.GeoDataFrame(
    stations_gdf,
    geometry=stations_gdf.to_crs(2154).buffer(DISTANCE_TO_STATION),
    crs=2154,
).to_crs(4326)


# %%
# spatial join

geotable = gpd.sjoin(
    stations_buffer.to_crs(2154),
    poiz_gdf.to_crs(2154),
    how="right",
    lsuffix="x",
    rsuffix="y",
).query("uic_code==uic_code")

del geotable["field_departments_cities"]
del geotable["field_quests"]
geotable.to_file(OUTPUT_DIR + "geotable.geojson", driver="GeoJSON")


# %%
