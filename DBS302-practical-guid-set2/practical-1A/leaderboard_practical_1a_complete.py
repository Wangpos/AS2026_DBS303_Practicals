"""
Practical 1A: Redis Leaderboard System - COMPLETE IMPLEMENTATION
================================================================

This implementation includes:
1. Core Leaderboard Methods (Required)
2. Exercises (Daily/AllTime leaderboards + Score Range + TTL)
3. Mini Case Study (Country-specific Leaderboards)

Key Features:
- All-time leaderboard: leaderboard:{name}:alltime
- Daily leaderboard: leaderboard:{name}:daily:{date} with 7-day TTL
- Country leaderboard: leaderboard:{name}:country:{code}
"""

import redis
from datetime import date
from typing import List, Dict, Optional, Tuple


class Leaderboard:
    """
    Leaderboard backed by Redis sorted sets.
    Encapsulates all leaderboard-related operations.
    
    Supports:
    - All-time rankings
    - Daily rankings with automatic expiration
    - Country-specific rankings
    """

    DAILY_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days in seconds

    def __init__(self, name: str, redis_client: Optional[redis.Redis] = None) -> None:
        """
        Initialize the Leaderboard.
        
        Args:
            name: Name of the leaderboard (e.g., 'game', 'quiz')
            redis_client: Optional Redis client. If None, creates new connection.
        """
        self.name = name
        # Keep self.key for backward compatibility with existing code.
        self.key = self.get_alltime_key()
        self.r = redis_client or redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )

    # ==================== KEY GENERATION METHODS ====================
    
    def get_alltime_key(self) -> str:
        """Get the Redis key for all-time leaderboard."""
        return f"leaderboard:{self.name}:alltime"

    def get_daily_key(self, day: Optional[str] = None) -> str:
        """
        Get the Redis key for daily leaderboard.
        
        Args:
            day: Optional date string (YYYY-MM-DD). If None, uses today's date.
        """
        day_value = day or date.today().isoformat()
        return f"leaderboard:{self.name}:daily:{day_value}"

    def get_country_key(self, country_code: str) -> str:
        """
        Get the Redis key for country-specific leaderboard.
        
        Args:
            country_code: Country code (e.g., 'BT', 'US', 'IN')
        """
        return f"leaderboard:{self.name}:country:{country_code.upper()}"

    def _resolve_key(
        self,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> str:
        """
        Resolve the appropriate Redis key based on parameters.
        Priority: country_code > daily board > alltime board
        """
        if country_code:
            return self.get_country_key(country_code)
        if board == "daily":
            return self.get_daily_key(day)
        if board == "alltime":
            return self.get_alltime_key()
        raise ValueError("board must be 'alltime' or 'daily'")

    def _set_daily_ttl_if_needed(self, key: str) -> None:
        """
        Set TTL on daily leaderboard key if not already set.
        Exercise: Daily leaderboards auto-expire after 7 days.
        """
        ttl = self.r.ttl(key)
        # TTL -1 means no expire set yet.
        if ttl == -1:
            self.r.expire(key, self.DAILY_TTL_SECONDS)

    # ==================== CORE METHODS (REQUIRED) ====================

    def add_score(
        self,
        player_id: str,
        score: float,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> int:
        """
        Add or update a player's score.
        Returns the player's new rank (1-based).
        
        Args:
            player_id: Unique player identifier
            score: Player's score value
            board: 'alltime' or 'daily' (default: 'alltime')
            day: Date string for daily boards (default: today)
            country_code: Country code for country boards (default: None)
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        # ZADD will insert or update the member's score
        self.r.zadd(key, {player_id: score})
        if board == "daily" and not country_code:
            self._set_daily_ttl_if_needed(key)
        return self.get_rank(player_id, board=board, day=day, country_code=country_code)

    def increment_score(
        self,
        player_id: str,
        delta: float,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> Tuple[float, int]:
        """
        Increment a player's score by delta.
        Returns (new_score, new_rank).
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        new_score = self.r.zincrby(key, delta, player_id)
        if board == "daily" and not country_code:
            self._set_daily_ttl_if_needed(key)
        new_rank = self.get_rank(player_id, board=board, day=day, country_code=country_code)
        return new_score, new_rank

    def get_rank(
        self,
        player_id: str,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> Optional[int]:
        """
        Get player's rank (1-based). Returns None if player is not found.
        Note: ZREVRANK returns 0-based rank, we add 1 for 1-based display.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        rank_zero_based = self.r.zrevrank(key, player_id)
        if rank_zero_based is None:
            return None
        # Convert 0-based rank to 1-based
        return rank_zero_based + 1

    def get_score(
        self,
        player_id: str,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> Optional[float]:
        """
        Get player's current score.
        Returns None if player does not exist.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        score = self.r.zscore(key, player_id)
        return float(score) if score is not None else None

    def get_top(
        self,
        n: int = 10,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get top N players in descending order by score.
        Returns list of dicts with rank, player, and score.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        results = self.r.zrevrange(key, 0, n - 1, withscores=True)
        return [
            {"rank": i + 1, "player": player, "score": score}
            for i, (player, score) in enumerate(results)
        ]

    def get_page(
        self,
        page: int,
        page_size: int = 10,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get a specific page of the leaderboard.
        Page is 1-based.
        
        Args:
            page: Page number (1-based)
            page_size: Number of entries per page (default: 10)
        """
        if page < 1:
            raise ValueError("page must be >= 1")

        key = self._resolve_key(board=board, day=day, country_code=country_code)
        start = (page - 1) * page_size
        end = start + page_size - 1
        results = self.r.zrevrange(key, start, end, withscores=True)
        return [
            {"rank": start + i + 1, "player": player, "score": score}
            for i, (player, score) in enumerate(results)
        ]

    def get_around_player(
        self,
        player_id: str,
        radius: int = 2,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get players around a specific player (for 'around me' views).
        Includes 'radius' players above and below the given player.
        
        Args:
            player_id: Target player's ID
            radius: Number of players to show above and below (default: 2)
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        rank_zero_based = self.r.zrevrank(key, player_id)
        if rank_zero_based is None:
            return []

        start = max(0, rank_zero_based - radius)
        end = rank_zero_based + radius
        results = self.r.zrevrange(key, start, end, withscores=True)

        return [
            {"rank": start + i + 1, "player": player, "score": score}
            for i, (player, score) in enumerate(results)
        ]

    def count_players(
        self,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> int:
        """
        Get total number of players in the leaderboard.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        return self.r.zcard(key)

    def remove_player(
        self,
        player_id: str,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> bool:
        """
        Remove a player from the leaderboard.
        Returns True if the player was removed, False otherwise.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        removed = self.r.zrem(key, player_id)
        return removed > 0

    # ==================== EXERCISE METHODS ====================

    def get_players_in_score_range(
        self,
        min_score: float,
        max_score: float,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict]:
        """
        Exercise: Get players whose scores are within [min_score, max_score].
        Returns results in descending order by score.
        Uses ZREVRANGEBYSCORE command.
        
        Args:
            min_score: Minimum score threshold
            max_score: Maximum score threshold
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        results = self.r.zrevrangebyscore(key, max_score, min_score, withscores=True)
        return [{"player": player, "score": score} for player, score in results]

    # ==================== CONVENIENCE METHODS ====================

    def add_global_score(self, player_id: str, score: float) -> int:
        """Convenience method for adding to all-time leaderboard."""
        return self.add_score(player_id=player_id, score=score, board="alltime")

    def increment_global_score(self, player_id: str, delta: float) -> Tuple[float, int]:
        """Convenience method for incrementing all-time leaderboard score."""
        return self.increment_score(player_id=player_id, delta=delta, board="alltime")

    def get_global_top(self, n: int = 10) -> List[Dict]:
        """Get top N players from all-time leaderboard."""
        return self.get_top(n=n, board="alltime")

    def get_global_rank(self, player_id: str) -> Optional[int]:
        """Get player's rank in all-time leaderboard."""
        return self.get_rank(player_id=player_id, board="alltime")

    # ==================== MINI CASE STUDY: COUNTRY LEADERBOARDS ====================

    def add_country_score(self, country_code: str, player_id: str, score: float) -> int:
        """
        Mini Case Study: Add score to country-specific leaderboard.
        Example: add_country_score('BT', 'kinley', 1500)
        """
        return self.add_score(player_id, score, country_code=country_code)

    def increment_country_score(self, country_code: str, player_id: str, delta: float) -> Tuple[float, int]:
        """Mini Case Study: Increment country leaderboard score."""
        return self.increment_score(player_id, delta, country_code=country_code)

    def get_country_top(self, country_code: str, n: int = 10) -> List[Dict]:
        """Mini Case Study: Get top N players from country leaderboard."""
        return self.get_top(n=n, country_code=country_code)

    def get_country_rank(self, country_code: str, player_id: str) -> Optional[int]:
        """Mini Case Study: Get player's rank in country leaderboard."""
        return self.get_rank(player_id=player_id, country_code=country_code)

    def get_country_score(self, country_code: str, player_id: str) -> Optional[float]:
        """Mini Case Study: Get player's score in country leaderboard."""
        return self.get_score(player_id=player_id, country_code=country_code)


def demo():
    """
    Comprehensive demo showing all features:
    1. Core methods
    2. Exercises (daily leaderboards + score range)
    3. Mini case study (country leaderboards)
    """
    print("=" * 70)
    print("PRACTICAL 1A: REDIS LEADERBOARD - COMPLETE DEMO")
    print("=" * 70)
    
    lb = Leaderboard("game")

    # Clear previous data for a clean demo
    daily_key = lb.get_daily_key("2026-03-17")
    bt_key = lb.get_country_key("BT")
    lb.r.delete(lb.key, daily_key, bt_key)

    # ===================== PART 1: CORE METHODS =====================
    print("\n[1] CORE METHODS: Adding initial scores (All-Time)...")
    print("-" * 70)
    lb.add_score("alice", 1500)
    lb.add_score("bob", 2300)
    lb.add_score("charlie", 1800)
    lb.add_score("diana", 2100)
    lb.add_score("eve", 1950)
    print("✓ Added 5 players: alice, bob, charlie, diana, eve")

    # Print top 3 (all-time)
    print("\nTop 3 players (All-Time Leaderboard):")
    for entry in lb.get_top(3):
        print(f"  #{entry['rank']} {entry['player']}: {entry['score']}")

    # ===================== PART 2: EXERCISES =====================
    print("\n[2] EXERCISE 1: Daily Leaderboard with TTL (7 days)")
    print("-" * 70)
    lb.add_score("alice", 200, board="daily", day="2026-03-17")
    lb.add_score("bob", 250, board="daily", day="2026-03-17")
    ttl = lb.r.ttl(daily_key)
    print(f"✓ Added scores to daily leaderboard for 2026-03-17")
    print(f"✓ TTL set to: {ttl} seconds (~{ttl // 86400} days)")

    print("\nDaily leaderboard (2026-03-17):")
    for entry in lb.get_top(2, board="daily", day="2026-03-17"):
        print(f"  #{entry['rank']} {entry['player']}: {entry['score']}")

    print("\n[3] EXERCISE 2: Score Range Query (ZREVRANGEBYSCORE)")
    print("-" * 70)
    print("Players with scores between 2000 and 3000:")
    for entry in lb.get_players_in_score_range(2000, 3000):
        print(f"  {entry['player']}: {entry['score']}")

    # ===================== PART 3: MINI CASE STUDY =====================
    print("\n[4] MINI CASE STUDY: Country-Specific Leaderboards")
    print("-" * 70)
    lb.add_country_score("BT", "kinley", 1200)
    lb.add_country_score("BT", "pema", 1400)
    lb.add_country_score("BT", "sonam", 1100)
    print("✓ Key Schema: leaderboard:game:country:BT")
    print("✓ Added 3 players to Bhutan (BT) leaderboard")

    print("\nTop BT players (Country Leaderboard):")
    for entry in lb.get_country_top("BT", 3):
        print(f"  #{entry['rank']} {entry['player']}: {entry['score']}")

    # ===================== ADDITIONAL FEATURES =====================
    print("\n[5] ADDITIONAL FEATURES")
    print("-" * 70)

    # Show Charlie's rank and score
    print("Charlie's current rank and score (All-Time):")
    print(f"  Rank: {lb.get_rank('charlie')}")
    print(f"  Score: {lb.get_score('charlie')}")

    # Increment Charlie's score
    print("\nIncrementing Charlie's score by 500...")
    new_score, new_rank = lb.increment_score("charlie", 500)
    print(f"  New score: {new_score}, New rank: {new_rank}")

    # Players around Charlie
    print("\nPlayers around Charlie (radius=2):")
    for entry in lb.get_around_player("charlie", radius=2):
        print(f"  #{entry['rank']} {entry['player']}: {entry['score']}")

    # Pagination
    print("\nPage 1 of leaderboard (page_size=3):")
    for entry in lb.get_page(page=1, page_size=3):
        print(f"  #{entry['rank']} {entry['player']}: {entry['score']}")

    # Count players
    print(f"\nTotal players (All-Time): {lb.count_players()}")
    print(f"Total players (Country BT): {lb.count_players(country_code='BT')}")


if __name__ == "__main__":
    demo()
