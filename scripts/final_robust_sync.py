import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def robust_sync():
    client = UnidadesClient()
    svc = SupabaseService()
    
    print("\n--- INICIANDO SYNC FINAL (2024+) ---")
    
    # 1. Fetch Modelos
    all_modelos = client._get_paginated_latest("modelos")
    valid_modelos = [m for m in all_modelos if (m.get("data_contrato") or m.get("data") or "") >= "2024-01-01"]
    print(f"Modelos >= 2024: {len(valid_modelos)}")
    
    # 2. Collect References
    required_units = set()
    required_pts = set()
    for m in valid_modelos:
        uid = m.get("unidade")
        if uid is not None: required_units.add(str(uid))
        pid = m.get("consultor_venda")
        if pid is not None: required_pts.add(str(pid))

    # 3. Create Placeholders for EVERYTHING missing
    existing_units = svc.get_all_ids("nexus_unidades")
    missing_units = required_units - existing_units
    if missing_units:
        print(f"Criando {len(missing_units)} placeholders para unidades...")
        batch = [{"id": uid, "nome": f"Unidade {uid} (Ref)", "cidade": "-", "uf": "-", "updated_at": datetime.now().isoformat()} for uid in missing_units]
        for i in range(0, len(batch), 500): svc.upsert_data("nexus_unidades", batch[i:i+500])

    existing_pts = svc.get_all_ids("nexus_participantes")
    missing_pts = required_pts - existing_pts
    if missing_pts:
        print(f"Criando {len(missing_pts)} placeholders para participantes...")
        batch = [{"id": pid, "nome": f"Participante {pid}", "email": None, "ativo": True, "updated_at": datetime.now().isoformat()} for pid in missing_pts]
        for i in range(0, len(batch), 500): svc.upsert_data("nexus_participantes", batch[i:i+500])
        
    # 4. Final Upsert
    msg_batch = []
    for m in valid_modelos:
        dt = m.get("data_contrato") or m.get("data")
        msg_batch.append({
            "id": m.get("id") or m.get("codigo"),
            "unidade_id": m.get("unidade"),
            "consultor_id": m.get("consultor_venda"),
            "data_contrato": dt,
            "valor": m.get("valor") or 0,
            "status": "Cancelado" if m.get("cancelamento") == 1 else "Ativo",
            "raw_data": m,
            "updated_at": datetime.now().isoformat()
        })
        
    success_all = True
    for i in range(0, len(msg_batch), 200):
        if not svc.upsert_data("nexus_modelos", msg_batch[i:i+200]):
            print(f"Chunk {i} failed.")
            success_all = False
            
    if success_all:
        print(f"Sucesso! {len(msg_batch)} modelos sincronizados.")

if __name__ == "__main__":
    robust_sync()
