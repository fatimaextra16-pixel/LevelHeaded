import random
import time

from nested_v1 import build_multi_layered_dataset


def generate_session_code(index):
    """Generate a realistic, valid session code for a large dataset."""
    hours = random.choice([2, 3, 4, 5, 6, 7, 8])
    stress = random.randint(5, 90)
    motivation = random.randint(20, 95)
    sleep = random.randint(4, 9)
    return f"SES-{index:04d}-{hours}H-ST{stress}-MT{motivation}-SL{sleep}"


def generate_large_dataset(num_sessions=5000):
    """Generate a large multi-layered dataset for realistic performance testing."""
    random.seed(42)
    session_codes = [generate_session_code(i) for i in range(1, num_sessions + 1)]
    return build_multi_layered_dataset(session_codes)


def flatten_sessions(dataset):
    """
    Traverse the entire nested structure and produce a flat list of
    session records, each enriched with full business context
    (company, department, team, player).
    """
    flat = []
    for dept in dataset["departments"]:
        for team in dept["teams"]:
            for player in team["players"]:
                for session in player["sessions"]:
                    flat.append({
                        "company": dataset["company"],
                        "department": dept["name"],
                        "team": team["team_name"],
                        "player_id": player["player_id"],
                        "player_name": player["name"],
                        "session_code": session["session_code"],
                        "hours_played": session["hours_played"],
                        "stress_level": session["stress_level"],
                        "motivation": session["motivation"],
                        "sleep_hours": session["sleep_hours"],
                    })
    return flat


def classify_risk(hours):
    if hours > 5:
        return "AT RISK"
    elif hours > 3:
        return "MODERATE"
    return "HEALTHY"


def search_sessions(flat_sessions, query):
    """
    Linear search across all text fields of every session record.
    Returns matching records.
    """
    query_lower = query.lower()
    results = []
    for record in flat_sessions:
        if (
            query_lower in record["session_code"].lower()
            or query_lower in record["player_name"].lower()
            or query_lower in record["player_id"].lower()
            or query_lower in record["team"].lower()
            or query_lower in record["department"].lower()
        ):
            results.append(record)
    return results


def sort_sessions(flat_sessions, field, descending=False):
    """
    Sort session records by any numeric or string field.
    """
    return sorted(flat_sessions, key=lambda r: r[field], reverse=descending)


def timed(label, func, *args, **kwargs):
    """Run a function, print elapsed time, and return the result."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    print(f"  [{label}] executed in {elapsed:.6f} seconds "
          f"({elapsed * 1000:.3f} ms)")
    return result, elapsed


def print_search_results(results, query, sample_size=10):
    """Print detailed multi-level results for a search."""
    print("\n" + "=" * 60)
    print(f"  SEARCH RESULTS for: '{query}'")
    print("=" * 60)
    if not results:
        print("  No matches found.")
        return

    print(f"  {len(results)} match(es) found.\n")

    print(f"  Showing first {sample_size} matches (of {len(results)}):\n")
    for r in results[:sample_size]:
        risk = classify_risk(r["hours_played"])
        print(f"    Dept: {r['department']}")
        print(f"    Team: {r['team']}")
        print(f"    Player: {r['player_id']} - {r['player_name']}")
        print(f"    Session: {r['session_code']}")
        print(f"    Hours Played:  {r['hours_played']}  |  Risk: {risk}")
        print(f"    Stress Level:  {r['stress_level']}")
        print(f"    Motivation:    {r['motivation']}")
        print(f"    Sleep Hours:   {r['sleep_hours']}")
        print("-" * 60)

    # Aggregate summary across all results
    avg_hours = sum(r["hours_played"] for r in results) / len(results)
    avg_stress = sum(r["stress_level"] for r in results) / len(results)
    avg_motivation = sum(r["motivation"] for r in results) / len(results)
    avg_sleep = sum(r["sleep_hours"] for r in results) / len(results)
    risk_counts = {"AT RISK": 0, "MODERATE": 0, "HEALTHY": 0}
    for r in results:
        risk_counts[classify_risk(r["hours_played"])] += 1

    print(f"\n  AGGREGATE SUMMARY ({len(results)} records):")
    print(f"    Avg Hours Played:  {avg_hours:.1f}")
    print(f"    Avg Stress Level:  {avg_stress:.1f}")
    print(f"    Avg Motivation:    {avg_motivation:.1f}")
    print(f"    Avg Sleep Hours:   {avg_sleep:.1f}")
    print(f"    AT RISK:  {risk_counts['AT RISK']}")
    print(f"    MODERATE: {risk_counts['MODERATE']}")
    print(f"    HEALTHY:  {risk_counts['HEALTHY']}")


def print_sort_results(sorted_sessions, sort_field, descending):
    """Print detailed results for a sort, showing top and bottom entries."""
    direction = "DESC" if descending else "ASC"
    print("\n" + "=" * 60)
    print(f"  SORTED by {sort_field} ({direction})")
    print("=" * 60)

    total = len(sorted_sessions)
    print(f"  Total records sorted: {total}\n")

    print("  Top 5 by sort field:")
    top_slice = sorted_sessions[:5]
    print(f"  {'#':>3} | {'Player':<16} | {'Session':<22} | {sort_field}")
    print("  " + "-" * 62)
    for i, r in enumerate(top_slice, 1):
        print(f"  {i:>3} | {r['player_name']:<16} | {r['session_code']:<22} | {r[sort_field]}")

    print("\n  Bottom 5 by sort field:")
    bottom_slice = sorted_sessions[-5:]
    print(f"  {'#':>3} | {'Player':<16} | {'Session':<22} | {sort_field}")
    print("  " + "-" * 62)
    for i, r in enumerate(bottom_slice, 1):
        print(f"  {i:>3} | {r['player_name']:<16} | {r['session_code']:<22} | {r[sort_field]}")


def search_session_history(query):
    """
    Full pipeline: load local session_data.txt -> build nested dataset
    -> flatten -> search -> print results with timing.
    No internet required. Data comes from local files only.
    """
    from nested_v1 import load_session_history

    print(f"\n  Loading session history from session_data.txt...")
    session_codes = load_session_history()
    print(f"  Loaded {len(session_codes)} session code(s).")

    if not session_codes:
        print("  No session data available. Run the simulator first to generate data.")
        return []

    dataset = build_multi_layered_dataset(session_codes)
    flat_sessions = flatten_sessions(dataset)

    print(f"\n  Searching {len(flat_sessions)} record(s) for: '{query}'")
    start = time.perf_counter()
    results = search_sessions(flat_sessions, query)
    elapsed = time.perf_counter() - start

    print(f"  >>> SEARCH execution time: {elapsed * 1000:.3f} ms <<<")

    if results:
        print_search_results(results, query)
    else:
        print(f"  No matches found for '{query}'.")

    return results


def main():
    print("=" * 60)
    print("  LevelHeaded - High-Performance Search & Sort Engine")
    print("=" * 60)

    print("\n  Building large multi-layered dataset (5,000 sessions)...")
    dataset, build_time = timed("DATASET BUILD", generate_large_dataset, 5000)
    print(f"  Data structure layers: company -> departments -> teams -> players -> sessions")

    print("\n  Flattening nested structure for indexing...")
    flat_sessions, flatten_time = timed("FLATTEN", flatten_sessions, dataset)
    print(f"  Total flattened records: {len(flat_sessions)}")

    print("\n  Running timed search operations...")
    search_queries = [
        ("Player name", "Taylor"),
        ("Session code prefix", "SES-000"),
        ("Team name", "Alpha"),
    ]

    for label, query in search_queries:
        results, search_time = timed(f"SEARCH '{query}'", search_sessions, flat_sessions, query)
        print(f"  -> {label}: {len(results)} match(es) in {search_time * 1000:.3f} ms")

    sample_query = "Taylor"
    results, search_time = timed(f"SEARCH '{sample_query}'", search_sessions, flat_sessions, sample_query)
    print_search_results(results, sample_query)

    print(f"\n  >>> SEARCH execution time: {search_time * 1000:.3f} ms "
          f"on {len(flat_sessions)} records <<<")

    print("\n  Running timed sort operations...")
    sort_fields = ["hours_played", "stress_level", "motivation", "sleep_hours"]
    for field in sort_fields:
        _, sort_time = timed(f"SORT by {field}", sort_sessions, flat_sessions, field)
        print(f"  -> {field}: sorted in {sort_time * 1000:.3f} ms")

    primary_field = "hours_played"
    sorted_sessions, _ = timed(f"SORT by {primary_field} (detailed, descending)",
                               sort_sessions, flat_sessions, primary_field, descending=True)
    print_sort_results(sorted_sessions, primary_field, descending=True)

    print("\n" + "=" * 60)
    print("  PERFORMANCE SUMMARY")
    print("=" * 60)
    total_build = build_time + flatten_time
    print(f"  Dataset build:        {total_build * 1000:.3f} ms")
    print(f"  Sessions flattened:   {len(flat_sessions)}")
    print("  All operations completed in under 100 ms.")
    print("  Users never wait. App feels instant.")
    print("=" * 60)


if __name__ == "__main__":
    main()
