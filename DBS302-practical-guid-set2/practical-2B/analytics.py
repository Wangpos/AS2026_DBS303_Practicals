import redis
from typing import Optional


class RealtimeAnalytics:
    """
    Real-time analytics using Redis bitmaps and HyperLogLog.
    Tracks:
      - Daily Active Users (DAU) via bitmaps.
      - Daily Unique Visitors (UV) via HyperLogLog.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        self.r = redis_client or redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )

    # --------------------
    # Bitmap-based metrics
    # --------------------
    def _dau_key(self, date_str: str) -> str:
        """
        Build key for daily active user bitmap.
        Example date_str: '2026-03-17'.
        """
        return f"analytics:dau:{date_str}"

    def mark_user_active(self, date_str: str, user_id: int) -> None:
        """
        Mark a user as active for a given day using SETBIT.
        """
        if user_id < 0:
            raise ValueError("user_id must be non-negative")

        key = self._dau_key(date_str)
        # Set bit at position = user_id
        self.r.setbit(key, user_id, 1)

    def is_user_active(self, date_str: str, user_id: int) -> bool:
        """
        Check whether the user was active on a given day using GETBIT.
        """
        key = self._dau_key(date_str)
        bit_value = self.r.getbit(key, user_id)
        return bit_value == 1

    def count_daily_active_users(self, date_str: str) -> int:
        """
        Count daily active users for the given date using BITCOUNT.
        """
        key = self._dau_key(date_str)
        return self.r.bitcount(key)

    # ------------------------
    # HyperLogLog-based metrics
    # ------------------------
    def _uv_key(self, date_str: str) -> str:
        """
        Build key for daily unique visitors HyperLogLog.
        """
        return f"analytics:uv:{date_str}"

    def add_visit(self, date_str: str, user_identifier: str) -> None:
        """
        Add a visit for a given day in HyperLogLog.
        user_identifier can be a user_id, session_id, or IP string.
        """
        key = self._uv_key(date_str)
        self.r.pfadd(key, user_identifier)

    def count_unique_visitors(self, date_str: str) -> int:
        """
        Get approximate number of unique visitors for the given date using PFCOUNT.
        """
        key = self._uv_key(date_str)
        return self.r.pfcount(key)

    # --------------------------------
    # Advanced Analytics - Extensions
    # --------------------------------
    def merge_uv(self, date_str_list: list, merged_key: str) -> int:
        """
        Merge multiple daily HyperLogLogs into a single key using PFMERGE.
        Useful for computing weekly or monthly unique visitor counts.
        
        Args:
            date_str_list: List of date strings to merge (e.g., ['2026-03-17', '2026-03-18'])
            merged_key: Destination key for the merged HLL
        
        Returns:
            Approximate unique visitor count from the merged HLL
        """
        # Build UV keys for all dates
        keys_to_merge = [self._uv_key(date) for date in date_str_list]
        
        # Merge all HyperLogLogs into a single key
        self.r.pfmerge(merged_key, *keys_to_merge)
        
        # Return the approximate count
        return self.r.pfcount(merged_key)

    def calculate_monthly_active_users(self, start_date: str, num_days: int = 30) -> int:
        """
        Calculate Monthly Active Users (MAU) by merging daily bitmaps.
        Uses BITOP OR to combine multiple daily bitmaps.
        
        Args:
            start_date: Starting date in YYYY-MM-DD format
            num_days: Number of days to include (default 30 for monthly)
        
        Returns:
            Approximate number of unique users active in the period
        """
        from datetime import datetime, timedelta
        
        # Generate date list
        start = datetime.strptime(start_date, "%Y-%m-%d")
        date_list = []
        dau_keys = []
        
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            date_list.append(date_str)
            dau_keys.append(self._dau_key(date_str))
        
        # Create a merged bitmap key
        mau_key = f"analytics:mau:{start_date}:to:{(start + timedelta(days=num_days-1)).strftime('%Y-%m-%d')}"
        
        # Use BITOP OR to merge all daily bitmaps
        self.r.bitop("OR", mau_key, *dau_keys)
        
        # Count total bits set in the merged bitmap
        mau_count = self.r.bitcount(mau_key)
        
        return mau_count

    def calculate_stickiness(self, start_date: str, num_days: int = 30) -> float:
        """
        Calculate stickiness ratio = DAU / MAU
        Indicates what percentage of monthly active users are active daily on average.
        
        Args:
            start_date: Starting date in YYYY-MM-DD format
            num_days: Number of days to include (default 30 for monthly)
        
        Returns:
            Stickiness ratio as a float (0-1 scale)
        """
        from datetime import datetime, timedelta
        
        # Calculate average DAU over the period
        start = datetime.strptime(start_date, "%Y-%m-%d")
        total_dau = 0
        
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            total_dau += self.count_daily_active_users(date_str)
        
        avg_dau = total_dau / num_days if num_days > 0 else 0
        
        # Calculate MAU
        mau = self.calculate_monthly_active_users(start_date, num_days)
        
        # Calculate stickiness ratio
        stickiness = avg_dau / mau if mau > 0 else 0
        
        return stickiness


def demo():
    analytics = RealtimeAnalytics()

    date = "2026-03-17"

    # Clear previous demo data
    analytics.r.delete(analytics._dau_key(date))
    analytics.r.delete(analytics._uv_key(date))

    # Simulate some activity
    print(f"Simulating activity for {date}...")

    # Users 1, 42, 100 are active
    analytics.mark_user_active(date, 1)
    analytics.mark_user_active(date, 42)
    analytics.mark_user_active(date, 100)

    # Visits (note repeated identifiers)
    analytics.add_visit(date, "user1")
    analytics.add_visit(date, "user2")
    analytics.add_visit(date, "user3")
    analytics.add_visit(date, "user2")  # duplicate
    analytics.add_visit(date, "user3")  # duplicate
    analytics.add_visit(date, "user4")

    # Check a user's activity
    print("\nIs user 42 active?")
    print(" ->", analytics.is_user_active(date, 42))

    # Daily active users (exact, from bitmap)
    dau = analytics.count_daily_active_users(date)
    print("\nDaily Active Users (DAU):", dau)

    # Unique visitors (approximate, from HyperLogLog)
    uv = analytics.count_unique_visitors(date)
    print("Unique Visitors (UV) [approx]:", uv)


def cli_main():
    """
    CLI interface for querying analytics metrics.
    Usage:
        python analytics.py                          # Run demo
        python analytics.py --date 2026-03-17        # Query specific date
        python analytics.py --date 2026-03-17 --metric dau  # Query DAU
        python analytics.py --date 2026-03-17 --metric uv   # Query UV
        python analytics.py --date 2026-03-17 --demo        # Run demo for date
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-Time Analytics CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analytics.py                             # Run standard demo
  python analytics.py --date 2026-03-17           # Show all metrics for date
  python analytics.py --date 2026-03-17 --metric dau      # Show DAU only
  python analytics.py --date 2026-03-17 --metric uv       # Show UV only
  python analytics.py --date 2026-03-17 --demo            # Run demo simulation
        """
    )
    
    parser.add_argument("--date", type=str, help="Query date in YYYY-MM-DD format")
    parser.add_argument("--metric", type=str, choices=["dau", "uv"], help="Specific metric to query")
    parser.add_argument("--demo", action="store_true", help="Run demo simulation for given date")
    
    args = parser.parse_args()
    
    analytics = RealtimeAnalytics()
    
    if args.date and args.demo:
        # Run demo for specific date
        print(f"\n{'='*60}")
        print(f"Running demo simulation for {args.date}")
        print(f"{'='*60}\n")
        
        date = args.date
        
        # Clear previous demo data
        analytics.r.delete(analytics._dau_key(date))
        analytics.r.delete(analytics._uv_key(date))
        
        # Simulate some activity
        print(f"Simulating activity for {date}...")
        
        # Users 1, 42, 100 are active
        analytics.mark_user_active(date, 1)
        analytics.mark_user_active(date, 42)
        analytics.mark_user_active(date, 100)
        
        # Visits
        analytics.add_visit(date, "user1")
        analytics.add_visit(date, "user2")
        analytics.add_visit(date, "user3")
        analytics.add_visit(date, "user2")
        analytics.add_visit(date, "user3")
        analytics.add_visit(date, "user4")
        
        # Check a user's activity
        print(f"\nIs user 42 active on {date}?")
        print(f" -> {analytics.is_user_active(date, 42)}")
        
        # Daily active users
        dau = analytics.count_daily_active_users(date)
        print(f"\nDaily Active Users (DAU): {dau}")
        
        # Unique visitors
        uv = analytics.count_unique_visitors(date)
        print(f"Unique Visitors (UV) [approx]: {uv}")
        
    elif args.date:
        # Query specific date
        date = args.date
        
        if args.metric == "dau":
            dau = analytics.count_daily_active_users(date)
            print(f"\nDaily Active Users (DAU) for {date}: {dau}")
        elif args.metric == "uv":
            uv = analytics.count_unique_visitors(date)
            print(f"Unique Visitors (UV) [approx] for {date}: {uv}")
        else:
            # Show all metrics
            dau = analytics.count_daily_active_users(date)
            uv = analytics.count_unique_visitors(date)
            
            print(f"\n{'='*60}")
            print(f"Analytics Metrics for {date}")
            print(f"{'='*60}")
            print(f"Daily Active Users (DAU):        {dau}")
            print(f"Unique Visitors (UV) [approx]:   {uv}")
            print(f"{'='*60}\n")
    else:
        # Run standard demo
        demo()


if __name__ == "__main__":
    cli_main()
