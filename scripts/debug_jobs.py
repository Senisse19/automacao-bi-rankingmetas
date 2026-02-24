import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.services.supabase_service import SupabaseService


def main():
    service = SupabaseService()

    # Listar as definições de jobs
    res_def = service._get("automation_definitions", {"select": "*"})
    with open("debug_out.txt", "w", encoding="utf-8") as f:
        f.write("=== JOB DEFINITIONS ===\n")
        for record in res_def:
            f.write(str(record) + "\n")

        f.write("\n=== SCHEDULES ===\n")
        res_sched = service._get("automation_schedules", {"select": "*, definition:automation_definitions(*)"})
        for sched in res_sched:
            if "meta" in sched.get("name", "").lower() or "meta" in sched.get("definition", {}).get("name", "").lower():
                f.write(str(sched) + "\n")


if __name__ == "__main__":
    main()
