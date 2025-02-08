# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields


class CustomerType(models.Model):
    """
    Model for defining customer types.
    This model allows categorizing customers into specific types
    to help streamline service operations and improve management.
    """
    _name = "service.customer.type"
    name = fields.Char(
        string="Name",
        required=True,
        help="The name of the customer type."
    )


class PartnerCustomerType(models.Model):
    """
    Extension of the res.partner model to include a customer type field.
    Links partners to specific customer types for better classification.
    """
    _inherit = "res.partner"
    customer_type = fields.Many2one('service.customer.type', 'Customer Type')


class ExchangeName(models.Model):
    """
    Model for managing service exchange names.
    Useful for categorizing exchanges related to customer services.
    """
    _name = "service.exchange"
    _description = "Service Exchange"

    name = fields.Char(string="Name", required=True)


class ServiceRequestType(models.Model):
    """
    Model to define types of service requests.
    Contains fields for request naming and a prefix used in sequences.
    """
    _name = "service.request.type"
    _description = "Service Request Type"

    name = fields.Char(string="Name", required=True)
    prefix = fields.Char(string="Prefix", required=True, help="letter prefix for the sequence.")

    """
        Validation to ensure that the prefix field adheres to the following rules:
        - Must consist of exactly 3 alphabetical characters.
        - Raises a ValidationError if the conditions are not met.
    """
    # @api.constrains('prefix')
    # def _check_prefix(self):
    #     for record in self:
    #         if not record.prefix or not record.prefix.isalpha():
    #             raise ValidationError("The prefix must be exactly 3 alphabetic characters.")


class ServiceConnectionType(models.Model):
    """
    Model for defining types of service connections.
    Used to categorize different types of service links or connections.
    """
    _name = "service.connection.type"
    _description = "Service Connection Type"

    name = fields.Char(string="Name", required=True)


class CrmLead(models.Model):
    """
    Extension of the crm.lead model to include service request relations.
    Adds a one-to-many relationship to service requests.
    """
    _inherit = "crm.lead"

    service_request_ids = fields.One2many('service.request', 'crm_id')
