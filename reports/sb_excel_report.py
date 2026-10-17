import io, xlsxwriter
from odoo import models
from datetime import datetime, timedelta
from collections import defaultdict

class AccountAccount(models.Model):
    _inherit = 'account.account'

    def populate_account_data(self, ytd_info, accounts_data, notes_data, account_dict, note_dict,period):
        if period == "prev_ytd":
            for entry in ytd_info:
                account_id = entry['account_id'][0] if entry['account_id'] else None
                if account_id:
                    note_name = note_dict[account_id] if account_id in note_dict else ''
                    debit = entry.get('debit', 0.0)
                    credit = -1 * entry.get('credit', 0.0)
                    accounts_data[account_id] = {
                        'prev_debit': debit,
                        'prev_credit': entry.get('credit', 0.0),
                        'movement_debit': 0.0,
                        'movement_credit': 0.0,
                        'current_debit': 0.0,
                        'current_credit': 0.0,
                        'account_name': account_dict[account_id]['name'],
                        'account_code':account_dict[account_id]['code'],
                        'note_name': note_name
                    }
                    if note_name and note_name in notes_data:
                        notes_data[note_name]['prev_ytd'] += debit+credit
        elif period == "curr_ytd":
            for entry in ytd_info:
                account_id = entry['account_id'][0] if entry['account_id'] else None
                if account_id:
                    note_name = note_dict[account_id] if account_id in note_dict else ''
                    debit = entry.get('debit', 0.0)
                    credit = -1 * entry.get('credit', 0.0)

                    if account_id not in accounts_data:
                        accounts_data[account_id] = {
                            'prev_debit': 0.0,
                            'prev_credit': 0.0,
                            'movement_debit': 0.0,
                            'movement_credit': 0.0,
                            'current_debit': 0.0,
                            'current_credit': 0.0,
                            'account_name': account_dict[account_id]['name'],
                            'account_code':account_dict[account_id]['code'],
                            'note_name': note_dict[account_id] if account_id in note_dict else ''
                        }

                    accounts_data[account_id]['current_debit'] = entry.get('debit', 0.0)
                    accounts_data[account_id]['current_credit'] = entry.get('credit', 0.0)
                    accounts_data[account_id]['movement_debit'] = accounts_data[account_id]['current_debit'] - accounts_data[account_id]['prev_debit']
                    accounts_data[account_id]['movement_credit'] = accounts_data[account_id]['current_credit'] - accounts_data[account_id]['prev_credit']
                    
                    if note_name and note_name in notes_data:
                        notes_data[note_name]['curr_ytd'] += debit+credit
        
        elif period == "curr_month":
            for entry in ytd_info:
                account_id = entry['account_id'][0] if entry['account_id'] else None
                if account_id:
                    note_name = note_dict[account_id] if account_id in note_dict else ''
                    debit = entry.get('debit', 0.0)
                    credit = -1 * entry.get('credit', 0.0)
                    if note_name and note_name in notes_data:
                        notes_data[note_name]['curr_month'] += debit+credit
            

        elif period == "prev_month":
            for entry in ytd_info:
                account_id = entry['account_id'][0] if entry['account_id'] else None
                if account_id:
                    note_name = note_dict[account_id] if account_id in note_dict else ''
                    debit = entry.get('debit', 0.0)
                    credit = -1 * entry.get('credit', 0.0)
                    if note_name and note_name in notes_data:
                        notes_data[note_name]['prev_month'] += debit+credit

        else:
            pass

        return (accounts_data,notes_data)



    def _build_bs_note_hierarchy(self, note_template):
        bs_notes = self.env['sb.bs.report'].search([('note_template','=',note_template)])
        bs_hierarchy = {}
        
        # Process BS notes into their own hierarchy  
        for note in bs_notes:
            bs_hierarchy[note.id] = {
                'model': 'bs', 
                'name': note.note_name,
                'type': note.note_type,
                'children': [],
                'report_to': note.report_to.id if note.report_to else None
            }
        # Build BS parent-child relationships (only within BS hierarchy)
        for note_id, note_data in bs_hierarchy.items():
            if note_data['report_to'] and note_data['report_to'] in bs_hierarchy:
                bs_hierarchy[note_data['report_to']]['children'].append(note_id)
        return bs_hierarchy
    

    def _build_pl_note_hierarchy(self, note_template):
        """Builds separate hierarchy trees for PL and BS notes"""
        pl_notes = self.env['sb.pl.report'].search([('note_template','=',note_template)])
        pl_hierarchy = {}
        
        # Process PL notes into their own hierarchy
        for note in pl_notes:
            pl_hierarchy[note.id] = {
                'model': 'pl',
                'name': note.note_name,
                'type': note.note_type,
                'children': [],
                'report_to': note.report_to.id if note.report_to else None
            }
        
        # Build PL parent-child relationships (only within PL hierarchy)
        for note_id, note_data in pl_hierarchy.items():
            if note_data['report_to'] and note_data['report_to'] in pl_hierarchy:
                pl_hierarchy[note_data['report_to']]['children'].append(note_id)
        return pl_hierarchy
    
    def _calculate_note_amounts(self, note_id, hierarchy, pl_data, bs_data):
        """Recursively calculates amounts for a note and its children"""
        note = hierarchy[note_id]
        amounts = {
            'curr_ytd': 0.0,
            'prev_ytd': 0.0,
            'curr_month': 0.0,
            'prev_month': 0.0
        }
        
        # Base case: detail note
        if note['type'] == 'detail':
            data_source = pl_data if note['model'] == 'pl' else bs_data

            if note['name'] in data_source:
                return {
                    'curr_ytd': data_source[note['name']]['curr_ytd'],
                    'prev_ytd': data_source[note['name']]['prev_ytd'],
                    'curr_month': data_source[note['name']]['curr_month'],
                    'prev_month': data_source[note['name']]['prev_month']
                }
            return amounts
        
        # Recursive case: total or header note
        for child_id in note['children']:
            child_amounts = self._calculate_note_amounts(child_id, hierarchy, pl_data, bs_data)
            for key in amounts:
                amounts[key] += child_amounts[key]
        
        return amounts
    
    def get_account_ids(self, current_ytd, all=False):
        if all:
            account_ids = self.env['account.account'].search([]).ids
        else:
            account_ids = [entry['account_id'][0] for entry in current_ytd if entry['account_id']]
        return account_ids

    def get_note_dict(self, account_ids, note_template):
        #{acc_id: note_name}

        note_lines = self.env['sb.account.note.line'].search([
            ('account_id', 'in', account_ids),
            ('note_template_id', '=', note_template)
        ])
        note_dict = {line.account_id.id: line.note_id.name for line in note_lines}
        return note_dict
    
    def get_account_dict(self, account_ids, all=False):
        #{acc_id: {name:acc_name, code:acc_code}}
        if all:
            accounts_info = self.env['account.account'].search_read(
                [(1, '=', 1)],
                ['id', 'name', 'code']
            )
        else:
            accounts_info = self.env['account.account'].search_read(
                [('id', 'in', account_ids)],
                ['id', 'name', 'code']
            )
        account_dict = {acc['id']: {'name': acc['name'], 'code': acc['code']} for acc in accounts_info}  
        return account_dict     

    def get_pl_bs_note_dict(self, note_template):
        #{note_name: {id:note_id, prev_ytd:0, curr_ytd:0, curr_month:0, prev_month:0}}
        pl_notes = self.env['sb.pl.report'].search([('note_template','=',note_template),('note_type','=','detail')])
        bs_notes = self.env['sb.bs.report'].search([('note_template','=',note_template),('note_type','=','detail')])
        pl_bs_note_dict = {}
        for note in pl_notes:
            pl_bs_note_dict[note.note_name] = {'id':note.id, 'prev_ytd':0, 'curr_ytd':0, 'curr_month':0, 'prev_month':0}
        
        for note in bs_notes:
            pl_bs_note_dict[note.note_name] = {'id':note.id, 'prev_ytd':0, 'curr_ytd':0, 'curr_month':0, 'prev_month':0}

        return pl_bs_note_dict
    
    def get_account_balances(self, end_date, note_template, all):


        first_day_current_month = end_date.replace(day=1)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        last_month_data = self.env['account.move.line'].read_group(
            [('date', '>=', first_day_prev_month), ('date', '<=', last_day_prev_month), ('move_id.state', '=', 'posted')],
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )
        current_month_data = self.env['account.move.line'].read_group(
            [('date', '>=', first_day_current_month), ('date', '<=', end_date), ('move_id.state', '=', 'posted')],
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )        
        prev_ytd = self.env['account.move.line'].read_group(
            [('date', '<=', last_day_prev_month), ('move_id.state', '=', 'posted')],
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )
        current_ytd = self.env['account.move.line'].read_group(
            [('date', '<=', end_date), ('move_id.state', '=', 'posted')],
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )
        accounts_data = {}
        account_ids = self.get_account_ids(current_ytd, all)
        note_dict = self.get_note_dict(account_ids, note_template)
        account_dict = self.get_account_dict(account_ids, all)
        pl_bs_note_dict = self.get_pl_bs_note_dict(note_template)
        all_data = [prev_ytd, current_ytd, last_month_data, current_month_data]

        self.populate_account_data(all_data[0],accounts_data,pl_bs_note_dict, account_dict, note_dict, period="prev_ytd")
        self.populate_account_data(all_data[1],accounts_data,pl_bs_note_dict, account_dict, note_dict, period="curr_ytd")
        self.populate_account_data(all_data[2],accounts_data,pl_bs_note_dict, account_dict, note_dict, period="prev_month")
        tb_data, pl_bs_data = self.populate_account_data(all_data[3],accounts_data,pl_bs_note_dict, account_dict, note_dict, period="curr_month")
        
        if all:
            for account_id in account_ids:
                if account_id not in tb_data:
                    tb_data[account_id] = {
                        'prev_debit': 0.0, 'prev_credit': 0.0, 'movement_debit': 0.0, 
                        'movement_credit': 0.0, 'current_debit': 0.0, 
                        'current_credit': 0.0, 'account_name': account_dict[account_id]['name'], 
                        'account_code': account_dict[account_id]['code'], 'note_name': note_dict[account_id] if account_id in note_dict else ''}

        
        return (tb_data, pl_bs_data)
    

    def create_trial_bal_sheet(self, formats, end_date,tb_sheet, tb_data):
        last_day_previous_month = end_date.replace(day=1) - timedelta(days=1)

        tb_sheet.set_column('A:A', 15)  # Account ID
        tb_sheet.set_column('B:B', 40)  # Account Name
        tb_sheet.set_column('C:H', 20)  # Debit and Credit
        tb_sheet.set_column('I:I', 30)  # Note

        #headers
        tb_sheet.write('C1', 'ACTUAL', formats['header'])
        tb_sheet.write('C2', 'PREVIOUS YTD', formats['header'])
        tb_sheet.write('C3', last_day_previous_month.strftime('%B %d, %Y'), formats['header'])
        tb_sheet.write('C4', 'DEBIT', formats['header'])
        tb_sheet.write('D4', 'CREDIT', formats['header'])
        tb_sheet.write('E1', 'MOVEMENT', formats['header'])
        tb_sheet.write('E2', '', formats['header'])
        tb_sheet.write('E3', '', formats['header'])
        tb_sheet.write('E4', 'DEBIT', formats['header'])
        tb_sheet.write('F4', 'CREDIT', formats['header'])
        tb_sheet.write('G1', 'ACTUAL', formats['header'])
        tb_sheet.write('G2', 'YTD', formats['header'])
        tb_sheet.write('G3', end_date.strftime('%B %d, %Y'), formats['header'])
        tb_sheet.write('G4', 'DEBIT', formats['header'])
        tb_sheet.write('H4', 'CREDIT', formats['header'])
        tb_sheet.write('I4', 'NOTE', formats['header'])

        row = 5
        for code, values in tb_data.items():
            # Net each period pair: show only the difference in the appropriate column
            for prefix in ('prev_', 'movement_', 'current_'):
                debit = values[prefix + 'debit']
                credit = values[prefix + 'credit']
                net = debit - credit
                if net > 0:
                    values[prefix + 'debit'] = net
                    values[prefix + 'credit'] = 0.0
                else:
                    values[prefix + 'debit'] = 0.0
                    values[prefix + 'credit'] = abs(net)

            tb_sheet.write(row, 0, values['account_code'])
            tb_sheet.write(row, 1, values['account_name'])
            tb_sheet.write(row, 2, values['prev_debit'], formats['number'])
            tb_sheet.write(row, 3, values['prev_credit'], formats['number'])
            tb_sheet.write(row, 4, values['movement_debit'], formats['number'])
            tb_sheet.write(row, 5, values['movement_credit'], formats['number'])
            tb_sheet.write(row, 6, values['current_debit'], formats['number'])
            tb_sheet.write(row, 7, values['current_credit'], formats['number'])
            tb_sheet.write(row, 8, values['note_name'])
            row += 1


    def create_pl_sheet(self, formats, end_date,pl_sheet, pl_data, note_template):
        last_day_previous_month = end_date.replace(day=1) - timedelta(days=1)

        pl_format = self.env['sb.pl.report'].search([('note_template','=',note_template)], order="sequence asc")
        hierarchy = self._build_pl_note_hierarchy(note_template)
        n_t = self.env['sb.note.templates'].search([('id','=',note_template)])
        pl = n_t.pl
        bs = n_t.bs
        pl_to_bs = {}
            
        pl_sheet.set_column('A:A', 30)
        pl_sheet.set_column('B:B', 12)
        pl_sheet.set_column('C:F', 25)

        pl_sheet.write('C1', 'ACTUAL', formats['header'])
        pl_sheet.write('D1', 'ACTUAL', formats['header'])
        pl_sheet.write('E1', 'ACTUAL', formats['header'])
        pl_sheet.write('F1', 'ACTUAL', formats['header'])

        pl_sheet.write('C2', 'YTD', formats['header'])
        pl_sheet.write('D2', 'Previous YTD', formats['header'])
        pl_sheet.write('E2', 'Previous Month', formats['header'])
        pl_sheet.write('F2', 'Current Month', formats['header'])

        pl_sheet.write('C3', end_date.strftime('%B %d, %Y'), formats['header'])
        pl_sheet.write('D3', last_day_previous_month.strftime('%B %d, %Y'), formats['header'])
        pl_sheet.write('E3', last_day_previous_month.strftime('%B %Y'), formats['header'])
        pl_sheet.write('F3', end_date.strftime('%B %Y'), formats['header'])


        row = 4
        for n in pl_format:
            # Get amounts recursively
            amounts = self._calculate_note_amounts(n.id, hierarchy, pl_data, {})
            formatting = formats['number'] if n.note_type == 'detail' else formats['total']

            
            if n.note_type == 'header':
                pl_sheet.write(row, 0, n.note_name, formats['bold'])
            else:
                # Write the amounts
                pl_sheet.write(row, 2, amounts['curr_ytd'], formatting)
                pl_sheet.write(row, 3, amounts['prev_ytd'], formatting)
                pl_sheet.write(row, 4, amounts['prev_month'], formatting)
                pl_sheet.write(row, 5, amounts['curr_month'], formatting)

                # Format based on note type
                if n.note_type == 'total':
                    pl_sheet.write(row, 0, n.note_name, formats['bold'])
                else:
                    pl_sheet.write(row, 0, n.note_name)
                    pl_sheet.write(row, 1, pl_data[n.note_name]['id'] if n.note_name in pl_data else 0)
                
                # Handle PL to BS mapping
                if n.note == pl.note:
                    pl_to_bs[bs.note_name] = {
                        'id': bs.note_id,
                        'curr_ytd': amounts['curr_ytd'],
                        'prev_ytd': amounts['prev_ytd'],
                        'prev_month': amounts['prev_month'],
                        'curr_month': amounts['curr_month']
                    }
            
            row += 1
        return pl_to_bs
    

    def create_bs_sheet(self, formats, end_date, bs_sheet, bs_data, note_template, pl_to_bs):
        last_day_previous_month = end_date.replace(day=1) - timedelta(days=1)
        bs_format = self.env['sb.bs.report'].search([('note_template', '=', note_template)], order="sequence asc")
        bs = self.env['sb.note.templates'].search([('id', '=', note_template)]).bs
        hierarchy = self._build_bs_note_hierarchy(note_template)
        if bs:
            hierarchy[bs.id]['type'] = 'detail'  # Ensure the linked BS note is treated as detail
        pl_to_bs_amount = pl_to_bs.get(bs.note_name, {})
        if pl_to_bs_amount:
            bs_data[bs.note_name] = pl_to_bs_amount

        bs_sheet.set_column('A:A', 30)
        bs_sheet.set_column('B:B', 12)
        bs_sheet.set_column('C:F', 25)

        bs_sheet.write('C1', 'ACTUAL', formats['header'])
        bs_sheet.write('D1', 'ACTUAL', formats['header'])
        bs_sheet.write('E1', 'ACTUAL', formats['header'])
        bs_sheet.write('F1', 'ACTUAL', formats['header'])

        bs_sheet.write('C2', 'YTD', formats['header'])
        bs_sheet.write('D2', 'Previous YTD', formats['header'])
        bs_sheet.write('E2', 'Previous Month', formats['header'])
        bs_sheet.write('F2', 'Current Month', formats['header'])

        bs_sheet.write('C3', end_date.strftime('%B %d, %Y'), formats['header'])
        bs_sheet.write('D3', last_day_previous_month.strftime('%B %d, %Y'), formats['header'])
        bs_sheet.write('E3', last_day_previous_month.strftime('%B %Y'), formats['header'])
        bs_sheet.write('F3', end_date.strftime('%B %Y'), formats['header'])

        row = 4
        for n in bs_format:
            if n.note_type != 'header':
                formatting = formats['number'] if n.note_type == 'detail' else formats['total']
                amounts = self._calculate_note_amounts(n.id, hierarchy, {}, bs_data)
                # Write the amounts
                bs_sheet.write(row, 2, amounts['curr_ytd'], formatting)
                bs_sheet.write(row, 3, amounts['prev_ytd'], formatting)
                bs_sheet.write(row, 4, amounts['prev_month'], formatting)
                bs_sheet.write(row, 5, amounts['curr_month'], formatting)

                # Format based on note type
            if n.note_type == 'header':
                bs_sheet.write(row, 0, n.note_name, formats['bold'])
            elif n.note_type == 'total':
                bs_sheet.write(row, 0, n.note_name, formats['bold'])
            else:
                bs_sheet.write(row, 0, n.note_name)
                bs_sheet.write(row, 1, bs_data[n.note_name]['id'] if n.note_name in bs_data else 0)
            row += 1


    def get_nta_data(self, note_template, end_date):

        accounts = self.env['account.account'].search([
            ('related_notes', '!=', False),
            ('related_notes.note_template_id', '=', note_template)
        ])

        # Get balances for those accounts
        balance_data = self.env['account.move.line'].read_group(
            [
                ('account_id', 'in', accounts.ids),
                ('move_id.state', '=', 'posted'),
                ('date', '<=', end_date)
            ],
            ['account_id', 'debit', 'credit'],
            ['account_id']
        )

        # Convert balance data to a dict for easy lookup
        balances = {
            entry['account_id'][0]: entry['debit'] - entry['credit']
            for entry in balance_data
        }

        # Prepare NTA data structure
        nta_data = defaultdict(lambda: {'id': 0, 'total': 0.0, 'data': []})

        # Get all detail-type notes
        notes = self.env['sb.account.notes'].search([('note_type', '=', 'detail')])

        for note in notes:
            note_lines = self.env['sb.account.note.line'].search([
                ('note_template_id', '=', note_template),
                ('note_id', '=', note.id)
            ])
            
            account_ids = list({line.account_id.id for line in note_lines if line.account_id})
            total = 0.0
            data = []

            for account in self.env['account.account'].browse(account_ids):
                bal = balances.get(account.id, 0.0)
                total += bal
                data.append({'account_name': account.name, 'balance': bal})

            if data:
                nta_data[note.name] = {
                    'id': note.note_id,
                    'total': total,
                    'data': data
                }
        return nta_data
            




    def create_nta_sheet(self, formats, nta_data, nta_sheet):
        nta_sheet.set_column('B:B', 40)  # Account ID
        nta_sheet.set_column('D:E', 20)  # Account Name

        #headers
        nta_sheet.write('D1', 'Balances', formats['header'])
        nta_sheet.write('E1', 'Total', formats['header'])

        row = 3
        for key, values in nta_data.items():
            nta_sheet.write(row, 0, '')
            nta_sheet.write(row, 1, key, formats['header'])
            nta_sheet.write(row, 2, values['id'], formats['header'])
            row+=1
            for rec in values['data']:
                nta_sheet.write(row, 1, rec['account_name'])
                nta_sheet.write(row, 3, rec['balance'], formats['number'])
                row += 1
            nta_sheet.write(row, 4, values['total'], formats['number'])
            row += 2

    def get_xlsx_report(self, data, response):
        end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d").date()
        display_all_accounts = True if data.get('display_accounts') == 'all' else False
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        number_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        total_format = workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'align': 'right', 'top': 1})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        bold_format = workbook.add_format({'bold':True})
        header_format.set_font_size(16)
        sheet_tb = workbook.add_worksheet('Trial Balance')
        sheet_pl = workbook.add_worksheet('Profit and Loss')
        sheet_bs = workbook.add_worksheet('Balance Sheet')
        sheet_nta = workbook.add_worksheet('Notes to Accounts')
        nta_data = self.get_nta_data(data.get('note_template'), end_date)
        tb_data, pl_data = self.get_account_balances(end_date, data.get('note_template'), display_all_accounts)
        formats = {'header':header_format, 'bold':bold_format, 'number':number_format, 'total':total_format}

        self.create_trial_bal_sheet(formats, end_date, sheet_tb, tb_data)
        pl_to_bs_data = self.create_pl_sheet(formats, end_date, sheet_pl, pl_data, data.get('note_template'))
        self.create_bs_sheet(formats, end_date, sheet_bs, pl_data, data.get('note_template'), pl_to_bs_data)
        self.create_nta_sheet(formats, nta_data, sheet_nta)



        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()