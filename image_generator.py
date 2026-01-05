"""
Gerador de imagens a partir de dados
Transforma dados do Power BI em imagens bonitas para WhatsApp
"""
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os


class ImageGenerator:
    def __init__(self):
        # Cores do tema - Paleta do Dashboard GS
        self.bg_color = (195, 195, 195)  # Cinza mais escuro (menos branco)
        self.card_color = (26, 26, 26)  # Preto dos cards
        self.text_color = (255, 255, 255)  # Texto branco
        self.accent_color = (201, 169, 98)  # Dourado/champagne
        self.gold_color = (201, 169, 98)  # Dourado para destaques
        self.silver_color = (180, 180, 180)  # Prata
        self.bronze_color = (160, 120, 80)  # Bronze
        self.header_color = (26, 26, 26)  # Header preto
        self.muted_text = (201, 169, 98)  # Texto secundário agora DOURADO para máxima visibilidade
        
        # Dimensões
        self.width = 800
        self.padding = 40
        self.line_height = 50
        
        # Tentar carregar fonte
        self.font_path = self._find_font()
    
    def _find_font(self):
        """Encontra uma fonte disponível no sistema"""
        # Preferência por fontes mais elegantes
        possible_fonts = [
            "C:/Windows/Fonts/segoeuil.ttf",  # Segoe UI Light
            "C:/Windows/Fonts/segoeuisl.ttf",  # Segoe UI Semilight
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibril.ttf",  # Calibri Light
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        return None
    
    def _find_bold_font(self):
        """Encontra fonte bold"""
        possible_fonts = [
            "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
            "C:/Windows/Fonts/calibrib.ttf",  # Calibri Bold
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        return self.font_path
    
    def _get_font(self, size, bold=False):
        """Retorna fonte com tamanho especificado"""
        font_path = self._find_bold_font() if bold else self.font_path
        if font_path:
            return ImageFont.truetype(font_path, size)
        return ImageFont.load_default()
    
    def generate_ranking_image(self, title, data, metrics=None, output_path="ranking.png"):
        """
        Gera imagem de ranking no estilo do dashboard GS
        """
        # Calcular altura necessária
        num_items = len(data) if data else 0
        num_metrics = len(metrics) if metrics else 0
        card_height = 80 + (num_items * 48)  # Mais espaço entre itens
        metrics_height = 100 + (num_metrics * 35) if metrics else 0
        height = 100 + card_height + 50 + metrics_height + 50
        
        # Criar imagem com fundo cinza
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fontes otimizadas
        font_logo = self._get_font(28, bold=True)
        font_title = self._get_font(28, bold=True)
        font_subtitle = self._get_font(13)
        font_card_title = self._get_font(14, bold=True)
        font_item = self._get_font(18)
        font_item_bold = self._get_font(18, bold=True)
        font_value = self._get_font(18, bold=True)
        font_small = self._get_font(11)
        font_metric_label = self._get_font(11)
        font_metric_value = self._get_font(24, bold=True)
        
        y = 35
        
        # Logo GS - box maior e melhor espaçamento
        logo_size = 50
        draw.rounded_rectangle(
            [(25, 20), (25 + logo_size, 20 + logo_size)], 
            radius=8,
            fill=self.card_color, 
            outline=self.accent_color, 
            width=2
        )
        draw.text((35, 28), "GS", font=font_logo, fill=self.accent_color)
        
        # Título principal - melhor posicionamento
        draw.text((95, 25), title.upper(), font=font_title, fill=self.card_color)
        
        # Data/hora
        now = datetime.now().strftime("%d/%m/%Y às %H:%M")
        draw.text((95, 52), f"Atualizado em {now}", font=font_subtitle, fill=(120, 120, 120))
        
        y = 95
        
        # Card principal do ranking (fundo preto) - margens maiores
        card_x = 25
        card_width = self.width - 50
        card_padding = 25
        
        draw.rounded_rectangle(
            [(card_x, y), (card_x + card_width, y + card_height)],
            radius=12,
            fill=self.card_color
        )
        
        # Título do card - mais espaço interno
        draw.text((card_x + card_padding, y + 18), "RANKING", font=font_card_title, fill=self.accent_color)
        
        # Linha dourada abaixo do título - mais espaço
        draw.line(
            [(card_x + card_padding, y + 50), (card_x + card_width - card_padding, y + 50)], 
            fill=self.accent_color, 
            width=1
        )
        
        item_y = y + 65
        
        # Itens do ranking
        for i, item in enumerate(data[:10]):
            name = item.get("name", "N/A")
            value = item.get("value", "")
            percent = item.get("percent", "")
            
            # Cor baseada na posição
            if i == 0:
                name_color = self.gold_color
            elif i == 1:
                name_color = self.silver_color
            elif i == 2:
                name_color = self.bronze_color
            else:
                name_color = self.text_color
            
            # Número + Nome - usando card_padding
            position_text = f"{i+1}º"
            draw.text((card_x + card_padding, item_y), position_text, font=font_item_bold, fill=self.accent_color)
            draw.text((card_x + card_padding + 50, item_y), name, font=font_item, fill=name_color)
            
            # Valor (alinhado à direita)
            value_text = percent if percent else str(value)
            bbox = draw.textbbox((0, 0), value_text, font=font_value)
            text_width = bbox[2] - bbox[0]
            draw.text((card_x + card_width - card_padding - text_width, item_y), value_text, font=font_value, fill=self.accent_color)
            
            item_y += 48  # Mais espaço entre itens
        
        y += card_height + 30
        
        # Cards de métricas (lado a lado) - melhor espaçamento
        if metrics:
            metric_items = list(metrics.items())
            num_cols = min(3, len(metric_items))
            gap = 20  # Espaço entre cards
            metric_width = (self.width - 50 - (num_cols - 1) * gap) // num_cols
            
            for i, (key, value) in enumerate(metric_items[:3]):
                mx = 25 + i * (metric_width + gap)
                
                draw.rounded_rectangle(
                    [(mx, y), (mx + metric_width, y + 80)],
                    radius=10,
                    fill=self.card_color
                )
                
                # Label - mais espaço interno
                draw.text((mx + 18, y + 15), key.upper(), font=font_metric_label, fill=self.muted_text)
                
                # Valor - mais espaço
                draw.text((mx + 18, y + 38), str(value), font=font_metric_value, fill=self.accent_color)
            
            y += 100
        
        # Rodapé
        draw.text((30, height - 30), "Grupo Studio • Automação Power BI", font=font_small, fill=(120, 120, 120))
        
        # Salvar
        img.save(output_path, "PNG")
        return output_path
    
    def generate_metas_image(self, periodo, departamentos, total_gs=None, output_path="metas.png"):
        """
        Gera imagem de metas no estilo do dashboard GS
        
        Args:
            periodo: String do período (ex: "Setembro/2026")
            departamentos: Lista de dicts com {nome, meta1, meta2, meta3, realizado, percent}
            total_gs: Dict opcional com metas totais da empresa
            output_path: Caminho para salvar
        """
        # Calcular altura
        num_deps = len(departamentos)
        cols = 2 if num_deps > 4 else 1
        rows = (num_deps + cols - 1) // cols
        card_height = 140
        header_height = 90
        total_height = 200 if total_gs else 0
        height = header_height + total_height + (rows * (card_height + 15)) + 80
        
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fontes
        font_logo = self._get_font(28, bold=True)
        font_title = self._get_font(24, bold=True)
        font_periodo = self._get_font(14)
        font_card_title = self._get_font(14, bold=True)
        font_label = self._get_font(13, bold=True) # Aumentado e BOLD
        font_value = self._get_font(15, bold=True) # Aumentado de 14
        font_big_value = self._get_font(28, bold=True)
        font_small = self._get_font(12)
        
        y = 25
        
        # Logo GS
        # Logo GS (Centralizado)
        logo_size = 50
        logo_x = 25
        draw.rounded_rectangle(
            [(logo_x, y), (logo_x + logo_size, y + logo_size)], 
            radius=8, fill=self.card_color, outline=self.accent_color, width=2
        )
        
        # Centralizar texto GS
        gs_text = "GS"
        bbox = draw.textbbox((0, 0), gs_text, font=font_logo)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Centralização matemática pura (sem offset manual)
        draw.text((logo_x + (logo_size - tw) / 2, y + (logo_size - th) / 2 - 2), gs_text, font=font_logo, fill=self.accent_color)
        
        # Título e período
        draw.text((95, y + 5), "METAS", font=font_title, fill=self.card_color)
        draw.text((95, y + 32), f"Período: {periodo}", font=font_periodo, fill=(100, 100, 100))
        
        y = header_height
        
        # Card total GS (se fornecido)
        if total_gs:
            card_x = 25
            card_w = self.width - 50
            
            draw.rounded_rectangle(
                [(card_x, y), (card_x + card_w, y + 180)],
                radius=12, fill=self.card_color
            )
            
            draw.text((card_x + 20, y + 15), "TOTAL GS", font=font_card_title, fill=self.accent_color)
            draw.line([(card_x + 20, y + 42), (card_x + card_w - 20, y + 42)], fill=self.accent_color, width=1)
            
            # Metas em linha
            meta_y = y + 55
            for i, (label, value) in enumerate([("Meta 1", total_gs.get("meta1", "-")), 
                                                 ("Meta 2", total_gs.get("meta2", "-")), 
                                                 ("Meta 3", total_gs.get("meta3", "-"))]):
                mx = card_x + 20 + i * 220
                draw.text((mx, meta_y), label, font=font_label, fill=self.muted_text)
                draw.text((mx, meta_y + 18), value, font=font_value, fill=self.text_color)
            
            # Realizado grande
            realizado_y = y + 110
            draw.text((card_x + 20, realizado_y), "REALIZADO", font=font_label, fill=self.muted_text)
            draw.text((card_x + 20, realizado_y + 18), total_gs.get("realizado", "-"), font=font_big_value, fill=self.accent_color)
            
            # Percentual
            percent = total_gs.get("percent", "")
            if percent:
                bbox = draw.textbbox((0, 0), percent, font=font_big_value)
                pw = bbox[2] - bbox[0]
                draw.text((card_x + card_w - 20 - pw, realizado_y + 18), percent, font=font_big_value, fill=self.accent_color)
            
            y += 195
        
        # Cards de departamentos
        card_w = (self.width - 50 - 15) // cols if cols == 2 else self.width - 50
        
        for idx, dep in enumerate(departamentos):
            col = idx % cols
            row = idx // cols
            
            cx = 25 + col * (card_w + 15)
            cy = y + row * (card_height + 15)
            
            draw.rounded_rectangle(
                [(cx, cy), (cx + card_w, cy + card_height)],
                radius=10, fill=self.card_color
            )
            
            # Nome do departamento
            draw.text((cx + 15, cy + 12), dep.get("nome", "").upper(), font=font_card_title, fill=self.accent_color)
            draw.line([(cx + 15, cy + 35), (cx + card_w - 15, cy + 35)], fill=self.accent_color, width=1)
            
            # Metas
            meta_y = cy + 45
            metas = [("Meta 1", dep.get("meta1", "-")), ("Meta 2", dep.get("meta2", "-")), ("Meta 3", dep.get("meta3", "-"))]
            
            for i, (label, value) in enumerate(metas):
                draw.text((cx + 15, meta_y + i * 22), label, font=font_label, fill=self.muted_text)
                # Valor alinhado à direita - Agora DOURADO
                bbox = draw.textbbox((0, 0), str(value), font=font_value)
                vw = bbox[2] - bbox[0]
                draw.text((cx + card_w - 15 - vw, meta_y + i * 22), str(value), font=font_value, fill=self.accent_color)
            
            # Realizado na parte inferior
            realizado = dep.get("realizado", "-")
            percent = dep.get("percent", "")
            
            ry = cy + card_height - 25
            draw.text((cx + 15, ry), "REALIZADO", font=font_small, fill=self.muted_text)
            
            realizado_text = f"{realizado}"
            if percent:
                realizado_text += f"  ({percent})"
            bbox = draw.textbbox((0, 0), realizado_text, font=font_value)
            rw = bbox[2] - bbox[0]
            draw.text((cx + card_w - 15 - rw, ry), realizado_text, font=font_value, fill=self.accent_color)
        
        # Rodapé
        draw.text((25, height - 30), "Grupo Studio • Automação Power BI", font=font_small, fill=(120, 120, 120))
        
        img.save(output_path, "PNG")
        return output_path
    
    def generate_departamento_image(self, departamento, periodo, output_path=None):
        """
        Gera imagem focada em um único departamento (para envio individual)
        """
        if output_path is None:
            output_path = f"metas_{departamento.get('nome', 'dept').lower()}.png"
        
        height = 360
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fontes
        font_logo = self._get_font(28, bold=True)
        font_title = self._get_font(24, bold=True)
        font_periodo = self._get_font(14, bold=True) # Periodo em bold
        font_label = self._get_font(14, bold=True) # Aumentado e BOLD
        font_value = self._get_font(18, bold=True) # Aumentado de 16
        font_big_value = self._get_font(36, bold=True)
        font_small = self._get_font(12)
        
        y = 25
        
        # Logo e título
        # Logo e título (Centralizado)
        logo_size = 50
        logo_x = 25
        draw.rounded_rectangle([(logo_x, y), (logo_x + logo_size, y + logo_size)], radius=8, fill=self.card_color, outline=self.accent_color, width=2)
        
        # Centralizar texto GS
        gs_text = "GS"
        bbox = draw.textbbox((0, 0), gs_text, font=font_logo)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((logo_x + (logo_size - tw) / 2, y + (logo_size - th) / 2 - 2), gs_text, font=font_logo, fill=self.accent_color)
        
        nome = departamento.get("nome", "DEPARTAMENTO").upper()
        draw.text((95, y + 8), nome, font=font_title, fill=self.card_color)
        draw.text((95, y + 38), f"Período: {periodo}", font=font_periodo, fill=(100, 100, 100))
        
        y = 95
        
        # Card único - mais alto
        cx, cw = 25, self.width - 50
        card_h = 220
        draw.rounded_rectangle([(cx, y), (cx + cw, y + card_h)], radius=12, fill=self.card_color)
        
        # Título do card
        draw.text((cx + 25, y + 18), "METAS", font=self._get_font(14, bold=True), fill=self.accent_color)
        draw.line([(cx + 25, y + 45), (cx + cw - 25, y + 45)], fill=self.accent_color, width=1)
        
        # Metas - layout em linha
        meta_y = y + 60
        metas = [
            ("Meta 1", departamento.get("meta1", "-")),
            ("Meta 2", departamento.get("meta2", "-")),
            ("Meta 3", departamento.get("meta3", "-"))
        ]
        
        col_width = (cw - 50) // 3
        for i, (label, value) in enumerate(metas):
            mx = cx + 25 + i * col_width
            # Labels em BRANCO (muted_text atualizado), Valores em DOURADO
            draw.text((mx, meta_y), label, font=font_label, fill=self.muted_text)
            draw.text((mx, meta_y + 22), str(value), font=font_value, fill=self.accent_color)
        
        # Linha separadora
        sep_y = y + 115
        draw.line([(cx + 25, sep_y), (cx + cw - 25, sep_y)], fill=(60, 60, 60), width=1)
        
        # Realizado - destaque maior
        ry = y + 130
        draw.text((cx + 25, ry), "REALIZADO", font=font_label, fill=self.muted_text)
        draw.text((cx + 25, ry + 22), departamento.get("realizado", "-"), font=font_big_value, fill=self.accent_color)
        
        # Percentual à direita
        percent = departamento.get("percent", "")
        if percent:
            bbox = draw.textbbox((0, 0), percent, font=font_big_value)
            pw = bbox[2] - bbox[0]
            draw.text((cx + cw - 25 - pw, ry + 22), percent, font=font_big_value, fill=self.accent_color)
        
        # Rodapé
        draw.text((25, height - 28), "Grupo Studio • Automação Power BI", font=font_small, fill=(120, 120, 120))
        
        img.save(output_path, "PNG")
        return output_path


# Teste
if __name__ == "__main__":
    generator = ImageGenerator()
    
    # Dados de exemplo baseados no dashboard real
    total_gs = {
        "meta1": "R$ 11.269.676",
        "meta2": "R$ 12.269.676", 
        "meta3": "R$ 13.269.676",
        "realizado": "R$ 229.868",
        "percent": "2,04%"
    }
    
    departamentos = [
        {"nome": "Comercial", "meta1": "R$ 1.394.059", "meta2": "R$ 1.394.059", "meta3": "R$ 1.394.059", "realizado": "-", "percent": ""},
        {"nome": "Operacional", "meta1": "R$ 9.875.617", "meta2": "R$ 9.875.617", "meta3": "R$ 9.875.617", "realizado": "R$ 114.934", "percent": "1,16%"},
        {"nome": "Expansão", "meta1": "R$ 833.356", "meta2": "R$ 833.356", "meta3": "R$ 833.356", "realizado": "-", "percent": ""},
        {"nome": "Franchising", "meta1": "R$ 553.341", "meta2": "R$ 553.341", "meta3": "R$ 553.341", "realizado": "-", "percent": ""},
        {"nome": "Educação", "meta1": "R$ 207.362", "meta2": "R$ 207.362", "meta3": "R$ 207.362", "realizado": "-", "percent": ""},
        {"nome": "Tax", "meta1": "R$ 7.654.364", "meta2": "R$ 7.654.364", "meta3": "R$ 7.654.364", "realizado": "-", "percent": ""},
        {"nome": "Corporate", "meta1": "R$ 2.004.875", "meta2": "R$ 2.004.875", "meta3": "R$ 2.004.875", "realizado": "-", "percent": ""},
        {"nome": "PJ", "meta1": "R$ 210.378", "meta2": "R$ 210.378", "meta3": "R$ 216.378", "realizado": "R$ 114.934", "percent": "53%"},
    ]
    
    # Gerar imagem geral (para grupo principal)
    output = generator.generate_metas_image(
        periodo="Setembro/2026",
        departamentos=departamentos,
        total_gs=total_gs,
        output_path="metas_geral.png"
    )
    print(f"Imagem geral gerada: {output}")
    
    # Gerar imagem de um departamento específico (para grupo individual)
    output2 = generator.generate_departamento_image(
        departamento=departamentos[1],  # Operacional
        periodo="Setembro/2026",
        output_path="metas_operacional.png"
    )
    print(f"Imagem departamento gerada: {output2}")
    
    print("\nAbra os arquivos para visualizar!")
