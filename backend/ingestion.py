import boto3
import json
import gzip
from datetime import datetime, timedelta
from io import BytesIO
from scoring import calculate_score, DAILY_SCORE_CAP, SERVICE_DAILY_CAP
from database import execute_query
import logging
import os

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


def process_local_cloudtrail_logs():
    """
    Process CloudTrail-style JSON or JSON.GZ log files from the local
    backend/sample_logs directory and update activity and daily scores.
    """
    sample_logs_dir = os.path.join(os.path.dirname(__file__), "sample_logs")

    if not os.path.isdir(sample_logs_dir):
        logger.warning(f"Sample logs directory not found: {sample_logs_dir}")
        return 0

    user_id_value = (
        os.getenv("LOCAL_CLOUDTRAIL_USER_ID")
        or os.getenv("LOCAL_INGEST_USER_ID")
        or "1"
    )

    try:
        user_id = int(user_id_value)
    except ValueError:
        logger.warning(
            f"Invalid LOCAL_CLOUDTRAIL_USER_ID/LOCAL_INGEST_USER_ID value "
            f"'{user_id_value}', defaulting to 1"
        )
        user_id = 1

    activities = []
    daily_service_scores = {}
    daily_totals = {}

    for entry in os.listdir(sample_logs_dir):
        file_path = os.path.join(sample_logs_dir, entry)

        if not os.path.isfile(file_path):
            continue

        if not (entry.endswith(".json") or entry.endswith(".json.gz")):
            continue

        try:
            if entry.endswith(".gz"):
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    log_data = json.load(f)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading local log file {file_path}: {str(e)}")
            continue

        for record in log_data.get("Records", []):
            try:
                # Skip read-only events
                read_only = record.get("readOnly")
                if isinstance(read_only, str):
                    if read_only.lower() == "true":
                        continue
                elif read_only is True:
                    continue

                event_time_str = record.get("eventTime")
                event_source = record.get("eventSource", "")
                event_name = record.get("eventName", "")

                if not event_time_str or not event_source or not event_name:
                    continue

                event_time = datetime.strptime(
                    event_time_str, "%Y-%m-%dT%H:%M:%SZ"
                )
                service = event_source.split(".")[0].upper()
                action = event_name

                if not service or not action:
                    continue

                score = calculate_score(service, action)
                if score <= 0:
                    continue

                date_key = event_time.date()
                service_key = f"{date_key}_{service}"

                if date_key not in daily_totals:
                    daily_totals[date_key] = 0
                if service_key not in daily_service_scores:
                    daily_service_scores[service_key] = 0

                if daily_totals[date_key] >= DAILY_SCORE_CAP:
                    continue
                if daily_service_scores[service_key] >= SERVICE_DAILY_CAP:
                    continue

                activities.append(
                    {
                        "user_id": user_id,
                        "date": date_key,
                        "service": service,
                        "action": action,
                        "score": score,
                    }
                )

                daily_totals[date_key] += score
                daily_service_scores[service_key] += score

            except Exception as e:
                logger.warning(
                    f"Error processing local record in {entry}: {str(e)}"
                )
                continue

    if activities:
        store_activities(activities)
        logger.info(
            f"Stored {len(activities)} local activities for user {user_id} "
            f"from sample_logs"
        )

    return len(activities)

def store_activities(activities):
    daily_aggregates = {}
    for activity in activities:
        try:
            execute_query(
                "INSERT INTO activity_logs (user_id, date, service, action, score) VALUES (%s, %s, %s, %s, %s)",
                (activity['user_id'], activity['date'], activity['service'], activity['action'], activity['score'])
            )

            aggregate_key = (activity["user_id"], activity["date"])
            daily_aggregates[aggregate_key] = daily_aggregates.get(
                aggregate_key, 0
            ) + int(activity["score"])
        except Exception as e:
            logger.error(f"Error storing activity: {str(e)}")
            continue

    # After inserting activity_logs, aggregate and upsert daily_scores once per user/day.
    for (user_id, date_value), day_total in daily_aggregates.items():
        try:
            existing = execute_query(
                "SELECT total_score FROM daily_scores WHERE user_id = %s AND date = %s",
                (user_id, date_value),
                fetch=True,
            )

            existing_total = int(existing[0]["total_score"]) if existing else 0
            new_total = min(existing_total + int(day_total), DAILY_SCORE_CAP)

            if existing:
                execute_query(
                    "UPDATE daily_scores SET total_score = %s WHERE user_id = %s AND date = %s",
                    (new_total, user_id, date_value),
                )
            else:
                execute_query(
                    "INSERT INTO daily_scores (user_id, date, total_score) VALUES (%s, %s, %s)",
                    (user_id, date_value, new_total),
                )
        except Exception as e:
            logger.error(
                f"Error updating daily score for user_id={user_id} date={date_value}: {str(e)}"
            )
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


# Optional manual trigger when the backend starts.
# If the ingestion module is imported and the environment variable
# PROCESS_LOCAL_CLOUDTRAIL_LOGS_ON_START is set to a truthy value,
# local CloudTrail logs in backend/sample_logs/ will be processed.
if os.getenv("PROCESS_LOCAL_CLOUDTRAIL_LOGS_ON_START", "").lower() in (
    "1",
    "true",
    "yes",
):
    try:
        logger.info(
            "PROCESS_LOCAL_CLOUDTRAIL_LOGS_ON_START is set; "
            "processing local CloudTrail logs from sample_logs."
        )
        process_local_cloudtrail_logs()
    except Exception as e:
        logger.error(
            f"Failed to process local CloudTrail logs on startup: {str(e)}"
        )
