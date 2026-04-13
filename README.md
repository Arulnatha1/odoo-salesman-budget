# Odoo 18 — Salesman GP Budget vs Actual

A monthly gross profit budget tracking module for Odoo 18. Designed for sales managers who need to set GP targets per salesman at the start of the financial year and track actual performance month by month from posted invoices.

## The Problem This Solves

Most sales teams track budgets in Excel — the sales manager sets targets at the start of the year, and at the end of each month someone manually pulls invoice data and reconciles it against the spreadsheet. This process is slow, error-prone, and gives no real-time visibility.

This module solves that by:
- Storing monthly GP budgets per salesman directly in Odoo
- Computing actual GP automatically from posted invoices every day
- Showing budget vs actual vs variance with traffic light indicators
- Giving the sales manager a live dashboard without any manual reconciliation
- Allowing each salesman to see only their own performance

## Features

### Monthly GP Budget Management
- One budget record per salesman per financial year
- 12 monthly GP budget lines generated automatically
- Budget amounts editable directly in the monthly table
- Year totals computed automatically — total budget, total actual, total variance, achievement %
- Full workflow: Draft → Active → Closed
- Chatter and audit trail on every budget record

### Automatic Actual GP Computation
- Actuals pulled from posted customer invoices in Odoo
- Filtered by salesman (invoice responsible user) and month
- Credit notes (out_refund) subtracted automatically — no manual adjustment needed
- GP per line = invoice revenue − (product standard cost × quantity)
- Invoice count per month visible for audit purposes
- Daily scheduled action refreshes all active budgets automatically
- Manual refresh available via Refresh Actuals button

### Traffic Light Indicators
- Green — achievement 80% or above — On Track
- Amber — achievement 50% to 79% — At Risk
- Red — achievement below 50% — Behind
- Grey — no budget set for that month
- Colour coding applied to both the monthly line list and the main budget list view

### Dashboard and KPI Views
- Graph view — bar chart comparing GP budget vs actual GP vs variance by month
- Pivot table — all salesmen as rows, months as columns, financial measures in cells
- Filter by salesman, year, active budgets, or current year
- Group by salesman or year
- Manager sees all salesmen — salesman sees only their own record

### CSV Import with Template Download
- Download a pre-filled CSV template with all salesman logins and zero budget values
- Template includes an instruction row explaining the format
- Fill in budget amounts in Excel or any spreadsheet app
- Upload the filled CSV — Odoo creates or updates budget records automatically
- Budgets activated automatically on successful import
- Import result shows records created, updated, and any errors

### Printable PDF Report
- Monthly performance report per salesman
- Shows all 12 months with budget, actual, variance, achievement %, and traffic light status
- Row colours match the traffic light (green, amber, red)
- Year total row at the bottom
- Disclaimer note about standard cost timing
- Generated via wkhtmltopdf — A4 format with company header

### Access Control
- Sales Manager — full access to all salesman budgets, can create, edit, activate, close
- Salesman — read only access to their own budget record via My Budget filter
- Portal users — no access

## Screenshots

### Monthly Budget View
```
┌─────────────────────────────────────────────────────────────────────┐
│  Marc Demo — 2026                              [Active]             │
│  [Refresh Actuals]  [Close Year]                                    │
├──────────────────────┬──────────────────────────────────────────────┤
│  SALESMAN            │  YEAR SUMMARY                                │
│  Salesman: Marc Demo │  Total Budget    :  64,000.00               │
│  Year    : 2026      │  Total Actual GP :  -6,500.00               │
│  Company : Aletek    │  Total Variance  : -70,500.00               │
│                      │  Achievement %   :     -10.2%               │
├──────────┬───────────┬──────────┬──────────┬──────────┬────────────┤
│  Month   │ GP Budget │ Actual GP│ Variance │ Achiev % │ Status     │
├──────────┼───────────┼──────────┼──────────┼──────────┼────────────┤
│ January  │  5,000.00 │     0.00 │-5,000.00 │     0.0% │ [Behind]   │
│ February │  6,000.00 │     0.00 │-6,000.00 │     0.0% │ [Behind]   │
│ March    │  5,000.00 │ 3,250.00 │-1,750.00 │    65.0% │ [At Risk]  │
│ April    │  5,000.00 │ 4,800.00 │  -200.00 │    96.0% │ [On Track] │
└──────────┴───────────┴──────────┴──────────┴──────────┴────────────┘
```

## Installation

### Requirements
- Odoo 18.0 Community Edition
- Dependencies installed automatically: `base`, `mail`, `sale`, `account`, `sales_team`
- wkhtmltopdf 0.12.6 for PDF reports

### Steps
1. Copy the `salesman_budget` folder into your Odoo custom addons path
2. Restart your Odoo server
3. Go to **Apps → Update Apps List**
4. Search for **Salesman Budget vs Actual**
5. Click **Activate**

A new **Sales Budget** app appears in your main menu.

## How to Use

### Setting Up Budgets for the Year

**Option A — Manual entry:**
1. Go to **Sales Budget → Budgets → New**
2. Select the salesman and financial year
3. Click **Generate 12 Monthly Lines**
4. Fill in the GP budget amount for each month
5. Click **Activate**

**Option B — CSV import (recommended for 10+ salesmen):**
1. Go to **Sales Budget → Import from CSV**
2. Set the financial year
3. Click **Download CSV Template**
4. Open the downloaded file in Excel
5. Fill in the monthly GP budget amounts for each salesman row
6. Delete the instruction row (starting with #)
7. Save as CSV format
8. Upload the filled CSV and click **Import Budgets**

### CSV Template Format
```
salesman_login,january,february,march,april,may,june,july,august,september,october,november,december
marc.demo@company.com,5000,6000,5000,5000,5000,6000,5000,6000,6000,6000,5000,5000
mitchell.admin@company.com,6000,6000,6000,6000,6000,6000,6000,6000,6000,6000,6000,6000
```

### Viewing Performance
1. Go to **Sales Budget → Dashboard** for the graph view
2. Go to **Sales Budget → Budgets** for the list view with colour coding
3. Click any salesman to see their 12-month detail
4. Use **Refresh Actuals** to pull the latest invoice data on demand

### Printing a Report
1. Open any budget record
2. Click **Print** → **Monthly Performance Report**
3. A PDF downloads with the full year breakdown

## Technical Reference

### Models

#### `salesman.budget` — Main budget record
| Field | Type | Description |
|-------|------|-------------|
| `salesman_id` | Many2one | Salesman (res.users) |
| `year` | Integer | Financial year |
| `state` | Selection | draft, active, closed |
| `total_budget` | Monetary | Computed: sum of monthly budgets |
| `total_actual` | Monetary | Computed: sum of monthly actuals |
| `total_variance` | Monetary | Computed: actual − budget |
| `total_achievement` | Float | Computed: actual / budget × 100 |

#### `salesman.budget.line` — Monthly line
| Field | Type | Description |
|-------|------|-------------|
| `budget_id` | Many2one | Parent budget |
| `month` | Integer | Month number 1-12 |
| `month_name` | Char | Month name (January etc) |
| `budget_amount` | Monetary | GP target for this month |
| `actual_gp` | Monetary | Computed from posted invoices |
| `variance` | Monetary | Computed: actual − budget |
| `achievement_percent` | Float | Computed: actual / budget × 100 |
| `traffic_light` | Selection | green, amber, red, grey |
| `invoice_count` | Integer | Number of invoices in this month |

### GP Calculation
Actual GP per invoice line = `price_subtotal − (product.standard_price × quantity)`

Includes: posted customer invoices (`out_invoice`)
Subtracts: posted credit notes (`out_refund`)
Excludes: draft, cancelled, and vendor bills

**Note:** Standard cost is taken at the time of the report run, not at the time of invoicing. If standard costs have changed during the year, historical months may show slightly different GP than at invoice date.

### Scheduled Action
- Name: Salesman Budget: Refresh Actual GP
- Frequency: Daily
- Scope: All active budget lines
- Runs automatically — no manual intervention needed

### Traffic Light Logic
| Achievement % | Status | Colour |
|---|---|---|
| ≥ 80% | On Track | Green |
| 50% – 79% | At Risk | Amber |
| < 50% | Behind | Red |
| No budget set | No Budget | Grey |

## Use Case — F&B Machinery Distributor

Aletek International has 10 salesmen. At the start of each financial year the sales manager sets monthly GP targets — for example $5,000 per month for junior salesmen and $8,000 for seniors.

Previously this was tracked in Excel — the accountant pulled invoice data at month end, calculated GP manually, and emailed a spreadsheet. This took 2-3 hours per month and was always slightly wrong because credit notes were sometimes missed.

With this module:

1. **January** — sales manager downloads the CSV template, fills in 10 rows with monthly targets, imports it in under 5 minutes. All 10 budget records created and activated automatically.
2. **During the month** — each salesman can check their own progress any time by going to Sales Budget → My Budget filter.
3. **Month end** — the manager opens the Dashboard and sees all 10 salesmen with traffic light status. No Excel. No manual calculation. No missed credit notes.
4. **Performance review** — manager prints the PDF report for each salesman and uses it in the monthly review meeting.
5. **Commission calculation** — accountant downloads the pivot table to Excel for commission calculation based on the pre-agreed percentage structure.

## Author

**Arulnatha**
Odoo ERP Consultant and Accountant
CIMA Management Level | 8+ years finance experience
Specialisation: F&B industry ERP implementations, accounting automation, and sales performance tracking

Available for Odoo consulting and custom module development.

## License

[LGPL-2.1](LICENSE)

---

*Tested on Odoo 18.0 Community Edition.*
*Built for F&B machinery distributors and multi-salesman sales teams.*
