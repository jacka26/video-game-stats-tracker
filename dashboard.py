import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from database import (
    get_players,
    get_player_stats,
    initialize_database
)


# PAGE CONFIGURATION
st.set_page_config(
    page_title="Video Game Stats Tracker",
    page_icon="🎮",
    layout="wide"
)

DB_PATH = Path(__file__).resolve().parent / "game_stats.db"


# DATABASE FUNCTIONS
def load_players():
    """Load players from the SQLite database."""
    with sqlite3.connect(DB_PATH) as connection:
        initialize_database(connection)
        cursor = connection.cursor()
        return get_players(cursor)


def load_player_stats(player_id):
    """Load statistics for one player."""
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        return get_player_stats(cursor, player_id)


def calculate_metrics(matches):
    """Calculate statistics from a list of matches."""
    total_matches = len(matches)
    total_kills = sum(match["Kills"] for match in matches)
    total_deaths = sum(match["Deaths"] for match in matches)

    wins = sum(
        match["Result"] == "Win"
        for match in matches
    )

    losses = sum(
        match["Result"] == "Loss"
        for match in matches
    )

    win_rate = (
        wins / total_matches * 100
        if total_matches > 0 else 0
    )

    kd_ratio = (
        total_kills / total_deaths
        if total_deaths > 0 else None
    )

    return {
        "matches": total_matches,
        "kills": total_kills,
        "deaths": total_deaths,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "kd_ratio": kd_ratio
    }


def filter_matches(matches, selected_results):
    """Keep matches with selected Win/Loss results."""
    return [
        match
        for match in matches
        if match["Result"] in selected_results
    ]


# LOAD PLAYERS
try:
    player_rows = load_players()
except sqlite3.Error as error:
    st.error(f"Unable to load players: {error}")
    st.stop()

players = {
    username: player_id
    for player_id, username, level, rank in player_rows
}

if not players:
    st.warning(
        "No players found. Add a player using main.py first."
    )
    st.stop()


# SIDEBAR
with st.sidebar:
    st.header("Dashboard Filters")

    selected_player = st.selectbox(
        "Select a Player",
        list(players.keys())
    )

    selected_player_id = players[selected_player]

    selected_results = st.multiselect(
        "Filter Match Results",
        ["Win", "Loss"],
        default=["Win", "Loss"]
    )

    stats_mode = st.radio(
        "Statistics Scope",
        ["Lifetime", "Filtered Matches"]
    )

    st.divider()
    st.caption("Video Game Stats Tracker")


# LOAD SELECTED PLAYER
try:
    stats = load_player_stats(selected_player_id)
except sqlite3.Error as error:
    st.error(f"Unable to load player statistics: {error}")
    st.stop()

if stats is None:
    st.warning("The selected player could not be found.")
    st.stop()


# CONVERT MATCH HISTORY
match_history = [
    {
        "Match ID": match_id,
        "Kills": kills,
        "Deaths": deaths,
        "Result": result,
        "Date Played": played_at
    }
    for match_id, kills, deaths, result, played_at
    in stats["history"]
]

filtered_matches = filter_matches(
    match_history,
    selected_results
)

# Lifetime metrics come from the database function.
lifetime_metrics = {
    "matches": stats["matches_played"],
    "kills": stats["total_kills"],
    "deaths": stats["total_deaths"],
    "wins": stats["wins"],
    "losses": stats["losses"],
    "win_rate": stats["win_rate"],
    "kd_ratio": stats["kd_ratio"]
}

# Filtered metrics are calculated from visible matches.
if stats_mode == "Filtered Matches":
    metrics = calculate_metrics(filtered_matches)
else:
    metrics = lifetime_metrics


# MAIN DASHBOARD
st.title("Video Game Stats Tracker")
st.write("Analyze player performance and match statistics.")

st.divider()

st.subheader("Selected Player")

col1, col2, col3 = st.columns(3)

with col1:
    st.write(f"**Username:** {stats['username']}")

with col2:
    st.write(f"**Level:** {stats['level']}")

with col3:
    st.write(f"**Rank:** {stats['rank']}")

st.caption(f"Player ID: {selected_player_id}")


# PLAYER OVERVIEW
st.divider()
st.subheader("Player Overview")
st.caption(f"Statistics scope: {stats_mode}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Matches", metrics["matches"])

with col2:
    st.metric("Total Kills", metrics["kills"])

with col3:
    st.metric(
        "Win Rate",
        f"{metrics['win_rate']:.1f}%"
    )

with col4:
    kd_ratio = metrics["kd_ratio"]

    kd_display = (
        f"{kd_ratio:.2f}"
        if kd_ratio is not None else "N/A"
    )

    st.metric("K/D Ratio", kd_display)


# PERFORMANCE CHARTS
st.divider()
st.subheader("Performance Charts")

if filtered_matches:
    # Reverse newest-first history to chronological order.
    chart_matches = list(reversed(filtered_matches))

    chart_df = pd.DataFrame(chart_matches)

    # Match number in chronological order.
    chart_df["Match Number"] = range(
        1, len(chart_df) + 1
    )

    st.write("### Kills and Deaths Over Time")

    st.line_chart(
        chart_df.set_index("Match Number")[
            ["Kills", "Deaths"]
        ]
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("### Win/Loss Distribution")

        result_counts = (
            chart_df["Result"]
            .value_counts()
            .reindex(["Win", "Loss"], fill_value=0)
        )

        st.bar_chart(result_counts)

    with chart_col2:
        st.write("### Kills per Match")

        st.bar_chart(
            chart_df.set_index("Match Number")["Kills"]
        )

else:
    st.info(
        "No match data available for the selected filters."
    )


# MATCH HISTORY
st.divider()
st.subheader("Match History")

if filtered_matches:
    history_df = pd.DataFrame(filtered_matches)

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing {len(filtered_matches)} "
        f"of {len(match_history)} matches."
    )

    csv_data = history_df.to_csv(index=False)

    st.download_button(
        "Download Match History (CSV)",
        data=csv_data,
        file_name="match_history.csv",
        mime="text/csv"
    )

else:
    st.info("No matches found for the selected filters.")


# FOOTER
st.divider()
st.caption(
    "Built with Python, SQLite, Pandas, and Streamlit."
)
