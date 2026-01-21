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
    
    print("\n--- INICIANDO SYNC ROBUSTO (2024+) ---")
    
    # 1. Fetch Modelos from API
    all_modelos = client._get_paginated_latest("modelos")
    print(f"Total de modelos na API: {len(all_modelos)}")
    
    # 2. Filter for 2024+
    valid_modelos = []
    required_units = set()
    required_participants = set()
    
    for m in all_modelos:
        dt = m.get("data_contrato") or m.get("data")
        if dt and dt >= "2024-01-01":
            valid_modelos.append(m)
            if m.get("unidade"): required_units.add(str(m.get("unidade")))
            if m.get("consultor_venda"): required_participants.add(str(m.get("consultor_venda")))
            
    print(f"Modelos >= 2024: {len(valid_modelos)}")
    
    # 3. Check and Create Placeholders for Units/Participants
    existing_units = svc.get_all_ids("nexus_unidades")
    missing_units = required_units - existing_units
    if missing_units:
        print(f"Criando {len(missing_units)} placeholders para unidades...")
        batch = []
        for uid in missing_units:
            batch.append({
                "id": uid, "nome": f"Unidade {uid} (Ref)",
                "cidade": "-", "uf": "-", "raw_data": {"placeholder": True},
                "updated_at": datetime.now().isoformat()
            })
        for i in range(0, len(batch), 500):
            svc.upsert_data("nexus_unidades", batch[i:i+500])

    existing_participants = svc.get_all_ids("nexus_participantes")
    missing_pts = required_participants - existing_participants
    if missing_pts:
        print(f"Criando {len(missing_pts)} placeholders para participantes...")
        batch = []
        for pid in missing_pts:
            batch.append({
                "id": pid, "nome": f"Participante {pid}",
                "email": None, "ativo": True, "raw_data": {"placeholder": True},
                "updated_at": datetime.now().isoformat()
            })
        for i in range(0, len(batch), 500):
            svc.upsert_data("nexus_participantes", batch[i:i+500])
            
    # 4. Insert Modelos
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
        
    print(f"Inserindo {len(msg_batch)} modelos...")
    for i in range(0, len(msg_batch), 200):
        success = svc.upsert_data("nexus_modelos", msg_batch[i:i+200])
        if success:
            print(f"Chunk {i} ok.")
        else:
            print(f"Chunk {i} FAILED.")
    
    print("--- SYNC FINALIZADO ---")

if __name__ == "__main__":
    robust_sync()
