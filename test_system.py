import unittest
from datetime import date, datetime
from app import create_app
from database import db
from models import (
    User, RepairRequest, RequestStatus, ProblemType, UrgencyLevel, UserRole,
    RepairRequestDomain
)
from helpers import generate_request_no


from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class TestSchoolRepairSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create test users
            admin = User(username='test_admin', fullname='Test Admin', role=UserRole.ADMIN.value, email='admin@test.com')
            admin.set_password('admin123')

            teacher = User(username='test_teacher', fullname='Test Teacher', role=UserRole.TEACHER.value, email='teacher@test.com')
            teacher.set_password('teacher123')

            tech = User(username='test_tech', fullname='Test Tech', role=UserRole.TECHNICIAN.value, email='tech@test.com')
            tech.set_password('tech123')

            db.session.add_all([admin, teacher, tech])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def test_domain_oop_workflow(self):
        """ทดสอบ Domain Dataclass และ State Transition ตาม Section 3"""
        req = RepairRequestDomain(
            id=1,
            request_no="RP-202609-001",
            user_id=10,
            building="อาคาร 3",
            room="301",
            problem_type=ProblemType.AIRCON,
            description="แอร์ไม่เย็น มีเสียงดัง",
            urgency="high"
        )
        self.assertEqual(req.status, RequestStatus.PENDING)

        # 1. Assign to technician
        req.assign_to(technician_id=5, due_date=date(2026, 9, 25))
        self.assertEqual(req.status, RequestStatus.ACCEPTED)
        self.assertEqual(req.assigned_to, 5)

        # 2. Start repair
        req.start_repair()
        self.assertEqual(req.status, RequestStatus.IN_PROGRESS)

        # 3. Complete repair
        req.complete_repair(cost=1500.0, result="ล้างแอร์และเติมสารทำความเย็น")
        self.assertEqual(req.status, RequestStatus.COMPLETED)
        self.assertEqual(req.cost, 1500.0)

    def test_invalid_state_transition(self):
        """ทดสอบการป้องกันข้ามขั้นตอน (State Transition Guard)"""
        req = RepairRequestDomain(
            id=2,
            request_no="RP-202609-002",
            user_id=10,
            building="อาคาร 1",
            room="101",
            problem_type=ProblemType.ELECTRICAL,
            description="ไฟดับ"
        )
        # ยังไม่ได้รับเรื่อง แต่พยายามเริ่มซ่อมทันที -> ต้อง Raise ValueError
        with self.assertRaises(ValueError):
            req.start_repair()

    def test_generate_request_no(self):
        """ทดสอบฟังก์ชันสร้างรหัสอัตโนมัติ RP-YYYYMM-XXX (โจทย์ 3.2)"""
        with self.app.app_context():
            no1 = generate_request_no()
            self.assertTrue(no1.startswith("RP-"))
            self.assertEqual(len(no1.split("-")), 3)

    def test_login_and_dashboard(self):
        """ทดสอบระบบล็อกอินและสิทธิ์การเข้าถึง (โจทย์ 5.1 & 5.2)"""
        # Login with correct password
        response = self.client.post('/login', data={
            'username': 'test_admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('แดชบอร์ดสรุปงานแจ้งซ่อม'.encode('utf-8'), response.data)

        # Dashboard access
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn('สถิติแยกตามหมวดหมู่'.encode('utf-8'), dash_res.data)

    def test_repair_create_and_export_csv(self):
        """ทดสอบการสร้างใบแจ้งซ่อมและส่งออก CSV (โจทย์ 5.5)"""
        # Login as teacher
        self.client.post('/login', data={
            'username': 'test_teacher',
            'password': 'teacher123'
        })

        # Create repair request
        res = self.client.post('/repair/create', data={
            'building': 'อาคาร 4',
            'room': 'Lab 1',
            'problem_type': 'computer',
            'urgency': 'high',
            'description': 'เครื่องเปิดไม่ติด'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('เครื่องเปิดไม่ติด'.encode('utf-8'), res.data)

        # Export CSV
        csv_res = self.client.get('/repair/export/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.headers['Content-Type'], 'text/csv; charset=utf-8-sig')


if __name__ == '__main__':
    unittest.main()
