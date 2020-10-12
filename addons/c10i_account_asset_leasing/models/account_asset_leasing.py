# -*- coding: utf-8 -*-

import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, exceptions
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

import odoo.addons.decimal_precision as dp


class AccountAssetLeasing(models.Model):
	_name = 'account.asset.leasing'
	_description = "Account Asset Leasing"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = 'ongoing_date desc, id desc'


	name = fields.Char(
		string='Number',
		default='New',
		readonly=True,
	)
	asset_id = fields.Many2one('account.asset.asset', 'Asset')
	gross_value= fields.Float(string='Gross/Purchase Value', compute='', store=True, digits=dp.get_precision('Account'))
	deposite_value= fields.Float(string='Deposite Value/Uang Muka', compute='', store=True, digits=dp.get_precision('Account'))
	installment_period_numb = fields.Integer(string='Installment Periode Number/Jumlah Cicilan')
	state = fields.Selection(selection=[('draft', 'Draft'),
										('ongoing', 'Ongoing'),
										('closed', 'Closed'),],
							 string='State', readonly=True, default='draft',
							 track_visibility='onchange')
	ongoing_date = fields.Date(string='Ongoing Date', default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
	account_asset_installment_line_ids = fields.One2many(comodel_name='account.asset.installment.line', inverse_name='account_asset_installment_line_id', string='Account Asset Installment Lines', ondelete='cascade')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]},default=lambda self: self.env.user.company_id.currency_id.id)


	@api.multi
	def get_leasing_number(self):
		self.name = self.env['ir.sequence'].next_by_code('account.asset.leasing') or 'New'

	@api.multi
	def get_ongoing(self):
		if len([rec.id for rec in self.account_asset_installment_line_ids]) < 1:
			raise exceptions.ValidationError('Warning, please click Compute Button to avoid Detail Installment Periode Data is empty.')

		self.get_leasing_number()
		return self.write({'state':'ongoing'})

	@api.multi
	def get_closed(self):
		return self.write({'state':'closed'})

	@api.multi
	def unlink(self):
		for leasing in self:
			if leasing.state not in ('draft'):
				raise exceptions.ValidationError('You cannot delete an Leasing which is Ongoing or Closed state.')
		return super(AccountAssetLeasing, self).unlink()

	
	@api.multi
	def compute_installment_amount(self, gross_value, deposite_value, installment_period_numb):
		temp_installment_amount = gross_value - deposite_value
		temp_installment_numb = temp_installment_amount/ installment_period_numb
		return temp_installment_numb


	@api.multi
	def warning_leasing(self):
		# pass
		if self.gross_value == 0 or self.deposite_value == 0 or self.installment_period_numb == 0:
			raise exceptions.ValidationError('Warning, surely not zero value for Gross Value or Deposite Value or Installment Periode Number !')

		if self.gross_value < self.deposite_value:
			raise exceptions.ValidationError('Warning, Purchase Value '+str(self.gross_value) +' must greater than Deposite Value ' +str(self.deposite_value))

		return True

	# show detail installment
	@api.multi
	def compute_installment(self):
		self.warning_leasing()
		installment_amount = self.compute_installment_amount(self.gross_value, self.deposite_value, self.installment_period_numb)
		if self.gross_value > 0 and self.deposite_value > 0 and self.installment_period_numb > 0:
			count = 0
			dt = fields.Datetime.from_string(self.ongoing_date)
			# dt = date_start_dt + relativedelta(months=+1)
			ongoing_date = datetime(dt.year, dt.month, 1)
			# dt = (datetime.strptime(str(self.ongoing_date),'%Y-%m-%d').date() + relativedelta(months=1)).strftime('%Y-%m-%d')
			if len([rec.id for rec in self.account_asset_installment_line_ids]) == 0: 
				for line in range(0,self.installment_period_numb):
					count += 1
					# dt = (datetime.strptime(str(self.ongoing_date),'%Y-%m-%d').date() + relativedelta(months=+count)).strftime('%Y-%m-%d')
					counter_date = (ongoing_date + relativedelta(months=+count)).strftime('%Y-%m-%d')
					vals = {'account_asset_installment_line_id': self.id,'installment_amount':  installment_amount, 'name': self.name, 'installment_date':counter_date}
					temp = self.env['account.asset.installment.line'].create(vals)
			else:
				raise exceptions.ValidationError('Warning, please click Correction Button to make sure the data is empty !')

	# correction
	@api.multi
	def reset_leasing(self, vals):
		self.state = 'draft'
		self.env.cr.execute("""DELETE FROM account_asset_installment_line WHERE account_asset_installment_line_id = '%s'""", (int(self.id),))
		self.env.cr.commit()

	# call ir.cron
	@api.multi
	def _cron_leasing(self):
		# find record account.asset.leasing with state == ongoing
		leasing = self.env['account.asset.leasing'].search([('state','in',['ongoing'])])
		for rec in leasing:
			# get installment by most recent date
			temp_installment_date = [line.installment_date for line in rec.account_asset_installment_line_ids.sorted(key=lambda r: r.installment_date)]
			end_date_line =  temp_installment_date[0] if len(temp_installment_date) > 0 else False
			if end_date_line < fields.Date.today():
				# change state from ongoing state to closed state automate
				return rec.write({'state':'closed'})

		return True