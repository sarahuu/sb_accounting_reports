from odoo import fields, models


class SBProfitLossReport(models.Model):
    _name = 'sb.pl.report'
    _description = 'Profit and Loss Report Line'
    _order = 'sequence,id'
    _rec_name = "note_name"

    note_template = fields.Many2one('sb.note.templates', 'Note Template')
    note = fields.Many2one('sb.account.notes', 'Account Note')
    note_id = fields.Integer('Note ID', related='note.note_id')
    note_name = fields.Char('Note Name', related='note.name')
    note_type = fields.Selection([('header','Header'),('detail','Detail'),('total','Total')],'Type', related="note.note_type")
    report_to = fields.Many2one('sb.pl.report', 'Report To?', domain="[('note_template', '=', note_template)]")
    calculate = fields.Boolean('Calculate')
    sequence = fields.Integer(string="Sequence")

    _sql_constraints = [
        ('unique_note_per_template', 'UNIQUE(note_template, note)', 'Each Note can only appear once per Note Template.')
    ]


class SBBalanceSheetReport(models.Model):
    _name = 'sb.bs.report'
    _description = 'Balance Sheet Report Line'
    _order = 'sequence,id'
    _rec_name = "note_name"

    note_template = fields.Many2one('sb.note.templates', 'Note Template')
    note = fields.Many2one('sb.account.notes', 'Account Note')
    note_id = fields.Integer('Note ID', related='note.note_id')
    note_name = fields.Char('Note Name', related='note.name')
    note_type = fields.Selection([('header','Header'),('detail','Detail'),('total','Total')],'Type', related="note.note_type")
    report_to = fields.Many2one('sb.bs.report', 'Report To?', domain="[('note_template', '=', note_template)]")
    calculate = fields.Boolean('Calculate')
    sequence = fields.Integer(string="Sequence")

    _sql_constraints = [
        ('unique_note_per_template', 'UNIQUE(note_template, note)', 'Each Note can only appear once per Note Template.')
    ]

