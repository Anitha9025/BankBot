# Banking AI Chatbot — Module 1: Intent & Entity Recognition Engine

> **Scope:** NLU only — Intent Classification + Entity Extraction using Rasa 3.x with DIETClassifier.

---

## Project Structure

```
banking_chatbot/
├── config.yml                  # NLU pipeline (DIETClassifier)
├── domain.yml                  # Intents, entities, slots, responses
├── data/
│   ├── nlu.yml                 # Training examples with entity annotations
│   └── rules.yml               # Basic conversation rules
├── tests/
│   └── test_nlu.yml            # NLU test cases with expected outputs
└── README.md
```

---

## Intents Defined (15 Total)

| # | Intent              | Description                              |
|---|---------------------|------------------------------------------|
| 1 | `check_balance`     | Account balance inquiry                  |
| 2 | `loan_inquiry`      | Loan products, rates, eligibility        |
| 3 | `block_card`        | Block lost/stolen debit or credit card   |
| 4 | `find_atm`          | Locate nearby ATMs                       |
| 5 | `find_branch`       | Locate bank branches                     |
| 6 | `transaction_status`| Check payment/transfer status            |
| 7 | `transfer_money`    | Fund transfer requests                   |
| 8 | `mini_statement`    | Last N transaction summary               |
| 9 | `open_account`      | New account opening                      |
|10 | `apply_credit_card` | Credit/debit card application            |
|11 | `change_pin`        | ATM/card PIN change or reset             |
|12 | `greet`             | Greeting messages                        |
|13 | `goodbye`           | Farewell messages                        |
|14 | `affirm`            | Positive confirmation                    |
|15 | `deny`              | Negative / cancel                        |

---

## Entities Defined

| Entity         | Example Values                                 |
|----------------|------------------------------------------------|
| `account_type` | savings, current                               |
| `amount`       | 5000, 100000, 2500                             |
| `date`         | January 2024, 15th March, yesterday            |
| `location`     | Mumbai, Chennai, T Nagar, Bangalore            |
| `card_type`    | credit, debit                                  |
| `loan_type`    | home, personal, car, education, business       |

---

## Slots Defined

All entities are mapped to slots for downstream use in Module 2 (Dialogue Management):

```yaml
account_type  → text slot
amount        → float slot
date          → text slot
location      → text slot
card_type     → text slot
loan_type     → text slot
```

---

## NLU Pipeline Summary (config.yml)

```
WhitespaceTokenizer
  └─ Splits text into tokens

RegexFeaturizer
  └─ Pattern matching (amounts, dates)

LexicalSyntacticFeaturizer
  └─ Word shape, prefix/suffix features

CountVectorsFeaturizer (word)
  └─ Bag-of-words intent features

CountVectorsFeaturizer (char_wb n-gram)
  └─ Handles typos, OOV words

DIETClassifier (100 epochs)
  └─ Joint intent + entity model (transformer-based)
  └─ BILOU tagging for multi-token entities

EntitySynonymMapper
  └─ Normalises entity synonyms

RegexEntityExtractor
  └─ Rule-based structured entity extraction

FallbackClassifier (threshold: 0.70)
  └─ Triggers default response for low-confidence predictions
```

---

## Setup & Installation

### Prerequisites
- Python 3.8 – 3.10 (Rasa 3.x requirement)
- pip ≥ 21.x

### Step 1 — Create a Virtual Environment

```bash
python -m venv banking_env
source banking_env/bin/activate        # Linux / macOS
# OR
banking_env\Scripts\activate           # Windows
```

### Step 2 — Install Rasa

```bash
pip install rasa==3.6.20
# Verify installation
rasa --version
```

### Step 3 — Copy Project Files

Copy the provided files into your project directory:
```
banking_chatbot/
├── config.yml
├── domain.yml
├── data/nlu.yml
├── data/rules.yml
└── tests/test_nlu.yml
```

### Step 4 — Validate Project

```bash
cd banking_chatbot
rasa data validate
```

Expected output:
```
Your data seems to be of very high quality!
The validation was successful.
```

---

## Training the Model

```bash
rasa train nlu
```

What happens:
- Rasa reads `data/nlu.yml` and `config.yml`
- Trains DIETClassifier for 100 epochs
- Saves model to `models/` directory (e.g., `models/nlu-20240115-123456.tar.gz`)

Training time: ~2–5 minutes depending on hardware.

---

## Testing Intent & Entity Predictions

### Interactive Shell Test

```bash
rasa shell nlu
```

Type sentences and see real-time predictions:

```
NLU model loaded. Type a message and press enter to parse it.
Next message:
  What is my savings account balance?

{
  "text": "What is my savings account balance?",
  "intent": {
    "name": "check_balance",
    "confidence": 0.9987
  },
  "entities": [
    {
      "entity": "account_type",
      "value": "savings",
      "confidence": 0.9921,
      "extractor": "DIETClassifier"
    }
  ]
}
```

### Automated NLU Test Suite

```bash
rasa test nlu --nlu data/nlu.yml --cross-validation
```

Generates a detailed report in `results/`:
- `intent_report.json`   — Precision, Recall, F1 per intent
- `DIETClassifier_report.json` — Entity extraction metrics
- `intent_confusion_matrix.png` — Visual confusion matrix

### Run Specific Test File

```bash
rasa test nlu --nlu tests/test_nlu.yml
```

---

## Example Predictions & Expected Outputs

| Input Sentence | Expected Intent | Expected Entities |
|----------------|----------------|-------------------|
| `What is my savings account balance?` | `check_balance` | `account_type=savings` |
| `Block my credit card immediately` | `block_card` | `card_type=credit` |
| `Find ATM near Chennai` | `find_atm` | `location=Chennai` |
| `Transfer 5000 to my friend` | `transfer_money` | `amount=5000` |
| `Apply for a home loan of 500000` | `loan_inquiry` | `loan_type=home, amount=500000` |
| `Transfer 2500 from savings to current` | `transfer_money` | `amount=2500, account_type=savings` |
| `Was my payment on 15th March successful?` | `transaction_status` | `date=15th March` |
| `I want to open a current account` | `open_account` | `account_type=current` |
| `How do I reset my debit card PIN?` | `change_pin` | `card_type=debit` |
| `Show me my mini statement` | `mini_statement` | _(none)_ |
| `Hi` | `greet` | _(none)_ |
| `Goodbye` | `goodbye` | _(none)_ |

---

## Advanced: Parse via Rasa REST API

```bash
# Start the Rasa NLU server
rasa run --enable-api --port 5005
```

```bash
# POST request to parse intent and entities
curl -X POST http://localhost:5005/model/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Transfer 10000 from savings account"}'
```

Expected JSON response:
```json
{
  "text": "Transfer 10000 from savings account",
  "intent": {
    "name": "transfer_money",
    "confidence": 0.9978
  },
  "entities": [
    {
      "entity": "amount",
      "value": "10000",
      "confidence": 0.9850,
      "extractor": "DIETClassifier"
    },
    {
      "entity": "account_type",
      "value": "savings",
      "confidence": 0.9763,
      "extractor": "DIETClassifier"
    }
  ],
  "intent_ranking": [
    { "name": "transfer_money", "confidence": 0.9978 },
    { "name": "check_balance",  "confidence": 0.0012 }
  ]
}
```

---

## Common Troubleshooting

| Problem | Solution |
|---------|----------|
| Python version mismatch | Use Python 3.8–3.10 with `pyenv` |
| `rasa train` is slow | Reduce `epochs` to 50 for faster iteration |
| Low intent confidence | Add more training examples (aim for 15+) |
| Entity not detected | Check BILOU annotations in `nlu.yml` |
| Validation errors | Run `rasa data validate` to see YAML issues |

---

## What's Next — Module 2 (Not in Scope Here)

Module 2 will cover **Dialogue Management**:
- Stories and conversation flows
- Form Actions for slot filling
- Custom Actions for live banking API calls
- Integration with core banking systems
