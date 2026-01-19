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
    IMAGES_DIR
)
from clients.unidades_client import UnidadesClient
from services.image_generator import ImageGenerator
from services.supabase_service import SupabaseService
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
        self.supabase = SupabaseService()
        
        # Garantir diretório de imagens
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def _send_image_to_group(self, grupo_key, image_path, caption_prefix, custom_recipients=None, template_content=None):
        """Helper para enviar imagem de Unidades para um grupo específico."""
        
        # Determine recipients source
        if not custom_recipients:
             logger.warning("Nenhum destinatário fornecido para Unidades. Config legacy removido.")
             return

        # Filter based on department if needed, or send to all given recipients
        # For Unidades, it usually goes to 'diretoria' which receives everything.
        # Or we check if the recipient belongs to the target group.
        destinatarios = []
        for r in custom_recipients:
             # If custom recipients are passed for a specific job, we usually just send to them all
             # regardless of 'grupo_key' unless we have multiple groups in one job.
             # For Unidades Daily/Weekly, it's usually just one target audience.
             destinatarios.append({
                "nome": r.get('name') or r.get('nome'),
                "telefone": r.get('phone') or r.get('telefone'),
                "id": r.get('id')
            })
             
        for pessoa in destinatarios:
            nome = pessoa.get("nome", "Colaborador")
            telefone = pessoa.get("telefone", "")
            if not telefone: continue
            
            try:
                primeiro_nome = nome.split()[0].title()
                
                # Dynamic Template Support
                if template_content:
                    try:
                        # Determine greeting based on time
                        hora = datetime.now().hour
                        if 5 <= hora < 12: saudacao = "Bom dia"
                        elif 12 <= hora < 18: saudacao = "Boa tarde"
                        else: saudacao = "Boa noite"
                        
                        caption = template_content.format(
                            nome=primeiro_nome,
                            nome_completo=nome,
                            saudacao=saudacao,
                            titulo=caption_prefix, # Specifically for Unidades reports
                            data=datetime.now().strftime("%d/%m/%Y")
                        )
                    except Exception as e:
                        logger.error(f"Erro ao formatar template Unidades para {nome}: {e}")
                        caption = f"📊 {caption_prefix}\n\nOlá, {primeiro_nome}! Segue resumo atualizado."
                else:
                    caption = f"📊 {caption_prefix}\n\nOlá, {primeiro_nome}! Segue resumo atualizado."
                
                logger.info(f"   Enviando Unidades para {nome}...")
                
                # Presença digitando
                self.whatsapp.set_presence(telefone, "composing", delay=5000)
                time.sleep(random.randint(3, 6))
                
                self.whatsapp.send_file(telefone, image_path, caption)
                self.supabase.log_event("message_sent", {"recipient": nome, "type": "unidades"}, contact_id=pessoa.get('id'))
                time.sleep(random.randint(5, 10))
            except Exception as e:
                logger.error(f"   Erro env Unidades {nome}: {e}")
                self.supabase.log_event("message_error", {"recipient": nome, "type": "unidades", "error": str(e)}, contact_id=pessoa.get('id'))

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

    def process_reports(self, daily=True, weekly=False, force_weekly=False, generate_only=False, recipients=None, template_content=None):
        """
        Processa relatórios de Unidades com flags explícitas para Diário e Semanal.
        Pode executar ambos em sequência se solicitado.
        """
        logger.info("\n--- Processando Unidades ---")
        try:
            # Determine Date Reference for Daily
            # If today is Monday (0), fetch data from Friday (D-3)
            # Else fetch Yesterday (D-1)
            today = datetime.now()
            days_back = 3 if today.weekday() == 0 else 1
            data_ref = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
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
                    self._send_image_to_group("diretoria", daily_path, f"Relatório Unidades - Diário {data_ref}", custom_recipients=recipients, template_content=template_content)
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
                    self._send_image_to_group("diretoria", weekly_path, f"Relatório Unidades - Semanal ({start_weekly} a {data_ref_weekly})", custom_recipients=recipients, template_content=template_content)
                else:
                    logger.info(f"   [INFO] Imagem gerada (apenas geração): {weekly_path}")
                
        except Exception as e:
            logger.error(f"Erro no processamento Unidades: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise para o scheduler detectar o erro

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
