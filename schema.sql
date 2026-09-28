-- ==============================================================
-- ระบบแจ้งซ่อมภายในโรงเรียน (School Repair Request System)
-- SQLite Database Schema Definition
-- ==============================================================

PRAGMA foreign_keys = ON;

-- 1. ตาราง users (ผู้ใช้งานระบบ)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    fullname TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'technician')),
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ตาราง repair_requests (ใบแจ้งซ่อม)
CREATE TABLE IF NOT EXISTS repair_requests (
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

-- 3. ตาราง repair_images (รูปภาพประกอบ)
CREATE TABLE IF NOT EXISTS repair_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL,
    image_type TEXT NOT NULL CHECK(image_type IN ('before', 'after')),
    image_path TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repair_id) REFERENCES repair_requests(id) ON DELETE CASCADE
);

-- 4. ตาราง comments (ความคิดเห็นและบันทึกเพิ่มเติม)
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repair_id) REFERENCES repair_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_repairs_status ON repair_requests(status);
CREATE INDEX IF NOT EXISTS idx_repairs_user_id ON repair_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_repairs_assigned ON repair_requests(assigned_to);
CREATE INDEX IF NOT EXISTS idx_images_repair ON repair_images(repair_id);
CREATE INDEX IF NOT EXISTS idx_comments_repair ON comments(repair_id);
