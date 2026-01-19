from PIL import Image, ImageDraw
from datetime import datetime
from .base_renderer import BaseRenderer

class UnidadesRenderer(BaseRenderer):
    """
    Renderizador para relatórios de Unidades (Nexus).
    """
    def __init__(self):
        super().__init__()
        print(f"DEBUG: UnidadesRenderer loaded from: {__file__}")
        self.light_gold = (235, 215, 140) # Dourado Claro

    def _truncate_text(self, draw, text, font, max_width):
        """Truncates text to fit within max_width."""
        if not text:
            return ""
        current_text = text
        if draw.textlength(current_text, font=font) <= max_width:
            return current_text
        
        while draw.textlength(current_text + "...", font=font) > max_width and len(current_text) > 0:
            current_text = current_text[:-1]
        return current_text + "..."

    def _get_wrapped_lines(self, draw, text, font, max_width):
        """Splits text into lines that fit within max_width."""
        if not text:
            return []
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if draw.textlength(test_line, font=font) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word longer than width, force split or just keep it (overflow)
                    # For simplicity, we keep it to avoid infinite loop or complex char splitting
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

    def _draw_text_autofit(self, draw, xy, text, max_width, initial_size=16, color=(0,0,0), font_func=None):
        pass # Removed/Deprecated


    def generate_unidades_reports(self, data, report_type="daily", output_path="unidades_report.png"):
        """
        Gera relatório de Novas Unidades e Cancelamentos (Layout Dark Premium).
        Suporta modo Diário e Semanal.
        """
        self.width = 650 
        
        # Estilos Fontes
        font_header_main = self._get_font(24, bold=True)
        font_section = self._get_font(18, bold=True)
        font_name = self._get_font(16, bold=True)
        
        font_label = self._get_font(12, bold=True)
        font_value = self._get_font(16, bold=True)
        font_money_label = self._get_font(12, bold=True) 
        font_money = self._get_font(18, bold=True)
        font_small = self._get_font(13)
        font_details = self._get_font(14)
        
        label_color_bright = (180, 180, 180) 
        
        header_h = 70
        padding = 15
        item_h = 200
        
        sections = [
            ("NOVAS UNIDADES", data.get("new", [])),
            ("CANCELADAS", data.get("cancelled", [])),
            ("UPSELL", data.get("upsell", []))
        ]
        
        h = header_h + padding + 10
        
        for title, items in sections:
            h += 40 
            
            if not items:
                h += 80 
            else:
                h += (len(items) * item_h) + 20
            
            h += 20 
            
        h += 60 # Footer
            
        img = Image.new("RGB", (self.width, h), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # === HEADER ===
        try:
            date_str = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            date_str = data["date"] # Fallback if format is different

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
            
        header_h = self._draw_header(draw, title_text, date_display)
        
        y = header_h + padding + 10
        
        # === CONTENT ===
        margin = self.padding
        card_w = self.width - 2 * margin
        
        for title, items in sections:
            section_count = len(items)
            display_title = f"{title} ({section_count})"
            
            draw.text((margin, y), display_title, font=font_section, fill=(40, 40, 40))
            y += 25
            
            draw.line([(margin, y), (margin + 200, y)], fill=self.accent_color, width=1)
            y += 15
            
            if not items:
                empty_h = 60
                draw.rounded_rectangle([(margin, y), (margin + card_w, y + empty_h)], radius=8, fill=self.card_color)
                
                if title == "NOVAS UNIDADES":
                    msg = "Nenhuma nova unidade nesta data"
                elif title == "CANCELADAS":
                    msg = "Nenhuma unidade cancelada nesta data"
                elif title == "UPSELL":
                    msg = "Nenhum upsell nesta data"
                else:
                    msg = "Não há dados"
                font_empty_bold = self._get_font(14, bold=True)
                bbox = draw.textbbox((0, 0), msg, font=font_empty_bold)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                
                draw.text((margin + (card_w - text_w)/2, y + (empty_h - text_h)/2 - 2), msg, font=font_empty_bold, fill=label_color_bright)
                y += empty_h + 20
            else:
                # Pre-calculate HEIGHTS for dynamic sizing
                # The block height needs to be sum of all item heights
                # We can draw and check constraints, unrolling the loop slightly to calculate layout first?
                # Or we can just draw on the fly but we need the background rectangle first.
                
                # First pass: Calculate total height needed
                total_content_height = 0
                item_heights = []
                
                for item in items:
                    modelo = item.get("modelo", "-") or "-"
                    rede_distribuicao = item.get("rede_distribuicao", "-") or "-"
                    rd_display = f"Tipo {rede_distribuicao}" if rede_distribuicao != "-" else "-"
                    
                    # Calculate wrapped lines
                    lines_modelo = self._get_wrapped_lines(draw, modelo, font_value, 240)
                    lines_rede = self._get_wrapped_lines(draw, rd_display, font_value, 240)
                    
                    # Base height for "City/Val" row + spacing
                    # Structure:
                    # Name row (~35px)
                    # City/Val Row (~50px)
                    # Modelo/Rede Row (Variable)
                    # Footer Row (~30px)
                    # Padding (20px)
                    
                    max_lines = max(len(lines_modelo), len(lines_rede), 1)
                    text_height = max_lines * 18 # approx line height
                    
                    # 10 (top pad) + 35 (name) + 50 (row1) + text_height + 50 (footer) + 20 (bottom pad)
                    computed_h = 10 + 35 + 50 + text_height + 40 + 20 
                    item_heights.append({
                        "h": computed_h, 
                        "lines_modelo": lines_modelo,
                        "lines_rede": lines_rede
                    })
                    total_content_height += computed_h
                
                # Draw Background Block
                draw.rounded_rectangle([(margin, y), (margin + card_w, y + total_content_height + 10)], radius=8, fill=self.card_color)
                
                current_y = y + 10 
                
                for i, item in enumerate(items):
                    layout_info = item_heights[i]
                    this_h = layout_info["h"]
                    
                    codigo = item.get("codigo", "")
                    nome = item.get("nome", "-") or "-"
                    cidade = item.get("cidade", "-") or "-"
                    uf = item.get("uf", "-") or "-"
                    
                    valor_aquisicao = item.get("valor", 0)
                    retencao = item.get("percentual_retencao", 0)
                    anos = item.get("anos_contrato", 0)
                    
                    def fmt_moeda(val):
                        if isinstance(val, (int, float)):
                            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        return str(val)
                    
                    if str(codigo) in nome and "Unidade" in nome:
                         display_name = f"{nome}"
                    elif codigo:
                         display_name = f"Unid: {codigo} - {nome}"
                    else:
                         display_name = nome
                    
                    # 1. Name
                    draw.text((margin + 20, current_y + 10), display_name[:50], font=self._get_font(18, bold=True), fill=self.light_gold)
                    
                    col1_x = margin + 20
                    col2_x = margin + 280
                    
                    # 2. Row 1: City | Value
                    row1_y = current_y + 45
                    draw.text((col1_x, row1_y), "CIDADE / UF", font=font_label, fill=label_color_bright)
                    draw.text((col1_x, row1_y + 18), f"{cidade} - {uf}", font=font_value, fill=self.text_color)
                    
                    draw.text((col2_x, row1_y), "VALOR AQUISIÇÃO", font=font_money_label, fill=label_color_bright)
                    draw.text((col2_x, row1_y + 18), fmt_moeda(valor_aquisicao), font=font_money, fill=self.text_color)
                    
                    # 3. Row 2: Modelo | Rede (Variable Height)
                    row2_y = current_y + 95
                    
                    draw.text((col1_x, row2_y), "MODELO", font=font_label, fill=label_color_bright)
                    # Draw Wrapped Modelo
                    dy = row2_y + 18
                    for line in layout_info["lines_modelo"]:
                        draw.text((col1_x, dy), line, font=font_value, fill=self.text_color)
                        dy += 18
                        
                    draw.text((col2_x, row2_y), "REDE DE DISTRIBUIÇÃO", font=font_label, fill=label_color_bright)
                    # Draw Wrapped Rede
                    dy = row2_y + 18
                     
                    draw.text((col2_x, row2_y), "REDE DE DISTRIBUIÇÃO", font=font_label, fill=label_color_bright)
                    
                    # Format: Tipo {rede_distribuicao}
                    rd_display = f"Tipo {rede_distribuicao}" if rede_distribuicao != "-" else "-"
                    
                    for line in layout_info["lines_rede"]:
                        draw.text((col2_x, dy), line, font=font_value, fill=self.text_color)
                        dy += 18
                        
                    # 4. Footer Row (Pushed down by max lines)
                    max_lines = max(len(layout_info["lines_modelo"]), len(layout_info["lines_rede"]), 1)
                    # row2_y + 18 (first line) + (max_lines * 18) + padding
                    row3_y = row2_y + 18 + (max_lines * 18) + 15
                    
                    line_detail = f"Tempo de Contrato: {anos} anos   •   Retenção: {retencao}%"
                    draw.text((col1_x, row3_y), line_detail, font=self._get_font(14, bold=True), fill=(180, 180, 180))
                    
                    if i < len(items) - 1:
                        sep_y = current_y + this_h
                        draw.line([(margin + 10, sep_y), (margin + card_w - 10, sep_y)], fill=(50, 50, 50), width=1)
                    
                    current_y += this_h
                
                y += total_content_height + 20
            
            y += 20 
            
            y += 20 
            
        self._draw_footer(draw, h)
        
        img.save(output_path, "PNG")
        return output_path
