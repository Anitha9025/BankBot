"""
clear_nlu_intents.py — Removes duplicate intent blocks from nlu.yml and nlu_module2.yml.
These are now managed via MySQL + nlu_admin.yml, so source files should only keep regex/lookup.
"""
import yaml, shutil, os

PATHS = [
    r"e:\BankBot\data\nlu.yml",
    r"e:\BankBot\data\nlu_module2.yml",
]

for path in PATHS:
    if not os.path.exists(path):
        print(f"SKIP (not found): {path}")
        continue
    shutil.copy2(path, path + ".bak2")  # extra safety backup
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    nlu = data.get("nlu") or []
    kept    = [b for b in nlu if "intent" not in b]
    removed = len(nlu) - len(kept)

    lines = ['version: "3.1"', "", "nlu:", ""]
    for block in kept:
        if "regex" in block:
            lines.append(f"- regex: {block['regex']}")
            lines.append("  examples: |")
            for ex in (block.get("examples") or "").strip().splitlines():
                lines.append(f"    {ex.strip()}")
            lines.append("")
        elif "lookup" in block:
            lines.append(f"- lookup: {block['lookup']}")
            lines.append("  examples: |")
            for ex in (block.get("examples") or "").strip().splitlines():
                lines.append(f"    {ex.strip()}")
            lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"OK  {os.path.basename(path)}: removed {removed} intent blocks, kept {len(kept)} regex/lookup blocks")

print("\nDone. Now click Retrain Model in the admin panel.")
