from flask import Flask, jsonify, request
from flask_cors import CORS
from database import execute_query
from datetime import datetime, timedelta
import logging
from ingestion import process_local_cloudtrail_logs

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
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
