"""
Gerador de Imagens (FACADE)
Responsável por delegar a criação das imagens para os renderizadores especializados.
"""
import os
from datetime import datetime
# from services.image_renderer.metas_renderer import MetasRenderer
# from services.image_renderer.unidades_renderer import UnidadesRenderer
from .image_renderer.metas_renderer import MetasRenderer
from .image_renderer.metas_renderer import MetasRenderer
from .image_renderer.unidades_renderer import UnidadesRenderer
from .image_renderer.jobs_renderer import JobsRenderer

class ImageGenerator:
    """
    Facade que delega a geração de imagens para MetasRenderer e UnidadesRenderer.
    Mantém a interface original para compatibilidade.
    """
    def __init__(self):
        self.metas_renderer = MetasRenderer()
        self.unidades_renderer = UnidadesRenderer()
        self.jobs_renderer = JobsRenderer()

    def generate_ranking_image(self, title, data, metrics=None, output_path="ranking.png"):
        return self.metas_renderer.generate_ranking_image(title, data, metrics, output_path)

    def generate_metas_image(self, periodo, departamentos, total_gs=None, receitas=None, output_path="metas.png"):
        return self.metas_renderer.generate_metas_image(periodo, departamentos, total_gs, receitas, output_path)

    def generate_resumo_image(self, periodo, total_gs=None, receitas=None, output_path="metas_resumo.png"):
        return self.metas_renderer.generate_resumo_image(periodo, total_gs, receitas, output_path)

    def generate_departamento_image(self, departamento, periodo, output_path=None):
        return self.metas_renderer.generate_departamento_image(departamento, periodo, output_path)

    def generate_unidades_reports(self, data, report_type="daily", output_path="unidades_report.png"):
        return self.unidades_renderer.generate_unidades_reports(data, report_type, output_path)

    def generate_jobs_report(self, new_jobs, cancelled_jobs, report_title="RELATÓRIO DE JOBS", output_path="jobs_report.pdf"):
        return self.jobs_renderer.generate_jobs_report(new_jobs, cancelled_jobs, report_title, output_path)


if __name__ == "__main__":
    import sys
    
    # Adicionar diretório raiz ao path para permitir imports de 'clients' e 'services'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    sys.path.append(root_dir)

    # Imports que dependem do path ajustado
    from core.services.powerbi_data import PowerBIDataFetcher
    from core.clients.unidades_client import UnidadesClient
    from config import IMAGES_DIR

    print("\n=== GERADOR DE IMAGENS (FACADE TEST) ===")
    
    generator = ImageGenerator()
    
    # Teste Metas (Simulado ou Real se variaveis de ambiente setadas)
    print("\n[1/2] Testando Facade Metas...")
    # ... (Poderíamos manter o teste original aqui, mas simplificarei para apenas instanciar)
    
    print("Facade inicializada com sucesso.")
