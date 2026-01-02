"""
Automação: SharePoint para WhatsApp
Monitora a pasta Diretoria e envia novos arquivos para o grupo do WhatsApp

Modos de execução:
    - Manual: python main.py (envia arquivo mais recente)
    - Agendado: python main.py --schedule (roda às 10h diariamente)
    - Monitor: python main.py --monitor (monitora novos uploads continuamente)
    - Init: python main.py --init (inicializa arquivos conhecidos sem enviar)
"""
import sys
import schedule
import time
import base64
from datetime import datetime

from sharepoint_client import SharePointClient
from evolution_client import EvolutionClient
from file_monitor import FileMonitor
from config import SCHEDULE_TIME, REPORT_CAPTION, MONITOR_INTERVAL_SECONDS


def send_file_to_whatsapp(sharepoint: SharePointClient, evolution: EvolutionClient, file: dict) -> bool:
    """Baixa um arquivo e envia para o WhatsApp"""
    file_id = file.get("id")
    file_name = file.get("name")
    
    print(f"\n📥 Baixando arquivo: {file_name}...")
    file_content, _ = sharepoint.download_file(file_id)
    
    if not file_content:
        print(f"❌ Falha ao baixar arquivo: {file_name}")
        return False
    
    # Converter para base64
    file_base64 = base64.b64encode(file_content).decode("utf-8")
    
    # Preparar caption
    caption = REPORT_CAPTION.format(data=datetime.now().strftime('%d/%m/%Y às %H:%M'))
    
    print(f"📤 Enviando para WhatsApp...")
    
    # Determinar se é imagem ou documento
    extension = file_name.lower().split(".")[-1] if "." in file_name else ""
    
    if extension in ["png", "jpg", "jpeg", "gif"]:
        return evolution.send_image(file_base64, caption)
    else:
        return evolution.send_document(file_base64, file_name, caption)


def run_automation():
    """Executa a automação principal (envia arquivo mais recente)"""
    print("\n" + "="*60)
    print(f"🚀 Iniciando automação - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    # 1. Inicializar clientes
    sharepoint = SharePointClient()
    evolution = EvolutionClient()
    
    # 2. Verificar conexão do WhatsApp
    print("\n📱 Verificando conexão WhatsApp...")
    if not evolution.check_instance_status():
        print("❌ Automação abortada: WhatsApp não está conectado")
        return False
    
    # 3. Baixar arquivo mais recente do SharePoint
    print("\n📥 Baixando arquivo do SharePoint...")
    file_base64, file_name = sharepoint.get_latest_file_as_base64()
    
    if not file_base64:
        print("❌ Automação abortada: Não foi possível baixar o arquivo")
        return False
    
    # 4. Enviar para o WhatsApp
    print("\n📤 Enviando arquivo para WhatsApp...")
    caption = REPORT_CAPTION.format(data=datetime.now().strftime('%d/%m/%Y às %H:%M'))
    
    if evolution.send_document(file_base64, file_name, caption):
        print("\n" + "="*60)
        print("✅ AUTOMAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        return True
    else:
        print("\n❌ Falha ao enviar arquivo para o WhatsApp")
        return False


def run_monitor():
    """Executa o monitoramento contínuo de novos arquivos"""
    print("\n" + "="*60)
    print(f"👁️ Iniciando Monitor de Arquivos - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   Intervalo de verificação: {MONITOR_INTERVAL_SECONDS} segundos")
    print("   (Pressione Ctrl+C para parar)")
    print("="*60)
    
    # Inicializar clientes
    sharepoint = SharePointClient()
    evolution = EvolutionClient()
    monitor = FileMonitor(sharepoint)
    
    # Verificar conexão do WhatsApp
    print("\n📱 Verificando conexão WhatsApp...")
    if not evolution.check_instance_status():
        print("❌ Monitor abortado: WhatsApp não está conectado")
        return
    
    print("\n🔄 Monitoramento iniciado. Aguardando novos arquivos...\n")
    
    check_count = 0
    while True:
        try:
            check_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Verificar novos arquivos
            new_files = monitor.check_for_new_files()
            
            if new_files:
                print(f"\n[{timestamp}] 🆕 {len(new_files)} novo(s) arquivo(s) detectado(s)!")
                
                for file in new_files:
                    # IMPORTANTE: Marca como processado ANTES de enviar
                    # Isso evita envios duplicados em caso de restart
                    monitor.mark_as_processed(file)
                    
                    # Tenta enviar
                    success = send_file_to_whatsapp(sharepoint, evolution, file)
                    if success:
                        print(f"✅ Arquivo enviado com sucesso!")
                    else:
                        print(f"⚠️ Falha no envio de {file.get('name')}")
                
                print()
            else:
                # Log silencioso a cada 10 verificações
                if check_count % 10 == 0:
                    print(f"[{timestamp}] ✓ Verificação #{check_count} - Nenhum arquivo novo")
            
            time.sleep(MONITOR_INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitor encerrado pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no monitoramento: {e}")
            print(f"   Tentando novamente em {MONITOR_INTERVAL_SECONDS} segundos...")
            time.sleep(MONITOR_INTERVAL_SECONDS)


def run_init():
    """Inicializa o registro de arquivos conhecidos"""
    print("\n" + "="*60)
    print("🔧 Inicializando registro de arquivos conhecidos")
    print("="*60)
    
    sharepoint = SharePointClient()
    monitor = FileMonitor(sharepoint)
    monitor.initialize_known_files()
    
    print("\n✅ Inicialização concluída!")
    print("   Os arquivos atuais não serão reenviados.")
    print("   Execute 'python main.py --monitor' para iniciar o monitoramento.")


def run_scheduled():
    """Executa o agendador"""
    print(f"⏰ Agendador iniciado - Próxima execução às {SCHEDULE_TIME}")
    print("   (Pressione Ctrl+C para parar)\n")
    
    schedule.every().day.at(SCHEDULE_TIME).do(run_automation)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--schedule":
            run_scheduled()
        elif arg == "--monitor":
            run_monitor()
        elif arg == "--init":
            run_init()
        else:
            print(f"Argumento desconhecido: {arg}")
            print("\nUso:")
            print("  python main.py           - Execução única (envia arquivo mais recente)")
            print("  python main.py --schedule - Agendado às 10h diariamente")
            print("  python main.py --monitor  - Monitoramento contínuo de novos uploads")
            print("  python main.py --init     - Inicializa arquivos (não reenvia existentes)")
    else:
        # Execução única
        run_automation()


if __name__ == "__main__":
    main()
