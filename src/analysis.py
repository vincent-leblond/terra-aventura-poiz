# %%
# Initialisation
import os
import json
import requests
import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from bs4 import BeautifulSoup
from shapely.geometry import Point
from datetime import datetime
from pandarallel import pandarallel

pandarallel.initialize(progress_bar=True, verbose=2)

COORDINATES = (1.67979, 46.24145)
COORDINATES = (1.60495, 46.22789)
DISTANCE = 25000

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
#


def poiz_info(id):
    url = f"https://www.terra-aventura.fr/parcours/geocachingmap-noderender/{id}"

    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "html.parser")
    count = 0
    km = "-"
    time = "-"
    divs = soup.find_all("div", class_="field__item")
    for div in divs:
        count += 1
        if count == len(divs) - 1:
            km = div.text
        elif count == len(divs):
            time = div.text

    # assert km != "-" and time != "-", f"Error for {id}, {km}, {time}, {url}"

    return km, time


poiz_info(990)

# %%
# Read data json data

colors = pd.DataFrame(
    {
        "poiz_raw_name": [
            "zabeth",
            "zigomatix",
            "zeidon",
            "zinzin",
            "zart",
            "ziclou",
            "zouch",
            "zacquet",
            "zefaim",
            "zisseo",
            "zeroik",
            "0",
            "zarthus",
            "zelle",
            "zabdo",
            "zonelib",
            "zalambic",
            "zahan",
            "map/zegraff-map",
            "zouti",
            "zektonic",
            "zechopp",
            "zenight",
            "zohee",
            "zecolo",
            "zilex",
            "zepapeur",
            "zaitek",
            "ziraider",
            "zamela",
            "zirrinzi",
        ],
        "poiz_name": [
            "zabeth",
            "zigomatix",
            "zeidon",
            "zinzin",
            "zart",
            "ziclou",
            "zouch",
            "zacquet",
            "zefaim",
            "zisseo",
            "zeroik",
            "zetoulu",
            "zarthus",
            "zelle",
            "zabdo",
            "zonelib",
            "zalambic",
            "zahan",
            "zegraff",
            "zouti",
            "zektonic",
            "zechopp",
            "zenight",
            "zohee",
            "zecolo",
            "zilex",
            "zepapeur",
            "zaitek",
            "ziraider",
            "zamela",
            "zirrinzi",
        ],
        "color": [
            "#EED100",
            "#F2BD65",
            "#3B8FD8",
            "#AA68A7",
            "#12DFE4",
            "#5B0D01",
            "#B29167",
            "#C29621",
            "#A89C81",
            "#446792",
            "#959595",
            "#0F2E3F",
            "#0CE500",
            "#9D2F83",
            "#FEB200",
            "#676F3C",
            "#564331",
            "#C4874D",
            "#EF1C77",
            "#E43B00",
            "#AE8D68",
            "#C7510B",
            "#416195",
            "#E1BB28",
            "#9AB600",
            "#665746",
            "#859B00",
            "#58768E",
            "#D25100",
            "#F51CE4",
            "#FD3635",
        ],
    }
)

poiz = data["geocaching_map"]["markers"]
poiz_df = pd.DataFrame(poiz).query("type=='geocaching_cache'")
poiz_df["lat"] = poiz_df.apply(lambda x: float(x["lat"]), axis=1)
poiz_df["lng"] = poiz_df.apply(lambda x: float(x["lng"]), axis=1)

poiz_df["poiz_raw_name"] = poiz_df["icon"].map(lambda x: x.split("_")[-1].split(".")[0])
poiz_df = poiz_df.merge(colors, how="left", on="poiz_raw_name")

poiz_df = poiz_df.rename(
    columns={
        "poiz_name": "Nom",
        "title": "Titre",
        "field_difficulty": "Niveau",
        "field_ground": "Terrain",
        "field_maintenance": "Maintenance",
        "color": "Couleur",
    }
)

poiz_df["Kilométrage"], poiz_df["Durée"] = zip(*poiz_df["nid"].parallel_map(poiz_info))

poiz_gdf = poiz_df[
    [
        "Nom",
        "Titre",
        "Niveau",
        "Terrain",
        "Durée",
        "Kilométrage",
        "Maintenance",
        "Couleur",
        "lng",
        "lat",
    ]
]

poiz_gdf = gpd.GeoDataFrame(
    poiz_gdf, geometry=gpd.points_from_xy(poiz_gdf.lng, poiz_gdf.lat), crs=4326
)

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
