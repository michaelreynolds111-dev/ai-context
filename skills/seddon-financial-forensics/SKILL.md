---
name: seddon-financial-forensics
description: Forensic financial analysis for the Seddon family law matter. Use for ANY financial query in this matter — income analysis, dissipation calculations, undisclosed asset investigation, Centrelink eligibility, Amy Thompson reconciliation, renovation expense analysis, annual lifestyle costs, asset pool quantification, affidavit schedules. Triggers on mentions of the Seddon matter, PocketSmith CSV, dissipation, or any financial figure from this case.
---

# Seddon Financial Forensics [SENSITIVE]

## When to use
- Income analysis (declared vs actual, salary vs drawings)
- Dissipation calculations (what left the asset pool, when, to whom)
- Undisclosed asset investigation
- Centrelink eligibility audit
- Amy Thompson payment reconciliation
- Renovation expense deep-dives
- Annual lifestyle cost analysis
- Asset pool quantification for s.79 purposes
- Building tables or schedules for affidavits or court documents

## Hard rules
- **Every figure must be sourced.** State the document, date range, and line items behind every calculation.
- **Never round or estimate without saying so.** Flag approximations explicitly.
- **Never infer intent** — describe what the financial record shows, not why it happened.
- **Distinguish between categories:** transfers, cash withdrawals, direct payments, and inter-account movements are different things and must not be conflated.
- **Gambling losses are a specific dissipation category** — track separately with dates and amounts.
- **Amy Thompson transfers are a specific category** — track separately with running total.

- **Custodian / documents-only.** Figures come exclusively from the `seddon-source/` source documents (PocketSmith CSV, bank statements, tax returns, payslips). Michael holds **no passwords and no account access** to any Seddon account; work from the provided documents only.

## Process
1. Identify the specific question (income, dissipation, asset pool, eligibility, etc.)
2. Identify which data source applies (PocketSmith CSV, bank statements, tax returns, payslips).
3. Calculate with full workings shown.
4. State the result with the supporting figures and source references.
5. Flag any gaps, inconsistencies, or data quality issues explicitly.

## Output format
- Tables for multi-row data (dissipation register, transaction lists, annual summaries)
- Totals with breakdowns, never totals alone
- For affidavit schedules: formal table format suitable for court filing
- Flag: [GAP] where data is missing, [CHECK] where figures need verification

## Routing [SENSITIVE]
This skill handles [SENSITIVE] family law content. Route only via DeepInfra direct or Anthropic direct. Never OpenRouter or any logging-enabled path.
