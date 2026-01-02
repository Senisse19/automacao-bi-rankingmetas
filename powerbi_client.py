"""
Cliente Power BI usando Microsoft Graph API
Exporta relatórios como PNG para envio via WhatsApp
"""
import requests
import base64
import time
from config import POWERBI_CONFIG


class PowerBIClient:
    def __init__(self):
        self.config = POWERBI_CONFIG
        self.access_token = None
        self.token_url = f"https://login.microsoftonline.com/{self.config['tenant']}/oauth2/v2.0/token"
        self.api_url = "https://api.powerbi.com/v1.0/myorg"
    
    def authenticate(self) -> bool:
        """Autentica com Microsoft Graph usando client credentials"""
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "scope": "https://analysis.windows.net/powerbi/api/.default"
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            self.access_token = response.json().get("access_token")
            print("✅ Autenticação Power BI realizada com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na autenticação Power BI: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return False
    
    def _get_headers(self) -> dict:
        """Retorna headers com token de autenticação"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_report_by_name(self, report_name: str) -> dict | None:
        """Busca um relatório pelo nome no workspace configurado"""
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            workspace_id = self.config["workspace_id"]
            url = f"{self.api_url}/groups/{workspace_id}/reports"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            reports = response.json().get("value", [])
            
            for report in reports:
                if report.get("name") == report_name:
                    print(f"📊 Relatório encontrado: {report_name} (ID: {report['id']})")
                    return report
            
            print(f"⚠️ Relatório '{report_name}' não encontrado no workspace")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao buscar relatório: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return None
    
    def export_report_to_png(self, report_id: str) -> bytes | None:
        """
        Exporta relatório como PNG (operação assíncrona)
        Retorna os bytes do arquivo PNG ou None em caso de erro
        """
        if not self.access_token:
            if not self.authenticate():
                return None
        
        try:
            workspace_id = self.config["workspace_id"]
            
            # 1. Iniciar exportação
            export_url = f"{self.api_url}/groups/{workspace_id}/reports/{report_id}/ExportTo"
            
            export_config = {
                "format": "PNG"
            }
            
            print("📤 Iniciando exportação do relatório para PNG...")
            response = requests.post(export_url, json=export_config, headers=self._get_headers())
            response.raise_for_status()
            
            export_data = response.json()
            export_id = export_data.get("id")
            
            if not export_id:
                print("❌ Não foi possível iniciar a exportação")
                return None
            
            print(f"   Export ID: {export_id}")
            
            # 2. Polling para verificar status da exportação
            status_url = f"{self.api_url}/groups/{workspace_id}/reports/{report_id}/exports/{export_id}"
            max_attempts = 60  # Máximo 5 minutos (60 * 5 segundos)
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(5)  # Aguarda 5 segundos entre verificações
                attempt += 1
                
                status_response = requests.get(status_url, headers=self._get_headers())
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data.get("status")
                percent_complete = status_data.get("percentComplete", 0)
                
                print(f"   Status: {status} ({percent_complete}%)")
                
                if status == "Succeeded":
                    break
                elif status == "Failed":
                    print(f"❌ Exportação falhou: {status_data.get('reportName', 'erro desconhecido')}")
                    return None
            
            if status != "Succeeded":
                print("❌ Timeout na exportação do relatório")
                return None
            
            # 3. Baixar arquivo exportado
            file_url = f"{status_url}/file"
            file_response = requests.get(file_url, headers=self._get_headers())
            file_response.raise_for_status()
            
            print(f"✅ Relatório exportado com sucesso ({len(file_response.content)} bytes)")
            return file_response.content
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao exportar relatório: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return None
    
    def export_report_as_base64(self, report_name: str = None) -> tuple[str, str] | tuple[None, None]:
        """
        Exporta relatório como PNG e retorna em base64
        Retorna (base64_content, filename) ou (None, None) em caso de erro
        """
        # Usar nome do relatório configurado se não especificado
        if report_name is None:
            report_name = self.config.get("report_name", "Ranking_Metas")
        
        # Buscar relatório pelo nome
        report = self.get_report_by_name(report_name)
        if not report:
            return None, None
        
        # Exportar como PNG
        png_content = self.export_report_to_png(report["id"])
        if not png_content:
            return None, None
        
        # Converter para base64
        base64_content = base64.b64encode(png_content).decode("utf-8")
        filename = f"{report_name}.png"
        
        return base64_content, filename
