"""
Automação Power BI -> WhatsApp
Extrai dados de metas do Power BI e envia imagens para grupos do WhatsApp
Agendamento: Todos os dias às 9h
"""
import os
import time
import schedule
from datetime import datetime, timedelta

from config import (
    POWERBI_CONFIG, 
    EVOLUTION_CONFIG, 
    GRUPOS_WHATSAPP, 
    DEPARTAMENTOS,
    DISPLAY_NAMES,
    SCHEDULE_TIME,
    IMAGES_DIR,
    METAS_CAPTION
)
from powerbi_client import PowerBIClient
from image_generator import ImageGenerator
from evolution_client import EvolutionClient


class MetasAutomation:
    def __init__(self):
        self.powerbi = PowerBIClient()
        self.image_gen = ImageGenerator()
        self.whatsapp = EvolutionClient()
        
        # Criar diretório de imagens se não existir
        os.makedirs(IMAGES_DIR, exist_ok=True)
    
    def get_periodo(self):
        """Retorna o período atual formatado"""
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        now = datetime.now()
        return f"{meses[now.month - 1]}/{now.year}"
    
    def get_data_referencia(self):
        """Retorna a data de referência (dia anterior - D-1)"""
        ontem = datetime.now() - timedelta(days=1)
        return ontem.strftime("%d/%m/%Y")
    
    def fetch_metas_data(self):
        """
        Busca dados de metas do Power BI via DAX
        Usa o PowerBIDataFetcher para queries reais
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Buscando dados do Power BI...")
        
        from powerbi_data import PowerBIDataFetcher
        
        fetcher = PowerBIDataFetcher()
        total_gs, departamentos, receitas = fetcher.fetch_all_data()
        
        if total_gs and departamentos:
            print(f"   OK - Dados de {len(departamentos)} departamentos obtidos")
            return total_gs, departamentos, receitas
        else:
            print("   ERRO: Falha ao obter dados do Power BI")
            return None, None, None
    
    def generate_images(self, total_gs, departamentos, receitas, periodo):
        """Gera todas as imagens necessárias"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Gerando imagens...")
        
        images = {}
        
        # 1. Imagem geral para Diretoria
        geral_path = os.path.join(IMAGES_DIR, "metas_geral.png")
        self.image_gen.generate_metas_image(
            periodo=periodo,
            departamentos=departamentos,
            total_gs=total_gs,
            receitas=receitas,
            output_path=geral_path
        )
        images["diretoria"] = geral_path
        print(f"   Gerada: metas_geral.png")
        


        # 2. Imagem Resumo (para todos os grupos individuais)
        resumo_path = os.path.join(IMAGES_DIR, "metas_resumo.png")
        self.image_gen.generate_resumo_image(
            periodo=periodo,
            total_gs=total_gs,
            receitas=receitas,
            output_path=resumo_path
        )
        print(f"   Gerada: metas_resumo.png")

        # 3. Gerar imagens individuais (mas NÃO enviar)
        # O usuário pediu para "continuar sendo geradas" mas enviar o resumo
        print("   Gerando imagens individuais (backup)...")
        for dep in departamentos:
            nome_lower = dep["nome"].lower().replace("ã", "a").replace("ç", "c")
            
            # Gerar o arquivo físico
            dep_path = os.path.join(IMAGES_DIR, f"metas_{nome_lower}.png")
            self.image_gen.generate_departamento_image(
                departamento=dep,
                periodo=periodo,
                output_path=dep_path
            )
            # print(f"   Gerada (backup): metas_{nome_lower}.png")

            # Mapear o envio para a imagem de RESUMO
            images[nome_lower] = resumo_path


        
        return images
    
    def send_to_whatsapp(self, images):
        """Envia as imagens para os grupos correspondentes"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando para WhatsApp...")
        
        # Usar data do dia anterior (D-1) como referência
        data_referencia = self.get_data_referencia()
        enviados = 0
        erros = 0
        
        for grupo_key, image_path in images.items():
            grupo_id = GRUPOS_WHATSAPP.get(grupo_key, "")
            
            if not grupo_id:
                print(f"   SKIP: Grupo '{grupo_key}' não configurado")
                continue
            
            if not os.path.exists(image_path):
                print(f"   ERRO: Imagem não encontrada: {image_path}")
                erros += 1
                continue
            
            try:
                # Formatar mensagem com nome correto (acentuado)
                # departmento = grupo_key.title() if grupo_key != "diretoria" else "Grupo Studio"
                departamento = DISPLAY_NAMES.get(grupo_key, grupo_key.title())
                
                caption = METAS_CAPTION.format(
                    departamento=departamento,
                    data=data_referencia  # D-1
                )
                
                # Enviar imagem
                success = self.whatsapp.send_file(
                    group_id=grupo_id,
                    file_path=image_path,
                    caption=caption
                )
                
                if success:
                    print(f"   OK: Enviado para {grupo_key}")
                    enviados += 1
                else:
                    print(f"   ERRO: Falha ao enviar para {grupo_key}")
                    erros += 1
                    
            except Exception as e:
                print(f"   ERRO: {grupo_key} - {e}")
                erros += 1
        
        return enviados, erros
    
    def run_once(self):
        """Executa a automação uma vez"""
        print("\n" + "=" * 60)
        print(f"AUTOMAÇÃO METAS - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        # 1. Buscar dados
        total_gs, departamentos, receitas = self.fetch_metas_data()
        if not departamentos:
            print("ERRO: Não foi possível obter dados")
            return False
        
        # 2. Gerar imagens
        periodo = self.get_periodo()
        images = self.generate_images(total_gs, departamentos, receitas, periodo)
        
        # 3. Enviar para WhatsApp
        enviados, erros = self.send_to_whatsapp(images)
        
        print("\n" + "-" * 60)
        print(f"RESUMO: {enviados} enviados, {erros} erros")
        print("=" * 60 + "\n")
        
        return erros == 0
    
    def run_scheduled(self):
        """Executa com agendamento diário"""
        print(f"Automação Metas iniciada")
        print(f"Agendamento: Todos os dias às {SCHEDULE_TIME}")
        print(f"Aguardando próxima execução...\n")
        
        # Agendar execução diária
        schedule.every().day.at(SCHEDULE_TIME).do(self.run_once)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto


def main():
    automation = MetasAutomation()
    
    # Executar com agendamento
    print("Iniciando automação em modo agendado...")
    automation.run_scheduled()


if __name__ == "__main__":
    main()
