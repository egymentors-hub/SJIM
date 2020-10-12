from odoo.addons.jasper_reports import JasperDataParser
from odoo.addons.jasper_reports import jasper_report

class jasper_report_stock_picking(JasperDataParser.JasperDataParser):
    def __init__(self, cr, uid, ids, data, context):
        super(jasper_report_stock_picking, self).__init__(cr, uid, ids, data, context)

    def generate_data_source(self, cr, uid, ids, data, context):
        return 'parameters'

    def generate_parameters(self, cr, uid, ids, data, context):
        data['form'].update({'company_name': 'PT. SINAR JAYA INTI MULYA'})
        data['form'].update({'location_id': data['form']['location_id'][0]})
        return data['form']

    def generate_properties(self, cr, uid, ids, data, context):
        return {}

    def generate_output(self,cr, uid, ids, data, context):
        return data['report_type']
    
    def generate_records(self, cr, uid, ids, data, context):
        return {}

jasper_report.ReportJasper('report.report_picking_skb', 'wizard.report.picking.skb', parser=jasper_report_stock_picking,)
jasper_report.ReportJasper('report.report_picking_skb_xlsx', 'wizard.report.picking.skb', parser=jasper_report_stock_picking,)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
