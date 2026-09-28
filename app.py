import os
import csv
import io
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    send_file, jsonify, abort, make_response
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash

from config import Config
from database import db
from models import (
    User, RepairRequest, RepairImage, Comment,
    RequestStatus, ProblemType, UrgencyLevel, UserRole
)
from helpers import (
    generate_request_no, allowed_file, save_uploaded_file,
    role_required, admin_required, tech_or_admin_required, format_thai_date
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message = 'กรุณาเข้าสู่ระบบก่อนทำรายการ'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register template filters
    @app.template_filter('thai_date')
    def _jinja2_filter_thai_date(date_val, include_time=False):
        return format_thai_date(date_val, include_time)

    @app.context_processor
    def inject_global_vars():
        return {
            'now': datetime.now(),
            'ProblemType': ProblemType,
            'RequestStatus': RequestStatus,
            'UrgencyLevel': UrgencyLevel,
            'UserRole': UserRole
        }

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ==============================================================
    # Authentication Routes
    # ==============================================================

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f'ยินดีต้อนรับคุณ {user.fullname} เข้าสู่ระบบ', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('ออกจากระบบเรียบร้อยแล้ว', 'info')
        return redirect(url_for('login'))

    # ==============================================================
    # Dashboard Route (โจทย์ที่ 5.2)
    # ==============================================================

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # สถิติภาพรวม
        total_repairs = RepairRequest.query.count()
        pending_count = RepairRequest.query.filter_by(status=RequestStatus.PENDING.value).count()
        accepted_count = RepairRequest.query.filter_by(status=RequestStatus.ACCEPTED.value).count()
        in_progress_count = RepairRequest.query.filter_by(status=RequestStatus.IN_PROGRESS.value).count()
        completed_count = RepairRequest.query.filter_by(status=RequestStatus.COMPLETED.value).count()

        # สถิติแยกตามประเภทปัญหา
        stats_by_type = {}
        for ptype in ProblemType:
            count = RepairRequest.query.filter_by(problem_type=ptype.value).count()
            stats_by_type[ptype.value] = count

        # งานล่าสุด 5 รายการ
        recent_repairs = RepairRequest.query.order_by(RepairRequest.created_at.desc()).limit(6).all()

        # งานเฉพาะของผู้ใช้ปัจจุบัน
        my_tasks = []
        if current_user.is_technician:
            my_tasks = RepairRequest.query.filter(
                RepairRequest.assigned_to == current_user.id,
                RepairRequest.status != RequestStatus.COMPLETED.value
            ).order_by(RepairRequest.created_at.desc()).all()
        elif current_user.is_teacher:
            my_tasks = RepairRequest.query.filter(
                RepairRequest.user_id == current_user.id,
                RepairRequest.status != RequestStatus.COMPLETED.value
            ).order_by(RepairRequest.created_at.desc()).all()

        return render_template(
            'dashboard.html',
            total_repairs=total_repairs,
            pending_count=pending_count,
            accepted_count=accepted_count,
            in_progress_count=in_progress_count,
            completed_count=completed_count,
            stats_by_type=stats_by_type,
            recent_repairs=recent_repairs,
            my_tasks=my_tasks
        )

    # ==============================================================
    # Repair Request Routes
    # ==============================================================

    @app.route('/repairs')
    @login_required
    def repairs_list():
        # การค้นหาและกรองข้อมูล
        query = RepairRequest.query

        # Search keyword
        search = request.args.get('search', '').strip()
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    RepairRequest.request_no.ilike(search_pattern),
                    RepairRequest.building.ilike(search_pattern),
                    RepairRequest.room.ilike(search_pattern),
                    RepairRequest.description.ilike(search_pattern)
                )
            )

        # Filters
        status = request.args.get('status', '').strip()
        if status:
            query = query.filter_by(status=status)

        problem_type = request.args.get('problem_type', '').strip()
        if problem_type:
            query = query.filter_by(problem_type=problem_type)

        urgency = request.args.get('urgency', '').strip()
        if urgency:
            query = query.filter_by(urgency=urgency)

        scope = request.args.get('scope', '').strip()
        if scope == 'mine':
            if current_user.is_technician:
                query = query.filter_by(assigned_to=current_user.id)
            else:
                query = query.filter_by(user_id=current_user.id)

        repairs = query.order_by(RepairRequest.created_at.desc()).all()
        return render_template('repair_list.html', repairs=repairs, current_search=search)

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
                flash('กรุณากรอกข้อมูลสำคัญให้ครบถ้วน (อาคาร, ห้อง, ประเภทปัญหา, รายละเอียด)', 'danger')
                return render_template('repair_create.html')

            # สร้างรหัสใบแจ้งซ่อมอัตโนมัติ (RP-YYYYMM-XXX)
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
            db.session.flush()  # เพื่อให้ได้ repair.id

            # บันทึกรูปภาพก่อนซ่อม (Before Images)
            files = request.files.getlist('before_images')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    image_path = save_uploaded_file(file, subfolder='repairs')
                    if image_path:
                        img_record = RepairImage(
                            repair_id=repair.id,
                            image_type='before',
                            image_path=image_path
                        )
                        db.session.add(img_record)

            db.session.commit()
            flash(f'แจ้งซ่อมสำเร็จ! หมายเลขใบแจ้งซ่อมคือ {new_request_no}', 'success')
            return redirect(url_for('repair_detail', id=repair.id))

        return render_template('repair_create.html')

    @app.route('/repair/<int:id>')
    @login_required
    def repair_detail(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        # รายชื่อช่างสำหรับ Admin ในการมอบหมายงาน
        technicians = User.query.filter_by(role=UserRole.TECHNICIAN.value).all()
        return render_template('repair_detail.html', repair=repair, technicians=technicians)

    @app.route('/repair/<int:id>/assign', methods=['POST'])
    @login_required
    @admin_required
    def repair_assign(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        tech_id = request.form.get('technician_id', type=int)
        due_date_str = request.form.get('due_date', '').strip()

        if not tech_id:
            flash('กรุณาเลือกเจ้าหน้าที่ช่างผู้รับผิดชอบ', 'warning')
            return redirect(url_for('repair_detail', id=id))

        due_date_val = None
        if due_date_str:
            try:
                due_date_val = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        repair.assign_to_tech(tech_id, due_date_val)

        # เพิ่มข้อความบันทึกอัตโนมัติ
        tech = db.session.get(User, tech_id)
        tech_name = tech.fullname if tech else "เจ้าหน้าที่"
        auto_comment = Comment(
            repair_id=repair.id,
            user_id=current_user.id,
            comment=f"[ระบบ] มอบหมายงานให้ {tech_name} กำหนดเสร็จ: {format_thai_date(due_date_val) if due_date_val else 'ไม่ระบุ'}"
        )
        db.session.add(auto_comment)
        db.session.commit()

        flash(f'มอบหมายงานให้ {tech_name} สำเร็จแล้ว', 'success')
        return redirect(url_for('repair_detail', id=id))

    @app.route('/repair/<int:id>/start', methods=['POST'])
    @login_required
    @tech_or_admin_required
    def repair_start(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        try:
            repair.start_repair_work()
            auto_comment = Comment(
                repair_id=repair.id,
                user_id=current_user.id,
                comment=f"[ระบบ] เจ้าหน้าที่ {current_user.fullname} ได้เริ่มดำเนินการซ่อมแล้ว"
            )
            db.session.add(auto_comment)
            db.session.commit()
            flash('อัปเดตสถานะเป็น "กำลังดำเนินการ" เรียบร้อยแล้ว', 'success')
        except ValueError as e:
            flash(str(e), 'danger')

        return redirect(url_for('repair_detail', id=id))

    @app.route('/repair/<int:id>/complete', methods=['POST'])
    @login_required
    @tech_or_admin_required
    def repair_complete(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        cost_val = request.form.get('cost', '0').strip()
        result_text = request.form.get('result', '').strip()

        try:
            cost_float = float(cost_val) if cost_val else 0.0
        except ValueError:
            cost_float = 0.0

        if not result_text:
            flash('กรุณากรอกผลการซ่อม/รายละเอียดการแก้ไข', 'warning')
            return redirect(url_for('repair_detail', id=id))

        repair.complete_repair_work(cost_amount=cost_float, result_text=result_text)

        # บันทึกรูปหลังซ่อม (After Images)
        files = request.files.getlist('after_images')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                image_path = save_uploaded_file(file, subfolder='repairs')
                if image_path:
                    img_record = RepairImage(
                        repair_id=repair.id,
                        image_type='after',
                        image_path=image_path
                    )
                    db.session.add(img_record)

        auto_comment = Comment(
            repair_id=repair.id,
            user_id=current_user.id,
            comment=f"[ระบบ] ดำเนินการซ่อมเสร็จสิ้น ค่าใช้จ่าย: {cost_float:,.2f} บาท | ผลการซ่อม: {result_text}"
        )
        db.session.add(auto_comment)
        db.session.commit()

        flash('บันทึกผลการซ่อมเสร็จสิ้นเรียบร้อยแล้ว!', 'success')
        return redirect(url_for('repair_detail', id=id))

    @app.route('/repair/<int:id>/comment', methods=['POST'])
    @login_required
    def repair_add_comment(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        comment_text = request.form.get('comment', '').strip()
        if comment_text:
            new_comment = Comment(
                repair_id=repair.id,
                user_id=current_user.id,
                comment=comment_text
            )
            db.session.add(new_comment)
            db.session.commit()
            flash('เพิ่มความคิดเห็นเรียบร้อยแล้ว', 'success')
        else:
            flash('กรุณากรอกข้อความความคิดเห็น', 'warning')

        return redirect(url_for('repair_detail', id=id))

    @app.route('/repair/<int:id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def repair_delete(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)

        req_no = repair.request_no
        db.session.delete(repair)
        db.session.commit()
        flash(f'ลบใบแจ้งซ่อม {req_no} เรียบร้อยแล้ว', 'info')
        return redirect(url_for('repairs_list'))

    # ==============================================================
    # Print / Export Routes (โจทย์ที่ 5.5)
    # ==============================================================

    @app.route('/repair/<int:id>/print')
    @login_required
    def repair_print(id):
        repair = db.session.get(RepairRequest, id)
        if not repair:
            abort(404)
        return render_template('repair_print.html', repair=repair)

    @app.route('/repair/export/csv')
    @login_required
    def repair_export_csv():
        # ดึงรายการทั้งหมดหรือตามกรอง
        repairs = RepairRequest.query.order_by(RepairRequest.id.asc()).all()

        # สร้าง CSV ในหน่วยความจำพร้อม UTF-8 BOM สำหรับ Excel ภาษาไทย
        output = io.StringIO()
        # Write UTF-8 BOM
        output.write('\ufeff')
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            'ลำดับ', 'รหัสใบแจ้งซ่อม', 'วันที่แจ้ง', 'ผู้แจ้งซ่อม',
            'อาคาร', 'ห้อง', 'ประเภทปัญหา', 'ความเร่งด่วน',
            'รายละเอียดปัญหา', 'สถานะ', 'ช่างผู้รับผิดชอบ',
            'กำหนดเสร็จ', 'วันที่เสร็จ', 'ค่าใช้จ่าย (บาท)', 'ผลการซ่อม'
        ])

        for index, r in enumerate(repairs, start=1):
            writer.writerow([
                index,
                r.request_no,
                r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
                r.reporter.fullname if r.reporter else '',
                r.building,
                r.room,
                r.problem_type_label,
                r.urgency_label,
                r.description.replace('\n', ' '),
                r.status_label,
                r.technician.fullname if r.technician else 'ยังไม่ได้มอบหมาย',
                r.due_date.strftime('%Y-%m-%d') if r.due_date else '',
                r.completion_date.strftime('%Y-%m-%d') if r.completion_date else '',
                f"{r.cost:.2f}" if r.cost is not None else '0.00',
                r.result.replace('\n', ' ') if r.result else ''
            ])

        response = make_response(output.getvalue())
        filename = f"repair_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response

    # ==============================================================
    # Admin User Management Routes
    # ==============================================================

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.order_by(User.id.asc()).all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/add', methods=['POST'])
    @login_required
    @admin_required
    def admin_add_user():
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        fullname = request.form.get('fullname', '').strip()
        role = request.form.get('role', 'teacher').strip()
        email = request.form.get('email', '').strip()

        if not (username and password and fullname and role):
            flash('กรุณากรอกข้อมูลสำคัญให้ครบถ้วน', 'warning')
            return redirect(url_for('admin_users'))

        if User.query.filter_by(username=username).first():
            flash(f'ชื่อผู้ใช้ {username} มีอยู่ในระบบแล้ว', 'danger')
            return redirect(url_for('admin_users'))

        user = User(
            username=username,
            fullname=fullname,
            role=role,
            email=email
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(f'เพิ่มผู้ใช้งาน {fullname} เรียบร้อยแล้ว', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
    @login_required
    @admin_required
    def admin_edit_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            abort(404)

        fullname = request.form.get('fullname', '').strip()
        role = request.form.get('role', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '').strip()

        if fullname:
            user.fullname = fullname
        if role in [UserRole.ADMIN.value, UserRole.TEACHER.value, UserRole.TECHNICIAN.value]:
            user.role = role
        user.email = email
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash(f'แก้ไขข้อมูลผู้ใช้ {user.username} สำเร็จ', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            abort(404)

        if user.id == current_user.id:
            flash('ไม่สามารถลบบัญชีของตัวเองได้', 'danger')
            return redirect(url_for('admin_users'))

        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'ลบผู้ใช้งาน {username} เรียบร้อยแล้ว', 'info')
        return redirect(url_for('admin_users'))

    # ==============================================================
    # Custom Error Handlers
    # ==============================================================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template(
            'error.html',
            error_code=404,
            error_title="ไม่พบหน้าที่คุณต้องการ (Page Not Found)",
            error_message="หน้าที่คุณกำลังค้นหาอาจถูกย้าย ลบ หรือไม่มีอยู่ในระบบ กรุณาตรวจสอบ URL อีกครั้ง"
        ), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template(
            'error.html',
            error_code=500,
            error_title="เกิดข้อผิดพลาดภายในระบบ (Internal Server Error)",
            error_message="ระบบพบปัญหาในการประมวลผลคำขอของคุณ กรุณาลองใหม่อีกครั้งในภายหลัง"
        ), 500

    return app


# Application entry point
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto seed if brand new database
        if not User.query.first():
            print("🌱 Empty database detected! Running auto-seed...")
            from seed import seed_data
            seed_data()
    app.run(debug=True, port=5000)
