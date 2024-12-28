# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of advicts. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError


class SrSurveyTemplate(models.Model):
    _name = 'sr.survey.template'
    _description = "SR Survey Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', translate=True, required=True)
    desc = fields.Text(string='Description')
    team_id = fields.Many2one('sh.helpdesk.team', 'Team', required=True)
    template_lines = fields.One2many('sr.survey.template.line', 'template_id', 'Template Lines')
    is_active = fields.Boolean('Active')

    @api.constrains('is_active')
    def _check_active_unique(self):
        for record in self:
            if record.is_active:
                domain = [
                    ('is_active', '=', True),
                    ('team_id', '=', record.team_id.id),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("Only one Survey can be active at a time."))

    def write(self, vals):

        if vals.get('is_active'):
            self.env['sr.survey.template'].search([
                ('id', '!=', self.id),
                ('team_id', '=', self.team_id.id),
                ('is_active', '=', True)
            ]).write({'is_active': False})
        return super(SrSurveyTemplate, self).write(vals)


class SrSurveyTemplateLine(models.Model):
    _name = 'sr.survey.template.line'
    _description = "SR Survey Template Line"

    template_id = fields.Many2one('sr.survey.template', 'template_id')
    question = fields.Char(string="Question", required=True)


class SrSurvey(models.Model):
    _name = 'sr.survey'
    _description = "SR Survey Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', translate=True, required=True)
    desc = fields.Text(string='Description')
    team_id = fields.Many2one('sh.helpdesk.team', 'Team', required=True)
    template_lines = fields.One2many('sr.survey.line', 'survey_id', 'Survey Lines')
    service_id = fields.Many2one('service.request', string="Service Request")
    stage = fields.Selection([('draft', 'New'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Done'),
                              ],
                             tracking=True,
                             default='draft')
    is_done = fields.Boolean(compute='_compute_is_done', store=True)

    @api.depends('stage')
    def _compute_is_done(self):
        for rec in self:
            if rec.stage == 'done':
                rec.is_done = True
            else:
                rec.is_done = False

    def in_progress(self):
        for rec in self:
            rec.stage = 'in_progress'

    def done(self):
        for rec in self:
            rec.stage = 'done'
            rec._create_auto_activity(not_user_id=rec.service_id.create_uid, title='Survey Done')

    def _create_auto_activity(self, group=False, not_user_id=False, title='Activity', message=''):
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


class SrSurveyLine(models.Model):
    _name = 'sr.survey.line'
    _description = "SR Survey Template Line"

    survey_id = fields.Many2one('sr.survey', 'survey_id')
    question = fields.Char(string="Question", required=True)
    Answer = fields.Char(string="Answer")
