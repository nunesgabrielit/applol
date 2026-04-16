from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path


ROLE_ORDER = ["top", "jungler", "mid", "carry", "sup"]
ROLE_LABELS = {
    "top": "Top",
    "jungler": "Jungler",
    "mid": "Mid",
    "carry": "Carry",
    "sup": "Sup",
}


class CounterService:
    """Loads the spreadsheet-derived ideal pick guide and computes recommendations."""

    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self.items = self._load_items()
        self.by_enemy = {
            self.normalize_text(item["enemy_champion"]): item
            for item in self.items
        }

    def _load_items(self) -> list[dict]:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        return [dict(item) for item in payload]

    def normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        return "".join(char for char in normalized if unicodedata.category(char) != "Mn").strip().casefold()

    def list_items(self) -> dict:
        return {
            "total": len(self.items),
            "items": self.items,
        }

    def get_analytics(self) -> dict:
        total_entries = len(self.items)
        enemy_counts = Counter(item["enemy_champion"] for item in self.items)
        adc_counts = Counter(item["ideal_adc"] for item in self.items)
        support_counts = Counter(item["ideal_support"] for item in self.items)
        duo_counts = Counter((item["ideal_adc"], item["ideal_support"]) for item in self.items)

        combined_presence: Counter[str] = Counter()
        for item in self.items:
            combined_presence[item["enemy_champion"]] += 1
            combined_presence[item["ideal_adc"]] += 1
            combined_presence[item["ideal_support"]] += 1

        def to_list_items(counter: Counter[str], denominator: int, limit: int = 8) -> list[dict]:
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
                "adc": adc,
                "support": support,
                "count": count,
                "share": round((count / total_entries) * 100, 2) if total_entries else 0.0,
            }
            for (adc, support), count in duo_counts.most_common(6)
        ]

        enemy_unique_counts = set(enemy_counts.values())

        return {
            "total_entries": total_entries,
            "unique_enemy_champions": len(enemy_counts),
            "unique_adc_recommendations": len(adc_counts),
            "unique_support_recommendations": len(support_counts),
            "strongest_duo": strongest_combinations[0] if strongest_combinations else None,
            "most_present_champions": to_list_items(combined_presence, total_entries * 3, 8),
            "top_enemy_appearance": to_list_items(enemy_counts, total_entries, 8),
            "top_adc_recommendations": to_list_items(adc_counts, total_entries, 8),
            "top_support_recommendations": to_list_items(support_counts, total_entries, 8),
            "strongest_combinations": strongest_combinations,
            "enemy_appearance_is_uniform": len(enemy_unique_counts) <= 1,
        }

    def recommend(self, enemy_team: dict[str, str | None]) -> dict:
        matched_counters: list[dict] = []
        unknown_entries: list[str] = []
        missing_roles: list[str] = []

        adc_votes: Counter[str] = Counter()
        support_votes: Counter[str] = Counter()

        for role in ROLE_ORDER:
            typed_value = (enemy_team.get(role) or "").strip()
            if not typed_value:
                missing_roles.append(ROLE_LABELS[role])
                continue

            counter = self.by_enemy.get(self.normalize_text(typed_value))
            if not counter:
                unknown_entries.append(f"{ROLE_LABELS[role]}: {typed_value}")
                continue

            adc_votes[counter["ideal_adc"]] += 1
            support_votes[counter["ideal_support"]] += 1
            matched_counters.append(
                {
                    "role": ROLE_LABELS[role],
                    "enemy_champion": counter["enemy_champion"],
                    "ideal_adc": counter["ideal_adc"],
                    "ideal_support": counter["ideal_support"],
                    "reason": counter["reason"],
                }
            )

        adc_ranking = [
            {"champion": champion, "votes": votes}
            for champion, votes in adc_votes.most_common()
        ]
        support_ranking = [
            {"champion": champion, "votes": votes}
            for champion, votes in support_votes.most_common()
        ]

        return {
            "suggested_adc": adc_ranking[0] if adc_ranking else None,
            "suggested_support": support_ranking[0] if support_ranking else None,
            "adc_ranking": adc_ranking,
            "support_ranking": support_ranking,
            "matched_counters": matched_counters,
            "missing_roles": missing_roles,
            "unknown_entries": unknown_entries,
        }
