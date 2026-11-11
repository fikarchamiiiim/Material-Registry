# -*- coding: utf-8 -*-
{
    'name': 'Material Registry',
    'version': '14.0.1.0.0',
    'summary': 'Registrasi material yang akan dijual + REST API',
    'description': """
Modul registrasi material: model supplier dan material, REST API, serta unit test.
    """,
    'author': 'Backend Test',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}
