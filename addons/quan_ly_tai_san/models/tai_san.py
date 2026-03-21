# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime

class TaiSan(models.Model):
    _name = 'tai_san'
    _description = 'Bảng chứa thông tin tài sản'
    
    # --- 1. THỪA KẾ MAIL THREAD (ĐỂ CÓ CHATTER - LỊCH SỬ DUYỆT) ---
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    
    _rec_name = 'cus_rec_name'
    _order = 'ngay_mua_ts desc'
    _sql_constraints = [
        ("ma_tai_san_unique", "unique(ma_tai_san)", "Mã tài sản đã tồn tại !"),
    ]

    # --- 2. CÁC TRƯỜNG CƠ BẢN---
    ma_tai_san = fields.Char('Mã tài sản', required=True, tracking=True) # Thêm tracking=True để lưu lịch sử sửa đổi
    ten_tai_san = fields.Char('Tên tài sản', required=True, tracking=True)
    ngay_mua_ts = fields.Date('Ngày mua tài sản', required=True, default=fields.Date.context_today)
    account_id = fields.Many2one('account.account', string="Tài khoản kế toán", domain=[('deprecated', '=', False)])
    
    # TRƯỜNG TRẠNG THÁI MỨC 2
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('in_use', 'Đang sử dụng'),
    ], default='draft', string="Trạng thái", tracking=True)

    don_vi_tien_te = fields.Selection([
        ('vnd', 'VNĐ'),
        ('usd', '$'),
    ], string='Đơn vị tiền tệ', default='vnd', required=True)
    
    gia_tri_ban_dau = fields.Float('Giá trị ban đầu', default=1, required=True, tracking=True)
    gia_tri_hien_tai = fields.Float('Giá trị hiện tại', default=1, required=True, tracking=True)
    danh_muc_ts_id = fields.Many2one('danh_muc_tai_san', string='Loại tài sản', required=True, ondelete='restrict')
    
    giay_to_tai_san = fields.Binary('Giấy tờ liên quan', attachment=True)
    giay_to_tai_san_filename = fields.Char('Tên file')
    hinh_anh = fields.Image('Hình ảnh', max_width=200, max_height=200)

    # --- 3. TÍCH HỢP HRM  ---
    # Thay vì chỉ dùng Text hoặc bảng tự tạo, ta dùng HRM gốc của Khoa
    nguoi_quan_ly_id = fields.Many2one('hr.employee', string='Người quản lý (HR)', tracking=True, 
                                     help="Nhân viên chịu trách nhiệm chính (Lấy từ module HR)")
    
    bo_phan_su_dung_id = fields.Many2one('hr.department', string='Bộ phận sử dụng (HR)', tracking=True,
                                       help="Bộ phận sở hữu tài sản (Lấy từ module HR)")

    # --- 4. TÍCH HỢP KẾ TOÁN ---
    # Để sau này tự động tạo bút toán
    tai_khoan_khau_hao_id = fields.Many2one('account.account', string='TK Khấu hao (214)', 
                                          domain="[('deprecated', '=', False)]")
    tai_khoan_chi_phi_id = fields.Many2one('account.account', string='TK Chi phí (64x)',
                                         domain="[('deprecated', '=', False)]")

    # --- 5. LOGIC KHẤU HAO (GIỮ NGUYÊN CỦA K15) ---
    pp_khau_hao = fields.Selection([
        ('straight-line', 'Tuyến tính'),
        ('degressive', 'Giảm dần'),
        ('none', 'Không')
    ], string='Phương pháp khấu hao', default='none', required=True, tracking=True)
    
    thoi_gian_su_dung = fields.Integer('Thời gian đã sử dụng (năm)', default=0)
    thoi_gian_toi_da = fields.Integer('Thời gian sử dụng còn lại tối đa (năm)', default=5)
    ty_le_khau_hao = fields.Float('Tỷ lệ khấu hao (%)', default=20)
    don_vi_tinh = fields.Char('Đơn vị tính', default='Chiếc', required=True)
    ghi_chu = fields.Char('Ghi chú')

    # --- 6. CÁC TRƯỜNG LIÊN KẾT & COMPUTE (GIỮ NGUYÊN CỦA K15) ---
    cus_rec_name = fields.Char(compute='_compute_cus_rec_name', store=True)
    
    phong_ban_su_dung_ids = fields.One2many('phan_bo_tai_san', 'tai_san_id', string='Lịch sử phân bổ')
    lich_su_khau_hao_ids = fields.One2many('lich_su_khau_hao', 'ma_ts', string='Lịch sử khấu hao')
    kiem_ke_history_ids = fields.One2many('kiem_ke_tai_san_line', compute='_compute_kiem_ke_history_ids', string='Lịch sử kiểm kê')
    luan_chuyen_ids = fields.Many2many('luan_chuyen_tai_san', compute='_compute_luan_chuyen_ids', string='Phiếu luân chuyển')
    thanh_ly_ids = fields.One2many('thanh_ly_tai_san', 'tai_san_id', string='Lịch sử thanh lý')
    
    # Kết hợp trạng thái thanh lý và trạng thái phê duyệt vào đây nếu cần
    trang_thai_thanh_ly = fields.Selection([
        ('chua_phan_bo', 'Chưa phân bổ'),
        ('chua_thanh_ly', 'Chưa thanh lý'),
        ('da_phan_bo', 'Đã phân bổ'),
        ('da_thanh_ly', 'Đã thanh lý'),
        ('draft', 'Nháp'),
    ], string='Trạng thái sử dụng', compute='_compute_trang_thai_thanh_ly', default='chua_phan_bo', store=True)

    lich_su_ky_thuat_ids = fields.One2many(comodel_name='lich_su_ky_thuat', inverse_name='tai_san_id', string='Tình trạng kỹ thuật')

    # --- 7. CÁC HÀM LOGIC (METHODS) ---

    # HÀM XÁC NHẬN MỨC 2
    def action_confirm(self):
        for record in self:
            if not record.account_id:
                raise ValidationError("Vui lòng chọn tài khoản kế toán trước khi xác nhận!")
            record.state = 'in_use'
            # Cập nhật thêm trạng thái sử dụng để đồng bộ với logic cũ của bạn
            record.trang_thai_thanh_ly = 'chua_thanh_ly'
    
    @api.depends('ten_tai_san', 'ma_tai_san')
    def _compute_cus_rec_name(self):
        for record in self:
            record.cus_rec_name = (record.ma_tai_san or '') + ' - ' + (record.ten_tai_san or '')

    @api.depends('thanh_ly_ids', 'phong_ban_su_dung_ids')
    def _compute_trang_thai_thanh_ly(self):
        for record in self:
            if record.thanh_ly_ids:
                record.trang_thai_thanh_ly = 'da_thanh_ly'
            elif record.phong_ban_su_dung_ids:
                record.trang_thai_thanh_ly = 'da_phan_bo'
            else:
                # Nếu chưa có lịch sử gì thì giữ ở trạng thái nháp hoặc chưa phân bổ
                record.trang_thai_thanh_ly = 'chua_phan_bo'

    def _compute_kiem_ke_history_ids(self):
        for record in self:
            phan_bo_ids = self.env['phan_bo_tai_san'].search([('tai_san_id', '=', record.id)]).ids
            record.kiem_ke_history_ids = self.env['kiem_ke_tai_san_line'].search([
                ('phan_bo_tai_san_id', 'in', phan_bo_ids)
            ])
    
    def _compute_luan_chuyen_ids(self):
        for record in self:
            phan_bo_ids = self.env['phan_bo_tai_san'].search([('tai_san_id', '=', record.id)]).ids
            luan_chuyen_lines = self.env['luan_chuyen_tai_san_line'].search([
                ('phan_bo_tai_san_id', 'in', phan_bo_ids)
            ])
            record.luan_chuyen_ids = luan_chuyen_lines.mapped('luan_chuyen_id')

    @api.constrains('gia_tri_ban_dau', 'gia_tri_hien_tai')
    def _check_gia_tri(self):
        for record in self:
            if record.gia_tri_ban_dau < 0 or record.gia_tri_hien_tai < 0:
                raise ValidationError("Giá trị (ban đầu, hiện tại) không thể âm !")
            if record.gia_tri_hien_tai > record.gia_tri_ban_dau:
                raise ValidationError("Giá trị hiện tại không thể lớn hơn giá trị ban đầu !")

    # --- HÀM TÍNH KHẤU HAO (AUTOMATION) ---
    def action_tinh_khau_hao(self):
        for record in self:
            if record.state != 'in_use':
                raise ValidationError("Tài sản phải ở trạng thái 'Đang sử dụng' mới có thể tính khấu hao!")
                
            if record.gia_tri_hien_tai <= 0:
                raise ValidationError("Giá trị hiện tại phải lớn hơn 0 !")
            if record.pp_khau_hao == 'none':
                raise ValidationError("Tài sản này không có phương pháp khấu hao!")

            so_tien_khau_hao = 0
            if record.pp_khau_hao == 'straight-line':  
                if record.thoi_gian_toi_da <= 0:
                    raise ValidationError("Thời gian sử dụng tối đa phải lớn hơn 0 (năm) !")
                so_tien_khau_hao = record.gia_tri_ban_dau / record.thoi_gian_toi_da  
            elif record.pp_khau_hao == 'degressive':  
                if record.ty_le_khau_hao <= 0 or record.ty_le_khau_hao >= 100:
                    raise ValidationError("Tỷ lệ khấu hao phải nằm trong khoảng (0,100) !")
                so_tien_khau_hao = record.gia_tri_hien_tai * (record.ty_le_khau_hao / 100) 

            so_tien_khau_hao = min(so_tien_khau_hao, record.gia_tri_hien_tai)  
            ma_phieu_khau_hao = 'KH-' + record.ma_tai_san + '-' + datetime.now().strftime('%Y%m%d%H%M%S%f')

            # Tạo bản ghi lịch sử khấu hao
            khau_hao_rec = self.env['lich_su_khau_hao'].create({
                'ma_phieu_khau_hao': ma_phieu_khau_hao,
                'ma_ts': record.id,
                'ngay_khau_hao': fields.Datetime.now(),
                'so_tien_khau_hao': so_tien_khau_hao,
                'gia_tri_con_lai': record.gia_tri_hien_tai - so_tien_khau_hao, # Lưu giá trị sau khi trừ
                'loai_phieu': 'automatic',
                'ghi_chu': f'Khấu hao tự động {fields.Date.today().strftime("%Y/%m")}'
            })

            # Cập nhật lại giá trị tài sản
            record.gia_tri_hien_tai = max(0, record.gia_tri_hien_tai - so_tien_khau_hao)
            record.thoi_gian_su_dung += 1

            # Thông báo thành công
            self.env['bus.bus']._sendone(
                self.env.user.partner_id, 
                'simple_notification', 
                {
                    'title': 'Thành công',
                    'message': f'Khấu hao tài sản "{record.ten_tai_san}" thành công!',
                    'sticky': False,  
                    'type': 'success'  
                }
            )

    # --- HÀM TẠO ACTIVITY THU HỒI TÀI SẢN ---
    def create_return_activity(self):
        # Tìm quản lý hoặc người phụ trách (mặc định lấy user đang thao tác)
        user_id = self.env.user.id 
        self.env['mail.activity'].create({
            'res_id': self.id,
            'res_model_id': self.env['ir.model']._get('tai_san').id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': 'Thu hồi tài sản từ nhân viên đã nghỉ việc',
            'user_id': user_id,
        })