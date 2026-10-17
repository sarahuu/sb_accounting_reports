from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    related_notes = fields.One2many('sb.account.note.line', 'account_id', string='Related Notes')

class SBAccountNoteLine(models.Model):
    _name = 'sb.account.note.line'
    _description = 'Account Related Notes'

    account_id = fields.Many2one('account.account', string='Account')
    note_id = fields.Many2one('sb.account.notes', string='Note', required=True, domain=[('note_type', '=', 'detail')])
    note_template_id = fields.Many2one('sb.note.templates', string='Note Template', required=True)

    _sql_constraints = [
        ('unique_account_note_template', 'UNIQUE(account_id, note_template_id)', 'This combination of Account and Template already exists.'),
    ]

