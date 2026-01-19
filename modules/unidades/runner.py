"""
Automação Unidades (Nexus Data)
Extrai dados de novas unidades/cancelamentos e envia para WhatsApp.
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta

# Fix path for standalone execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import (
    IMAGES_DIR
)
from core.clients.unidades_client import UnidadesClient
from core.services.image_generator import ImageGenerator
from core.services.supabase_service import SupabaseService
from core.clients.evolution_client import EvolutionClient
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

    def _send_image_to_group(self, grupo_key, image_path, caption_prefix, custom_recipients=None, template_content=None, data_ref_str=None):
        """Helper para enviar imagem de Unidades usando o NotificationService."""
        
        # Determine recipients source
        if not custom_recipients:
             logger.warning("Nenhum destinatário fornecido para Unidades. Config legacy removido.")
             return

        # Instantiate Notification Service
        from core.services.notification_service import NotificationService
        notification_service = NotificationService(self.supabase)

        # Filter recipients
        destinatarios = []
        for r in custom_recipients:
             destinatarios.append({
                "nome": r.get('name') or r.get('nome'),
                "telefone": r.get('phone') or r.get('telefone'),
                "id": r.get('id')
            })
             
        for pessoa in destinatarios:
            nome = pessoa.get("nome", "Colaborador")
            telefone = pessoa.get("telefone", "")
            if not telefone: continue
            
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
                        saudacao_lower=saudacao.lower(),
                        titulo=caption_prefix, # Specifically for Unidades reports
                        data=data_ref_str or datetime.now().strftime("%d/%m/%Y"),
                        grupo=grupo_key.title()
                    )
                except Exception as e:
                    logger.error(f"Erro ao formatar template Unidades para {nome}: {e}")
                    caption = f"📊 {caption_prefix}\n\nOlá, {primeiro_nome}! Segue resumo atualizado."
            else:
                caption = f"📊 {caption_prefix}\n\nOlá, {primeiro_nome}! Segue resumo atualizado."
            
            # Check First Shot Logic
            # We need contact_id to check welcome status. 
            # In Unidades, 'pessoa' dict has 'id' key based on line 60: "id": r.get('id')
            contact_id = pessoa.get("id")
            if contact_id:
                is_first_time = not self.supabase.check_welcome_sent(contact_id)
                if is_first_time:
                    logger.info(f"   ℹ Novo usuário detectado (Unidades): {nome}. Adicionando aviso.")
                    warning_msg = "\n\n⚠ Aviso Importante: Por favor salve este contato. Para garantir o recebimento contínuo dos relatórios, pedimos que responda sempre todas as mensagens confirmando o recebimento (ex: \"ok\", \"recebido\")."
                    caption += warning_msg
            else:
                is_first_time = False

            
            # --- Send via Service ---
            success = notification_service.send_whatsapp_report(
                recipient_data=pessoa,
                image_path=image_path,
                caption=caption,
                context_tag="unidades"
            )

            if success and is_first_time and contact_id:
                self.supabase.mark_welcome_sent(contact_id)

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
                    # Format data for diplay: 2026-01-16 -> 16/01/2026
                    data_display = datetime.strptime(data_ref, "%Y-%m-%d").strftime("%d/%m/%Y")
                    self._send_image_to_group("diretoria", daily_path, f"Relatório Unidades - Diário {data_display}", custom_recipients=recipients, template_content=template_content, data_ref_str=data_display)
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
                    data_display = f"{datetime.strptime(start_weekly, '%Y-%m-%d').strftime('%d/%m')} a {datetime.strptime(data_ref_weekly, '%Y-%m-%d').strftime('%d/%m')}"
                    self._send_image_to_group("diretoria", weekly_path, f"Relatório Unidades - Semanal ({data_display})", custom_recipients=recipients, template_content=template_content, data_ref_str=data_display)
                else:
                    logger.info(f"   [INFO] Imagem gerada (apenas geração): {weekly_path}")
                
        except Exception as e:
            logger.error(f"Erro no processamento Unidades: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise para o scheduler detectar o erro

def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Run Unidades Automation')
    parser.add_argument('--generate-only', action='store_true', help='Only generate images')
    parser.add_argument('--weekly-only', action='store_true', help='Run only weekly report')
    parser.add_argument('--daily-only', action='store_true', help='Run only daily report')
    parser.add_argument('--payload', type=str, help='JSON payload with recipients and template.')
    
    args = parser.parse_args()
    
    automation = UnidadesAutomation()
    
    recipients = None
    template_content = None
    
    if args.payload:
        try:
            data = json.loads(args.payload)
            recipients = data.get('recipients')
            template_content = data.get('template_content')
            logger.info(f"Recebido payload via CLI com {len(recipients) if recipients else 0} destinatários.")
        except Exception as e:
            logger.error(f"Erro ao fazer parse do payload JSON: {e}")
            return
            
    # Default behavior logic
    daily = True
    weekly = False
    force_weekly = False
    
    if args.weekly_only:
        daily = False
        force_weekly = True
    elif args.daily_only:
        daily = True
        weekly = False
        
    automation.process_reports(
        daily=daily, 
        weekly=weekly, 
        force_weekly=force_weekly, 
        generate_only=args.generate_only,
        recipients=recipients,
        template_content=template_content
    )

if __name__ == "__main__":
    main()
