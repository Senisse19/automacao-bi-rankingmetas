from core.services.supabase_service import SupabaseService
import datetime

def check():
    print("Initializing SupabaseService...")
    try:
        svc = SupabaseService()
    except Exception as e:
        print(f"Failed to init SupabaseService: {e}")
        return

    print("--- Checking Recent Logs (Last 50) ---")
    try:
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": "50"
        }
        logs = svc._get("automation_logs", params)
            
        if not logs:
            print("No logs found.")
        
        for log in logs:
            ts = log['created_at'].split('.')[0].replace('T', ' ')
            print(f"[{ts}] {log['event_type']} | Job: {log.get('details', {}).get('job_id')} | Details: {log.get('details')}")
            
    except Exception as e:
        print(f"Error fetching logs: {e}")

    print("\n--- Checking Pending Queue Count ---")
    try:
        params = {
            "status": "eq.pending",
            "select": "count", 
        }
        pending = svc.get_pending_jobs() 
        print(f"Pending Jobs in Queue: {len(pending)}")
        if len(pending) > 0:
            print("First 5 pending:")
            for p in pending[:5]:
                print(f"- ID: {p['id']} | SchedID: {p['schedule_id']} | Created: {p['created_at']}")

    except Exception as e:
        print(f"Error checking queue: {e}")

if __name__ == "__main__":
    check()
