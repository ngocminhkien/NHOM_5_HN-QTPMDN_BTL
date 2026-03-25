from odoo import models, fields, api
from datetime import date

from odoo.exceptions import ValidationError

class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_va_ten'
    _order = 'ten asc, tuoi desc'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)

    ho_ten_dem = fields.Char("Họ tên đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ và tên", compute="_compute_ho_va_ten", store=True)
    
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách lịch sử công tác")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    anh = fields.Binary("Ảnh")
    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap", 
        inverse_name="nhan_vien_id", 
        string = "Danh sách chứng chỉ bằng cấp")
    so_nguoi_bang_tuoi = fields.Integer("Số người bằng tuổi", 
                                        compute="_compute_so_nguoi_bang_tuoi",
                                        store=True
                                        )

    # ===== LIÊN KẾT CHÉO MODULE DNU_ASSET =====
    trang_thai = fields.Selection([
        ('dang_lam', 'Đang làm việc'),
        ('nghi_viec', 'Nghỉ việc')
    ], string='Trạng thái', default='dang_lam')

    don_vi_id = fields.Many2one('don_vi', string='Phòng ban')

    @api.constrains('trang_thai')
    def _check_thu_hoi_tai_san_khi_nghi_viec(self):
        for record in self:
            if record.trang_thai == 'nghi_viec':
                # Tìm xem nhân viên này có đang giữ tài sản nào của dnu.asset không
                assets = self.env['dnu.asset'].search([
                    ('user_id', '=', record.id),
                    ('state', '=', 'in_use')
                ])
                if assets:
                    ten_tai_san = ', '.join(assets.mapped('name'))
                    raise ValidationError(f"Không thể cho nghỉ việc! Nhân viên đang giữ tài sản: {ten_tai_san}. Vui lòng thu hồi trước.")

    def write(self, vals):
        res = super(NhanVien, self).write(vals)
        # Tự động cập nhật phòng ban cho tài sản đang giữ bên dnu_asset
        if 'don_vi_id' in vals:
            for record in self:
                if record.don_vi_id:
                    assets = self.env['dnu.asset'].search([
                        ('user_id', '=', record.id),
                        ('state', '=', 'in_use')
                    ])
                    # Update thẳng trường phong_ban_su_dung_id
                    assets.write({'phong_ban_su_dung_id': record.don_vi_id.id})
        return res
    
    @api.depends("tuoi")
    def _compute_so_nguoi_bang_tuoi(self):
        for record in self:
            if record.tuoi:
                records = self.env['nhan_vien'].search(
                    [
                        ('tuoi', '=', record.tuoi),
                        ('ma_dinh_danh', '!=', record.ma_dinh_danh)
                    ]
                )
                record.so_nguoi_bang_tuoi = len(records)
    _sql_constrains = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã định danh phải là duy nhất')
    ]

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                record.ho_va_ten = record.ho_ten_dem + ' ' + record.ten
    
    
    
                
    @api.onchange("ten", "ho_ten_dem")
    def _default_ma_dinh_danh(self):
        for record in self:
            if record.ho_ten_dem and record.ten:
                chu_cai_dau = ''.join([tu[0][0] for tu in record.ho_ten_dem.lower().split()])
                record.ma_dinh_danh = record.ten.lower() + chu_cai_dau
    
    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                year_now = date.today().year
                record.tuoi = year_now - record.ngay_sinh.year

    @api.constrains('tuoi')
    def _check_tuoi(self):
        for record in self:
            if record.tuoi < 18:
                raise ValidationError("Tuổi không được bé hơn 18")
