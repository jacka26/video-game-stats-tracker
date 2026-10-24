import sqlite3

from database import (
    initialize_database,
    view_players,
    add_player,
    record_match,
    view_leaderboard,
    view_player_stats
)


def main():
    connection = sqlite3.connect("game_stats.db")
    connection.execute("PRAGMA foreign_keys = ON;")
    initialize_database(connection)
    cursor = connection.cursor()

    try:
        while True:
            print("\n=== VIDEO GAME STATS TRACKER ===")
            print("1. View Players")
            print("2. Add Player")
            print("3. Record Match")
            print("4. View Leaderboard")
            print("5. View Player Statistics")
            print("6. Exit")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                view_players(cursor)

            elif choice == "2":
                add_player(connection, cursor)

            elif choice == "3":
                record_match(connection, cursor)

            elif choice == "4":
                view_leaderboard(cursor)

            elif choice == "5":
                view_player_stats(cursor)

            elif choice == "6":
                print("Exiting Stats Tracker...")
                break

            else:
                print("Invalid choice. Please try again.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()