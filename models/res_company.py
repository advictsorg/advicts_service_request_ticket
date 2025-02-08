from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    service_request_excluded_fields = fields.Text(
        string="Service Request Excluded Fields",
        help="Comma-separated list of field names that should not be copied or written automatically.",
        default="id,name,activity_ids,service_type,connection,change_request_type,request_type,write_uid,stage,__last_update,create_date,write_date,create_uid"
    )
