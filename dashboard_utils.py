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