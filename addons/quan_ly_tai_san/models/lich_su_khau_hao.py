from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class LichSuKhauHao(models.Model):
    _name = 'lich_su_khau_hao'
    _description = 'lich_su_khau_hao'
    _rec_name = "ma_phieu_khau_hao"
    _order = 'ngay_khau_hao desc'
    _sql_constraints = [
        ("ma_phieu_khau_hao_unique", "unique(ma_phieu_khau_hao)", "Mã phiếu khấu hao đã tồn tại !"),
    ]
    
    ma_phieu_khau_hao = fields.Char('Mã phiếu', default='KHTS-', required=True)
    ma_ts = fields.Many2one('tai_san', string='Mã tài sản', required=True, ondelete='cascade')
    ngay_khau_hao = fields.Datetime('Ngày khấu hao', default=fields.Datetime.now(), required=True)
    gia_tri_hien_tai = fields.Float(string='Giá trị ban đầu', related='ma_ts.gia_tri_hien_tai', store=True)
    so_tien_khau_hao = fields.Float('Số tiền khấu hao', required=True, default=0)
    gia_tri_con_lai = fields.Float(string='Giá trị còn lại', store=True)
    
    # --- HÀM TÍNH TOÁN KHI BẤM NÚT XÁC NHẬN ---
    def compute_depreciation(self):
        for record in self:
            # Lưu ý: record ở đây là đối tượng LichSuKhauHao
            # Nếu bạn gọi hàm này từ model TaiSan, logic sẽ cần điều chỉnh lại một chút
            if record.ma_ts.gia_tri_ban_dau and record.ma_ts.thoi_gian_toi_da:
                # Ví dụ: Nguyên giá 12tr, dùng 12 tháng -> mỗi tháng 1tr
                # Sử dụng thoi_gian_toi_da (năm) * 12 để ra số tháng
                tong_so_thang = record.ma_ts.thoi_gian_toi_da * 12
                per_month = record.ma_ts.gia_tri_ban_dau / tong_so_thang
                
                for i in range(1, tong_so_thang + 1):
                    self.env['lich_su_khau_hao'].create({
                        'ma_ts': record.ma_ts.id,
                        'ma_phieu_khau_hao': f"KH-{record.ma_ts.ma_tai_san}-{i}",
                        'so_tien_khau_hao': per_month,
                        'loai_phieu': 'automatic',
                        'ghi_chu': f'Khấu hao tháng {i}',
                    })

    @api.onchange('so_tien_khau_hao')
    def _onchange_so_tien_khau_hao(self):
        for record in self:
            if record.ma_ts:
                record.gia_tri_con_lai = max(0, record.ma_ts.gia_tri_hien_tai - record.so_tien_khau_hao)
    
    loai_phieu = fields.Selection([
        ('automatic', 'Tự động'),
        ('manual', 'Thủ công')
    ], string='Phương thức', required=True)
    ghi_chu = fields.Char('Ghi chú')
    
    @api.model
    def create(self, vals):
        tai_san = self.env['tai_san'].browse(vals.get('ma_ts'))
        if tai_san:
            so_tien_khau_hao = vals.get('so_tien_khau_hao', 0)
            if tai_san.gia_tri_hien_tai == 0:
                raise ValidationError("Tài sản đã hết giá trị, không thể khấu hao !")
            if so_tien_khau_hao > tai_san.gia_tri_hien_tai:
                so_tien_khau_hao = tai_san.gia_tri_hien_tai
            
            # Cập nhật trực tiếp vào tài sản
            tai_san.gia_tri_hien_tai = max(0, tai_san.gia_tri_hien_tai - so_tien_khau_hao)
            # Cập nhật giá trị còn lại cho bản ghi lịch sử này
            vals['gia_tri_con_lai'] = tai_san.gia_tri_hien_tai  
        return super().create(vals)