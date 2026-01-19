import time
import random
from typing import Dict, Optional, Any
from utils.logger import get_logger
from core.clients.evolution_client import EvolutionClient

logger = get_logger("notification_service")

class NotificationService:
    def __init__(self, supabase_service: Optional[Any] = None):
        self.whatsapp = EvolutionClient()
        self.supabase = supabase_service

    def send_whatsapp_report(self, recipient_data: Dict[str, Any], image_path: str, caption: str, context_tag: str = "report") -> bool:
        """
        Envia um relatório via WhatsApp com lógica anti-banimento e (opcional) logging no Supabase.
        
        :param recipient_data: Dict com keys 'nome', 'telefone'/'phone', 'id' (opcional para Supabase)
        :param image_path: Caminho da imagem
        :param caption: Texto da legenda
        :param context_tag: Tag para log (ex: 'metas', 'unidades')
        """
        nome = recipient_data.get("nome") or recipient_data.get("name", "Colaborador")
        telefone = recipient_data.get("telefone") or recipient_data.get("phone")
        contact_id = recipient_data.get("id")

        if not telefone:
            logger.warning(f"Tentativa de envio sem telefone para {nome}")
            return False

        try:
            # 1. Simular humano digitando
            self.whatsapp.set_presence(str(telefone), "composing", delay=5000)
            time.sleep(random.randint(4, 8))

            # 2. Enviar Arquivo
            self.whatsapp.send_file(str(telefone), image_path, caption)
            logger.info(f"   [Notification] OK: WhatsApp para {nome} ({context_tag})")

            # 3. Log no Supabase (se disponível e ID válido)
            if self.supabase and contact_id:
                try:
                    self.supabase.log_event("message_sent", {
                        "recipient": nome, 
                        "type": context_tag
                    }, contact_id)
                except Exception as log_err:
                     logger.warning(f"   [Supabase Log Error]: {log_err}")
            
            # 4. Delay Humanizado (Anti-Ban)
            delay = random.randint(45, 120)
            logger.debug(f"   [Anti-Ban] Aguardando {delay}s...")
            time.sleep(delay)
            return True

        except Exception as e:
            logger.error(f"   [Notification ERROR] Falha ao enviar para {nome}: {e}")
            if self.supabase and contact_id:
                try:
                    self.supabase.log_event("message_error", {
                        "recipient": nome, 
                        "type": context_tag, 
                        "error": str(e)
                    }, contact_id)
                except:
                    pass
            return False
