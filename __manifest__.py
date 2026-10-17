{
    "name": "Accounting Report",
    "version": "18.0.1.0.0",
    "summary": "Configurable trial balance, profit and loss, balance sheet and notes-to-accounts Excel reports",
    "description": """
Accounting Report
=================

Adds configurable financial reporting on top of Odoo Accounting.

Features
--------
* Define reusable *Note Templates* that map accounts to report notes
  (header, detail and total lines) for both the Profit and Loss and the
  Balance Sheet.
* Link accounts to notes directly from the account form.
* Export a single Excel workbook containing:

  - Trial Balance
  - Profit and Loss
  - Balance Sheet
  - Notes to Accounts

* Report wizard to generate the workbook for a given end date, with the
  option to include all accounts or only those with movements.

Configuration
-------------
1. Go to *Accounting > Configuration > Account Notes* and define the notes.
2. Create a *Note Template* and lay out the Profit and Loss and Balance
   Sheet structure.
3. On each account, add its notes in the *Related Notes* tab.
4. Run *Accounting > Reporting > Trial Balance Report*.
    """,
    "category": "Accounting/Accounting",
    "author": "Sarah Unokerieghan",
    "license": "LGPL-3",
    "depends": ["base", "account"],
    "external_dependencies": {"python": ["xlsxwriter"]},
    "data": [
        "views/sb_account_notes.xml",
        "views/sb_note_template.xml",
        "views/account_inherit.xml",
        "wizard/download_report_wizard.xml",

        "views/menu.xml",
        "security/ir.model.access.csv",

    ],
    'assets': {
        'web.assets_backend': [
            'sb_accounting_reports/static/src/action_manager.js',]
    },

    "installable": True,
    "application": True,
}
