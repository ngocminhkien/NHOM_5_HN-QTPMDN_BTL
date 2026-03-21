# -*- coding: utf-8 -*-
from odoo import models, api

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        # Thực hiện cập nhật dữ liệu gốc trước
        res = super(HrEmployeeInherit, self).write(vals)
        
        # Bắt sự kiện nhân viên nghỉ việc (Trường active chuyển sang False)
        if 'active' in vals and not vals.get('active'):
            for employee in self:
                # Tìm các tài sản mà nhân viên này đang giữ (nguoi_quan_ly_id)
                assets = self.env['tai_san'].search([('nguoi_quan_ly_id', '=', employee.id)])
                
                for asset in assets:
                    # Gửi thông báo (Activity) cho người phụ trách
                    # Sử dụng activity_schedule để tạo task "To-do" tự động
                    asset.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=self.env.user.id,
                        summary=f'Thu hồi tài sản từ nhân viên nghỉ việc: {employee.name}',
                        note=f'Hệ thống phát hiện nhân viên {employee.name} đã nghỉ việc. '
                             f'Vui lòng làm thủ tục thu hồi tài sản: {asset.ten_tai_san} ({asset.ma_tai_san}).'
                    )
        return res