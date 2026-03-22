import redis
from datetime import date
from typing import List, Dict, Optional, Tuple

class Leaderboard:
    """
    Leaderboard backed by Redis sorted sets.
    Encapsulates all leaderboard-related operations.
    """

    DAILY_TTL_SECONDS = 7 * 24 * 60 * 60

    def __init__(self, name: str, redis_client: Optional[redis.Redis] = None) -> None:
        self.name = name
        # Keep self.key for backward compatibility with existing code.
        self.key = self.get_alltime_key()
        self.r = redis_client or redis.Redis(
            host="127.0.0.1",
            port=6379,
            db=0,
            decode_responses=True,
        )

    def get_alltime_key(self) -> str:
        return f"leaderboard:{self.name}:alltime"

    def get_daily_key(self, day: Optional[str] = None) -> str:
        day_value = day or date.today().isoformat()
        return f"leaderboard:{self.name}:daily:{day_value}"

    def get_country_key(self, country_code: str) -> str:
        return f"leaderboard:{self.name}:country:{country_code.upper()}"

    def _resolve_key(
        self,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> str:
        if country_code:
            return self.get_country_key(country_code)
        if board == "daily":
            return self.get_daily_key(day)
        if board == "alltime":
            return self.get_alltime_key()
        raise ValueError("board must be 'alltime' or 'daily'")

    def _set_daily_ttl_if_needed(self, key: str) -> None:
        ttl = self.r.ttl(key)
        # TTL -1 means no expire set yet.
        if ttl == -1:
            self.r.expire(key, self.DAILY_TTL_SECONDS)

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
        Increment a player's score.
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
        Get top N players.
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

    def get_players_in_score_range(
        self,
        min_score: float,
        max_score: float,
        board: str = "alltime",
        day: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get players whose scores are within [min_score, max_score], descending by score.
        Uses ZREVRANGEBYSCORE.
        """
        key = self._resolve_key(board=board, day=day, country_code=country_code)
        results = self.r.zrevrangebyscore(key, max_score, min_score, withscores=True)
        return [{"player": player, "score": score} for player, score in results]

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

    # Convenience methods for country-wise leaderboards (mini case study)
    def add_global_score(self, player_id: str, score: float) -> int:
        return self.add_score(player_id=player_id, score=score, board="alltime")

    def increment_global_score(self, player_id: str, delta: float) -> Tuple[float, int]:
        return self.increment_score(player_id=player_id, delta=delta, board="alltime")

    def get_global_top(self, n: int = 10) -> List[Dict]:
        return self.get_top(n=n, board="alltime")

    def get_global_rank(self, player_id: str) -> Optional[int]:
        return self.get_rank(player_id=player_id, board="alltime")

    def add_country_score(self, country_code: str, player_id: str, score: float) -> int:
        return self.add_score(player_id, score, country_code=country_code)

    def increment_country_score(self, country_code: str, player_id: str, delta: float) -> Tuple[float, int]:
        return self.increment_score(player_id, delta, country_code=country_code)

    def get_country_top(self, country_code: str, n: int = 10) -> List[Dict]:
        return self.get_top(n=n, country_code=country_code)

    def get_country_rank(self, country_code: str, player_id: str) -> Optional[int]:
        return self.get_rank(player_id=player_id, country_code=country_code)


def demo():
    """
    Demonstrate basic usage of the Leaderboard class.
    """
    lb = Leaderboard("game")

    # Clear previous data for a clean demo
    daily_key = lb.get_daily_key("2026-03-17")
    bt_key = lb.get_country_key("BT")
    lb.r.delete(lb.key, daily_key, bt_key)

    # Add players
    print("Adding initial scores...")
    lb.add_score("alice", 1500)
    lb.add_score("bob", 2300)
    lb.add_score("charlie", 1800)
    lb.add_score("diana", 2100)
    lb.add_score("eve", 1950)

    # Print top 3 (all-time)
    print("\nTop 3 players (all-time):")
    for entry in lb.get_top(3):
        print(f" #{entry['rank']} {entry['player']}: {entry['score']}")

    # Daily leaderboard with TTL
    lb.add_score("alice", 200, board="daily", day="2026-03-17")
    lb.add_score("bob", 250, board="daily", day="2026-03-17")
    ttl = lb.r.ttl(daily_key)
    print(f"\nDaily leaderboard TTL (seconds): {ttl}")

    # Country leaderboard
    lb.add_country_score("BT", "kinley", 1200)
    lb.add_country_score("BT", "pema", 1400)
    print("\nTop BT players:")
    for entry in lb.get_country_top("BT", 2):
        print(f" #{entry['rank']} {entry['player']}: {entry['score']}")

    # Show Charlie's rank and score
    print("\nCharlie's current rank and score:")
    print(" Rank:", lb.get_rank("charlie"))
    print(" Score:", lb.get_score("charlie"))

    # Increment Charlie's score
    print("\nIncrementing Charlie's score by 500...")
    new_score, new_rank = lb.increment_score("charlie", 500)
    print(f" New score: {new_score}, new rank: {new_rank}")

    # Players around Charlie
    print("\nPlayers around Charlie:")
    for entry in lb.get_around_player("charlie", radius=2):
        print(f" #{entry['rank']} {entry['player']}: {entry['score']}")

    # Score range query (exercise)
    print("\nPlayers with scores between 2000 and 3000:")
    for entry in lb.get_players_in_score_range(2000, 3000):
        print(f" {entry['player']}: {entry['score']}")

    # Page 1 of leaderboard
    print("\nPage 1 of leaderboard (page_size=3):")
    for entry in lb.get_page(page=1, page_size=3):
        print(f" #{entry['rank']} {entry['player']}: {entry['score']}")


if __name__ == "__main__":
    demo()