"""
Compute Poï'z within areas
"""

# %%
# imports

from utils import *

# %%
# TODO compute time and distance with valhalla between two coordinates

body = {
    "sources": [
        {"lat": 45.3849680, "lon": 1.1638579},
        {"lat": 45.39052, "lon": 1.00609},
    ],
    "targets": [
        {"lat": 45.326914, "lon": 1.183304},
        {"lat": 45.335152, "lon": 1.048799},
    ],
    "costing": "auto",
}

print(matrix(body))

# %%
# TODO compute from one point, time and distance to all Poï'z & compute results (synthesis and list of Poï'z)

# %%
# TODO from all cities to all Poï'z

# %%
# get all list of Poï'z

data = get_poiz()

# %%
#
