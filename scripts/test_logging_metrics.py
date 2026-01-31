
import sys
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger, log_error
from utils.metrics import track_error_detail, METRICS_DIR

logger = get_logger("test_verifier")

def verify_logging_metrics():
    print("🚀 Starting Logging & Metrics Verification...")
    
    # 1. Test Standard Logging
    test_msg_info = f"Test INFO log entry {datetime.now().timestamp()}"
    test_msg_error = f"Test ERROR log entry {datetime.now().timestamp()}"
    
    logger.info(test_msg_info)
    log_error("TestError", test_msg_error)
    
    # Verify in log file
    log_file = Path("logs/market_rover.log")
    if not log_file.exists():
        print("❌ CRITICAL: Log file not found!")
        return False
        
    with open(log_file, 'r', encoding='utf-8') as f:
        log_content = f.read()
        
    if test_msg_info in log_content:
        print("✅ INFO log entry found.")
    else:
        print("❌ INFO log entry MISSING.")
        
    if test_msg_error in log_content:
        print("✅ ERROR log entry found.")
    else:
        print("❌ ERROR log entry MISSING.")

    # 2. Test Detailed Error Tracking (Metrics)
    test_error_type = "VerificationTestError"
    test_error_msg = f"Simulated crash for verification {datetime.now().timestamp()}"
    context = {"test_run": True, "timestamp": str(datetime.now())}
    
    track_error_detail(test_error_type, test_error_msg, context)
    
    # Verify in metrics file
    today = datetime.now(timezone.utc).date().isoformat()
    metrics_file = METRICS_DIR / f"errors_{today}.jsonl"
    
    if not metrics_file.exists():
        print(f"❌ CRITICAL: Metrics file {metrics_file} not found!")
        return False
        
    found_metric = False
    with open(metrics_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("message") == test_error_msg and rec.get("type") == test_error_type:
                    found_metric = True
                    break
            except json.JSONDecodeError:
                continue
                
    if found_metric:
        print("✅ Detailed Error Metric found in JSONL.")
    else:
        print("❌ Detailed Error Metric MISSING.")
        
    return True

if __name__ == "__main__":
    verify_logging_metrics()
