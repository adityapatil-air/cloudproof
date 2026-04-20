import boto3
import json
import gzip
import re
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from io import BytesIO
from scoring import calculate_score, DAILY_SCORE_CAP, SERVICE_DAILY_CAP, ACTION_DAILY_CAP
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
        daily_action_scores = {}
        
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
                                    action_key = f"{date_key}_{service}_{action}"
                                    
                                    # Apply daily caps
                                    if date_key not in daily_totals:
                                        daily_totals[date_key] = 0
                                    if service_key not in daily_service_scores:
                                        daily_service_scores[service_key] = 0
                                    if action_key not in daily_action_scores:
                                        daily_action_scores[action_key] = 0
                                    
                                    if daily_totals[date_key] >= DAILY_SCORE_CAP:
                                        continue
                                    if daily_service_scores[service_key] >= SERVICE_DAILY_CAP:
                                        continue
                                    if daily_action_scores[action_key] >= ACTION_DAILY_CAP:
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
                                    daily_action_scores[action_key] += score
                                    
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


# ── Fraud Prevention ─────────────────────────────────────────────────────────

def _validate_arn_ownership(records, registered_account_id):
    """Layer 1: Verify every event ARN belongs to the registered AWS account."""
    if not registered_account_id:
        return True
    for record in records:
        arn = record.get('userIdentity', {}).get('arn', '')
        if arn:
            parts = arn.split(':')
            if len(parts) >= 5 and parts[4] and parts[4] != registered_account_id:
                logger.warning(f"ARN mismatch: {arn} vs registered {registered_account_id}")
                return False
    return True


def _validate_log_metadata(records, s3_key):
    """Layer 2: Validate structural patterns - catches manually crafted fake logs."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    )
    filename = s3_key.split('/')[-1]
    time_match = re.search(r'_(\d{8}T\d{4}Z)_', filename)
    filename_time = None
    if time_match:
        try:
            filename_time = datetime.strptime(time_match.group(1), '%Y%m%dT%H%MZ')
        except Exception:
            pass

    for record in records:
        # Check 1: eventID must be valid UUID
        event_id = record.get('eventID', '')
        if event_id and not uuid_pattern.match(event_id):
            logger.warning(f"Invalid eventID format: {event_id} in {s3_key}")
            return False

        # Check 2: eventTime must be within 2 hours of filename timestamp
        if filename_time:
            try:
                event_time = datetime.strptime(record['eventTime'], '%Y-%m-%dT%H:%M:%SZ')
                if abs((event_time - filename_time).total_seconds()) > 7200:
                    logger.warning(f"Event time {event_time} too far from filename time {filename_time}")
                    return False
            except Exception:
                pass

        # Check 3: Suspicious source IPs
        source_ip = record.get('sourceIPAddress', '')
        if source_ip in ['127.0.0.1', 'localhost', '0.0.0.0']:
            logger.warning(f"Suspicious sourceIPAddress: {source_ip} in {s3_key}")
            return False

    return True


def _verify_sample_via_api(records, ak, sk, region, sample_rate=0.1):
    """Layer 3: Randomly verify 10% of scoreable events via CloudTrail API - cannot be faked."""
    if not ak or not sk:
        return True

    # Only verify events that actually score points (not read-only actions)
    from scoring import calculate_score, should_ignore_action
    scoreable = [
        r for r in records
        if r.get('eventID')
        and not r.get('readOnly', False)
        and not should_ignore_action(r.get('eventName', ''))
        and calculate_score(
            r.get('eventSource', '').split('.')[0].upper(),
            r.get('eventName', '')
        ) > 0
    ]
    if not scoreable:
        return True

    sample_size = max(1, int(len(scoreable) * sample_rate))
    sample = random.sample(scoreable, min(sample_size, len(scoreable)))

    try:
        # Group records by region so we create one client per region, not per record
        from collections import defaultdict
        by_region = defaultdict(list)
        for record in sample:
            event_region = record.get('awsRegion') or region
            by_region[event_region].append(record)

        for event_region, region_records in by_region.items():
            cloudtrail = boto3.client(
                'cloudtrail',
                aws_access_key_id=ak,
                aws_secret_access_key=sk,
                region_name=event_region
            )
            for record in region_records:
                event_id    = record.get('eventID')
                event_name  = record.get('eventName')
                event_time  = datetime.strptime(record['eventTime'], '%Y-%m-%dT%H:%M:%SZ')

                response = cloudtrail.lookup_events(
                    LookupAttributes=[{'AttributeKey': 'EventId', 'AttributeValue': event_id}],
                    StartTime=event_time - timedelta(minutes=20),
                    EndTime=event_time   + timedelta(minutes=20),
                    MaxResults=1
                )
                if not response.get('Events'):
                    logger.warning(f"Event {event_id} ({event_name}) not found in CloudTrail API - possible fake!")
                    return False

                api_name = response['Events'][0].get('EventName', '')
                if api_name != event_name:
                    logger.warning(f"Event name mismatch: log={event_name} api={api_name}")
                    return False

    except Exception as e:
        logger.warning(f"CloudTrail API verification skipped: {e}")

    return True


# ── Main ingestion ────────────────────────────────────────────────────────────

def process_user_s3_logs(
    user_id: int,
    bucket_name: str,
    s3_prefix: str = '',
    aws_region: str = 'us-east-1',
    aws_access_key: str = None,
    aws_secret_key: str = None,
    progress_callback=None,
) -> int:
    """
    Process CloudTrail logs for a specific user from their own S3 bucket.
    If aws_access_key/aws_secret_key are provided, uses those credentials.
    Otherwise falls back to the machine's ambient AWS credential chain.

    progress_callback(event, value) is called with:
      ('total', n)       — total number of files to process
      ('batch_done', n)  — n records processed in the latest batch
    """
    WORKERS = 25

    if aws_access_key and aws_secret_key:
        s3 = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            config=boto3.session.Config(max_pool_connections=WORKERS),
        )
    else:
        s3 = boto3.client(
            's3',
            region_name=aws_region,
            config=boto3.session.Config(max_pool_connections=WORKERS),
        )

    # Fetch registered AWS account ID for fraud validation
    user_row = execute_query(
        "SELECT aws_account_id FROM users WHERE id = %s",
        (user_id,), fetch=True
    )
    registered_account_id = user_row[0]['aws_account_id'] if user_row else None

    last_processed = get_last_processed_timestamp(user_id)
    if last_processed is not None:
        last_processed = last_processed.replace(tzinfo=None)

    # ── Collect all eligible file keys first so we can report a total ─────────
    file_keys = []
    paginator = s3.get_paginator('list_objects_v2')
    paginate_kwargs = {'Bucket': bucket_name}
    if s3_prefix:
        paginate_kwargs['Prefix'] = s3_prefix

    for page in paginator.paginate(**paginate_kwargs):
        for obj in page.get('Contents', []):
            key = obj.get('Key')
            if not key:
                continue
            if last_processed is not None:
                if obj['LastModified'].replace(tzinfo=None) <= last_processed:
                    continue
            if not (key.endswith('.json') or key.endswith('.json.gz')):
                continue
            file_keys.append(key)

    if progress_callback:
        progress_callback('total', len(file_keys))

    # ── Per-file download + parse (runs in parallel) ──────────────────────────
    def download_and_parse(key):
        """Download one S3 file, validate it, and return scored activities."""
        try:
            s3_obj = s3.get_object(Bucket=bucket_name, Key=key)
            if key.endswith('.gz'):
                with gzip.GzipFile(fileobj=BytesIO(s3_obj['Body'].read())) as gz:
                    log_data = json.loads(gz.read())
            else:
                log_data = json.loads(s3_obj['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.warning(f"Error reading s3://{bucket_name}/{key}: {e}")
            return []

        records = log_data.get('Records', [])

        # 3-Layer fraud validation
        if not _validate_arn_ownership(records, registered_account_id):
            logger.warning(f"FRAUD: ARN mismatch in {key} for user {user_id} - skipping")
            return []
        if not _validate_log_metadata(records, key):
            logger.warning(f"FRAUD: Metadata invalid in {key} for user {user_id} - skipping")
            return []
        if not _verify_sample_via_api(records, aws_access_key, aws_secret_key, aws_region):
            logger.warning(f"FRAUD: API verification failed in {key} for user {user_id} - skipping")
            return []

        file_activities = []
        for record in records:
            try:
                read_only = record.get('readOnly')
                if isinstance(read_only, str):
                    if read_only.lower() == 'true':
                        continue
                elif read_only is True:
                    continue

                event_time_str = record.get('eventTime')
                event_source   = record.get('eventSource', '')
                event_name     = record.get('eventName', '')

                if not event_time_str or not event_source or not event_name:
                    continue

                event_time = datetime.strptime(event_time_str, '%Y-%m-%dT%H:%M:%SZ')
                service    = event_source.split('.')[0].upper()
                score      = calculate_score(service, event_name)
                if score <= 0:
                    continue

                file_activities.append({
                    'user_id':  user_id,
                    'date':     event_time.date(),
                    'service':  service,
                    'action':   event_name,
                    'score':    score,
                    'event_id': record.get('eventID'),
                })
            except Exception as e:
                logger.warning(f"Error processing record from {key}: {e}")
                continue

        return file_activities

    # ── Run downloads in parallel (25 workers) ────────────────────────────────
    all_activities = []
    files_done = 0
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(download_and_parse, key): key for key in file_keys}
        for future in as_completed(futures):
            result = future.result()
            with lock:
                all_activities.extend(result)
                files_done += 1
            if progress_callback and files_done % 10 == 0:
                progress_callback('batch_done', 10)

    remainder = files_done % 10
    if progress_callback and remainder > 0:
        progress_callback('batch_done', remainder)

    # ── Apply daily caps across all collected activities ───────────────────────
    # Must be done sequentially after parallel download to keep caps consistent
    daily_totals         = {}
    daily_service_scores = {}
    daily_action_scores  = {}
    capped_activities    = []

    # Sort by date so caps are applied chronologically
    all_activities.sort(key=lambda x: x['date'])

    for activity in all_activities:
        date_key    = activity['date']
        service_key = f"{date_key}_{activity['service']}"
        action_key  = f"{date_key}_{activity['service']}_{activity['action']}"

        daily_totals.setdefault(date_key, 0)
        daily_service_scores.setdefault(service_key, 0)
        daily_action_scores.setdefault(action_key, 0)

        if daily_totals[date_key]            >= DAILY_SCORE_CAP:   continue
        if daily_service_scores[service_key] >= SERVICE_DAILY_CAP: continue
        if daily_action_scores[action_key]   >= ACTION_DAILY_CAP:  continue

        capped_activities.append(activity)
        daily_totals[date_key]            += activity['score']
        daily_service_scores[service_key] += activity['score']
        daily_action_scores[action_key]   += activity['score']

    # ── Store and return ──────────────────────────────────────────────────────
    total_records = 0
    if capped_activities:
        store_activities(capped_activities)
        total_records = len(capped_activities)
        logger.info(f"Parallel sync complete: {total_records} activities for user {user_id} from {len(file_keys)} files")

    try:
        update_last_processed_timestamp(user_id, datetime.now())
    except Exception as e:
        logger.error(f"Error updating last processed timestamp: {str(e)}")

    return total_records


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
    daily_action_scores = {}

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
                action_key = f"{date_key}_{service}_{action}"

                if date_key not in daily_totals:
                    daily_totals[date_key] = 0
                if service_key not in daily_service_scores:
                    daily_service_scores[service_key] = 0
                if action_key not in daily_action_scores:
                    daily_action_scores[action_key] = 0

                if daily_totals[date_key] >= DAILY_SCORE_CAP:
                    continue
                if daily_service_scores[service_key] >= SERVICE_DAILY_CAP:
                    continue
                if daily_action_scores[action_key] >= ACTION_DAILY_CAP:
                    continue

                activities.append(
                    {
                        "user_id": user_id,
                        "date": date_key,
                        "service": service,
                        "action": action,
                        "score": score,
                        "event_id": record.get("eventID"),
                    }
                )

                daily_totals[date_key] += score
                daily_service_scores[service_key] += score
                daily_action_scores[action_key] += score

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


def process_s3_cloudtrail_logs(bucket_name):
    """
    Process CloudTrail-style JSON or JSON.GZ log files from the given S3
    bucket and update activity and daily scores.
    Uses the same scoring and aggregation logic as process_local_cloudtrail_logs().
    """
    # Reuse the same user id resolution logic as local ingestion.
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

    s3 = boto3.client("s3")

    # Fetch last processed timestamp to avoid reprocessing older objects.
    last_processed = get_last_processed_timestamp(user_id)
    if last_processed is not None:
        # Normalize to naive datetime for safe comparison.
        last_processed = last_processed.replace(tzinfo=None)

    activities = []
    daily_service_scores = {}
    daily_totals = {}
    daily_action_scores = {}

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name)

    for page in page_iterator:
        for obj in page.get("Contents", []):
            key = obj.get("Key")
            if not key:
                continue

            if last_processed is not None:
                # S3 returns timezone-aware datetimes; strip tzinfo before comparison.
                if obj["LastModified"].replace(tzinfo=None) <= last_processed:
                    continue

            if not (key.endswith(".json") or key.endswith(".json.gz")):
                continue

            try:
                s3_obj = s3.get_object(Bucket=bucket_name, Key=key)

                if key.endswith(".gz"):
                    with gzip.GzipFile(
                        fileobj=BytesIO(s3_obj["Body"].read())
                    ) as gzipfile:
                        content = gzipfile.read()
                        log_data = json.loads(content)
                else:
                    body_bytes = s3_obj["Body"].read()
                    log_data = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                logger.warning(
                    f"Error reading S3 log file s3://{bucket_name}/{key}: {str(e)}"
                )
                continue

            for record in log_data.get("Records", []):
                try:
                    # Skip read-only events (same as local ingestion).
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
                    action_key = f"{date_key}_{service}_{action}"

                    if date_key not in daily_totals:
                        daily_totals[date_key] = 0
                    if service_key not in daily_service_scores:
                        daily_service_scores[service_key] = 0
                    if action_key not in daily_action_scores:
                        daily_action_scores[action_key] = 0

                    if daily_totals[date_key] >= DAILY_SCORE_CAP:
                        continue
                    if daily_service_scores[service_key] >= SERVICE_DAILY_CAP:
                        continue
                    if daily_action_scores[action_key] >= ACTION_DAILY_CAP:
                        continue

                    activities.append(
                        {
                            "user_id": user_id,
                            "date": date_key,
                            "service": service,
                            "action": action,
                            "score": score,
                            "event_id": record.get("eventID"),
                        }
                    )

                    daily_totals[date_key] += score
                    daily_service_scores[service_key] += score
                    daily_action_scores[action_key] += score

                except Exception as e:
                    logger.warning(
                        f"Error processing S3 record from {key}: {str(e)}"
                    )
                    continue

    if activities:
        store_activities(activities)
        logger.info(
            f"Stored {len(activities)} S3 activities for user {user_id} "
            f"from bucket {bucket_name}"
        )

    # Update processing state after successful run to prevent duplicate processing.
    try:
        update_last_processed_timestamp(user_id, datetime.now())
    except Exception as e:
        logger.error(
            f"Error updating last processed timestamp after S3 ingestion: {str(e)}"
        )

    return len(activities)

# Global write lock for SQLite — prevents "database locked" under parallel ingestion
_sqlite_write_lock = threading.Lock()


def store_activities(activities):
    """
    Bulk-insert scored activities using INSERT OR IGNORE for dedup,
    then upsert daily_scores — all in a single DB connection.
    """
    if not activities:
        return

    from database import get_db_connection, DB_ENGINE, _convert_sqlite_placeholders

    lock_ctx = _sqlite_write_lock if DB_ENGINE == 'sqlite' else threading.nullcontext()
    with lock_ctx:
        conn = get_db_connection()
    try:
        cursor = conn.cursor()
        daily_aggregates = {}

        if DB_ENGINE == 'sqlite':
            insert_sql = (
                "INSERT OR IGNORE INTO activity_logs "
                "(user_id, date, service, action, score, event_id) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            )
        else:
            insert_sql = (
                "INSERT INTO activity_logs "
                "(user_id, date, service, action, score, event_id) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (user_id, event_id) DO NOTHING"
            )

        for activity in activities:
            try:
                row = (
                    activity['user_id'], activity['date'],
                    activity['service'], activity['action'],
                    activity['score'], activity.get('event_id'),
                )
                cursor.execute(insert_sql, row)
                if cursor.rowcount > 0:
                    key = (activity['user_id'], activity['date'])
                    daily_aggregates[key] = daily_aggregates.get(key, 0) + int(activity['score'])
            except Exception as e:
                logger.error(f"Error storing activity: {e}")
                continue

        # Upsert daily_scores in the same connection
        for (user_id, date_value), day_total in daily_aggregates.items():
            try:
                if DB_ENGINE == 'sqlite':
                    cursor.execute(
                        "SELECT total_score FROM daily_scores WHERE user_id = ? AND date = ?",
                        (user_id, date_value)
                    )
                    row = cursor.fetchone()
                    existing_total = int(row[0]) if row else 0
                    new_total = min(existing_total + day_total, DAILY_SCORE_CAP)
                    if row:
                        cursor.execute(
                            "UPDATE daily_scores SET total_score = ? WHERE user_id = ? AND date = ?",
                            (new_total, user_id, date_value)
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO daily_scores (user_id, date, total_score) VALUES (?, ?, ?)",
                            (user_id, date_value, new_total)
                        )
                else:
                    cursor.execute(
                        "INSERT INTO daily_scores (user_id, date, total_score) VALUES (%s, %s, %s) "
                        "ON CONFLICT (user_id, date) DO UPDATE "
                        "SET total_score = LEAST(daily_scores.total_score + EXCLUDED.total_score, %s)",
                        (user_id, date_value, min(day_total, DAILY_SCORE_CAP), DAILY_SCORE_CAP)
                    )
            except Exception as e:
                logger.error(f"Error updating daily score for user_id={user_id} date={date_value}: {e}")
                continue

        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"store_activities failed: {e}")
        raise
    finally:
        conn.close()

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
        from database import DB_ENGINE
        existing = execute_query(
            "SELECT id FROM processing_state WHERE user_id = %s",
            (user_id,), fetch=True
        )
        if existing:
            execute_query(
                "UPDATE processing_state SET last_processed_timestamp = %s WHERE user_id = %s",
                (timestamp, user_id)
            )
        else:
            execute_query(
                "INSERT INTO processing_state (user_id, last_processed_timestamp) VALUES (%s, %s)",
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
