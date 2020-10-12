# -*- coding: utf-8 -*-
######################################################################################################
#
#   Odoo, Open Source Management Solution
#   Copyright (C) 2018  Konsaltén Indonesia (Consult10 Indonesia) <www.consult10indonesia.com>
#   @author Deby Wahyu Kurdian <deby.wahyu.kurdian@gmail.com>
#   For more details, check COPYRIGHT and LICENSE files
#
######################################################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class SaleOrder(models.Model):
    _inherit    = ['sale.order']

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.partner_id and res.name:
            if res.name.find('custom_partner') > 0:
                partner_code    = str(res.partner_id.partner_code) if str(res.partner_id.partner_code) != 'False' else "SO"
                new_name        = res.name.replace(res.name[(res.name.find('custom_partner')):(res.name.find('custom_partner'))+14], str(partner_code))
                if res.name:
                    res.name = new_name
        return res

    price_statement_rule    = fields.Char("Peraturan Pemerintah")
    source_warehouse_note   = fields.Text("Asal Barang", default="KCP PT. SINAR JAYA INTI MULYA\nDUSUN VI RT 46 RW 13, BANJARSARI, METRO UTARA, METRO, LAMPUNG")
    picking_location_note   = fields.Text("Lokasi Pemuatan", default="PELABUHAN PANJANG, LAMPUNG")
    delivery_of_goods       = fields.Text("Penyerahan")
    quantity_note           = fields.Text("Catatan Kuantitas", default="BERDASARKAN HASIL SOUNDING PADA TANKI PIHAK PEMBELI")
    quality_ffa             = fields.Char("FFA")
    quality_mni             = fields.Char("M & I")
    quality_iv              = fields.Char("IV (WIJS)")
    quality_claim           = fields.Text("Perhitungan Klaim")
    quality_note            = fields.Text("Catatan Kualitas", default="""FINAL MUTU BERDASARKAN INDEPENDENT SURVEYOR/PT.SUCOFINDO DI PELABUHAN BONGKAR  
""")
    other_claim             = fields.Text("Lain - lain", default="""- Apabila terdapat hal-hal yang tidak dapat diselesaikan secara musyawarah mufakat, maka kedua belah pihak sepakat untuk menyelesaikannya ke Kepaniteraan Pengadilan Negeri Bandar Lampung
- Dokumen Pabean untuk pengeluaran barang akan dikirim terlebih dahulu via email dan untuk dokumen asli akan dibawakan saat kapal tiba""")
    payment_term_note       = fields.Text("Pembayaran", default="""95% TANGGAL -
5% SETELAH FINAL PEMBONGKARAN
""")
    partner_bank_id         = fields.Many2one("res.partner.bank", string="Bank Payment")
    ppn_include             = fields.Boolean(string="Include PPN")
    # sign_city               = fields.Char("Ttd Kota", default=lambda self:self.env.user.company_id.city)
    sign_city               = fields.Char("Ttd Kota")
    sign_seller             = fields.Char("Ttd Penjual", default="ROSDIANA")
    sign_buyer              = fields.Char("Ttd Pembeli", default="PEMBELI")
    sign_seller_position    = fields.Char("Jabatan Penjual")
    sign_buyer_position     = fields.Char("Jabatan Pembeli")
    draft_proforma_invoice_ids = fields.One2many('sale.proforma.invoice', 'sale_id', 'Proforma Invoice')
    proforma_invoice_count = fields.Integer(compute="_compute_proforma_invoice", string='Proforma', copy=False, default=0)

    @api.depends('draft_proforma_invoice_ids')
    def _compute_proforma_invoice(self):
        for order in self:
            order.advance_invoice_count = len(order.draft_proforma_invoice_ids.ids)

    @api.onchange('doc_type_id')
    def onchange_document_type_sale_sjm(self):
        if self.doc_type_id:
            if self.doc_type_id.source_warehouse_note:
                self.source_warehouse_note = self.doc_type_id.source_warehouse_note
            if self.doc_type_id.picking_location_note:
                self.picking_location_note = self.doc_type_id.picking_location_note
            # self.price_statement_rule   = self.doc_type_id.price_statement_rule or False
            # self.delivery_of_goods      = self.doc_type_id.delivery_of_goods or False
            # self.quantity_note          = self.doc_type_id.quantity_note or False
            # self.quality_ffa            = self.doc_type_id.quality_ffa or False
            # self.quality_mni            = self.doc_type_id.quality_mni or False
            # self.quality_iv             = self.doc_type_id.quality_iv or False
            # self.quality_claim          = self.doc_type_id.quality_claim or False
            # self.quality_note           = self.doc_type_id.quality_note or False
            # self.other_claim            = self.doc_type_id.other_claim or False
            # self.payment_term_note      = self.doc_type_id.payment_term_note or False
            # self.partner_bank_id        = self.doc_type_id.partner_bank_id and self.doc_type_id.partner_bank_id.id or False
            # self.ppn_include            = self.doc_type_id.ppn_include or False
            # self.sign_seller            = self.doc_type_id.sign_seller or False
            # self.sign_buyer             = self.doc_type_id.sign_buyer or False

    @api.multi
    def action_view_proforma_invoice(self):
        action = self.env.ref('sjm_sale.action_sale_proforma_invoice')
        result = action.read()[0]
        # override the context to get rid of the default filtering
        result['context'] = {'default_sale_id': self.id}
        # choose the view_mode accordingly
        if len(self.draft_proforma_invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.draft_proforma_invoice_ids.ids) + ")]"
        elif len(self.draft_proforma_invoice_ids) == 1:
            res = self.env.ref('sjm_sale.sale_proforma_invoice_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.draft_proforma_invoice_ids.id
        return result

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.client_order_ref:
                name = "%s / %s" % (record.name, record.client_order_ref)
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('client_order_ref', operator, name)]
        order = self.search(domain + args, limit=limit)
        return order.name_get()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        # if self.product_id.type == 'product':
        #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        #     product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
        #     if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
        #         is_available = self._check_routing()
        #         if not is_available:
        #             warning_mess = {
        #                 'title': _('Not enough inventory!'),
        #                 'message' : _('You plan to sell %s %s but you only have %s %s available!\nThe stock on hand is %s %s.') % \
        #                     (self.product_uom_qty, self.product_uom.name, self.product_id.virtual_available, self.product_id.uom_id.name, self.product_id.qty_available, self.product_id.uom_id.name)
        #             }
        #             return {'warning': warning_mess}
        return {}

class SaleProformaInvoice(models.Model):
    _name = 'sale.proforma.invoice'
    _description = 'Proforma Invoice'

    sale_id = fields.Many2one('sale.order', 'Sale Order')
    name = fields.Char('Number')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    date_invoice = fields.Date('Date')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    note = fields.Text('Notes')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    state = fields.Selection([('draft', 'Draft')], string='Status', default='draft')
    # other info
    sign_seller = fields.Char('Tanda Tangan Oleh')
    sign_job_position = fields.Char('Jabatan')
    sign_place = fields.Char('Tempat')
    sign_date = fields.Date('Tanggal')

    invoice_line_ids = fields.One2many('sale.proforma.invoice.line', 'invoice_id', 'Invoice Lines')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')

    @api.depends('invoice_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for invoice in self:
            amount_untaxed = amount_tax = 0.0
            for line in invoice.invoice_line_ids:
                amount_untaxed += line.price_subtotal
                if invoice.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit
                    taxes = line.tax_id.compute_all(price, currency=line.invoice_id.currency_id, quantity=line.product_uom_qty,
                                                    product=line.product_id, partner=invoice.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            invoice.update({
                'amount_untaxed': invoice.currency_id.round(amount_untaxed),
                'amount_tax': invoice.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    def _prepare_invoice_line_from_so_line(self, line):
        qty = line.product_uom_qty or 0.0
        data = {
            'name': line.order_id.name+': '+line.name,
            'product_uom': line.product_uom.id,
            'product_id': line.product_id.id,
            'price_unit': line.price_unit,
            'product_uom_qty': qty,
            'invoice_line_tax_ids': line.tax_id.ids
        }
        return data

    @api.onchange('sale_id')
    def onchange_sale(self):
        if not self.sale_id:
            return {}
        self.partner_id = self.sale_id.partner_shipping_id.id or self.sale_id.partner_id.id
        self.date_invoice = self.sale_id.date_order
        self.currency_id = self.sale_id.currency_id.id
        self.name = self.sale_id.name
        new_lines = self.env['sale.proforma.invoice.line']
        for line in self.sale_id.order_line:
            data = self._prepare_invoice_line_from_so_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        return {}

    @api.multi
    def invoice_print(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'sale_proforma_invoice',
            'datas': {
                'model': 'sale.order',
                'id': self._context.get('active_ids') and self._context.get('active_ids')[0] or self.id,
                'ids': self._context.get('active_ids') and self._context.get('active_ids') or [],
                'name': self.name or "---",
            },
            'nodestroy': False
        }

class SaleProformaInvoiceLine(models.Model):
    _name = 'sale.proforma.invoice.line'
    _description = 'Proforma Invoice Lines'

    sequence = fields.Integer(string='Sequence', default=10)
    invoice_id = fields.Many2one('sale.proforma.invoice', 'Proforma Invoice')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    name = fields.Text('Description', required=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    product_uom_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    price_unit = fields.Float('Price Unit', digits=dp.get_precision('Product Price'), default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', string='Currency')

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.with_context(round=False).compute_all(price, currency=line.invoice_id.currency_id, quantity=line.product_uom_qty,
                                            product=line.product_id, partner=line.invoice_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.name = self.product_id.name
        else:
            self.name = False