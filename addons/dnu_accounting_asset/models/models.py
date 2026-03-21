from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class DnuAsset(models.Model):
    _inherit = 'quan_ly_tai_san.tai_san' # Kiểm tra đúng tên model gốc của bạn

    # 1. Thêm các trường kế toán
    asset_account_id = fields.Many2one('account.account', string="Tài khoản tài sản (211)", 
                                       domain=[('code', '=like', '211%')])
    expense_account_id = fields.Many2one('account.account', string="Tài khoản chi phí (642)", 
                                         domain=[('code', '=like', '642%')])
    state = fields.Selection([('draft', 'Nháp'), ('open', 'Đang khấu hao')], string="Trạng thái", default='draft')
    depreciation_line_ids = fields.One2many('dnu.asset.line', 'asset_id', string="Bảng khấu hao")

    # 2. Hàm tự động sinh bảng khấu hao khi bấm nút "Xác nhận"
    def action_confirm_asset(self):
        for rec in self:
            if rec.gia_tri > 0 and rec.thoi_gian_khau_hao > 0:
                amount_per_month = rec.gia_tri / rec.thoi_gian_khau_hao
                start_date = fields.Date.today()
                
                # Xóa bảng cũ nếu có
                rec.depreciation_line_ids.unlink()
                
                # Tạo các dòng khấu hao tự động
                for i in range(rec.thoi_gian_khau_hao):
                    self.env['dnu.asset.line'].create({
                        'asset_id': rec.id,
                        'name': 'Khấu hao tháng %s' % (i + 1),
                        'depreciation_date': start_date + relativedelta(months=i),
                        'amount': amount_per_month,
                    })
                rec.state = 'open'

# Model lưu bảng khấu hao
class DnuAssetLine(models.Model):
    _name = 'dnu.asset.line'
    _description = 'Chi tiết khấu hao'

    asset_id = fields.Many2one('quan_ly_tai_san.tai_san', string="Tài sản")
    name = fields.Char(string="Diễn giải")
    depreciation_date = fields.Date(string="Ngày khấu hao")
    amount = fields.Float(string="Số tiền")

# 3. Logic HR: Tự động nhắc thu hồi tài sản khi nhân viên nghỉ việc
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def action_archive(self):
        # Tìm tất cả tài sản đang được gán cho nhân viên này
        assets = self.env['quan_ly_tai_san.tai_san'].search([('nhan_vien_id', '=', self.id)])
        for asset in assets:
            # Tạo một thông báo (Activity) cho người quản lý
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': f'Cần thu hồi tài sản {asset.name} từ nhân viên {self.name} do nghỉ việc.',
                'res_id': asset.id,
                'res_model_id': self.env.ref('dnu_accounting_asset.model_quan_ly_tai_san_tai_san').id,
                'user_id': self.env.user.id,
            })
        return super(HrEmployee, self).action_archive()