"""
Automação Metas (Power BI)
Extrai dados de metas do Power BI e envia imagens para WhatsApp/Email.
"""
import os
import sys
import time
import random
import json
from datetime import datetime, timedelta

# Fix path for standalone execution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import (
    IMAGES_DIR, 
    IMAGES_DIR, 
    DEPARTAMENTOS,
    DISPLAY_NAMES,
    METAS_CAPTION,
    EMAIL_CONFIG
)
from core.clients.powerbi_client import PowerBIClient
from core.services.image_generator import ImageGenerator
from core.services.supabase_service import SupabaseService
from core.clients.evolution_client import EvolutionClient
from core.clients.email_client import EmailClient
from utils.logger import get_logger

logger = get_logger("run_metas")

class MetasAutomation:
    """
    Controlador principal da automação de Metas.
    Responsável por buscar dados, gerar imagens e enviar mensagens.
    """
    def __init__(self):
        self.powerbi = PowerBIClient()
        self.image_gen = ImageGenerator()
        self.whatsapp = EvolutionClient()
        self.supabase = SupabaseService()
        self.email_client = EmailClient(EMAIL_CONFIG)
        
        os.makedirs(IMAGES_DIR, exist_ok=True)
    
    def get_periodo(self):
        """Retorna o período atual formatado (ex: Janeiro/2024)."""
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        now = datetime.now() - timedelta(days=1)
        return f"{meses[now.month - 1]}/{now.year}"
    
    def get_data_referencia(self):
        """Retorna a data de referência (ontem) formatada."""
        ontem = datetime.now() - timedelta(days=1)
        return ontem.strftime("%d/%m/%Y")
    
    def fetch_data(self):
        """Busca todos os dados necessários do Power BI."""
        logger.info("Buscando dados do Power BI...")
        from core.services.powerbi_data import PowerBIDataFetcher
        fetcher = PowerBIDataFetcher()
        return fetcher.fetch_all_data()

    def generate_images(self, total_gs, departamentos, receitas, periodo):
        """
        Gera todas as imagens de relatòrio (Geral, Resumo e por Departamento).
        Retorna um dicionário mapeando 'cliente/departamento' -> 'caminho_da_imagem'.
        """
        logger.info("Gerando imagens...")
        images = {}
        
        # 1. Geral
        geral_path = os.path.join(IMAGES_DIR, "metas_geral.png")
        self.image_gen.generate_metas_image(periodo, departamentos, total_gs, receitas, geral_path)
        images["diretoria"] = geral_path
        
        # 2. Resumo
        resumo_path = os.path.join(IMAGES_DIR, "metas_resumo.png")
        self.image_gen.generate_resumo_image(periodo, total_gs, receitas, resumo_path)
        
        # 3. Individuais (Backup / Mapping)
        for dep in departamentos:
            nome_lower = dep["nome"].lower().replace("ã", "a").replace("ç", "c")
            dep_path = os.path.join(IMAGES_DIR, f"metas_{nome_lower}.png")
            self.image_gen.generate_departamento_image(dep, periodo, dep_path)
            
            # Map valid departments to their SPECIFIC Image
            images[nome_lower] = dep_path
            
        return images

    def send_whatsapp(self, images, custom_recipients=None, template_content=None):
        """
        Envia as imagens geradas via WhatsApp.
        :param images: Dict {dept: image_path}
        :param custom_recipients: Lista plana de destinatários do Supabase
        :param template_content: String do template (opcional)
        """

        logger.info("Enviando para WhatsApp...")
        data_ref = self.get_data_referencia()
        
        # Pre-fetch templates form DB
        welcome_template_str = None
        fallback_template_str = None
        
        try:
            # 1. Welcome Template
            welcome_tmpl = self.supabase.get_template_by_name("Boas Vindas (Orientação)")
            if welcome_tmpl:
                welcome_template_str = welcome_tmpl['content']
                
            # 2. Daily Ranking Default (Fallback if no custom template provided)
            # Only needed if template_content is None (scheduler didn't find one)
            if not template_content:
                default_tmpl = self.supabase.get_template_by_name("Ranking Diário (Padrão)")
                if default_tmpl:
                    fallback_template_str = default_tmpl['content']
                    
        except Exception as e:
             logger.error(f"Erro ao carregar templates do DB: {e}")

        if not custom_recipients:
            logger.error("Nenhum destinatário fornecido (custom_recipients empty).")
            return

        # Group flat list by department to match image keys
        recipients_map = {}
        for r in custom_recipients:
            # Normalize department name to match image keys (e.g. 'Diretoria' -> 'diretoria')
            dept_key = (r.get('department') or 'geral').lower()
            dept_key = dept_key.replace("ã", "a").replace("ç", "c").replace("õ", "o").replace("é", "e").replace("á", "a")
            
            if dept_key not in recipients_map:
                recipients_map[dept_key] = []
            
            recipients_map[dept_key].append(r) # Keep full object
            
        source_data = recipients_map
        logger.info(f"Processando envio para {len(custom_recipients)} destinatários dinâmicos.")
        
        # Instantiate Notification Service
        from core.services.notification_service import NotificationService
        notification_service = NotificationService(self.supabase)

        for grupo_key, image_path in images.items():
            destinatarios = source_data.get(grupo_key, [])
            if not destinatarios: continue
            
            for pessoa in destinatarios:
                nome = pessoa.get("nome") or pessoa.get("name", "Colaborador")
                telefone = pessoa.get("telefone") or pessoa.get("phone")
                contact_id = pessoa.get("id") # Supabase ID
                
                if not telefone: continue
                
                # Saudação Variables
                primeiro_nome = nome.split()[0].title()
                hora = datetime.now().hour
                if 5 <= hora < 12: saudacao = "Bom dia"
                elif 12 <= hora < 18: saudacao = "Boa tarde"
                else: saudacao = "Boa noite"
                saudacao_lower = saudacao.lower()
                
                # --- Template Logic ---
                current_template = template_content or fallback_template_str
                is_first_time = not self.supabase.check_welcome_sent(contact_id)
                
                # Warning Message for First-Time Users
                warning_msg = "\n\n⚠ Aviso Importante: Por favor salve este contato. Para garantir o recebimento contínuo dos relatórios, pedimos que responda sempre todas as mensagens confirmando o recebimento (ex: \"ok\", \"recebido\")."

                if current_template:
                    # Dynamic Template
                    try:
                        caption = current_template.format(
                            nome=primeiro_nome,
                            nome_completo=nome,
                            saudacao=saudacao,
                            saudacao_lower=saudacao_lower,
                            data=data_ref,
                            grupo=grupo_key.title()
                        )
                    except Exception as e:
                        logger.error(f"Erro ao formatar template para {nome}: {e}")
                        caption = f"{saudacao}, {primeiro_nome}!\n\nSegue o relatório de {data_ref}."
                else:
                    # Legacy Hardcoded Fallback
                    variations = [
                        f"{saudacao}, {primeiro_nome}!",
                        f"Olá, {primeiro_nome}! {saudacao}.",
                        f"{saudacao}, {primeiro_nome}, tudo bem?",
                        f"{primeiro_nome}, {saudacao_lower}!",
                        f"Oi, {primeiro_nome}. {saudacao}!"
                    ]
                    selected_greeting = random.choice(variations)
                    caption = f"{selected_greeting}\n\n" + METAS_CAPTION.format(data=data_ref)

                # Append warning if new user
                if is_first_time:
                    logger.info(f"   ℹ Novo usuário detectado: {nome}. Adicionando aviso de primeiro envio.")
                    caption += warning_msg

                # --- Send via Service ---
                success = notification_service.send_whatsapp_report(
                    recipient_data=pessoa,
                    image_path=image_path,
                    caption=caption,
                    context_tag="metas"
                )
                
                if success and is_first_time:
                    self.supabase.mark_welcome_sent(contact_id)

    def send_email(self, images):
        # Email logic remains unchanged for now, using hardcoded templates or separate implementation
        pass

    def run(self, generate_only=False, recipients=None, template_content=None):
        """
        Executa o fluxo completo da automação.
        :param recipients: Lista opcional de destinatários do DB.
        :param template_content: Conteúdo do template de mensagem.
        """
        logger.info("\n=== AUTOMAÇÃO METAS ===")
        total_gs, deps, receitas = self.fetch_data()
        if not deps: return
        
        periodo = self.get_periodo()
        images = self.generate_images(total_gs, deps, receitas, periodo)
        
        if not generate_only:
            self.send_whatsapp(images, custom_recipients=recipients, template_content=template_content)
            # self.send_email(images) # Commenting out email for now to focus on WA
        else:
            logger.info(f"   [INFO] Imagens geradas, envio pulado (--generate-only). Verifique a pasta images/")
        logger.info("=== FIM AUTOMAÇÃO METAS ===\n")

def main():
    automation = MetasAutomation()
    generate_only = "--generate-only" in sys.argv
    automation.run(generate_only=generate_only)

if __name__ == "__main__":
    main()
