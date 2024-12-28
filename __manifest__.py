# -*- coding: utf-8 -*-
# Copyright 2024  Advicts LTD.
# Part of Advicts. See LICENSE file for full copyright and licensing details.
{
    'name': "Advicts Service Request Ticket",
    'description': """
       Service Request Ticket Management
    """,
    'summary': """ Service Request Ticket Management""",
    'version': "1.0",
    'author': 'Advicts LTD.',
    'company': 'Advicts LTD.',
    'maintainer': 'Advicts LTD.',
    'website': "https://www.advicts.com",
    'category': 'Services',
    'depends': ['mail', 'advicts_advance_helpdesk', 'contacts', 'crm'],
    'data': [
        # security
        'security/ir.model.access.csv',
        'security/security.xml',
        # data
        'data/sequence.xml',

        # Views
        'views/views.xml',
        'views/service_request.xml',
        'views/helpdesk.xml',

        'views/config_views.xml',
        # Menus
        'views/menus.xml',

    ],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
