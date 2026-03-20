# -*- coding: utf-8 -*-
{
    'name': 'DNU Accounting',
    'version': '1.0',
    'summary': 'Mở rộng kế toán cho tài sản DNU',
    'category': 'Accounting',
    'author': 'DNU',
    'license': 'AGPL-3',
    'depends': ['dnu_asset', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/dnu_asset_accounting_views.xml',
    ],
    'installable': True,
    'application': False,
}
