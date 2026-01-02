"""
Monitor de arquivos do SharePoint
Detecta novos uploads e dispara envio para WhatsApp
"""
import json
import os
from datetime import datetime
from config import KNOWN_FILES_PATH


class FileMonitor:
    def __init__(self, sharepoint_client):
        self.sharepoint = sharepoint_client
        print(f"📂 Caminho do arquivo de controle: {KNOWN_FILES_PATH}")
        print(f"📂 Diretório existe: {os.path.exists(os.path.dirname(KNOWN_FILES_PATH) or '.')}")
        self.known_files = self._load_known_files()
        print(f"📂 Arquivos conhecidos carregados: {len(self.known_files)}")
    
    def _load_known_files(self) -> dict:
        """Carrega arquivos já processados do arquivo JSON"""
        print(f"📂 Verificando se {KNOWN_FILES_PATH} existe: {os.path.exists(KNOWN_FILES_PATH)}")
        if os.path.exists(KNOWN_FILES_PATH):
            try:
                with open(KNOWN_FILES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"📂 Carregados {len(data)} arquivos do JSON")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"❌ Erro ao carregar JSON: {e}")
                return {}
        print(f"📂 Arquivo não existe, iniciando vazio")
        return {}
    
    def _save_known_files(self):
        """Salva arquivos conhecidos no arquivo JSON"""
        # Garantir que o diretório existe
        dir_path = os.path.dirname(KNOWN_FILES_PATH)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"📂 Diretório criado: {dir_path}")
        
        with open(KNOWN_FILES_PATH, "w", encoding="utf-8") as f:
            json.dump(self.known_files, f, indent=2, ensure_ascii=False)
        print(f"💾 Salvo {len(self.known_files)} arquivos em {KNOWN_FILES_PATH}")
    
    def check_for_new_files(self) -> list:
        """
        Verifica se há novos arquivos na pasta Diretoria
        Retorna lista de arquivos novos (não processados anteriormente)
        """
        current_files = self.sharepoint.list_files_in_folder()
        
        if not current_files:
            return []
        
        new_files = []
        
        for file in current_files:
            file_id = file.get("id")
            file_name = file.get("name")
            modified = file.get("lastModifiedDateTime", "")
            
            # Verifica se é um arquivo novo ou foi modificado
            if file_id not in self.known_files:
                print(f"🆕 Novo arquivo detectado: {file_name}")
                new_files.append(file)
            elif self.known_files[file_id].get("lastModified") != modified:
                print(f"📝 Arquivo modificado detectado: {file_name}")
                new_files.append(file)
        
        return new_files
    
    def mark_as_processed(self, file: dict):
        """Marca um arquivo como processado"""
        file_id = file.get("id")
        file_name = file.get("name")
        modified = file.get("lastModifiedDateTime", "")
        
        self.known_files[file_id] = {
            "name": file_name,
            "lastModified": modified,
            "processedAt": datetime.now().isoformat()
        }
        
        self._save_known_files()
        print(f"✅ Arquivo '{file_name}' marcado como processado")
    
    def initialize_known_files(self):
        """
        Inicializa o registro de arquivos conhecidos
        Marca todos os arquivos atuais como 'já processados'
        Útil para primeira execução (evita reenviar arquivos antigos)
        """
        current_files = self.sharepoint.list_files_in_folder()
        
        if not current_files:
            print("⚠️ Nenhum arquivo encontrado para inicialização")
            return
        
        for file in current_files:
            file_id = file.get("id")
            file_name = file.get("name")
            modified = file.get("lastModifiedDateTime", "")
            
            self.known_files[file_id] = {
                "name": file_name,
                "lastModified": modified,
                "processedAt": datetime.now().isoformat(),
                "initializedOnly": True  # Marcador que indica que não foi enviado
            }
        
        self._save_known_files()
        print(f"✅ {len(current_files)} arquivo(s) marcado(s) como conhecidos (não serão reenviados)")
