from odoo import fields, models


class SBAccountNotes(models.Model):
    _name = 'sb.account.notes'
    _description = 'Account Note'
    _rec_name = 'name'

    note_id = fields.Integer('Note ID')
    name = fields.Char('Name')
    note_type = fields.Selection([('header','Header'),('detail','Detail'),('total','Total')],'Type')

    _sql_constraints = [
        ('unique_note_id', 'UNIQUE(note_id)', 'Note ID must be unique.'),
        ('unique_note_name', 'UNIQUE(name)', 'Note Name must be unique.')
    ]
    


class SBNoteTemplates(models.Model):
    _name = 'sb.note.templates'
    _description = 'Note Template'
    _rec_name = 'name'

    name = fields.Char('Name')
    pl_report = fields.One2many('sb.pl.report', 'note_template', 'PL Report')
    bs_report = fields.One2many('sb.bs.report', 'note_template', 'BS Report')
    pl = fields.Many2one('sb.pl.report', string='PL record', domain=[('note.note_type', '!=', 'header')])
    bs = fields.Many2one('sb.bs.report', string='BS record', domain=[('note.note_type', '!=', 'header')])

    _sql_constraints = [
        ('unique_template_name', 'UNIQUE(name)', 'Template Name must be unique.')
    ]

