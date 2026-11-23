from dataclasses import dataclass


@dataclass
class GamingSession:
    hours_played: float
    stress_level: int
    sleep_hours: float
    personal_growth_time: float
    motivation: int
    skill_level: int
    chose_exercise: bool
    chose_social: bool
    chose_learning: bool


session = GamingSession(
    hours_played=4.5,
    stress_level=35,
    sleep_hours=7.0,
    personal_growth_time=1.5,
    motivation=65,
    skill_level=52,
    chose_exercise=True,
    chose_social=False,
    chose_learning=True,
)

print(session)

# List of gaming sessions to evaluate
gaming_sessions = [
    GamingSession(3, 20, 8, 2, 80, 45, False, False, False),
    GamingSession(5, 35, 7, 1.5, 70, 52, False, True, False),
    GamingSession(6, 60, 5.5, 0.5, 45, 58, False, False, True),
]

# Expert threshold: 5 hours of gaming per day
EXPERT_THRESHOLD = 5

# Loop through each session and evaluate the hours played
for gaming_session in gaming_sessions:
    if gaming_session.hours_played > EXPERT_THRESHOLD:
        print(f"WARNING: You played {gaming_session.hours_played} hours. Take a break!")
    else:
        print(f"{gaming_session.hours_played} hours of gaming is within the set limit.")
