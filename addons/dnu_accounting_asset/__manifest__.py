# -*- coding: utf-8 -*-
{
    'name': "Tự động hóa Kế toán Tài sản (Mức 2)",
    'summary': "Tự động tính khấu hao và sinh bút toán kế toán",
    'author': "Nhóm 5",
    'category': 'Accounting',
    'version': '1.0',
    # Chỉnh sửa Depend để tập trung thẳng vào dnu_asset và nhan_su
    'depends': ['base', 'dnu_asset', 'nhan_su', 'account', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'report/asset_handover_report.xml',
        'data/cron_jobs.xml',
        'views/asset_accounting_views.xml',
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dnu_accounting_asset/static/src/scss/fix_color.scss',
        ],
    },
    'installable': True,
    'application': False,
}