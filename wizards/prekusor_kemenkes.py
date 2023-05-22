from odoo import fields, models, api, _
from odoo.exceptions import UserError

from datetime import datetime as dt

class ReportPrekusorKemenkes(models.TransientModel):
    _name = 'report.prekusor.kemenkes'
    _description = 'Report Prekusor Kemenkes'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    type = fields.Selection([
        ("receipt","Pemasukan"),
        ("do","Pengeluaraan"),
        ("receipt_do", "Pemasukan & Pengeluaran")
    ], string='Type', default="receipt_do")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    product_ids = fields.Many2many("product.product", string="Product")
    golongan_obat = fields.Many2one(comodel_name='jenis.obat', string='Golongan Obat')

    def download_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.prekusor.kemenkes'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_pbf_stock.prekusor_kemenkes').report_action(self, data=datas)

class PrekusorKemenkesReportXlsx(models.AbstractModel):
    _name = 'report.ati_pbf_stock.prekusor_kemenkes_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        formatHeader = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center','bg_color':'#D3D3D3', 'color': 'black', 'bold': True})
        formatTabel = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'color': 'black', 'bold': False})
        formatTabelLeft = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'left', 'color': 'black', 'bold': False})

        formatHeader.set_border(1)
        formatTabel.set_border(1)
        formatTabelLeft.set_border(1)
        formatHeader.set_text_wrap()
        formatTabel.set_text_wrap()
        formatTabelLeft.set_text_wrap()

        sheet = workbook.add_worksheet('Prekusor Kemenkes')

        sheet.set_column(4, 0, 15)
        sheet.set_column(4, 1, 25)
        sheet.set_column(4, 2, 15)
        sheet.set_column(4, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(4, 5, 15)
        sheet.set_column(4, 6, 15)
        sheet.set_column(4, 7, 15)
        sheet.set_column(4, 8, 15)
        sheet.set_column(4, 9, 15)
        sheet.set_column(4, 10, 15)
        sheet.set_column(4, 11, 15)
        sheet.set_column(4, 12, 15)
        sheet.set_column(4, 13, 15)
        sheet.set_column(4, 14, 15)
        sheet.set_column(4, 15, 15)

        sheet.merge_range(2,0,4,0, 'Kode Obat', formatHeader)
        sheet.merge_range(2,1,4,1, 'Nama Obat', formatHeader)

        sheet.merge_range(2,2,2,8, 'Pemasukan', formatHeader)
        sheet.merge_range(3,2,4,2, 'Tanggal Transaksi', formatHeader)
        sheet.merge_range(3,3,4,3, 'Dokumen Penerima', formatHeader)
        sheet.merge_range(3,4,4,4, 'Kode Industri', formatHeader)
        sheet.merge_range(3,5,4,5, 'Kode PBF', formatHeader)
        sheet.merge_range(3,6,4,6, 'Jumlah Masuk', formatHeader)
        sheet.merge_range(3,7,4,7, 'Kode Batch', formatHeader)
        sheet.merge_range(3,8,4,8, 'Expired Date', formatHeader)

        sheet.merge_range(2,9,2,15, 'Pengeluaran', formatHeader)
        sheet.merge_range(3,9,4,9, 'Tanggal Transaksi', formatHeader)
        sheet.merge_range(3,10,4,10, 'Nomor Faktur', formatHeader)
        sheet.merge_range(3,11,4,11, 'Kode Batch', formatHeader)
        sheet.merge_range(3,12,3,14, 'Sarana', formatHeader)
        sheet.write(4, 12, 'Jumlah', formatHeader)
        sheet.write(4, 13, 'Kode Sarana', formatHeader)
        sheet.write(4, 14, 'Jumlah', formatHeader)
        sheet.merge_range(3,15,4,15, 'HJD (BOX)', formatHeader)

        datas = data.get('form', {})
        if datas:
            warehouse = datas.get('warehouse_id', False)
            location_ids = []
            if warehouse:
                warehouse_id = self.env['stock.warehouse'].sudo().browse(warehouse)
                # location_ids = self.env['stock.location'].sudo().search([('id', '=', warehouse_id.lot_stock_id.id)])
                # location_ids = self.env['stock.location'].sudo().search([('warehouse_id', '=', warehouse), ('usage', '=', 'internal')])
                location = self.env['stock.location'].sudo().browse(warehouse_id.lot_stock_id.id)
                product_move = self.env['stock.move.line'].sudo().search([
                    '|',
                    ('location_id', '=', location.id),
                    ('location_dest_id', '=', location.id),
                    ('date', '>=', datas.get('date_from')),
                    ('date', '<=', datas.get('date_to')),
                    ('state', '=', 'done'),
                ], order='date asc')

                ## PRODUCT IDS ##
                if datas.get('product_ids'):
                    products = tuple(datas.get('product_ids'))
                    if products:
                        product_move = self.env['stock.move.line'].sudo().search([
                            '|',
                            ('location_id', '=', location.id),
                            ('location_dest_id', '=', location.id),
                            ('date', '>=', datas.get('date_from')),
                            ('date', '<=', datas.get('date_to')),
                            ('state', '=', 'done'),
                            ('product_id', 'in', products)
                        ], order='date asc')

                row = 5
                for move in product_move:
                    # print("golongan", datas.get('golongan_obat'), move.product_id.jenis_obat)
                    if not datas.get('golongan_obat'):
                        if move.picking_id and move.picking_id.purchase_id and location.id == move.location_dest_id.id:
                            sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
                            sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
                            ''' Pemasukan '''
                            date_done = move.picking_id.date_done.strftime('%Y-%m-%d') if move.picking_id.date_done else ''
                            sheet.write(row, 2, date_done, formatTabel)
                            sheet.write(row, 3, move.origin or '', formatTabel)
                            sheet.write(row, 4, move.product_id.industry_code or '', formatTabel)
                            sheet.write(row, 5, move.product_id.sku or '', formatTabel)
                            sheet.write(row, 6, move.qty_done or '', formatTabel)
                            sheet.write(row, 7, move.lot_id.name or '', formatTabel)
                            expiration_date = move.expiration_date.strftime('%Y-%m-%d') if move.expiration_date else ''
                            sheet.write(row, 8, expiration_date, formatTabel)
                            ''' Pengeluaran '''
                            sheet.write(row, 9, '', formatTabel)
                            sheet.write(row, 10, '', formatTabel)
                            sheet.write(row, 11, '', formatTabel)
                            sheet.write(row, 12, '', formatTabel)
                            sheet.write(row, 13, '', formatTabel)
                            sheet.write(row, 14, '', formatTabel)
                            sheet.write(row, 15, '', formatTabel)
                            row += 1

                        elif move.picking_id and move.picking_id.sale_id and location.id == move.location_id.id:
                            sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
                            sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
                            ''' Pemasukan '''
                            sheet.write(row, 2, '', formatTabel)
                            sheet.write(row, 3, '', formatTabel)
                            sheet.write(row, 4, '', formatTabel)
                            sheet.write(row, 5, '', formatTabel)
                            sheet.write(row, 6, '', formatTabel)
                            sheet.write(row, 7, '', formatTabel)
                            sheet.write(row, 8, '', formatTabel)
                            ''' Pengeluaran '''
                            date = move.date.strftime('%Y-%m-%d') if move.date else ''
                            sheet.write(row, 9, date, formatTabel)
                            sheet.write(row, 10, move.origin or '', formatTabel)
                            sheet.write(row, 11, move.lot_id.name or '', formatTabel)
                            sheet.write(row, 12, move.qty_done or '', formatTabel)
                            sheet.write(row, 13, move.picking_id.partner_id.no_izin_sarana or '', formatTabel)
                            sheet.write(row, 14, '', formatTabel)
                            sheet.write(row, 15, '', formatTabel)
                            row += 1
                    elif datas.get('golongan_obat'):
                        if move.product_id.jenis_obat.id == datas.get('golongan_obat'):
                            if move.picking_id and move.picking_id.purchase_id and location.id == move.location_dest_id.id:
                                sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
                                sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
                                ''' Pemasukan '''
                                date_done = move.picking_id.date_done.strftime('%Y-%m-%d') if move.picking_id.date_done else ''
                                sheet.write(row, 2, date_done, formatTabel)
                                sheet.write(row, 3, move.origin or '', formatTabel)
                                sheet.write(row, 4, move.product_id.industry_code or '', formatTabel)
                                sheet.write(row, 5, move.product_id.sku or '', formatTabel)
                                sheet.write(row, 6, move.qty_done or '', formatTabel)
                                sheet.write(row, 7, move.lot_id.name or '', formatTabel)
                                expiration_date = move.expiration_date.strftime('%Y-%m-%d') if move.expiration_date else ''
                                sheet.write(row, 8, expiration_date, formatTabel)
                                ''' Pengeluaran '''
                                sheet.write(row, 9, '', formatTabel)
                                sheet.write(row, 10, '', formatTabel)
                                sheet.write(row, 11, '', formatTabel)
                                sheet.write(row, 12, '', formatTabel)
                                sheet.write(row, 13, '', formatTabel)
                                sheet.write(row, 14, '', formatTabel)
                                sheet.write(row, 15, '', formatTabel)
                                row += 1

                            elif move.picking_id and move.picking_id.sale_id and location.id == move.location_id.id:
                                sheet.write(row, 0, move.product_id.nie or '', formatTabelLeft)
                                sheet.write(row, 1, move.product_id.name or '', formatTabelLeft)
                                ''' Pemasukan '''
                                sheet.write(row, 2, '', formatTabel)
                                sheet.write(row, 3, '', formatTabel)
                                sheet.write(row, 4, '', formatTabel)
                                sheet.write(row, 5, '', formatTabel)
                                sheet.write(row, 6, '', formatTabel)
                                sheet.write(row, 7, '', formatTabel)
                                sheet.write(row, 8, '', formatTabel)
                                ''' Pengeluaran '''
                                date = move.date.strftime('%Y-%m-%d') if move.date else ''
                                sheet.write(row, 9, date, formatTabel)
                                sheet.write(row, 10, move.origin or '', formatTabel)
                                sheet.write(row, 11, move.lot_id.name or '', formatTabel)
                                sheet.write(row, 12, move.qty_done or '', formatTabel)
                                sheet.write(row, 13, move.picking_id.partner_id.no_izin_sarana or '', formatTabel)
                                sheet.write(row, 14, '', formatTabel)
                                sheet.write(row, 15, '', formatTabel)
                                row += 1


                

