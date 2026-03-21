# -*- coding: utf-8 -*-
{
    'name': 'DNU Asset',
    'version': '1.0',
    'summary': 'Quản lý tài sản DNU',
    'category': 'Inventory',
    'author': 'DNU',
    'license': 'AGPL-3',
    'depends': ['base', 'nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'views/dnu_asset_views.xml',
        'views/res_users_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
}
