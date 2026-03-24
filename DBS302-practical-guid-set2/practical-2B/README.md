# Practical 2B: Real-Time Analytics with Bitmaps and HyperLogLog

---

## What is the Practical About

### Overview

This practical exercise demonstrates how to implement real-time user analytics using Redis, leveraging two powerful data structures: **Bitmaps** and **HyperLogLog**. The goal is to track user activities and unique visitor counts efficiently with minimal memory footprint, which is critical for modern web applications and analytics platforms.

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

### Advanced Analytics Methods (Extensions)

#### 1. `merge_uv(date_str_list, merged_key)`

Merges multiple daily HyperLogLogs into a single key using `PFMERGE`. Perfect for computing weekly or monthly unique visitor counts.

```python
# Merge 7 days of UV data into a weekly key
dates = ["2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20",
         "2026-03-21", "2026-03-22", "2026-03-23"]
weekly_uv = analytics.merge_uv(dates, "analytics:uv:weekly:2026-03-17")
print(f"Weekly Unique Visitors: {weekly_uv}")
```

#### 2. `calculate_monthly_active_users(start_date, num_days)`

Calculates Monthly Active Users (MAU) by merging daily bitmaps using `BITOP OR` operation. Shows total unique users active in the period.

```python
# Calculate MAU for March 2026
mau = analytics.calculate_monthly_active_users("2026-03-01", num_days=31)
print(f"Monthly Active Users: {mau}")
```

#### 3. `calculate_stickiness(start_date, num_days)`

Computes the **Stickiness Ratio** = Average DAU / MAU. This metric indicates what percentage of monthly active users are engaging daily, showing user engagement level.

```python
# Calculate user engagement for March 2026
stickiness = analytics.calculate_stickiness("2026-03-01", num_days=31)
print(f"Stickiness Ratio: {stickiness:.2%}")  # Shows as percentage
```

**Interpretation:**

- Stickiness = 0.5 (50%): Half of monthly users engage daily
- Stickiness = 0.8 (80%): Highly engaged user base
- Stickiness = 0.2 (20%): Low engagement, many users are sporadic

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

- User 42 is confirmed as active
- **3 unique active users** identified (users 1, 42, 100)
- **~4 unique visitors** counted (HLL estimates unique visitors from sessions/identifiers)

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

## Extensions Implemented

All extension exercises from the practical instructions have been **successfully implemented** (COMPLETED):

### Extension 1: Weekly HyperLogLog Merge (IMPLEMENTED)

**Status:** IMPLEMENTED  
**Method:** `merge_uv(date_str_list, merged_key)`

Merges multiple daily HyperLogLogs using `PFMERGE` for weekly/monthly UV counts.

```python
# Example: Merge 7 days of data
dates = ["2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20",
         "2026-03-21", "2026-03-22", "2026-03-23"]
weekly_uv = analytics.merge_uv(dates, "analytics:uv:weekly:2026-03-17")
```

### Extension 2: Stickiness Ratio (DAU/MAU) (COMPLETED)

**Status:** IMPLEMENTED  
**Methods:** `calculate_monthly_active_users()` and `calculate_stickiness()`

Computes user engagement metrics by merging bitmaps (`BITOP OR`) to calculate MAU, then computes DAU/MAU ratio.

```python
# Calculate stickiness for a month
stickiness = analytics.calculate_stickiness("2026-03-01", num_days=31)
print(f"User Engagement: {stickiness:.2%}")  # e.g., 65.5% daily engagement

# Get MAU count
mau = analytics.calculate_monthly_active_users("2026-03-01", num_days=31)
print(f"Monthly Active Users: {mau}")
```

### Extension 3: CLI Interface (IMPLEMENTED)

**Status:** IMPLEMENTED  
**Command:** Enhanced `cli_main()` with argument parsing

Full command-line interface for querying analytics metrics:

```bash
# Run standard demo
python analytics.py

# Query all metrics for a specific date
python analytics.py --date 2026-03-17

# Query only DAU
python analytics.py --date 2026-03-17 --metric dau

# Query only UV
python analytics.py --date 2026-03-17 --metric uv

# Run demo simulation for specific date
python analytics.py --date 2026-03-17 --demo
```

---

## Common Pitfalls & Best Practices

### Avoid These Mistakes

1. **Using bitmaps for extremely sparse user IDs**
   - If your user IDs are 0-1,000,000,000 with only 100 active users, this wastes massive memory
   - Consider mapping user IDs to sequential indices or use alternative structures

2. **Expecting HyperLogLog exact counts**
   - Always remember HLL provides estimates (~1-2% error)
   - For audit-critical data, combine with other tracking methods

3. **Forgetting TTL on old data**
   - Without expiration, old analytics keys accumulate indefinitely
   - Use `EXPIRE` or `PEXPIRE` to auto-clean old data

### Best Practices

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

**Status:** SUCCESSFUL

---

### Session 2: Code Structure & Testing

#### Screenshot 2.1: Project Directory Structure

```
practical-2B/
├── instruction.txt          # Original practical instructions
├── analytics.py             # Implementation (created)
└── README.md                # This documentation
```

#### Screenshot 2.2: Core Methods Implemented

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

#### Screenshot 2.3: Extension Methods Implemented

**Advanced Analytics Methods:**

- `merge_uv()` - Merges multiple daily HLLs using `PFMERGE`
- `calculate_monthly_active_users()` - Merges daily bitmaps using `BITOP OR`
- `calculate_stickiness()` - Calculates DAU/MAU engagement ratio

**Command-Line Interface:**

- Enhanced CLI with argparse support
- Support for date-based queries
- Metric-specific filtering (DAU, UV)
- Demo simulation mode for any date

#### Screenshot 2.4: CLI Interface Testing - All Modes (VERIFIED)

**Test 1: Standard Demo Mode**

```bash
$ python analytics.py

Simulating activity for 2026-03-17...

Is user 42 active?
 -> True

Daily Active Users (DAU): 3
Unique Visitors (UV) [approx]: 4
```

**Test 2: Query All Metrics for a Date**

```bash
$ python analytics.py --date 2026-03-17

============================================================
Analytics Metrics for 2026-03-17
============================================================
Daily Active Users (DAU):        3
Unique Visitors (UV) [approx]:   4
============================================================
```

**Test 3: Query DAU Only**

```bash
$ python analytics.py --date 2026-03-17 --metric dau

Daily Active Users (DAU) for 2026-03-17: 3
```

**Test 4: Query UV Only**

```bash
$ python analytics.py --date 2026-03-17 --metric uv

Unique Visitors (UV) [approx] for 2026-03-17: 4
```

**Test 5: Run Demo Simulation for Specific Date**

```bash
$ python analytics.py --date 2026-03-17 --demo

============================================================
Running demo simulation for 2026-03-17
============================================================

Simulating activity for 2026-03-17...

Is user 42 active on 2026-03-17?
 -> True

Daily Active Users (DAU): 3
Unique Visitors (UV) [approx]: 4
```

**CLI Status:** ALL MODES WORKING PERFECTLY

---

## Verification Checklist

| Task                                         | Status    | Evidence                                        |
| -------------------------------------------- | --------- | ----------------------------------------------- |
| Understand bitmap concepts                   | COMPLETED | Implemented SETBIT, GETBIT, BITCOUNT operations |
| Understand HyperLogLog concepts              | COMPLETED | Implemented PFADD, PFCOUNT operations           |
| Create basic analytics service               | COMPLETED | RealtimeAnalytics class with 5 methods          |
| Demonstrate bitmap operations                | COMPLETED | DAU tracking working correctly                  |
| Demonstrate HyperLogLog operations           | COMPLETED | UV counting working correctly                   |
| Test with demo data                          | COMPLETED | All outputs as expected                         |
| **Implement weekly UV merge (Extension 1)**  | COMPLETED | `merge_uv()` method using PFMERGE               |
| **Implement stickiness ratio (Extension 2)** | COMPLETED | `calculate_stickiness()` computing DAU/MAU      |
| **Implement CLI interface (Extension 3)**    | COMPLETED | Enhanced CLI with date/metric queries           |
| Create comprehensive documentation           | COMPLETED | This README.md file with all details            |

---

## Technical Specifications

**Module Mapping:**

- DBS302 LO5: Assess performance implications of different NoSQL data structures
- Unit II 2.3.1: Bitmaps for analytics
- Unit II 2.3.2: HyperLogLog for analytics

**Redis Commands Used:**

- `SETBIT`, `GETBIT`, `BITCOUNT` (Bitmap operations)
- `PFADD`, `PFCOUNT`, `PFMERGE` (HyperLogLog operations)
- `BITOP` (Bitmap merging for MAU calculation)
- `DELETE` (Cleanup)

**Programming Language:** Python 3.x

**Dependencies:**

- `redis-py` (Python Redis client)
- Redis server (local: localhost:6379)

**Methods Count:** 8 total

- Core methods: 5 (mark_user_active, is_user_active, count_daily_active_users, add_visit, count_unique_visitors)
- Extension methods: 3 (merge_uv, calculate_monthly_active_users, calculate_stickiness)

---

## Summary of Implementation & Enhancements

### Core Requirements (COMPLETED)

All foundational requirements from the practical instructions have been implemented:

- Bitmap-based Daily Active User (DAU) tracking using SETBIT/GETBIT/BITCOUNT (COMPLETED)
- HyperLogLog-based Unique Visitor (UV) counting using PFADD/PFCOUNT (COMPLETED)
- Full `RealtimeAnalytics` class with core methods (COMPLETED)
- Demonstrated with working examples (COMPLETED)
- Comprehensive documentation (COMPLETED)

### Extensions (ALL 3 IMPLEMENTED)

#### Extension 1: Weekly HyperLogLog Merge (COMPLETED)

**Method:** `merge_uv(date_str_list, merged_key)`

- Uses Redis `PFMERGE` command to combine multiple daily HyperLogLogs
- Enables weekly, monthly, or custom period UV calculations
- Maintains probabilistic accuracy across merged HLLs

```python
# Example: Calculate weekly unique visitors
weekly_uv = analytics.merge_uv(["2026-03-17", "2026-03-18", ...],
                                "analytics:uv:weekly:2026-03-17")
```

#### Extension 2: Stickiness Ratio & MAU Calculation (COMPLETED)

**Methods:**

- `calculate_monthly_active_users(start_date, num_days)`
- `calculate_stickiness(start_date, num_days)`

**Features:**

- Uses Redis `BITOP OR` to merge multiple daily bitmaps
- Calculates MAU by combining all daily active user records
- Computes stickiness ratio = Average DAU / MAU
- Shows user engagement percentage

```python
# Example: Calculate monthly engagement
mau = analytics.calculate_monthly_active_users("2026-03-01", 31)
stickiness = analytics.calculate_stickiness("2026-03-01", 31)
print(f"Engagement: {stickiness:.2%}")  # e.g., "Engagement: 65.5%"
```

#### Extension 3: CLI Interface (COMPLETED)

**Enhanced:** Command-line argument parsing with `argparse`

**Supported Commands:**

```bash
# Standard demo
python analytics.py

# Query all metrics for a date
python analytics.py --date 2026-03-17

# Query specific metrics
python analytics.py --date 2026-03-17 --metric dau
python analytics.py --date 2026-03-17 --metric uv

# Run demo for a specific date
python analytics.py --date 2026-03-17 --demo

# Help
python analytics.py --help
```

---

## Implementation Statistics

| Aspect                  | Details                                                      |
| ----------------------- | ------------------------------------------------------------ |
| **Total Methods**       | 8 (5 core + 3 extensions)                                    |
| **Redis Commands Used** | 7 (SETBIT, GETBIT, BITCOUNT, PFADD, PFCOUNT, PFMERGE, BITOP) |
| **Code Quality**        | Full docstrings, type hints, error handling                  |
| **CLI Support**         | Full argparse integration with help text                     |
| **Documentation**       | Comprehensive README with examples                           |
| **Testing**             | All methods tested and verified                              |

---

## Conclusion

This practical exercise successfully demonstrates how modern analytics systems leverage specialized Redis data structures to efficiently track user metrics at scale.

**Core Implementation:** Bitmaps provide exact user activity tracking with constant-time operations, while HyperLogLog enables approximate unique counting with minimal memory overhead.

**Extensions:** The implementation goes beyond basic requirements by providing:

1. **Advanced aggregation capabilities** via HLL merging for arbitrary time periods
2. **Engagement metrics** through stickiness ratio calculation using bitmap operations
3. **Production-ready CLI interface** for querying and analyzing metrics

Together, these structures form the backbone of real-time analytics dashboards used by major technology platforms worldwide, enabling efficient tracking of DAU, MAU, and visitor metrics at scale.

---

## Final Status

| Aspect                         | Status    |
| ------------------------------ | --------- |
| Core Requirements              | COMPLETED |
| Extension 1 (Weekly UV Merge)  | COMPLETED |
| Extension 2 (Stickiness Ratio) | COMPLETED |
| Extension 3 (CLI Interface)    | COMPLETED |
| Documentation                  | COMPLETED |
| Testing & Verification         | COMPLETED |

**Overall Status:** FULLY COMPLETED (Core + All Extensions)

**Completion Date:** March 24, 2026  
**Last Updated:** March 24, 2026
