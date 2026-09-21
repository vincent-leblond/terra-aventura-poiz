"""
Compute Poï'z within areas
"""

# %%
# imports

from utils import *

# %%
# get communes

communes = get_communes()

# %%
# get all list of Poï'z

data = get_poiz()

# %%
# compute time and distance with valhalla between two coordinates

poiz_coordinates = (
    data[["lng", "lat"]].rename(columns={"lng": "lon"}).to_dict("records")
)

communes_coordinates = (
    communes["geometry"]
    .get_coordinates()
    .rename(columns={"x": "lon", "y": "lat"})
    .to_dict("records")
)

body = {
    "sources": communes_coordinates,
    "targets": poiz_coordinates,
    "costing": "auto",
}

results = matrix(body)

# %%
# TODO add poiz and communes data to results

# %%
#
