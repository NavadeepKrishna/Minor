from app import db # Import db from app.py
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime

# --- Role Definition ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # 'patient', 'doctor', 'admin'
    users = db.relationship('User', backref='role', lazy='dynamic')

# --- User Model ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    scans_submitted = db.relationship('Scan', foreign_keys='Scan.patient_id', backref='patient', lazy='dynamic')
    scans_assigned = db.relationship('Scan', foreign_keys='Scan.doctor_id', backref='doctor', lazy='dynamic')

    def set_password(self, password):
        # Decode to utf-8 is crucial for database storage compatibility
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- Scan/Report Model ---
class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(256), nullable=False) # Path relative to static/
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    # Status: 'Pending', 'In Review', 'Fracture Detected', 'No Fracture'
    status = db.Column(db.String(50), default='Pending')
    
    # Automated YOLO Report
    yolo_result = db.Column(db.String(20), default='N/A')
    yolo_confidence = db.Column(db.Float)
    
    # Doctor's Final Diagnosis
    doctor_report = db.Column(db.Text)
    report_timestamp = db.Column(db.DateTime)
    
    # Foreign Keys
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Assigned doctor