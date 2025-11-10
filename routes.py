from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from app import db 
from models import User, Role, Scan
from utils.yolo_detector import run_yolo_detection

# --- Blueprints ---
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# --- AUTH ROUTES ---

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handles patient registration, assigning the 'patient' role."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
            
        patient_role = Role.query.filter_by(name='patient').first()
        if not patient_role:
             flash('System error: Roles not set up. Contact admin.', 'danger')
             return redirect(url_for('auth.register'))
             
        user = User(username=username, role_id=patient_role.id)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', title='Register')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login for all roles."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        flash(f'Welcome back, {user.username}! You are logged in as a {user.role.name}.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/login.html', title='Login')

@auth.route('/logout')
@login_required
def logout():
    """Logs the user out and clears the session."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

# --- MAIN ROUTES ---

@main.route('/')
def index():
    """Public landing page."""
    return render_template('index.html', title='Welcome')

@main.route('/dashboard')
@login_required
def dashboard():
    """Routes users to their respective dashboards based on role."""
    role_name = current_user.role.name
    
    if role_name == 'patient':
        scans = Scan.query.filter_by(patient_id=current_user.id).order_by(Scan.timestamp.desc()).all()
        return render_template('patient/dashboard.html', title='Patient Dashboard', scans=scans)
        
    elif role_name == 'doctor':
        pending_scans = Scan.query.filter(
            Scan.status.in_(['Pending', 'In Review'])
        ).order_by(Scan.timestamp.asc()).all()
        return render_template('doctor/dashboard.html', title='Doctor Dashboard', scans=pending_scans)
        
    elif role_name == 'admin':
        all_users = User.query.all()
        return render_template('admin/dashboard.html', title='Admin Dashboard', users=all_users)

    return redirect(url_for('main.index'))

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_scan():
    """Patient: Handles X-ray image upload, initiates YOLO analysis, and assigns to a doctor."""
    if current_user.role.name != 'patient':
        flash('Access denied. Only patients can upload scans.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        unique_filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        # --- YOLO PROCESSING ---
        yolo_result, yolo_confidence = run_yolo_detection(filepath)
        
        doctor = User.query.join(Role).filter(Role.name == 'doctor').first()
        doctor_id = doctor.id if doctor else None
        
        new_scan = Scan(
            image_path=os.path.join('uploads', unique_filename), 
            patient_id=current_user.id,
            doctor_id=doctor_id,
            status='Pending',
            yolo_result=yolo_result,
            yolo_confidence=yolo_confidence
        )
        db.session.add(new_scan)
        db.session.commit()
        
        flash(f'Scan uploaded successfully! AI prediction: {yolo_result}. A doctor has been notified for final review.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('patient/upload_scan.html', title='Upload X-ray')

@main.route('/review/<int:scan_id>', methods=['GET', 'POST'])
@login_required
def review_scan(scan_id):
    """Doctor: Reviews a pending scan and submits a final report."""
    if current_user.role.name != 'doctor':
        flash('Access denied. Only doctors can review scans.', 'danger')
        return redirect(url_for('main.dashboard'))

    scan = Scan.query.get_or_404(scan_id)
    
    # Claim Logic: If status is 'Pending', the doctor claims it and sets status to 'In Review'
    if scan.status == 'Pending':
        scan.doctor_id = current_user.id
        scan.status = 'In Review'
        db.session.commit()
        flash('You have successfully claimed this scan for review.', 'info')
    elif scan.doctor_id and scan.doctor_id != current_user.id and scan.status in ['In Review']:
         flash(f'This scan is currently being reviewed by Dr. {scan.doctor.username}.', 'warning')
         if scan.status not in ['Fracture Detected', 'No Fracture', 'Inconclusive']:
             return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if scan.doctor_id != current_user.id and scan.status not in ['In Review', 'Pending']:
             flash('This scan has already been finalized.', 'danger')
             return redirect(url_for('main.dashboard'))

        final_report = request.form.get('final_report')
        diagnosis_status = request.form.get('diagnosis') 
        
        scan.doctor_report = final_report
        scan.status = diagnosis_status
        scan.report_timestamp = datetime.utcnow()
        
        db.session.commit()
        flash('Final report submitted successfully. Status updated.', 'success')
        return redirect(url_for('main.dashboard'))

    # CRITICAL FIX: Ensure the image URL uses forward slashes (/) for web compatibility.
    image_path_with_forward_slashes = scan.image_path.replace('\\', '/')
    full_image_url = url_for('static', filename=image_path_with_forward_slashes)
    
    return render_template('doctor/review_scan.html', 
                           title=f'Review Scan {scan_id}', 
                           scan=scan, 
                           full_image_url=full_image_url)