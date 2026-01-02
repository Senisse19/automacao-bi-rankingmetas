"""
Cliente SharePoint usando Microsoft Graph API
"""
import requests
import base64
from datetime import datetime
from config import SHAREPOINT_CONFIG


class SharePointClient:
    def __init__(self):
        self.config = SHAREPOINT_CONFIG
        self.access_token = None
        self.token_url = f"https://login.microsoftonline.com/{self.config['tenant']}/oauth2/v2.0/token"
        self.graph_url = "https://graph.microsoft.com/v1.0"
    
    def authenticate(self) -> bool:
        """Autentica com Microsoft Graph usando client credentials"""
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "scope": "https://graph.microsoft.com/.default"
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            self.access_token = response.json().get("access_token")
            print("✅ Autenticação SharePoint realizada com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na autenticação SharePoint: {e}")
            return False
    
    def _get_headers(self) -> dict:
        """Retorna headers com token de autenticação"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def list_files_in_folder(self) -> list:
        """Lista todos os arquivos na pasta Diretoria"""
        if not self.access_token:
            if not self.authenticate():
                return []
        
        try:
            site_id = self.config["site_id"]
            folder_id = self.config["folder_id"]
            
            # Endpoint para listar arquivos na pasta
            url = f"{self.graph_url}/sites/{site_id}/drive/items/{folder_id}/children"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            files = response.json().get("value", [])
            # Filtrar apenas arquivos (excluir pastas)
            files = [f for f in files if f.get("file")]
            
            print(f"📁 Encontrados {len(files)} arquivo(s) na pasta Diretoria")
            return files
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao listar arquivos: {e}")
            return []
    
    def get_latest_file(self) -> dict | None:
        """Retorna o arquivo mais recente da pasta"""
        files = self.list_files_in_folder()
        
        if not files:
            print("⚠️ Nenhum arquivo encontrado na pasta")
            return None
        
        # Ordenar por data de modificação (mais recente primeiro)
        sorted_files = sorted(
            files,
            key=lambda x: datetime.fromisoformat(x.get("lastModifiedDateTime", "").replace("Z", "+00:00")),
            reverse=True
        )
        
        latest = sorted_files[0]
        print(f"📄 Arquivo mais recente: {latest.get('name')} (modificado em {latest.get('lastModifiedDateTime')})")
        return latest
    
    def download_file(self, file_id: str) -> tuple[bytes, str] | tuple[None, None]:
        """Baixa o conteúdo de um arquivo e retorna (bytes, nome)"""
        if not self.access_token:
            if not self.authenticate():
                return None, None
        
        try:
            site_id = self.config["site_id"]
            
            # Primeiro, pegar metadados do arquivo
            meta_url = f"{self.graph_url}/sites/{site_id}/drive/items/{file_id}"
            meta_response = requests.get(meta_url, headers=self._get_headers())
            meta_response.raise_for_status()
            file_info = meta_response.json()
            file_name = file_info.get("name", "arquivo.pdf")
            
            # Baixar conteúdo do arquivo
            url = f"{self.graph_url}/sites/{site_id}/drive/items/{file_id}/content"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            print(f"✅ Arquivo '{file_name}' baixado com sucesso ({len(response.content)} bytes)")
            return response.content, file_name
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao baixar arquivo: {e}")
            return None, None
    
    def get_latest_file_as_base64(self) -> tuple[str, str] | tuple[None, None]:
        """Baixa o arquivo mais recente e retorna como base64"""
        latest_file = self.get_latest_file()
        
        if not latest_file:
            return None, None
        
        file_content, file_name = self.download_file(latest_file["id"])
        
        if file_content:
            base64_content = base64.b64encode(file_content).decode("utf-8")
            return base64_content, file_name
        
        return None, None
