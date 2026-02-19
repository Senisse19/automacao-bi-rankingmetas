import sys
import os
import json
from dotenv import load_dotenv

# Load env vars from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)
from datetime import datetime, timedelta

# Add project root to path
# Add project root to path (scripts/dev -> ../../)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.unidades_client import UnidadesClient
from modules.jobs.automation import JobsAutomation


def test_unidades():
    print("\n--- Testing Unidades ---")
    client = UnidadesClient()

    # Calculate yesterday
    today = datetime.now()
    days_back = 3 if today.weekday() == 0 else 1
    ref_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")

    print(f"Checking data for date: {ref_date}")

    data = client.fetch_data_for_range(ref_date, ref_date)

    new_len = len(data.get("new", []))
    cnc_len = len(data.get("cancelled", []))
    ups_len = len(data.get("upsell", []))

    print(f"New: {new_len}")
    print(f"Cancelled: {cnc_len}")
    print(f"Upsell: {ups_len}")

    if new_len > 0:
        print("First New Item:", json.dumps(data["new"][0], indent=2, default=str))
    if cnc_len > 0:
        print(
            "First Cancelled Item:",
            json.dumps(data["cancelled"][0], indent=2, default=str),
        )


def test_jobs():
    print("\n--- Testing Jobs ---")
    JobsAutomation()

    # Calculate yesterday
    today = datetime.now()
    days_back = 3 if today.weekday() == 0 else 1
    ref_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")

    print(f"Checking jobs for date: {ref_date}")

    print("Checking jobs (latest 1)...")

    try:
        from core.services.supabase_service import SupabaseService

        svc = SupabaseService()
        jobs = svc._get("nexus_jobs", {"select": "*", "limit": "1", "order": "created_at.desc"})

        if jobs:
            print("Latest Job Found:", json.dumps(jobs[0], indent=2, default=str))
        else:
            print("❌ No jobs found in table 'nexus_jobs'.")

    except Exception as e:
        print(f"Error fetching raw jobs: {e}")


if __name__ == "__main__":
    test_unidades()
    test_jobs()
