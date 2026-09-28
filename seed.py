import os
from datetime import datetime, date, timedelta
from app import create_app
from database import db
from models import User, RepairRequest, RepairImage, Comment, RequestStatus, ProblemType, UrgencyLevel, UserRole


def seed_data(reset=False):
    app = create_app()
    with app.app_context():
        if reset:
            print("🗑️ Dropping existing database tables...")
            db.drop_all()
        print("🔧 Creating database tables...")
        db.create_all()

        # ตรวจสอบว่ามีผู้ใช้อยู่แล้วหรือไม่
        if not reset and User.query.first():
            print("ℹ️ Database already has data. Skipping seed. (Use --reset to force re-seed)")
            return

        print("👤 Seeding Users...")
        # 1. Admin
        admin = User(
            username="admin",
            fullname="ดร.สมชาย บริหารงาน (หัวหน้าฝ่ายบริหารทั่วไป)",
            role=UserRole.ADMIN.value,
            email="admin@school.ac.th"
        )
        admin.set_password("admin123")

        # 2. Teachers
        teacher1 = User(
            username="teacher1",
            fullname="อาจารย์กานดา สอนดี (กลุ่มสาระวิทยาศาสตร์)",
            role=UserRole.TEACHER.value,
            email="kanda@school.ac.th"
        )
        teacher1.set_password("teacher123")

        teacher2 = User(
            username="teacher2",
            fullname="อาจารย์ประสิทธิ์ รักเรียน (กลุ่มสาระคอมพิวเตอร์)",
            role=UserRole.TEACHER.value,
            email="prasit@school.ac.th"
        )
        teacher2.set_password("teacher123")

        # 3. Technicians
        tech1 = User(
            username="tech1",
            fullname="นายช่างวิชัย ชำนาญการ (ช่างไฟฟ้า/แอร์)",
            role=UserRole.TECHNICIAN.value,
            email="wichai@school.ac.th"
        )
        tech1.set_password("tech123")

        tech2 = User(
            username="tech2",
            fullname="นายช่างสมปอง มือทอง (ช่างครุภัณฑ์/คอมพิวเตอร์)",
            role=UserRole.TECHNICIAN.value,
            email="sompong@school.ac.th"
        )
        tech2.set_password("tech123")

        db.session.add_all([admin, teacher1, teacher2, tech1, tech2])
        db.session.commit()

        print("📝 Seeding Repair Requests...")
        today = date.today()

        # ใบแจ้งซ่อม 1: รอรับเรื่อง (Pending)
        req1 = RepairRequest(
            request_no="RP-202609-001",
            user_id=teacher1.id,
            building="อาคาร 2 (อาคารวิทยาศาสตร์)",
            room="ห้อง 204",
            problem_type=ProblemType.AIRCON.value,
            description="แอร์ไม่เย็น ลมไม่ออก และมีน้ำหยดลงบนโต๊ะเรียนนักเรียนแถวหน้า",
            urgency=UrgencyLevel.HIGH.value,
            status=RequestStatus.PENDING.value,
            created_at=datetime.now() - timedelta(days=2)
        )

        # ใบแจ้งซ่อม 2: รับเรื่องแล้ว มอบหมายแล้ว (Accepted)
        req2 = RepairRequest(
            request_no="RP-202609-002",
            user_id=teacher2.id,
            building="อาคาร 4 (ศูนย์คอมพิวเตอร์)",
            room="Lab Com 1",
            problem_type=ProblemType.COMPUTER.value,
            description="จอคอมพิวเตอร์เปิดไม่ติด 2 เครื่อง (เครื่องเบอร์ 14 และ 15) ไฟสถานะไม่เข้า",
            urgency=UrgencyLevel.MEDIUM.value,
            status=RequestStatus.ACCEPTED.value,
            assigned_to=tech2.id,
            due_date=today + timedelta(days=3),
            created_at=datetime.now() - timedelta(days=3)
        )

        # ใบแจ้งซ่อม 3: กำลังดำเนินการ (In Progress)
        req3 = RepairRequest(
            request_no="RP-202609-003",
            user_id=teacher1.id,
            building="อาคาร 1 (อาคารอำนวยการ)",
            room="ห้อง 102 (ห้องพักครู)",
            problem_type=ProblemType.ELECTRICAL.value,
            description="หลอดไฟฟลูออเรสเซนต์กะพริบและมีเสียงดัง ได้กลิ่นไหม้เล็กน้อย",
            urgency=UrgencyLevel.HIGH.value,
            status=RequestStatus.IN_PROGRESS.value,
            assigned_to=tech1.id,
            due_date=today + timedelta(days=1),
            created_at=datetime.now() - timedelta(days=4)
        )

        # ใบแจ้งซ่อม 4: ซ่อมเสร็จแล้ว (Completed)
        req4 = RepairRequest(
            request_no="RP-202609-004",
            user_id=teacher2.id,
            building="อาคาร 3 (อาคารศิลปะและดนตรี)",
            room="ห้อง 305",
            problem_type=ProblemType.FURNITURE.value,
            description="ขาโต๊ะเรียนไม้โยก น็อตยึดหลุด 2 ตัว เสี่ยงจะหัก",
            urgency=UrgencyLevel.LOW.value,
            status=RequestStatus.COMPLETED.value,
            assigned_to=tech2.id,
            due_date=today - timedelta(days=1),
            completion_date=today - timedelta(days=1),
            cost=150.0,
            result="เสริมเหล็กฉากยึดขาโต๊ะและใส่น็อตตัวใหม่ ขันแน่นแข็งแรงทดสอบรับน้ำหนักแล้ว",
            created_at=datetime.now() - timedelta(days=7)
        )

        # ใบแจ้งซ่อม 5: ซ่อมเสร็จแล้ว (Completed)
        req5 = RepairRequest(
            request_no="RP-202609-005",
            user_id=teacher1.id,
            building="อาคาร 2 (อาคารวิทยาศาสตร์)",
            room="ห้องชีววิทยา 201",
            problem_type=ProblemType.AIRCON.value,
            description="แอร์มีกลิ่นอับชื้น เสียงพัดลมคอยล์เย็นดังมาก",
            urgency=UrgencyLevel.HIGH.value,
            status=RequestStatus.COMPLETED.value,
            assigned_to=tech1.id,
            due_date=today - timedelta(days=2),
            completion_date=today - timedelta(days=2),
            cost=1200.0,
            result="ทำการล้างแอร์เต็มระบบ ฉีดล้างแผงคอยล์ เติมน้ำยา R-32 และเปลี่ยนลูกปืนพัดลม",
            created_at=datetime.now() - timedelta(days=10)
        )

        db.session.add_all([req1, req2, req3, req4, req5])
        db.session.commit()

        print("💬 Seeding Comments...")
        c1 = Comment(
            repair_id=req1.id,
            user_id=teacher1.id,
            comment="ขอรบกวนตรวจสอบด่วนนะคะ เพราะห้องนี้ต้องใช้สอนทั้งวันเลยค่ะ",
            created_at=datetime.now() - timedelta(days=2, hours=-1)
        )
        c2 = Comment(
            repair_id=req1.id,
            user_id=admin.id,
            comment="รับทราบเรื่องแล้วครับ กำลังประสานงานช่างวิชัยให้เข้าตรวจสอบครับ",
            created_at=datetime.now() - timedelta(days=1)
        )

        c3 = Comment(
            repair_id=req2.id,
            user_id=tech2.id,
            comment="เบื้องต้นคาดว่าเป็นที่ปลั๊กพ่วงหรือสาย Power Adapter พรุ่งนี้ช่วงบ่ายจะนำมิเตอร์ไปวัดไฟครับ",
            created_at=datetime.now() - timedelta(days=2)
        )

        c4 = Comment(
            repair_id=req3.id,
            user_id=tech1.id,
            comment="ตัดไฟเบรกเกอร์วงจรห้อง 102 ชั่วคราวแล้ว กำลังเบิกบัลลาสต์และสตาร์ตเตอร์ตัวใหม่จากห้องพัสดุครับ",
            created_at=datetime.now() - timedelta(days=1)
        )

        db.session.add_all([c1, c2, c3, c4])
        db.session.commit()

        print("📸 Seeding Sample Images...")
        from PIL import Image, ImageDraw
        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'repairs')
        os.makedirs(upload_dir, exist_ok=True)

        samples = [
            ("aircon_before.jpg", "ภาพก่อนซ่อม: แอร์มีน้ำหยด", (220, 53, 69)),
            ("aircon_after.jpg", "ภาพหลังซ่อม: ล้างแอร์เสร็จเรียบร้อย", (40, 167, 69)),
            ("pc_before.jpg", "ภาพก่อนซ่อม: จอดำ เปิดไม่ติด", (108, 117, 125)),
            ("lamp_before.jpg", "ภาพก่อนซ่อม: หลอดไฟเสีย กะพริบ", (255, 193, 7)),
            ("table_after.jpg", "ภาพหลังซ่อม: เสริมฉากเหล็กขันแน่น", (23, 162, 184))
        ]

        for filename, text, color in samples:
            file_path = os.path.join(upload_dir, filename)
            img = Image.new('RGB', (600, 400), color=color)
            draw = ImageDraw.Draw(img)
            draw.rectangle([20, 20, 580, 380], outline=(255, 255, 255), width=3)
            draw.text((40, 180), text, fill=(255, 255, 255))
            draw.text((40, 220), "School Repair System Sample Image", fill=(240, 240, 240))
            img.save(file_path, "JPEG")

        db.session.add(RepairImage(repair_id=req1.id, image_type="before", image_path="uploads/repairs/aircon_before.jpg"))
        db.session.add(RepairImage(repair_id=req2.id, image_type="before", image_path="uploads/repairs/pc_before.jpg"))
        db.session.add(RepairImage(repair_id=req3.id, image_type="before", image_path="uploads/repairs/lamp_before.jpg"))
        db.session.add(RepairImage(repair_id=req4.id, image_type="after", image_path="uploads/repairs/table_after.jpg"))
        db.session.add(RepairImage(repair_id=req5.id, image_type="before", image_path="uploads/repairs/aircon_before.jpg"))
        db.session.add(RepairImage(repair_id=req5.id, image_type="after", image_path="uploads/repairs/aircon_after.jpg"))
        db.session.commit()

        print("✅ Database seeding completed successfully!")
        print("---------------------------------------------------------")
        print("Demo Accounts:")
        print("  1. Admin:       Username: admin     / Password: admin123")
        print("  2. Teacher 1:   Username: teacher1  / Password: teacher123")
        print("  3. Teacher 2:   Username: teacher2  / Password: teacher123")
        print("  4. Technician 1:Username: tech1     / Password: tech123")
        print("  5. Technician 2:Username: tech2     / Password: tech123")
        print("---------------------------------------------------------")


if __name__ == '__main__':
    import sys
    do_reset = '--reset' in sys.argv
    seed_data(reset=do_reset)
