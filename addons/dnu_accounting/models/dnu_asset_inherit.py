# -*- coding: utf-8 -*-
from odoo import fields, models


class DnuAsset(models.Model):
    _inherit = 'dnu.asset'

    account_id = fields.Many2one('account.account', string='Tài khoản kế toán')
    depreciation_method = fields.Selection([
        ('linear', 'Khấu hao đường thẳng'),
        ('declining', 'Khấu hao giảm dần'),
    ], string='Phương pháp khấu hao', default='linear')
    depreciated_amount = fields.Monetary(string='Giá trị đã khấu hao', currency_field='currency_id', default=0.0)
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', required=True, default=lambda self: self.env.company.currency_id)

    depreciation_line_ids = fields.One2many('dnu.asset.depreciation.line', 'asset_id', string='Lịch sử khấu hao')
