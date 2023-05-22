from odoo import models, fields, _, api, exceptions
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError, Warning, RedirectWarning



# batch_on_location_id = None

class StockMoveLineIb(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Product Moves (Stock Move Line)'


    # @api.constrains('product_uom_qty')
    # def _check_reserved_done_quantity(self):
    #     for move_line in self:
    #         print("xxxxxxxx", float_is_zero(move_line.product_uom_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')))
    #         if move_line.state == 'done' and not float_is_zero(move_line.product_uom_qty, precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure')):
    #             raise ValidationError(_('A done move line should never have a reserved quantity.'))

    @api.depends('picking_id.picking_type_id.is_receipt')
    def _dynamic_domain_of_product(self):
        if 'params' in self._context:
            if self._context['params']['model'] == 'stock.picking':
                if 'id' in self._context['params']:
                    sml = self.search([('picking_id', '=', self._context['params']['id'])])
                    for sml_ in sml:
                        for picking_id in sml_.picking_id:
                            for picking_type_id in picking_id.picking_type_id:
                                if not picking_type_id.is_receipt:
                                    return "[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', '=', product_on_location_id)]"
                                elif picking_type_id.is_receipt:
                                    return "[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"

    @api.depends('picking_id.picking_type_id.is_receipt')
    def _dynamic_domain_of_lot_id(self):
        if 'params' in self._context:
            if self._context['params']['model'] == 'stock.picking':
                if 'id' in self._context['params']:
                    sm = self.search([('picking_id', '=', self._context['params']['id'])])
                    for sm_ in sm:
                        for picking_id in sm_.picking_id:
                            for picking_type_id in picking_id.picking_type_id:
                                if not picking_type_id.is_receipt:
                                    return "[('product_id', '=', product_id), ('company_id', '=', company_id), ('id', '=', batch_on_location_id)]"
                                elif picking_type_id.is_receipt:
                                    return "[('product_id', '=', product_id), ('company_id', '=', company_id)]"

    product_on_location_id = fields.Many2many('product.product', 'product_on_location_id_rel_move_line',
                                              compute='_compute_product_batch_on_location_id', string='product_on_location_id', readonly=False)
    batch_on_location_id = fields.Many2many('stock.production.lot', 'batch_on_location_id_rel_move_line',
                                            compute='_compute_product_batch_on_location_id', string='batch_on_location_id', readonly=False, store=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True, domain=_dynamic_domain_of_product)
    lot_id = fields.Many2one(
        'stock.production.lot', 'Batch',
        domain=_dynamic_domain_of_lot_id, check_company=True)

    @api.depends('picking_id.location_id')
    def _compute_product_batch_on_location_id(self):
        for this in self:
            stock_location = []
            for picking in self.picking_id:
                stock_location.append([location_id.id for location_id in picking.location_id])

            if stock_location:
                self.product_on_location_id = self.env['stock.location'].search([
                    ('id', 'in', stock_location[0])
                ]).quant_ids.product_id
                get_data = self.env['stock.location'].search([
                    ('id', 'in', stock_location[0]),
                    ('company_id', '=', self.env.company.id)
                ]).quant_ids.lot_id.ids
                # ins_values = ",".join(["({},{})".format(
                #     this.id,
                #     data
                # ) for data in get_data])
                # if len(ins_values) > 0:
                #     delete = "delete from batch_on_location_id_rel_move_line where stock_move_line_id = {_sm}".format(_sm=this.id)
                #     self._cr.execute(delete)
                #     query = "insert into batch_on_location_id_rel_move_line (stock_move_line_id, stock_production_lot_id) values {_vals}".format(_vals=ins_values)
                #     self._cr.execute(query)
                # else:
                #     self.batch_on_location_id = None
                # self.batch_on_location_id = self.env['stock.location'].search([
                #     ('id', 'in', stock_location[0]),
                #     ('company_id', '=', self.env.company.id)
                # ]).quant_ids.lot_id
                if this._origin.id == False:
                    self.batch_on_location_id = self.env['stock.location'].search([
                        ('id', 'in', stock_location[0]),
                        ('company_id', '=', self.env.company.id)
                    ]).quant_ids.lot_id
                else:
                    self._cr.execute("""(select id from stock_move_line where id = {_id} and product_uom_qty > 0)""".format(_id=this._origin.id))
                    fet = [x[0] for x in self._cr.fetchall()]
                    if len(fet) > 0:
                        self.batch_on_location_id = self.env['stock.location'].search([
                            ('id', 'in', stock_location[0]),
                            ('company_id', '=', self.env.company.id)
                        ]).quant_ids.lot_id

