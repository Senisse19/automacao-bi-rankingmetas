
import os
import sys

# Add project root to path explicitly
project_root = r"c:\Users\victor.senisse.GRUPOSTUDIO\Desktop\Plataforma BI\ranking-metas-automation"
sys.path.append(project_root)

from services.image_renderer.unidades_renderer import UnidadesRenderer

def generate_mock():
    renderer = UnidadesRenderer()
    
    # Save to images dir
    output_dir = os.path.join(project_root, "images")
    output_path = os.path.join(output_dir, "unidades_daily_mock_filled.png")
    
    # Mock data with rich content to test layout
    data = {
        "date": "2026-01-19",
        "new": [
            {
                "codigo": "1234",
                "nome": "Unidade Exemplar SP",
                "cidade": "São Paulo",
                "uf": "SP",
                "modelo": "Studio Fiscal | Corporate | Partnership License (Modelo Muito Longo Para Teste)",
                "tipo": "Franquia",
                "consultor": "João Silva",
                "gerente": "Maria Souza",
                "valor": 75000.00,
                "rede_distribuicao": "14 - Rede B2C",
                "percentual_retencao": 10.0,
                "anos_contrato": 5,
                "data": "2026-01-19"
            },
            {
                "codigo": "5678",
                "nome": "Unidade Teste Longo Nome Layout",
                "cidade": "Rio de Janeiro",
                "uf": "RJ",
                "modelo": "Studio Energy | Partnership License | Extra Long Name To Force Scale Down",
                "tipo": "Licença",
                "consultor": "Pedro Santos",
                "gerente": "Ana Costa",
                "valor": 45000.00,
                "rede_distribuicao": "3 - Corporate | Area de Distribuição Especializada",
                "percentual_retencao": 5.0,
                "anos_contrato": 2,
                "data": "2026-01-19"
            }
        ],
        "cancelled": [
             {
                "codigo": "9999",
                "nome": "Unidade Cancelada Teste",
                "cidade": "Belo Horizonte",
                "uf": "MG",
                "modelo": "Studio Bank",
                "tipo": "Franquia",
                "consultor": "-",
                "gerente": "-",
                "valor": 0,
                "rede_distribuicao": "-",
                "percentual_retencao": 0,
                "anos_contrato": 0,
                "data_cancelamento": "2026-01-19"
            }
        ],
        "upsell": [] # Keep empty to test partial sections
    }
    
    print("Generating Mock Daily Report...")
    renderer.generate_unidades_reports(data, "daily", output_path)
    print(f"Mock Daily Image generated at: {output_path}")

if __name__ == "__main__":
    generate_mock()
