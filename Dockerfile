FROM odoo:15.0

# Chuyển sang quyền root để cài đặt thư viện hệ thống
USER root

# LƯU Ý KỸ THUẬT QUAN TRỌNG VỀ PDF (WKHTMLTOPDF):
# Image odoo:15.0 gốc ĐÃ ĐƯỢC CÀI ĐẶT SẴN wkhtmltopdf bản vá lõi QT (phiên bản 0.12.5). 
# NẾU chạy lệnh "apt-get install wkhtmltopdf" ở đây, Ubuntu sẽ đè một bản wkhtmltopdf 
# rút gọn lên bản của Odoo, dẫn đến việc khi in Báo cáo PDF Margin/Header/Footer sẽ bị vỡ nát!
# Do đó, ta bảo vệ wkhtmltopdf gốc và chỉ cài thêm các FONT hệ thống để Báo cáo tiếng Việt không bị lỗi font chữ.
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fontconfig \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python phục vụ thuật toán QR Code
RUN pip3 install --no-cache-dir qrcode pillow

# Hạ quyền lại về user odoo để đảm bảo an ninh hệ thống file
USER odoo
