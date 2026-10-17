import json
from odoo.tools import json_default

from odoo import models, fields

class TrialBalanceWizard(models.TransientModel):
    _name = 'sb.trial.balance.wizard'
    _description = 'Trial Balance Report Wizard'

    display_accounts = fields.Selection([
        ('all', 'All'),
        ('with_movements', 'With movements'),
    ], string="Display Accounts", default='with_movements')

    note_template = fields.Many2one('sb.note.templates', 'Note Template', required=True)

    end_date = fields.Date(string="End Date", required=True)

    def action_export(self):
        data = {
            'display_accounts': self.display_accounts,
            'note_template': self.note_template.id,
            'end_date': self.end_date,
        }
        return {
           'type': 'ir.actions.report',
           'data': {'model': 'account.account',
                    'options': json.dumps(data,
                                          default=json_default),
                    'output_format': 'xlsx',
                    'report_name': 'report',
                    },
           'report_type': 'xlsx',
       }
