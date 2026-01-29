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
    PORTAL_URL
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
        # PdfGenerator removed (replaced by ImageGenerator/UnidadesRenderer)
        self.whatsapp = EvolutionClient()
        self.unidades_client = UnidadesClient()
        self.supabase = SupabaseService()
        
        # Garantir diretório de imagens
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def get_periodo_semanal(self):
        """Retorna o período da semana anterior (seg-dom) formatado (ex: 15/01 a 21/01)."""
        hoje = datetime.now()
        inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
        inicio_semana_anterior = inicio_semana_atual - timedelta(days=7)
        fim_semana_anterior = inicio_semana_anterior + timedelta(days=6)
        return f"{inicio_semana_anterior.strftime('%d/%m/%Y')} a {fim_semana_anterior.strftime('%d/%m/%Y')}"


    def _validate_units(self, items, label="items"):
        """Filtra itens inválidos ou vazios."""
        valid = []
        for item in items:
            # Check ID
            uid = item.get("codigo")
            if not uid:
                logger.warning(f"   [FILTER] Item removido ({label}): ID vazio. Dump: {item}")
                continue
            
            # Check Name validity (ignoring "Unidade None" or similar fallbacks if critical)
            nome = item.get("nome", "")
            if not nome or "Unidade None" in nome:
                 logger.warning(f"   [FILTER] Item removido ({label}): Nome inválido ({nome}). ID: {uid}")
                 continue
                 
            valid.append(item)
        
        if len(valid) < len(items):
            logger.info(f"   [FILTER] {len(items) - len(valid)} itens inválidos removidos de '{label}'.")
            
        return valid

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
                # logger.info(f"   [TEMPLATE] Formatando template personalizada...") 
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
                        data_semanal=self.get_periodo_semanal(),
                        grupo=grupo_key.title()
                    )
                except Exception as e:
                    logger.error(f"❌ [ERRO DE TEMPLATE] Falha ao formatar para {nome}: {e}")
                    logger.error(f"   Conteúdo do Template: {template_content}")
                    # Fallback com erro logado
                    caption = f"📊 {caption_prefix}\n\nOlá, {primeiro_nome}! Segue resumo atualizado."
            else:
                # logger.info("   [TEMPLATE] Nenhum template (None). Usando padrão.")
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
                if filename.startswith(prefix) and filename.endswith(".pdf"):
                    file_path = os.path.join(IMAGES_DIR, filename)
                    try:
                        os.remove(file_path)
                        logger.info(f"   [Cleanup] Removido arquivo antigo: {filename}")
                    except Exception as e:
                        logger.warning(f"   [Cleanup] Falha ao remover {filename}: {e}")
        except Exception as e:
            logger.error(f"   [Cleanup] Erro ao listar diretório: {e}")

    def process_reports(self, daily=True, weekly=False, force_weekly=False, generate_only=False, recipients=None, template_content=None, date_override=None):
        """
        Processa relatórios de Unidades com flags explícitas para Diário e Semanal.
        Pode executar ambos em sequência se solicitado.
        """
        logger.info("\n--- Processando Unidades ---")
        
        # Base URL for dynamic reports (should be in env, defaulting to portal URL)
        # TODO: Move to config properly
        base_url = os.getenv("PORTAL_URL", "https://bi.grupostudio.tec.br")
        
        try:
            # Determine Date Reference for Daily
            if date_override:
                data_ref = date_override
            else:
                # If today is Monday (0), fetch data from Friday (D-3)
                # Else fetch Yesterday (D-1)
                today = datetime.now()
                days_back = 3 if today.weekday() == 0 else 1
                data_ref = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            # 1. Relatório Diário
            if daily:
                logger.info(f"   [Processando] Relatório Diário (Ref: {data_ref})")
                
                # Cleanup old daily images
                self._cleanup_old_images("Relatório de Unidades Diárias")
                
                daily_data = self.unidades_client.fetch_data_for_range(data_ref, data_ref)
                
                # --- strict validation ---
                daily_data['new'] = self._validate_units(daily_data.get('new', []), "Daily New")
                daily_data['cancelled'] = self._validate_units(daily_data.get('cancelled', []), "Daily Cancelled")
                daily_data['upsell'] = self._validate_units(daily_data.get('upsell', []), "Daily Upsell")
                
                has_daily_items = (daily_data.get('new') or daily_data.get('cancelled') or daily_data.get('upsell'))

                if not has_daily_items:
                    logger.info(f"   [SKIP] Nenhum dado encontrado para o relatório diário ({data_ref}).")
                else:
                    # --- LIVE LINK ---
                    # Link aponta para a página dinâmica com filtro de data
                    report_link = f"{base_url}/reports/unidades?start={data_ref}&end={data_ref}&type=daily"
                    
                    daily_path = os.path.join(IMAGES_DIR, f"Relatório de Unidades Diárias {data_ref}.pdf")
                    # Use ImageGenerator (Facade) -> UnidadesRenderer (Dark Premium Layout)
                    self.image_gen.generate_unidades_reports(daily_data, "daily", daily_path)
                    
                    # Enviar Diário
                    if not generate_only:
                        # Format data for diplay: 2026-01-16 -> 16/01/2026
                        data_display = datetime.strptime(data_ref, "%Y-%m-%d").strftime("%d/%m/%Y")
                        
                        base_caption = f"Relatório Unidades - Diário {data_display}"
                        if report_link:
                            base_caption += f"\n\n🔗 Ver lista completa:\n{report_link}"
                            
                        self._send_image_to_group("diretoria", daily_path, base_caption, custom_recipients=recipients, template_content=template_content, data_ref_str=data_display)
                    else:
                        logger.info(f"   [INFO] Imagem gerada (apenas geração): {daily_path}")
                        logger.info(f"   [INFO] Link: {report_link}")
            
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
                
                # --- strict validation ---
                weekly_data['new'] = self._validate_units(weekly_data.get('new', []), "Weekly New")
                weekly_data['cancelled'] = self._validate_units(weekly_data.get('cancelled', []), "Weekly Cancelled")
                weekly_data['upsell'] = self._validate_units(weekly_data.get('upsell', []), "Weekly Upsell")
                
                has_weekly_items = (weekly_data.get('new') or weekly_data.get('cancelled') or weekly_data.get('upsell'))

                if not has_weekly_items:
                    logger.info(f"   [SKIP] Nenhum dado encontrado para o relatório semanal ({start_weekly} a {data_ref_weekly}).")
                else:
                    # --- LIVE LINK ---
                    report_link = f"{base_url}/reports/unidades?start={start_weekly}&end={data_ref_weekly}&type=weekly"

                    weekly_path = os.path.join(IMAGES_DIR, f"Relatório de Unidades Semanal {start_weekly} a {data_ref_weekly}.pdf")
                    
                    # Cleanup old weekly images
                    self._cleanup_old_images("Relatório de Unidades Semanal")
                    
                    # Use ImageGenerator (Facade) -> UnidadesRenderer (Dark Premium Layout)
                    self.image_gen.generate_unidades_reports(weekly_data, "weekly", weekly_path)
                    
                    # Enviar Semanal
                    if not generate_only:
                        data_display = f"{datetime.strptime(start_weekly, '%Y-%m-%d').strftime('%d/%m')} a {datetime.strptime(data_ref_weekly, '%Y-%m-%d').strftime('%d/%m')}"
                        
                        base_caption = f"Relatório Unidades - Semanal ({data_display})"
                        if report_link:
                             base_caption += f"\n\n🔗 Ver lista completa:\n{report_link}"
                             
                        self._send_image_to_group("diretoria", weekly_path, base_caption, custom_recipients=recipients, template_content=template_content, data_ref_str=data_display)
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
    parser.add_argument('--date', type=str, help='Override reference date (YYYY-MM-DD)')
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
        template_content=template_content,
        date_override=args.date
    )

if __name__ == "__main__":
    main()
