from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SalesmanBudget(models.Model):
    """
    One record per salesman per financial year.
    Holds 12 monthly budget targets and computes
    actuals from posted invoices.
    """
    _name = 'salesman.budget'
    _description = 'Salesman GP Budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, salesman_id'
    _rec_name = 'display_name'

    salesman_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesman',
        required=True,
        tracking=True,
        domain=[('share', '=', False)],
    )
    year = fields.Integer(
        string='Financial Year',
        required=True,
        default=lambda self: fields.Date.today().year,
        tracking=True,
    )
    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    budget_line_ids = fields.One2many(
        comodel_name='salesman.budget.line',
        inverse_name='budget_id',
        string='Monthly Budgets',
    )
    total_budget = fields.Monetary(
        string='Total Year Budget',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_actual = fields.Monetary(
        string='Total Year Actual GP',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_variance = fields.Monetary(
        string='Total Year Variance',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_achievement = fields.Float(
        string='Year Achievement %',
        compute='_compute_totals',
        store=True,
        digits=(10, 1),
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ],
        string='Status',
        default='draft',
        tracking=True,
    )

    @api.depends('salesman_id', 'year')
    def _compute_display_name(self):
        for rec in self:
            if rec.salesman_id and rec.year:
                rec.display_name = '%s — %s' % (
                    rec.salesman_id.name, rec.year
                )
            else:
                rec.display_name = _('New Budget')

    @api.depends(
        'budget_line_ids.budget_amount',
        'budget_line_ids.actual_gp',
    )
    def _compute_totals(self):
        for rec in self:
            total_budget = sum(
                rec.budget_line_ids.mapped('budget_amount')
            )
            total_actual = sum(
                rec.budget_line_ids.mapped('actual_gp')
            )
            rec.total_budget = total_budget
            rec.total_actual = total_actual
            rec.total_variance = total_actual - total_budget
            if total_budget > 0:
                rec.total_achievement = (
                    total_actual / total_budget * 100
                )
            else:
                rec.total_achievement = 0.0

    @api.constrains('salesman_id', 'year', 'company_id')
    def _check_unique(self):
        for rec in self:
            duplicate = self.search([
                ('salesman_id', '=', rec.salesman_id.id),
                ('year', '=', rec.year),
                ('company_id', '=', rec.company_id.id),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise UserError(_(
                    'A budget already exists for %s in %s.',
                    rec.salesman_id.name, rec.year
                ))

    def action_activate(self):
        for rec in self:
            if not rec.budget_line_ids:
                raise UserError(_(
                    'Please add monthly budget lines before activating.'
                ))
            rec.state = 'active'

    def action_close(self):
        for rec in self:
            rec.state = 'closed'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_refresh_actuals(self):
        """
        Manually trigger recompute of actual GP
        for all lines of this budget.
        """
        for rec in self:
            rec.budget_line_ids._compute_actual_gp()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actuals Refreshed'),
                'message': _(
                    'Actual GP figures have been updated '
                    'from posted invoices.'
                ),
                'type': 'success',
            }
        }

    @api.model
    def action_generate_lines(self):
        """Generate 12 monthly budget lines if not present."""
        for rec in self:
            if rec.budget_line_ids:
                continue
            for month in range(1, 13):
                self.env['salesman.budget.line'].create({
                    'budget_id': rec.id,
                    'month': month,
                    'year': rec.year,
                    'budget_amount': 0.0,
                })

    def action_generate_budget_lines(self):
        """Button to generate 12 monthly lines."""
        for rec in self:
            if rec.budget_line_ids:
                raise UserError(_(
                    'Budget lines already exist. '
                    'Delete them first to regenerate.'
                ))
            for month in range(1, 13):
                self.env['salesman.budget.line'].create({
                    'budget_id': rec.id,
                    'month': month,
                    'year': rec.year,
                    'budget_amount': 0.0,
                })