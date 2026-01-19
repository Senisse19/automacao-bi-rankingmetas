from PIL import Image, ImageDraw
from datetime import datetime, timedelta
from .base_renderer import BaseRenderer

class MetasRenderer(BaseRenderer):
    """
    Renderizador para relatórios de Metas e Rankings.
    """
    
    def generate_ranking_image(self, title, data, metrics=None, output_path="ranking.png"):
        """
        Gera uma imagem de Ranking (estilo tabela) com Top 10 e métricas adicionais.
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
        
        # Header (Usando o método base refatorado, adaptando chamadas antigas se necessário)
        # O método antigo usava _draw_header com lógica fixa. Agora usamos o base.
        # title é passado. Data é 'agora'.
        now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
        
        # Nota: O generate_ranking_image original não usava _draw_header refatorado, ele tinha lógica inline.
        # Vamos substituir pela chamada padronizada para consistência.
        header_h = self._draw_header(draw, title.upper(), now_str)
        
        y = header_h + 30
        
        # Card principal do ranking
        card_x = 25
        card_width = self.width - 50
        card_padding = 25
        
        draw.rounded_rectangle(
            [(card_x, y), (card_x + card_width, y + card_height)],
            radius=12,
            fill=self.card_color
        )
        
        draw.text((card_x + card_padding, y + 18), "RANKING", font=font_card_title, fill=self.accent_color)
        
        draw.line(
            [(card_x + card_padding, y + 50), (card_x + card_width - card_padding, y + 50)], 
            fill=self.accent_color, 
            width=1
        )
        
        item_y = y + 65
        
        for i, item in enumerate(data[:10]):
            name = item.get("name", "N/A")
            value = item.get("value", "")
            percent = item.get("percent", "")
            
            if i == 0:
                name_color = self.gold_color
            elif i == 1:
                name_color = self.silver_color
            elif i == 2:
                name_color = self.bronze_color
            else:
                name_color = self.text_color
            
            position_text = f"{i+1}º"
            draw.text((card_x + card_padding, item_y), position_text, font=font_item_bold, fill=self.accent_color)
            draw.text((card_x + card_padding + 50, item_y), name, font=font_item, fill=name_color)
            
            if percent:
                value_text = f"{percent:.1f}%" if isinstance(percent, (int, float)) else str(percent)
            else:
                 value_text = str(value)
            
            bbox = draw.textbbox((0, 0), value_text, font=font_value)
            text_width = bbox[2] - bbox[0]
            draw.text((card_x + card_width - card_padding - text_width, item_y), value_text, font=font_value, fill=self.accent_color)
            
            item_y += 48
        
        y += card_height + 30
        
        if metrics:
            metric_items = list(metrics.items())
            num_cols = min(3, len(metric_items))
            gap = 20
            metric_width = (self.width - 50 - (num_cols - 1) * gap) // num_cols
            
            for i, (key, value) in enumerate(metric_items[:3]):
                mx = 25 + i * (metric_width + gap)
                
                draw.rounded_rectangle(
                    [(mx, y), (mx + metric_width, y + 80)],
                    radius=10,
                    fill=self.card_color
                )
                
                draw.text((mx + 18, y + 15), key.upper(), font=font_metric_label, fill=self.muted_text)
                draw.text((mx + 18, y + 38), str(value), font=font_metric_value, fill=self.accent_color)
            
            y += 100
        
        self._draw_footer(draw, height)
        img.save(output_path, "PNG")
        return output_path

    def generate_metas_image(self, periodo, departamentos, total_gs=None, receitas=None, output_path="metas.png"):
        self.width = 500
        
        header_h = 100
        gs_card_h = 240
        dept_row_h = 210
        num_dept_rows = 4
        receitas_h = 100 if receitas else 0
        padding = 15

        height = header_h + gs_card_h + (num_dept_rows * (dept_row_h + padding)) + receitas_h + 80
        
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        font_title = self._get_font(15, bold=True)
        font_label = self._get_font(12, bold=True)
        font_value = self._get_font(13, bold=True)
        font_big_value = self._get_font(22, bold=True)
        font_small = self._get_font(11, bold=True)
        
        dept_map = {d["nome"].lower(): d for d in departamentos}
        margin = 15
        card_gap = 10
        
        header_h = self._draw_header(draw, "RELATÓRIO DE METAS", periodo)
        y = header_h + padding
        
        if total_gs:
            card_w = self.width - 2 * margin
            card_h = gs_card_h
            
            draw.rounded_rectangle([(margin, y), (margin + card_w, y + card_h)], radius=12, fill=self.card_color, outline=self.accent_color, width=2)
            draw.text((margin + 20, y + 15), "GS - RESUMO GERAL", font=font_title, fill=self.accent_color)
            
            pad = 20
            meta_y = y + 42
            pct_keys = ["pct_meta1", "pct_meta2", "pct_meta3"]
            for i, key in enumerate(["meta1", "meta2", "meta3"]):
                val = str(total_gs.get(key, "-"))
                pct = total_gs.get(pct_keys[i], 0)
                pct_text = f"{pct:.0f}%" if pct else "0%"
                label = f"Meta {i+1}"
                
                draw.text((margin + pad, meta_y), label, font=font_label, fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=font_value)
                val_w = bbox[2] - bbox[0]
                draw.text((margin + card_w - pad - val_w, meta_y), val, font=font_value, fill=self.text_color)
                
                draw.text((margin + pad, meta_y + 14), pct_text, font=font_small, fill=self.muted_text)
                
                bar_y = meta_y + 28
                bar_width = card_w - 2 * pad
                draw.rounded_rectangle([(margin + pad, bar_y), (margin + pad + bar_width, bar_y + 6)], radius=3, fill=(60, 60, 60))
                
                fill_width = max(0, min(bar_width, bar_width * (pct / 100)))
                if fill_width > 0:
                    draw.rounded_rectangle([(margin + pad, bar_y), (margin + pad + fill_width, bar_y + 6)], radius=3, fill=self.accent_color)
                
                meta_y += 40
            
            real_y = meta_y + 5
            draw.text((margin + pad, real_y), "REALIZADO:", font=font_small, fill=self.muted_text)
            realizado = str(total_gs.get("realizado", "R$ 0,00"))
            draw.text((margin + pad, real_y + 16), realizado, font=font_big_value, fill=self.text_color)
            
            y += card_h + padding
        
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
                self._draw_dept_card(draw, cx, y, card_w, card_h, label, data, is_small=False)
            y += card_h + padding
        
        if receitas:
            rec_y = y
            rec_h = receitas_h
            rec_w = self.width - 2 * margin
            draw.rounded_rectangle([(margin, rec_y), (margin + rec_w, rec_y + rec_h)], radius=12, fill=self.card_color)
            
            title_text = "RECEITAS"
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_w = title_bbox[2] - title_bbox[0]
            draw.text((margin + (rec_w - title_w) / 2, rec_y + 12), title_text, font=font_title, fill=self.accent_color)
            
            col_w = rec_w // 4
            col_y = rec_y + 45
            
            keys = [("outras", "Outras Receitas:"), ("intercompany", "Intercompany:"), 
                    ("nao_identificadas", "Não Identificadas:"), ("sem_categoria", "Sem Categoria:")]

            for i, (key, label) in enumerate(keys):
                val = str(receitas.get(key, "R$ 0,00"))
                center = margin + (col_w * i) + col_w // 2
                
                bbox_l = draw.textbbox((0, 0), label, font=font_small)
                wl = bbox_l[2] - bbox_l[0]
                draw.text((center - wl // 2, col_y), label, font=font_small, fill=self.muted_text)
                
                bbox_v = draw.textbbox((0, 0), val, font=font_value)
                wv = bbox_v[2] - bbox_v[0]
                draw.text((center - wv // 2, col_y + 16), val, font=font_value, fill=self.text_color)

        self._draw_footer(draw, height)
        img.save(output_path, "PNG")
        return output_path

    def _draw_dept_card(self, draw, x, y, w, h, title, data, is_small=False):
        draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=10, fill=self.card_color, outline=self.gold_color, width=1)
        pad = 18
        
        font_title = self._get_font(12 if is_small else 14, bold=True)
        bbox = draw.textbbox((0, 0), title, font=font_title)
        tw = bbox[2] - bbox[0]
        draw.text((x + (w - tw)/2, y + 15), title, font=font_title, fill=self.muted_text)
        
        meta_keys = ["meta1", "meta2", "meta3"]
        pct_keys = ["pct_meta1", "pct_meta2", "pct_meta3"]
        if is_small:
            my = y + 45
            for i, k in enumerate(meta_keys):
                val = str(data.get(k, "-"))
                pct = data.get(pct_keys[i], 0)
                pct_text = f"{pct:.0f}%"
                
                draw.text((x + 10, my), f"Meta {k[-1]}", font=self._get_font(9), fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=self._get_font(9, bold=True))
                vw = bbox[2] - bbox[0]
                draw.text((x + w - 10 - vw, my), val, font=self._get_font(9, bold=True), fill=self.text_color)
                
                draw.text((x + 10, my + 11), pct_text, font=self._get_font(8), fill=self.muted_text)
                
                bar_width = w - 20
                draw.rounded_rectangle([(x + 10, my + 20), (x + w - 10, my + 24)], radius=2, fill=(60, 60, 60))
                fill_width = max(0, min(bar_width, bar_width * (pct / 100)))
                if fill_width > 0:
                    draw.rounded_rectangle([(x + 10, my + 20), (x + 10 + fill_width, my + 24)], radius=2, fill=self.gold_color)
                my += 30
        else:
            my = y + 42
            for i, k in enumerate(meta_keys):
                val = str(data.get(k, "-"))
                pct = data.get(pct_keys[i], 0)
                pct_text = f"{pct:.0f}%"
                
                draw.text((x + pad, my), f"Meta {k[-1]}", font=self._get_font(11, bold=True), fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=self._get_font(11, bold=True))
                vw = bbox[2] - bbox[0]
                draw.text((x + w - pad - vw, my), val, font=self._get_font(11, bold=True), fill=self.text_color)
                
                draw.text((x + pad, my + 13), pct_text, font=self._get_font(9, bold=True), fill=self.muted_text)
                
                bar_y = my + 24
                bar_width = w - 2 * pad
                draw.rounded_rectangle([(x + pad, bar_y), (x + w - pad, bar_y + 5)], radius=2, fill=(60, 60, 60))
                
                fill_width = max(0, min(bar_width, bar_width * (pct / 100)))
                if fill_width > 0:
                    draw.rounded_rectangle([(x + pad, bar_y), (x + pad + fill_width, bar_y + 5)], radius=2, fill=self.gold_color)
                my += 35

        realizado = str(data.get("realizado", "-"))
        if not realizado or realizado == "":
            realizado = "-"
        
        ry = my + 3
        draw.text((x + pad, ry), "REALIZADO", font=self._get_font(10, bold=True), fill=self.muted_text)
        
        bbox = draw.textbbox((0, 0), realizado, font=self._get_font(14, bold=True))
        rw = bbox[2] - bbox[0]
        draw.text((x + (w - rw)/2, ry + 14), realizado, font=self._get_font(14, bold=True), fill=self.text_color)

    def generate_resumo_image(self, periodo, total_gs=None, receitas=None, output_path="metas_resumo.png"):
        self.width = 500
        header_h = 70
        gs_card_h = 240
        receitas_h = 100 if receitas else 0
        padding = 15
        height = header_h + gs_card_h + padding + receitas_h + 80
        
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        font_title = self._get_font(15, bold=True)
        font_label = self._get_font(12, bold=True)
        font_value = self._get_font(13, bold=True)
        font_big_value = self._get_font(22, bold=True)
        font_small = self._get_font(11, bold=True)
        
        margin = 15
        
        data_atual = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        header_h = self._draw_header(draw, "RELATÓRIO GERAL", data_atual)
        y = header_h + padding
        
        if total_gs:
            card_w = self.width - 2 * margin
            card_h = gs_card_h
            
            draw.rounded_rectangle([(margin, y), (margin + card_w, y + card_h)], radius=12, fill=self.card_color, outline=self.accent_color, width=2)
            draw.text((margin + 20, y + 15), "GS - RESUMO GERAL", font=font_title, fill=self.accent_color)
            
            pad = 20
            meta_y = y + 42
            pct_keys = ["pct_meta1", "pct_meta2", "pct_meta3"]
            for i, key in enumerate(["meta1", "meta2", "meta3"]):
                val = str(total_gs.get(key, "-"))
                pct = total_gs.get(pct_keys[i], 0)
                pct_text = f"{pct:.0f}%" if pct else "0%"
                label = f"Meta {i+1}"
                
                draw.text((margin + pad, meta_y), label, font=font_label, fill=self.muted_text)
                
                bbox = draw.textbbox((0, 0), val, font=font_value)
                val_w = bbox[2] - bbox[0]
                draw.text((margin + card_w - pad - val_w, meta_y), val, font=font_value, fill=self.text_color)
                
                draw.text((margin + pad, meta_y + 14), pct_text, font=font_small, fill=self.muted_text)
                
                bar_y = meta_y + 28
                bar_width = card_w - 2 * pad
                draw.rounded_rectangle([(margin + pad, bar_y), (margin + pad + bar_width, bar_y + 6)], radius=3, fill=(60, 60, 60))
                
                fill_width = max(0, min(bar_width, bar_width * (pct / 100)))
                if fill_width > 0:
                    draw.rounded_rectangle([(margin + pad, bar_y), (margin + pad + fill_width, bar_y + 6)], radius=3, fill=self.accent_color)
                meta_y += 40
            
            real_y = meta_y + 5
            draw.text((margin + pad, real_y), "REALIZADO:", font=font_small, fill=self.muted_text)
            realizado = str(total_gs.get("realizado", "R$ 0,00"))
            draw.text((margin + pad, real_y + 16), realizado, font=font_big_value, fill=self.text_color)
            
            y += card_h + padding
        
        if receitas:
            rec_y = y
            rec_h = receitas_h
            rec_w = self.width - 2 * margin
            draw.rounded_rectangle([(margin, rec_y), (margin + rec_w, rec_y + rec_h)], radius=12, fill=self.card_color)
            
            title_text = "RECEITAS"
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_w = title_bbox[2] - title_bbox[0]
            draw.text((margin + (rec_w - title_w) / 2, rec_y + 12), title_text, font=font_title, fill=self.accent_color)
            
            col_w = rec_w // 4
            col_y = rec_y + 45
            
            keys = [("outras", "Outras Receitas:"), ("intercompany", "Intercompany:"), 
                    ("nao_identificadas", "Não Identificadas:"), ("sem_categoria", "Sem Categoria:")]
            
            for i, (key, label) in enumerate(keys):
                val = str(receitas.get(key, "R$ 0,00"))
                center = margin + (col_w * i) + col_w // 2
                
                bbox_l = draw.textbbox((0, 0), label, font=font_small)
                wl = bbox_l[2] - bbox_l[0]
                draw.text((center - wl // 2, col_y), label, font=font_small, fill=self.muted_text)
                
                bbox_v = draw.textbbox((0, 0), val, font=font_value)
                wv = bbox_v[2] - bbox_v[0]
                draw.text((center - wv // 2, col_y + 16), val, font=font_value, fill=self.text_color)
        
        self._draw_footer(draw, height)
        img.save(output_path, "PNG")
        return output_path

    def generate_departamento_image(self, departamento, periodo, output_path=None):
        if output_path is None:
            output_path = f"metas_{departamento.get('nome', 'dept').lower()}.png"
        
        height = 480
        img = Image.new("RGB", (self.width, height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        font_label = self._get_font(14, bold=True)
        font_value = self._get_font(18, bold=True)
        font_big_value = self._get_font(36, bold=True)
        font_small = self._get_font(12)
        
        nome = departamento.get("nome", "DEPARTAMENTO").upper()
        data_geracao = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        periodo_display = f"Período: {data_geracao}"
        
        header_h = self._draw_header(draw, nome, periodo_display)
        y = header_h + 15
        y = 85 # Override? This was in original code. Wait, original code said y = 85 after y = header_h + 15. The header calculation logic implies it should flow.
        # But if header is ~70, y=85 is strict.
        # Original code (Line 692 in Step 209): y = 85.
        # Just to be safe and consistent with refactor, knowing header is 70, y=85 is 15px margin.
        
        cx, cw = 25, self.width - 50
        card_h = 300
        draw.rounded_rectangle([(cx, y), (cx + cw, y + card_h)], radius=12, fill=self.card_color)
        
        draw.text((cx + 25, y + 18), "METAS", font=self._get_font(14, bold=True), fill=self.accent_color)
        draw.line([(cx + 25, y + 45), (cx + cw - 25, y + 45)], fill=self.accent_color, width=1)
        
        metas = [
            ("Meta 1", departamento.get("meta1", "-"), departamento.get("pct_meta1", 0)),
            ("Meta 2", departamento.get("meta2", "-"), departamento.get("pct_meta2", 0)),
            ("Meta 3", departamento.get("meta3", "-"), departamento.get("pct_meta3", 0))
        ]
        
        meta_y = y + 55
        pad = 25
        bar_width = cw - 2 * pad
        
        for label, value, pct in metas:
            pct_text = f"{pct:.0f}%" if pct else "0%"
            
            draw.text((cx + pad, meta_y), label, font=font_label, fill=self.muted_text)
            
            val_str = str(value)
            bbox = draw.textbbox((0, 0), val_str, font=font_value)
            val_w = bbox[2] - bbox[0]
            draw.text((cx + cw - pad - val_w, meta_y), val_str, font=font_value, fill=self.text_color)
            
            draw.text((cx + pad, meta_y + 18), pct_text, font=self._get_font(11, bold=True), fill=self.muted_text)
            
            bar_y = meta_y + 32
            draw.rounded_rectangle([(cx + pad, bar_y), (cx + cw - pad, bar_y + 6)], radius=3, fill=(60, 60, 60))
            
            fill_width = max(0, min(bar_width, bar_width * (pct / 100)))
            if fill_width > 0:
                draw.rounded_rectangle([(cx + pad, bar_y), (cx + pad + fill_width, bar_y + 6)], radius=3, fill=self.accent_color)
            
            meta_y += 50
        
        sep_y = meta_y + 5
        draw.line([(cx + pad, sep_y), (cx + cw - pad, sep_y)], fill=(60, 60, 60), width=1)
        
        ry = sep_y + 15
        draw.text((cx + pad, ry), "REALIZADO", font=font_label, fill=self.muted_text)
        draw.text((cx + pad, ry + 25), str(departamento.get("realizado", "-")), font=font_big_value, fill=self.text_color)
        
        draw.text((25, height - 25), "Grupo Studio • Automação Power BI", font=font_small, fill=(80, 80, 80))
        img.save(output_path, "PNG")
        return output_path
