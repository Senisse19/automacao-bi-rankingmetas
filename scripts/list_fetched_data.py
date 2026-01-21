import os
import sys
from datetime import datetime, timedelta
import json

# Fix path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.clients.unidades_client import UnidadesClient

def list_data():
    client = UnidadesClient()
    
    # Fetch data for last 30 days
    today = datetime.now()
    d_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    d_end = today.strftime("%Y-%m-%d")
    
    print(f"--- DADOS RECUPERADOS: {d_start} até {d_end} ---\n")
    
    data = client.fetch_data_for_range(d_start, d_end)
    
    all_items = data.get("new", []) + data.get("cancelled", []) + data.get("upsell", [])
    # Limit to display
    all_items = all_items[-5:]
    
    for i, item in enumerate(all_items):
        # Resolve Name Logic (Simulated from Renderer)
        val_cod = item.get("codigo", "")
        nome = item.get("nome", "-")
        display_name = nome
        if not "Unidade" in str(display_name) and val_cod:
                display_name = f"Unidade {val_cod} - {display_name}"
        
        print(f"ITEM {i+1}:")
        print(f"  Nome Exibido:       {display_name}")
        print(f"  Cidade/UF:          {item.get('cidade')} - {item.get('uf')}")
        print(f"  Modelo:             {item.get('modelo')}")
        print(f"  Rede Distribuição:  {item.get('tipo')}") # This is type_name from client
        print(f"  Valor Aquisição:    R$ {item.get('valor')}")
        print(f"  Tempo Contrato:     {item.get('anos_contrato')} anos")
        
        consultor = item.get("consultor")
        if not consultor: consultor = item.get("rede_distribuicao", "N/A")
        print(f"  Consultor:          {consultor}")
        print("-" * 40)

if __name__ == "__main__":
    list_data()
