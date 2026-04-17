"""
reset_training_data.py — Clears seeded data and reloads from actual NLU YAML files.
Run ONCE from e:\BankBot\admin\: python reset_training_data.py
"""
import sys, os, yaml
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from database import execute, query

RASA_DIR  = r"e:\BankBot"
DATA_DIR  = os.path.join(RASA_DIR, "data")

# Prefer .bak files (original data) if current files were already cleared
NLU_FILES = [
    (os.path.join(DATA_DIR, "nlu.yml.bak"),         os.path.join(DATA_DIR, "nlu.yml")),
    (os.path.join(DATA_DIR, "nlu_module2.yml.bak"),  os.path.join(DATA_DIR, "nlu_module2.yml")),
]
DOMAIN_PATHS = [
    os.path.join(RASA_DIR, "domain.yml.bak"),
    os.path.join(RASA_DIR, "domain.yml"),
]


def parse_nlu(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    rows = []
    for block in (data or {}).get("nlu") or []:
        if not isinstance(block, dict) or "intent" not in block:
            continue
        intent = block["intent"]
        for line in (block.get("examples") or "").strip().splitlines():
            line = line.strip()
            if line.startswith("- "):
                ex = line[2:].strip()
                if ex:
                    rows.append({"intent": intent, "example_text": ex})
    return rows


print("=== Resetting Training Data from YAML Files ===\n")

# Step 1: Clear existing data
execute("TRUNCATE TABLE training_data")
execute("DELETE FROM faq")
print("✅ Cleared training_data and faq tables")

# Step 2: Import training examples
imported, seen = 0, set()
for (bak_path, main_path) in NLU_FILES:
    path = bak_path if os.path.exists(bak_path) else main_path
    if not os.path.exists(path):
        print(f"   ⚠️  Not found: {path}")
        continue
    rows = parse_nlu(path)
    for row in rows:
        key = (row["intent"], row["example_text"])
        if key in seen:
            continue
        seen.add(key)
        execute(
            "INSERT INTO training_data (intent, example_text) VALUES (%s, %s)",
            (row["intent"], row["example_text"])
        )
        imported += 1
    print(f"   ✅ {len(rows)} examples from {os.path.basename(path)}")

print(f"\n✅ Total training examples imported: {imported}")

# Step 3: Import FAQs from domain.yml
all_nlu = list(seen)
nlu_by_intent = defaultdict(list)
for intent, ex in seen:
    nlu_by_intent[intent].append(ex)

for dp in DOMAIN_PATHS:
    if not os.path.exists(dp):
        continue
    with open(dp, "r", encoding="utf-8") as f:
        domain = yaml.safe_load(f)
    responses = (domain or {}).get("responses", {})
    faq_imported = 0
    for utter_name, resp_list in responses.items():
        if not utter_name.startswith("utter_faq_"):
            continue
        intent = utter_name[len("utter_"):]
        answer = (resp_list or [{}])[0].get("text", "")
        if not answer:
            continue
        examples = nlu_by_intent.get(intent, [])
        question = examples[0] if examples else intent.replace("_", " ").title()
        execute("INSERT INTO faq (question, answer) VALUES (%s, %s)", (question, answer))
        faq_imported += 1
    if faq_imported:
        print(f"✅ Imported {faq_imported} FAQs from {os.path.basename(dp)}")
        break

# Summary
td   = query("SELECT COUNT(*) AS c FROM training_data")[0]["c"]
ints = query("SELECT COUNT(DISTINCT intent) AS c FROM training_data")[0]["c"]
faq  = query("SELECT COUNT(*) AS c FROM faq")[0]["c"]
print(f"\n📊 Final counts:")
print(f"   Training examples : {td} across {ints} intents")
print(f"   FAQs              : {faq}")
print("\n🎉 Done! Refresh the Training Data page — all intents will show.")
