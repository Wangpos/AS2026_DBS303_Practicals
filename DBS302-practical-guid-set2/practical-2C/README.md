# Practical–2C: Geo-Search Functionality with Redis Geospatial Indexes

## Overview

This practical implements location-based search and distance queries using Redis geospatial indexes. The project demonstrates how to store and query coordinates efficiently, enabling real-world applications like food delivery services and ride-hailing platforms to find nearby locations within a specified radius.

## What is Practical-2C About?

The practical focuses on implementing geospatial indexing capabilities in Redis. Students learn to:

- Store and manage location data (longitude, latitude pairs) efficiently
- Calculate distances between two locations using the `GEODIST` command
- Search for locations within a specified radius using the `GEOSEARCH` command
- Extend the basic functionality with real-world use cases like ride-hailing services
- Understand common pitfalls in geospatial queries (e.g., latitude/longitude order)

## Methodology

### Implementation Steps:

1. **GeoSearchService Class**: A Python wrapper around Redis geospatial commands that provides high-level methods:
   - `add_location()` - Adds or updates a location using GEOADD
   - `distance_between()` - Calculates distance using GEODIST
   - `nearby()` - Finds locations within a radius using GEOSEARCH
   - `nearby_sorted_limited()` - Returns results sorted by distance with a limit
   - `nearby_within_box()` - Searches within a bounding box

2. **RideHailingService Class**: An extension that demonstrates real-world application by:
   - Managing driver locations for a specific city
   - Finding available drivers near a passenger's location
   - Tracking driver positions dynamically

3. **Demo Implementation**: The demo includes:
   - 5 food delivery stores in Thimphu with realistic coordinates
   - Distance calculations between locations
   - Multiple search queries with different parameters
   - Full ride-hailing service simulation with 4 drivers

## Results


### Distance Calculation

```
Distance Norzin -> Changzamtog: 1.39 km
```

### Basic Radius Search (3 km from Norzin)

```
[Basic Radius Search] Stores within 3 km of Norzin:
  • store_ramala at (27.4650, 89.6450) – 1.05 km
  • store_centenary at (27.4810, 89.6250) – 1.66 km
  • store_norzin at (27.4728, 89.6390) – 0.00 km
  • store_changzamtog at (27.4712, 89.6530) – 1.39 km
  • store_motithang at (27.4770, 89.6490) – 1.09 km
```

### Exercise 3: Top 2 Closest Stores (Sorted by Distance)

```
[Exercise 3] Top 2 closest stores to Norzin:
  • store_norzin – 0.00 km
  • store_ramala – 1.05 km
```

### Use Case Extension: Ride-Hailing Service

```
Passenger location: (27.4730, 89.6400)
Finding drivers within 2 km radius...

Available drivers nearby:
  • driver_001 – 0.10 km away
  • driver_003 – 0.99 km away
  • driver_002 – 1.30 km away
```

## Key Findings

1. **Efficient Proximity Queries**: Redis geospatial indexes enable fast location-based searches suitable for real-time applications.

2. **Practical Distance Calculations**: The distances calculated align with real-world expectations for the Thimphu coordinates used in the demo.

3. **Scalable Architecture**: The implementation easily scales from food delivery to ride-hailing applications by extending the base service class.

4. **Critical Best Practices**:
   - Always use (longitude, latitude) order, NOT (latitude, longitude)
   - Redis geospatial is ideal for app-level proximity but not for high-precision GIS analysis
   - Maintain consistent coordinate systems and units across the application

## Conclusion

This practical successfully demonstrated how Redis geospatial indexes provide an efficient solution for location-based queries in real-world applications. The implementation shows that with minimal code, we can build a robust service capable of handling:

- Distance calculations between locations
- Radius-based proximity searches
- Bounding box searches
- Sorting results by distance with limits
- Real-time driver/resource location tracking

The extension to a ride-hailing service proves the flexibility of the approach. Redis geospatial commands—GEOADD, GEODIST, and GEOSEARCH—form a solid foundation for any application requiring location intelligence, making it a practical choice for modern mobile and web applications.
