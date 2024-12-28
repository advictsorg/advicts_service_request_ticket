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
            ticket_dic = {}
            partner_id = False
            if kw.get('partner_id') and kw.get('partner_id') != '':
                partner_id = request.env['res.partner'].sudo().search(
                    [('id', '=', int(kw.get('partner_id')))], limit=1)
            else:
                partner_id = request.env['res.partner'].sudo().search(
                    [('email', '=', kw.get('portal_email'))], limit=1)
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().create({
                    'name': kw.get('portal_contact_name'),
                    'company_type': 'person',
                    'email': kw.get('portal_email'),
                    'company_id': request.env.company.id
                })
            if kw.get('portal_email'):
                if partner_id:
                    ticket_dic.update({
                        'partner_id': partner_id.id,
                        'company_id': request.env.company.id
                    })
                    if kw.get('portal_email_subject'):
                        ticket_dic.update({
                            'email_subject': kw.get('portal_email_subject')
                        })
                    if kw.get('portal_contact_name'):
                        ticket_dic.update({
                            'person_name': kw.get('portal_contact_name'),
                        })
                    if kw.get('portal_type') and kw.get('portal_type') != 'type':
                        ticket_dic.update({
                            'ticket_type': int(kw.get('portal_type')),
                        })
                    if kw.get('PriorityRadioOptions'):
                        ticket_dic.update({
                            'priority': kw.get('PriorityRadioOptions'),
                        })
                    if kw.get('portal_service_request') and kw.get('portal_service_request') != 'SR':
                        ticket_dic.update({
                            'sr_service_id': int(kw.get('portal_service_request')),
                        })
                    if kw.get('portal_category') and kw.get('portal_category') != 'category':
                        ticket_dic.update({
                            'category_id': int(kw.get('portal_category')),
                        })
                    if kw.get('portal_subcategory') and kw.get('portal_subcategory') != 'sub_category':
                        ticket_dic.update({
                            'sub_category_id': int(kw.get('portal_subcategory')),
                        })
                    if kw.get('portal_description'):
                        ticket_dic.update({
                            'description': kw.get('portal_description'),
                        })
                    # team_id=False
                    # if request.env.company and request.env.company.sh_default_team_id:
                    #     team_id = request.env['sh.helpdesk.team'].sudo().search([('id','=',request.env.company.sh_default_team_id.id)], limit=1).id
                    # ticket_dic.update({
                    #     'team_id':team_id,
                    #     'name':kw.get('portal_email_subject') if kw.get('portal_email_subject') else '',
                    # })
                    ticket_id = request.env['sh.helpdesk.ticket'].sudo().create(ticket_dic)
                    if ticket_id:
                        if 'portal_file' in request.params:
                            attached_files = request.httprequest.files.getlist(
                                'portal_file')
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
            return werkzeug.utils.redirect("/my/sh_tickets")
        except Exception as e:
            _logger.exception('Something went wrong %s', str(e))
