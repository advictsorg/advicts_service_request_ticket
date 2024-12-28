# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields


class CustomerType(models.Model):
    _name = "service.customer.type"

    name = fields.Char(string="Name", required=True)


class PartnerCustomerType(models.Model):
    _inherit = "res.partner"
    customer_type = fields.Many2one('service.customer.type', 'Customer Type')


class ExchangeName(models.Model):
    _name = "service.exchange"
    _description = "Service Exchange"

    name = fields.Char(string="Name", required=True)


class ServiceRequestType(models.Model):
    _name = "service.request.type"
    _description = "Service Request Type"

    name = fields.Char(string="Name", required=True)
    prefix = fields.Char(string="Prefix", size=3, required=True, help="3-letter prefix for the sequence.")

    @api.constrains('prefix')
    def _check_prefix(self):
        for record in self:
            if not record.prefix or len(record.prefix) != 3 or not record.prefix.isalpha():
                raise ValidationError("The prefix must be exactly 3 alphabetic characters.")


class ServiceConnectionType(models.Model):
    _name = "service.connection.type"
    _description = "Service Connection Type"

    name = fields.Char(string="Name", required=True)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    service_request_ids = fields.One2many('service.request', 'crm_id')
