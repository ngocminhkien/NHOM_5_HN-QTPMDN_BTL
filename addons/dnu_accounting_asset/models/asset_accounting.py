# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import date

# =================================================================================
# Logic tự động hóa Mức 2: Kế thừa Tài sản thêm Tài chính
# =================================================================================
class DnuAssetInherit(models.Model):
    _inherit = 'tai_san' # Thay bằng tên model tài sản gốc của bạn nếu khác

    method = fields.Selection([
        ('linear', 'Đường thẳng'),
        ('degressive', 'Số dư giảm dần')
    ], string='Phương pháp khấu hao', default='linear', required=True)
    
    duration = fields.Integer(string='Tổng thời gian khấu hao (tháng)', required=True, default=12)
    
    depreciated_value = fields.Float(string='Giá trị đã khấu hao', compute='_compute_remaining_value', store=True)
    remaining_value = fields.Float(string='Giá trị còn lại', compute='_compute_remaining_value', store=True)
    
    account_asset_id = fields.Many2one('account.account', string='Tài khoản tài sản', domain="[('deprecated', '=', False)]")
    account_depreciation_id = fields.Many2one('account.account', string='Tài khoản chi phí khấu hao', domain="[('deprecated', '=', False)]")
    
    depreciation_line_ids = fields.One2many('dnu.asset.depreciation.line', 'asset_id', string='Bảng kế hoạch khấu hao')

    @api.depends('gia_tri_ban_dau', 'depreciation_line_ids.amount', 'depreciation_line_ids.state')
    def _compute_remaining_value(self):
        # Logic tự động hóa Mức 2: Tính toán giá trị còn lại
        for record in self:
            posted_lines = record.depreciation_line_ids.filtered(lambda l: l.state == 'posted')
            record.depreciated_value = sum(posted_lines.mapped('amount'))
            record.remaining_value = record.gia_tri_ban_dau - record.depreciated_value

    def action_confirm_usage(self):
        # Logic tự động hóa Mức 2 (Action Trigger): Sinh bảng kế hoạch khấu hao
        self.ensure_one()
        if self.duration <= 0 or self.gia_tri_ban_dau <= 0:
            raise UserError(_("Thời gian và giá trị ban đầu phải lớn hơn 0."))
        if not self.account_asset_id or not self.account_depreciation_id:
            raise UserError(_("Vui lòng cấu hình tài khoản kế toán trước khi xác nhận."))

        self.depreciation_line_ids.unlink() # Xóa bảng cũ nếu có
        
        lines = []
        amount_per_month = self.gia_tri_ban_dau / self.duration
        current_date = date.today()

        for i in range(self.duration):
            depreciation_date = current_date + relativedelta(months=i+1)
            lines.append((0, 0, {
                'depreciation_date': depreciation_date,
                'amount': amount_per_month,
                'state': 'draft'
            }))
        self.write({'depreciation_line_ids': lines})

    def unlink(self):
        # Đảm bảo không xóa tài sản đã có bút toán
        for record in self:
            if any(line.state == 'posted' for line in record.depreciation_line_ids):
                raise UserError(_('Không thể xóa tài sản đã có bút toán khấu hao được ghi sổ!'))
        return super(DnuAssetInherit, self).unlink()

# =================================================================================
# Logic tự động hóa Mức 2: Bảng kế hoạch khấu hao & Sinh Bút toán (Cron)
# =================================================================================
class DnuAssetDepreciationLine(models.Model):
    _name = 'dnu.asset.depreciation.line'
    _description = 'Bảng kế hoạch khấu hao'

    asset_id = fields.Many2one('tai_san', string='Tài sản', ondelete='cascade')
    depreciation_date = fields.Date(string='Ngày khấu hao', required=True)
    amount = fields.Float(string='Số tiền', required=True)
    state = fields.Selection([
        ('draft', 'Chưa ghi sổ'),
        ('posted', 'Đã ghi sổ')
    ], string='Trạng thái', default='draft')
    move_id = fields.Many2one('account.move', string='Bút toán kế toán', readonly=True)

    @api.model
    def _cron_generate_accounting_entries(self):
        # Logic tự động hóa Mức 2 (Scheduled Action - Cron Job)
        today = fields.Date.today()
        lines_to_post = self.search([
            ('state', '=', 'draft'),
            ('depreciation_date', '<=', today)
        ])

        for line in lines_to_post:
            asset = line.asset_id
            move_vals = {
                'date': line.depreciation_date,
                'ref': f'Khấu hao {asset.ten_tai_san} - {line.depreciation_date.strftime("%m/%Y")}',
                'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                'line_ids': [
                    (0, 0, {
                        'name': f'Chi phí khấu hao - {asset.ten_tai_san}',
                        'account_id': asset.account_depreciation_id.id,
                        'debit': line.amount,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': f'Hao mòn tài sản - {asset.ten_tai_san}',
                        'account_id': asset.account_asset_id.id,
                        'debit': 0.0,
                        'credit': line.amount,
                    }),
                ]
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post() # Ghi sổ ngay lập tức
            
            line.write({
                'state': 'posted',
                'move_id': move.id
            })