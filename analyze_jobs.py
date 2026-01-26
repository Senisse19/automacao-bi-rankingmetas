import requests
import json
from config import NEXUS_CONFIG

url = NEXUS_CONFIG["api_url"] + "/jobs/"
headers = {
    "X-API-KEY": NEXUS_CONFIG["token"],
    "Content-Type": "application/json"
}

resp = requests.get(url, headers=headers, params={"limit": 100})
if resp.status_code == 200:
    items = resp.json()
    if items:
        found = False
        for i in items:
            est = i.get('estimativa_credito')
            hon = i.get('honorarios_apos_rt')
            
            # Print if we find something interesting
            if (est and est > 0) or (hon and hon > 1):
                print(f"--- Job {i.get('codigo')} ---")
                print(f"Mod. Negocio: {i.get('modelo_negocio')}")
                print(f"Divisao: {i.get('job_divisao')}")
                print(f"Linha: {i.get('linha')}")
                print(f"Honorarios: {hon}")
                print(f"Estimativa: {est}")
                print(f"Simulacao: {i.get('simulacao_credito')}")
                print(f"Quantificacao: {i.get('quantificacao_contratada')}")
                print("-" * 20)
                found = True
        
        if not found:
            print("No items with significant values found in first 100.")
else:
    print(resp.text)
