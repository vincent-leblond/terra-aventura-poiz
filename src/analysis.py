# %%
# Initialisation
import os
import json
import requests
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from bs4 import BeautifulSoup

# Set display options
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 1000)
pd.set_option("mode.chained_assignment", None)

DISTANCE_TO_STATION = 1500  # meters

GARE_SNCF = (
    "https://ressources.data.sncf.com/api/v2/catalog/datasets/"
    + "referentiel-gares-voyageurs/exports/geojson"
    + "?select=uic_code%2Cgare_alias_libelle_fronton%2Cwgs_84"
    + "&limit=-1&timezone=UTC&pretty=false"
)
URL = "https://www.terra-aventura.fr/parcours"

OUTPUT_DIR = "../data/outputs/"

if not os.path.isdir(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

# %%
# Read data from Terra Aventura web site
html_text = requests.get(URL).text
soup = BeautifulSoup(html_text, "html.parser")
for script in soup.find_all("script"):
    if script.get("data-drupal-selector") == "drupal-settings-json":
        poiz_data = script.contents[0]

data = json.loads(poiz_data)

# %%
# Read data json data
poiz = data["geocaching_map"]["markers"]
poiz_df = pd.DataFrame(poiz).query("type=='geocaching_cache'")
poiz_df["lat"] = poiz_df.apply(lambda x: float(x["lat"]), axis=1)
poiz_df["lng"] = poiz_df.apply(lambda x: float(x["lng"]), axis=1)

poiz_gdf = gpd.GeoDataFrame(
    poiz_df, geometry=gpd.points_from_xy(poiz_df.lng, poiz_df.lat), crs=4326
)

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
