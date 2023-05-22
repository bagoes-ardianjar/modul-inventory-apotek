from odoo import models, fields, _, api
from odoo.http import request
from odoo.exceptions import UserError
from json import dumps
import uuid
import http

class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'
    _description = 'Stock & Logistic Management'

    def _compute_is_requested(self):
        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', '=', self.id),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False),
                                                  ('author_id', '=', self.env.user.partner_id.id)], limit=1, order='id asc')
        if not msg_id:
            self.is_requested = False
        else:
            self.is_requested = True

    @api.depends('do_reportbutton', 'do_reportbutton.name', 'do_reportbutton.button_clicked', 'do_reportbutton.picking_ids')
    def _compute_one_click(self):
        check_for_click = self.env['do.reportbutton.click'].search(
            [('name', 'in', self.env.user.ids), ('picking_ids', 'in', self.ids)])
        if not check_for_click:
            self.one_click = False

        else:
            for check_for_click_ in check_for_click:
                if check_for_click_.button_clicked == False:
                    self.one_click = False
                elif check_for_click_.button_clicked == True:
                    self.one_click = True

    def _compute_one_click_check(self):
        check_for_click = self.env['do.reportbutton.click'].search(
            [('name', 'in', self.env.user.ids), ('picking_ids', 'in', self.ids)])

        if not check_for_click:
            for picking in self:
                picking.doreport_button_check = False
        else:
            for picking in self:
                for check_for_click_ in check_for_click:
                    if picking.id == check_for_click_.picking_ids.id:
                        picking.doreport_button_check = True

    @api.depends('user_id')
    def _compute_is_admin(self):
        if self.env.user.name != 'Administrator':
            for picking in self:
                picking.is_admin = False

        elif self.env.user.name == 'Administrator':
            for picking in self:
                picking.is_admin = True

    def _compute_manager_do_report_user(self):
        # msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
        #                                              ('res_id', '=', self.id),
        #                                              ('is_requested_open_do', '=', True),
        #                                              ('is_approved', '=', False),
        #                                              ('is_rejected', '=', False),
        #                                              ('requested_user', '!=', False)
        #                                              ], limit=1, order='id asc')

        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', 'in', self.ids),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False),
                                                  ('author_id.user_ids.manager_approval.user_ids.id', '=', self.env.user.id)])

        if not msg_id:
            for pick in self:
                pick.manager_do_report_user = False
        else:
            for pick in self:
                pick.manager_do_report_user = True

    picking_type_id_name = fields.Char('picking_type_id_name', related='picking_type_id.name', store=True)
    checker = fields.Many2one('checker', string='Checker')
    picker = fields.Many2one('picker', string='Picker')
    customer_invoice = fields.Char('No. Invoice Customer')
    coli = fields.Char('Coli')
    expedition_name = fields.Char('Nama Ekspedisi')
    plat_number = fields.Char('No. Plat')
    driver_name = fields.Char('Nama Supir')
    apj = fields.Many2one('hr.employee', string='APJ')
    delivery_status = fields.Char('Delivery Order Status')

    # returns
    return_reason = fields.Many2one('return.reason', string='Reason')
    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True,
        states={'done': [('readonly', False)], 'cancel': [('readonly', False)]},
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    is_no_backorder = fields.Boolean(string='Is No Backorder')
    invoice_check = fields.Boolean(string='Inv Check', default=False)
    one_click = fields.Boolean(string='One click', compute='_compute_one_click', readonly=False)
    do_reportbutton = fields.One2many('do.reportbutton.click', 'picking_ids', string='DO Report Button Clicked Count')
    doreport_button_check = fields.Boolean(compute='_compute_one_click_check', readonly=False)
    is_admin = fields.Boolean(compute='_compute_is_admin', readonly=False)
    is_requested = fields.Boolean(compute='_compute_is_requested', readonly=False)
    manager_do_report_user = fields.Boolean(compute='_compute_manager_do_report_user', string='Manager DO Report User',
                                            readonly=False)

    access_token = fields.Char('Identification token', default=lambda self: str(uuid.uuid4()), readonly=True, required=True, copy=False)
    jumlah_koli = fields.Integer('Jumlah Koli', tracking=True)
    nomor_koli = fields.Char('Nomor Koli', tracking=True)
    kasir = fields.Many2one('hr.employee', string='Kasir')

    def button_validate(self):
        res = super(DeliveryOrder, self).button_validate()
        ctx = dict(self.env.context or {})

        for picking in self:
            if picking.picking_type_id_name == 'Receipts':
                if 'active_ids' in ctx and not picking.is_return:
                    po = self.env['purchase.order'].browse(ctx['active_ids'])

                    if_of_supplierinfo = []

                    if po:
                        for po_obj in po:
                            for order_line in po_obj.order_line:
                                for prd in order_line.product_id:
                                    for seller_ids in prd.seller_ids:
                                        if_of_supplierinfo.append(seller_ids.id)
                                        if seller_ids.id == po_obj.id_of_supplierinfo:
                                            seller_ids.effective_date = po_obj.effective_date

        return res

    def on_delivery(self):
        if not self.delivery_status:
            self.delivery_status = 'On Delivery'

    def on_complete(self):
        self.delivery_status = 'Completed'
    
    def button_print_no_backorder(self):
        return self.env.ref('ati_pbf_stock.action_report_no_backorder_custom').report_action(self)

    def button_report_delivery_order(self):
        data_ = {
            'name': self.env.user.id,
            'button_clicked': True,
            'picking_ids': self.id,
        }

        self.write({'do_reportbutton': [(0, 0, data_)]})

        return self.env.ref('ati_pbf_stock.action_report_delivery_order_custom').report_action(self)

    def button_report_retur(self):
        return self.env.ref('ati_pbf_stock.action_report_tanda_terima_retur').report_action(self)

    def button_report_return_picking(self):
        return self.env.ref('ati_pbf_stock.action_report_picking_pbf').report_action(self)

    def request_approval_for_print_do(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env['mail.template'].search([('name', '=', 'Stock Picking: Request to Delivery Order Report')])

        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)

        url_approve = request.env['ir.config_parameter'].get_param('web.base.url')
        url_approve += '/web/approve?token=%s&db=%s&user_id=%s&id=%s&view_id=%s&requestor=%s&manager=%s&do_number=%s&requestor_email=%s&manager_email=%s&requestor_id=%s&user=%s' % (self.access_token,
                            self._cr.dbname,
                            self.env.user.id,
                            self.id,
                            self.env.ref('stock.view_picking_form').id,
                            self.env.user.name,
                            self.env.user.manager_approval.name or '',
                            self.name,
                            self.env.user.partner_id.email,
                            self.env.user.manager_approval.email or '',
                            self.env.user.partner_id.id,
                            self.env.user.manager_approval.user_ids.id)

        url_reject = request.env['ir.config_parameter'].get_param('web.base.url')
        url_reject += '/web/reject?token=%s' \
                      '&db=%s' \
                      '&user_id=%s' \
                      '&id=%s' \
                      '&view_id=%s' \
                      '&requestor=%s' \
                      '&manager=%s' \
                      '&do_number=%s' \
                      '&requestor_email=%s' \
                      '&manager_email=%s&user=%s' % (
                            self.access_token,
                            self._cr.dbname,
                            self.env.user.id,
                            self.id,
                            self.env.ref('stock.view_picking_form').id,
                            self.env.user.name,
                            self.env.user.manager_approval.name or '',
                            self.name,
                            self.env.user.partner_id.email,
                            self.env.user.manager_approval.email or '',
                            self.env.user.manager_approval.user_ids.id)

        body_html = f'''Dear {request.env.user.manager_approval.name or ''},<br><br>
                        {request.env.user.name} request to open DO Report Button on
                        <a href={base_url}>{self.name}</a><br><br>
                        <a href={url_approve} style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">Approve</a> <a href={url_reject} style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;"> Reject</a><br><br>
                        Thank you,<br>
                        {request.env.user.signature}'''
        template_id.body_html = body_html

        # mail_pool = self.env['mail.mail']
        # values = {}
        # values.update({'subject': '%s Request to open Delivery Order Report Button on %s' % (self.env.user.name, self.name) })
        # values.update({'email_to': self.env.user.manager_approval.email})
        # values.update({'body_html': body_html})
        # values.update({'body': body_html})
        # values.update(
        #     {'res_id': self.id})  # [optional] here is the record id, where you want to post that email after sending
        #
        # values.update({
        #     'model': 'stock.picking'})  # [optional] here is the object(like 'project.project')  to whose record id you want to post that email after sending
        #
        # msg_id = mail_pool.create(values).send()

        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_partner_ids': self.env.user.manager_approval.ids,
            'default_composition_mode': 'comment',
            'default_is_requested_open_do': True,
            'mark_so_as_sent': True,
            'force_email': True,
        }

        if not self.env.user.manager_approval:
            raise UserError(_('Anda harus mengisi manager approval di Menu User'))
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }

    def open_the_list_of_request_do_report(self):
        msg_id = self.env['mail.message'].search([('model', '=', 'stock.picking'),
                                                  ('res_id', '=', self.id),
                                                  ('is_requested_open_do', '=', True),
                                                  ('is_approved', '=', False),
                                                  ('is_rejected', '=', False)],
                                                 order='id asc')

        view_id = self.env.ref('ati_pbf_stock.view_do_reportbutton_request_form').id

        return {
            'name': _('DO Report Request List'),
            'res_model': 'do.reportbutton.req',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': False,
            'context': {
                'edit': False,
                'create': False,
                'active_id': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Users'

    manager_approval = fields.Many2one('res.partner', string='Manager Approval')

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'
    _description = 'Mail Composer'

    @api.depends('template_id')
    def _compute_mail_template_name(self):
        self.mail_template_name = self.template_id.name

    mail_template_name = fields.Char(string='Mail template name', compute='_compute_mail_template_name', readonly=False)

class OpenReportDo(models.TransientModel):
    _name = 'open.report.do'
    _description = 'Open Report DO'

