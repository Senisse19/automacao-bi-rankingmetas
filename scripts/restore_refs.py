import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService
from scripts.sync_nexus_to_supabase import sync_unidades, sync_participantes

if __name__ == "__main__":
    client = UnidadesClient()
    svc = SupabaseService()
    
    print("--- Restoring Unidades ---")
    sync_unidades(client, svc)
    print("--- Restoring Participantes ---")
    sync_participantes(client, svc)
    print("--- Done ---")
