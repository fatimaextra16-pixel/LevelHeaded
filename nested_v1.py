import json
from sequence_logic import parse_session_code, validate_code_format


def load_session_history():
    """Read all session codes from the data file into a flat list."""
    try:
        with open("session_data.txt", "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("  [WARNING] session_data.txt was not found. "
              "No session history to load.")
        return []
    except OSError as error:
        print(f"  [WARNING] Could not read session_data.txt: {error}")
        return []


def build_multi_layered_dataset(session_codes):
    """
    Build a multi-layered data structure:
    players -> list of days -> each day has multiple sessions -> session metrics.

    In a real business app this mirrors the hierarchy:
        company / departments / teams / players / gaming-days / sessions
    """
    dataset = {
        "company": "LevelHeaded Studios",
        "departments": [
            {
                "name": "Competitive Gaming Division",
                "teams": [
                    {
                        "team_name": "Alpha Squad",
                        "players": [
                            {
                                "player_id": "P-001",
                                "name": "Alex",
                                "sessions": [],
                            },
                            {
                                "player_id": "P-002",
                                "name": "Jordan",
                                "sessions": [],
                            },
                        ],
                    },
                    {
                        "team_name": "Beta Squad",
                        "players": [
                            {
                                "player_id": "P-003",
                                "name": "Morgan",
                                "sessions": [],
                            },
                        ],
                    },
                ],
            },
            {
                "name": "Casual Gaming Division",
                "teams": [
                    {
                        "team_name": "Gamma Squad",
                        "players": [
                            {
                                "player_id": "P-004",
                                "name": "Taylor",
                                "sessions": [],
                            },
                        ],
                    }
                ],
            },
        ],
    }

    # Distribute session codes across players round-robin style
    player_pool = []
    for dept in dataset["departments"]:
        for team in dept["teams"]:
            for player in team["players"]:
                player_pool.append(player)

    skipped = 0
    for index, code in enumerate(session_codes):
        if not validate_code_format(code):
            skipped += 1
            continue
        try:
            metrics = parse_session_code(code)
        except (ValueError, IndexError):
            # A code can have the right shape but unreadable numbers
            skipped += 1
            continue
        player = player_pool[index % len(player_pool)]
        metrics["session_code"] = code
        player["sessions"].append(metrics)

    if skipped:
        print(f"  [WARNING] Skipped {skipped} unreadable session code(s) "
              f"in session_data.txt.")

    return dataset


def scan_dataset(dataset):
    """
    Nested scan: iterate company -> departments -> teams -> players -> sessions.
    Uses a conditional inside the loop to flag at-risk sessions.
    Prints detailed, multi-level results.
    """
    total_sessions_scanned = 0
    at_risk_sessions = []

    print("=" * 60)
    print(f"  SCANNING BUSINESS DATA: {dataset['company']}")
    print("=" * 60)

    # --- Outer loop: departments ---
    for dept in dataset["departments"]:
        print(f"\n[DEPARTMENT] {dept['name']}")
        print("-" * 50)

        # --- Middle loop: teams within department ---
        for team in dept["teams"]:
            print(f"  [TEAM] {team['team_name']}")

            # --- Inner loop: players within team ---
            for player in team["players"]:
                session_count = len(player["sessions"])
                print(f"    [PLAYER] {player['player_id']} - {player['name']} "
                      f"({session_count} session(s))")

                # --- Deepest loop: sessions within player ---
                for session in player["sessions"]:
                    total_sessions_scanned += 1

                    # Conditional inside the loop: flag excessive gaming
                    if session["hours_played"] > 5:
                        risk_label = "AT RISK"
                        at_risk_sessions.append(session)
                    elif session["hours_played"] > 3:
                        risk_label = "MODERATE"
                    else:
                        risk_label = "HEALTHY"

                    print(f"      Session: {session['session_code']}")
                    print(f"        Hours Played:  {session['hours_played']}")
                    print(f"        Stress Level:  {session['stress_level']}")
                    print(f"        Motivation:    {session['motivation']}")
                    print(f"        Sleep Hours:   {session['sleep_hours']}")
                    print(f"        Risk Status:   {risk_label}")

    print("\n" + "=" * 60)
    print("SCAN COMPLETE - SUMMARY REPORT")
    print("=" * 60)
    print(f"  Total sessions scanned: {total_sessions_scanned}")
    print(f"  At-risk sessions (>5h):  {len(at_risk_sessions)}")

    if at_risk_sessions:
        print("\n  At-risk session details:")
        for s in at_risk_sessions:
            print(f"    - {s['session_code']} "
                  f"({s['hours_played']}h, Stress: {s['stress_level']})")
    else:
        print("  No at-risk sessions found.")


def export_results(dataset, filename="nested_scan_results.json"):
    """Persist the multi-layered dataset to a JSON file for audit."""
    with open(filename, "w") as file:
        json.dump(dataset, file, indent=2)
    print(f"\n  Multi-layered results exported to: {filename}")


def main():
    session_codes = load_session_history()
    dataset = build_multi_layered_dataset(session_codes)
    scan_dataset(dataset)
    export_results(dataset)


if __name__ == "__main__":
    main()
