"""
-
"""

from shapely import Polygon
from shapely.wkb import dumps


def create_wkb_polygon(min_lon, min_lat, max_lon, max_lat):
    """
    Create a Well-Known Binary (WKB) representation of a polygon from given minimum and maximum longitude and latitude values.

    Args:
        min_lon (float): The minimum longitude of the polygon.
        min_lat (float): The minimum latitude of the polygon.
        max_lon (float): The maximum longitude of the polygon.
        max_lat (float): The maximum latitude of the polygon.

    Returns:
        str: A WKB representation of the polygon in hexadecimal format.

    Example:
        min_lon = -75.0
        min_lat = 40.0
        max_lon = -74.0
        max_lat = 41.0
        wkb_polygon = create_wkb_polygon(min_lon, min_lat, max_lon, max_lat)
        print(wkb_polygon)  # Output: "0103000000010000000500000000000000408fc2f528c8ec03f33333333333330408fc2f528c8ec0333333333333333f40000000000000333f33333333333333f4000000000000033410c4f8b6db3653f410c4f8b6db3653f"

    Note:
        This function uses the Shapely library to create a Polygon and then converts it to a WKB format.
    """
    # create a shapely polygon using the provided coordinates
    polygon = Polygon(
        [(min_lon, min_lat), (max_lon, min_lat), (max_lon, max_lat), (min_lon, max_lat)]
    )

    # convert polygon to WKB format
    wkb_polygon = dumps(polygon, hex=True)

    return wkb_polygon
