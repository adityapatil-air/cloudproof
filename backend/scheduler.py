"""
CloudProof Auto-Sync Scheduler
Runs daily at a fixed time and syncs CloudTrail logs for all users.
Run this as a separate process: python scheduler.py
"""
import schedule
import time
import sys
import logging
from datetime import datetime
from database import execute_query
from ingestion import process_user_s3_logs
from credentials import decrypt_credential

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SYNC_TIME      = "02:00"   # Run daily at 2:00 AM
MAX_WORKERS    = 3         # Max users syncing simultaneously


def sync_all_users():
    """Fetch all users with credentials and sync their CloudTrail logs."""
    logger.info(f"=== Auto-sync started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

    try:
        users = execute_query(
            """SELECT id, username, email, s3_bucket, s3_prefix, aws_region,
                      aws_access_key_encrypted, aws_secret_key_encrypted
               FROM users
               WHERE s3_bucket IS NOT NULL
               AND aws_access_key_encrypted IS NOT NULL""",
            fetch=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        return

    if not users:
        logger.info("No users with credentials found. Skipping.")
        return

    logger.info(f"Found {len(users)} users to sync.")

    success = 0
    failed  = 0

    for user in users:
        username = user.get('username') or f"user_{user['id']}"
        try:
            # Decrypt stored credentials
            ak = decrypt_credential(user['aws_access_key_encrypted'])
            sk = decrypt_credential(user['aws_secret_key_encrypted'])

            logger.info(f"Syncing @{username} (id={user['id']}) from s3://{user['s3_bucket']}")

            count = process_user_s3_logs(
                user_id       = user['id'],
                bucket_name   = user['s3_bucket'],
                s3_prefix     = user.get('s3_prefix') or '',
                aws_region    = user.get('aws_region') or 'us-east-1',
                aws_access_key= ak,
                aws_secret_key= sk,
            )

            logger.info(f"@{username}: {count} new records processed.")
            success += 1

            # Update last_auto_synced_at
            execute_query(
                "UPDATE users SET last_auto_synced_at = %s WHERE id = %s",
                (datetime.now(), user['id'])
            )

        except Exception as e:
            logger.error(f"@{username} sync failed: {e}")
            failed += 1
            continue

    logger.info(f"=== Auto-sync complete: {success} succeeded, {failed} failed ===")


# ── Schedule ──────────────────────────────────────────────────────────────────
# Only register the schedule when running as a standalone script,
# NOT when imported by app.py (which registers its own schedule).
if __name__ == '__main__':
    schedule.every().day.at(SYNC_TIME).do(sync_all_users)

if __name__ == '__main__':
    logger.info(f"CloudProof Auto-Sync Scheduler started.")
    logger.info(f"Scheduled daily at {SYNC_TIME}.")
    logger.info("Press Ctrl+C to stop.")

    # Run once immediately on startup
    logger.info("Running initial sync on startup...")
    sync_all_users()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
        sys.exit(0)
