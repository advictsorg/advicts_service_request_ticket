# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models


class SrBackWizard(models.TransientModel):
    _name = "sr.back.reason"
    _description = "SR Back Reason"

    name = fields.Text(string="Reason", required=True)

    def action_save(self):
        active_id = self._context.get('active_id')
        service_id = self.env['service.request'].browse(active_id)
        if service_id:
            service_id.write({
                'back_reason': self.name,
                'stage': 'ws_request'
            })
            group = self.env.ref('advicts_service_request_ticket.sr_ws_group', raise_if_not_found=False)
            if group:
                service_id._create_auto_activity(group, False,
                                                 f'Service {service_id.service_name} is backward')
