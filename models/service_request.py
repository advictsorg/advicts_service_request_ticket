# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from lxml import etree

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError


class ServiceRequestTicket(models.Model):
    _name = 'service.request'
    _description = "Service Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Ref", tracking=True, copy=False, readonly=False, index=True,
                       default=lambda self: _('New'))
    service_name = fields.Char(string="Service Description", required=True, tracking=True, translate=True, index=True)
    active_date = fields.Date(string="Activation Date", tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, index=True)
    poc_partner_id = fields.Many2one('res.partner', string='Customer POC', tracking=True, index=True)
    responsible_id = fields.Many2one('res.users',
                                     default=lambda self: self.env.user and self.env.user.id or False,
                                     string="Responsible")
    dem_device = fields.Many2one('dem.device', 'Demarcation Device', tracking=True)
    dem_port_vlan = fields.Char('Demarcation Port:Vlan', tracking=True)
    connection_type = fields.Many2one('service.connection.type', 'Connection Type', tracking=True)

    request_type = fields.Selection([
        ('request', 'request'),
        ('change_request', 'Change Request'),
    ], tracking=True, string='Type')
    is_ws = fields.Boolean(compute='_is_have_group')
    is_cts = fields.Boolean(compute='_is_have_group')
    is_legal = fields.Boolean(compute='_is_have_group')

    @api.depends('name', 'connection_id')
    def _compute_display_name(self):
        for record in self:
            if record.request_type == 'request' and record.connection_id:
                record.display_name = f"{record.connection_id}"
            else:
                record.display_name = f"{record.name}"

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = list(args or [])
        if name:
            args += ['|', ('name', operator, name), ('connection_id', operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid, order=order)

    def _is_have_group(self):
        for rec in self:
            rec.is_ws = False
            rec.is_cts = False
            rec.is_legal = False
            if self.env.user.has_group("advicts_service_request_ticket.sr_ws_group"):
                rec.is_ws = True
            if self.env.user.has_group("advicts_service_request_ticket.sr_cts_group"):
                rec.is_cts = True
            if self.env.user.has_group("advicts_service_request_ticket.sr_legal_group"):
                rec.is_legal = True

    interface_name = fields.Char('Interface Name', tracking=True)
    prtg_sensor = fields.Char('PRTG Sensor', tracking=True)
    qos_upload = fields.Float('QoS Upload(Mbps)', tracking=True)
    qos_download = fields.Float('QoS Download(Mbps)', tracking=True)
    ip_address = fields.Char('IP Address', tracking=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'In Active'),
    ], tracking=True)
    crm_id = fields.Many2one('crm.lead')
    team_ids = fields.Many2many('sh.helpdesk.team', 'service_request_team_rel', 'service_request_id', 'team_id',
                                string="Related Teams", tracking=True)
    description = fields.Text('Description', tracking=True)
    back_reason = fields.Text('Back Reason', tracking=True)

    survey_lines = fields.One2many('sr.survey', 'service_id', string="Survey Lines", tracking=True)
    survey_count = fields.Integer(string="Survey Count", compute="_compute_survey_count")

    ticket_count = fields.Integer(string="ticket Count", compute="_compute_ticket_count")
    ticket_ids = fields.One2many('sh.helpdesk.ticket', 'sr_service_id', 'Tickets')

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids)

    connection_id = fields.Char(string="Connection ID", readonly=False, required=True, copy=False, default="New")
    request_type_id = fields.Many2one(
        'service.request.type',
        string="Request Type",
    )

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'view_mode': 'tree,form',
            'res_model': 'sh.helpdesk.ticket',
            'domain': [('sr_service_id', '=', self.id)],
            'context': {
                'default_sr_service_id': self.id,  # Default value for a field
                'default_partner_id': self.partner_id.id,
            },
        }

    @api.depends('survey_lines')
    def _compute_survey_count(self):
        for record in self:
            record.survey_count = len(record.survey_lines)

    def action_view_surveys(self):
        """
        Opens the related surveys in a list view when the smart button is clicked.
        """
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Survey',
            'view_mode': 'tree,form',
            'res_model': 'sr.survey',
            'domain': [('service_id', '=', self.id)],
        }
        return action

    change_request_count = fields.Integer(string="Change Request Count", compute="_compute_change_request_count")

    @api.depends('connection')
    def _compute_change_request_count(self):
        for record in self:
            record.change_request_count = self.env['service.request'].search_count([('connection', '=', record.id)])

    def action_view_change_requests(self):

        self.ensure_one()
        action = {'type': 'ir.actions.act_window', 'name': 'Survey', 'view_mode': 'tree,form',
                  'res_model': 'service.request', 'domain': [('connection', '=', self.id)], 'context': dict(
                self.env.context,
                default_request_type='change_request',
                default_connection=self.id
            )}
        return action

    severity = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], default='0')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    stage = fields.Selection([('draft', 'New'),
                              ('ws_request', 'WS Request'),
                              ('select_department', 'Select Related Department'),
                              ('survey', 'Survey'),
                              ('avail_confirm', 'Availability Confirm'),
                              ('ws_discuss', 'WS Discuss'),
                              ('contract_draft', 'Contract Drafted'),
                              ('contract_sign', 'Contract Signed'),
                              ('wh_manager', 'Wholesale Manager'),
                              ('service_delivery', 'Service Delivery'),
                              ('service_activate', 'Service Activation'),
                              ('done', 'Done'),
                              ('cancel', 'Canceled'),
                              ('reject', 'Rejected'),
                              ],
                             tracking=True,
                             copy=False,
                             default='draft')
    drafted_contract = fields.Binary('Drafted Contract', tracking=True)
    signed_contract = fields.Binary('Signed Contract', tracking=True)

    # -------------------- Change Request Fields

    change_request_type = fields.Selection([
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('disconnect', 'Disconnect'),
        ('re_active', 'Re-Activation'),
        ('ge_upgrade', '1GE-to-10GE-Upgrade'),
    ], tracking=True, string='Request Type')
    service_type = fields.Selection([
        ('internet', 'Internet'),
        ('vpn', 'VPN'),
        ('clear_channel', 'Clear Channel'),
    ], tracking=True, string='Service Type')

    connection = fields.Many2one('service.request', 'Connection ID')
    connection_partner_id = fields.Many2one('res.partner', related='connection.partner_id')
    connection_qos_download = fields.Float('Connection QoS Download(Mbps)', related='connection.qos_download')
    connection_qos_upload = fields.Float('Connection QoS Upload(Mbps)', related='connection.qos_upload')
    connection_ip_address = fields.Char('Connection IP Address', related='connection.ip_address')
    connection_status = fields.Selection('Connection Status', related='connection.status')
    poc_name = fields.Char('POC Name')
    poc_number = fields.Char('POC Number')

    # --------------------------------------------
    def submit(self):
        for rec in self:
            rec.stage = 'ws_request'

    # def service_confirmed(self):
    #     for rec in self:
    #         rec.stage = 'service_confirmed'

    def next_to_select_department(self):
        for rec in self:
            rec.stage = 'select_department'
            group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, 'New Request')

    def next_to_survey(self):
        for rec in self:
            rec.create_survey()
            rec.stage = 'survey'

    def next_to_avail_confirm(self):
        for rec in self:
            if all(rec.survey_lines.mapped('is_done')):
                rec.stage = 'avail_confirm'

            else:
                raise ValidationError('All Survey Must be Done')

    def next_to_ws_discuss(self):
        for rec in self:
            rec.stage = 'ws_discuss'
            group = self.env.ref('advicts_service_request_ticket.sr_ws_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, f'Service {rec.service_name} Confirm Availability')

    def next_to_contract_draft(self):
        for rec in self:
            rec.stage = 'contract_draft'
            group = self.env.ref('advicts_service_request_ticket.sr_legal_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False,
                                           f'New Service {rec.service_name} Need to prepare draft contract')

    def next_to_contract_sign(self):
        for rec in self:
            rec.stage = 'contract_sign'
            group = self.env.ref('advicts_service_request_ticket.sr_ws_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False,
                                           f'New Service {rec.service_name} Need to prepare signed contract')

    def next_to_wh_manager(self):
        for rec in self:
            rec.stage = 'wh_manager'

            group = self.env.ref('advicts_service_request_ticket.sr_ws_manager_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, 'Service Wholesale Manager')

    def next_to_service_delivery(self):
        for rec in self:
            rec.stage = 'service_delivery'
            group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, 'Service Delivery')

    def next_to_service_activate(self):
        for rec in self:
            rec.stage = 'service_activate'
            group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, 'Service Activation')

    def reject(self):
        for rec in self:
            rec.stage = 'reject'
            group = self.env.ref('advicts_service_request_ticket.sr_ws_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False,
                                           f'Service {rec.service_name} is rejected')

    def send_back(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Enter Reason',
                'res_model': 'sr.back.reason',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'active_id': rec.id
                }
            }

    def _get_excluded_fields(self):
        return self.env.company.service_request_excluded_fields.split(",")

    @api.onchange('connection')
    def _onchange_connection(self):
        if self.connection and self.request_type == 'change_request':
            excluded_fields = self._get_excluded_fields()
            for field_name, field_value in self.connection.read()[0].items():
                if field_name not in excluded_fields and field_name in self._fields:
                    self[field_name] = field_value

    def done(self):
        for rec in self:
            if rec.request_type == 'change_request':
                # rec.connection.qos_upload = rec.qos_upload
                # rec.connection.qos_download = rec.qos_download
                rec.action_apply_changes()
            rec.stage = 'done'
            group = self.env.ref('advicts_service_request_ticket.sr_activation_group', raise_if_not_found=False)
            if group:
                self._create_auto_activity(group, False, 'Service Activation')

    def action_apply_changes(self):
        for record in self:

            if not record.connection:
                raise ValidationError(_("There is no connection to apply changes to."))

            excluded_fields = record._get_excluded_fields()
            updated_values = {}
            for field_name in self._fields:
                if field_name not in excluded_fields and field_name in record.connection._fields:
                    updated_values[field_name] = record[field_name]

            record.connection.write(updated_values)

    def create_survey(self):
        for rec in self:
            if rec.team_ids:
                for team in rec.team_ids:
                    team_survey = self.env['sr.survey.template'].search(
                        [('team_id', '=', team.id), ('is_active', '=', True)], limit=1)
                    old_survey = self.env['sr.survey'].search(
                        [('team_id', '=', team.id), ('service_id', '=', rec.id)], limit=1)
                    if team_survey:
                        if not old_survey:
                            survey = self.env['sr.survey'].sudo().create({
                                'name': team_survey.name,
                                'desc': team_survey.desc,
                                'team_id': team_survey.team_id.id,
                                'service_id': rec.id,
                            })
                            for line in team_survey.template_lines:
                                self.env['sr.survey.line'].sudo().create({
                                    'question': line.question,
                                    'survey_id': survey.id,
                                })
                            if team_survey.team_id.team_head:
                                survey._create_auto_activity(not_user_id=team_survey.team_id.team_head,
                                                             title='New Survey Request',
                                                             message=f'New Survey for {rec.service_name}')
                            if team_survey.team_id:
                                for member in team_survey.team_id.team_members:
                                    survey._create_auto_activity(not_user_id=member,
                                                                 title='New Survey Request',
                                                                 message=f'New Survey for {rec.service_name}')
                        else:
                            old_survey.stage = 'draft'
                            if old_survey.team_id:
                                for member in old_survey.team_id.team_members:
                                    old_survey._create_auto_activity(not_user_id=member,
                                                                     title='New Survey Request',
                                                                     message=f'New Survey for {rec.service_name}')
                    else:
                        raise ValidationError(f"Warning : {team.name} Didn't Have A Active Survey Template")
            else:
                raise ValidationError('Warning : Select The Teams First')

    def _create_auto_activity(self, group=False, not_user_id=False, title='Activity', message=''):
        try:
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            if group:
                for user in group.users:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        note=f'{message}',
                        user_id=user.id,
                        summary=_(f'{title}')
                    )
            elif not_user_id:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note=f'{message}',
                    user_id=not_user_id.id,
                    summary=_(f'{title}')
                )
        except Exception as e:
            raise ValidationError(str(e))

    @api.model
    def create(self, vals):
        seq = False
        if vals.get('name', _('New')) == _('New'):
            request_type = vals.get('request_type')

            if request_type == 'change_request':

                vals['name'] = self.env['ir.sequence'].next_by_code('service.change.request') or _('New')
            else:
                seq = self.env['ir.sequence'].next_by_code('service.request') or _('New')
                vals['name'] = seq

            # Debugging output
            print(f"Generated sequence for request_type '{request_type}': {vals['name']}")

        if vals.get('connection_id', 'New') == 'New' and vals.get('request_type') == 'request':
            request_type = self.env['service.request.type'].browse(vals.get('request_type_id'))
            if not request_type.prefix:
                raise ValidationError("The selected Request Type must have a prefix.")
            sequence = seq or '0000'
            vals['connection_id'] = f"{request_type.prefix.upper()}-{sequence}"

        record = super(ServiceRequestTicket, self).create(vals)

        if record.request_type == 'change_request' and record.connection:
            record._onchange_connection()
        return record


class HelpdeskTicket(models.Model):
    _inherit = 'sh.helpdesk.ticket'
    sr_service_id = fields.Many2one('service.request')

    def action_approve(self):
        res = super(HelpdeskTicket, self).action_approve()
        # Update Next Stages [Ghaith]
        if self.sr_service_id:
            if self.stage_id.name == 'Done' and self.ticket_type.is_internal_ticket:
                group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
                if group:
                    self.sr_service_id._create_auto_activity(group, False,
                                                             f'Ticket {self.email_subject} is Done')
            elif self.stage_id.name == 'Closed' and self.ticket_type.is_internal_ticket:
                group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
                if group:
                    self.sr_service_id._create_auto_activity(group, False,
                                                             f'Ticket {self.email_subject} is Closed')
            elif self.stage_id.name == 'Cancelled' and self.ticket_type.is_internal_ticket:
                group = self.env.ref('advicts_service_request_ticket.sr_cts_group', raise_if_not_found=False)
                if group:
                    self.sr_service_id._create_auto_activity(group, False,
                                                             f'Ticket {self.email_subject} is Cancelled')
        return res
