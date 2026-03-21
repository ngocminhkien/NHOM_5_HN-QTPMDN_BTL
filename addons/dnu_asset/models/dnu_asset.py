# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DnuAsset(models.Model):
    _name = 'dnu.asset'
    _description = 'Tài sản DNU'

    code = fields.Char(string='Mã tài sản', required=True, copy=False)
    name = fields.Char(string='Tên tài sản', required=True)
    user_id = fields.Many2one('hr.employee', string='Người sử dụng')
    location = fields.Char(string='Vị trí')
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_use', 'Đang sử dụng'),
        ('maintenance', 'Bảo dưỡng'),
        ('retired', 'Thanh lý')
    ], string='Tình trạng', default='new')

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('dnu.asset') or '/'  # nếu cần sequence
        return super().create(vals)
