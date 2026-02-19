import schedule
import time
import sys
from database import execute_query
from ingestion import process_cloudtrail_logs
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ingestion_job():
    logger.info(f"Starting ingestion job at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        users = execute_query(
            "SELECT id, role_arn, email FROM users",
            fetch=True
        )
        
        if not users:
            logger.info("No users found to process")
            return
        
        for user in users:
            try:
                # Extract bucket name from role ARN or use convention
                bucket_name = f"cloudtrail-logs-{user['id']}"
                
                logger.info(f"Processing user {user['id']} ({user['email']})")
                count = process_cloudtrail_logs(user['id'], user['role_arn'], bucket_name)
                logger.info(f"Processed {count} activities for user {user['id']}")
                
            except Exception as e:
                logger.error(f"Error processing user {user['id']}: {str(e)}")
                continue
        
        logger.info("Ingestion job completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in ingestion job: {str(e)}")
        sys.exit(1)

schedule.every(30).minutes.do(run_ingestion_job)

if __name__ == '__main__':
    logger.info("CloudProof Ingestion Scheduler Started")
    logger.info("Running initial ingestion job...")
    
    try:
        run_ingestion_job()
    except Exception as e:
        logger.error(f"Initial job failed: {str(e)}")
    
    logger.info("Scheduler running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
