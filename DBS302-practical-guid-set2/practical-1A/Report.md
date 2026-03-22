# Redis Practical Report

Implementation of Leaderboard, Real-Time Analytics, and Geo-Search with Redis.

## Methodologiest

In this practical, we have practical (1A, 1B, 1C) for which we need to have a common setup for all the practicals.

Python test connectivity to Redis server:

![test_redis_connection](screenshots/test_redis_connection.png)

## Practical–1A: Leaderboard with Redis Sorted Sets

### Objectives

1. Implement a real-time leaderboard system using Redis sorted sets (ZSET).
2. Understand Redis sorted set commands: ZADD, ZREVRANGE, ZREVRANK, ZINCRBY, ZREVRANGEBYSCORE.
3. Design and encapsulate leaderboard operations in a Python class for maintainability and testability.
4. Support advanced features: pagination, "around-me" queries, daily/all-time leaderboards, and country-wise leaderboards.
5. Implement TTL expiry for temporary leaderboard data.

### Implementation Approach

The `Leaderboard` class encapsulates all Redis sorted set operations with:

- **Key naming conventions**: `leaderboard:{name}:alltime`, `leaderboard:{name}:daily:{date}`, `leaderboard:{name}:country:{code}`
- **Core methods**: add_score, increment_score, get_rank, get_score, get_top, get_page, get_around_player, remove_player
- **Exercise methods**: get_players_in_score_range (using ZREVRANGEBYSCORE)
- **TTL support**: Automatic expiry for daily leaderboards (7 days = 604,800 seconds)
- **Case study methods**: Country-specific and global leaderboard wrappers

### Execution Output Analysis

#### Phase 1: Initial Score Addition

```
Adding initial scores...
Top 3 players (all-time):
 #1 bob: 2300.0
 #2 diana: 2100.0
 #3 eve: 1950.0
```

**Observation**: ZADD successfully inserted 5 players (alice: 1500, bob: 2300, charlie: 1800, diana: 2100, eve: 1950). ZREVRANGE correctly returned the top 3 in descending score order.

#### Phase 2: Daily Leaderboard with TTL

```
Daily leaderboard TTL (seconds): 604800
Top BT players:
 #1 pema: 1400.0
 #2 kinley: 1200.0
```

**Observation**:

- Daily leaderboard key `leaderboard:game:daily:2026-03-17` was created with ZADD.
- EXPIRE command automatically set TTL to 604,800 seconds (exactly 7 days).
- Country-specific leaderboard `leaderboard:game:country:BT` was created and stored country data independently.

#### Phase 3: Rank and Score Query

```
Charlie's current rank and score:
 Rank: 4
 Score: 1800.0
```

**Observation**:

- ZREVRANK returned 0-based rank 3; the application correctly converted it to 1-based rank 4.
- ZSCORE returned 1800.0, confirming the correct score retrieval.

#### Phase 4: Score Increment and Rank Change

```
Incrementing Charlie's score by 500...
 New score: 2300.0, new rank: 1
```

**Observation**:

- ZINCRBY incremented charlie's score from 1800 to 2300.
- Rank changed from 4 to 1 (tied with bob at 2300), demonstrating automatic reordering.
- This simulates a real-time competitive scenario where score updates trigger immediate rank recalculation.

#### Phase 5: Around-Me Query

```
Players around Charlie:
 #1 charlie: 2300.0
 #2 bob: 2300.0
 #3 diana: 2100.0
```

**Observation**:

- The get_around_player(radius=2) method retrieved charlie's rank and fetched ±2 neighbors.
- Useful for "around me" leaderboard views in mobile/web games.

#### Phase 6: Score Range Query (Exercise)

```
Players with scores between 2000 and 3000:
 charlie: 2300.0
 bob: 2300.0
 diana: 2100.0
```

**Observation**:

- ZREVRANGEBYSCORE(max=3000, min=2000) returned all players in the range in descending order.
- This demonstrates filtering leaderboard entries by score tier without full table scan.

#### Phase 7: Pagination

```
Page 1 of leaderboard (page_size=3):
 #1 charlie: 2300.0
 #2 bob: 2300.0
 #3 diana: 2100.0
```

**Observation**:

- ZREVRANGE with computed offsets correctly paginated results.
- Efficient for rendering leaderboard UIs with user-defined page sizes.

### Key Findings

| Feature               | Command               | Result                                           |
| --------------------- | --------------------- | ------------------------------------------------ |
| Insert/Update players | ZADD                  | Successful, O(log N) complexity                  |
| Get top N players     | ZREVRANGE             | Returns in descending score order                |
| Get rank              | ZREVRANK              | 0-based rank; application converts to 1-based    |
| Increment score       | ZINCRBY               | Automatic reordering after increment             |
| Score range query     | ZREVRANGEBYSCORE      | Efficient filtering without full scan            |
| TTL expiry            | EXPIRE                | Daily board auto-cleans after 7 days             |
| Pagination            | ZREVRANGE with offset | Supports large leaderboards efficiently          |
| Country/Global boards | Multiple sorted sets  | Isolated per-country rankings with shared schema |

### Code Quality Observations

1. **Encapsulation**: All Redis operations are encapsulated in the Leaderboard class.
2. **Type hints**: Python type annotations improve code clarity and IDE support.
3. **Error handling**: Rank None check prevents AttributeError on non-existent players.
4. **Backward compatibility**: self.key defaults to alltime board for existing code.
5. **Convenience methods**: add_country_score, get_country_top provide intuitive APIs for case study.

### Conclusion

The Leaderboard implementation successfully demonstrates:

- ✓ Real-time ranking with automatic sorting via Redis sorted sets
- ✓ Efficient operations on large player datasets (O(log N) for updates, O(log N + M) for range queries)
- ✓ Scalable architecture supporting multiple leaderboard scopes (global, daily, country)
- ✓ Advanced features (pagination, around-me, score filtering, TTL expiry)
- ✓ Clean API design following encapsulation principles

This approach scales to production leaderboards for competitive games, quiz platforms, and ranking applications without significant modifications.

![learderboard_first_img](screenshots/python_output_leaderboared.png)

![learderboard_second_exercise_img](screenshots/python_output_leaderboard_exercise.png)

## Practical–1B: Real-Time Analytics with Bitmaps and HyperLogLog