from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any
import unicodedata


class DatasetService:
    """Loads the generated LoL dataset and exposes analytics for the dashboard deck."""

    def __init__(self, data_path: Path, profiles_path: Path | None = None) -> None:
        self.data_path = data_path
        self.profiles_path = profiles_path
        self.payload = self._load_payload()
        self.champions = list(self.payload.get("champions", []))
        self.meta = dict(self.payload.get("meta", {}))
        self.profiles_payload = self._load_profiles_payload()
        self.by_key = {str(champion["key"]): champion for champion in self.champions}
        self.by_name = {
            self.normalize_text(champion["name"]): champion
            for champion in self.champions
        }
        for champion in self.champions:
            self.by_name[self.normalize_text(champion["riot_id"])] = champion

    def _load_payload(self) -> dict[str, Any]:
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def _load_profiles_payload(self) -> dict[str, Any]:
        if not self.profiles_path or not self.profiles_path.exists():
            return {}
        return json.loads(self.profiles_path.read_text(encoding="utf-8"))

    def normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        return "".join(char for char in normalized if unicodedata.category(char) != "Mn").strip().casefold()

    def get_champion_entry(self, champion_key: str) -> dict[str, Any] | None:
        champion = self.by_key.get(str(champion_key))
        if champion:
            return self._merge_profiles(champion)
        champion = self.by_name.get(self.normalize_text(champion_key))
        return self._merge_profiles(champion) if champion else None

    def _merge_profiles(self, champion: dict[str, Any] | None) -> dict[str, Any] | None:
        if not champion:
            return None

        merged = dict(champion)
        profile_entry = self.profiles_payload.get(champion["name"]) or self.profiles_payload.get(champion["riot_id"])
        if profile_entry:
            merged["note"] = profile_entry.get("note")
            merged["profiles"] = profile_entry.get("profiles", [])
        else:
            merged["note"] = None
            merged["profiles"] = [
                {
                    "label": merged.get("primary_role", "Flex"),
                    "counters": merged.get("counters", []),
                    "against": merged.get("against", []),
                    "synergy_label": "Sinergias",
                    "synergies": [
                        {"champion": ally, "reason": None}
                        for ally in merged.get("synergy_good", [])
                    ],
                    "warning": None,
                }
            ]
        return merged

    def get_analytics(self) -> dict[str, Any]:
        total_entries = len(self.champions)
        role_counts = Counter(champion.get("primary_role", "Unknown") for champion in self.champions)

        counter_presence = Counter()
        against_presence = Counter()
        synergy_presence = Counter()
        synergy_pairs = Counter()
        combined_presence = Counter()

        for champion in self.champions:
            name = champion["name"]

            for target in champion.get("counters", []):
                counter_presence[target] += 1
                combined_presence[target] += 1

            for target in champion.get("against", []):
                against_presence[target] += 1
                combined_presence[target] += 1

            for target in champion.get("synergy_good", []):
                synergy_presence[target] += 1
                combined_presence[target] += 1
                pair = tuple(sorted((name, target)))
                synergy_pairs[pair] += 1

            for target in champion.get("synergy_bad", []):
                combined_presence[target] += 1

        def to_list_items(counter: Counter[str], denominator: int, limit: int = 6) -> list[dict]:
            return [
                {
                    "label": label,
                    "count": count,
                    "share": round((count / denominator) * 100, 2) if denominator else 0.0,
                }
                for label, count in counter.most_common(limit)
            ]

        strongest_combinations = [
            {
                "adc": left,
                "support": right,
                "count": count,
                "share": round((count / total_entries) * 100, 2) if total_entries else 0.0,
            }
            for (left, right), count in synergy_pairs.most_common(6)
        ]

        role_distribution = [
            {
                "label": label,
                "count": count,
                "share": round((count / total_entries) * 100, 2) if total_entries else 0.0,
            }
            for label, count in role_counts.most_common()
        ]

        return {
            "total_entries": total_entries,
            "unique_enemy_champions": len(counter_presence),
            "unique_adc_recommendations": len(role_counts),
            "unique_support_recommendations": len(synergy_pairs),
            "strongest_duo": strongest_combinations[0] if strongest_combinations else None,
            "most_present_champions": to_list_items(combined_presence, max(total_entries * 4, 1), 8),
            "top_enemy_appearance": to_list_items(counter_presence, max(total_entries * 5, 1), 8),
            "top_adc_recommendations": role_distribution[:6],
            "top_support_recommendations": to_list_items(synergy_presence, max(total_entries * 3, 1), 6),
            "strongest_combinations": strongest_combinations,
            "enemy_appearance_is_uniform": len(set(counter_presence.values())) <= 1 if counter_presence else False,
            "dataset_meta": {
                "version": self.meta.get("version"),
                "locale": self.meta.get("locale"),
                "generator": self.meta.get("generator"),
            },
        }
