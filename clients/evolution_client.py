"""
Cliente Evolution API para envio de mensagens WhatsApp
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import EVOLUTION_CONFIG
from utils.logger import get_logger

logger = get_logger("evolution_client")


class EvolutionClient:
    def __init__(self):
        self.config = EVOLUTION_CONFIG
        self.base_url = self.config["server_url"]
        self.api_key = self.config["api_key"]
        self.instance = self.config["instance_name"]
        
        # Configure Autoscaling Retry
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
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
            response = self.session.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            data = response.json()
            state = data.get("instance", {}).get("state", "unknown")
            
            if state == "open":
                logger.info(f"✅ Instância '{self.instance}' está conectada")
                return True
            else:
                logger.warning(f"⚠️ Instância '{self.instance}' não está conectada (estado: {state})")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao verificar instância: {e}")
            return False
    
    def set_presence(self, number: str, presence: str = "composing", delay: int = 1200) -> bool:
        """
        Define o status de presença (digitando/gravando)
        
        Args:
            number: Número do destinatário (ex: "5551999999999@s.whatsapp.net")
            presence: "composing" (digitando) ou "recording" (gravando)
            delay: Tempo em ms para manter o status
        """
        try:
            url = f"{self.base_url}/chat/sendPresence/{self.instance}"
            payload = {
                "number": number,
                "presence": presence,
                "delay": delay
            }
            
            response = self.session.post(url, json=payload, headers=self._get_headers(), timeout=10)
            # response.raise_for_status() # Algumas versões da API não retornam 200 sempre
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao definir presença: {e}")
            return False

    def send_document(self, file_base64: str, file_name: str, caption: str = None, group_id: str = None) -> bool:
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
            
            # Usar group_id passado ou o default do config
            target = group_id or self.config.get("group_id", "")
            
            payload = {
                "number": target,
                "mediatype": "document",
                "mimetype": mime_type,
                "caption": caption or f"📄 {file_name}",
                "media": file_base64,
                "fileName": file_name
            }
            
            response = self.session.post(url, json=payload, headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("key"):
                logger.info(f"✅ Documento '{file_name}' enviado com sucesso para o grupo!")
                return True
            else:
                logger.warning(f"⚠️ Resposta inesperada: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar documento: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return False
    
    def send_image(self, image_base64: str, caption: str = None, group_id: str = None) -> bool:
        """Envia uma imagem para o grupo do WhatsApp"""
        try:
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            # Usar group_id passado ou o default do config
            target = group_id or self.config.get("group_id", "")
            
            payload = {
                "number": target,
                "mediatype": "image",
                "mimetype": "image/png",
                "caption": caption or "📊 Relatório",
                "media": image_base64,
            }
            
            response = self.session.post(url, json=payload, headers=self._get_headers(), timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("key"):
                return True
            else:
                logger.warning(f"⚠️ Resposta inesperada: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar imagem: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Resposta: {e.response.text}")
            return False
    
    def send_file(self, group_id: str, file_path: str, caption: str = None) -> bool:
        """
        Envia um arquivo (imagem) para um grupo específico do WhatsApp
        
        Args:
            group_id: ID do grupo (ex: "120363424554621359@g.us")
            file_path: Caminho do arquivo a enviar
            caption: Legenda opcional
        """
        import base64
        import os
        
        if not os.path.exists(file_path):
            logger.error(f"❌ Arquivo não encontrado: {file_path}")
            return False
        
        try:
            # Ler arquivo e converter para base64
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            file_base64 = base64.b64encode(file_data).decode("utf-8")
            
            # Detectar tipo de mídia
            extension = file_path.lower().split(".")[-1]
            
            if extension in ["png", "jpg", "jpeg", "gif"]:
                # Enviar como imagem
                return self.send_image(file_base64, caption, group_id)
            else:
                # Enviar como documento
                file_name = os.path.basename(file_path)
                return self.send_document(file_base64, file_name, caption, group_id)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar arquivo: {e}")
            return False
    
    def send_text_message(self, message: str, number_override: str = None) -> bool:
        """Envia uma mensagem de texto para o grupo ou número específico"""
        try:
            url = f"{self.base_url}/message/sendText/{self.instance}"
            
            payload = {
                "number": number_override or self.config.get("group_id"),
                "text": message
            }
            
            response = self.session.post(url, json=payload, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Mensagem de texto enviada com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
