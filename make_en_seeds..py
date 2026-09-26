import json
from pathlib import Path

SEEDS = Path("data/seeds")
POS_RU = SEEDS / "positive_signals.json"
TRANS = SEEDS / "translations.json"
OUT = SEEDS / "positive_signals_en.json"


def extract_en(entry):
    """Пытается вытащить английское название из разных форматов."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("en", "english", "translation", "name_en", "text"):
            if key in entry and entry[key]:
                return entry[key]
    return None


def main():
    pos_ru = json.loads(POS_RU.read_text(encoding="utf-8"))
    translations = json.loads(TRANS.read_text(encoding="utf-8"))

    # Если translations — список, превратим в dict по русскому названию
    if isinstance(translations, list):
        trans_map = {}
        for item in translations:
            if isinstance(item, dict):
                ru = item.get("ru") or item.get("name") or item.get("original")
                en = extract_en(item)
                if ru and en:
                    trans_map[ru] = en
        translations = trans_map

    signals = pos_ru.get("signals", [])
    en_signals = []
    missing = []

    for s in signals:
        ru_name = s.get("name")
        if not ru_name:
            continue
        en_name = None
        if isinstance(translations, dict):
            entry = translations.get(ru_name)
            en_name = extract_en(entry)
        if en_name:
            en_signals.append({"name": en_name, "original_ru": ru_name})
        else:
            missing.append(ru_name)

    out = {"signals": en_signals}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Создано {len(en_signals)} английских сигналов → {OUT}")
    if missing:
        print(f"Не найдено переводов для {len(missing)} сигналов:")
        for m in missing[:20]:
            print(f"  - {m}")
        if len(missing) > 20:
            print(f"  ... и ещё {len(missing) - 20}")


if __name__ == "__main__":
    main()