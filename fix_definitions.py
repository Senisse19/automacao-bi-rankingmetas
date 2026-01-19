
import os
import requests
from services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("fix_definitions")

def fix_definitions():
    svc = SupabaseService()
    
    # 1. Fetch current definitions
    print("Fetching current definitions...")
    defs = svc._get("automation_definitions")
    print("Current definitions found:", [d['name'] for d in defs])
    
    # 2. Define desired state
    desired = [
        {
            "key": "metas_diarias",
            "name": "Relatório de Metas",
            "description": "Envia relatórios de metas (Geral para Diretoria, Individual para Departamentos)"
        },
        {
            "key": "unidades_diario",
            "name": "Relatório de Unidades (Diário)",
            "description": "Relatório diário de novas unidades, cancelamentos e upsell"
        },
        {
            "key": "unidades_semanal",
            "name": "Relatório de Unidades (Semanal)",
            "description": "Resumo semanal de unidades (Segunda a Domingo anterior)"
        }
    ]
    
    # 3. Upsert Desired
    headers = svc.headers
    url_base = f"{svc.url}/rest/v1/automation_definitions"
    
    for d in desired:
        print(f"Upserting {d['name']} ({d['key']})...")
        # Check if exists by name or key
        # We prefer key as unique identifier if possible, but let's check matches
        
        # Try to update if key exists, else insert.
        # Supabase UPSERT via POST with On-Conflict usually requires header Prefer: resolution=merge-duplicates
        
        # Simpler: Try GET by key first
        existing = [x for x in defs if x['key'] == d['key']]
        if existing:
            # Update
            eid = existing[0]['id']
            resp = requests.patch(f"{url_base}?id=eq.{eid}", json=d, headers=headers)
            if resp.status_code < 300:
                print(f"  ✅ Updated {d['key']}")
            else:
                print(f"  ❌ Error updating {d['key']}: {resp.text}")
        else:
            # Insert
            resp = requests.post(url_base, json=d, headers=headers)
            if resp.status_code < 300:
                print(f"  ✅ Created {d['key']}")
            else:
                print(f"  ❌ Error creating {d['key']}: {resp.text}")

    # 4. Remove unwanted
    unwanted_keys = ["ranking_geral", "unidades"] # 'unidades' was likely the old 'Resumo Unidades' key
    
    # We need to be careful not to delete if 'unidades' IS 'unidades_diario' but just renamed.
    # But if I created 'unidades_diario' new, and 'unidades' exists separately, delete 'unidades'.
    
    # Refresh defs
    defs = svc._get("automation_definitions")
    
    for d in defs:
        if d['key'] in unwanted_keys:
            print(f"Removing deprecated definition: {d['name']} ({d['key']})...")
            # WARNING: This might fail if schedules depend on it.
            # We should probably update schedules first to point to new valid keys if applicable.
            
            # Check schedules
            schedules = svc._get("automation_schedules", params={"automation_definition_id": f"eq.{d['id']}"})
            if schedules:
                print(f"  ⚠️ Warning: {len(schedules)} schedules depend on {d['key']}. Migrating them to safe defaults...")
                
                # Determine target
                target_key = "unidades_diario" if "unidades" in d['key'] else "metas_diarias"
                target_def = next((x for x in defs if x['key'] == target_key), None)
                
                if target_def:
                    for s in schedules:
                        print(f"    Migrating schedule '{s['name']}' to {target_key}...")
                        requests.patch(
                            f"{svc.url}/rest/v1/automation_schedules?id=eq.{s['id']}", 
                            json={"automation_definition_id": target_def['id']},
                            headers=headers
                        )
            
            # Now delete
            resp = requests.delete(f"{url_base}?id=eq.{d['id']}", headers=headers)
            if resp.status_code < 300:
                 print(f"  ✅ Deleted {d['key']}")
            else:
                 print(f"  ❌ Error deleting {d['key']}: {resp.text}")

if __name__ == "__main__":
    fix_definitions()
