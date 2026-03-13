import logging
import random
import re
from typing import Any, Text, Dict, List
from datetime import datetime

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ConversationPaused,
    ActionExecuted,
    UserUtteranceReverted,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  DUMMY BANKING API
# ═══════════════════════════════════════════════════════════════════

class DummyBankingAPI:

    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """
        Validates account number:
        - Must be exactly 10 digits
        - Must contain only digits (no letters, no spaces)
        In production: GET /api/accounts/{account_number}/validate
        """
        cleaned = account_number.strip()
        return bool(re.fullmatch(r"\d{10}", cleaned))

    @staticmethod
    def get_balance(account_type: str, account_number: str) -> Dict:
        """
        In production: GET /api/accounts/{account_number}/balance
        """
        balances = {
            "savings": {
                "balance": 45820.50,
                "available": 45320.50,
                "account_holder": "John Kumar"
            },
            "current": {
                "balance": 128000.00,
                "available": 125000.00,
                "account_holder": "John Kumar"
            },
        }
        key = (account_type or "savings").lower()
        return balances.get(key, balances["savings"])

    @staticmethod
    def transfer_funds(amount: float, account_type: str) -> Dict:
        return {
            "success": True,
            "transaction_id": f"TXN{random.randint(100000, 999999)}",
            "amount": amount,
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "status": "COMPLETED",
        }

    @staticmethod
    def get_loan_info(loan_type: str) -> Dict:
        data = {
            "home":      {"rate": "8.50%",  "max_amount": "Rs.1 Crore",  "tenure": "30 years", "fee": "0.5%"},
            "personal":  {"rate": "10.50%", "max_amount": "Rs.25 Lakhs", "tenure": "5 years",  "fee": "1.0%"},
            "car":       {"rate": "9.00%",  "max_amount": "Rs.50 Lakhs", "tenure": "7 years",  "fee": "0.5%"},
            "education": {"rate": "8.00%",  "max_amount": "Rs.20 Lakhs", "tenure": "15 years", "fee": "Nil"},
            "business":  {"rate": "11.00%", "max_amount": "Rs.2 Crores", "tenure": "10 years", "fee": "1.5%"},
        }
        return data.get((loan_type or "personal").lower(), data["personal"])

    @staticmethod
    def block_card(card_type: str) -> Dict:
        return {
            "success": True,
            "reference_id": f"BLK{random.randint(10000, 99999)}",
            "card_type": card_type,
            "status": "BLOCKED",
            "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        }

    @staticmethod
    def find_atms(location: str) -> List[Dict]:
        return [
            {"name": f"BankAI ATM - {location} Main",    "distance": "0.3 km", "address": f"123 Main Street, {location}",  "status": "Online", "cash": "Available"},
            {"name": f"BankAI ATM - {location} Mall",    "distance": "0.8 km", "address": f"City Mall, {location}",        "status": "Online", "cash": "Available"},
            {"name": f"BankAI ATM - {location} Station", "distance": "1.2 km", "address": f"Railway Station, {location}", "status": "Online", "cash": "Limited"},
        ]

    @staticmethod
    def find_branches(location: str) -> List[Dict]:
        return [
            {"name": f"BankAI - {location} Main Branch", "distance": "0.5 km", "address": f"MG Road, {location}",     "hours": "Mon-Fri 9:30-4:30, Sat 9:30-1:30", "ifsc": "BNKA0001234"},
            {"name": f"BankAI - {location} East Branch", "distance": "2.1 km", "address": f"East Avenue, {location}", "hours": "Mon-Fri 9:30-4:30",                 "ifsc": "BNKA0001235"},
        ]

    @staticmethod
    def get_transactions(date_filter: str) -> List[Dict]:
        return [
            {"date": "15 Mar 2024", "description": "UPI Transfer - John",      "amount": "-Rs.2,500",  "balance": "Rs.43,320"},
            {"date": "14 Mar 2024", "description": "Salary Credit",             "amount": "+Rs.45,000", "balance": "Rs.45,820"},
            {"date": "13 Mar 2024", "description": "Electricity Bill - BESCOM", "amount": "-Rs.1,200",  "balance": "Rs.820"},
            {"date": "12 Mar 2024", "description": "ATM Withdrawal",            "amount": "-Rs.5,000",  "balance": "Rs.2,020"},
            {"date": "11 Mar 2024", "description": "Grocery - BigBasket",       "amount": "-Rs.850",    "balance": "Rs.7,020"},
        ]


# ═══════════════════════════════════════════════════════════════════
#  HELPER — safely extract account number as plain text
#
#  ROOT CAUSE OF THE BUG:
#  Rasa's amount slot type is "float". When user types "2345678914",
#  Rasa tries to interpret it as amount=2345678914.0 rupees.
#  The action then reads amount slot, sees a huge number, and fires
#  the "exceeds daily limit" message.
#
#  FIX applied at THREE levels:
#  1. nlu_module2.yml — amount examples use SMALL numbers + rupee words
#     so model classifies "2345678914" as inform_account_number, not inform_amount
#  2. domain.yml      — amount slot has not_intent: [inform_account_number]
#     so account number replies can NEVER fill the amount slot
#  3. actions.py      — ActionCheckBalance reads account_number as a
#     raw string and NEVER converts it to float
# ═══════════════════════════════════════════════════════════════════

def get_account_number_from_tracker(tracker: Tracker) -> str:
    """
    Safely reads account_number slot as a plain string.
    Strips whitespace. Never converts to float.
    """
    raw = tracker.get_slot("account_number")
    if raw is None:
        return None
    # Convert to string in case Rasa stored it as a number internally
    return str(raw).strip().split(".")[0]   # remove any decimal e.g. "1234567890.0" → "1234567890"


# ═══════════════════════════════════════════════════════════════════
#  ACTION 1: CHECK BALANCE
# ═══════════════════════════════════════════════════════════════════

class ActionCheckBalance(Action):

    def name(self) -> Text:
        return "action_check_balance"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        account_type   = tracker.get_slot("account_type")
        account_number = get_account_number_from_tracker(tracker)   # always a string

        logger.info(f"[action_check_balance] account_type={account_type}, account_number={account_number}")

        # ── Step 1: Need account type first ─────────────────────────
        if not account_type:
            dispatcher.utter_message(response="utter_ask_account_type")
            return []

        # ── Step 2: Need account number ─────────────────────────────
        if not account_number:
            dispatcher.utter_message(response="utter_ask_account_number")
            return []

        # ── Step 3: Validate — must be exactly 10 digits ────────────
        if not DummyBankingAPI.validate_account_number(account_number):
            dispatcher.utter_message(
                text=(
                    f"'{account_number}' is not a valid account number.\n"
                    "Please enter a valid 10-digit account number.\n"
                    "Example: 1234567890"
                )
            )
            return [SlotSet("account_number", None)]   # clear bad value, ask again

        # ── Step 4: Fetch balance ────────────────────────────────────
        try:
            result = DummyBankingAPI.get_balance(account_type, account_number)

            # Mask account number: show only last 4 digits for security
            masked = "X" * (len(account_number) - 4) + account_number[-4:]

            dispatcher.utter_message(
                text=(
                    f"--- {account_type.capitalize()} Account Balance ---\n\n"
                    f"Account Holder:    {result['account_holder']}\n"
                    f"Account Number:    {masked}\n"
                    f"Account Type:      {account_type.capitalize()}\n\n"
                    f"Total Balance:     Rs.{result['balance']:,.2f}\n"
                    f"Available Balance: Rs.{result['available']:,.2f}\n\n"
                    f"As of: {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
                    f"Need a detailed statement or want to transfer funds?"
                )
            )

        except Exception as e:
            logger.error(f"[action_check_balance] API error: {e}")
            dispatcher.utter_message(
                text="I am having trouble fetching your balance right now. "
                     "Please try again or call 1800-XXX-XXXX."
            )

        # ── Step 5: Reset both slots ─────────────────────────────────
        return [
            SlotSet("account_type", None),
            SlotSet("account_number", None),
        ]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 2: TRANSFER MONEY
# ═══════════════════════════════════════════════════════════════════

class ActionTransferMoney(Action):

    def name(self) -> Text:
        return "action_transfer_money"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        amount       = tracker.get_slot("amount")
        account_type = tracker.get_slot("account_type")

        logger.info(f"[action_transfer_money] amount={amount}, account_type={account_type}")

        if not amount:
            dispatcher.utter_message(response="utter_ask_amount")
            return []

        # Safe conversion — amount slot is float type so this is fine here
        try:
            amount_val = float(amount)
        except (ValueError, TypeError):
            dispatcher.utter_message(text="Please provide a valid numeric amount. For example: 5000 rupees.")
            return [SlotSet("amount", None)]

        if amount_val <= 0:
            dispatcher.utter_message(
                text="The transfer amount must be greater than Rs.0. Please provide a valid amount."
            )
            return []

        if amount_val > 500000:
            dispatcher.utter_message(
                text=(
                    f"Rs.{amount_val:,.0f} exceeds the daily limit of Rs.5,00,000. "
                    "For large transfers please visit your nearest branch or call 1800-XXX-XXXX."
                )
            )
            return []

        try:
            result = DummyBankingAPI.transfer_funds(amount_val, account_type or "savings")
            dispatcher.utter_message(
                text=(
                    f"--- Transfer Successful ---\n\n"
                    f"Amount Transferred: Rs.{amount_val:,.2f}\n"
                    f"From Account:       {(account_type or 'Savings').capitalize()}\n"
                    f"Transaction ID:     {result['transaction_id']}\n"
                    f"Status:             {result['status']}\n"
                    f"Time:               {result['timestamp']}\n\n"
                    f"Please save your Transaction ID for future reference. "
                    f"Is there anything else I can help you with?"
                )
            )
        except Exception as e:
            logger.error(f"[action_transfer_money] Error: {e}")
            dispatcher.utter_message(
                text="Transfer could not be processed. Please try again or contact support at 1800-XXX-XXXX."
            )

        return [SlotSet("amount", None), SlotSet("account_type", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 3: LOAN INQUIRY
# ═══════════════════════════════════════════════════════════════════

class ActionLoanInquiry(Action):

    def name(self) -> Text:
        return "action_loan_inquiry"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        loan_type = tracker.get_slot("loan_type")
        amount    = tracker.get_slot("amount")

        if not loan_type:
            dispatcher.utter_message(response="utter_ask_loan_type")
            return []

        try:
            info     = DummyBankingAPI.get_loan_info(loan_type)
            emi_info = ""
            if amount:
                try:
                    rate_val     = float(info["rate"].replace("%", ""))
                    monthly_rate = rate_val / 12 / 100
                    tenure_years = int(info["tenure"].split()[0])
                    n = tenure_years * 12
                    p = float(amount)
                    if monthly_rate > 0:
                        emi = p * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)
                        emi_info = f"\nEstimated EMI for Rs.{p:,.0f}: Rs.{emi:,.0f} per month"
                except Exception:
                    pass

            dispatcher.utter_message(
                text=(
                    f"--- {loan_type.capitalize()} Loan Details ---\n\n"
                    f"Interest Rate:   {info['rate']} per annum\n"
                    f"Maximum Amount:  {info['max_amount']}\n"
                    f"Maximum Tenure:  {info['tenure']}\n"
                    f"Processing Fee:  {info['fee']}"
                    f"{emi_info}\n\n"
                    f"Would you like to apply for a {loan_type} loan? "
                    f"I can guide you through the document requirements."
                )
            )
        except Exception as e:
            logger.error(f"[action_loan_inquiry] Error: {e}")
            dispatcher.utter_message(text="I could not fetch loan details right now. Please call 1800-XXX-XXXX.")

        return [SlotSet("loan_type", None), SlotSet("amount", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 4: BLOCK CARD
# ═══════════════════════════════════════════════════════════════════

class ActionBlockCard(Action):

    def name(self) -> Text:
        return "action_block_card"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        card_type = tracker.get_slot("card_type")

        if not card_type:
            dispatcher.utter_message(response="utter_ask_card_type")
            return []

        try:
            result = DummyBankingAPI.block_card(card_type)
            dispatcher.utter_message(
                text=(
                    f"--- Card Blocked Successfully ---\n\n"
                    f"Card Type:    {card_type.capitalize()} Card\n"
                    f"Reference ID: {result['reference_id']}\n"
                    f"Status:       {result['status']}\n"
                    f"Time:         {result['timestamp']}\n\n"
                    f"Your card has been immediately blocked. No further transactions will be processed.\n\n"
                    f"To report fraud: 1800-XXX-XXXX\n"
                    f"Replacement card: Visit your nearest branch (5-7 working days)"
                )
            )
        except Exception as e:
            logger.error(f"[action_block_card] Error: {e}")
            dispatcher.utter_message(
                text="Card block failed. Please call our emergency helpline IMMEDIATELY at 1800-XXX-XXXX (24/7)."
            )

        return [SlotSet("card_type", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 5: FIND ATM
# ═══════════════════════════════════════════════════════════════════

class ActionFindATM(Action):

    def name(self) -> Text:
        return "action_find_atm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        location = tracker.get_slot("location")

        if not location:
            dispatcher.utter_message(response="utter_ask_location")
            return []

        try:
            atms     = DummyBankingAPI.find_atms(location)
            atm_list = "\n".join([
                f"\n{i+1}. {a['name']}\n"
                f"   Address:  {a['address']}\n"
                f"   Distance: {a['distance']}  |  Status: {a['status']}  |  Cash: {a['cash']}"
                for i, a in enumerate(atms)
            ])
            dispatcher.utter_message(
                text=f"ATMs near {location}:\n{atm_list}\n\nAll ATMs are operational 24/7. Need anything else?"
            )
        except Exception as e:
            logger.error(f"[action_find_atm] Error: {e}")
            dispatcher.utter_message(
                text=f"I could not find ATMs in {location} right now. Please try again or visit our website."
            )

        return [SlotSet("location", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 6: FIND BRANCH
# ═══════════════════════════════════════════════════════════════════

class ActionFindBranch(Action):

    def name(self) -> Text:
        return "action_find_branch"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        location = tracker.get_slot("location")

        if not location:
            dispatcher.utter_message(response="utter_ask_location")
            return []

        try:
            branches    = DummyBankingAPI.find_branches(location)
            branch_list = "\n".join([
                f"\n{i+1}. {b['name']}\n"
                f"   Address:  {b['address']}\n"
                f"   Hours:    {b['hours']}\n"
                f"   IFSC: {b['ifsc']}  |  Distance: {b['distance']}"
                for i, b in enumerate(branches)
            ])
            dispatcher.utter_message(
                text=f"Branches near {location}:\n{branch_list}\n\nNeed help with documents to carry?"
            )
        except Exception as e:
            logger.error(f"[action_find_branch] Error: {e}")
            dispatcher.utter_message(
                text=f"I could not find branches in {location}. Please check our website or call 1800-XXX-XXXX."
            )

        return [SlotSet("location", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 7: TRANSACTION STATUS
# ═══════════════════════════════════════════════════════════════════

class ActionTransactionStatus(Action):

    def name(self) -> Text:
        return "action_transaction_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        date_filter = tracker.get_slot("date")

        try:
            transactions = DummyBankingAPI.get_transactions(date_filter)
            header       = f"Transactions for {date_filter}" if date_filter else "Recent Transactions"
            rows         = "\n".join([
                f"  {t['date']} | {t['description'][:30]:<30} | {t['amount']:>10} | Bal: {t['balance']}"
                for t in transactions
            ])
            dispatcher.utter_message(
                text=f"{header}:\n\n{rows}\n\nShowing last {len(transactions)} transactions."
            )
        except Exception as e:
            logger.error(f"[action_transaction_status] Error: {e}")
            dispatcher.utter_message(
                text="Unable to fetch transactions right now. Please try Net Banking or call 1800-XXX-XXXX."
            )

        return [SlotSet("date", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 8: MINI STATEMENT
# ═══════════════════════════════════════════════════════════════════

class ActionMiniStatement(Action):

    def name(self) -> Text:
        return "action_mini_statement"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        account_type = tracker.get_slot("account_type")
        label        = (account_type or "Savings").capitalize()
        transactions = DummyBankingAPI.get_transactions(None)
        rows         = "\n".join([
            f"  {t['date']} | {t['description'][:28]:<28} | {t['amount']:>10}"
            for t in transactions
        ])
        dispatcher.utter_message(
            text=f"Mini Statement - {label} Account:\n\n{rows}\n\nShowing last {len(transactions)} transactions."
        )
        return [SlotSet("account_type", None)]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 9: ESCALATE TO HUMAN
# ═══════════════════════════════════════════════════════════════════

class ActionEscalateToHuman(Action):

    def name(self) -> Text:
        return "action_escalate_to_human"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        last_intent = tracker.latest_message.get("intent", {}).get("name", "unknown")
        ticket_id   = f"TKT{random.randint(100000, 999999)}"
        logger.info(f"[action_escalate_to_human] Escalating. Ticket: {ticket_id}")

        dispatcher.utter_message(
            text=(
                f"Connecting you to a Human Agent\n\n"
                f"Support Ticket ID: {ticket_id}\n"
                f"Topic: {last_intent.replace('_', ' ').title()}\n\n"
                f"An agent will be with you shortly. Estimated wait: 2 to 5 minutes.\n\n"
                f"If you prefer to call:\n"
                f"Toll-Free: 1800-XXX-XXXX (24/7)\n\n"
                f"Your conversation history has been shared with the agent."
            )
        )

        return [
            SlotSet("escalation_triggered", True),
            ConversationPaused(),
        ]


# ═══════════════════════════════════════════════════════════════════
#  ACTION 10: DEFAULT FALLBACK
# ═══════════════════════════════════════════════════════════════════

class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        fallback_count  = tracker.get_slot("consecutive_fallback_count") or 0
        fallback_count += 1
        logger.warning(f"[action_default_fallback] Fallback count: {fallback_count}")

        if fallback_count >= 2:
            dispatcher.utter_message(
                text="I have had trouble understanding your last couple of messages. "
                     "Let me connect you with a human agent who can better assist you."
            )
            return [
                SlotSet("consecutive_fallback_count", 0),
                ActionExecuted("action_escalate_to_human"),
            ]
        else:
            dispatcher.utter_message(
                text=(
                    "I am sorry, I did not quite understand that.\n\n"
                    "I can help you with:\n"
                    "  - Account balance and statements\n"
                    "  - Fund transfers\n"
                    "  - Loan inquiries\n"
                    "  - Card blocking\n"
                    "  - ATM and Branch locator\n"
                    "  - Banking FAQs\n\n"
                    "Please try rephrasing, or type 'agent' to speak with a human."
                )
            )
            return [
                SlotSet("consecutive_fallback_count", fallback_count),
                UserUtteranceReverted(),
            ]