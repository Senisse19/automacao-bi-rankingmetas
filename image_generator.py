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
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
            "C:/Windows/Fonts/tahomabd.ttf",
        ]
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        # Fallback se não achar nenhuma bold
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
    
    def generate_metas_image(self, periodo, departamentos, total_gs=None, receitas=None, output_path="metas.png"):
        """
        Gera imagem de metas no estilo vertical para WhatsApp
        
        Args:
            periodo: String do período (ex: "Setembro/2026")
            departamentos: Lista de dicts com {nome, meta1, meta2, meta3, realizado, percent}
            total_gs: Dict opcional com metas totais da empresa
            receitas: Dict opcional com dados de receitas {itens: [], outras: "..."}
            output_path: Caminho para salvar
        """
        # Canvas vertical (estilo mobile/WhatsApp)
        self.width = 500
        
        # Calcular altura dinamicamente
        header_h = 60
        gs_card_h = 200  # Altura compacta
        dept_row_h = 175 # Altura compacta para departamentos
        num_dept_rows = 4
        receitas_h = 100 if receitas else 0
        padding = 15
        
        height = header_h + gs_card_h + (num_dept_rows * (dept_row_h + padding)) + receitas_h + 40
        
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fontes (todas bold para maior visibilidade)
        font_header = self._get_font(18, bold=True)
        font_title = self._get_font(15, bold=True)
        font_label = self._get_font(12, bold=True)
        font_value = self._get_font(13, bold=True)
        font_big_value = self._get_font(22, bold=True)
        font_small = self._get_font(11, bold=True)
        
        # Mapa de departamentos
        dept_map = {d["nome"].lower(): d for d in departamentos}
        
        margin = 15
        card_gap = 10
        y = 0
        
        # === HEADER ===
        # Fundo do header (barra dourada)
        draw.rectangle([(0, 0), (self.width, header_h)], fill=self.bg_color)
        
        # Título do relatório com data atual
        data_atual = datetime.now().strftime("%d/%m/%Y")
        header_text = f"RELATÓRIO GERAL - {data_atual}"
        draw.text((margin, 18), header_text, font=font_header, fill=self.card_color)
        
        # Logo GS (canto direito)
        logo_size = 40
        logo_x = self.width - margin - logo_size
        draw.rounded_rectangle(
            [(logo_x, 10), (logo_x + logo_size, 10 + logo_size)],
            radius=6, fill=self.card_color, outline=self.accent_color, width=2
        )
        gs_bbox = draw.textbbox((0, 0), "GS", font=self._get_font(18, bold=True))
        gs_tw = gs_bbox[2] - gs_bbox[0]
        gs_th = gs_bbox[3] - gs_bbox[1]
        draw.text((logo_x + (logo_size - gs_tw)/2, 10 + (logo_size - gs_th)/2 - 2), "GS", font=self._get_font(18, bold=True), fill=self.accent_color)
        
        # Linha dourada abaixo do header
        draw.rectangle([(0, header_h - 4), (self.width, header_h)], fill=self.accent_color)
        
        y = header_h + padding
        
        # === GS - RESUMO GERAL ===
        if total_gs:
            card_w = self.width - 2 * margin
            card_h = gs_card_h
            
            draw.rounded_rectangle([(margin, y), (margin + card_w, y + card_h)], radius=12, fill=self.card_color, outline=self.accent_color, width=2)
            
            # Título
            draw.text((margin + 20, y + 15), "GS - RESUMO GERAL", font=font_title, fill=self.accent_color)
            
            # 3 Metas com barras de progresso
            pad = 20
            meta_y = y + 42
            for i, key in enumerate(["meta1", "meta2", "meta3"]):
                val = total_gs.get(key, "-")
                label = f"Meta {i+1}:"
                
                draw.text((margin + pad, meta_y), label, font=font_label, fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=font_value)
                val_w = bbox[2] - bbox[0]
                draw.text((margin + card_w - pad - val_w, meta_y), val, font=font_value, fill=self.text_color)
                
                # Barra de progresso
                bar_y = meta_y + 16
                draw.rounded_rectangle([(margin + pad, bar_y), (margin + card_w - pad, bar_y + 5)], radius=3, fill=self.accent_color)
                
                meta_y += 30
            
            # Realizado (logo após a última meta)
            real_y = meta_y + 5
            draw.text((margin + pad, real_y), "REALIZADO:", font=font_small, fill=self.muted_text)
            realizado = total_gs.get("realizado", "R$ 0,00")
            draw.text((margin + pad, real_y + 16), realizado, font=font_big_value, fill=self.text_color)
            
            y += card_h + padding
        
        # === DEPARTAMENTOS EM PARES (2 colunas empilhadas) ===
        dept_pairs = [
            [("comercial", "COMERCIAL"), ("operacional", "OPERACIONAL")],
            [("expansão", "EXPANSÃO"), ("corporate", "CORPORATE")],
            [("educação", "EDUCAÇÃO"), ("tax", "TAX")],
            [("franchising", "FRANCHISING"), ("tecnologia", "TECNOLOGIA")]
        ]
        
        card_w = (self.width - 2 * margin - card_gap) // 2
        card_h = dept_row_h
        
        for pair in dept_pairs:
            for i, (key, label) in enumerate(pair):
                cx = margin + i * (card_w + card_gap)
                data = dept_map.get(key, {})
                # Usar o estilo original de card (_draw_dept_card)
                self._draw_dept_card(draw, cx, y, card_w, card_h, label, data, is_small=False)
            
            y += card_h + padding
        
        # === RECEITAS ===
        if receitas:
            rec_y = y
            rec_h = receitas_h
            rec_w = self.width - 2 * margin
            
            draw.rounded_rectangle([(margin, rec_y), (margin + rec_w, rec_y + rec_h)], radius=12, fill=self.card_color)
            
            # Título
            draw.text((margin + (rec_w // 2) - 30, rec_y + 12), "RECEITAS", font=font_title, fill=self.accent_color)
            
            # 3 colunas: Outras Receitas, Intercompany, Não Identificadas
            col_w = (rec_w - 40) // 3
            col_y = rec_y + 45
            pad = 20
            
            # Coluna 1: Outras Receitas
            outras = receitas.get("outras", "R$ 0,00")
            draw.text((margin + pad, col_y), "Outras Receitas:", font=font_small, fill=self.muted_text)
            draw.text((margin + pad, col_y + 16), outras, font=font_value, fill=self.text_color)
            
            # Coluna 2: Intercompany
            intercompany = receitas.get("intercompany", "R$ 0,00")
            col2_x = margin + pad + col_w
            draw.text((col2_x, col_y), "Intercompany:", font=font_small, fill=self.muted_text)
            draw.text((col2_x, col_y + 16), intercompany, font=font_value, fill=self.text_color)
            
            # Coluna 3: Não Identificadas
            nao_ident = receitas.get("nao_identificadas", "R$ 0,00")
            col3_x = margin + pad + col_w * 2
            draw.text((col3_x, col_y), "Não Identificadas:", font=font_small, fill=self.muted_text)
            draw.text((col3_x, col_y + 16), nao_ident, font=font_value, fill=self.text_color)

        img.save(output_path, "PNG")
        return output_path

    def _draw_vertical_card(self, draw, x, y, w, h, title, data, font_title, font_label, font_value, font_small):
        """Helper para desenhar card de departamento no layout vertical"""
        draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=10, fill=self.card_color)
        
        # Padding interno maior
        pad = 18
        
        # Título centralizado
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text((x + (w - tw)/2, y + 12), title, font=font_title, fill=self.accent_color)
        
        # Metas
        meta_y = y + 40
        for i, key in enumerate(["meta1", "meta2", "meta3"]):
            val = data.get(key, "R$ 0,00")
            label = f"Meta {i+1}"
            
            draw.text((x + pad, meta_y), label, font=font_label, fill=self.muted_text)
            
            # Valor alinhado à direita
            bbox = draw.textbbox((0, 0), val, font=font_value)
            val_w = bbox[2] - bbox[0]
            draw.text((x + w - pad - val_w, meta_y), val, font=font_value, fill=self.text_color)
            
            # Barra dourada
            bar_y = meta_y + 17
            draw.rounded_rectangle([(x + pad, bar_y), (x + w - pad, bar_y + 5)], radius=2, fill=self.accent_color)
            
            meta_y += 30
        
        # Realizado
        real_y = y + h - 38
        draw.text((x + pad, real_y), "REALIZADO:", font=font_small, fill=self.muted_text)
        
        realizado = data.get("realizado", "R$ 0,00")
        if realizado == "-":
            realizado = "R$ 0,00"
        draw.text((x + pad, real_y + 14), realizado, font=font_value, fill=self.text_color)

    def _draw_dept_card(self, draw, x, y, w, h, title, data, is_small=False):
        """Helper para desenhar card de departamento"""
        draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=10, fill=self.card_color, outline=self.gold_color, width=1)
        
        # Padding lateral
        pad = 18
        
        # Titulo
        font_title = self._get_font(12 if is_small else 14, bold=True)
        # Centralizar titulo
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text((x + (w - tw)/2, y + 15), title, font=font_title, fill=self.muted_text)
        
        # Metas (barras de progresso simuladas + texto)
        meta_keys = ["meta1", "meta2", "meta3"]
        if is_small:
            # Layout simplificado para cards pquenos
            my = y + 45
            for k in meta_keys:
                val = data.get(k, "-")
                draw.text((x + 10, my), f"Meta {k[-1]}", font=self._get_font(9), fill=self.muted_text)
                
                # Valor direita
                bbox = draw.textbbox((0, 0), val, font=self._get_font(9, bold=True))
                vw = bbox[2] - bbox[0]
                draw.text((x + w - 10 - vw, my), val, font=self._get_font(9, bold=True), fill=self.text_color)
                
                # Barra dourada
                draw.rounded_rectangle([(x + 10, my + 12), (x + w - 10, my + 16)], radius=2, fill=self.gold_color)
                my += 23
        else:
            # Layout padrão com espaçamentos compactos
            my = y + 42
            for k in meta_keys:
                val = data.get(k, "-")
                
                # Usar pad = 18 definido acima
                draw.text((x + pad, my), f"Meta {k[-1]}", font=self._get_font(11, bold=True), fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=self._get_font(11, bold=True))
                vw = bbox[2] - bbox[0]
                draw.text((x + w - pad - vw, my), val, font=self._get_font(11, bold=True), fill=self.text_color)
                
                draw.rounded_rectangle([(x + pad, my + 15), (x + w - pad, my + 19)], radius=2, fill=self.gold_color)
                my += 25

        # Realizado rodapé (sempre mostrar, logo após metas)
        realizado = data.get("realizado", "-")
        if not realizado or realizado == "":
            realizado = "-"
        
        # Posicionar logo após as metas
        ry = my + 3
        draw.text((x + pad, ry), "REALIZADO", font=self._get_font(10, bold=True), fill=self.muted_text)
        
        bbox = draw.textbbox((0, 0), realizado, font=self._get_font(14, bold=True))
        rw = bbox[2] - bbox[0]
        draw.text((x + (w - rw)/2, ry + 14), realizado, font=self._get_font(14, bold=True), fill=self.text_color)

    
    def generate_departamento_image(self, departamento, periodo, output_path=None):
        """
        Gera imagem focada em um único departamento (para envio individual)
        """
        if output_path is None:
            output_path = f"metas_{departamento.get('nome', 'dept').lower()}.png"
        
        height = 400  # Mais espaço para rodapé visível
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
        
        # Card único - altura ajustada para layout vertical
        cx, cw = 25, self.width - 50
        card_h = 250
        draw.rounded_rectangle([(cx, y), (cx + cw, y + card_h)], radius=12, fill=self.card_color)
        
        # Título do card
        draw.text((cx + 25, y + 18), "METAS", font=self._get_font(14, bold=True), fill=self.accent_color)
        draw.line([(cx + 25, y + 45), (cx + cw - 25, y + 45)], fill=self.accent_color, width=1)
        
        # Metas - layout vertical (uma por linha)
        metas = [
            ("Meta 1", departamento.get("meta1", "-")),
            ("Meta 2", departamento.get("meta2", "-")),
            ("Meta 3", departamento.get("meta3", "-"))
        ]
        
        meta_y = y + 55
        pad = 25
        for label, value in metas:
            # Label à esquerda
            draw.text((cx + pad, meta_y), label, font=font_label, fill=self.muted_text)
            
            # Valor à direita
            bbox = draw.textbbox((0, 0), str(value), font=font_value)
            val_w = bbox[2] - bbox[0]
            draw.text((cx + cw - pad - val_w, meta_y), str(value), font=font_value, fill=self.text_color)
            
            meta_y += 28
        
        # Linha separadora
        sep_y = meta_y + 5
        draw.line([(cx + pad, sep_y), (cx + cw - pad, sep_y)], fill=(60, 60, 60), width=1)
        
        # Realizado - destaque maior
        ry = sep_y + 15
        draw.text((cx + pad, ry), "REALIZADO", font=font_label, fill=self.muted_text)
        draw.text((cx + pad, ry + 25), departamento.get("realizado", "-"), font=font_big_value, fill=self.text_color)
        
        # Percentual à direita
        percent = departamento.get("percent", "")
        if percent:
            bbox = draw.textbbox((0, 0), percent, font=font_big_value)
            pw = bbox[2] - bbox[0]
            draw.text((cx + cw - pad - pw, ry + 25), percent, font=font_big_value, fill=self.text_color)
        
        # Rodapé (visível abaixo do card)
        draw.text((25, height - 25), "Grupo Studio • Automação Power BI", font=font_small, fill=(80, 80, 80))
        
        img.save(output_path, "PNG")
        return output_path


# Teste com dados reais do Power BI
if __name__ == "__main__":
    from powerbi_data import PowerBIDataFetcher
    
    generator = ImageGenerator()
    fetcher = PowerBIDataFetcher()
    
    # Buscar dados reais do Power BI
    print("Buscando dados do Power BI...")
    total_gs, departamentos = fetcher.fetch_all_data()
    
    if total_gs is None or departamentos is None:
        print("Erro ao buscar dados. Usando dados de exemplo...")
        # Fallback para dados mock se falhar
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
            {"nome": "Tecnologia", "meta1": "R$ 210.378", "meta2": "R$ 210.378", "meta3": "R$ 216.378", "realizado": "R$ 114.934", "percent": "53%"},
        ]
    
    # Dados de receitas (buscar do Power BI se disponível)
    receitas = {
        "outras": "R$ 1.211",
        "intercompany": "R$ 0,00",
        "nao_identificadas": "R$ 0,00"
    }
    
    # Gerar imagem geral (metas_geral.png) na pasta images/
    print("\nGerando imagem geral...")
    output = generator.generate_metas_image(
        periodo="Janeiro/2026",
        departamentos=departamentos,
        total_gs=total_gs,
        receitas=receitas,
        output_path="images/metas_geral.png"
    )
    print(f"✓ Imagem geral gerada: {output}")
    
    # Gerar imagens individuais de cada departamento na pasta images/
    print("\nGerando imagens individuais...")
    for dept in departamentos:
        nome_arquivo = dept["nome"].lower().replace("ã", "a").replace("ç", "c")
        output_path = f"images/metas_{nome_arquivo}.png"
        generator.generate_departamento_image(
            departamento=dept,
            periodo="Janeiro/2026",
            output_path=output_path
        )
        print(f"✓ {output_path}")
    
    print("\n" + "=" * 50)
    print("Todas as imagens foram geradas na pasta images/!")
    print("=" * 50)
