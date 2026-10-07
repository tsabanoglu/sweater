# constraints

# sweater/constants.py

# Standard neck circumferences by size (cm)
NECK_SIZES = {
    "XS": 34, "S": 36, "M": 38, "L": 40, "XL": 42, "XXL": 44, "XXXL": 46,
}

# Standard finished chest measurements by size (cm)
CHEST_SIZES = {
    "XS": 86, "S": 92, "M": 98, "L": 104, "XL": 110, "XXL": 116, "XXXL": 122,
}

# Useful when rounding cast-on to ribbing multiples
RIB_MULTIPLES = {
    "1x1": 2,
    "2x2": 4,
    "none": 1,
}

# Target proportions for (front, back, sleeve_each, sleeve_each), as relative
# weights (not percentages). Default (2, 2, 1, 1) => front 33.3%, back 33.3%,
# each sleeve 16.7% (sleeves 33.3% combined) of total stitches. Used both for
# the initial neck-cast-on split and for the yoke's sleeve growth target, so
# there is a single source of truth for sleeve proportion.
FRONT_BACK_SLEEVE_RATIO = (2, 2, 1, 1)

# Body hem shaping by fit: hem circumference ease over bust (as a fraction of
# body stitches at separation) and the (min, max) increase-round count that
# ease is spread across. "straight" keeps the current no-shaping tube.
BODY_FIT_EASE = {
    "straight": 0.00,
    "fitted": 0.04,
    "loose": 0.12,
}
BODY_FIT_INC_ROUNDS = {
    "straight": (0, 0),
    "fitted": (1, 2),
    "loose": (7, 9),
}

# Physical depth (in cm) of the "combined" yoke phase - body and sleeves
# increasing together, after short rows end and before sleeves are held.
# This is NOT total yoke depth (neckband + short rows + combined + body-only
# all add up separately) - it is converted to a round count via each
# pattern's own row gauge (cm_to_rows), so it scales correctly across gauges
# rather than being a flat round count. Calibrated from a real top-down
# raglan reference pattern (PetiteKnit's Louvre Sweater): its combined phase
# is 22 rounds at 28 rows/10cm, every other round = 44 rows = 15.7cm, and
# that figure is close to constant across all its sizes (same gauge, same
# depth target). Body-only rounds afterward are uncapped and absorb all the
# size-to-size scaling, same as that reference pattern (7-19 rounds by size).
COMBINED_PHASE_DEPTH_CM = 15.7


