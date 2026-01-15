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

from config import (
    IMAGES_DIR, 
    DESTINATARIOS_WHATSAPP,
    EMAILS_DESTINO,
    DEPARTAMENTOS,
    DISPLAY_NAMES,
    METAS_CAPTION,
    EMAIL_CONFIG
)
from clients.powerbi_client import PowerBIClient
from services.image_generator import ImageGenerator
from clients.evolution_client import EvolutionClient
from clients.email_client import EmailClient
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
        from services.powerbi_data import PowerBIDataFetcher
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
            
            # Map valid departments to Summary Image as per new logic
            images[nome_lower] = resumo_path
            
        return images

    def send_whatsapp(self, images):
        """Envia as imagens geradas via WhatsApp para os destinatários configurados."""
        logger.info("Enviando para WhatsApp...")
        data_ref = self.get_data_referencia()
        
        for grupo_key, image_path in images.items():
            destinatarios = DESTINATARIOS_WHATSAPP.get(grupo_key, [])
            if not destinatarios: continue
            
            for pessoa in destinatarios:
                nome = pessoa.get("nome", "Colaborador")
                telefone = pessoa.get("telefone", "")
                if not telefone: continue
                
                # Carregar histórico de mensagens
                history_file = "message_history.json"
                try:
                    if os.path.exists(history_file):
                        with open(history_file, "r") as f:
                            message_history = json.load(f)
                    else:
                        message_history = []
                except Exception:
                    message_history = []

                # Saudação
                primeiro_nome = nome.split()[0].title()
                hora = datetime.now().hour
                if 5 <= hora < 12: saudacao = "Bom dia"
                elif 12 <= hora < 18: saudacao = "Boa tarde"
                else: saudacao = "Boa noite"
                
                # Base Greeting Variations
                saudacao_lower = saudacao.lower()
                variations = [
                    f"{saudacao}, {primeiro_nome}!",
                    f"Olá, {primeiro_nome}! {saudacao}.",
                    f"{saudacao}, {primeiro_nome}, tudo bem?",
                    f"{primeiro_nome}, {saudacao_lower}!",
                    f"Oi, {primeiro_nome}. {saudacao}!"
                ]
                selected_greeting = random.choice(variations)
                
                # Base Caption
                caption = f"{selected_greeting}\n\n" + METAS_CAPTION.format(data=data_ref)

                # Lógica de Primeiro Envio (Aviso Importante)
                clean_phone = str(telefone).replace("@s.whatsapp.net", "") # Armazenar apenas números limpos por consistência
                if clean_phone not in message_history:
                    warning_msg = '\n\n⚠️ Aviso Importante: Por favor salve este contato. Para garantir o recebimento contínuo dos relatórios, pedimos que *responda sempre* todas as mensagens confirmando o recebimento (ex: "ok", "recebido").'
                    caption += warning_msg
                    
                    # Atualizar histórico
                    message_history.append(clean_phone)
                    try:
                        with open(history_file, "w") as f:
                            json.dump(message_history, f)
                    except Exception as e:
                        logger.error(f"Erro ao salvar message_history: {e}")
                
                try:
                    # Send
                    self.whatsapp.set_presence(telefone, "composing", delay=5000)
                    time.sleep(random.randint(4, 8))
                    self.whatsapp.send_file(telefone, image_path, caption)
                    logger.info(f"   OK: WhatsApp para {nome} ({grupo_key})")
                    time.sleep(random.randint(45, 120)) # Delay humanizado entre envios
                    
                except Exception as e:
                    logger.error(f"   ERRO WhatsApp {nome}: {e}")

    def send_email(self, images):
        """Envia as imagens geradas via Email para os destinatários configurados."""
        logger.info("Enviando por Email...")
        data_ref = self.get_data_referencia()
        
        for grupo_key, image_path in images.items():
            destinatarios = EMAILS_DESTINO.get(grupo_key, [])
            if not destinatarios: continue
            
            departamento = DISPLAY_NAMES.get(grupo_key, grupo_key.title())
            subject = f"Relatório de Metas - {departamento} - {data_ref}"
            
            for pessoa in destinatarios:
                nome = pessoa.get("nome", "Colaborador")
                email = pessoa.get("email", "")
                if not email or "@" not in email: continue
                
                primeiro_nome = nome.split()[0].title()
                body = f"Prezado(a) {primeiro_nome},\n\nSegue em anexo o Relatório de Metas referente a {data_ref}.\n\nhttps://bi.grupostudio.tec.br\n\nAtt,\nGrupo Studio"
                
                if self.email_client.send_email([email], subject, body, image_path):
                    logger.info(f"   OK: Email para {nome} ({grupo_key})")
                else:
                    logger.error(f"   ERRO Email para {nome}")

    def run(self, generate_only=False):
        """Executa o fluxo completo da automação."""
        logger.info("\n=== AUTOMAÇÃO METAS ===")
        total_gs, deps, receitas = self.fetch_data()
        if not deps: return
        
        periodo = self.get_periodo()
        images = self.generate_images(total_gs, deps, receitas, periodo)
        
        if not generate_only:
            self.send_whatsapp(images)
            self.send_email(images)

        else:
            logger.info(f"   [INFO] Imagens geradas, envio pulado (--generate-only). Verifique a pasta images/")
        logger.info("=== FIM AUTOMAÇÃO METAS ===\n")

def main():
    automation = MetasAutomation()
    generate_only = "--generate-only" in sys.argv
    automation.run(generate_only=generate_only)

if __name__ == "__main__":
    main()
