# Household Schema

**Classification:** [IDENTITY]
**Purpose:** Structure only — what fields exist. **No values.**
**Status:** SCAFFOLD — categories drafted from typical Australian household admin scope. Refine to actual household data at Cluster 6 build time (post-Session 10).

---

## Rules for this file

1. **Never a value.** A field name is fine (`medicare_number`). A value is not (`000 00000 0` — use X characters, not real digits). Values live in `~/household-vault/`, which is not in git.
2. **Never a Tier-1 field.** Passwords, PINs, MFA seeds, recovery codes, and security answers are not fields the vault holds — they live in the password manager. What the schema records is the *fact* that a login exists, and where its Tier-1 material lives (e.g. "MyGov: login stored in Bitwarden").
3. **Structure is portable, safe to commit.** The point of writing structure down is that the agent can tell you *what it should know* even when it can't find a specific value.

---

## People

Each person in the household has:

- `name`
- `dob`
- `medicare_number` (Tier 2, source: Medicare card)
- `medicare_reference_number` (1-digit, on card)
- `medicare_expiry`
- `tfn` (Tier 2, source: TFN letter or ATO record)
- `passport` — number, country, issue date, expiry, source scan filename
- `licence` — number, class, expiry, source scan filename
- `birth_certificate` — source scan filename, date issued
- `crn` — Centrelink Customer Reference Number (if applicable)
- `ndis_number` (if applicable)
- `ihi` — Individual Healthcare Identifier

---

## Vehicles

Each vehicle has:

- `label` (household nickname — "the Corolla")
- `make_model_year`
- `rego` (Tier 2)
- `rego_expiry`
- `insurer` — name, policy number (Tier 2), policy expiry, source PDS or renewal doc
- `roadside_membership` — provider, membership number (Tier 2), expiry
- `service_provider` — mechanic name/contact, last service date, next due
- `finance` (if applicable) — lender, account reference (Tier 2), payout figure as at date

---

## Property

Each property has:

- `address`
- `ownership_type` — owned / rented / mortgaged
- `lot_plan` — title reference
- `council` — LGA name, rates reference number (Tier 2)
- `water` — provider, account number (Tier 2)
- `electricity` — provider, account number (Tier 2), NMI
- `gas` — provider, account number (Tier 2), MRIN
- `internet` — provider, account number (Tier 2), NBN address ID
- `home_insurance` — provider, policy number, expiry, PDS scan
- `contents_insurance` — provider, policy number, expiry, PDS scan
- `strata_body_corporate` (if applicable) — reference, contact
- `mortgage` (if applicable) — lender, account reference (Tier 2), rate at date, next review

---

## Health

Each person has:

- `gp` — practice, doctor name, contact
- `specialists` — list: type, name, contact, referral status
- `private_health` — insurer, membership number (Tier 2), level of cover, source doc
- `prescriptions` — list: medication, dose, prescriber, last filled, repeat count remaining
- `allergies` — clinical detail, source record
- `emergency_contact` — name, relationship, phone

---

## Insurance (non-vehicle, non-property)

Each policy has:

- `type` — life, income protection, TPD, travel, pet, etc
- `insured_person`
- `insurer`
- `policy_number` (Tier 2)
- `sum_insured` (as at date)
- `expiry_or_review`
- `pds_document` — source filename

---

## Education (if applicable)

Each child/student has:

- `school` — name, campus, contact
- `student_id` (Tier 2)
- `year_level`
- `enrolment_documents` — source filenames

---

## Government / benefits

- `mygov_account` — login stored in password manager
- `ato_myid` — login stored in password manager
- `centrelink` — CRN per person (Tier 2), current payment types
- `service_australia` — reference numbers per service

---

## Financial (reference only — no values)

The vault holds references so the agent can answer *"which bank is the joint account with?"* — it does not hold balances, card numbers, or credentials.

Each account has:

- `label` (household nickname)
- `bank`
- `account_holders`
- `account_purpose` — everyday / savings / offset / mortgage / credit
- `bsb_and_account_number` (Tier 2 — source: last statement)
- `card_type` (if applicable) — debit / credit, holders
- `login_pointer` — "login stored in [password manager] as [item name]"

Card numbers and expiry dates are **Tier 1** (they authenticate transactions with CVV/expiry). Do not store them in the vault. If they need to be somewhere, that somewhere is the password manager.

---

## Memberships and subscriptions

Each item has:

- `provider`
- `membership_number` (Tier 2)
- `member_since`
- `renewal_date`
- `cost_at_last_renewal`
- `login_pointer` (if online)

---

## Warranties and appliances

Each item has:

- `item` — description
- `make_model`
- `serial_number`
- `purchase_date`
- `retailer`
- `warranty_end`
- `receipt_scan` — source filename
- `manual_link_or_scan` (if kept)

---

## Contacts

Each entry has:

- `name`
- `role` — e.g. GP, dentist, plumber, electrician, accountant, solicitor, tradie, insurance broker
- `contact` — phone, email
- `notes` — anything relevant to future use

---

## Renewals — the calendar

Renewals live in `~/household-vault/renewals.md`, not here. Each entry there has:

- `item` (e.g. "Corolla rego")
- `due_date`
- `notice_period` — how far ahead to act
- `action` — what to actually do
- `who` — which person's account/name it's under
- `last_completed`

The schema records that a field exists. The renewals file records dates. Neither holds the value being renewed — that comes from the source document.

---

## Fields that are deliberately absent

- **Passwords, PINs, MFA seeds, recovery codes, security answers, private keys** — Tier 1, password manager only, no exceptions.
- **Full card numbers with expiry and CVV** — Tier 1 (authenticates transactions).
- **Answers to security questions** — Tier 1 (they authenticate).
- **Health record content beyond identifiers and prescription references** — clinical detail lives in the health provider's system. The vault records "GP is Dr X at Practice Y" and the Medicare/private-health identifiers to reach them; it is not a clinical record.
