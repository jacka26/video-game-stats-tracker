
import sqlite3
import unittest

from database import (
    insert_player,
    insert_match,
    get_players,
    get_leaderboard,
    get_player_stats
)


class TestDatabase(unittest.TestCase):

    # -------------------------
    # TEST DATABASE SETUP
    # -------------------------

    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE players (
                player_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                rank TEXT DEFAULT 'Bronze'
            )
        """)

        self.cursor.execute("""
            CREATE TABLE matches (
                match_id INTEGER PRIMARY KEY,
                player_id INTEGER NOT NULL,
                kills INTEGER NOT NULL DEFAULT 0,
                deaths INTEGER NOT NULL DEFAULT 0,
                result TEXT NOT NULL,
                played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
            )
        """)

        self.connection.commit()

    def tearDown(self):
        self.connection.close()

    # -------------------------
    # HELPER METHODS
    # -------------------------

    def create_player(self, username="Jack", level=20):
        success = insert_player(
            self.connection,
            self.cursor,
            username,
            level
        )
        self.assertTrue(success)
        return self.cursor.lastrowid

    def create_match(self, player_id, kills, deaths, result):
        success = insert_match(
            self.connection,
            self.cursor,
            player_id,
            kills,
            deaths,
            result
        )
        self.assertTrue(success)

    # -------------------------
    # BASIC DATABASE TESTS
    # -------------------------

    def test_database_starts_empty(self):
        self.cursor.execute("SELECT COUNT(*) FROM players")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 0)

    def test_insert_temporary_player(self):
        self.cursor.execute("""
            INSERT INTO players (username, level)
            VALUES (?, ?)
        """, ("TemporaryPlayer", 10))

        self.connection.commit()

        self.cursor.execute("SELECT COUNT(*) FROM players")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 1)

    # -------------------------
    # PLAYER INSERTION TESTS
    # -------------------------

    def test_insert_player_success(self):
        success = insert_player(
            self.connection, self.cursor, "TestPlayer", 15
        )

        self.assertTrue(success)

        self.cursor.execute("""
            SELECT username, level, rank
            FROM players
        """)

        player = self.cursor.fetchone()
        self.assertEqual(player, ("TestPlayer", 15, "Bronze"))

    def test_insert_player_failure(self):
        success = insert_player(
            self.connection, self.cursor, None, 10
        )

        self.assertFalse(success)

        self.cursor.execute("SELECT COUNT(*) FROM players")
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_rollback_preserves_committed_player(self):
        self.create_player("Jack", 20)

        success = insert_player(
            self.connection, self.cursor, None, 10
        )

        self.assertFalse(success)

        players = get_players(self.cursor)

        self.assertEqual(len(players), 1)
        self.assertEqual(players[0][1], "Jack")
        self.assertEqual(players[0][2], 20)

    def test_player_default_rank(self):
        self.create_player("Alex", 5)

        self.cursor.execute("""
            SELECT rank FROM players WHERE username = ?
        """, ("Alex",))

        self.assertEqual(self.cursor.fetchone()[0], "Bronze")

    # -------------------------
    # MATCH INSERTION TESTS
    # -------------------------

    def test_insert_match_success(self):
        player_id = self.create_player()

        success = insert_match(
            self.connection, self.cursor,
            player_id, 20, 5, "Win"
        )

        self.assertTrue(success)

        self.cursor.execute("""
            SELECT player_id, kills, deaths, result
            FROM matches
        """)

        self.assertEqual(
            self.cursor.fetchone(),
            (player_id, 20, 5, "Win")
        )

    def test_insert_match_invalid_player(self):
        success = insert_match(
            self.connection, self.cursor,
            9999, 15, 4, "Win"
        )

        self.assertFalse(success)

        self.cursor.execute("SELECT COUNT(*) FROM matches")
        self.assertEqual(self.cursor.fetchone()[0], 0)

    def test_failed_match_preserves_committed_match(self):
        player_id = self.create_player()

        self.create_match(player_id, 20, 5, "Win")

        success = insert_match(
            self.connection, self.cursor,
            9999, 15, 4, "Loss"
        )

        self.assertFalse(success)

        self.cursor.execute("""
            SELECT player_id, kills, deaths, result
            FROM matches
        """)

        matches = self.cursor.fetchall()

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], (player_id, 20, 5, "Win"))

    def test_multiple_matches_same_player(self):
        player_id = self.create_player()

        self.create_match(player_id, 10, 3, "Win")
        self.create_match(player_id, 5, 7, "Loss")

        self.cursor.execute("""
            SELECT COUNT(*) FROM matches WHERE player_id = ?
        """, (player_id,))

        self.assertEqual(self.cursor.fetchone()[0], 2)

    def test_match_rejects_null_result(self):
        player_id = self.create_player()

        success = insert_match(
            self.connection, self.cursor,
            player_id, 10, 2, None
        )

        self.assertFalse(success)

        self.cursor.execute("SELECT COUNT(*) FROM matches")
        self.assertEqual(self.cursor.fetchone()[0], 0)

    # -------------------------
    # PLAYER RETRIEVAL TESTS
    # -------------------------

    def test_get_players_returns_correct_order(self):
        self.create_player("Jack", 20)
        self.create_player("Alex", 15)
        self.create_player("Sarah", 30)

        players = get_players(self.cursor)

        expected = [
            (1, "Jack", 20, "Bronze"),
            (2, "Alex", 15, "Bronze"),
            (3, "Sarah", 30, "Bronze")
        ]

        self.assertEqual(players, expected)

    def test_get_players_empty_database(self):
        players = get_players(self.cursor)
        self.assertEqual(players, [])

    # -------------------------
    # LEADERBOARD TESTS
    # -------------------------

    def test_leaderboard_empty_database(self):
        leaderboard = get_leaderboard(self.cursor)
        self.assertEqual(leaderboard, [])

    def test_leaderboard_includes_players_without_matches(self):
        self.create_player("Jack", 20)

        leaderboard = get_leaderboard(self.cursor)

        self.assertEqual(
            leaderboard,
            [("Jack", 0, 0, 0, 0)]
        )

    def test_leaderboard_correct_statistics(self):
        jack_id = self.create_player("Jack", 20)
        alex_id = self.create_player("Alex", 15)

        self.create_match(jack_id, 20, 5, "Win")
        self.create_match(jack_id, 10, 5, "Loss")
        self.create_match(alex_id, 12, 4, "Win")

        leaderboard = get_leaderboard(self.cursor)

        expected = [
            ("Jack", 2, 30, 10, 15.0),
            ("Alex", 1, 12, 4, 12.0)
        ]

        self.assertEqual(leaderboard, expected)

    def test_leaderboard_sorts_by_total_kills(self):
        jack_id = self.create_player("Jack", 20)
        alex_id = self.create_player("Alex", 15)

        self.create_match(jack_id, 5, 2, "Win")
        self.create_match(alex_id, 25, 8, "Loss")

        leaderboard = get_leaderboard(self.cursor)

        self.assertEqual(leaderboard[0][0], "Alex")
        self.assertEqual(leaderboard[1][0], "Jack")

    def test_leaderboard_tie_breaks_by_username(self):
        jack_id = self.create_player("Jack", 20)
        alex_id = self.create_player("Alex", 15)

        self.create_match(jack_id, 10, 2, "Win")
        self.create_match(alex_id, 10, 3, "Loss")

        leaderboard = get_leaderboard(self.cursor)

        self.assertEqual(
            [row[0] for row in leaderboard],
            ["Alex", "Jack"]
        )

    # -------------------------
    # PLAYER STATISTICS TESTS
    # -------------------------

    def test_player_stats_nonexistent_player(self):
        stats = get_player_stats(self.cursor, 9999)
        self.assertIsNone(stats)

    def test_player_stats_without_matches(self):
        player_id = self.create_player("Jack", 20)

        stats = get_player_stats(self.cursor, player_id)

        self.assertEqual(stats["username"], "Jack")
        self.assertEqual(stats["matches_played"], 0)
        self.assertEqual(stats["wins"], 0)
        self.assertEqual(stats["losses"], 0)
        self.assertEqual(stats["total_kills"], 0)
        self.assertEqual(stats["total_deaths"], 0)
        self.assertIsNone(stats["kd_ratio"])
        self.assertEqual(stats["win_rate"], 0)
        self.assertEqual(stats["history"], [])

    def test_player_stats_correct_totals(self):
        player_id = self.create_player("Jack", 20)

        self.create_match(player_id, 20, 5, "Win")
        self.create_match(player_id, 10, 5, "Loss")
        self.create_match(player_id, 15, 5, "Win")

        stats = get_player_stats(self.cursor, player_id)

        self.assertEqual(stats["matches_played"], 3)
        self.assertEqual(stats["wins"], 2)
        self.assertEqual(stats["losses"], 1)
        self.assertEqual(stats["total_kills"], 45)
        self.assertEqual(stats["total_deaths"], 15)
        self.assertEqual(stats["kd_ratio"], 3.0)
        self.assertAlmostEqual(stats["win_rate"], 66.6666667)

    def test_player_stats_zero_deaths(self):
        player_id = self.create_player()

        self.create_match(player_id, 20, 0, "Win")

        stats = get_player_stats(self.cursor, player_id)

        self.assertIsNone(stats["kd_ratio"])
        self.assertEqual(stats["win_rate"], 100.0)

    def test_player_stats_match_history(self):
        player_id = self.create_player()

        self.create_match(player_id, 10, 2, "Win")
        self.create_match(player_id, 5, 4, "Loss")

        stats = get_player_stats(self.cursor, player_id)
        history = stats["history"]

        self.assertEqual(len(history), 2)

        # Match history sorts newest match ID first
        self.assertEqual(history[0][1:4], (5, 4, "Loss"))
        self.assertEqual(history[1][1:4], (10, 2, "Win"))

    def test_player_stats_excludes_other_players(self):
        jack_id = self.create_player("Jack", 20)
        alex_id = self.create_player("Alex", 15)

        self.create_match(jack_id, 20, 5, "Win")
        self.create_match(alex_id, 50, 10, "Loss")

        stats = get_player_stats(self.cursor, jack_id)

        self.assertEqual(stats["matches_played"], 1)
        self.assertEqual(stats["total_kills"], 20)
        self.assertEqual(stats["total_deaths"], 5)


if __name__ == "__main__":
    unittest.main()
