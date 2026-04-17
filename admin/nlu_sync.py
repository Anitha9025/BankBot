"""
nlu_sync.py — Sync between MySQL ↔ Rasa YAML files.

Startup:  import_all_to_db()   — reads YAML files → MySQL
Retrain:  write_training_yaml() — MySQL → data/nlu_admin.yml
          write_faq_yaml()      — MySQL → domain_faq.yml + data/nlu_faq.yml + data/rules_faq.yml
"""

import os
import re
import shutil
import logging
from collections import defaultdict

import yaml
from database import query, execute

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────
RASA_DIR   = os.getenv("RASA_PROJECT_DIR", r"e:\BankBot")
DATA_DIR   = os.path.join(RASA_DIR, "data")

NLU_SOURCES = [
    os.path.join(DATA_DIR, "nlu.yml"),
    os.path.join(DATA_DIR, "nlu.yml.bak"),          # fallback if original was cleared
    os.path.join(DATA_DIR, "nlu_module2.yml"),
    os.path.join(DATA_DIR, "nlu_module2.yml.bak"),  # fallback if original was cleared
]

DOMAIN_DIR    = os.path.join(RASA_DIR, "domain")
DOMAIN_FILE   = os.path.join(DOMAIN_DIR, "domain.yml")
RULES_FILE    = os.path.join(DATA_DIR, "rules.yml")

ADMIN_NLU     = os.path.join(DATA_DIR, "nlu_admin.yml")
FAQ_NLU       = os.path.join(DATA_DIR, "nlu_faq.yml")
DOMAIN_FAQ    = os.path.join(DOMAIN_DIR, "domain_faq.yml")
RULES_FAQ     = os.path.join(DATA_DIR, "rules_faq.yml")


# ── Helpers ──────────────────────────────────────────────────────────

def _parse_nlu_file(path):
    """Return [{intent, example_text}, ...] from a NLU YAML file."""
    if not os.path.exists(path):
        return []
    try:
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
    except Exception as e:
        logger.error(f"[nlu_sync] Error parsing {path}: {e}")
        return []


def _clear_nlu_intents(path):
    """
    Remove intent blocks from a NLU file, keeping regex/lookup blocks.
    Saves a .bak backup first.
    """
    if not os.path.exists(path):
        return
    shutil.copy2(path, path + ".bak")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "nlu" not in data:
            return
        # Keep only non-intent blocks (regex, lookup, synonym)
        data["nlu"] = [b for b in (data["nlu"] or []) if "intent" not in b]
        # Write back using manual formatting (preserves YAML readability)
        lines = [f'version: "{data.get("version", "3.1")}"', "", "nlu:", ""]
        for block in data["nlu"]:
            if "regex" in block:
                lines.append(f"- regex: {block['regex']}")
                lines.append("  examples: |")
                for ex_line in (block.get("examples") or "").strip().splitlines():
                    lines.append(f"    {ex_line.strip()}")
                lines.append("")
            elif "lookup" in block:
                lines.append(f"- lookup: {block['lookup']}")
                lines.append("  examples: |")
                for ex_line in (block.get("examples") or "").strip().splitlines():
                    lines.append(f"    {ex_line.strip()}")
                lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        logger.error(f"[nlu_sync] Error clearing {path}: {e}")
        shutil.copy2(path + ".bak", path)  # restore backup


def _remove_faq_from_domain(domain_path):
    """Remove utter_faq_* entries from domain.yml responses. Saves .bak."""
    if not os.path.exists(domain_path):
        return {}
    shutil.copy2(domain_path, domain_path + ".bak")
    removed = {}
    try:
        with open(domain_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Read the file as lines and remove utter_faq_* blocks
        # Use yaml to parse, remove faq responses, write custom yaml back
        # Actually: just use regex to clear utter_faq entries from responses section
        # Simple approach: read all non-faq responses
        with open(domain_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        responses = data.get("responses", {})
        faq_resp = {k: v for k, v in responses.items() if k.startswith("utter_faq_")}
        non_faq  = {k: v for k, v in responses.items() if not k.startswith("utter_faq_")}
        data["responses"] = non_faq

        # Write domain.yml back without faq responses (use safer approach)
        _write_domain_yml(domain_path, data)
        return faq_resp
    except Exception as e:
        logger.error(f"[nlu_sync] Error removing FAQ from domain: {e}")
        shutil.copy2(domain_path + ".bak", domain_path)
        return {}


def _write_domain_yml(path, data):
    """Write domain.yml preserving structure."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ── Import: YAML → MySQL (one-time on startup) ───────────────────────

def import_all_to_db():
    """
    Called once on Flask startup.
    Reads NLU YAML files → MySQL training_data.
    Reads domain.yml FAQ responses → MySQL faq.
    After import, clears source files to avoid duplication at retrain.
    """
    _import_training()
    _import_faqs()


def _import_training():
    count = query("SELECT COUNT(*) AS c FROM training_data")[0]["c"]
    if count > 0:
        logger.info("[nlu_sync] training_data already populated, skipping import.")
        return

    imported = 0
    for path in NLU_SOURCES:
        for row in _parse_nlu_file(path):
            execute(
                "INSERT IGNORE INTO training_data (intent, example_text) VALUES (%s, %s)",
                (row["intent"], row["example_text"])
            )
            imported += 1

    logger.info(f"[nlu_sync] Imported {imported} training examples → MySQL")

    # Clear intent blocks from source files (they'll be written to nlu_admin.yml at retrain)
    for path in NLU_SOURCES:
        _clear_nlu_intents(path)
    logger.info("[nlu_sync] Cleared NLU intent blocks from source files (backups saved as .bak)")


def _import_faqs():
    count = query("SELECT COUNT(*) AS c FROM faq")[0]["c"]
    if count > 0:
        logger.info("[nlu_sync] faq table already populated, skipping import.")
        return

    if not os.path.exists(DOMAIN_FILE):
        return

    with open(DOMAIN_FILE, "r", encoding="utf-8") as f:
        domain = yaml.safe_load(f)

    responses = (domain or {}).get("responses", {})

    # Also read NLU for example questions for each FAQ intent
    all_nlu = []
    for path in NLU_SOURCES:
        all_nlu.extend(_parse_nlu_file(path))
    by_intent = defaultdict(list)
    for row in all_nlu:
        by_intent[row["intent"]].append(row["example_text"])

    imported = 0
    for utter_name, resp_list in responses.items():
        if not utter_name.startswith("utter_faq_"):
            continue
        intent = utter_name[len("utter_"):]   # faq_working_hours
        answer = (resp_list or [{}])[0].get("text", "")
        if not answer:
            continue
        examples = by_intent.get(intent, [])
        question = examples[0] if examples else intent.replace("_", " ").title()
        execute("INSERT INTO faq (question, answer) VALUES (%s, %s)", (question, answer))
        imported += 1

    logger.info(f"[nlu_sync] Imported {imported} FAQs → MySQL")

    # Remove utter_faq_* from domain.yml (they'll be in domain_faq.yml)
    _remove_faq_from_domain(DOMAIN_FILE)
    logger.info("[nlu_sync] Removed utter_faq_* from domain.yml (backup saved)")


# ── Export: MySQL → YAML (called before retrain) ─────────────────────

def write_training_yaml():
    """Write ALL MySQL training_data → data/nlu_admin.yml + domain_admin.yml"""
    rows = query("SELECT intent, example_text FROM training_data ORDER BY intent, id")
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["intent"]].append(r["example_text"])

    # 1. Write NLU examples
    nlu_lines = ['version: "3.1"', "", "nlu:", ""]
    for intent, examples in grouped.items():
        nlu_lines.append(f"- intent: {intent}")
        nlu_lines.append("  examples: |")
        for ex in examples:
            nlu_lines.append(f"    - {ex}")
        nlu_lines.append("")
    with open(ADMIN_NLU, "w", encoding="utf-8") as f:
        f.write("\n".join(nlu_lines))

    # 2. Write domain_admin.yml — declares all intents so Rasa doesn't reject unknown ones
    domain_admin = os.path.join(DOMAIN_DIR, "domain_admin.yml")
    dom_lines = ['version: "3.1"', "", "intents:", ""]
    for intent in sorted(grouped.keys()):
        dom_lines.append(f"  - {intent}")
    dom_lines.append("")
    with open(domain_admin, "w", encoding="utf-8") as f:
        f.write("\n".join(dom_lines))

    logger.info(f"[nlu_sync] Wrote {len(rows)} training examples → {ADMIN_NLU} + domain_admin.yml")


def write_faq_yaml():
    """Write ALL MySQL FAQs → nlu_faq.yml, domain_faq.yml (with intents+actions), rules_faq.yml"""
    faqs = query("SELECT id, question, answer FROM faq ORDER BY id")

    nlu_lines  = ['version: "3.1"', "", "nlu:", ""]
    rule_lines = ['version: "3.1"', "", "rules:", ""]

    # domain_faq.yml needs: intents, responses, and actions declared
    intent_names = []
    utter_names  = []
    response_lines = []

    for faq in faqs:
        fid         = faq["id"]
        intent_name = f"faq_admin_{fid}"
        utter_name  = f"utter_faq_admin_{fid}"
        intent_names.append(intent_name)
        utter_names.append(utter_name)

        nlu_lines += [
            f"- intent: {intent_name}",
            "  examples: |",
            f"    - {faq['question']}",
            "",
        ]

        answer_safe = str(faq["answer"]).replace("\\", "\\\\").replace('"', '\\"')
        response_lines += [
            f"  {utter_name}:",
            f'  - text: "{answer_safe}"',
            "",
        ]

        rule_lines += [
            f"  - rule: Admin FAQ {fid} - {str(faq['question'])[:30]}",
            "    steps:",
            f"      - intent: {intent_name}",
            f"      - action: {utter_name}",
            "",
        ]

    # Build domain_faq.yml with ALL required sections
    dom_lines = ['version: "3.1"', "", "intents:", ""]
    for n in intent_names:
        dom_lines.append(f"  - {n}")
    dom_lines += ["", "responses:", ""]
    dom_lines += response_lines

    with open(FAQ_NLU, "w", encoding="utf-8") as f:
        f.write("\n".join(nlu_lines))
    with open(DOMAIN_FAQ, "w", encoding="utf-8") as f:
        f.write("\n".join(dom_lines))
    with open(RULES_FAQ, "w", encoding="utf-8") as f:
        f.write("\n".join(rule_lines))

    logger.info(f"[nlu_sync] Wrote {len(faqs)} FAQs → FAQ YAML files (with intents+responses declared)")

