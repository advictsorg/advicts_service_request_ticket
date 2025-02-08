# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from odoo import fields, http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.osv.expression import AND
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from collections import OrderedDict
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper
import json
import base64
import werkzeug
import logging

_logger = logging.getLogger(__name__)


class PortalHelpdesk(CustomerPortal):

    @http.route('/portal-create-ticket', type='http', auth="user", csrf=False)
    def portal_create_ticket(self, **kw):
        try:
            _logger.info('--- Starting the ticket creation process with data: %s ---', kw)
            ticket_dic = {}
            partner_id = False

            # Check if partner ID is provided or needs to be created
            if kw.get('partner_id') and kw.get('partner_id') != '':
                _logger.debug('Searching partner by ID: %s', kw.get('partner_id'))
                partner_id = request.env['res.partner'].sudo().search(
                    [('id', '=', int(kw.get('partner_id')))], limit=1
                )
            else:
                _logger.debug('Searching partner by email: %s', kw.get('portal_email'))
                partner_id = request.env['res.partner'].sudo().search(
                    [('email', '=', kw.get('portal_email'))], limit=1
                )

            # Create new partner if not found
            if not partner_id:
                _logger.info('Partner not found. Creating a new partner.')
                partner_id = request.env['res.partner'].sudo().create({
                    'name': kw.get('portal_contact_name'),
                    'company_type': 'person',
                    'email': kw.get('portal_email'),
                    'company_id': request.env.company.id
                })
                _logger.debug('New partner created with ID: %s', partner_id.id)

            if kw.get('portal_email'):
                if partner_id:
                    _logger.info('Populating ticket details.')
                    ticket_dic.update({
                        'partner_id': partner_id.id,
                        'company_id': request.env.company.id
                    })
                    if kw.get('portal_email_subject'):
                        ticket_dic.update({'email_subject': kw.get('portal_email_subject')})
                    if kw.get('portal_contact_name'):
                        ticket_dic.update({'person_name': kw.get('portal_contact_name')})
                    if kw.get('portal_type') and kw.get('portal_type') != 'type':
                        ticket_dic.update({'ticket_type': int(kw.get('portal_type'))})
                    if kw.get('portal_category') and kw.get('portal_category') != 'category':
                        ticket_dic.update({'category_id': int(kw.get('portal_category'))})
                    if kw.get('PriorityRadioOptions'):
                        ticket_dic.update({'priority': kw.get('PriorityRadioOptions')})
                    if kw.get('portal_subcategory') and kw.get('portal_subcategory') != 'sub_category':
                        ticket_dic.update({'sub_category_id': int(kw.get('portal_subcategory'))})
                    if kw.get('portal_description'):
                        ticket_dic.update({'description': kw.get('portal_description')})

                    # Create ticket
                    _logger.info('Creating ticket with details: %s', ticket_dic)
                    ticket_id = request.env['sh.helpdesk.ticket'].sudo().create(ticket_dic)
                    if ticket_id:
                        _logger.info('Ticket created successfully with ID: %s', ticket_id.id)

                        # Handle file attachments
                        if 'portal_file' in request.params:
                            _logger.info('Adding file attachments to the ticket.')
                            attached_files = request.httprequest.files.getlist('portal_file')
                            attachment_ids = []
                            for attachment in attached_files:
                                result = base64.b64encode(attachment.read())
                                attachment_id = request.env['ir.attachment'].sudo().create({
                                    'name': attachment.filename,
                                    'res_model': 'sh.helpdesk.ticket',
                                    'res_id': ticket_id.id,
                                    'display_name': attachment.filename,
                                    'datas': result,
                                })
                                attachment_ids.append(attachment_id.id)
                                _logger.debug('File attached: %s', attachment.filename)

            _logger.info('Redirecting to ticket list.')
            return werkzeug.utils.redirect("/my/sh_tickets")
        except Exception as e:
            _logger.exception('Something went wrong %s', str(e))
