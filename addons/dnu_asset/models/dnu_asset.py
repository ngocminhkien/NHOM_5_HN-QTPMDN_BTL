# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DnuAsset(models.Model):
    _name = 'dnu.asset'
    _description = 'Tài sản DNU'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Mã tài sản', required=True, copy=False)
    name = fields.Char(string='Tên tài sản', required=True, tracking=True)
    user_id = fields.Many2one('nhan_vien', string='Nhân viên sử dụng', tracking=True)
    phong_ban_su_dung_id = fields.Many2one('don_vi', string='Phòng ban sử dụng', tracking=True)
    location = fields.Char(string='Vị trí')
    remaining_value = fields.Float(string='Giá trị còn lại', default=0.0, tracking=True)
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_use', 'Đang sử dụng'),
        ('maintenance', 'Bảo dưỡng'),
        ('retired', 'Thanh lý')
    ], string='Tình trạng', default='new')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Lỗi: Mã tài sản đã tồn tại trong Hệ thống! Vui lòng nhập mã khác để tránh trùng lặp.')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('dnu.asset') or '/'
        return super().create(vals)

    # === TÍNH NĂNG QR CODE (Dành cho KANBAN) ===
    qr_image = fields.Binary(string='Mã QR', compute='_compute_qr_code')

    @api.depends('code')
    def _compute_qr_code(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        try:
            import qrcode
            import base64
            from io import BytesIO
            has_qr = True
        except ImportError:
            has_qr = False

        for record in self:
            url = f"{base_url}/web#id={record._origin.id or record.id}&model=dnu.asset&view_type=form"
            if has_qr:
                qr = qrcode.QRCode(version=1, box_size=3, border=4)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                temp = BytesIO()
                img.save(temp, format="PNG")
                record.qr_image = base64.b64encode(temp.getvalue())
            else:
                record.qr_image = False

class DnuAssetCategory(models.Model):
    _name = 'dnu.asset.category'
    _description = 'Loại tài sản / Danh mục'

    name = fields.Char(string='Tên Danh mục', required=True)
    code = fields.Char(string='Mã danh mục')

class NhanVienInherit(models.Model):
    _inherit = 'nhan_vien'
    
    tai_san_ids = fields.One2many('dnu.asset', 'user_id', string='Tài sản đang giữ')
    asset_ids = fields.One2many('dnu.asset', 'user_id', string='Tài sản (Tương thích view cũ)')

class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên liên kết')
