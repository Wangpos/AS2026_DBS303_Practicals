import redis
from typing import List, Dict, Optional


class GeoSearchService:
    """
    Geo-search functionality using Redis geospatial indexes.
    Stores locations (e.g., stores, drivers, users) and supports nearby queries.
    """

    def __init__(self, key: str, redis_client: Optional[redis.Redis] = None) -> None:
        self.key = key  # e.g., "geo:stores:thimphu"
        self.r = redis_client or redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )

    def add_location(self, name: str, longitude: float, latitude: float) -> None:
        """
        Add or update a named location.
        """
        self.r.geoadd(self.key, (longitude, latitude, name))

    def distance_between(
        self,
        name1: str,
        name2: str,
        unit: str = "km",
    ) -> Optional[float]:
        """
        Compute distance between two locations in the given unit.
        Units: 'm', 'km', 'mi', 'ft'
        Returns None if one of the locations does not exist.
        """
        dist = self.r.geodist(self.key, name1, name2, unit)
        return float(dist) if dist is not None else None

    def nearby(
        self,
        longitude: float,
        latitude: float,
        radius: float,
        unit: str = "km",
        withdist: bool = True,
        withcoord: bool = True,
    ) -> List[Dict]:
        """
        Find locations within a given radius from a point.
        Uses GEOSEARCH with FROMLONLAT.
        """
        # GEOSEARCH returns list of names or tuples depending on flags;
        # redis-py uses 'geosearch' wrapper method.
        results = self.r.geosearch(
            self.key,
            longitude=longitude,
            latitude=latitude,
            radius=radius,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
        )

        # Results structure depends on redis-py version. For decode_responses=True,
        # each row is [name, dist, [lon, lat]] if withdist and withcoord are True.
        formatted_results: List[Dict] = []
        for item in results:
            # Defensive parsing
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                name = item[0]
                dist_value = float(item[1])
                coord = item[2]
                lon = float(coord[0])
                lat = float(coord[1])
                formatted_results.append(
                    {
                        "name": name,
                        "distance": dist_value,
                        "longitude": lon,
                        "latitude": lat,
                    }
                )
            else:
                # Fallback if we only have the name
                formatted_results.append({"name": str(item)})

        return formatted_results

    def nearby_within_box(
        self,
        longitude1: float,
        latitude1: float,
        longitude2: float,
        latitude2: float,
        unit: str = "km",
        withdist: bool = True,
        withcoord: bool = True,
    ) -> List[Dict]:
        """
        Exercise 1: Find locations within a bounding box.
        Uses GEOSEARCH with BYBOX command.
        """
        results = self.r.geosearch(
            self.key,
            longitude=longitude1,
            latitude=latitude1,
            width=longitude2 - longitude1,
            height=latitude2 - latitude1,
            unit=unit,
            withdist=withdist,
            withcoord=withcoord,
        )

        formatted_results: List[Dict] = []
        for item in results:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                name = item[0]
                dist_value = float(item[1])
                coord = item[2]
                lon = float(coord[0])
                lat = float(coord[1])
                formatted_results.append(
                    {
                        "name": name,
                        "distance": dist_value,
                        "longitude": lon,
                        "latitude": lat,
                    }
                )
            else:
                formatted_results.append({"name": str(item)})

        return formatted_results

    def nearby_sorted_limited(
        self,
        longitude: float,
        latitude: float,
        radius: float,
        unit: str = "km",
        limit: int = 5,
    ) -> List[Dict]:
        """
        Exercise 3: Find locations within radius, sorted by distance, limited to top N.
        Returns the N closest locations sorted by distance in ascending order.
        """
        nearby_results = self.nearby(
            longitude, latitude, radius, unit, withdist=True, withcoord=True
        )

        # Sort by distance and limit
        sorted_results = sorted(nearby_results, key=lambda x: x["distance"])
        return sorted_results[:limit]


class RideHailingService(GeoSearchService):
    """
    Use Case Extension: Ride-hailing service with driver location management.
    Extends GeoSearchService to track drivers and find nearby drivers for passengers.
    """

    def __init__(self, city: str, redis_client: Optional[redis.Redis] = None) -> None:
        """
        Initialize the ride-hailing service for a specific city.
        Uses key pattern: geo:drivers:{city}
        """
        super().__init__(f"geo:drivers:{city}", redis_client)
        self.city = city

    def update_driver_location(
        self, driver_id: str, longitude: float, latitude: float
    ) -> None:
        """
        Update a driver's current location.
        This method wraps add_location for clarity in the ride-hailing context.
        """
        self.add_location(driver_id, longitude, latitude)

    def find_nearby_drivers(
        self, passenger_lon: float, passenger_lat: float, radius_km: float = 2
    ) -> List[Dict]:
        """
        Find drivers within a given radius of the passenger's location.
        Default radius is 2 km as per typical ride-hailing use case.
        """
        return self.nearby(
            passenger_lon, passenger_lat, radius_km, unit="km", withdist=True
        )


def demo():
    """
    Demo function showcasing all features including exercises and use cases.
    """
    print("=" * 70)
    print("BASIC GEO-SEARCH DEMO: Food Delivery Stores in Thimphu")
    print("=" * 70)
    
    service = GeoSearchService("geo:stores:thimphu")

    # Clear old data
    service.r.delete(service.key)

    # Add some demo stores in Thimphu (coordinates are illustrative)
    service.add_location("store_norzin", 89.6390, 27.4728)
    service.add_location("store_changzamtog", 89.6530, 27.4712)
    service.add_location("store_motithang", 89.6490, 27.4770)
    service.add_location("store_ramala", 89.6450, 27.4650)
    service.add_location("store_centenary", 89.6250, 27.4810)

    # Distance example
    dist = service.distance_between("store_norzin", "store_changzamtog", unit="km")
    print(f"\nDistance Norzin -> Changzamtog: {dist:.2f} km")

    # Nearby example: user standing at Norzin
    print("\n[Basic Radius Search] Stores within 3 km of Norzin:")
    nearby_stores = service.nearby(89.6390, 27.4728, radius=3, unit="km")
    for store in nearby_stores:
        print(
            f"  • {store['name']} at ({store['latitude']:.4f}, "
            f"{store['longitude']:.4f}) – {store['distance']:.2f} km"
        )

    # Exercise 3: Sorted by distance with limit
    print("\n[Exercise 3] Top 2 closest stores to Norzin:")
    top_stores = service.nearby_sorted_limited(89.6390, 27.4728, radius=3, limit=2)
    for store in top_stores:
        print(
            f"  • {store['name']} – {store['distance']:.2f} km"
        )

    # Exercise 1: Bounding box search
    print("\n[Exercise 1] Stores within bounding box (89.62 to 89.66 longitude, 27.46 to 27.49 latitude):")
    box_stores = service.nearby_within_box(89.62, 27.46, 89.66, 27.49)
    for store in box_stores:
        print(
            f"  • {store['name']} at ({store['latitude']:.4f}, "
            f"{store['longitude']:.4f})"
        )

    print("\n" + "=" * 70)
    print("USE CASE EXTENSION: Ride-Hailing Service with Drivers")
    print("=" * 70)

    # Use Case Extension: Ride-hailing service
    ride_service = RideHailingService("thimphu")

    # Clear old driver data
    ride_service.r.delete(ride_service.key)

    # Add drivers in Thimphu
    ride_service.update_driver_location("driver_001", 89.6390, 27.4728)
    ride_service.update_driver_location("driver_002", 89.6530, 27.4712)
    ride_service.update_driver_location("driver_003", 89.6490, 27.4770)
    ride_service.update_driver_location("driver_004", 89.6200, 27.4600)

    # Passenger requests ride at a location
    passenger_lon, passenger_lat = 89.6400, 27.4730
    print(f"\nPassenger location: ({passenger_lat:.4f}, {passenger_lon:.4f})")
    print("Finding drivers within 2 km radius...")

    nearby_drivers = ride_service.find_nearby_drivers(passenger_lon, passenger_lat)
    print(f"\nAvailable drivers nearby:")
    for driver in nearby_drivers:
        print(
            f"  • {driver['name']} – {driver['distance']:.2f} km away"
        )

    print("\n" + "=" * 70)
    print("COMMON MISTAKES & BEST PRACTICES SUMMARY")
    print("=" * 70)
    print("""
1. COORDINATE ORDER: Always use (longitude, latitude), NOT (latitude, longitude)
   - Redis geospatial expects: GEOADD key longitude latitude member
   - Example: GEOADD geo:stores 89.6390 27.4728 store_name

2. GEOSPATIAL ACCURACY:
   - Redis geospatial is great for app-level proximity queries (2-5 km ranges)
   - NOT suitable for high-precision GIS analysis (surveying, mapping)
   - Suitable use cases: "nearby stores", "nearby drivers", "nearby events"

3. CONSISTENCY:
   - Always use consistent coordinate systems (WGS84 is standard)
   - Maintain consistent distance units across the application
   - Document which coordinate system is being used

QUICK REVISION POINTS:
✓ Geospatial indexes are stored as sorted sets with encoded coordinates
✓ GEOADD inserts/updates locations, GEODIST measures distance
✓ GEOSEARCH performs geo-proximity search (newer alternative to GEORADIUS)
✓ Typical use cases: ride-hailing, food delivery, friend finder, nearby events
    """)


if __name__ == "__main__":
    demo()
