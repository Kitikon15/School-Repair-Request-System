# 📝 เฉลยและแนวทางการตอบใบงานปฏิบัติการ: ระบบแจ้งซ่อมภายในโรงเรียน (Python Edition)
**การวิเคราะห์ออกแบบระบบ (OOAD) และการพัฒนาด้วย Python**  
*Tech Stack: Python 3.10+ | SQLite | Flask | SweetAlert2 | Bootstrap 5*

---

## 📋 ส่วนที่ 1: ความต้องการของระบบ (System Requirements)

### 📌 คำถามที่ 1.1: จงระบุ User Roles ทั้ง 3 ประเภท และอธิบายสิทธิ์การเข้าถึงข้อมูลของแต่ละบทบาท
**แนวคำตอบ:**
1. **ผู้ดูแลระบบ (Admin):**
   - **สิทธิ์:** มีสิทธิ์เข้าถึงข้อมูลและฟังก์ชันทั้งหมดของระบบ (Full Access)
   - **หน้าที่หลัก:**
     - ตรวจสอบรายการแจ้งซ่อมทั้งหมดในโรงเรียน
     - มอบหมายงาน (Assign) ให้กับเจ้าหน้าที่ช่าง พร้อมกำหนดวันแล้วเสร็จ (Due Date)
     - จัดการผู้ใช้งานในระบบ (เพิ่ม, แก้ไข, ลบ, เปลี่ยนแปลงสิทธิ์)
     - ดูสรุปสถิติภาพรวมบน Dashboard และส่งออกรายงานเป็น CSV / สั่งพิมพ์ใบงาน
     - สามารถปรับปรุงสถานะหรือลบรายการแจ้งซ่อมได้
2. **ครู / บุคลากร (Teacher / Staff):**
   - **สิทธิ์:** มีสิทธิ์แจ้งซ่อม ติดตามงาน และแสดงความคิดเห็น
   - **หน้าที่หลัก:**
     - สร้างใบแจ้งซ่อมใหม่ ระบุอาคาร ห้อง ประเภทปัญหา ความเร่งด่วน และแนบรูปภาพก่อนซ่อม
     - ดูรายการแจ้งซ่อมทั้งหมดเพื่อไม่ให้แจ้งซ้ำ และติดตามสถานะเฉพาะรายการที่ตนเองแจ้ง
     - เขียนความคิดเห็นหรือตอบข้อซักถามในใบแจ้งซ่อม
     - พิมพ์เอกสารใบแจ้งซ่อม (A4 / PDF)
3. **เจ้าหน้าที่ซ่อม (Technician):**
   - **สิทธิ์:** มีสิทธิ์ดูงานที่ได้รับมอบหมายและบันทึกผลการปฏิบัติงาน
   - **หน้าที่หลัก:**
     - ดูรายการงานซ่อมที่ตนเองรับผิดชอบบน Dashboard
     - เปลี่ยนสถานะงานเป็น "กำลังดำเนินการ (In Progress)" เมื่อเริ่มปฏิบัติงาน
     - บันทึกผลการซ่อม รายละเอียดการแก้ไข ค่าใช้จ่าย และแนบรูปภาพหลังซ่อมเสร็จ เพื่อเปลี่ยนสถานะเป็น "ซ่อมเสร็จสิ้น (Completed)"
     - เขียนบันทึกข้อความสอบถามหรือแจ้งความคืบหน้าให้ผู้แจ้งซ่อมทราบ

---

### 📌 คำถามที่ 1.2: จงสกัดคำนาม (Noun Extraction) เพื่อระบุคลาสที่ควรสร้างและไม่ควรสร้าง
**แนวคำตอบ:**

| ประเภทคำนาม | รายการคำนาม | เหตุผลในการวิเคราะห์ |
| :--- | :--- | :--- |
| **คลาสที่ควรสร้าง (Entity / Domain Classes)** | `User` (ผู้ใช้งาน) | เป็นเอนทิตีหลักที่มีตัวตน มี attributes เช่น username, password, role และมีความสัมพันธ์กับงานซ่อม |
| | `RepairRequest` (ใบแจ้งซ่อม) | เป็นแกนหลักของระบบ (Core Domain) มีวงจรชีวิต (Lifecycle), สถานะ (Status), และพฤติกรรม (Behavior) เช่น การมอบหมาย, การซ่อม |
| | `RepairImage` (รูปภาพประกอบ) | มีความสัมพันธ์แบบ 1:N กับใบแจ้งซ่อม และจำเป็นต้องเก็บ path, ประเภทภาพ (ก่อน/หลัง) และวันที่อัปโหลด |
| | `Comment` (ความคิดเห็น) | มีความสัมพันธ์แบบ 1:N กับใบแจ้งซ่อม เก็บประวัติการสนทนาและ timestamp |
| **คำนามที่ไม่ควรสร้างเป็นคลาส (Attributes / Values)** | `request_no`, `building`, `room`, `cost`, `result` | เป็นเพียงคุณลักษณะ (Attributes) ของคลาส `RepairRequest` |
| | `status`, `problem_type`, `urgency`, `role` | ควรสร้างเป็น **Enum** แทนการสร้างเป็นคลาสทั่วไป เพื่อจำกัดขอบเขตค่า (Type Safety) |
| | `Dashboard`, `CSV`, `PDF` | เป็นส่วนของการแสดงผล (View / Presentation) หรือฟังก์ชันยูทิลิตี ไม่ใช่ข้อมูลธุรกิจ (Domain Model) |

---

## 🏗️ ส่วนที่ 2: การออกแบบฐานข้อมูล (Database Design)

### 📌 คำถามที่ 2.1: คำสั่ง SQL CREATE TABLE สำหรับตาราง `repair_requests`
```sql
CREATE TABLE repair_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_no TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    building TEXT NOT NULL,
    room TEXT NOT NULL,
    problem_type TEXT NOT NULL CHECK(problem_type IN ('electrical', 'furniture', 'computer', 'aircon', 'other')),
    description TEXT NOT NULL,
    urgency TEXT NOT NULL DEFAULT 'medium' CHECK(urgency IN ('low', 'medium', 'high')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'in_progress', 'completed')),
    assigned_to INTEGER,
    due_date DATE,
    completion_date DATE,
    cost REAL,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
);
```

---

### 📌 คำถามที่ 2.2: อธิบายความสัมพันธ์ (Relationships) และเหตุผลที่แยกตาราง `repair_images`
**แนวคำตอบ:**
1. **ความสัมพันธ์ระหว่างตาราง:**
   - `users` (1) ── (N) `repair_requests` (ผู้ใช้ 1 คน สามารถแจ้งซ่อมได้หลายใบ)
   - `users` (1) ── (N) `repair_requests` [assigned_to] (ช่าง 1 คน สามารถรับผิดชอบได้หลายใบ)
   - `repair_requests` (1) ── (N) `repair_images` (ใบแจ้งซ่อม 1 ใบ มีรูปภาพประกอบได้หลายรูป)
   - `repair_requests` (1) ── (N) `comments` (ใบแจ้งซ่อม 1 ใบ มีความคิดเห็นได้หลายข้อความ)
   - `users` (1) ── (N) `comments` (ผู้ใช้ 1 คน สามารถเขียนความคิดเห็นได้หลายข้อความ)

2. **เหตุผลที่ต้องแยกตาราง `repair_images` ออกจาก `repair_requests`:**
   - **หลักการ Normalization (First Normal Form - 1NF):** 1NF กำหนดว่าข้อมูลในแต่ละ attribute ต้องเป็นค่าเดี่ยว (Atomic Value) ไม่ควรมี Repeating Groups หากเก็บรูปไว้ในตารางหลัก จะต้องสร้างคอลัมน์ เช่น `image1, image2, image3...` ซึ่งจำกัดจำนวนและเกิดค่าว่าง (NULL) สิ้นเปลืองพื้นที่
   - **ความยืดหยุ่น (Flexibility):** รองรับการแนบภาพได้ไม่จำกัดจำนวน ทั้งภาพก่อนซ่อม (Before) และหลังซ่อม (After)
   - **ประสิทธิภาพ (Performance):** การแยกตารางทำให้ตารางหลัก `repair_requests` มีขนาดแถวคงที่ ค้นหาและทำดัชนีได้รวดเร็ว

---

## 💻 ส่วนที่ 3: การพัฒนาด้วย Python 3.10+ (Python Implementation)

### 📌 คำถามที่ 3.1: การนำหลักการ OOP มาประยุกต์ใช้ใน Python
**แนวคำตอบ:**
1. **Encapsulation ใน Python vs PHP:**
   - ใน PHP มี keyword ระดับการเข้าถึงชัดเจน (`private`, `protected`, `public`)
   - ใน Python ใช้หลัก "We are all consenting adults" โดยใช้ Convention คือ ขีดล่างเดี่ยว `_attribute` สำหรับ internal use หรือดับเบิลขีดล่าง `__attribute` สำหรับ Name Mangling และควบคุมการอ่าน-เขียนผ่าน Property Decorator (`@property`, `@setter`) เพื่อปกป้องสถานะภายในของออบเจกต์
2. **เหตุใดจึงใช้ `Optional[int]` และ `Optional[date]` (Nullable Types):**
   - ในช่วงเริ่มต้นของการแจ้งซ่อม ฟิลด์บางตัวจะ **ยังไม่มีค่า** เช่น `assigned_to` (ยังไม่มีช่างรับผิดชอบ), `due_date`, `cost`, `completion_date` (ยังไม่ได้เริ่มหรือยังซ่อมไม่เสร็จ)
   - การกำหนด `Optional[T]` (หรือ `T | None` ใน Python 3.10+) ช่วยให้ Static Type Checker (mypy) และ IDE รู้ว่าตัวแปรนี้อาจเป็น `None` ได้ ป้องกันข้อผิดพลาด `AttributeError` หรือ `TypeError` ในระหว่างรันไทม์
3. **`@dataclass` ช่วยลดโค้ดซ้ำซ้อนอย่างไร:**
   - สร้างเมธอดพื้นฐานให้อัตโนมัติ เช่น `__init__()`, `__repr__()`, `__eq__()` จากคลาสแอตทริบิวต์ที่กำหนด type hint
   - ช่วยลด Boilerplate Code ที่ต้องเขียน `self.x = x` ซ้ำๆ ในคอนสตรักเตอร์ ทำให้โค้ดสะอาด สั้นกระชับ และอ่านเข้าใจง่าย

---

### 📌 คำถามที่ 3.2: ฟังก์ชันสร้างรหัสใบแจ้งซ่อมอัตโนมัติ (RP-YYYYMM-XXX)
```python
from datetime import datetime

def generate_request_no() -> str:
    now = datetime.now()
    year_month = now.strftime("%Y%m")
    prefix = f"RP-{year_month}-"
    
    # ค้นหารายการล่าสุดของเดือนปัจจุบันจากฐานข้อมูล
    latest = RepairRequest.query.filter(
        RepairRequest.request_no.like(f"{prefix}%")
    ).order_by(RepairRequest.id.desc()).first()
    
    if latest and latest.request_no:
        try:
            last_seq = int(latest.request_no.split("-")[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1
        
    return f"{prefix}{str(next_seq).zfill(3)}"
```

---

### 📌 คำถามที่ 3.3: อธิบาย State Transition และ State Pattern
**แนวคำตอบ:**
- **State Transition:** ลำดับสถานะต้องเป็นไปตามขั้นตอน:  
  `pending (รอรับเรื่อง) ➔ accepted (รับเรื่องแล้ว) ➔ in_progress (กำลังดำเนินการ) ➔ completed (ซ่อมเสร็จ)`
- **เหตุผลที่ต้องมีเงื่อนไขตรวจสอบใน `start_repair()`:**
  - ป้องกันการดำเนินงานข้ามขั้นตอน เช่น ช่างจะเริ่มงานไม่ได้หากงานนั้นยังไม่ได้รับการอนุมัติ/มอบหมาย (`accepted`)
  - สอดคล้องกับหลักการ **State Pattern** และ **Domain-Driven Design (Invariants Enforcement)** ที่อ็อบเจกต์ต้องควบคุมความถูกต้องของสถานะตนเองเสมอ ไม่อนุญาตให้ภายนอกแก้ไขค่าโดยตรงโดยไม่ผ่าน Business Logic

---

## 🎨 ส่วนที่ 4: การออกแบบอินเทอร์เฟซ (UI/UX)

### 📌 คำถามที่ 4.1: โค้ด Flask Route `/repair/create` (GET/POST)
```python
@app.route('/repair/create', methods=['GET', 'POST'])
@login_required
def repair_create():
    if request.method == 'POST':
        building = request.form.get('building', '').strip()
        room = request.form.get('room', '').strip()
        problem_type = request.form.get('problem_type', '').strip()
        urgency = request.form.get('urgency', 'medium').strip()
        description = request.form.get('description', '').strip()

        if not (building and room and problem_type and description):
            flash('กรุณากรอกข้อมูลสำคัญให้ครบถ้วน', 'danger')
            return render_template('repair_create.html')

        new_request_no = generate_request_no()
        repair = RepairRequest(
            request_no=new_request_no,
            user_id=current_user.id,
            building=building,
            room=room,
            problem_type=problem_type,
            urgency=urgency,
            description=description,
            status=RequestStatus.PENDING.value
        )
        db.session.add(repair)
        db.session.flush()

        # บันทึกรูปภาพก่อนซ่อม
        files = request.files.getlist('before_images')
        for file in files:
            if file and allowed_file(file.filename):
                path = save_uploaded_file(file, subfolder='repairs')
                if path:
                    db.session.add(RepairImage(repair_id=repair.id, image_type='before', image_path=path))

        db.session.commit()
        flash(f'แจ้งซ่อมสำเร็จ รหัส {new_request_no}', 'success')
        return redirect(url_for('repair_detail', id=repair.id))

    return render_template('repair_create.html')
```

---

## 🚀 ส่วนที่ 5: สรุปโจทย์ฝึกปฏิบัติ (Coding Exercise Implementation)

| ข้อที่ | หัวข้อ | การนำไปใช้จริงในโปรเจกต์นี้ |
| :--- | :--- | :--- |
| **5.1** | ระบบ Login + Flask-Login | อยู่ใน `app.py` ฟังก์ชัน `login()`, `logout()` พร้อม `UserMixin`, `@login_required` และ Role Decorator |
| **5.2** | Dashboard สถิติ SQLAlchemy | ฟังก์ชัน `dashboard()` ใน `app.py` ใช้ Query กรอง `status`, นับรวมประเภทปัญหา และแสดงใน `templates/dashboard.html` |
| **5.3** | ระบบอัปโหลดรูปภาพปลอดภัย | อยู่ใน `helpers.py` ฟังก์ชัน `save_uploaded_file()` ใช้ `secure_filename()` + `uuid` + จำกัดประเภทไฟล์ บันทึกลง `static/uploads/repairs` |
| **5.4** | แจ้งเตือน SweetAlert2 | ไฟล์ `static/js/main.js` และ `templates/base.html` ดักจับ Flash message เพื่อแสดงผล Toast และ Confirmation Dialog |
| **5.5** | ส่งออก CSV และพิมพ์ใบแจ้งซ่อม A4/PDF | Route `/repair/export/csv` ส่งออก CSV เข้ารหัส UTF-8 BOM สำหรับ Excel และ Route `/repair/<id>/print` หน้าเอกสารทางการพร้อม `window.print()` |
