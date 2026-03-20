# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DnuAssetDepreciationLine(models.Model):
    _name = 'dnu.asset.depreciation.line'
    _description = 'Dòng khấu hao tài sản DNU'

    asset_id = fields.Many2one('dnu.asset', string='Tài sản', required=True)
    date = fields.Date(string='Ngày', required=True)
    amount = fields.Monetary(string='Số tiền', required=True)
    currency_id = fields.Many2one('res.currency', related='asset_id.currency_id', store=True, readonly=True)
    state = fields.Selection([('draft', 'Nháp'), ('confirmed', 'Đã xác nhận'), ('cancel', 'Hủy')], string='Trạng thái', default='draft')
    account_move_id = fields.Many2one('account.move', string='Bút toán khấu hao')

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            move_vals = {
                'date': rec.date,
                'ref': 'Khấu hao %s' % (rec.asset_id.name or ''),
                'move_type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': 'Chi phí khấu hao',
                        'account_id': rec.asset_id.account_id.id,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'currency_id': rec.currency_id.id,
                    }),
                    (0, 0, {
                        'name': 'Tích lũy khấu hao',
                        'account_id': rec.asset_id.account_id.id,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'currency_id': rec.currency_id.id,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            rec.write({'account_move_id': move.id, 'state': 'confirmed'})
            rec.asset_id.write({'depreciated_amount': rec.asset_id.depreciated_amount + rec.amount})
