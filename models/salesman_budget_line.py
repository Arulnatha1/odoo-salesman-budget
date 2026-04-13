from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March',
    4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September',
    10: 'October', 11: 'November', 12: 'December',
}


class SalesmanBudgetLine(models.Model):
    """
    One record per salesman per month.
    Holds the budget amount and computes actual GP
    from posted invoices for that salesman and month.
    """
    _name = 'salesman.budget.line'
    _description = 'Salesman Budget Line'
    _order = 'year, month'
    _rec_name = 'month_name'

    budget_id = fields.Many2one(
        comodel_name='salesman.budget',
        string='Budget',
        required=True,
        ondelete='cascade',
        index=True,
    )
    salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        related='budget_id.salesman_id',
        store=True,
        readonly=True,
    )
    year = fields.Integer(
        string='Year',
        required=True,
    )
    month = fields.Integer(
        string='Month',
        required=True,
    )
    month_name = fields.Char(
        string='Month',
        compute='_compute_month_name',
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='budget_id.currency_id',
        readonly=True,
    )
    budget_amount = fields.Monetary(
        string='GP Budget',
        currency_field='currency_id',
        default=0.0,
    )
    actual_gp = fields.Monetary(
        string='Actual GP',
        currency_field='currency_id',
        compute='_compute_actual_gp',
        store=True,
    )
    variance = fields.Monetary(
        string='Variance',
        currency_field='currency_id',
        compute='_compute_variance',
        store=True,
    )
    achievement_percent = fields.Float(
        string='Achievement %',
        compute='_compute_variance',
        store=True,
        digits=(10, 1),
    )
    traffic_light = fields.Selection([
        ('green', 'On Track'),
        ('amber', 'At Risk'),
        ('red', 'Behind'),
        ('grey', 'No Budget'),
    ],
        string='Status',
        compute='_compute_variance',
        store=True,
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_actual_gp',
        store=True,
    )

    @api.depends('month')
    def _compute_month_name(self):
        for line in self:
            line.month_name = MONTH_NAMES.get(line.month, '')

    @api.depends(
        'budget_id.salesman_id',
        'year',
        'month',
    )
    def _compute_actual_gp(self):
        """
        Compute actual gross profit from posted invoices
        for this salesman and month.

        GP per line = (price_unit * quantity) - (cost * quantity)
        Includes posted customer invoices.
        Subtracts posted credit notes (out_refund).
        Excludes cancelled and draft moves.
        """
        for line in self:
            if not line.salesman_id or not line.year or not line.month:
                line.actual_gp = 0.0
                line.invoice_count = 0
                continue

            date_from = '%s-%02d-01' % (line.year, line.month)
            if line.month == 12:
                date_to = '%s-12-31' % line.year
            else:
                date_to = '%s-%02d-01' % (
                    line.year,
                    line.month + 1
                )

            invoices = self.env['account.move'].search([
                ('move_type', 'in',
                 ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('invoice_user_id', '=',
                 line.salesman_id.id),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<', date_to),
                ('company_id', '=',
                 line.budget_id.company_id.id),
            ])

            total_gp = 0.0
            for invoice in invoices:
                sign = (
                    -1 if invoice.move_type == 'out_refund'
                    else 1
                )
                for inv_line in invoice.invoice_line_ids:
                    if inv_line.display_type in (
                        'line_section', 'line_note'
                    ):
                        continue
                    revenue = inv_line.price_subtotal
                    cost = (
                        inv_line.product_id.standard_price
                        * inv_line.quantity
                        if inv_line.product_id else 0.0
                    )
                    gp = revenue - cost
                    total_gp += sign * gp

            line.actual_gp = total_gp
            line.invoice_count = len(invoices)

    @api.depends('budget_amount', 'actual_gp')
    def _compute_variance(self):
        for line in self:
            line.variance = line.actual_gp - line.budget_amount
            if line.budget_amount > 0:
                pct = line.actual_gp / line.budget_amount * 100
                line.achievement_percent = pct
                if pct >= 80:
                    line.traffic_light = 'green'
                elif pct >= 50:
                    line.traffic_light = 'amber'
                else:
                    line.traffic_light = 'red'
            else:
                line.achievement_percent = 0.0
                line.traffic_light = 'grey'