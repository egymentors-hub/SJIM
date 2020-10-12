# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class AdjustmentsInventory(models.Model):
	_inherit = "stock.inventory"
	_description = "Inventory"


	account_id = fields.Many2one('account.account', string='Adjustments Account', ondelete='restrict')
	adjustment_date = fields.Datetime(
		'Inventory Adjustments Date',
		help="The date that will be used for the stock level check of the products and the validation of the stock move related to this inventory.")
	adjustments_option = fields.Boolean(string='Not Default?', default=False)

	@api.multi
	def action_start(self):
		for inventory in self:
			vals = {'state': 'confirm', 'date': fields.Datetime.now() if not self.adjustments_option else self.adjustment_date}
			if (inventory.filter != 'partial') and not inventory.line_ids:
				if not inventory.adjustments_option:
					vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
				else:
					vals.update({'line_ids': [(0, 0, line_values) for line_values in inventory._get_inventory_lines_values()]})
					
			inventory.write(vals)
		# Attention: this is not default odoo , modify for dynamic inventory adjustments by adjustment_date
		# do repetitions to fill theoretical_qty field in model :  stock.inventory.line
		# this looping is force to do because inventory.write(vals) function result still: theoretical_qty = 0. maybe _compute_theoretical_qty define its.
		if self.adjustments_option:
			temp = inventory._get_inventory_lines_values()
			self._compute_qty_forced(temp)
		
		return True
	prepare_inventory = action_start


	@api.multi
	def _compute_qty_forced(self, temp):
		for rec in self:
			if rec.line_ids:
				for lines in rec.line_ids:
					for line in temp:
						if lines.product_id.id == line["product_id"] and lines.location_id.id == line["location_id"] and lines.product_uom_id.id == line["product_uom_id"]:
							lines["theoretical_qty"] = line["theoretical_qty"]

		return True


	@api.multi
	def _get_inventory_lines_values(self):
		# TDE CLEANME: is sql really necessary ? I don't think so
		locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
		domain = ' location_id in %s'
		
		domain_adjustments = ' location_dest_id in %s'
		args = (tuple(locations.ids),)

		# add filter by adjustment date
		date = str(self.adjustment_date)

		vals = []
		Product = self.env['product.product']
		# Empty recordset of products available in stock_quants
		quant_products = self.env['product.product']
		# Empty recordset of products to filter
		products_to_filter = self.env['product.product']

		# case 0: Filter on company
		if self.company_id:
			domain += ' AND company_id = %s'
			args += (self.company_id.id,)

			domain_adjustments += ' AND company_id = %s'
		
		#case 1: Filter on One owner only or One product for a specific owner
		if self.partner_id:
			domain += ' AND owner_id = %s'
			args += (self.partner_id.id,)

			domain_adjustments += ' AND owner_id = %s'
		#case 2: Filter on One Lot/Serial Number
		if self.lot_id:
			domain += ' AND lot_id = %s'
			args += (self.lot_id.id,)

			domain_adjustments += ' AND lot_id = %s'
		#case 3: Filter on One product
		if self.product_id:
			domain += ' AND product_id = %s'
			args += (self.product_id.id,)
			products_to_filter |= self.product_id

			domain_adjustments += ' AND product_id = %s'
		#case 4: Filter on A Pack
		if self.package_id:
			domain += ' AND package_id = %s'
			args += (self.package_id.id,)

			domain_adjustments += ' AND package_id = %s'
		#case 5: Filter on One product category + Exahausted Products
		if self.category_id:
			categ_products = Product.search([('categ_id', '=', self.category_id.id)])
			domain += ' AND product_id = ANY (%s)'
			args += (categ_products.ids,)
			products_to_filter |= categ_products

			domain_adjustments += ' AND product_id = ANY (%s)'
		# filter by adjustment_date
		if self.adjustments_option:
			domain += ' AND date < %s'
			args += (str(self.adjustment_date),)
			domain_adjustments += ' AND date < %s'

		
		if not self.adjustments_option: 
			self.env.cr.execute("""SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
				FROM stock_quant
				WHERE %s
				GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)
		else:
			temp_args = args+args
			self.env.cr.execute("""SELECT product_id, sum(product_qty) as product_qty, location_id, company_id, lot_id as prod_lot_id, product_packaging as package_id, partner_id from 
					(
					SELECT product_id, sum(product_uom_qty) as product_qty, location_dest_id as location_id, company_id, restrict_lot_id as lot_id, product_packaging, partner_id 
					FROM stock_move
					WHERE %s
					GROUP BY product_id, location_dest_id, company_id, restrict_lot_id, product_packaging, partner_id
					UNION ALL
					SELECT product_id, sum(-product_uom_qty) as product_qty, location_id as location_id, company_id,  restrict_lot_id as lot_id, product_packaging, partner_id
					FROM stock_move
					WHERE %s
					GROUP BY product_id, location_id, company_id, restrict_lot_id, product_packaging, partner_id
					) 
					as stock_move
					GROUP BY product_id, location_id, company_id, lot_id, product_packaging, partner_id"""% (domain_adjustments, domain), temp_args)

		for product_data in self.env.cr.dictfetchall():
			# replace the None the dictionary by False, because falsy values are tested later on
			for void_field in [item[0] for item in product_data.items() if item[1] is None]:
				product_data[void_field] = False
			product_data['theoretical_qty'] = product_data['product_qty']
			# add account number
			product_data['account_details_id'] = self.account_id.id or False
			# 
			if product_data['product_id']:
				product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
				quant_products |= Product.browse(product_data['product_id'])
			vals.append(product_data)
		if self.exhausted:
			exhausted_vals = self._get_exhausted_inventory_line(products_to_filter, quant_products)
			vals.extend(exhausted_vals)
	
		return vals


class InventoryDetailsAccount(models.Model):
	_inherit = 'stock.inventory.line'

	account_details_id = fields.Many2one('account.account', string='Inventory Details Account', ondelete='restrict')
	theoretical_qty = fields.Float(
		'Theoretical Quantity', compute='_compute_theoretical_qty',
		digits=dp.get_precision('Product Unit of Measure'), readonly=False, store=True)

	@api.one
	@api.depends('location_id', 'product_id', 'package_id', 'product_uom_id', 'company_id', 'prod_lot_id', 'partner_id')
	def _compute_theoretical_qty(self):
		if not self.inventory_id.adjustments_option: # add an expression so that below expression is not excecute  (not default odoo's bussiness) 
			# below statement is odoo default
			if not self.product_id:
				self.theoretical_qty = 0
				return
			theoretical_qty = sum([x.qty for x in self._get_quants()])
			if theoretical_qty and self.product_uom_id and self.product_id.uom_id != self.product_uom_id:
				theoretical_qty = self.product_id.uom_id._compute_quantity(theoretical_qty, self.product_uom_id)
			self.theoretical_qty = theoretical_qty
		
		