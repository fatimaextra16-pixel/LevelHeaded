import json
import os

from main import create_player


class LevelHeadedDB:
    """Persistent JSON-backed store for LevelHeaded player and session data."""

    def __init__(self, db_path="levelheaded_db.json"):
        self.db_path = db_path

    def _default_data(self):
        return {
            "player": create_player(),
            "session_log": [],
            "days_simulated": 0,
        }

    def load(self):
        """Read the JSON database; return defaults if it is missing/corrupt."""
        if not os.path.exists(self.db_path):
            data = self._default_data()
            self.save(data)
            return data
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = self._default_data()
            self.save(data)
            return data
        # Backfill any missing keys for older DB files
        defaults = self._default_data()
        for key, value in defaults.items():
            data.setdefault(key, value)
        if "focus_score" not in data["player"]:
            data["player"]["focus_score"] = 82
        if not data["player"].get("sleep_hours"):
            data["player"]["sleep_hours"] = 7.5
        return data

    def save(self, data):
        """Write the full data dict to the JSON file immediately."""
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_player(self):
        return self.load()["player"]

    def save_player(self, player):
        data = self.load()
        data["player"] = player
        self.save(data)

    def get_session_log(self):
        return self.load()["session_log"]

    def log_session(self, code):
        data = self.load()
        data["session_log"].append(code)
        self.save(data)

    def get_days_simulated(self):
        return self.load()["days_simulated"]

    def set_days_simulated(self, n):
        data = self.load()
        data["days_simulated"] = n
        self.save(data)

    def reset(self):
        data = self._default_data()
        self.save(data)
        return data