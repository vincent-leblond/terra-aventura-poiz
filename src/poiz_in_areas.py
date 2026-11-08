"""
Compute Poï'z within areas
"""

# %%
# imports

from shapely.geometry import Polygon
from utils import *

# %%
# get all list of Poï'z

data = get_poiz()

# %%
# remove poiz in Limoges

coords = [
    (1.19046, 45.78361),  # Point 1: Bottom-left 45.78361,1.19046
    (1.18480, 45.89476),  # Point 2: Top-left 45.89476,1.18480
    (1.35376, 45.88190),  # Point 3: Top-right 45.88190,1.35376
    (1.35863, 45.78562),  # Point 4: Bottom-right 45.78562,1.35863
]

# 2. Create the Shapely Polygon
polygon = Polygon(coords)
polygon_gdf = gpd.GeoDataFrame(geometry=[polygon], crs=4326)

# Perform a left spatial join looking for points within any polygon
joined = gpd.sjoin(data, polygon_gdf, how="left", predicate="within")

# Points inside polygons will get an index from polygons (index_right)
# Filter for points where index_right is NaN (points outside)
data = joined[joined["index_right"].isna()].drop(columns=["index_right"])

print(len(data), "poiz sans Limoges")

polygon_gdf.to_file("../data/outputs/polygon.gpkg", driver="GPKG")

# %%
# get communes

communes = get_communes()

# %%
# compute stats for each municipality


def poiz_routing(
    coordinates, poiz=data, max_time=30, max_distance=100, return_poiz=False
):

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
        "costing_options": {"auto": {"top_speed": 90, "use_highways": 0.3}},
    }

    try:
        results = matrix(body)
        results = results[results["time"] <= max_time]

        if return_poiz:
            return results, poiz
        else:
            return len(results)
    except ValueError:
        return None
    except:
        return None


# %%
# export for one city

results, poiz = poiz_routing(
    list(communes.query("id=='87017'")["geometry"])[0], return_poiz=True
)
# poiz.to_file("../data/outputs/communes_selected_poiz.gpkg", driver="GPKG")

poiz = poiz.reset_index(drop=True).reset_index()

results = results.merge(poiz, how="left", left_on="to_index", right_on="index")

gpd.GeoDataFrame(
    results, geometry=gpd.points_from_xy(results.lng, results.lat), crs=4326
).to_file("../data/outputs/communes_selected_poiz.gpkg", driver="GPKG")

print(len(results))

# %%
#

# communes = communes[communes["id"].isin(["24227", "87177"])]
communes["count_poiz_30mn"] = communes["geometry"].progress_map(poiz_routing)

print(communes.sort_values("count_poiz_30mn", ascending=False).head())

communes.to_file("../data/outputs/communes_poiz.gpkg", driver="GPKG")

# %%
#
