from itertools import groupby
from datetime import datetime, timedelta
from collections import namedtuple
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
import time
import odoo.addons.decimal_precision as dp
import socket

from odoo.addons.mail.tests.common import TestMail
from odoo.tools import mute_logger


class WizardGenerateReportPurchaseOrder(models.TransientModel):
	_name = "wizard.generate.report.purchase.order"
	_description = "Wizard generate Report Purchase Order"

	type_report = fields.Selection([
				(1, 'Rekap Pembelian'),
				(2, 'Detail Pembelian Product'),
				(3, 'Rincian Pemenuhan Pembelian Product'),
				], string='Type Report')
	start_date  = fields.Date(string='Start Date')
	end_date  	= fields.Date(string='End Date')
	product_id	= fields.Many2one('product.product', string="Product")


	@api.multi
	def generatereport(self):
		
		data = self.read()[-1]
		if self.type_report == 1:
			name = 'report_generate_rekap_pembelian_xls'
		elif self.type_report == 2:
			name = 'report_generate_detail_pembelian_product_xls'
		else:
			name = 'report_generate_perincian_pemenuhan_pembelian_barang_xls'

		# return {
		#     'type'          : 'ir.actions.report.xml',
		#     'report_name'   : name,
		#     'datas': {
		#             'model': 'wizard.purchase.report',
		#             'id': self._context.get('active_ids') and self._context.get('active_ids')[0] or  self.id,
		#             'ids': self._context.get('active_ids') and self._context.get('active_ids') or[],
		#             'report_type': data['report_type'],
		#             'form': data
		#         },
		#     'nodestroy'     : False
		#     }
		res = self.env['report'].get_action(self, name)
		return res



	def get_report_lines(self):
		lines = []

		POLine = self.env['purchase.order.line'].search([
			('date_order','>=',self.start_date),
			('date_order','<=',self.end_date),
			('product_id', '=', self.product_id.id)
		], order="date_order ASC")

		no = 1
		for x in POLine:

			lines.append({
				'no':no,
				'product':x.name
				})

			no +=1

		return lines



# inherit to document type
class wizard_pending_po(models.TransientModel):
    _inherit           = "wizard.pending.purchase.order"
    _description       = "Pending Purchase Order"


    document_type_ids   = fields.Many2many('res.document.type', string = 'Document Type')


    @api.multi
    def create_report(self):
        data = self.read()[-1]
        print('sjm--->data', data)
        name = 'report_pending_po_sjm'
        if data['report_type'] in ['xls', 'xlsx']:
            name = 'report_pending_po_sjm_xls'
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : name,
            'datas': {
                    'model'         :'wizard.pending.purchase.order',
                    'id'            : self._context.get('active_ids') and self._context.get('active_ids')[0] or  self.id,
                    'ids'           : self._context.get('active_ids') and self._context.get('active_ids') or[],
                    'report_type'   : data['report_type'],
                    'form'          : data
                },
            'nodestroy'     : False
            }

