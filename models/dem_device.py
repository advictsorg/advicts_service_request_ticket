# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError


class DemDevice(models.Model):
    _name = 'dem.device'
    _description = "Demarcation Device"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", tracking=True, copy=False, index=True , required=True)
