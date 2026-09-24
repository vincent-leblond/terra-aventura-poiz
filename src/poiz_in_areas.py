"""
Compute Poï'z within areas
"""

# %%
# imports

from utils import *

# %%
# get all list of Poï'z

data = get_poiz()

# %%
# get communes

communes = get_communes()

# %%
# compute stats for each municipality


def poiz_routing(coordinates, poiz=data, max_time=30, max_distance=100):

    coordinates_x = coordinates.x
    coordinates_y = coordinates.y

    poiz["distance"] = poiz.apply(
        lambda x: haversine((coordinates_y, coordinates_x), (x["lat"], x["lng"])),
        axis=1,
    )  # return distance in km

    poiz = poiz[poiz["distance"] <= max_distance].drop(columns=["geometry"])

    # format data
    poiz_coordinates = (
        poiz[["lng", "lat"]].rename(columns={"lng": "lon"}).to_dict("records")
    )

    communes_coordinates = [{"lat": coordinates_y, "lon": coordinates_x}]

    body = {
        "sources": communes_coordinates,
        "targets": poiz_coordinates,
        "costing": "auto",
    }

    results = matrix(body)

    return len(results[results["time"] <= max_time])


# communes = communes[communes["id"].isin(["24227", "87177"])]
communes["count_poiz_30mn"] = communes["geometry"].progress_map(poiz_routing)

print(communes.sort_values("count_poiz_30mn", ascending=False).head())

communes.to_file("../data/outputs/communes_poiz.gpkg", driver="GPKG")

# %%
#
