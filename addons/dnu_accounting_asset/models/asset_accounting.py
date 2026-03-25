# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date

class DnuAssetInherit(models.Model):
    _inherit = 'dnu.asset' # KHẮC PHỤC LỖI: Sửa tai_san thành chuẩn technical name dnu.asset

    # ĐẢM BẢO TÍNH TOÁN BẰNG MONETARY VÀ CURRENCY_ID
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    
    danh_muc_ts_id = fields.Many2one('dnu.asset.category', string='Loại tài sản', tracking=True)
    ngay_mua_ts = fields.Date(string='Ngày mua', default=fields.Date.context_today)
    ngay_bat_dau_khau_hao = fields.Date(string='Ngày bắt đầu khấu hao', default=fields.Date.context_today)
    gia_tri_ban_dau = fields.Monetary(string='Nguyên giá', default=0.0, required=True, currency_field='currency_id', tracking=True)

    state = fields.Selection(selection_add=[('disposed', 'Đã thanh lý')], ondelete={'disposed': 'set default'})

    method = fields.Selection([
        ('linear', 'Đường thẳng'),
        ('degressive', 'Số dư giảm dần')
    ], string='Phương pháp khấu hao', default='linear', required=True)
    
    duration = fields.Integer(string='Thời gian khấu hao (tháng)', required=True, default=12)
    
    # Store=True giúp Báo cáo PIVOT tính toán cực nhanh qua SQL Aggregation (Thay vì RAM Python)
    depreciated_value = fields.Monetary(string='Giá trị đã khấu hao', compute='_compute_remaining_value', store=True, currency_field='currency_id')
    
    account_asset_id = fields.Many2one('account.account', string='Tài khoản tài sản', domain="[('deprecated', '=', False)]")
    account_depreciation_id = fields.Many2one('account.account', string='Tài khoản chi phí', domain="[('deprecated', '=', False)]")
    
    depreciation_line_ids = fields.One2many('dnu.asset.depreciation.line', 'asset_id', string='Bảng khấu hao')
    
    khau_hao_moi_thang = fields.Monetary(string='Khấu hao tháng', compute='_compute_khau_hao_moi_thang', store=True, currency_field='currency_id')

    ngay_bao_tri = fields.Date(string='Ngày bảo trì')

    @api.constrains('gia_tri_ban_dau', 'duration')
    def _check_positive_accounting_values(self):
        for record in self:
            if record.gia_tri_ban_dau <= 0:
                raise ValidationError("Lỗi Kế toán: Nguyên giá tài sản phải mang giá trị dương (> 0).")
            if record.duration <= 0:
                raise ValidationError("Lỗi Kế toán: Thời gian phân bổ khấu hao phải lớn hơn 0 tháng.")

    @api.constrains('ngay_bat_dau_khau_hao', 'ngay_mua_ts')
    def _check_depreciation_launch_date(self):
        for record in self:
            if record.ngay_bat_dau_khau_hao and record.ngay_mua_ts:
                if record.ngay_bat_dau_khau_hao < record.ngay_mua_ts:
                    raise ValidationError("Lỗi Logic Thời gian: Ngày bắt đầu tính khấu hao không thể diễn ra trước Ngày mua tài sản!")

    @api.model
    def _cron_send_maintenance_warning(self):
        warning_date = fields.Date.today() + relativedelta(days=3)
        assets = self.search([
            ('ngay_bao_tri', '=', warning_date),
            ('state', '=', 'in_use'),
            ('user_id', '!=', False)
        ])
        for asset in assets:
            asset.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=asset.ngay_bao_tri,
                summary=f'Bảo trì tài sản Định kỳ: {asset.name}',
                note=f'Tài sản {asset.name} (Mã: {asset.code}) tới hạn bảo trì vào {asset.ngay_bao_tri}.'
            )

    @api.depends('gia_tri_ban_dau', 'duration')
    def _compute_khau_hao_moi_thang(self):
        for record in self:
            if record.duration > 0:
                record.khau_hao_moi_thang = record.gia_tri_ban_dau / record.duration
            else:
                record.khau_hao_moi_thang = 0.0

    @api.onchange('user_id') # user_id hiện đã trỏ tới nhan_su.nhan_vien
    def _onchange_user_id_resign_check(self):
        if self.user_id and self.user_id.trang_thai == 'nghi_viec':
            emp_name = self.user_id.ho_va_ten
            self.user_id = False
            return {'warning': {'title': 'Cảnh báo Nhân sự', 'message': f'Nhân viên "{emp_name}" đã nghỉ việc!'}}

    @api.depends('gia_tri_ban_dau', 'depreciation_line_ids.amount', 'depreciation_line_ids.state')
    def _compute_remaining_value(self):
        for record in self:
            posted_lines = record.depreciation_line_ids.filtered(lambda l: l.state == 'posted')
            record.depreciated_value = sum(posted_lines.mapped('amount'))
            record.remaining_value = record.gia_tri_ban_dau - record.depreciated_value

    def action_confirm_usage(self):
        self.ensure_one()
        if self.duration <= 0 or self.gia_tri_ban_dau <= 0:
            raise UserError(_("Vui lòng kiểm tra nguyên giá và thời gian khấu hao."))
        if not self.account_asset_id or not self.account_depreciation_id:
            raise UserError(_("Vui lòng cấu hình tài khoản kế toán."))

        self.depreciation_line_ids.unlink()
        lines = []
        amount_per_month = self.gia_tri_ban_dau / self.duration
        start_date = self.ngay_bat_dau_khau_hao or date.today()

        for i in range(self.duration):
            lines.append((0, 0, {
                'depreciation_date': start_date + relativedelta(months=i+1),
                'amount': amount_per_month,
                'state': 'draft'
            }))
        self.write({'depreciation_line_ids': lines, 'state': 'in_use'})

    def action_open_disposal_wizard(self):
        self.ensure_one()
        return {
            'name': 'Thanh lý Tài sản',
            'type': 'ir.actions.act_window',
            'res_model': 'dnu.asset.disposal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_asset_id': self.id}
        }

    def write(self, vals):
        # KHÓA DỮ LIỆU: BẢO VỆ TÀI SẢN ĐÃ THANH LÝ
        for record in self:
            if record.state == 'disposed' and not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
                # Trừ khi code nội bộ đổi trạng thái ngược lại
                if 'state' not in vals:
                    raise UserError("Lỗi Khóa Cứng: Tài sản này đã Khép vòng đời (Đã Thanh lý). Hệ thống niêm phong dữ liệu. Chỉ Quản trị viên tối cao mới có thể sửa đổi!")
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state == 'disposed' and not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
                raise UserError("Lỗi Data Lock: Không thể xóa tài sản đã Thanh lý (Để bảo vệ lịch sử truy xuất).")
            if any(line.state == 'posted' for line in record.depreciation_line_ids):
                raise UserError("Lỗi Nghiệp vụ: Chặn xóa vĩnh viễn vì Tài sản này đã phát sinh Bút toán Khấu hao trên Sổ Kế toán!")
        return super().unlink()

    move_count = fields.Integer(string='Bút toán', compute='_compute_move_count')

    def _compute_move_count(self):
        for record in self:
            dep_moves = record.depreciation_line_ids.mapped('move_id')
            disposal_moves = self.env['account.move'].search([('ref', 'ilike', f'Thanh lý {record.name}')])
            record.move_count = len(dep_moves) + len(disposal_moves)

    def action_view_accounting_moves(self):
        self.ensure_one()
        dep_moves = self.depreciation_line_ids.mapped('move_id').ids
        disposal_moves = self.env['account.move'].search([('ref', 'ilike', f'Thanh lý {self.name}')]).ids
        return {
            'name': 'Giao dịch Kế toán',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', dep_moves + disposal_moves)],
            'context': {'create': False}
        }

    def action_view_handover_history(self):
        self.ensure_one()
        return {
            'name': 'Lịch sử Bàn giao',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.message',
            'view_mode': 'tree,form',
            'domain': [('model', '=', 'dnu.asset'), ('res_id', '=', self.id)],
            'context': {'create': False, 'edit': False}
        }

class DnuAssetDepreciationLine(models.Model):
    _name = 'dnu.asset.depreciation.line'
    _description = 'Dòng khấu hao'

    asset_id = fields.Many2one('dnu.asset', string='Tài sản', ondelete='cascade')
    currency_id = fields.Many2one(related='asset_id.currency_id', store=True)
    depreciation_date = fields.Date(string='Ngày khấu hao', required=True)
    amount = fields.Monetary(string='Số tiền', required=True, currency_field='currency_id')
    state = fields.Selection([('draft', 'Chưa ghi sổ'), ('posted', 'Đã ghi sổ'), ('cancelled', 'Đã hủy')], default='draft')
    move_id = fields.Many2one('account.move', string='Bút toán kế toán', readonly=True)

    def write(self, vals):
        # KHÓA DỮ LIỆU: BẢO VỆ CHỮ KÝ KẾ TOÁN (POSTED)
        for line in self:
            if line.state == 'posted' and not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
                if 'amount' in vals or 'depreciation_date' in vals:
                    raise UserError("Luật Tài Chính: Bút toán này đã được Chốt sổ (Posted). Nghiêm cấm hành vi giả mạo, cạo sửa Số tiền hoặc Ngày hạch toán!")
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.state == 'posted' and not self.env.is_superuser() and not self.env.user.has_group('base.group_system'):
                raise UserError("Luật Tài Chính: Lỗi Immutability! Bạn không được quyền bôi xóa một Khấu hao đã nộp vào Sổ Cái.")
        return super().unlink()

    def action_post_depreciation(self):
        for line in self:
            asset = line.asset_id
            move_vals = {
                'date': line.depreciation_date,
                'ref': f'Khấu hao {asset.name}',
                'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'line_ids': [
                    (0, 0, {'name': 'CP Khấu hao', 'account_id': asset.account_depreciation_id.id, 'debit': line.amount, 'credit': 0}),
                    (0, 0, {'name': 'Hao mòn', 'account_id': asset.account_asset_id.id, 'debit': 0, 'credit': line.amount}),
                ]
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            line.write({'state': 'posted', 'move_id': move.id})

    @api.model
    def _cron_generate_accounting_entries(self):
        for line in self.search([('state', '=', 'draft'), ('depreciation_date', '<=', fields.Date.today())]):
            line.action_post_depreciation()

class AssetDisposalWizard(models.TransientModel):
    _name = 'dnu.asset.disposal.wizard'
    _description = 'Wizard thanh lý tài sản'

    asset_id = fields.Many2one('dnu.asset', string='Tài sản', required=True)
    currency_id = fields.Many2one(related='asset_id.currency_id')
    ngay_thanh_ly = fields.Date(string='Ngày thanh lý', default=fields.Date.context_today)
    gia_thanh_ly = fields.Monetary(string='Giá thanh lý', required=True, currency_field='currency_id')

    def action_confirm_disposal(self):
        self.ensure_one()
        asset = self.asset_id
        
        asset.depreciation_line_ids.filtered(lambda l: l.state == 'draft' and l.depreciation_date >= self.ngay_thanh_ly).write({'state': 'cancelled'})
        
        move_vals = {
            'date': self.ngay_thanh_ly,
            'ref': f'Thanh lý {asset.name}',
            'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
            'line_ids': []
        }
        
        tk_doanh_thu = self.env['account.account'].search([('code', 'like', '711%')], limit=1)
        tk_tien = self.env['account.account'].search([('code', 'like', '111%')], limit=1)
        tk_xoa_so = self.env['account.account'].search([('code', 'like', '811%')], limit=1)
        
        if tk_tien and tk_doanh_thu:
            move_vals['line_ids'].extend([(0, 0, {'account_id': tk_tien.id, 'debit': self.gia_thanh_ly, 'credit': 0}), (0, 0, {'account_id': tk_doanh_thu.id, 'debit': 0, 'credit': self.gia_thanh_ly})])
            
        if asset.account_depreciation_id and asset.account_asset_id and tk_xoa_so:
            move_vals['line_ids'].extend([
                (0, 0, {'account_id': asset.account_depreciation_id.id, 'debit': asset.depreciated_value, 'credit': 0}),
                (0, 0, {'account_id': tk_xoa_so.id, 'debit': asset.remaining_value, 'credit': 0}),
                (0, 0, {'account_id': asset.account_asset_id.id, 'debit': 0, 'credit': asset.gia_tri_ban_dau})
            ])
            
        self.env['account.move'].create(move_vals).action_post()
        asset.write({'state': 'disposed', 'remaining_value': 0.0})
        return {'type': 'ir.actions.act_window_close'}