import json
from pathlib import Path

from app.services.dataset_service import DatasetService


def test_dataset_analytics(tmp_path: Path) -> None:
    payload = {
        "meta": {
            "version": "16.6.1",
            "locale": "pt_BR",
            "generator": "heuristic-role-based",
        },
        "champions": [
            {
                "key": 266,
                "riot_id": "Aatrox",
                "name": "Aatrox",
                "title": "a Espada Darkin",
                "primary_role": "Fighter",
                "tags": ["Fighter"],
                "counters": ["Galio", "Shen"],
                "against": ["Annie"],
                "synergy_good": ["Thresh", "Amumu"],
                "synergy_bad": ["Tryndamere"],
            },
            {
                "key": 103,
                "riot_id": "Ahri",
                "name": "Ahri",
                "title": "a Raposa de Nove Caudas",
                "primary_role": "Mage",
                "tags": ["Mage", "Assassin"],
                "counters": ["Galio", "Nautilus"],
                "against": ["Qiyana"],
                "synergy_good": ["Thresh", "Jinx"],
                "synergy_bad": ["Annie"],
            },
        ],
    }
    data_path = tmp_path / "lol_full_dataset.json"
    data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    profiles_path = tmp_path / "champion_deck_profiles.json"
    profiles_path.write_text(
        json.dumps(
            {
                "Ahri": {
                    "profiles": [
                        {
                            "label": "Mid",
                            "counters": ["Yasuo"],
                            "against": ["Xerath"],
                            "synergy_label": "Sinergia (Mid + Jg)",
                            "synergies": [{"champion": "Vi", "reason": "Engage simples."}],
                            "warning": None,
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    service = DatasetService(data_path=data_path, profiles_path=profiles_path)
    result = service.get_analytics()

    assert result["total_entries"] == 2
    assert result["unique_enemy_champions"] == 3
    assert result["unique_adc_recommendations"] == 2
    assert result["strongest_duo"] == {
        "adc": "Aatrox",
        "support": "Thresh",
        "count": 1,
        "share": 50.0,
    }
    assert result["dataset_meta"]["version"] == "16.6.1"
    ahri = service.get_champion_entry("Ahri")
    assert ahri["primary_role"] == "Mage"
    assert ahri["profiles"][0]["label"] == "Mid"
    assert ahri["profiles"][0]["synergies"][0]["champion"] == "Vi"
