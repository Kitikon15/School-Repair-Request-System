import os
import uuid
from datetime import datetime
from functools import wraps
from flask import current_app, abort, flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from database import db
from models import RepairRequest


# ==============================================================
# 3.2: รหัสใบแจ้งซ่อมอัตโนมัติ (Format: RP-YYYYMM-XXX)
# ==============================================================

def generate_request_no() -> str:
    """
    สร้างรหัสใบแจ้งซ่อมอัตโนมัติ
    รูปแบบ: RP-YYYYMM-XXX เช่น RP-202609-001
    โดยใช้ datetime และ str.zfill()
    """
    now = datetime.now()
    year_month = now.strftime("%Y%m")
    prefix = f"RP-{year_month}-"

    # ค้นหาใบแจ้งซ่อมล่าสุดของเดือนนี้
    latest_request = RepairRequest.query.filter(
        RepairRequest.request_no.like(f"{prefix}%")
    ).order_by(RepairRequest.id.desc()).first()

    if latest_request and latest_request.request_no:
        try:
            # ดึงลำดับตัวเลข 3 หลักท้าย
            last_seq = int(latest_request.request_no.split("-")[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1

    # ใช้ str.zfill() เพื่อเติมเลข 0 ด้านหน้าให้ครบ 3 หลัก
    formatted_seq = str(next_seq).zfill(3)
    return f"{prefix}{formatted_seq}"


# ==============================================================
# การจัดการและตรวจสอบไฟล์อัปโหลดอย่างปลอดภัย
# ==============================================================

def allowed_file(filename: str) -> bool:
    """ตรวจสอบนามสกุลไฟล์ที่อนุญาต"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file_storage, subfolder: str = "") -> str:
    """
    บันทึกไฟล์อัปโหลดอย่างปลอดภัย:
    1. ใช้ secure_filename
    2. เติม UUID ป้องกันการเขียนทับ (Collision) และ Path Traversal
    3. บันทึกและคืนค่า relative path สำหรับแสดงผลบนเว็บ
    """
    if not file_storage or not file_storage.filename:
        return ""

    original_filename = secure_filename(file_storage.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    unique_filename = f"{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}.{ext}"

    target_dir = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        target_dir = os.path.join(target_dir, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    file_path = os.path.join(target_dir, unique_filename)
    file_storage.save(file_path)

    # Return relative path for web access e.g., 'uploads/xxx.jpg' or 'uploads/subfolder/xxx.jpg'
    rel_path = f"uploads/{subfolder}/{unique_filename}" if subfolder else f"uploads/{unique_filename}"
    return rel_path.replace("\\", "/")


# ==============================================================
# Role-based Access Control Decorators
# ==============================================================

def role_required(*allowed_roles):
    """Decorator ตรวจสอบบทบาทผู้ใช้งาน"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def tech_or_admin_required(f):
    return role_required('technician', 'admin')(f)


# ==============================================================
# Template Filters & Formatters
# ==============================================================

def format_thai_date(value, include_time: bool = False) -> str:
    """แปลงวันที่เป็นรูปแบบไทย พ.ศ."""
    if not value:
        return "-"
    
    thai_months = [
        "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
        "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."
    ]
    
    day = value.day
    month = thai_months[value.month]
    year = value.year + 543  # พุทธศักราช
    
    if include_time and hasattr(value, 'hour'):
        return f"{day} {month} {year} เวลา {value.strftime('%H:%M')} น."
    return f"{day} {month} {year}"
