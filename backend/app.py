from flask import Flask, jsonify, request
from flask_cors import CORS
from database import execute_query
from datetime import datetime, timedelta
import logging
import os
import re
import uuid
import random
from werkzeug.security import generate_password_hash, check_password_hash
from ingestion import process_local_cloudtrail_logs, process_s3_cloudtrail_logs, process_user_s3_logs, store_activities
from scoring import calculate_score, DAILY_SCORE_CAP, SERVICE_DAILY_CAP, ACTION_DAILY_CAP
from config import get_credibility, CREDIBILITY_TIERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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
        db_status = 'connected'
    except Exception as e:
        db_status = str(e)
    return jsonify({'status': 'healthy', 'db': db_status, 'timestamp': datetime.now().isoformat()}), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        
        if not data or not all(k in data for k in ['name', 'email', 'role_arn']):
            return jsonify({'error': 'Missing required fields: name, email, role_arn'}), 400
        
        # Check if email already exists
        existing = execute_query(
            "SELECT id FROM users WHERE email = %s",
            (data['email'],),
            fetch=True
        )
        
        if existing:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        execute_query(
    "INSERT INTO users (name, email, role_arn) VALUES (%s, %s, %s)",
    (data['name'], data['email'], data['role_arn'])
    )
        
        logger.info(f"User created: {data['email']}")
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


@app.route('/api/users/<int:user_id>/dashboard', methods=['GET'])
def get_user_dashboard(user_id):
    try:
        user = execute_query(
            "SELECT id, name, email FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        days = int(request.args.get('days', 30))
        start_date = datetime.now().date() - timedelta(days=days)
        
        daily_usage = execute_query(
            """
            SELECT 
                date,
                service,
                action,
                score,
                COALESCE(timestamp, created_at) as timestamp
            FROM activity_logs 
            WHERE user_id = %s AND date >= %s 
            ORDER BY date DESC, COALESCE(timestamp, created_at) DESC
            """,
            (user_id, start_date),
            fetch=True
        )
        
        dashboard_data = {}
        for row in daily_usage:
            date_str = row['date'].isoformat()
            if date_str not in dashboard_data:
                dashboard_data[date_str] = {
                    'date': date_str,
                    'services': {},
                    'total_actions': 0,
                    'total_score': 0
                }
            
            service = row['service']
            if service not in dashboard_data[date_str]['services']:
                dashboard_data[date_str]['services'][service] = {
                    'count': 0,
                    'actions': [],
                    'total_score': 0
                }
            
            dashboard_data[date_str]['services'][service]['count'] += 1
            dashboard_data[date_str]['services'][service]['total_score'] += row['score']
            timestamp_val = row['timestamp']
            if isinstance(timestamp_val, str):
                timestamp_str = timestamp_val
            elif timestamp_val:
                timestamp_str = timestamp_val.isoformat()
            else:
                timestamp_str = None
            dashboard_data[date_str]['services'][service]['actions'].append({
                'action': row['action'],
                'score': row['score'],
                'timestamp': timestamp_str
            })
            dashboard_data[date_str]['total_actions'] += 1
            dashboard_data[date_str]['total_score'] += row['score']
        
        result = sorted(dashboard_data.values(), key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'user': {
                'id': user[0]['id'],
                'name': user[0]['name'],
                'email': user[0]['email']
            },
            'dashboard': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard'}), 500

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

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        execute_query("DELETE FROM users WHERE id = %s", (user_id,))
        
        logger.info(f"User deleted: {user_id}")
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 500


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
    Manually trigger processing of CloudTrail-style logs from the
    fixed S3 bucket using process_s3_cloudtrail_logs().
    """
    try:
        processed_count = process_s3_cloudtrail_logs("cloudproof-test-logs")
        return (
            jsonify(
                {
                    "message": "Processed S3 CloudTrail logs",
                    "records_processed": processed_count,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error processing S3 logs: {str(e)}")
        return jsonify({"error": "Failed to process S3 logs"}), 500

@app.route('/api/users/<int:user_id>/resources', methods=['GET'])
def get_user_resources(user_id):
    try:
        user = execute_query(
            "SELECT id FROM users WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resources = execute_query(
            """
            SELECT 
                resource_type,
                resource_id,
                parent_resource_id,
                state,
                metadata,
                last_updated
            FROM resource_state 
            WHERE user_id = %s 
            ORDER BY last_updated DESC
            """,
            (user_id,),
            fetch=True
        )
        
        result = []
        for row in resources:
            timestamp_val = row['last_updated']
            if isinstance(timestamp_val, str):
                timestamp_str = timestamp_val
            elif timestamp_val:
                timestamp_str = timestamp_val.isoformat()
            else:
                timestamp_str = None
                
            result.append({
                'resource_type': row['resource_type'],
                'resource_id': row['resource_id'],
                'parent_resource_id': row['parent_resource_id'],
                'state': row['state'],
                'metadata': row['metadata'],
                'last_updated': timestamp_str
            })
        
        return jsonify({
            'resources': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching resources: {str(e)}")
        return jsonify({'error': 'Failed to fetch resources'}), 500

# ─── Public Profile Endpoints ────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register_user():
    """Create a new public profile. Stores S3 bucket config for log ingestion."""
    data = request.json
    required = ['username', 'name', 'email', 's3_bucket', 'sync_pin']
    if not data or not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {", ".join(required)}'}), 400

    username = data['username'].strip().lower()
    if not re.match(r'^[a-z0-9_-]+$', username):
        return jsonify({'error': 'Username can only contain lowercase letters, numbers, hyphens, and underscores'}), 400
    if len(username) < 3 or len(username) > 30:
        return jsonify({'error': 'Username must be between 3 and 30 characters'}), 400

    sync_pin = data['sync_pin']
    if len(sync_pin) < 4:
        return jsonify({'error': 'Sync password must be at least 4 characters'}), 400

    existing_username = execute_query(
        "SELECT id FROM users WHERE username = %s", (username,), fetch=True
    )
    if existing_username:
        return jsonify({'error': 'Username already taken'}), 409

    existing_email = execute_query(
        "SELECT id FROM users WHERE email = %s", (data['email'],), fetch=True
    )
    if existing_email:
        return jsonify({'error': 'Email already registered'}), 409

    s3_bucket = data['s3_bucket'].strip()
    s3_prefix = data.get('s3_prefix', '').strip()
    aws_region = data.get('aws_region', 'us-east-1').strip() or 'us-east-1'
    pin_hash = generate_password_hash(sync_pin)

    execute_query(
        "INSERT INTO users (username, name, email, s3_bucket, s3_prefix, aws_region, sync_pin_hash) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (username, data['name'].strip(), data['email'].strip(), s3_bucket, s3_prefix, aws_region, pin_hash)
    )

    logger.info(f"New profile created: {username} → s3://{s3_bucket}/{s3_prefix}")
    return jsonify({'message': 'Profile created successfully', 'username': username}), 201


@app.route('/api/profile/<username>', methods=['GET'])
def get_profile(username):
    """Return the full public profile for a username — used by the profile page."""
    user = execute_query(
        "SELECT id, username, name, email, s3_bucket, aws_region, created_at FROM users WHERE username = %s",
        (username.lower(),),
        fetch=True
    )
    if not user:
        return jsonify({'error': 'Profile not found'}), 404

    user_row = user[0]
    user_id = user_row['id']

    days = int(request.args.get('days', 365))
    if days < 1 or days > 730:
        days = 365
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

    heatmap = {row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']): int(row['total_score']) for row in daily_scores}
    services = {row['service']: int(row['total']) for row in service_breakdown}
    total_score = sum(services.values())

    # Compute streaks server-side
    sorted_dates = sorted(heatmap.keys())
    current_streak = 0
    max_streak = 0
    if sorted_dates:
        temp = 1
        for i in range(1, len(sorted_dates)):
            prev = datetime.strptime(sorted_dates[i - 1], '%Y-%m-%d').date()
            curr = datetime.strptime(sorted_dates[i], '%Y-%m-%d').date()
            if (curr - prev).days == 1:
                temp += 1
                max_streak = max(max_streak, temp)
            else:
                temp = 1
        max_streak = max(max_streak, 1)

        # Current streak: walk back from most recent active day
        current_streak = 1
        for i in range(len(sorted_dates) - 2, -1, -1):
            prev = datetime.strptime(sorted_dates[i], '%Y-%m-%d').date()
            nxt = datetime.strptime(sorted_dates[i + 1], '%Y-%m-%d').date()
            if (nxt - prev).days == 1:
                current_streak += 1
            else:
                break

    created_at = user_row['created_at']
    if hasattr(created_at, 'isoformat'):
        created_at = created_at.isoformat()
    else:
        created_at = str(created_at)

    return jsonify({
        'user': {
            'username': user_row['username'],
            'name': user_row['name'],
            'created_at': created_at,
        },
        'heatmap': heatmap,
        'services': services,
        'recent_actions': [
            {
                'date': str(row['date']),
                'service': row['service'],
                'action': row['action'],
                'score': int(row['score']),
            } for row in recent_actions
        ],
        'total_score': total_score,
        'streaks': {'current': current_streak, 'longest': max_streak},
        'credibility': get_credibility(total_score),
        'tiers': CREDIBILITY_TIERS,
    }), 200


@app.route('/api/profile/<username>/sync', methods=['POST'])
def sync_profile(username):
    """Pull latest CloudTrail logs from the user's S3 bucket and update their scores.
    Requires the sync_pin set at registration to prevent others from triggering syncs."""
    data = request.json or {}
    sync_pin = data.get('sync_pin', '')

    user = execute_query(
        "SELECT id, s3_bucket, s3_prefix, aws_region, sync_pin_hash FROM users WHERE username = %s",
        (username.lower(),),
        fetch=True
    )
    if not user:
        return jsonify({'error': 'Profile not found'}), 404

    row = user[0]

    # Verify ownership via sync PIN
    pin_hash = row['sync_pin_hash']
    if not pin_hash or not sync_pin or not check_password_hash(pin_hash, sync_pin):
        return jsonify({'error': 'Invalid sync password'}), 403

    if not row['s3_bucket']:
        return jsonify({'error': 'No S3 bucket configured for this profile'}), 400

    try:
        count = process_user_s3_logs(
            user_id=row['id'],
            bucket_name=row['s3_bucket'],
            s3_prefix=row['s3_prefix'] or '',
            aws_region=row['aws_region'] or 'us-east-1',
        )
        logger.info(f"Sync complete for {username}: {count} records processed")
        return jsonify({'message': 'Sync complete', 'records_processed': count}), 200
    except Exception as e:
        logger.error(f"Sync failed for {username}: {str(e)}")
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500


@app.route('/api/profile/<username>/dashboard', methods=['GET'])
def get_profile_dashboard(username):
    """Dashboard view for a profile — daily breakdown by service and action."""
    user = execute_query(
        "SELECT id FROM users WHERE username = %s", (username.lower(),), fetch=True
    )
    if not user:
        return jsonify({'error': 'Profile not found'}), 404

    user_id = user[0]['id']
    days = int(request.args.get('days', 30))
    if days < 1 or days > 365:
        days = 30
    start_date = datetime.now().date() - timedelta(days=days)

    daily_usage = execute_query(
        """
        SELECT date, service, action, score,
               COALESCE(timestamp, created_at) as timestamp
        FROM activity_logs
        WHERE user_id = %s AND date >= %s
        ORDER BY date DESC, COALESCE(timestamp, created_at) DESC
        """,
        (user_id, start_date),
        fetch=True
    )

    dashboard_data = {}
    for row in daily_usage:
        date_str = row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])
        if date_str not in dashboard_data:
            dashboard_data[date_str] = {'date': date_str, 'services': {}, 'total_actions': 0, 'total_score': 0}

        service = row['service']
        if service not in dashboard_data[date_str]['services']:
            dashboard_data[date_str]['services'][service] = {'count': 0, 'actions': [], 'total_score': 0}

        ts = row['timestamp']
        ts_str = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts) if ts else None

        dashboard_data[date_str]['services'][service]['count'] += 1
        dashboard_data[date_str]['services'][service]['total_score'] += row['score']
        dashboard_data[date_str]['services'][service]['actions'].append({
            'action': row['action'], 'score': row['score'], 'timestamp': ts_str
        })
        dashboard_data[date_str]['total_actions'] += 1
        dashboard_data[date_str]['total_score'] += row['score']

    return jsonify({
        'dashboard': sorted(dashboard_data.values(), key=lambda x: x['date'], reverse=True)
    }), 200


@app.route('/api/profile/<username>/resources', methods=['GET'])
def get_profile_resources(username):
    """Resource inventory for a profile."""
    user = execute_query(
        "SELECT id FROM users WHERE username = %s", (username.lower(),), fetch=True
    )
    if not user:
        return jsonify({'error': 'Profile not found'}), 404

    user_id = user[0]['id']
    resources = execute_query(
        """
        SELECT resource_type, resource_id, parent_resource_id, state, metadata, last_updated
        FROM resource_state
        WHERE user_id = %s
        ORDER BY last_updated DESC
        """,
        (user_id,),
        fetch=True
    )

    result = []
    for row in resources:
        ts = row['last_updated']
        result.append({
            'resource_type': row['resource_type'],
            'resource_id': row['resource_id'],
            'parent_resource_id': row['parent_resource_id'],
            'state': row['state'],
            'metadata': row['metadata'],
            'last_updated': ts.isoformat() if hasattr(ts, 'isoformat') else str(ts) if ts else None,
        })

    return jsonify({'resources': result}), 200


@app.route('/api/profile/<username>/test-sync', methods=['POST'])
def test_sync_profile(username):
    """DEV ONLY — generate random CloudTrail-like events and process them for this profile.
    Requires sync_pin to prevent accidental or unauthorised use."""
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403

    data     = request.json or {}
    sync_pin = data.get('sync_pin', '')

    user = execute_query(
        "SELECT id, sync_pin_hash FROM users WHERE username = %s",
        (username.lower(),), fetch=True
    )
    if not user:
        return jsonify({'error': 'Profile not found'}), 404

    row = user[0]
    if not sync_pin or not check_password_hash(row['sync_pin_hash'], sync_pin):
        return jsonify({'error': 'Invalid sync password'}), 403

    activities = _generate_test_activities(row['id'])
    if activities:
        store_activities(activities)

    return jsonify({
        'message': f'Generated and processed {len(activities)} test activity records',
        'count': len(activities),
    }), 200


def _generate_test_activities(user_id):
    """Return a list of fake scored activity dicts spread across the last 90 days."""
    SAMPLE_EVENTS = [
        ('ec2', 'RunInstances'), ('ec2', 'TerminateInstances'), ('ec2', 'CreateSecurityGroup'),
        ('ec2', 'AuthorizeSecurityGroupIngress'), ('ec2', 'CreateKeyPair'), ('ec2', 'AllocateAddress'),
        ('s3', 'CreateBucket'), ('s3', 'PutBucketPolicy'), ('s3', 'PutObject'), ('s3', 'DeleteObject'),
        ('iam', 'CreateRole'), ('iam', 'AttachRolePolicy'), ('iam', 'CreateUser'), ('iam', 'CreatePolicy'),
        ('lambda', 'CreateFunction'), ('lambda', 'UpdateFunctionCode'), ('lambda', 'PublishVersion'),
        ('rds', 'CreateDBInstance'), ('rds', 'CreateDBSnapshot'), ('rds', 'ModifyDBInstance'),
        ('eks', 'CreateCluster'), ('eks', 'CreateNodegroup'),
        ('ecs', 'CreateCluster'), ('ecs', 'RegisterTaskDefinition'), ('ecs', 'RunTask'),
        ('cloudformation', 'CreateStack'), ('cloudformation', 'UpdateStack'), ('cloudformation', 'DeleteStack'),
        ('dynamodb', 'CreateTable'), ('dynamodb', 'PutItem'), ('dynamodb', 'UpdateTable'),
        ('route53', 'CreateHostedZone'), ('route53', 'ChangeResourceRecordSets'),
    ]

    today = datetime.now().date()
    # Pick ~55 random days out of the last 90 to simulate realistic usage
    active_offsets = sorted(random.sample(range(90), min(55, 90)))

    activities = []
    daily_totals         = {}
    daily_service_scores = {}
    daily_action_scores  = {}

    for offset in active_offsets:
        date_key   = today - timedelta(days=offset)
        num_events = random.randint(3, 14)
        sample     = random.choices(SAMPLE_EVENTS, k=num_events)

        for event_source, event_name in sample:
            service      = event_source.upper()
            action       = event_name
            score        = calculate_score(service, action)
            if score <= 0:
                continue

            service_key = f"{date_key}_{service}"
            action_key  = f"{date_key}_{service}_{action}"

            daily_totals.setdefault(date_key, 0)
            daily_service_scores.setdefault(service_key, 0)
            daily_action_scores.setdefault(action_key, 0)

            if daily_totals[date_key]         >= DAILY_SCORE_CAP:    continue
            if daily_service_scores[service_key] >= SERVICE_DAILY_CAP: continue
            if daily_action_scores[action_key]   >= ACTION_DAILY_CAP:  continue

            activities.append({
                'user_id': user_id,
                'date':    date_key,
                'service': service,
                'action':  action,
                'score':   score,
                # Each test run gets unique event IDs so it doesn't de-dup with previous runs
                'event_id': str(uuid.uuid4()),
            })

            daily_totals[date_key]            += score
            daily_service_scores[service_key] += score
            daily_action_scores[action_key]   += score

    return activities


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=False, port=port)