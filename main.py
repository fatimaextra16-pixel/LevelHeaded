import random

from search_engine import search_session_history

# Track every simulated day so sessions can be saved at exit
session_log = []

# Shown whenever bad input or a failed file operation is caught
WARNING_PREFIX = "  [WARNING]"


def safe_input(prompt):
    """
    Wrap input() so a closed stdin (Ctrl-D) or a Ctrl-C never crashes the app.
    Returns None when the user aborts input, so callers can shut down cleanly.
    """
    try:
        return input(prompt)
    except EOFError:
        print(f"\n{WARNING_PREFIX} No input available (end of input stream).")
        return None
    except KeyboardInterrupt:
        print(f"\n{WARNING_PREFIX} Input interrupted.")
        return None


def prompt_number(prompt, minimum, maximum):
    """Ask for a number inside a range. Re-prompts on letters, blanks or junk."""
    while True:
        raw = safe_input(prompt)
        if raw is None:
            return None

        text = raw.strip()
        if not text:
            print(f"{WARNING_PREFIX} Nothing entered. Please type a number.")
            continue

        try:
            value = float(text)
        except ValueError:
            print(f"{WARNING_PREFIX} '{text}' is not a number. "
                  f"Use digits only, e.g. 3 or 3.5")
            continue

        if minimum <= value <= maximum:
            return value

        print(f"{WARNING_PREFIX} {value:g} is out of range. "
              f"Enter a value between {minimum:g} and {maximum:g}.")


def prompt_yes_no(prompt, default=False):
    """Ask a yes/no question. Anything other than y/yes/n/no is rejected."""
    while True:
        raw = safe_input(prompt)
        if raw is None:
            return default

        answer = raw.strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        if answer == "":
            return default

        print(f"{WARNING_PREFIX} '{answer}' is not a yes/no answer. "
              f"Please enter y or n.")


def prompt_choice(prompt, valid_choices):
    """Ask for a menu choice. Keeps asking until a valid option is given."""
    allowed = ", ".join(valid_choices)
    while True:
        raw = safe_input(prompt)
        if raw is None:
            return None

        choice = raw.strip()
        if not choice:
            print(f"{WARNING_PREFIX} Nothing entered. Please enter {allowed}.")
            continue

        if choice in valid_choices:
            return choice

        print(f"{WARNING_PREFIX} '{choice}' is not one of the options. "
              f"Please enter {allowed}.")


def generate_session_data():
    """Create fresh gaming session codes and save them to the data file."""
    sessions = []
    for session_number in range(1, 4):
        hours = random.choice([3, 5, 6])
        stress = random.randint(15, 70)
        motivation = random.randint(40, 90)
        sleep = random.randint(5, 9)
        session_code = f"SES-{session_number:03d}-{hours}H-ST{stress}-MT{motivation}-SL{sleep}"
        sessions.append(session_code)

    try:
        with open("session_data.txt", "w") as file:
            for session_code in sessions:
                file.write(session_code + "\n")
    except OSError as error:
        print(f"{WARNING_PREFIX} Could not write session_data.txt: {error}")
        return []

    print(f"Generated {len(sessions)} new gaming sessions in session_data.txt")
    return sessions


def save_sessions():
    """Write all logged sessions to the data file at exit."""
    if not session_log:
        generate_session_data()
        return

    try:
        with open("session_data.txt", "w") as file:
            for session_code in session_log:
                file.write(session_code + "\n")
    except OSError as error:
        print(f"{WARNING_PREFIX} Could not save sessions to session_data.txt: {error}")
        return

    print(f"Saved {len(session_log)} session(s) to session_data.txt")


def create_player():
    return {
        "skill_level": 50,       # Starting skill baseline (mid-range)
        "stress_level": 20,      # Low starting stress
        "sleep_hours": 7.5,      # Healthy default (CDC recommends 7-9h for adults)
        "personal_growth_time": 3.0, # 3 hours available daily for non-gaming growth
        "motivation": 70,        # Healthy starting motivation
        "hours_played_today": 0,
        "days_simulated": 0,
        "focus_score": 80        # Derived from sleep, stress, and motivation
    }


def calculate_sustainability_score(player):
    skill = player["skill_level"]
    stress = player["stress_level"]
    sleep = player["sleep_hours"]
    growth = player["personal_growth_time"]
    motivation = player["motivation"]

    # Each category weighted equally (25 pts each) to avoid over-indexing on one metric
    sleep_score = min(sleep / 8.0, 1.0) * 25      # 8h = ideal sleep (caps at 25)
    stress_score = max(0, (100 - stress) / 100.0) * 25  # 0 stress = 25 pts, 100 stress = 0 pts
    growth_score = min(growth / 4.0, 1.0) * 25    # 4h daily growth = max 25 pts
    motivation_score = motivation / 100.0 * 25    # 100 motivation = 25 pts

    return round(sleep_score + stress_score + growth_score + motivation_score, 1)


def apply_session_effects(player, hours_played, chose_exercise, chose_social, chose_learning):
    player["hours_played_today"] += hours_played

    # Thresholds based on research: >5h = heavy session, >3h = moderate, else = light
    if hours_played > 5:
        player["stress_level"] += 15   # Overtraining spike (exceeds healthy daily limit)
        player["motivation"] -= 5      # Diminishing returns from excessive repetition
        player["sleep_hours"] -= 1.5   # Late-night gaming cuts into recommended 7-9h
    elif hours_played > 3:
        player["stress_level"] += 8    # Moderate fatigue accumulation
        player["sleep_hours"] -= 0.5   # Minor schedule disruption
    else:
        player["stress_level"] += 3    # Light session, minimal stress impact

    # Activities reduce stress but consume personal growth time
    if chose_exercise:
        player["stress_level"] = max(0, player["stress_level"] - 10)  # Exercise lowers cortisol
        player["motivation"] += 5
        player["personal_growth_time"] -= 1.0  # 1 hour of exercise

    if chose_social:
        player["stress_level"] = max(0, player["stress_level"] - 5)   # Social connection reduces anxiety
        player["motivation"] += 3
        player["personal_growth_time"] -= 1.0  # 1 hour socializing

    if chose_learning:
        player["skill_level"] += 2
        player["motivation"] += 5
        player["personal_growth_time"] -= 1.5  # 1.5 hours learning a new skill

    # Sleep threshold: <6h impairs reaction time, focus, and emotional regulation
    if player["sleep_hours"] < 6:
        player["motivation"] -= 10
        player["stress_level"] += 5

    # Clamp values to realistic bounds
    player["stress_level"] = max(0, min(100, player["stress_level"]))
    player["motivation"] = max(0, min(100, player["motivation"]))
    player["skill_level"] = max(0, min(100, player["skill_level"]))
    player["sleep_hours"] = max(0, min(12, player["sleep_hours"]))
    player["personal_growth_time"] = max(0, min(24, player["personal_growth_time"]))


def check_burnout_risk(player):
    # Thresholds calibrated to simulate progressive warning stages
    if player["stress_level"] > 80:
        return "HIGH BURNOUT RISK: Stress levels are critically high. Take immediate action."
    elif player["stress_level"] > 60:
        return "MODERATE BURNOUT RISK: Stress is accumulating. Consider reducing gaming hours."
    elif player["motivation"] < 30:
        return "LOW MOTIVATION WARNING: You may be approaching burnout."
    elif player["personal_growth_time"] == 0:
        return "NEGLECT ALERT: No time allocated to personal growth. Life goals are at risk."
    return "Burnout risk is low. Keep maintaining balance."


def display_comparison(player, hours_played, chose_exercise, chose_social, chose_learning):
    perceived_gains = []
    hidden_costs = []

    if hours_played > 0:
        if hours_played > 5:
            # Heavy grind: inflated perceived gain (1.5x) vs diminishing real returns
            perceived_gains.append(f"+{round(hours_played * 1.5, 1)} Skill points (heavy grind)")
            hidden_costs.append(f"+15 Stress (overtraining)")
            hidden_costs.append(f"-1.5 Sleep hours")
            hidden_costs.append(f"-5 Motivation")
        elif hours_played > 3:
            perceived_gains.append(f"+{round(hours_played, 1)} Skill points")
            hidden_costs.append(f"+8 Stress")
            hidden_costs.append(f"-0.5 Sleep hours")
        else:
            # Light practice: lower skill gain but also lower hidden cost
            perceived_gains.append(f"+{round(hours_played * 0.5, 1)} Skill points (light practice)")

    if chose_exercise:
        perceived_gains.append("+5 Motivation (feeling healthy)")
        hidden_costs.append("-1.0 Personal Growth Time")

    if chose_social:
        perceived_gains.append("+3 Motivation (connected)")
        hidden_costs.append("-1.0 Personal Growth Time")

    if chose_learning:
        perceived_gains.append("+2 Skill Level (+5 Motivation)")
        hidden_costs.append("-1.5 Personal Growth Time")

    if player["sleep_hours"] < 6:
        hidden_costs.append(f"REDUCED Focus and Reaction Time (sleep: {player['sleep_hours']} hrs)")

    print("\n" + "=" * 50)
    print("PERCEIVED GAINS (What players think they get)")
    print("=" * 50)
    for gain in perceived_gains:
        print(f"  {gain}")

    print("\n" + "=" * 50)
    print("HIDDEN COSTS (What accumulates behind the scenes)")
    print("=" * 50)
    for cost in hidden_costs:
        print(f"  {cost}")

    if player["personal_growth_time"] == 0:
        print("\n  *** WARNING: Personal Growth Time has reached zero. ***")
        print("  *** Important life goals, education, and relationships are being neglected. ***")


def display_status(player):
    sustainability = calculate_sustainability_score(player)
    # Focus score blends sleep, stress, and motivation to model reaction time and clarity
    focus_score = max(0, min(100, round(
        (player["sleep_hours"] / 8.0) * 40 +
        ((100 - player["stress_level"]) / 100.0) * 30 +
        (player["motivation"] / 100.0) * 30
    )))
    player["focus_score"] = focus_score

    print("\n" + "=" * 50)
    print("PLAYER STATUS")
    print("=" * 50)
    print(f"  Skill Level:          {player['skill_level']}")
    print(f"  Stress Level:         {player['stress_level']}")
    print(f"  Sleep Hours:          {player['sleep_hours']}")
    print(f"  Personal Growth Time: {player['personal_growth_time']} hrs")
    print(f"  Motivation:           {player['motivation']}")
    print(f"  Focus Score:          {focus_score}")
    print(f"  Today's Play Time:    {player['hours_played_today']} hrs")
    print(f"  Days Simulated:       {player['days_simulated']}")
    print(f"  Sustainability Score: {sustainability}/100")
    print("=" * 50)

    if focus_score < 40:
        print("WARNING: Your focus has collapsed. Continuing to play will lead to costly in-game mistakes and tilted decisions.")


def simulate_day(player):
    print("\n" + "-" * 50)
    print("END OF DAY - Reflect on your day")
    print("-" * 50)

    hours = prompt_number("How many hours did you play today? (0-12): ", 0, 12)
    if hours is None:
        print(f"{WARNING_PREFIX} No hours provided. Skipping this day.")
        return

    print("\nDid you do any of these today? (y/n for each):")
    chose_exercise = prompt_yes_no("  Did you exercise today? (y/n): ")
    chose_social = prompt_yes_no("  Did you socialize with friends/family? (y/n): ")
    chose_learning = prompt_yes_no("  Did you learn something new (study/skill)? (y/n): ")

    apply_session_effects(player, hours, chose_exercise, chose_social, chose_learning)
    player["days_simulated"] += 1

    # Log this session to the global log
    day_number = len(session_log) + 1
    session_code = (
        f"SES-{day_number:03d}-{int(hours)}H-ST{int(player['stress_level'])}"
        f"-MT{int(player['motivation'])}-SL{int(round(player['sleep_hours']))}"
    )
    session_log.append(session_code)

    display_status(player)
    display_comparison(player, hours, chose_exercise, chose_social, chose_learning)
    print("\n" + check_burnout_risk(player))


def main():
    print("=" * 60)
    print("          LevelHeaded - Sustainable Gaming Simulator")
    print("=" * 60)
    print("\nTrack your gaming habits and discover the hidden costs")
    print("of excessive play. Build sustainable habits for long-term success.")
    print("\n")

    player = create_player()
    display_status(player)

    while True:
        print("\nOptions:")
        print("  1. Simulate a new day")
        print("  2. View current status")
        print("  3. Search session history")
        print("  4. Exit")
        choice = prompt_choice("Enter your choice (1-4): ", ["1", "2", "3", "4"])

        if choice is None:
            save_sessions()
            print("\nThanks for using LevelHeaded. Remember:")
            print("Success is not created by endless grinding.")
            print("Balance ambition, recovery, and personal growth.")
            break

        if choice == "1":
            simulate_day(player)
        elif choice == "2":
            display_status(player)
        elif choice == "3":
            query = safe_input("Enter search term (player name, team, dept, or session code): ")
            if query is None:
                continue
            query = query.strip()
            if not query:
                print(f"{WARNING_PREFIX} Search term cannot be empty.")
                continue
            try:
                search_session_history(query)
            except (OSError, ValueError, IndexError) as error:
                print(f"{WARNING_PREFIX} Search could not be completed: {error}")
        elif choice == "4":
            save_sessions()
            print("\nThanks for using LevelHeaded. Remember:")
            print("Success is not created by endless grinding.")
            print("Balance ambition, recovery, and personal growth.")
            break


if __name__ == "__main__":
    main()
