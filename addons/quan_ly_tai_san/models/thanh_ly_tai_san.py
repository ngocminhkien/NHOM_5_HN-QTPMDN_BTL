# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class ThanhLyTaiSan(models.Model):
    _name = 'thanh_ly_tai_san'
    _description = 'Phiếu thanh lý tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Để hiện chatter lịch sử
    _rec_name = 'ma_phieu_thanh_ly'
    _order = 'ngay_thanh_ly desc'

    # --- 1. THÔNG TIN CƠ BẢN ---
    ma_phieu_thanh_ly = fields.Char('Mã phiếu', required=True, default=lambda self: _('Mới'), copy=False)
    tai_san_id = fields.Many2one('tai_san', string='Tài sản', required=True, domain="[('trang_thai_thanh_ly', '!=', 'da_thanh_ly')]")
    ngay_thanh_ly = fields.Date('Ngày thanh lý', default=fields.Date.context_today, required=True)
    ly_do = fields.Text('Lý do thanh lý', required=True)

    # --- 2. THÔNG TIN TÀI CHÍNH & KẾ TOÁN (QUAN TRỌNG) ---
    gia_tri_thanh_ly = fields.Float('Giá trị thanh lý (Thu về)', required=True, default=0.0, help="Số tiền thu được từ việc bán thanh lý")
    chi_phi_thanh_ly = fields.Float('Chi phí thanh lý', default=0.0, help="Chi phí bỏ ra để thanh lý (nếu có)")
    
    # Bút toán kế toán được tạo tự động (Lưu lại để truy vết)
    but_toan_id = fields.Many2one('account.move', string='Bút toán kế toán', readonly=True)

    # --- 3. QUY TRÌNH PHÊ DUYỆT (HỘI NHẬP HRM) ---
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('wait_finance', 'Chờ Tài chính duyệt'),
        ('approved', 'Đã duyệt'),
        ('cancel', 'Hủy bỏ')
    ], default='draft', string='Trạng thái', tracking=True)

    nguoi_de_xuat_id = fields.Many2one('hr.employee', string='Người đề xuất', default=lambda self: self.env.user.employee_id, readonly=True)
    nguoi_duyet_id = fields.Many2one('hr.employee', string='Kế toán duyệt', readonly=True, tracking=True)
    ngay_duyet = fields.Datetime('Ngày duyệt', readonly=True)

    # --- 4. CÁC HÀM XỬ LÝ (LOGIC) ---

    @api.model
    def create(self, vals):
        if vals.get('ma_phieu_thanh_ly', _('Mới')) == _('Mới'):
            vals['ma_phieu_thanh_ly'] = self.env['ir.sequence'].next_by_code('thanh.ly.sequence') or _('TL-NEW')
        return super(ThanhLyTaiSan, self).create(vals)

    def action_gui_duyet(self):
        """Chuyển trạng thái sang chờ duyệt"""
        for rec in self:
            if rec.gia_tri_thanh_ly < 0:
                raise ValidationError("Giá trị thanh lý không thể âm!")
            rec.trang_thai = 'wait_finance'

    def action_duyet(self):
        """
        Kế toán duyệt:
        1. Tạo bút toán tự động (Mức 2).
        2. Cập nhật trạng thái tài sản thành 'Đã thanh lý'.
        3. Lưu thông tin người duyệt.
        """
        for rec in self:
            # Kiểm tra quyền (chỉ nhóm kế toán mới được duyệt - tùy chọn)
            # if not self.env.user.has_group('account.group_account_user'):
            #     raise UserError("Chỉ có nhân viên Kế toán mới được phép duyệt!")

            # 1. Tự động tạo bút toán kế toán
            rec._create_account_entry()

            # 2. Cập nhật trạng thái
            rec.trang_thai = 'approved'
            rec.nguoi_duyet_id = self.env.user.employee_id.id
            rec.ngay_duyet = fields.Datetime.now()
            
            # 3. Cập nhật trạng thái bên Model Tài sản gốc
            if rec.tai_san_id:
                rec.tai_san_id.write({
                    'trang_thai_thanh_ly': 'da_thanh_ly',
                    'gia_tri_hien_tai': 0  # Tài sản đã thanh lý thì giá trị về 0
                })

    def action_huy(self):
        """Hủy phiếu thanh lý"""
        for rec in self:
            if rec.trang_thai == 'approved':
                raise ValidationError("Không thể hủy phiếu đã được duyệt và hạch toán!")
            rec.trang_thai = 'cancel'

    # --- 5. LOGIC TỰ ĐỘNG HÓA BÚT TOÁN (MỨC 2 - ĂN ĐIỂM) ---
    def _create_account_entry(self):
        """Hàm private để sinh bút toán Account Move"""
        self.ensure_one()
        
        # Lấy tài khoản từ cấu hình bên Tài sản (Hội nhập)
        tk_co = self.tai_san_id.tai_khoan_chi_phi_id  # TK ghi nhận giảm tài sản/chi phí (VD: 211)
        tk_no = self.env['account.account'].search([('code', 'like', '111%')], limit=1) # VD: Tiền mặt (hoặc lấy từ cấu hình khác)

        # Nếu không tìm thấy TK tiền mặt, lấy tạm TK đầu tiên loại 'liquidity'
        if not tk_no:
             tk_no = self.env['account.account'].search([('user_type_id.type', '=', 'liquidity')], limit=1)

        if not tk_co or not tk_no:
            # Nếu chưa cấu hình TK bên tab Hội nhập, báo lỗi nhắc người dùng
            raise UserError(f"Vui lòng cấu hình 'Tài khoản chi phí' trong tab Hội nhập của tài sản: {self.tai_san_id.ten_tai_san}")

        # Tìm sổ nhật ký (Journal) loại Tổng hợp hoặc Tiền mặt
        journal = self.env['account.journal'].search([('type', 'in', ('general', 'cash'))], limit=1)
        if not journal:
            raise UserError("Không tìm thấy Sổ nhật ký (Journal) phù hợp để hạch toán!")

        # Chuẩn bị dòng hạch toán (Nợ/Có)
        line_ids = [
            (0, 0, {
                'name': f"Thu thanh lý: {self.tai_san_id.ten_tai_san}",
                'account_id': tk_no.id,
                'debit': self.gia_tri_thanh_ly,
                'credit': 0,
            }),
            (0, 0, {
                'name': f"Giảm giá trị tài sản: {self.tai_san_id.ten_tai_san}",
                'account_id': tk_co.id,
                'debit': 0,
                'credit': self.gia_tri_thanh_ly,
            }),
        ]

        # Tạo bút toán
        move_vals = {
            'date': self.ngay_thanh_ly,
            'ref': f"THANHLY/{self.ma_phieu_thanh_ly}",
            'journal_id': journal.id,
            'line_ids': line_ids,
            'move_type': 'entry', # Bút toán nhật ký chung
        }
        
        move = self.env['account.move'].create(move_vals)
        move.action_post() # Post bút toán ngay lập tức
        
        # Lưu liên kết để truy vết
        self.but_toan_id = move.id
        
        return True