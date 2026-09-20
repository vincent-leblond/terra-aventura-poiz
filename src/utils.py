"""
Utils
"""

import os
import json
import requests
import geopandas as gpd
import pandas as pd
from pandarallel import pandarallel
from bs4 import BeautifulSoup

pandarallel.initialize(progress_bar=True, verbose=2)

# Set display options
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 1000)
pd.set_option("mode.chained_assignment", None)

VALHALLA_URL = "http://localhost:8002/"


COLORS = pd.DataFrame(
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


def get_poiz():
    URL = "https://www.terra-aventura.fr/parcours"

    html_text = requests.get(URL).text
    soup = BeautifulSoup(html_text, "html.parser")
    for script in soup.find_all("script"):
        if script.get("data-drupal-selector") == "drupal-settings-json":
            poiz_data = script.contents[0]

    data = json.loads(poiz_data)

    poiz = data["geocaching_map"]["markers"]
    poiz_df = pd.DataFrame(poiz).query("type=='geocaching_cache'")
    poiz_df["lat"] = poiz_df.apply(lambda x: float(x["lat"]), axis=1)
    poiz_df["lng"] = poiz_df.apply(lambda x: float(x["lng"]), axis=1)

    poiz_df["poiz_raw_name"] = poiz_df["icon"].map(
        lambda x: x.split("_")[-1].split(".")[0]
    )
    poiz_df = poiz_df.merge(COLORS, how="left", on="poiz_raw_name")

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

    poiz_df["Kilométrage"], poiz_df["Durée"] = zip(
        *poiz_df["nid"].parallel_map(poiz_info)
    )

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

    return poiz_gdf


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


def request_valhalla(
    service: str,
    body,
    url: str = VALHALLA_URL,
) -> requests.Response:
    """
    Make a POST request to Tellae's valhalla instance.

    See https://valhalla.github.io/valhalla/api/ for the list of available services.

    :param service: valhalla service (without leading /)
    :param body: request body
    :param url: valhalla url

    :return: request Response
    """
    # build the request url
    url = os.path.join(url, service)

    # make the request
    response = requests.post(url, json=body)

    return response


def matrix(body):
    """
    Compute time / distance matrix using valhalla

    :param body: sources and targets dict

    :return: dataframe
    """

    r = request_valhalla("sources_to_targets", body)

    # check response status
    if r.status_code != 200:
        if r.status_code == 400:
            error_body = r.json()
            error_code = error_body["error_code"]
            if error_code == 171:
                raise NoDataException

            raise ValueError(
                f"Valhalla isochrone request failed: {error_body['error']}"
            )
        else:
            r.raise_for_status()

    result_df = pd.concat(
        [pd.DataFrame(result) for result in r.json()["sources_to_targets"]]
    )
    result_df["time"] = result_df["time"] / 60

    return result_df
