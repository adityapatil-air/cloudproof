import boto3
import json
import gzip
from datetime import datetime, timedelta
from io import BytesIO
from scoring import calculate_score, DAILY_SCORE_CAP, SERVICE_DAILY_CAP
from database import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def assume_role(role_arn):
    try:
        sts = boto3.client('sts')
        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName='CloudProofIngestion',
            DurationSeconds=3600
        )
        return response['Credentials']
    except Exception as e:
        logger.error(f"Failed to assume role {role_arn}: {str(e)}")
        raise

def process_cloudtrail_logs(user_id, role_arn, bucket_name):
    try:
        credentials = assume_role(role_arn)
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        last_processed = get_last_processed_timestamp(user_id)
        cutoff_time = last_processed or datetime.now() - timedelta(days=7)
        
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix='AWSLogs/')
        
        activities = []
        daily_service_scores = {}
        daily_totals = {}
        
        for page in page_iterator:
            for obj in page.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) <= cutoff_time:
                    continue
                    
                if not obj['Key'].endswith('.json.gz'):
                    continue
                
                try:
                    file_obj = s3.get_object(Bucket=bucket_name, Key=obj['Key'])
                    
                    with gzip.GzipFile(fileobj=BytesIO(file_obj['Body'].read())) as gzipfile:
                        content = gzipfile.read()
                        log_data = json.loads(content)
                        
                        for record in log_data.get('Records', []):
                            try:
                                event_time = datetime.strptime(record['eventTime'], '%Y-%m-%dT%H:%M:%SZ')
                                service = record.get('eventSource', '').split('.')[0].upper()
                                action = record.get('eventName', '')
                                
                                if not service or not action:
                                    continue
                                
                                score = calculate_score(service, action)
                                
                                if score > 0:
                                    date_key = event_time.date()
                                    service_key = f"{date_key}_{service}"
                                    
                                    # Apply daily caps
                                    if date_key not in daily_totals:
                                        daily_totals[date_key] = 0
                                    if service_key not in daily_service_scores:
                                        daily_service_scores[service_key] = 0
                                    
                                    if daily_totals[date_key] >= DAILY_SCORE_CAP:
                                        continue
                                    if daily_service_scores[service_key] >= SERVICE_DAILY_CAP:
                                        continue
                                    
                                    activities.append({
                                        'user_id': user_id,
                                        'date': date_key,
                                        'service': service,
                                        'action': action,
                                        'score': score
                                    })
                                    
                                    daily_totals[date_key] += score
                                    daily_service_scores[service_key] += score
                                    
                            except Exception as e:
                                logger.warning(f"Error processing record: {str(e)}")
                                continue
                                
                except Exception as e:
                    logger.warning(f"Error processing file {obj['Key']}: {str(e)}")
                    continue
        
        if activities:
            store_activities(activities)
            logger.info(f"Stored {len(activities)} activities for user {user_id}")
        
        update_last_processed_timestamp(user_id, datetime.now())
        
        return len(activities)
        
    except Exception as e:
        logger.error(f"Error in process_cloudtrail_logs: {str(e)}")
        raise

def store_activities(activities):
    for activity in activities:
        try:
            execute_query(
                "INSERT INTO activity_logs (user_id, date, service, action, score) VALUES (%s, %s, %s, %s, %s)",
                (activity['user_id'], activity['date'], activity['service'], activity['action'], activity['score'])
            )
            
            execute_query(
                """
                INSERT INTO daily_scores (user_id, date, total_score) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, date) 
                DO UPDATE SET total_score = LEAST(daily_scores.total_score + EXCLUDED.total_score, %s)
                """,
                (activity['user_id'], activity['date'], activity['score'], DAILY_SCORE_CAP)
            )
        except Exception as e:
            logger.error(f"Error storing activity: {str(e)}")
            continue

def get_last_processed_timestamp(user_id):
    try:
        result = execute_query(
            "SELECT last_processed_timestamp FROM processing_state WHERE user_id = %s",
            (user_id,),
            fetch=True
        )
        return result[0]['last_processed_timestamp'] if result else None
    except Exception as e:
        logger.warning(f"Error getting last processed timestamp: {str(e)}")
        return None

def update_last_processed_timestamp(user_id, timestamp):
    try:
        execute_query(
            """
            INSERT INTO processing_state (user_id, last_processed_timestamp) 
            VALUES (%s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET last_processed_timestamp = EXCLUDED.last_processed_timestamp
            """,
            (user_id, timestamp)
        )
    except Exception as e:
        logger.error(f"Error updating last processed timestamp: {str(e)}")
        raise
