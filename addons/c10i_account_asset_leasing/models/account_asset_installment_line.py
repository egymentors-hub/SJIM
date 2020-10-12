# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

import odoo.addons.decimal_precision as dp


class AccountAssetLeasing(models.Model):
    _name = 'account.asset.installment.line'
    _description = "Account Asset Installment Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'installment_date desc, id desc'


    
    installment_amount= fields.Float(string='Installment Amount', compute='', store=True, digits=dp.get_precision('Account'))
    installment_date = fields.Date(string='Installment Date', readonly=True)
    account_asset_installment_line_id = fields.Many2one('account.asset.leasing', string="Account Asset Leasing")
    name = fields.Char(
        string='Number',
        related = 'account_asset_installment_line_id.name',
        readonly=1,
    )
