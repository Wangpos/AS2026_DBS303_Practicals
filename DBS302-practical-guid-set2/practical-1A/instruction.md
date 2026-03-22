Here's a breakdown of everything you need to do in Practical 1A:

**Setup (before starting 1A)**

You need to have Redis server running, Python 3.10+ installed, and the `redis` package installed via pip. Test your connection using the `test_redis_connection.py` script provided in the common setup.

**Core Tasks in Practical 1A**

The main goal is to build a leaderboard using Redis Sorted Sets. Here's what you need to do, in order:

1. **CLI Demo first** — Open `redis-cli` and manually run the ZADD, ZREVRANGE, ZREVRANK, ZSCORE, and ZINCRBY commands to add players (alice, bob, charlie, diana, eve) and observe how rankings change when scores are updated.

2. **Create `leaderboard.py`** — Copy and implement the `Leaderboard` class with these methods: `add_score`, `increment_score`, `get_rank`, `get_score`, `get_top`, `get_page`, `get_around_player`, `count_players`, and `remove_player`.

3. **Run the demo function** — Execute the script and verify your output matches the sample output shown (top 3 players, Charlie's rank before and after increment, "around me" view, and paginated results).

**Exercises (you're expected to complete these too)**

There are three exercises after the main practical:

- Add support for **daily and all-time leaderboards** using date-based key naming like `leaderboard:game:daily:2026-03-17`.
- Add a new method `get_players_in_score_range(min_score, max_score)` using the `ZREVRANGEBYSCORE` command.
- Set a **TTL of 7 days** on the daily leaderboard key so it auto-expires.

**Mini Case Study**

Finally, you need to design a key schema and extend the `Leaderboard` class to support **country-specific leaderboards** for an online quiz app — for example, `leaderboard:quiz:country:BT` for Bhutan.

The key things to watch out for are using `ZREVRANGE` instead of `ZRANGE` (since you want descending order), remembering that `ZREVRANK` returns a 0-based rank so you need to add 1 in your code, and always following the `leaderboard:{name}` key naming convention.