from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import db


# ==============================================================
# Enum Classes (Type Safety & Validation)
# ==============================================================

class RequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ProblemType(str, Enum):
    ELECTRICAL = "electrical"
    FURNITURE = "furniture"
    COMPUTER = "computer"
    AIRCON = "aircon"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    TECHNICIAN = "technician"


# ==============================================================
# Domain Dataclass (Pure OOP Implementation according to Section 3)
# ==============================================================

@dataclass
class RepairRequestDomain:
    """คลาสแทนใบแจ้งซ่อมตามหลักการเชิงวัตถุ (OOAD) พร้อม Type Hints"""
    id: int
    request_no: str
    user_id: int
    building: str
    room: str
    problem_type: ProblemType
    description: str
    urgency: str = "medium"
    status: RequestStatus = RequestStatus.PENDING
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    completion_date: Optional[date] = None
    cost: Optional[float] = None
    result: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def assign_to(self, technician_id: int, due_date: date) -> None:
        """มอบหมายงานให้เจ้าหน้าที่ซ่อมบำรุง"""
        self.assigned_to = technician_id
        self.due_date = due_date
        self.status = RequestStatus.ACCEPTED

    def start_repair(self) -> None:
        """เริ่มดำเนินการซ่อม (ต้องได้รับเรื่องหรือมอบหมายก่อน)"""
        if self.status != RequestStatus.ACCEPTED:
            raise ValueError("Cannot start repair: Request not accepted yet")
        self.status = RequestStatus.IN_PROGRESS

    def complete_repair(self, cost: float, result: str) -> None:
        """บันทึกผลการซ่อมและค่าใช้จ่าย"""
        if self.status != RequestStatus.IN_PROGRESS:
            raise ValueError("Cannot complete repair: Request is not in progress")
        self.cost = cost
        self.result = result
        self.completion_date = date.today()
        self.status = RequestStatus.COMPLETED


# ==============================================================
# SQLAlchemy ORM Models (Database Mapping)
# ==============================================================

class User(UserMixin, db.Model):
    """ตารางผู้ใช้งานระบบ (users)"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'technician'
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    created_repairs = db.relationship('RepairRequest', foreign_keys='RepairRequest.user_id', backref='reporter', lazy=True, cascade='all, delete-orphan')
    assigned_repairs = db.relationship('RepairRequest', foreign_keys='RepairRequest.assigned_to', backref='technician', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """แปลงรหัสผ่านเป็น Hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """ตรวจสอบรหัสผ่าน"""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @property
    def is_technician(self) -> bool:
        return self.role == UserRole.TECHNICIAN.value

    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER.value

    @property
    def role_label(self) -> str:
        labels = {
            'admin': 'ผู้ดูแลระบบ (Admin)',
            'teacher': 'ครู / บุคลากร (Teacher)',
            'technician': 'เจ้าหน้าที่ซ่อม (Technician)'
        }
        return labels.get(self.role, self.role)

    @property
    def role_badge_class(self) -> str:
        badges = {
            'admin': 'badge bg-danger',
            'teacher': 'badge bg-primary',
            'technician': 'badge bg-warning text-dark'
        }
        return badges.get(self.role, 'badge bg-secondary')

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class RepairRequest(db.Model):
    """ตารางใบแจ้งซ่อม (repair_requests)"""
    __tablename__ = 'repair_requests'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_no = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    problem_type = db.Column(db.String(30), nullable=False)  # 'electrical', 'furniture', 'computer', 'aircon', 'other'
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='medium', nullable=False)  # 'low', 'medium', 'high'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'accepted', 'in_progress', 'completed'
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    completion_date = db.Column(db.Date, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    result = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    images = db.relationship('RepairImage', backref='repair', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='repair', lazy=True, cascade='all, delete-orphan', order_by='Comment.created_at.asc()')

    # Domain methods
    def assign_to_tech(self, technician_id: int, due_date_val: Optional[date] = None) -> None:
        self.assigned_to = technician_id
        if due_date_val:
            self.due_date = due_date_val
        self.status = RequestStatus.ACCEPTED.value

    def start_repair_work(self) -> None:
        if self.status != RequestStatus.ACCEPTED.value and self.status != RequestStatus.PENDING.value:
            raise ValueError("สามารถเริ่มซ่อมได้เฉพาะรายการที่อยู่ในสถานะรอรับเรื่องหรือรับเรื่องแล้ว")
        self.status = RequestStatus.IN_PROGRESS.value

    def complete_repair_work(self, cost_amount: float, result_text: str) -> None:
        self.cost = cost_amount
        self.result = result_text
        self.completion_date = date.today()
        self.status = RequestStatus.COMPLETED.value

    # UI Helpers
    @property
    def status_label(self) -> str:
        mapping = {
            'pending': 'รอรับเรื่อง',
            'accepted': 'รับเรื่องแล้ว',
            'in_progress': 'กำลังดำเนินการ',
            'completed': 'ซ่อมเสร็จสิ้น'
        }
        return mapping.get(self.status, self.status)

    @property
    def status_badge_class(self) -> str:
        mapping = {
            'pending': 'badge bg-secondary',
            'accepted': 'badge bg-info text-dark',
            'in_progress': 'badge bg-warning text-dark',
            'completed': 'badge bg-success'
        }
        return mapping.get(self.status, 'badge bg-light text-dark')

    @property
    def problem_type_label(self) -> str:
        mapping = {
            'electrical': 'ระบบไฟฟ้า',
            'furniture': 'ครุภัณฑ์ / เฟอร์นิเจอร์',
            'computer': 'คอมพิวเตอร์และอุปกรณ์',
            'aircon': 'เครื่องปรับอากาศ',
            'other': 'อื่นๆ'
        }
        return mapping.get(self.problem_type, self.problem_type)

    @property
    def problem_type_icon(self) -> str:
        mapping = {
            'electrical': 'bi-lightning-charge-fill text-warning',
            'furniture': 'bi-box-seam-fill text-secondary',
            'computer': 'bi-pc-display text-primary',
            'aircon': 'bi-snow text-info',
            'other': 'bi-tools text-dark'
        }
        return mapping.get(self.problem_type, 'bi-wrench')

    @property
    def urgency_label(self) -> str:
        mapping = {
            'low': 'ต่ำ (ไม่เร่งด่วน)',
            'medium': 'ปานกลาง',
            'high': 'สูง (เร่งด่วนมาก)'
        }
        return mapping.get(self.urgency, self.urgency)

    @property
    def urgency_badge_class(self) -> str:
        mapping = {
            'low': 'badge bg-light text-secondary border',
            'medium': 'badge bg-warning text-dark',
            'high': 'badge bg-danger'
        }
        return mapping.get(self.urgency, 'badge bg-secondary')

    @property
    def before_images(self) -> List['RepairImage']:
        return [img for img in self.images if img.image_type == 'before']

    @property
    def after_images(self) -> List['RepairImage']:
        return [img for img in self.images if img.image_type == 'after']

    def __repr__(self):
        return f"<RepairRequest {self.request_no} - {self.status}>"


class RepairImage(db.Model):
    """ตารางรูปภาพประกอบการซ่อม (repair_images)"""
    __tablename__ = 'repair_images'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    repair_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id', ondelete='CASCADE'), nullable=False)
    image_type = db.Column(db.String(20), nullable=False)  # 'before', 'after'
    image_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def image_type_label(self) -> str:
        return 'ก่อนซ่อม' if self.image_type == 'before' else 'หลังซ่อม'

    def __repr__(self):
        return f"<RepairImage {self.id} ({self.image_type}) for Repair #{self.repair_id}>"


class Comment(db.Model):
    """ตารางความคิดเห็นและประวัติบันทึก (comments)"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    repair_id = db.Column(db.Integer, db.ForeignKey('repair_requests.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Comment {self.id} by User #{self.user_id}>"
