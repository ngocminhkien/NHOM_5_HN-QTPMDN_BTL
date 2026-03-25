# -*- coding: utf-8 -*-
from odoo import fields, models


class DnuAsset(models.Model):
    _inherit = 'dnu.asset'
    
    # LƯU Ý GỘP CODE:
    # Toàn bộ cấu trúc Kế toán (depreciation_method, depreciated_amount, currency_id, depreciation_line_ids)
    # đã được quy hoạch chuẩn mực và gộp sang module dnu_accounting_asset (tên mới: method, depreciated_value).
    # Không định nghĩa lại ở đây để tránh bảng CSDL bị phình to và Log báo trùng lặp.
