# %%
# Initialisation
import json
import requests
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic

POIZ_JSON = "../data/web_site_export.json"
GARE_SNCF = (
    "https://ressources.data.sncf.com/api/v2/catalog/datasets/"
    + "referentiel-gares-voyageurs/exports/geojson?select=uic_code%2Cgare_alias_libelle_fronton%2Cwgs_84"
    + "&limit=-1&timezone=UTC&pretty=false"
)

# %%
# Read data
with open(POIZ_JSON, "r") as f:
    data = json.load(f)

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

# %%
# Compute distance


def compute_distance(x):
    try:
        distance = geodesic((x["lat"], x["lng"]), (x["lat_y"], x["lng_y"])).km
    except:
        distance = 999999
    return distance


df = poiz_df.merge(stations, how="left", on="key")
df["distance"] = df.apply(lambda x: compute_distance(x), axis=1)
# df = df.query("distance < 3")

# %%
