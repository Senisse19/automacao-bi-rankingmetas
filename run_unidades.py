"""
Automação Unidades (Nexus Data)
Extrai dados de novas unidades/cancelamentos e envia para WhatsApp.
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta

from config import (
    IMAGES_DIR, 
    DESTINATARIOS_WHATSAPP
)
from clients.unidades_client import UnidadesClient
from services.image_generator import ImageGenerator
from clients.evolution_client import EvolutionClient
from utils.logger import get_logger

logger = get_logger("run_unidades")

class UnidadesAutomation:
    """
    Controlador principal da automação de Unidades.
    Gerencia a busca de dados no Nexus, geração de report e envio.
    """
    def __init__(self):
        self.image_gen = ImageGenerator()
        self.whatsapp = EvolutionClient()
        self.unidades_client = UnidadesClient()
        
        # Garantir diretório de imagens
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def _send_image_to_group(self, grupo_key, image_path, caption_prefix):
        """Helper para enviar imagem de Unidades para um grupo específico."""
        destinatarios = DESTINATARIOS_WHATSAPP.get(grupo_key, [])
        if not destinatarios:
             # Fallback logic if needed or just skip
             pass
             
        for pessoa in destinatarios:
            nome = pessoa.get("nome", "Colaborador")
            telefone = pessoa.get("telefone", "")
            if not telefone: continue
            
            try:
                caption = f"📊 {caption_prefix}\n\nOlá, {nome.split()[0]}! Segue resumo atualizado."
                logger.info(f"   Enviando Unidades para {nome}...")
                
                # Presença digitando
                self.whatsapp.set_presence(telefone, "composing", delay=5000)
                time.sleep(random.randint(3, 6))
                
                self.whatsapp.send_file(telefone, image_path, caption)
                time.sleep(random.randint(5, 10))
            except Exception as e:
                logger.error(f"   Erro env Unidades {nome}: {e}")

    def _cleanup_old_images(self, prefix):
        """
        Remove imagens antigas que começam com o prefixo especificado.
        Ex: 'unidades_daily_' para limpar relatórios diários anteriores.
        """
        try:
            for filename in os.listdir(IMAGES_DIR):
                if filename.startswith(prefix) and filename.endswith(".png"):
                    file_path = os.path.join(IMAGES_DIR, filename)
                    try:
                        os.remove(file_path)
                        logger.info(f"   [Cleanup] Removido arquivo antigo: {filename}")
                    except Exception as e:
                        logger.warning(f"   [Cleanup] Falha ao remover {filename}: {e}")
        except Exception as e:
            logger.error(f"   [Cleanup] Erro ao listar diretório: {e}")

    def process_reports(self, daily=True, weekly=False, force_weekly=False, generate_only=False):
        """
        Processa relatórios de Unidades com flags explícitas para Diário e Semanal.
        Pode executar ambos em sequência se solicitado.
        """
        logger.info("\n--- Processando Unidades ---")
        try:
            # Determine Date Reference for Daily
            # Determine Date Reference for Daily
            # Always generate for yesterday as per user requirement (never today)
            data_ref = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # 1. Relatório Diário
            if daily:
                logger.info(f"   [Processando] Relatório Diário (Ref: {data_ref})")
                
                # Cleanup old daily images
                self._cleanup_old_images("unidades_daily_")
                
                daily_data = self.unidades_client.fetch_data_for_range(data_ref, data_ref)
                daily_path = os.path.join(IMAGES_DIR, f"unidades_daily_{data_ref}.png")
                self.image_gen.generate_unidades_reports(daily_data, "daily", daily_path)
                
                # Enviar Diário
                if not generate_only:
                    self._send_image_to_group("diretoria", daily_path, f"Relatório Unidades - Diário {data_ref}")
                else:
                    logger.info(f"   [INFO] Imagem gerada (apenas geração): {daily_path}")
            
            # 2. Relatório Semanal
            should_run_weekly = weekly or force_weekly
            
            if should_run_weekly:
                # Calculate Previous Week (always Monday to Sunday of the week before execution)
                today = datetime.now()
                # Find the Monday of the current week (0 = Monday, 6 = Sunday)
                current_week_monday = today - timedelta(days=today.weekday())
                
                # Previous week start (Monday) and end (Sunday)
                start_dt_obj = current_week_monday - timedelta(days=7)
                end_dt_obj = start_dt_obj + timedelta(days=6)
                
                data_ref_weekly = end_dt_obj.strftime("%Y-%m-%d")
                start_weekly = start_dt_obj.strftime("%Y-%m-%d")
                
                logger.info(f"   [Processando] Relatório Semanal (Semana Anterior Completa): {start_weekly} a {data_ref_weekly}")

                weekly_data = self.unidades_client.fetch_data_for_range(start_weekly, data_ref_weekly)
                weekly_path = os.path.join(IMAGES_DIR, f"unidades_weekly_{data_ref_weekly}.png")
                
                # Cleanup old weekly images
                self._cleanup_old_images("unidades_weekly_")
                
                self.image_gen.generate_unidades_reports(weekly_data, "weekly", weekly_path)
                
                # Enviar Semanal
                if not generate_only:
                    self._send_image_to_group("diretoria", weekly_path, f"Relatório Unidades - Semanal ({start_weekly} a {data_ref_weekly})")
                else:
                    logger.info(f"   [INFO] Imagem gerada (apenas geração): {weekly_path}")
                
        except Exception as e:
            logger.error(f"Erro no processamento Unidades: {e}")
            import traceback
            traceback.print_exc()

def main():
    automation = UnidadesAutomation()
    
    generate_only = "--generate-only" in sys.argv
    
    # CLI Argument Handling
    if "--weekly-only" in sys.argv:
        automation.process_reports(daily=False, force_weekly=True, generate_only=generate_only)
    elif "--daily-only" in sys.argv:
        automation.process_reports(daily=True, weekly=False, generate_only=generate_only)
    else:
        # Default run (usually called by scheduler or manual test)
        # We can default to Daily, or both if needed. 
        # For manual execution without args, let's run Daily.
        automation.process_reports(daily=True, weekly=False, generate_only=generate_only)

if __name__ == "__main__":
    main()
