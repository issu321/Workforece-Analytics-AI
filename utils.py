"""
Utility functions for the Workforce Analytics System.
Handles JSON storage, authentication helpers, data validation, and common operations.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np

# ===================== PATH HELPERS =====================

def get_data_path(filename):
    """Get absolute path to a data JSON file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', filename)

def get_upload_path(filename):
    """Get absolute path to an uploaded file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', filename)

def get_report_path(filename):
    """Get absolute path to a report file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports', filename)

def get_model_path(filename):
    """Get absolute path to a model file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', filename)

# ===================== JSON STORAGE =====================

def load_json(filename, default=None):
    """Load JSON file with default fallback."""
    path = get_data_path(filename)
    if not os.path.exists(path):
        if default is not None:
            save_json(filename, default)
            return default
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        if default is not None:
            return default
        return {}

def save_json(filename, data):
    """Save data to JSON file."""
    path = get_data_path(filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ===================== USER MANAGEMENT =====================

def get_users():
    """Get all users from users.json."""
    data = load_json('users.json', {'users': []})
    return data.get('users', [])

def get_user_by_username(username):
    """Find user by username (case-insensitive)."""
    users = get_users()
    for user in users:
        if user.get('username', '').lower() == username.lower():
            return user
    return None

def get_user_by_id(user_id):
    """Find user by ID."""
    users = get_users()
    for user in users:
        if user.get('id') == user_id:
            return user
    return None

def get_user_by_email(email):
    """Find user by email."""
    users = get_users()
    for user in users:
        if user.get('email', '').lower() == email.lower():
            return user
    return None

def add_user(username, email, password, role='user'):
    """Add a new user with hashed password."""
    users_data = load_json('users.json', {'users': []})
    users = users_data.get('users', [])

    new_id = max([u.get('id', 0) for u in users], default=0) + 1

    new_user = {
        'id': new_id,
        'username': username,
        'email': email,
        'password': generate_password_hash(password),
        'role': role,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }

    users.append(new_user)
    users_data['users'] = users
    save_json('users.json', users_data)
    return new_user

def update_user(user_id, updates):
    """Update user fields."""
    users_data = load_json('users.json', {'users': []})
    users = users_data.get('users', [])

    for user in users:
        if user.get('id') == user_id:
            user.update(updates)
            users_data['users'] = users
            save_json('users.json', users_data)
            return user
    return None

def update_last_login(user_id):
    """Update user's last login timestamp."""
    update_user(user_id, {'last_login': datetime.now().isoformat()})

def verify_password(user, password):
    """Verify password against stored hash."""
    return check_password_hash(user.get('password', ''), password)

# ===================== HISTORY =====================

def add_history_entry(entry):
    """Add entry to history.json."""
    history = load_json('history.json', {'entries': []})
    entries = history.get('entries', [])
    entry['id'] = str(uuid.uuid4())
    entry['timestamp'] = datetime.now().isoformat()
    entries.insert(0, entry)
    history['entries'] = entries
    save_json('history.json', history)
    return entry

def get_history(user_id=None, limit=50):
    """Get history entries, optionally filtered by user."""
    history = load_json('history.json', {'entries': []})
    entries = history.get('entries', [])
    if user_id is not None:
        entries = [e for e in entries if e.get('user_id') == user_id]
    return entries[:limit]

# ===================== REPORTS =====================

def add_report(report):
    """Add report metadata to reports.json."""
    reports_data = load_json('reports.json', {'reports': []})
    reports = reports_data.get('reports', [])
    report['id'] = str(uuid.uuid4())
    report['created_at'] = datetime.now().isoformat()
    reports.insert(0, report)
    reports_data['reports'] = reports
    save_json('reports.json', reports_data)
    return report

def get_reports(user_id=None, limit=50):
    """Get reports, optionally filtered by user."""
    reports_data = load_json('reports.json', {'reports': []})
    reports = reports_data.get('reports', [])
    if user_id is not None:
        reports = [r for r in reports if r.get('user_id') == user_id]
    return reports[:limit]

# ===================== SETTINGS =====================

def get_settings():
    """Get system settings."""
    return load_json('settings.json', {
        'theme': 'dark',
        'default_model': 'xgboost',
        'notifications': True,
        'auto_save': True
    })

def save_settings(settings):
    """Save system settings."""
    save_json('settings.json', settings)

def get_user_settings(user_id):
    """Get user-specific settings."""
    all_settings = load_json('settings.json', {})
    user_key = f'user_{user_id}'
    return all_settings.get(user_key, {
        'theme': all_settings.get('theme', 'dark'),
        'default_model': all_settings.get('default_model', 'xgboost'),
        'notifications': True
    })

def save_user_settings(user_id, settings):
    """Save user-specific settings."""
    all_settings = load_json('settings.json', {})
    user_key = f'user_{user_id}'
    all_settings[user_key] = settings
    save_json('settings.json', all_settings)

# ===================== DATA VALIDATION =====================

def validate_csv_file(file_path):
    """Validate uploaded CSV file."""
    errors = []

    if not os.path.exists(file_path):
        errors.append("File does not exist.")
        return errors

    if os.path.getsize(file_path) == 0:
        errors.append("File is empty.")
        return errors

    if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB limit
        errors.append("File exceeds 50MB limit.")

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            errors.append("CSV file contains no data.")
        if len(df.columns) == 0:
            errors.append("CSV file has no columns.")
    except pd.errors.EmptyDataError:
        errors.append("CSV file is empty.")
    except pd.errors.ParserError:
        errors.append("Invalid CSV format.")
    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")

    return errors

def get_dataset_summary(df):
    """Generate summary statistics for a dataset."""
    summary = {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'missing_percentage': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'numeric_summary': {},
        'categorical_summary': {}
    }

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            summary['numeric_summary'][col] = {
                'mean': round(float(df[col].mean()), 2) if not df[col].isnull().all() else None,
                'std': round(float(df[col].std()), 2) if not df[col].isnull().all() else None,
                'min': round(float(df[col].min()), 2) if not df[col].isnull().all() else None,
                'max': round(float(df[col].max()), 2) if not df[col].isnull().all() else None,
                'median': round(float(df[col].median()), 2) if not df[col].isnull().all() else None
            }
        else:
            summary['categorical_summary'][col] = {
                'unique_count': df[col].nunique(),
                'top_values': df[col].value_counts().head(5).to_dict()
            }

    return summary

# ===================== SECURITY =====================

def generate_csrf_token():
    """Generate a CSRF token."""
    return hashlib.sha256(os.urandom(32)).hexdigest()

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

def sanitize_filename(filename):
    """Sanitize filename for safe storage."""
    return "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).rstrip()

# ===================== HELPERS =====================

def generate_id():
    """Generate unique ID."""
    return str(uuid.uuid4())

def format_number(num, decimals=2):
    """Format number with specified decimals."""
    try:
        return round(float(num), decimals)
    except:
        return num

def safe_divide(a, b, default=0):
    """Safe division with default fallback."""
    try:
        return a / b if b != 0 else default
    except:
        return default
