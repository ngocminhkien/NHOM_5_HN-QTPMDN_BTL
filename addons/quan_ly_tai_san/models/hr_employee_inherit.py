# -*- coding: utf-8 -*-
from odoo import models, api

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        res = super(HrEmployeeInherit, self).write(vals)
        # Bắt sự kiện nhân viên nghỉ việc (Giả sử trường active = False)
        if 'active' in vals and not vals.get('active'):
            for employee in self:
                # Tìm các tài sản người này đang quản lý
                assets = self.env['tai_san'].search([('nguoi_quan_ly_id', '=', employee.id)])
                for asset in assets:
                    # Gửi thông báo (Activity) cho người quản lý tài sản
                    asset.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=self.env.user.id,
                        summary=f'Thu hồi tài sản từ nhân viên nghỉ việc: {employee.name}',
                        note=f'Hệ thống phát hiện nhân viên {employee.name} đã nghỉ việc. Vui lòng làm thủ tục thu hồi tài sản.'
                    )
        return res