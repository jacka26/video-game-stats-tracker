import sqlite3

# PLAYER RETRIEVAL
def initialize_database(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            rank TEXT DEFAULT 'Bronze'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS matches (
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

    connection.commit()


def get_players(cursor):
    cursor.execute("""
        SELECT player_id, username, level, rank
        FROM players
        ORDER BY player_id
    """)
    return cursor.fetchall()


def view_players(cursor):
    try:
        players = get_players(cursor)
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return

    print("\n=== PLAYER LIST ===")

    if not players:
        print("No players found.")
        return

    for player in players:
        print(
            f"ID: {player[0]} | Username: {player[1]} | "
            f"Level: {player[2]} | Rank: {player[3]}"
        )


# PLAYER INSERTION
def insert_player(connection, cursor, username, level):
    try:
        cursor.execute("""
            INSERT INTO players (username, level)
            VALUES (?, ?)
        """, (username, level))

        connection.commit()
        return True

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")
        return False


def add_player(connection, cursor):
    print("\n=== ADD PLAYER ===")

    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    try:
        level = int(input("Enter starting level: "))
    except ValueError:
        print("Level must be a whole number.")
        return

    if level < 1:
        print("Level must be at least 1.")
        return

    success = insert_player(connection, cursor, username, level)

    if success:
        print(f"Player '{username}' added successfully!")
    else:
        print("Player could not be added.")


# MATCH INSERTION
def insert_match(connection, cursor, player_id, kills, deaths, result):
    try:
        cursor.execute("""
            INSERT INTO matches (player_id, kills, deaths, result)
            VALUES (?, ?, ?, ?)
        """, (player_id, kills, deaths, result))

        connection.commit()
        return True

    except sqlite3.IntegrityError as error:
        connection.rollback()
        print(f"Database constraint error: {error}")
        return False

    except sqlite3.Error as error:
        connection.rollback()
        print(f"Database error: {error}")
        return False


def record_match(connection, cursor):
    print("\n=== RECORD MATCH ===")

    try:
        player_id = int(input("Enter Player ID: "))
    except ValueError:
        print("Player ID must be a whole number.")
        return

    try:
        cursor.execute(
            "SELECT username FROM players WHERE player_id = ?",
            (player_id,)
        )
        player = cursor.fetchone()
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return

    if player is None:
        print("Player not found.")
        return

    try:
        kills = int(input("Enter kills: "))
        deaths = int(input("Enter deaths: "))
    except ValueError:
        print("Kills and deaths must be whole numbers.")
        return

    if kills < 0 or deaths < 0:
        print("Kills and deaths cannot be negative.")
        return

    result = input("Enter result (Win/Loss): ").strip().capitalize()

    if result not in ("Win", "Loss"):
        print("Result must be Win or Loss.")
        return

    success = insert_match(
        connection, cursor, player_id, kills, deaths, result
    )

    if success:
        print(f"Match recorded successfully for {player[0]}!")
    else:
        print("Match could not be recorded.")

# LEADERBOARD
def get_leaderboard(cursor):
    cursor.execute("""
        SELECT
            players.username,
            COUNT(matches.match_id) AS matches_played,
            COALESCE(SUM(matches.kills), 0) AS total_kills,
            COALESCE(SUM(matches.deaths), 0) AS total_deaths,
            COALESCE(ROUND(AVG(matches.kills), 2), 0) AS avg_kills
        FROM players
        LEFT JOIN matches
            ON players.player_id = matches.player_id
        GROUP BY players.player_id, players.username
        ORDER BY total_kills DESC, players.username ASC
    """)

    return cursor.fetchall()


def view_leaderboard(cursor):
    try:
        leaderboard = get_leaderboard(cursor)
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return

    print("\n=== PLAYER LEADERBOARD ===")
    print(
        f"{'Rank':<6}{'Player':<15}{'Matches':<10}"
        f"{'Kills':<8}{'Deaths':<8}{'Avg Kills':<10}"
    )
    print("-" * 57)

    for rank, player in enumerate(leaderboard, start=1):
        print(
            f"{rank:<6}{player[0]:<15}{player[1]:<10}"
            f"{player[2]:<8}{player[3]:<8}{player[4]:<10.2f}"
        )


# PLAYER STATISTICS
def get_player_stats(cursor, player_id):
    cursor.execute("""
        SELECT username, level, rank
        FROM players
        WHERE player_id = ?
    """, (player_id,))

    player = cursor.fetchone()

    if player is None:
        return None

    cursor.execute("""
        SELECT
            COUNT(match_id),
            SUM(CASE WHEN result = 'Win' THEN 1 ELSE 0 END),
            SUM(CASE WHEN result = 'Loss' THEN 1 ELSE 0 END),
            COALESCE(SUM(kills), 0),
            COALESCE(SUM(deaths), 0)
        FROM matches
        WHERE player_id = ?
    """, (player_id,))

    stats = cursor.fetchone()

    matches_played = stats[0]
    wins = stats[1] or 0
    losses = stats[2] or 0
    total_kills = stats[3]
    total_deaths = stats[4]

    kd_ratio = (
        total_kills / total_deaths
        if total_deaths > 0 else None
    )

    win_rate = (
        (wins / matches_played) * 100
        if matches_played > 0 else 0
    )

    cursor.execute("""
        SELECT match_id, kills, deaths, result, played_at
        FROM matches
        WHERE player_id = ?
        ORDER BY played_at DESC, match_id DESC
    """, (player_id,))

    history = cursor.fetchall()

    return {
        "username": player[0],
        "level": player[1],
        "rank": player[2],
        "matches_played": matches_played,
        "wins": wins,
        "losses": losses,
        "total_kills": total_kills,
        "total_deaths": total_deaths,
        "kd_ratio": kd_ratio,
        "win_rate": win_rate,
        "history": history
    }


def view_player_stats(cursor):
    print("\n=== PLAYER STATISTICS ===")

    try:
        player_id = int(input("Enter Player ID: "))
    except ValueError:
        print("Player ID must be a whole number.")
        return

    try:
        stats = get_player_stats(cursor, player_id)
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return

    if stats is None:
        print("Player not found.")
        return

    print(f"\nPlayer: {stats['username']}")
    print(f"Level: {stats['level']}")
    print(f"Rank: {stats['rank']}")

    print(f"\nMatches Played: {stats['matches_played']}")
    print(f"Wins: {stats['wins']}")
    print(f"Losses: {stats['losses']}")
    print(f"Total Kills: {stats['total_kills']}")
    print(f"Total Deaths: {stats['total_deaths']}")

    if stats["kd_ratio"] is None:
        print("K/D Ratio: N/A")
    else:
        print(f"K/D Ratio: {stats['kd_ratio']:.2f}")

    print(f"Win Rate: {stats['win_rate']:.2f}%")

    print("\n=== MATCH HISTORY ===")

    if not stats["history"]:
        print("No matches recorded yet.")
        return

    print(
        f"{'Match ID':<10}{'Kills':<8}{'Deaths':<8}"
        f"{'Result':<10}{'Played At':<20}"
    )
    print("-" * 56)

    for match in stats["history"]:
        print(
            f"{match[0]:<10}{match[1]:<8}{match[2]:<8}"
            f"{match[3]:<10}{match[4]:<20}"
        )