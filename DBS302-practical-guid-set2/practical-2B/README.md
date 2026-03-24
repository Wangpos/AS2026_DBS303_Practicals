# Practical 2B: Real-Time Analytics with Bitmaps and HyperLogLog

## Overview

This practical exercise demonstrates how to implement real-time user analytics using Redis, leveraging two powerful data structures: **Bitmaps** and **HyperLogLog**. These structures enable efficient tracking of user activities and unique visitor counts with minimal memory footprint.

---

## Learning Objectives

Upon completing this practical, you will be able to:

- **Understand** how Redis bitmaps and HyperLogLog work conceptually and their respective trade-offs
- **Implement** daily active user tracking using bitmap operations (SETBIT, GETBIT, BITCOUNT)
- **Implement** approximate unique visitor counting using HyperLogLog (PFADD, PFCOUNT)
- **Design** and code an analytics service with high-level methods for these metrics
- **Assess** performance implications of different NoSQL data structures (DBS302 LO5)

---

## Conceptual Foundation

### What are Bitmaps?

A **bitmap** is a string data structure where each bit represents a binary state (0 or 1). In analytics, we typically use bitmaps to track whether a user was active on a particular day.

**Key Idea:** Each bit position represents a user ID, and the bit value indicates activity.

```
Example: 2026-03-17 activity
Bit position 1   = 1 (user 1 was active)
Bit position 42  = 1 (user 42 was active)
Bit position 100 = 1 (user 100 was active)
```

**Key Commands:**

- `SETBIT key offset value` – Set a bit at a specific position
- `GETBIT key offset` – Read a bit at a specific position
- `BITCOUNT key` – Count total bits set to 1

**Advantages:**

- Constant-time lookups for individual users
- Extremely fast counting of active users
- Space-efficient for large user bases

### What is HyperLogLog?

**HyperLogLog (HLL)** is a probabilistic data structure for cardinality estimation—that is, counting unique elements. Unlike bitmaps, HLL doesn't store individual records but instead provides an approximate count.

**Key Analogy:** Think of HLL as a "smart bucket" that doesn't remember exactly who entered, but can accurately estimate how many unique people have entered.

**Key Commands:**

- `PFADD key element [element ...]` – Add elements to HLL
- `PFCOUNT key` – Get approximate cardinality (unique count)
- `PFMERGE dest_key key1 key2 ...` – Merge multiple HLL structures

**Advantages:**

- Extremely low memory usage (typically < 16KB regardless of data size)
- Negligible error rate (~1-2%)
- Perfect for tracking unique visitors, impressions, etc.

---

## Implementation Details

### Architecture

The implementation is centered around the `RealtimeAnalytics` class, which encapsulates all bitmap and HyperLogLog operations.

**Class Structure:**

```python
class RealtimeAnalytics:
    """
    Real-time analytics using Redis bitmaps and HyperLogLog.
    Handles Daily Active Users (DAU) and Daily Unique Visitors (UV).
    """
```

### Bitmap-based Methods

#### 1. `mark_user_active(date_str, user_id)`

Marks a user as active for a given day using `SETBIT`.

```python
analytics.mark_user_active("2026-03-17", 1)
analytics.mark_user_active("2026-03-17", 42)
```

#### 2. `is_user_active(date_str, user_id)`

Checks if a user was active on a specific date using `GETBIT`.

```python
is_active = analytics.is_user_active("2026-03-17", 42)  # Returns True/False
```

#### 3. `count_daily_active_users(date_str)`

Returns the exact number of active users for a date using `BITCOUNT`.

```python
dau = analytics.count_daily_active_users("2026-03-17")  # Returns integer
```

### HyperLogLog-based Methods

#### 1. `add_visit(date_str, user_identifier)`

Adds a visitor to the daily unique visitors count.

```python
analytics.add_visit("2026-03-17", "user1")
analytics.add_visit("2026-03-17", "session123")
```

#### 2. `count_unique_visitors(date_str)`

Returns the approximate count of unique visitors for a date.

```python
uv = analytics.count_unique_visitors("2026-03-17")  # Returns approximate integer
```

---

## Demonstration Results

The demo simulation demonstrates a typical day's worth of analytics:

### Simulated Scenario

For **March 17, 2026**, we track:

- **Active Users:** User IDs 1, 42, and 100
- **Visits:** Sessions/users 1, 2, 3, 4 (with some repetitions)

### Output

```
Simulating activity for 2026-03-17...

Is user 42 active?
 -> True

Daily Active Users (DAU): 3
Unique Visitors (UV) [approx]: 4
```

**Explanation:**

- ✅ User 42 is confirmed as active
- ✅ **3 unique active users** identified (users 1, 42, 100)
- ✅ **~4 unique visitors** counted (HLL estimates unique visitors from sessions/identifiers)

---

## Why These Data Structures?

| Metric                | Bitmap                | HyperLogLog               |
| --------------------- | --------------------- | ------------------------- |
| **Use Case**          | User presence per day | Unique visitor estimation |
| **Accuracy**          | Exact (100%)          | Approximate (~1-2% error) |
| **Memory**            | ~125KB per 1M users   | ~16KB regardless of size  |
| **Query Speed**       | O(N) bit operations   | O(1) average              |
| **Individual Lookup** | Yes (GETBIT)          | No                        |
| **Merge Operations**  | Yes (BITOP)           | Yes (PFMERGE)             |

---

## Key Insights from DBS302

### Performance Implications

1. **Bitmaps** are ideal when you need:
   - Exact counts of active users
   - Individual user lookups
   - Fast boolean state tracking
   - Real-time dashboards with precise data

2. **HyperLogLog** is ideal when you need:
   - Approximate unique counts
   - Minimal memory footprint
   - Scalability across billions of records
   - Trade-off between precision and resource consumption

### Real-World Applications

- **E-commerce:** Track daily active shoppers (bitmap) vs. unique browsers (HLL)
- **Streaming Platforms:** Daily active viewers (bitmap) vs. unique show viewers (HLL)
- **SaaS Dashboards:** Monthly active users (MAU) using merged HLL structures
- **Analytics Pipelines:** Real-time metrics for dashboards and reporting

---

## Extension Exercises

### Exercise 1: Weekly HyperLogLog Merge

Implement a method that merges multiple daily HyperLogLogs into a weekly UV count:

```python
def merge_weekly_uv(self, start_date_str, num_days=7):
    """Merge HyperLogLogs for multiple days to get weekly unique visitors."""
    keys = [self._uv_key(date) for date in date_range]
    self.r.pfmerge(f"analytics:uv:weekly:{start_date_str}", *keys)
```

### Exercise 2: Stickiness Ratio (DAU/MAU)

Calculate user engagement by comparing daily active users to monthly active users, indicating what percentage of monthly users are engaging daily.

### Exercise 3: CLI Interface

Create a command-line tool to query DAU and UV for any date:

```bash
python analytics.py --date 2026-03-17
```

---

## Common Pitfalls & Best Practices

### ❌ Avoid These Mistakes

1. **Using bitmaps for extremely sparse user IDs**
   - If your user IDs are 0-1,000,000,000 with only 100 active users, this wastes massive memory
   - Consider mapping user IDs to sequential indices or use alternative structures

2. **Expecting HyperLogLog exact counts**
   - Always remember HLL provides estimates (~1-2% error)
   - For audit-critical data, combine with other tracking methods

3. **Forgetting TTL on old data**
   - Without expiration, old analytics keys accumulate indefinitely
   - Use `EXPIRE` or `PEXPIRE` to auto-clean old data

### ✅ Best Practices

1. **Use consistent key naming conventions**
   - `analytics:dau:YYYY-MM-DD`
   - `analytics:uv:YYYY-MM-DD`

2. **Set appropriate TTLs**

   ```python
   self.r.setex(key, 86400 * 365, value)  # Keep for 1 year
   ```

3. **Monitor memory usage**
   - Use `INFO memory` to track Redis memory allocation

4. **Batch operations** where possible for efficiency

---

## Screenshots & Execution Evidence

### Session 1: Initial Setup & Configuration

This section documents screenshots of the implementation and testing process.

#### Screenshot 1.1: Environment Configuration

- Python virtual environment successfully configured
- Redis package dependency installed
- Ready for execution

#### Screenshot 1.2: Demo Script Execution

**Command executed:**

```bash
python analytics.py
```

**Output captured:**

```
Simulating activity for 2026-03-17...

Is user 42 active?
 -> True

Daily Active Users (DAU): 3
Unique Visitors (UV) [approx]: 4
```

**Status:** ✅ SUCCESSFUL

---

### Session 2: Code Structure & Testing

#### Screenshot 2.1: Project Directory Structure

```
practical-2B/
├── instruction.txt          # Original practical instructions
├── analytics.py             # Implementation (created)
└── README.md                # This documentation
```

#### Screenshot 2.2: Key Code Sections

**RealtimeAnalytics class initialization:**

- Establishes Redis connection
- Configure for local testing (localhost:6379)

**Bitmap Operations:**

- `SETBIT` for marking users active
- `GETBIT` for checking activity
- `BITCOUNT` for counting active users

**HyperLogLog Operations:**

- `PFADD` for adding visitors
- `PFCOUNT` for approximate counts

---

## Verification Checklist

| Task                               | Status | Evidence                                        |
| ---------------------------------- | ------ | ----------------------------------------------- |
| Understand bitmap concepts         | ✅     | Implemented SETBIT, GETBIT, BITCOUNT operations |
| Understand HyperLogLog concepts    | ✅     | Implemented PFADD, PFCOUNT operations           |
| Create analytics service           | ✅     | RealtimeAnalytics class with 5 methods          |
| Demonstrate bitmap operations      | ✅     | DAU tracking working correctly                  |
| Demonstrate HyperLogLog operations | ✅     | UV counting working correctly                   |
| Test with demo data                | ✅     | All outputs as expected                         |
| Create documentation               | ✅     | This README.md file                             |

---

## Technical Specifications

**Module Mapping:**

- DBS302 LO5: Assess performance implications of different NoSQL data structures
- Unit II 2.3.1: Bitmaps for analytics
- Unit II 2.3.2: HyperLogLog for analytics

**Redis Commands Used:**

- `SETBIT`, `GETBIT`, `BITCOUNT` (Bitmap operations)
- `PFADD`, `PFCOUNT` (HyperLogLog operations)
- `DELETE` (Cleanup)

**Programming Language:** Python 3.x

**Dependencies:**

- `redis-py` (Python Redis client)
- Redis server (local: localhost:6379)

---

## Conclusion

This practical exercise successfully demonstrates how modern analytics systems leverage specialized Redis data structures to efficiently track user metrics at scale. Bitmaps provide exact user activity tracking with constant-time operations, while HyperLogLog enables approximate unique counting with minimal memory overhead. Together, these structures form the backbone of real-time analytics dashboards used by major technology platforms worldwide.

---

**Completion Date:** March 24, 2026  
**Status:** Completed Successfully ✅
