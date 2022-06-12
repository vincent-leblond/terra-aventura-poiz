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
poiz_df = pd.DataFrame(poiz)
poiz_df["key"] = 1
poiz_df["lat"] = poiz_df.apply(lambda x: float(x["lat"]), axis=1)
poiz_df["lng"] = poiz_df.apply(lambda x: float(x["lng"]), axis=1)

# %%
# Read stations
stations = gpd.read_file(GARE_SNCF)
stations["lat"] = stations["geometry"].y
stations["lng"] = stations["geometry"].x
stations = stations.query("lat==lat")
stations["key"] = 1
stations = stations[["uic_code", "gare_alias_libelle_fronton", "lat", "lng", "key"]]

# %%
# Compute distance to all stations


def compute_distance(x):
    try:
        distance = geodesic((x["lat_x"], x["lng_x"]), (x["lat_y"], x["lng_y"])).km
    except:
        distance = 999999
    return distance


df = poiz_df.merge(stations, how="left", on="key")
df = df.query("type=='geocaching_cache'")
df["distance"] = df.apply(lambda x: compute_distance(x), axis=1)

# %%
# Filter data and export to geojson
table = (
    df.query("distance < 1.5")
    .groupby(["nid", "title", "lat_x", "lng_x"], as_index=False)
    .first()
)
geotable = gpd.GeoDataFrame(
    table, geometry=gpd.points_from_xy(table.lng_x, table.lat_x)
)
del geotable["field_departments_cities"]
del geotable["field_quests"]
geotable.to_file(OUTPUT_DIR + "geotable.geojson", driver="GeoJSON")
# %%
