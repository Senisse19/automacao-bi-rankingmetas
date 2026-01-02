"""
Cliente Evolution API para envio de mensagens WhatsApp
"""
import requests
from config import EVOLUTION_CONFIG


class EvolutionClient:
    def __init__(self):
        self.config = EVOLUTION_CONFIG
        self.base_url = self.config["server_url"]
        self.api_key = self.config["api_key"]
        self.instance = self.config["instance_name"]
    
    def _get_headers(self) -> dict:
        """Retorna headers com API key"""
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
    
    def check_instance_status(self) -> bool:
        """Verifica se a instância está conectada"""
        try:
            url = f"{self.base_url}/instance/connectionState/{self.instance}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            state = data.get("instance", {}).get("state", "unknown")
            
            if state == "open":
                print(f"✅ Instância '{self.instance}' está conectada")
                return True
            else:
                print(f"⚠️ Instância '{self.instance}' não está conectada (estado: {state})")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao verificar instância: {e}")
            return False
    
    def send_document(self, file_base64: str, file_name: str, caption: str = None) -> bool:
        """Envia um documento para o grupo do WhatsApp"""
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            # Detectar tipo MIME baseado na extensão
            extension = file_name.lower().split(".")[-1] if "." in file_name else "pdf"
            mime_types = {
                "pdf": "application/pdf",
                "doc": "application/msword",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xls": "application/vnd.ms-excel",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "ppt": "application/vnd.ms-powerpoint",
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
            }
            mime_type = mime_types.get(extension, "application/octet-stream")
            
            payload = {
                "number": self.config["group_id"],
                "mediatype": "document",
                "mimetype": mime_type,
                "caption": caption or f"📄 {file_name}",
                "media": file_base64,
                "fileName": file_name
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("key"):
                print(f"✅ Documento '{file_name}' enviado com sucesso para o grupo!")
                return True
            else:
                print(f"⚠️ Resposta inesperada: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar documento: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return False
    
    def send_image(self, image_base64: str, caption: str = None) -> bool:
        """Envia uma imagem para o grupo do WhatsApp"""
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            payload = {
                "number": self.config["group_id"],
                "mediatype": "image",
                "mimetype": "image/png",
                "caption": caption or "📊 Relatório",
                "media": image_base64,
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("key"):
                print("✅ Imagem enviada com sucesso para o grupo!")
                return True
            else:
                print(f"⚠️ Resposta inesperada: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar imagem: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return False
    
    def send_text_message(self, message: str) -> bool:
        """Envia uma mensagem de texto para o grupo"""
        try:
            url = f"{self.base_url}/message/sendText/{self.instance}"
            
            payload = {
                "number": self.config["group_id"],
                "text": message
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            print(f"✅ Mensagem de texto enviada com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
