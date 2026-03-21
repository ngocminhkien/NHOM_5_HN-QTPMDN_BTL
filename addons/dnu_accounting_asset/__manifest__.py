# -*- coding: utf-8 -*-
{
    'name': "Tự động hóa Kế toán Tài sản (Mức 2)",
    'summary': "Tự động tính khấu hao và sinh bút toán kế toán",
    'author': "Nhóm 5",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['base', 'quan_ly_tai_san', 'account', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_jobs.xml',
        'views/asset_accounting_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dnu_accounting_asset/static/src/scss/fix_color.scss',
        ],
    },
    'installable': True,
    'application': False,
}