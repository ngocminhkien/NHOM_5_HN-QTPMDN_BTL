# -*- coding: utf-8 -*-
{
    'name': "Quản lý Tài sản Doanh nghiệp (Nhóm 5)",
    'summary': """
        Hệ thống Quản lý Tài sản tích hợp HRM và Kế toán
        Bài tập lớn môn: Hội nhập và Quản trị phần mềm doanh nghiệp
    """,

    'description': """
        Module quản lý tài sản được nâng cấp và tích hợp:
        1. Tích hợp dữ liệu Nhân sự (HRM):
           - Sử dụng danh sách Nhân viên (hr.employee) và Phòng ban (hr.department) làm dữ liệu gốc.
        
        2. Tích hợp dữ liệu Kế toán (Accounting):
           - Tự động tạo bút toán khấu hao và thanh lý tài sản.
        
        3. Quy trình phê duyệt (Workflow):
           - Luồng phê duyệt mua sắm và thanh lý có sự tham gia của bộ phận Tài chính.
    """,

    'author': "Nhóm 5 - FIT DNU",
    'website': "https://github.com/FIT-DNU/Business-Internship",
    
    # Categories can be used to filter modules in modules listing
    'category': 'Operations/Assets',
    'version': '1.0',

    # --- PHẦN1: DEPENDS (SỰ PHỤ THUỘC) ---
    # Bắt buộc phải có 'hr' và 'account' để code không bị lỗi khi liên kết
    'depends': [
        'base',
        'mail',           # Module Nhân sự gốc
        'hr',      # Module Kế toán gốc
        'account',         # Module Chat/Lịch sử
    ],

    # --- PHẦN2: DATA (CÁC FILE GIAO DIỆN) ---
    # Odoo sẽ nạp các file này theo thứ tự. 
    
    'data': [
        # 1. Phân quyền (Bắt buộc nạp đầu tiên)
        'security/ir.model.access.csv',
        
        'views/dashboard_borrowing.xml',
        'views/dashboard_overview.xml',
        'views/danh_muc_tai_san.xml',
        'views/don_muon_tai_san.xml',
        'views/kiem_ke_tai_san.xml',
        'views/lich_su_khau_hao.xml',
        'views/luan_chuyen_tai_san.xml',
        
        'views/muon_tra_tai_san.xml',
        'views/phan_bo_tai_san.xml',
        'views/tai_san.xml',
        'views/thanh_ly_tai_san.xml',
        'views/menu.xml',
    ],
    
   
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}