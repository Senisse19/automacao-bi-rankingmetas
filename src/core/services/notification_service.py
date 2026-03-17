import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from src.core.clients.evolution_client import EvolutionClient
from src.core.utils.logger import get_logger

logger = get_logger("notification_service")

# Garante que apenas um envio HTTP acontece por vez na mesma instância do WhatsApp.
# Os delays anti-ban de cada worker correm em paralelo, reduzindo o tempo total
# de envio para ~max(delays) + N*send_time, em vez de sum(delays + send_times).
_send_lock = threading.Lock()


class NotificationService:
    def __init__(self, supabase_service: Optional[Any] = None):
        self.whatsapp = EvolutionClient()
        self.supabase = supabase_service

    def send_whatsapp_report(
        self,
        recipient_data: Dict[str, Any],
        image_path: str,
        caption: str,
        context_tag: str = "report",
    ) -> bool:
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
            # --- Seção protegida: apenas um envio HTTP por vez (anti-ban) ---
            with _send_lock:
                # 1. Simular humano digitando
                self.whatsapp.set_presence(str(telefone), "composing", delay=5000)
                time.sleep(random.randint(4, 8))

                # 2. Enviar Arquivo
                self.whatsapp.send_file(str(telefone), image_path, caption)

            logger.info(f"   [Notification] OK: WhatsApp para {nome} ({context_tag})")

            # 3. Log no Supabase (se disponível e ID válido)
            if self.supabase and contact_id:
                try:
                    self.supabase.log_event(
                        "message_sent",
                        {"recipient": nome, "type": context_tag},
                        contact_id,
                    )
                except Exception as log_err:
                    logger.warning(f"   [Supabase Log Error]: {type(log_err).__name__}")

            # 4. Delay Humanizado anti-ban — corre fora do lock (em paralelo com outros workers)
            delay = random.randint(45, 120)
            logger.debug(f"   [Anti-Ban] Aguardando {delay}s antes do próximo envio...")
            time.sleep(delay)
            return True

        except Exception as e:
            logger.error(f"   [Notification ERROR] Falha ao enviar para {nome}: {type(e).__name__}")
            if self.supabase and contact_id:
                try:
                    self.supabase.log_event(
                        "message_error",
                        {"recipient": nome, "type": context_tag, "error": type(e).__name__},
                        contact_id,
                    )
                except Exception:
                    pass
            return False

    def send_batch(
        self,
        sends: List[Tuple[Dict[str, Any], str, str]],
        context_tag: str = "report",
        max_workers: int = 3,
    ) -> Dict[str, int]:
        """
        Envia um lote de mensagens WhatsApp com concorrência controlada.

        Estratégia anti-ban: o envio HTTP é sequencial (lock global), mas os delays
        de cada worker correm em paralelo — reduzindo o tempo total de ~N*delay
        para ~max(delay) + N*send_time.

        :param sends: Lista de tuplas (recipient_data, image_path, caption)
        :param context_tag: Tag de contexto para logs
        :param max_workers: Número máximo de workers simultâneos (default: 3)
        :returns: {"success": N, "failed": M}
        """
        if not sends:
            return {"success": 0, "failed": 0}

        results = {"success": 0, "failed": 0}
        logger.info(f"[Batch] Iniciando envio de {len(sends)} mensagens ({context_tag}) com {max_workers} workers.")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.send_whatsapp_report, recipient, image, caption, context_tag): recipient
                for recipient, image, caption in sends
            }

            for future in as_completed(futures):
                recipient = futures[future]
                nome = recipient.get("nome") or recipient.get("name", "?")
                try:
                    success = future.result()
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    logger.error(f"   [Batch] Exceção não tratada para {nome}: {type(e).__name__}")
                    results["failed"] += 1

        logger.info(f"[Batch] Concluído: {results['success']} enviados, {results['failed']} falhas.")
        return results
