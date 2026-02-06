"""
Sales target management utilities.
Stores and manages per-rep monthly sales targets in JSON config.
"""
import json
from pathlib import Path
from typing import Optional
from datetime import date


class SalesTargetManager:
    """Manage sales targets from JSON config file."""

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "sales_targets.json"
        self.config_path = config_path

    def _load(self) -> dict:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"version": "1.0", "targets": {}, "notes": {}}

    def _save(self, config: dict):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        config["updated"] = date.today().isoformat()
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_target(self, sales_person: str, year_month: str) -> Optional[float]:
        """Get target for a sales person in YYYY-MM format. Returns None if not set."""
        config = self._load()
        return config.get("targets", {}).get(year_month, {}).get(sales_person)

    def get_all_targets(self, year_month: str) -> dict[str, float]:
        """Get all targets for a month. Returns {name: amount} dict."""
        config = self._load()
        return config.get("targets", {}).get(year_month, {})

    def set_target(self, sales_person: str, year_month: str, amount: float):
        """Set target for a sales person. Creates month entry if needed."""
        config = self._load()
        if "targets" not in config:
            config["targets"] = {}
        if year_month not in config["targets"]:
            config["targets"][year_month] = {}
        config["targets"][year_month][sales_person] = amount
        self._save(config)

    def get_all_reps_with_targets(self) -> list[str]:
        """Get list of all sales rep names that have targets in any period."""
        config = self._load()
        reps = set()
        for month_targets in config.get("targets", {}).values():
            reps.update(month_targets.keys())
        return sorted(list(reps))
