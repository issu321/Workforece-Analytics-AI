"""
AI-Powered Workforce Analytics and Attrition Prediction System
Main Flask Application
GitHub: https://github.com/issu321
Repo: https://github.com/issu321/Workforece-Analytics-AI
"""

import os
import json
import pickle
import uuid
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import plotly

from utils import (
    get_users, get_user_by_username, get_user_by_id, get_user_by_email,
    add_user, update_user, update_last_login, verify_password,
    add_history_entry, get_history, add_report, get_reports,
    get_settings, save_settings, get_user_settings, save_user_settings,
    validate_csv_file, get_dataset_summary, allowed_file, sanitize_filename,
    get_data_path, get_upload_path, get_report_path, get_model_path
)
from predictor import AttritionPredictor, generate_synthetic_attrition_data
from analyzer import WorkforceAnalyzer

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ===================== PER-USER DATA STORAGE =====================
_user_sessions = {}

def get_user_state(user_id):
    if user_id not in _user_sessions:
        _user_sessions[user_id] = {'df': None, 'predictor': None, 'analyzer': None, 'filename': None}
    return _user_sessions[user_id]

def clear_user_state(user_id):
    if user_id in _user_sessions:
        _user_sessions[user_id] = {'df': None, 'predictor': None, 'analyzer': None, 'filename': None}

# ===================== AUTH HELPERS =====================
def login_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

def get_current_user():
    if 'user_id' in session:
        return get_user_by_id(session["user_id"])
    return None

# ===================== INITIALIZATION =====================
def init_data_files():
    os.makedirs(get_data_path(''), exist_ok=True)
    os.makedirs(get_upload_path(''), exist_ok=True)
    os.makedirs(get_report_path(''), exist_ok=True)
    os.makedirs(get_model_path(''), exist_ok=True)
    if not os.path.exists(get_data_path('users.json')):
        from utils import save_json
        save_json('users.json', {
            'users': [{
                'id': 1,
                'username': 'admin',
                'email': 'admin@company.com',
                'password': generate_password_hash('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat(),
                'last_login': None
            }]
        })
    for fname in ['history.json', 'reports.json', 'settings.json']:
        path = get_data_path(fname)
        if not os.path.exists(path):
            with open(path, "w") as f:
                if fname == 'history.json':
                    json.dump({'entries': []}, f)
                elif fname == 'reports.json':
                    json.dump({'reports': []}, f)
                else:
                    json.dump({}, f)

init_data_files()

# ===================== ROUTES =====================
@app.route('/')
def home():
    user = get_current_user()
    return render_template('home.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        user = get_user_by_username(username)
        if user and verify_password(user, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            update_last_login(user["id"])
            flash('Welcome back, ' + user['username'] + '!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not all([username, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if get_user_by_username(username):
            flash('Username already exists.', 'danger')
            return render_template('register.html')
        if get_user_by_email(email):
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        add_user(username, email, password)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    settings = get_user_settings(user['id'])
    state = get_user_state(user['id'])
    overview = {}
    scores = {}
    has_data = state['df'] is not None
    if has_data and state['analyzer']:
        overview = state['analyzer'].workforce_overview()
        scores = state['analyzer'].calculate_advanced_scores()
    history = get_history(user['id'], limit=5)
    return render_template('dashboard.html', user=user, settings=settings,
                         overview=overview, scores=scores, has_data=has_data,
                         history=history)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == "POST":
        action = request.form.get('action')
        if action == 'update_profile':
            email = request.form.get('email', '').strip()
            if email and email != user.get('email'):
                if get_user_by_email(email) and get_user_by_email(email)['id'] != user['id']:
                    flash('Email already in use.', 'danger')
                else:
                    update_user(user['id'], {'email': email})
                    flash('Profile updated successfully.', 'success')
        elif action == 'change_password':
            current = request.form.get('current_password', '')
            new_pass = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            if not verify_password(user, current):
                flash('Current password is incorrect.', 'danger')
            elif new_pass != confirm:
                flash('New passwords do not match.', 'danger')
            elif len(new_pass) < 6:
                flash('Password must be at least 6 characters.', 'danger')
            else:
                update_user(user['id'], {'password': generate_password_hash(new_pass)})
                flash('Password changed successfully.', 'success')
    user = get_current_user()
    return render_template('profile.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = get_current_user()
    user_settings = get_user_settings(user['id'])
    if request.method == "POST":
        theme = request.form.get('theme', 'dark')
        default_model = request.form.get('default_model', 'xgboost')
        notifications = request.form.get('notifications') == 'on'
        save_user_settings(user["id"], {
            'theme': theme,
            'default_model': default_model,
            'notifications': notifications
        })
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', user=user, settings=user_settings)

# ===================== DATA UPLOAD =====================
@app.route('/upload', methods=['POST'])
@login_required
def upload_csv():
    user = get_current_user()
    state = get_user_state(user['id'])
    if "file" not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('dashboard'))
    file = request.files["file"]
    if file.filename == "":
        flash('No file selected.', 'danger')
        return redirect(url_for('dashboard'))
    if not allowed_file(file.filename):
        flash('Only CSV files are allowed.', 'danger')
        return redirect(url_for('dashboard'))
    filename = secure_filename(sanitize_filename(file.filename))
    filepath = get_upload_path(filename)
    file.save(filepath)
    errors = validate_csv_file(filepath)
    if errors:
        os.remove(filepath)
        flash('Invalid file: ' + '; '.join(errors), 'danger')
        return redirect(url_for('dashboard'))
    try:
        state['df'] = pd.read_csv(filepath)
        state['filename'] = filename
        state['analyzer'] = WorkforceAnalyzer(state['df'])
        state['predictor'] = None
        summary = get_dataset_summary(state['df'])
        add_history_entry({
            'user_id': session['user_id'],
            'action': 'upload',
            'dataset_name': filename,
            'details': 'Uploaded ' + str(summary['rows']) + ' rows, ' + str(summary['columns']) + ' columns'
        })
        flash('Successfully loaded ' + str(summary['rows']) + ' rows and ' + str(summary['columns']) + ' columns.', 'success')
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        flash('Error processing file: ' + str(e), 'danger')
    return redirect(url_for('dashboard'))

@app.route('/upload-demo')
@login_required
def upload_demo():
    user = get_current_user()
    state = get_user_state(user['id'])
    try:
        state['df'] = generate_synthetic_attrition_data(n_samples=1000)
        state['filename'] = 'demo_synthetic_data.csv'
        filepath = get_upload_path(state['filename'])
        state['df'].to_csv(filepath, index=False)
        state['analyzer'] = WorkforceAnalyzer(state['df'])
        state['predictor'] = None
        add_history_entry({
            'user_id': session['user_id'],
            'action': 'demo',
            'dataset_name': state['filename'],
            'details': 'Loaded synthetic demo dataset with 1000 employees'
        })
        flash('Demo dataset loaded successfully with 1000 synthetic employees.', 'success')
    except Exception as e:
        flash('Error loading demo data: ' + str(e), 'danger')
    return redirect(url_for('dashboard'))

# ===================== ATTRITION PREDICTION =====================
@app.route('/attrition')
@login_required
def attrition():
    user = get_current_user()
    state = get_user_state(user['id'])
    has_data = state['df'] is not None
    is_trained = state['predictor'] is not None and state['predictor'].is_trained
    results = None
    feature_importance = None
    if is_trained:
        results = {}
        for k, v in state['predictor'].results.items():
            results[k] = {kk: vv for kk, vv in v.items() if kk != 'model'}
        feature_importance = state['predictor'].get_feature_importance()
    return render_template('attrition.html', user=user, has_data=has_data,
                         is_trained=is_trained, results=results,
                         feature_importance=feature_importance,
                         best_model=state['predictor'].best_model_name if is_trained else None)

@app.route('/train-models', methods=['POST'])
@login_required
def train_models():
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['df'] is None:
        flash('Please upload a dataset first.', 'warning')
        return redirect(url_for('attrition'))
    try:
        state['predictor'] = AttritionPredictor()
        results = state['predictor'].train_models(state['df'])
        model_path = get_model_path('latest_model.pkl')
        state['predictor'].save_model(model_path)
        valid_models = [k for k, v in results.items() if "error" not in v]
        flash('Trained ' + str(len(valid_models)) + ' models successfully. Best: ' + str(state['predictor'].best_model_name), 'success')
        add_history_entry({
            'user_id': session['user_id'],
            'action': 'train',
            'dataset_name': state['filename'] or 'unknown',
            'details': 'Trained ' + str(len(valid_models)) + ' models. Best: ' + str(state['predictor'].best_model_name)
        })
    except Exception as e:
        flash('Error training models: ' + str(e), 'danger')
    return redirect(url_for('attrition'))

@app.route('/predict-attrition', methods=['POST'])
@login_required
def predict_attrition():
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['df'] is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    if state['predictor'] is None or not state['predictor'].is_trained:
        return jsonify({'error': 'Models not trained yet'}), 400
    try:
        predictions = state['predictor'].predict(state['df'])
        result_data = []
        for i, pred in enumerate(predictions):
            row = {"index": i}
            if 'EmployeeID' in state['df'].columns:
                row['employee_id'] = str(state['df'].iloc[i].get('EmployeeID', i))
            elif 'EmployeeNumber' in state['df'].columns:
                row['employee_id'] = str(state['df'].iloc[i].get('EmployeeNumber', i))
            else:
                row['employee_id'] = 'Employee_' + str(i)
            row.update(pred)
            result_data.append(row)
        risk_counts = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
        for p in predictions:
            risk_counts[p['risk_level']] = risk_counts.get(p['risk_level'], 0) + 1
        return jsonify({
            'predictions': result_data[:100],
            'total': len(predictions),
            'risk_distribution': risk_counts,
            'high_risk_count': risk_counts.get('High Risk', 0),
            'medium_risk_count': risk_counts.get('Medium Risk', 0),
            'low_risk_count': risk_counts.get('Low Risk', 0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================== ANALYTICS =====================
@app.route('/analytics')
@login_required
def analytics():
    user = get_current_user()
    state = get_user_state(user['id'])
    has_data = state['df'] is not None
    overview = {}
    dept_analytics = {}
    perf_analytics = {}
    salary_analytics = {}
    if has_data and state['analyzer']:
        overview = state['analyzer'].workforce_overview()
        dept_analytics = state['analyzer'].department_analytics()
        perf_analytics = state['analyzer'].performance_analytics()
        salary_analytics = state['analyzer'].salary_analytics()
    return render_template('analytics.html', user=user, has_data=has_data,
                         overview=overview, dept_analytics=dept_analytics,
                         perf_analytics=perf_analytics, salary_analytics=salary_analytics)

@app.route('/workforce')
@login_required
def workforce():
    user = get_current_user()
    state = get_user_state(user['id'])
    has_data = state['df'] is not None
    scores = {}
    recommendations = []
    insights = []
    forecast = {}
    if has_data and state['analyzer']:
        scores = state['analyzer'].calculate_advanced_scores()
        recommendations = state['analyzer'].generate_retention_recommendations()
        insights = state['analyzer'].generate_insights()
        forecast = state['analyzer'].workforce_forecast()
    return render_template('workforce.html', user=user, has_data=has_data,
                         scores=scores, recommendations=recommendations,
                         insights=insights, forecast=forecast)

# ===================== CHARTS API =====================
@app.route('/api/charts/<chart_type>')
@login_required
def get_chart(chart_type):
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['analyzer'] is None:
        return jsonify({'error': 'No data loaded'}), 400
    chart_methods = {
        'department': state['analyzer'].get_department_chart,
        'attrition_heatmap': state['analyzer'].get_attrition_heatmap,
        'salary_distribution': state['analyzer'].get_salary_distribution_chart,
        'satisfaction': state['analyzer'].get_satisfaction_chart,
        'age_distribution': state['analyzer'].get_age_distribution_chart,
        'gender': state['analyzer'].get_gender_chart,
        'tenure': state['analyzer'].get_tenure_chart,
        'correlation': state['analyzer'].get_correlation_heatmap,
    }
    if chart_type in chart_methods:
        chart_json = chart_methods[chart_type]()
        if chart_json:
            return jsonify({'chart': json.loads(chart_json)})
        return jsonify({'error': 'Could not generate chart'}), 500
    if chart_type == 'model_comparison':
        if state['predictor'] and state['predictor'].is_trained:
            chart_json = state['predictor'].get_model_comparison_chart()
            if chart_json:
                return jsonify({'chart': json.loads(chart_json)})
        return jsonify({'error': 'Models not trained'}), 400
    if chart_type == 'feature_importance':
        if state['predictor'] and state['predictor'].is_trained:
            chart_json = state['predictor'].get_feature_importance_chart()
            if chart_json:
                return jsonify({'chart': json.loads(chart_json)})
        return jsonify({'error': 'Models not trained'}), 400
    if chart_type == 'roc_curve':
        if state['predictor'] and state['predictor'].is_trained:
            chart_json = state['predictor'].get_roc_curve_chart()
            if chart_json:
                return jsonify({'chart': json.loads(chart_json)})
        return jsonify({'error': 'Models not trained'}), 400
    if chart_type == 'forecast':
        forecast = state['analyzer'].workforce_forecast()
        chart_json = state['analyzer'].get_workforce_forecast_chart(forecast)
        if chart_json:
            return jsonify({'chart': json.loads(chart_json)})
        return jsonify({'error': 'Could not generate forecast'}), 500
    return jsonify({'error': 'Unknown chart type'}), 400

# ===================== REPORTS =====================
@app.route('/reports')
@login_required
def reports():
    user = get_current_user()
    user_reports = get_reports(user['id'])
    return render_template('reports.html', user=user, reports=user_reports)

@app.route('/generate-report/<format_type>', methods=['POST'])
@login_required
def generate_report(format_type):
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['df'] is None:
        flash('Please upload data first.', 'warning')
        return redirect(url_for('reports'))
    report_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        if format_type == 'json':
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'dataset': state['filename'],
                "overview": state['analyzer'].workforce_overview() if state['analyzer'] else {},
                "scores": state['analyzer'].calculate_advanced_scores() if state['analyzer'] else {},
                "recommendations": state['analyzer'].generate_retention_recommendations() if state['analyzer'] else [],
                "insights": state['analyzer'].generate_insights() if state['analyzer'] else []
            }
            if state['predictor'] and state['predictor'].is_trained:
                report_data['model_results'] = {}
                for k, v in state['predictor'].results.items():
                    report_data['model_results'][k] = {kk: vv for kk, vv in v.items() if kk != 'model'}
            filename = 'report_' + timestamp + '.json'
            filepath = get_report_path(filename)
            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=2, default=str)
            add_report({'user_id': session['user_id'], 'filename': filename, 'format': 'json', 'type': 'analytics'})
            return send_file(filepath, as_attachment=True, download_name=filename)
        elif format_type == 'txt':
            lines = []
            lines.append('=' * 60)
            lines.append('  WORKFORCE ANALYTICS REPORT')
            lines.append('=' * 60)
            lines.append('Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            lines.append('Dataset: ' + str(state['filename']))
            lines.append('')
            lines.append('WORKFORCE OVERVIEW')
            lines.append('-' * 40)
            if state['analyzer']:
                overview = state['analyzer'].workforce_overview()
                for k, v in overview.items():
                    lines.append(str(k) + ': ' + str(v))
                lines.append('')
                lines.append('ADVANCED SCORES')
                lines.append('-' * 40)
                scores = state['analyzer'].calculate_advanced_scores()
                for k, v in scores.items():
                    lines.append(str(k) + ': ' + str(v))
                lines.append('')
                lines.append('RETENTION RECOMMENDATIONS')
                lines.append('-' * 40)
                for rec in state['analyzer'].generate_retention_recommendations():
                    lines.append('[' + str(rec.get('priority', '')) + '] ' + str(rec.get('category', '')) + ': ' + str(rec.get('recommendation', '')))
            lines.append('=' * 60)
            filename = 'report_' + timestamp + '.txt'
            filepath = get_report_path(filename)
            with open(filepath, "w") as f:
                f.write(chr(10).join(lines))
            add_report({'user_id': session['user_id'], 'filename': filename, 'format': 'txt', 'type': 'analytics'})
            return send_file(filepath, as_attachment=True, download_name=filename)
        elif format_type == 'html':
            html_content = generate_html_report(state)
            filename = 'report_' + timestamp + '.html'
            filepath = get_report_path(filename)
            with open(filepath, "w") as f:
                f.write(html_content)
            add_report({'user_id': session['user_id'], 'filename': filename, 'format': 'html', 'type': 'analytics'})
            return send_file(filepath, as_attachment=True, download_name=filename)
        elif format_type == 'pdf':
            if not REPORTLAB_AVAILABLE:
                flash('PDF generation requires reportlab. Install with: pip install reportlab', 'warning')
                return redirect(url_for('reports'))
            filename = 'report_' + timestamp + '.pdf'
            filepath = get_report_path(filename)
            generate_pdf_report(filepath, state)
            add_report({'user_id': session['user_id'], 'filename': filename, 'format': 'pdf', 'type': 'analytics'})
            return send_file(filepath, as_attachment=True, download_name=filename)
        flash('Report generated successfully.', 'success')
    except Exception as e:
        flash('Error generating report: ' + str(e), 'danger')
    return redirect(url_for('reports'))

def generate_html_report(state):
    overview = state['analyzer'].workforce_overview() if state['analyzer'] else {}
    scores = state['analyzer'].calculate_advanced_scores() if state['analyzer'] else {}
    recommendations = state['analyzer'].generate_retention_recommendations() if state['analyzer'] else []
    insights = state['analyzer'].generate_insights() if state['analyzer'] else []
    html_parts = []
    html_parts.append('<!DOCTYPE html><html><head><title>Workforce Analytics Report</title><style>')
    html_parts.append('body { font-family: Arial, sans-serif; margin: 40px; background: #050510; color: #f1f5f9; }')
    html_parts.append('h1 { color: #ff6b35; border-bottom: 2px solid #ff6b35; padding-bottom: 10px; }')
    html_parts.append('h2 { color: #00d4ff; margin-top: 30px; }')
    html_parts.append('.section { background: #0a0a1a; padding: 20px; margin: 20px 0; border-radius: 20px; border: 1px solid rgba(255,255,255,0.06); }')
    html_parts.append('table { width: 100%; border-collapse: collapse; margin: 15px 0; }')
    html_parts.append('th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); }')
    html_parts.append('th { background: #16122b; color: #f8fafc; }')
    html_parts.append('.metric { display: inline-block; background: #16122b; padding: 15px 25px; margin: 10px; border-radius: 12px; }')
    html_parts.append('.metric-label { font-size: 12px; color: #94a3b8; }')
    html_parts.append('.metric-value { font-size: 24px; font-weight: bold; color: #ff6b35; }')
    html_parts.append('.high { color: #ef4444; } .medium { color: #f59e0b; } .low { color: #10b981; }')
    html_parts.append('</style></head><body>')
    html_parts.append('<h1>Workforce Analytics Report</h1>')
    html_parts.append('<p>Generated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '</p>')
    html_parts.append('<p>Dataset: ' + str(state['filename'] or 'N/A') + '</p>')
    html_parts.append('<div class="section"><h2>Workforce Overview</h2><div>')
    for k, v in overview.items():
        html_parts.append('<div class="metric"><div class="metric-label">' + str(k).replace('_', ' ').title() + '</div><div class="metric-value">' + str(v) + '</div></div>')
    html_parts.append('</div></div>')
    html_parts.append('<div class="section"><h2>Advanced Scores</h2><div>')
    for k, v in scores.items():
        html_parts.append('<div class="metric"><div class="metric-label">' + str(k).replace('_', ' ').title() + '</div><div class="metric-value">' + str(v) + '</div></div>')
    html_parts.append('</div></div>')
    html_parts.append('<div class="section"><h2>AI Insights</h2><table>')
    html_parts.append('<tr><th>Type</th><th>Severity</th><th>Insight</th><th>Recommendation</th></tr>')
    for insight in insights:
        severity_class = insight.get('severity', '').lower()
        html_parts.append('<tr><td>' + str(insight.get('type', '')) + '</td><td class="' + severity_class + '">' + str(insight.get('severity', '')) + '</td><td>' + str(insight.get('insight', '')) + '</td><td>' + str(insight.get('recommendation', '')) + '</td></tr>')
    html_parts.append('</table></div>')
    html_parts.append('<div class="section"><h2>Retention Recommendations</h2><table>')
    html_parts.append('<tr><th>Priority</th><th>Category</th><th>Issue</th><th>Recommendation</th></tr>')
    for rec in recommendations:
        priority_class = rec.get('priority', '').lower()
        html_parts.append('<tr><td class="' + priority_class + '">' + str(rec.get('priority', '')) + '</td><td>' + str(rec.get('category', '')) + '</td><td>' + str(rec.get('issue', '')) + '</td><td>' + str(rec.get('recommendation', '')) + '</td></tr>')
    html_parts.append('</table></div>')
    html_parts.append('</body></html>')
    return chr(10).join(html_parts)

def generate_pdf_report(filepath, state):
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=24, textColor=colors.HexColor("#ff6b35"), spaceAfter=30)
    story.append(Paragraph("Workforce Analytics Report", title_style))
    story.append(Paragraph("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), styles["Normal"]))
    story.append(Paragraph("Dataset: " + str(state['filename'] or "N/A"), styles["Normal"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Workforce Overview", styles["Heading2"]))
    if state['analyzer']:
        overview = state['analyzer'].workforce_overview()
        overview_data = [[str(k).replace("_", " ").title(), str(v)] for k, v in overview.items()]
        t = Table(overview_data, colWidths=[200, 300])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16122b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0a0a1a")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#1e1e3f")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        story.append(t)
    story.append(PageBreak())
    story.append(Paragraph("Advanced Scores", styles["Heading2"]))
    if state['analyzer']:
        scores = state['analyzer'].calculate_advanced_scores()
        scores_data = [[str(k).replace("_", " ").title(), str(v)] for k, v in scores.items()]
        t = Table(scores_data, colWidths=[200, 300])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16122b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0a0a1a")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#1e1e3f")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        story.append(t)
    doc.build(story)

# ===================== HISTORY =====================
@app.route('/history')
@login_required
def history():
    user = get_current_user()
    entries = get_history(user['id'], limit=100)
    return render_template('history.html', user=user, entries=entries)

# ===================== SEARCH =====================
@app.route('/search')
@login_required
def search():
    user = get_current_user()
    query = request.args.get('q', '').lower()
    results = {'employees': [], 'departments': [], 'predictions': []}
    state = get_user_state(user['id'])
    if state['df'] is not None and query:
        for col in ["EmployeeID", "EmployeeNumber", "Name", "FirstName", "LastName"]:
            if col in state['df'].columns:
                matches = state['df'][state['df'][col].astype(str).str.lower().str.contains(query, na=False)]
                for _, row in matches.head(20).iterrows():
                    results["employees"].append(row.to_dict())
                break
        if "Department" in state['df'].columns:
            depts = state['df']["Department"].unique()
            results["departments"] = [d for d in depts if query in str(d).lower()]
    return render_template('search.html', user=user, query=query, results=results)

# ===================== CONTACT =====================
@app.route('/contact')
def contact():
    user = get_current_user()
    return render_template('contact.html', user=user)

# ===================== API ENDPOINTS =====================
@app.route('/api/dataset-summary')
@login_required
def api_dataset_summary():
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['df'] is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    return jsonify(get_dataset_summary(state['df']))

@app.route('/api/data-preview')
@login_required
def api_data_preview():
    user = get_current_user()
    state = get_user_state(user['id'])
    if state['df'] is None:
        return jsonify({'error': 'No dataset loaded'}), 400
    preview = state['df'].head(50).fillna('').to_dict('records')
    return jsonify({'data': preview, 'columns': list(state['df'].columns)})

@app.route('/api/clear-data', methods=['POST'])
@login_required
def api_clear_data():
    user = get_current_user()
    clear_user_state(user['id'])
    return jsonify({'success': True})

# ===================== ERROR HANDLERS =====================
@app.errorhandler(404)
def not_found(e):
    return render_template('home.html', error='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('home.html', error='Internal server error'), 500

# ===================== MAIN =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
