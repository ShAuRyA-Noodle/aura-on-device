# FinanceAgent

Per `technical_spec.md` §3.3.

UPI SMS parsing + Gmail receipt parsing + categorisation + Z-score anomaly
detection + linear-burn EoM projection + frugal substitution suggestions. All
on-device. Persist contract is `(merchant_hash, amount, currency,
account_last4, ts, category)` — raw SMS body never leaves the parser.

## Bank coverage

The regex hot path covers the 4 most-common Indian bank UPI formats:

### HDFC
```
Sent Rs.350.00 from A/c **1234 to ZOMATO via UPI on 07-MAY
Sent Rs. 450.00 From HDFC Bank A/C *1234 To VPA zomato@hdfcbank On 07-05-26
```
Captured groups: direction (Sent/Received), amount, account_last4 (after `**`
or `*`), merchant (token before `via UPI` / `On <date>`), date.

### SBI
```
Dear Customer, Rs.1200.00 debited from A/c X1234 on 07-05-26 to VPA bigbasket@okhdfc Ref 412345. -SBI
```
Captured groups: direction (debited/credited), amount (separate scan), account
suffix after `X`/`*`, date, merchant (after `to VPA`/`from VPA`).

### ICICI (card + UPI)
```
INR 250.00 spent on ICICI Bank Card XX1234 at SWIGGY on 07-May-26
Dear Customer, Acct XX1234 debited with INR 800.00 on 07-May-26; UPI:412345678912; toward swiggy@icici.
```

### Axis
```
INR 540 debited A/c no. XX1234 07-05-26 13:42 UPI/P2A/uber@axis/Uber
```

Anything that doesn't match falls into `unparsed_log` and would route to a
DistilBERT fallback in production (TEAM TO VERIFY: collect 200 SMS templates
per bank).

## Tools

| Name | Purpose |
|---|---|
| `parse_sms` | Regex bank-pack -> Transaction \| None. |
| `parse_gmail_receipt` | Resolve thread metadata to Transaction. |
| `categorize` | 14 fixed categories; merchant table + keyword fallback. |
| `anomaly_flag` | Per-category Z-score against 30d rolling mean + velocity check. |
| `predict_eom_balance` | Linear-burn EoM projection. Phase 2 swap-in: 2-layer LSTM. |
| `suggest_substitution` | Frugal swap per category. |

## Fixtures

| File | Purpose |
|---|---|
| `fixtures/upi_sms.jsonl` | 50 synthetic UPI SMS spanning HDFC, SBI, ICICI, Axis. |
| `fixtures/gmail_receipts.jsonl` | 20 receipt headers (Zomato, Swiggy, Blinkit, Amazon, IRCTC, Uber, BookMyShow). |

Names used: Anu, Manish, Riya, Kabir, Mira (no real personal data).

## Run tests

```bash
pytest agents/finance -q
```
