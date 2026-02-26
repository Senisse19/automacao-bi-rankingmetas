import os
from dotenv import load_dotenv

load_dotenv()

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService
from modules.sync.nexus_runner import sync_contas_receber

client = UnidadesClient()
svc = SupabaseService()

print("Synchronizing contas_receber...")
sync_contas_receber(client, svc)
print("Synchronization complete.")
