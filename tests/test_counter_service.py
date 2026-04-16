from pathlib import Path
import json

from app.services.counter_service import CounterService


def build_service(tmp_path: Path) -> CounterService:
    payload = [
        {
            "enemy_champion": "Darius",
            "ideal_adc": "Jhin",
            "ideal_support": "Karma",
            "reason": "Kiting forte contra Darius.",
        },
        {
            "enemy_champion": "Lee Sin",
            "ideal_adc": "Corki",
            "ideal_support": "Braum",
            "reason": "Segura o engage inicial.",
        },
        {
            "enemy_champion": "Ahri",
            "ideal_adc": "Jhin",
            "ideal_support": "Nautilus",
            "reason": "Punicao a distancia.",
        },
    ]
    data_path = tmp_path / "counter_picks.json"
    data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return CounterService(data_path=data_path)


def test_recommendation_votes_and_rankings(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    result = service.recommend(
        {
            "top": "Darius",
            "jungler": "Lee Sin",
            "mid": "Ahri",
            "carry": None,
            "sup": None,
        }
    )

    assert result["suggested_adc"] == {"champion": "Jhin", "votes": 2}
    assert result["suggested_support"] == {"champion": "Karma", "votes": 1}
    assert len(result["matched_counters"]) == 3
    assert result["missing_roles"] == ["Carry", "Sup"]


def test_recommendation_unknown_entries(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    result = service.recommend(
        {
            "top": "Camille",
            "jungler": "Lee Sin",
            "mid": "",
            "carry": None,
            "sup": None,
        }
    )

    assert result["unknown_entries"] == ["Top: Camille"]
    assert result["matched_counters"][0]["enemy_champion"] == "Lee Sin"


def test_counter_analytics(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    result = service.get_analytics()

    assert result["total_entries"] == 3
    assert result["unique_enemy_champions"] == 3
    assert result["unique_adc_recommendations"] == 2
    assert result["unique_support_recommendations"] == 3
    assert result["strongest_duo"] == {
        "adc": "Jhin",
        "support": "Karma",
        "count": 1,
        "share": 33.33,
    }
    assert result["enemy_appearance_is_uniform"] is True
