import os
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from database import execute_query
from datetime import datetime, timedelta
import logging
from ingestion import process_local_cloudtrail_logs, process_s3_cloudtrail_logs
from auth import hash_password, verify_password, require_login, get_session_secret
from credentials import encrypt_credential, decrypt_credential
from aws_client import list_s3_buckets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", get_session_secret())
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
CORS(app, supports_credentials=True)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        execute_query("SELECT 1", fetch=True)
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

# ============== Auth: Register, Login, Logout ==============

@app.route('/api/register', methods=['POST'])
def register():
    """Register with email (unique ID) and password."""
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Missing required fields: email, password'}), 400

        email = data['email'].strip().lower()
        password = data['password']
        name = (data.get('name') or '').strip()

        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        existing = execute_query(
            "SELECT id FROM users WHERE email = %s", (email,), fetch=True
        )
        if existing:
            return jsonify({'error': 'User with this email already exists'}), 409

        pwd_hash = hash_password(password)
        execute_query(
            "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s)",
            (email, pwd_hash, name or "")
        )

        logger.info(f"User registered: {email}")
        return jsonify({'message': 'Registration successful. Please log in.'}), 201
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Failed to register'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Login with email and password. Sets session."""
    try:
        data = request.json
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Missing email or password'}), 400

        email = data['email'].strip().lower()
        password = data['password']

        user = execute_query(
            "SELECT id, email, name, password_hash, cloudtrail_bucket, credential_type FROM users WHERE email = %s",
            (email,),
            fetch=True
        )
        if not user or not user[0].get('password_hash'):
            return jsonify({'error': 'Invalid email or password'}), 401
        if not verify_password(user[0]['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        u = user[0]
        session['user_id'] = u['id']
        session.permanent = True

        return jsonify({
            'user_id': u['id'],
            'email': u['email'],
            'name': u.get('name'),
            'cloudtrail_bucket': u.get('cloudtrail_bucket'),
            'has_credentials': bool(u.get('credential_type')),
            'message': 'Logged in successfully'
        }), 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Failed to log in'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/me', methods=['GET'])
@require_login
def me(user_id):
    """Return current user info."""
    user = execute_query(
        "SELECT id, email, name, cloudtrail_bucket, credential_type FROM users WHERE id = %s",
        (user_id,),
        fetch=True
    )
    if not user:
        return jsonify({'error': 'User not found'}), 404
    u = user[0]
    return jsonify({
        'id': u['id'],
        'email': u['email'],
        'name': u.get('name'),
        'cloudtrail_bucket': u.get('cloudtrail_bucket'),
        'has_credentials': bool(u.get('credential_type')),
    }), 200


# ============== AWS Credentials & Buckets ==============

@app.route('/api/credentials', methods=['POST'])
@require_login
def add_credentials(user_id):
    """
    Add or update AWS credentials. Provide either:
    - access_key + secret_key, or
    - role_arn
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        access_key = (data.get('access_key') or '').strip()
        secret_key = (data.get('secret_key') or '').strip()
        role_arn = (data.get('role_arn') or '').strip()

        if access_key and secret_key:
            cred_type = 'access_key'
            enc_access = encrypt_credential(access_key)
            enc_secret = encrypt_credential(secret_key)
            execute_query(
                """UPDATE users SET credential_type = %s, aws_access_key_encrypted = %s,
                   aws_secret_key_encrypted = %s, role_arn = NULL WHERE id = %s""",
                (cred_type, enc_access, enc_secret, user_id)
            )
        elif role_arn:
            cred_type = 'role_arn'
            execute_query(
                """UPDATE users SET credential_type = %s, aws_access_key_encrypted = NULL,
                   aws_secret_key_encrypted = NULL, role_arn = %s WHERE id = %s""",
                (cred_type, role_arn, user_id)
            )
        else:
            return jsonify({
                'error': 'Provide either (access_key + secret_key) or role_arn'
            }), 400

        logger.info(f"Credentials updated for user {user_id}")
        return jsonify({'message': 'Credentials saved successfully'}), 200
    except Exception as e:
        logger.error(f"Credentials error: {e}")
        return jsonify({'error': 'Failed to save credentials'}), 500


def _get_user_credentials(user_id):
    """Return decrypted credentials for the user. Raises if missing."""
    rows = execute_query(
        """SELECT credential_type, aws_access_key_encrypted, aws_secret_key_encrypted, role_arn
           FROM users WHERE id = %s""",
        (user_id,),
        fetch=True
    )
    if not rows or not rows[0].get('credential_type'):
        return None
    r = rows[0]
    if r['credential_type'] == 'access_key':
        ak = decrypt_credential(r.get('aws_access_key_encrypted'))
        sk = decrypt_credential(r.get('aws_secret_key_encrypted'))
        return {'access_key': ak, 'secret_key': sk, 'role_arn': None}
    if r['credential_type'] == 'role_arn':
        return {'access_key': None, 'secret_key': None, 'role_arn': r.get('role_arn')}
    return None


@app.route('/api/buckets', methods=['GET'])
@require_login
def list_buckets_route(user_id):
    """List S3 buckets using the user's stored AWS credentials."""
    try:
        creds = _get_user_credentials(user_id)
        if not creds:
            return jsonify({
                'error': 'No AWS credentials configured. Add credentials first.'
            }), 400

        buckets = list_s3_buckets(
            access_key=creds.get('access_key'),
            secret_key=creds.get('secret_key'),
            role_arn=creds.get('role_arn'),
            region=request.args.get('region') or 'us-east-1',
        )
        return jsonify({'buckets': buckets}), 200
    except Exception as e:
        logger.error(f"List buckets error: {e}")
        return jsonify({'error': f'Failed to list buckets: {str(e)}'}), 500


@app.route('/api/buckets/select', methods=['POST'])
@require_login
def select_bucket(user_id):
    """Set the CloudTrail bucket for the current user."""
    try:
        data = request.json
        bucket = (data.get('bucket') or '').strip()
        if not bucket:
            return jsonify({'error': 'Bucket name required'}), 400

        execute_query(
            "UPDATE users SET cloudtrail_bucket = %s WHERE id = %s",
            (bucket, user_id)
        )
        logger.info(f"User {user_id} selected bucket: {bucket}")
        return jsonify({'message': 'Bucket selected', 'cloudtrail_bucket': bucket}), 200
    except Exception as e:
        logger.error(f"Select bucket error: {e}")
        return jsonify({'error': 'Failed to select bucket'}), 500


# ============== Public Profile System ==============

@app.route('/api/profile/create', methods=['POST'])
def profile_create():
    """Create a public profile. Email and username must be unique."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        email = (data.get('email') or '').strip().lower()
        username = (data.get('username') or '').strip()

        if not email or not username:
            return jsonify({'error': 'email and username are required'}), 400

        existing_email = execute_query(
            "SELECT id FROM profiles WHERE email = %s", (email,), fetch=True
        )
        if existing_email:
            return jsonify({'error': 'Email already in use'}), 409

        existing_username = execute_query(
            "SELECT id FROM profiles WHERE username = %s", (username,), fetch=True
        )
        if existing_username:
            return jsonify({'error': 'Username already taken'}), 409

        execute_query(
            "INSERT INTO profiles (email, username) VALUES (%s, %s)",
            (email, username)
        )
        profile = execute_query(
            "SELECT id FROM profiles WHERE username = %s", (username,), fetch=True
        )
        profile_id = profile[0]['id'] if profile else None

        return jsonify({
            'message': 'Profile created',
            'profile_id': profile_id
        }), 201
    except Exception as e:
        logger.error(f"Profile create error: {e}")
        return jsonify({'error': 'Failed to create profile'}), 500


@app.route('/api/profile/<username>', methods=['GET'])
def profile_get(username):
    """
    Get public profile by username.
    Links to user via email (users.email = profiles.email), then fetches
    heatmap from daily_scores and services from activity_logs.
    """
    try:
        profile = execute_query(
            "SELECT id, email, username FROM profiles WHERE username = %s",
            (username.strip(),),
            fetch=True
        )
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        p = profile[0]
        profile_email = p['email']

        user = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (profile_email,),
            fetch=True
        )
        user_id = user[0]['id'] if user else None

        heatmap = {}
        services = {}
        total_score = 0

        if user_id:
            daily_scores = execute_query(
                "SELECT date, total_score FROM daily_scores WHERE user_id = %s ORDER BY date",
                (user_id,),
                fetch=True
            )
            heatmap = {row['date'].isoformat(): int(row['total_score']) for row in daily_scores}

            service_rows = execute_query(
                "SELECT service, SUM(score) as total FROM activity_logs WHERE user_id = %s GROUP BY service ORDER BY total DESC",
                (user_id,),
                fetch=True
            )
            services = {row['service']: int(row['total']) for row in service_rows}
            total_score = sum(services.values())

        return jsonify({
            'username': p['username'],
            'heatmap': heatmap,
            'services': services,
            'total_score': total_score
        }), 200
    except Exception as e:
        logger.error(f"Profile get error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


# ============== Legacy / Other Routes ==============

@app.route('/api/users', methods=['POST'])
def create_user():
    """Legacy: create user with name, email, role_arn (no password). Kept for backward compatibility."""
    try:
        data = request.json
        if not data or not all(k in data for k in ['name', 'email', 'role_arn']):
            return jsonify({'error': 'Missing required fields: name, email, role_arn'}), 400

        existing = execute_query(
            "SELECT id FROM users WHERE email = %s", (data['email'],), fetch=True
        )
        if existing:
            return jsonify({'error': 'User with this email already exists'}), 409

        execute_query(
            "INSERT INTO users (name, email, role_arn, credential_type) VALUES (%s, %s, %s, 'role_arn')",
            (data['name'], data['email'], data['role_arn'])
        )
        logger.info(f"Legacy user created: {data['email']}")
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/users/<int:user_id>/activity', methods=['GET'])
def get_user_activity(user_id):
    try:
        # Verify user exists
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        days = int(request.args.get('days', 365))
        if days < 1 or days > 730:
            return jsonify({'error': 'Days must be between 1 and 730'}), 400
        
        start_date = datetime.now().date() - timedelta(days=days)
        
        daily_scores = execute_query(
            "SELECT date, total_score FROM daily_scores WHERE user_id = %s AND date >= %s ORDER BY date",
            (user_id, start_date),
            fetch=True
        )
        
        service_breakdown = execute_query(
            "SELECT service, SUM(score) as total FROM activity_logs WHERE user_id = %s AND date >= %s GROUP BY service ORDER BY total DESC",
            (user_id, start_date),
            fetch=True
        )
        
        recent_actions = execute_query(
            "SELECT date, service, action, score FROM activity_logs WHERE user_id = %s ORDER BY date DESC, id DESC LIMIT 20",
            (user_id,),
            fetch=True
        )
        
        heatmap = {row['date'].isoformat(): int(row['total_score']) for row in daily_scores}
        services = {row['service']: int(row['total']) for row in service_breakdown}
        
        return jsonify({
            'heatmap': heatmap,
            'services': services,
            'recent_actions': [
                {
                    'date': str(row['date']),
                    'service': row['service'],
                    'action': row['action'],
                    'score': int(row['score'])
                } for row in recent_actions
            ],
            'total_score': sum(services.values())
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid days parameter'}), 400
    except Exception as e:
        logger.error(f"Error fetching user activity: {str(e)}")
        return jsonify({'error': 'Failed to fetch user activity'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = execute_query(
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = dict(user[0])
        user_data['created_at'] = user_data['created_at'].isoformat()
        
        return jsonify(user_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return jsonify({'error': 'Failed to fetch user'}), 500

@app.route('/api/users', methods=['GET'])
def list_users():
    try:
        users = execute_query(
            "SELECT id, name, email, created_at FROM users ORDER BY created_at DESC",
            fetch=True
        )
        
        return jsonify([
            {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'created_at': user['created_at'].isoformat()
            } for user in users
        ]), 200
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return jsonify({'error': 'Failed to list users'}), 500


@app.route('/api/debug/daily-scores', methods=['GET'])
def debug_daily_scores():
    try:
        rows = execute_query(
            "SELECT user_id, date, total_score FROM daily_scores ORDER BY date DESC, user_id ASC",
            fetch=True,
        )
        return jsonify(rows), 200
    except Exception as e:
        logger.error(f"Error fetching daily_scores debug data: {str(e)}")
        return jsonify({'error': 'Failed to fetch daily scores'}), 500


@app.route('/api/process-sample-logs', methods=['POST'])
def process_sample_logs():
    """
    Manually trigger processing of local CloudTrail-style logs
    from backend/sample_logs using process_local_cloudtrail_logs().
    """
    try:
        processed_count = process_local_cloudtrail_logs()
        return (
            jsonify(
                {
                    'message': 'Processed local sample CloudTrail logs',
                    'records_processed': processed_count,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error processing sample logs: {str(e)}")
        return jsonify({'error': 'Failed to process sample logs'}), 500


@app.route('/api/process-s3-logs', methods=['POST'])
def process_s3_logs():
    """
    Manually trigger processing of CloudTrail-style logs.
    If logged in and user has a selected bucket, uses that.
    Otherwise falls back to cloudproof-test-logs.
    """
    try:
        user_id = session.get("user_id")
        bucket = None
        if user_id:
            rows = execute_query(
                "SELECT cloudtrail_bucket FROM users WHERE id = %s",
                (user_id,),
                fetch=True
            )
            if rows and rows[0].get("cloudtrail_bucket"):
                bucket = rows[0]["cloudtrail_bucket"]
        if not bucket:
            bucket = request.json.get("bucket") if request.json else None
        if not bucket:
            bucket = "cloudproof-test-logs"

        # TODO: pass user credentials to ingestion for user-specific processing
        processed_count = process_s3_cloudtrail_logs(bucket)
        return jsonify({
            "message": "Processed S3 CloudTrail logs",
            "records_processed": processed_count,
            "bucket": bucket,
        }), 200
    except Exception as e:
        logger.error(f"Error processing S3 logs: {str(e)}")
        return jsonify({"error": "Failed to process S3 logs"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
