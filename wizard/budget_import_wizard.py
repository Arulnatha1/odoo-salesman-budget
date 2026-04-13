from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class BudgetImportWizard(models.TransientModel):
    """
    Wizard to bulk import monthly budget figures from CSV.
    CSV format: salesman_login, jan, feb, mar, apr, may,
    jun, jul, aug, sep, oct, nov, dec
    """
    _name = 'budget.import.wizard'
    _description = 'Budget CSV Import Wizard'

    year = fields.Integer(
        string='Financial Year',
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    csv_file = fields.Binary(
        string='CSV File',
        attachment=False,
    )
    csv_filename = fields.Char(
        string='Filename',
    )
    template_file = fields.Binary(
        string='Download Template',
        readonly=True,
        attachment=False,
    )
    template_filename = fields.Char(
        string='Template Filename',
        readonly=True,
    )
    result_message = fields.Text(
        string='Import Result',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Ready'),
        ('done', 'Done'),
    ], default='draft')

    def action_download_template(self):
        """
        Generate a CSV template pre-filled with all
        internal users who have the salesman role.
        One row per salesman with zero budget values.
        The sales manager fills in the numbers and
        uploads the same file to import.
        """
        salesmen = self.env['res.users'].search([
            ('share', '=', False),
            ('active', '=', True),
        ], order='name')

        lines = []
        header = (
            'salesman_login,'
            'january,february,march,april,may,june,'
            'july,august,september,october,november,december'
        )
        lines.append(header)

        instruction = (
            '# Instructions: Fill in the monthly GP budget '
            'amounts for each salesman. Do not change the '
            'salesman_login column. Delete this instruction '
            'row before importing. Save as CSV.'
        )
        lines.append(instruction)

        for user in salesmen:
            row = '%s,0,0,0,0,0,0,0,0,0,0,0,0' % user.login
            lines.append(row)

        csv_content = '\n'.join(lines)
        csv_bytes = csv_content.encode('utf-8')
        csv_b64 = base64.b64encode(csv_bytes)

        self.template_file = csv_b64
        self.template_filename = (
            'budget_template_%s.csv' % self.year
        )
        self.state = 'draft'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'budget.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        if not self.csv_file:
            raise UserError(_('Please upload a CSV file.'))

        try:
            csv_data = base64.b64decode(self.csv_file)
            csv_text = csv_data.decode('utf-8')
        except Exception:
            raise UserError(_(
                'Could not read the file. '
                'Please ensure it is a valid UTF-8 CSV file.'
            ))

        lines = csv_text.strip().split('\n')

        data_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith('#'):
                continue
            if stripped.lower().startswith('salesman_login'):
                continue
            data_lines.append(stripped)

        if not data_lines:
            raise UserError(_(
                'No data rows found in the CSV file. '
                'Please check the file format.'
            ))

        created = 0
        updated = 0
        errors = []

        for row_num, row in enumerate(data_lines, start=1):
            cols = [c.strip().strip('"') for c in row.split(',')]
            if len(cols) < 13:
                errors.append(
                    'Row %s: expected 13 columns, got %s — skipped'
                    % (row_num, len(cols))
                )
                continue

            login = cols[0]
            if not login:
                continue

            user = self.env['res.users'].search(
                [('login', '=', login)], limit=1
            )
            if not user:
                errors.append(
                    'Row %s: no user found for login "%s" — skipped'
                    % (row_num, login)
                )
                continue

            budget = self.env['salesman.budget'].search([
                ('salesman_id', '=', user.id),
                ('year', '=', self.year),
                ('company_id', '=', self.env.company.id),
            ], limit=1)

            if not budget:
                budget = self.env['salesman.budget'].create({
                    'salesman_id': user.id,
                    'year': self.year,
                    'company_id': self.env.company.id,
                })
                budget.action_generate_budget_lines()
                created += 1
            else:
                updated += 1

            month_values = []
            for i in range(1, 13):
                try:
                    val = float(
                        cols[i].replace(',', '').replace(' ', '')
                    )
                except (ValueError, IndexError):
                    val = 0.0
                month_values.append(val)

            for line in budget.budget_line_ids.sorted('month'):
                idx = line.month - 1
                if idx < len(month_values):
                    line.budget_amount = month_values[idx]

            if budget.state == 'draft':
                budget.action_activate()

        result_parts = [
            'Import complete for year %s.' % self.year,
            'Budgets created: %s' % created,
            'Budgets updated: %s' % updated,
        ]
        if errors:
            result_parts.append('Errors:')
            result_parts.extend(errors)
        else:
            result_parts.append('No errors.')

        self.result_message = '\n'.join(result_parts)
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'budget.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }