from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
from .base_renderer import BaseRenderer

class UnidadesRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        # Background sampled from mock_unidades_weekly.png
        self.bg_color = (195, 195, 195)    # Light Grey
        
        # Cards remain Dark for contrast
        self.card_color = (31, 31, 31)     # #1F1F1F
        self.accent_color = (213, 174, 119) # #D5AE77
        self.light_gold = (213, 174, 119)   # #D5AE77
        
        # High-DPI Scaling
        self.scale = 4
        self.padding = 20 * self.scale

    def generate_unidades_reports(self, data, report_type="daily", output_path="unidades_report.pdf"):
        """
        Gera relatório de Novas Unidades e Cancelamentos com Layout Dark Premium e Paginação (High DPI).
        """
        s = self.scale
        self.width = 650 * s
        
        # Estilos Fontes (Sizes are pre-scaled in BaseRenderer)
        font_header_main = self._get_font(24, bold=True)
        font_section = self._get_font(18, bold=True)
        
        font_label = self._get_font(11, bold=True) 
        font_value = self._get_font(14, bold=False)
        font_value_bold = self._get_font(14, bold=True)
        
        font_money_label = self._get_font(10, bold=True) 
        font_money = self._get_font(18, bold=True) 
        
        # Colors
        label_color_bright = (160, 160, 160) 
        text_white = (240, 240, 240)
        
        header_h = 70 * s # Base estimation, real value from _draw_header
        padding = 15 * s
        
        sections = [
            ("NOVAS UNIDADES", data.get("new", [])),
            ("CANCELADAS", data.get("cancelled", [])),
            ("UPSELL", data.get("upsell", []))
        ]

        # === TITLE LOGIC ===
        try:
            date_str = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            date_str = data["date"]

        if report_type == "weekly" and "start_date" in data:
            try:
                start_str = datetime.strptime(data["start_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                start_str = data["start_date"]
            date_display = f"{start_str} a {date_str}"
            title_text = f"RELATÓRIO DE UNIDADES SEMANAL"
        else:
            date_display = f"{date_str}"
            title_text = f"RELATÓRIO DE UNIDADES DIÁRIO"

        # === PAGINATION LOGIC ===
        pages = []
        MAX_H = 1000 * s # Max page height Scaled
        
        # Start First Page
        current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
        current_draw = ImageDraw.Draw(current_img)
        
        # Header Page 1
        header_h = self._draw_header(current_draw, title_text, date_display)
        y = header_h + padding + (10 * s)
        current_h_used = y
        
        margin = self.padding
        card_w = self.width - 2 * margin

        for title, items in sections:
            section_count = len(items)
            display_title = f"{title} ({section_count})"
            
            # Check Title Space
            if current_h_used + (60 * s) > MAX_H - (60 * s): 
                 self._draw_footer(current_draw, MAX_H)
                 pages.append(current_img)
                 
                 current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                 current_draw = ImageDraw.Draw(current_img)
                 header_h = self._draw_header(current_draw, title_text, date_display)
                 y = header_h + padding + (10 * s)
                 current_h_used = y
            
            # Draw Title
            current_draw.text((margin, y), display_title, font=font_section, fill=(40, 40, 40))
            y += 28 * s
            current_draw.rectangle([(margin, y), (margin + (300 * s), y + (3 * s))], fill=self.accent_color)
            y += 25 * s
            current_h_used = y
            
            if not items:
                 empty_h = 80 * s
                 if current_h_used + empty_h > MAX_H - (60 * s):
                     self._draw_footer(current_draw, MAX_H)
                     pages.append(current_img)
                     current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                     current_draw = ImageDraw.Draw(current_img)
                     header_h = self._draw_header(current_draw, title_text, date_display)
                     y = header_h + padding + (10 * s)
                     current_h_used = y
                 
                 current_draw.rounded_rectangle([(margin, y), (margin + card_w, y + empty_h)], radius=int(6*s), fill=self.card_color)
                 
                 if title == "NOVAS UNIDADES":
                    msg = "Nenhuma nova unidade nesta data"
                 elif title == "CANCELADAS":
                    msg = "Nenhuma unidade cancelada nesta data"
                 elif title == "UPSELL":
                    msg = "Nenhum upsell nesta data"
                 else:
                    msg = "Não há dados"
                 
                 font_empty_bold = self._get_font(14, bold=False)
                 bbox = current_draw.textbbox((0, 0), msg, font=font_empty_bold)
                 text_w = bbox[2] - bbox[0]
                 text_h = bbox[3] - bbox[1]
                
                 current_draw.text((margin + (card_w - text_w)/2, y + (empty_h - text_h)/2 - (3 * s)), msg, font=font_empty_bold, fill=label_color_bright)
                 y += empty_h + (30 * s)
                 current_h_used = y

                 
            else:
                current_y = y 
                item_h = 160 * s  # Reduced height for 2 rows
                items_idx = 0
                
                while items_idx < len(items):
                    available_h = (MAX_H - (60 * s)) - current_y
                    can_fit = max(0, int(available_h // item_h))
                    
                    if can_fit == 0:
                        self._draw_footer(current_draw, MAX_H)
                        pages.append(current_img)
                        current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                        current_draw = ImageDraw.Draw(current_img)
                        header_h = self._draw_header(current_draw, title_text, date_display)
                        
                        y = header_h + padding + (10 * s)
                        current_y = y
                        continue
                    
                    chunk_items = items[items_idx : items_idx + can_fit]
                    
                    block_h = (len(chunk_items) * item_h) + (10 * s)
                    current_draw.rounded_rectangle([(margin, current_y), (margin + card_w, current_y + block_h)], radius=int(6*s), fill=self.card_color)
                    
                    inner_y = current_y + (20 * s)
                    for i, item in enumerate(chunk_items):
                        # Data extraction
                        val_cod = item.get("codigo", "")
                        nome = item.get("nome", "-") or "-" 
                        # UnidadesClient now returns "Unidade X - Partner Name" if possible
                        
                        cidade = item.get("cidade", "-") or "-"
                        uf = item.get("uf", "-") or "-"
                        
                        valor_aquisicao = item.get("valor", 0)
                        
                        raw_data = item.get("raw_data") or item.get("unit_raw_data") or {}
                        
                        modelo = item.get("modelo", "-") or "-"
                        tipo_franquia = item.get("tipo", "-") or "-"
                        
                        anos_contrato = item.get("anos_contrato", 0)
                        percentual_retencao = item.get("percentual_retencao", 0)

                        def fmt_moeda(val):
                            if isinstance(val, (int, float)):
                                return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            return str(val)
                        
                        # Display Name Logic matches client output
                        display_name = nome
                        if not "Unidade" in str(display_name) and val_cod:
                             display_name = f"Unidade {val_cod} - {display_name}"
                        
                        # Draw Name (Top Left)
                        px = margin + (25 * s)
                        rx = margin + card_w - (25 * s)
                        
                        current_draw.text((px, inner_y), display_name, font=self._get_font(20, bold=True), fill=self.light_gold)
                        
                        # Grid Layout Definition
                        # Row 1 Y
                        row1_y = inner_y + (40 * s)
                        row2_y = inner_y + (85 * s)
                        
                        # Cols X (3 Columns)
                        col1_x = px
                        col2_x = px + (210 * s)
                        col3_x = px + (410 * s)
                        
                        # Helper to draw label/value pair
                        def draw_field(x, y, label, value, val_color=text_white, is_money=False):
                            current_draw.text((x, y), label, font=font_label, fill=label_color_bright)
                            f_val = self._get_font(14, bold=False)
                            if is_money:
                                f_val = self._get_font(15, bold=True)
                                
                            current_draw.text((x, y + (14 * s)), str(value)[:28], font=f_val, fill=val_color)
                        
                        # Row 1: Cidade/UF | Modelo | Rede
                        draw_field(col1_x, row1_y, "CIDADE / UF", f"{cidade} - {uf}")
                        draw_field(col2_x, row1_y, "MODELO DE NEGÓCIO", modelo)
                        draw_field(col3_x, row1_y, "REDE DE DISTRIBUIÇÃO", tipo_franquia)
                        
                        # Row 2: Valor Aquisição | Tempo Contrato | % Retenção
                        draw_field(col1_x, row2_y, "VALOR AQUISIÇÃO", fmt_moeda(valor_aquisicao), val_color=text_white, is_money=True)
                        draw_field(col2_x, row2_y, "TEMPO DE CONTRATO", f"{anos_contrato} Anos" if anos_contrato else "-")
                        draw_field(col3_x, row2_y, "% RETENÇÃO", f"{percentual_retencao}%" if percentual_retencao else "-")

                        # Separator
                        if i < len(chunk_items) - 1:
                            sep_y = inner_y + item_h - (10 * s)
                            current_draw.line([(px, sep_y), (rx, sep_y)], fill=(60, 60, 60), width=int(1*s))
                        
                        inner_y += item_h
                    
                    current_y += block_h + (20 * s)
                    y = current_y
                    current_h_used = y
                    items_idx += can_fit
                    
        self._draw_footer(current_draw, MAX_H)
        pages.append(current_img)
        
        if pages:
            # Save first frame with append for others
            pages[0].save(output_path, save_all=True, append_images=pages[1:])
        
        return output_path
