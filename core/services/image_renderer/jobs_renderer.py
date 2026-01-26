from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
from .base_renderer import BaseRenderer

class JobsRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        # Background matched to Unidades (Light Grey)
        self.bg_color = (195, 195, 195)    
        self.card_color = (31, 31, 31)     # Card Background
        self.accent_color = (213, 174, 119) # Gold Accent
        self.scale = 4
        self.padding = 20 * self.scale
        self.width = 650 * self.scale
        
        # Area Mapping
        self.AREA_MAP = {
            "Tax": [1, 4, 5, 6, 10, 11, 37, 42, 14, 15], # Studio Fiscal, E-Fiscal, SF..., SCI, Audit
            "Corporate": [2, 3, 9, 13, 21, 33, 23, 39], # Law, Brokers, Corporate, M&A, Family Business, Management
            "Agro": [16],
            "Energy": [17],
            "Bank & Finance": [27, 32, 22, 18], # Rev Bancaria, Bank, Par, Economix
            "Education": [29],
            "Other": []
        }
        
    def _get_area(self, model_id):
        try:
            mid = int(model_id)
            for area, ids in self.AREA_MAP.items():
                if mid in ids:
                    return area
        except:
            pass
        return "Outros"

    def generate_jobs_report(self, data, report_title="RELATÓRIO DE JOBS", output_path="jobs_report.pdf"):
        s = self.scale
        
        # Prepare Data Grouped by Area
        grouped_data = {}
        # Expected data structure: list of job items
        # items should be dicts from runner transformation
        
        total_items = 0
        total_revenue = 0
        
        for item in data:
            mid = item.get("modelo_negocio")
            area = self._get_area(mid)
            if area not in grouped_data:
                grouped_data[area] = []
            grouped_data[area].append(item)
            total_items += 1
            # Try to sum revenue if available
            try:
                rev = float(item.get("honorarios_apos_rt") or 0)
                total_revenue += rev
            except: pass

        # Sort Areas: Tax First, then Corporate, then others
        area_order = ["Tax", "Corporate", "Agro", "Energy", "Bank & Finance", "Education", "Outros"]
        sections = []
        for a in area_order:
            if a in grouped_data and grouped_data[a]:
                sections.append((a.upper(), grouped_data[a]))

        # === PAGINATION LOGIC ===
        pages = []
        MAX_H = 1000 * s
        
        current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
        current_draw = ImageDraw.Draw(current_img)
        
        # Date is already in title
        header_h = self._draw_header(current_draw, report_title, "")
        
        y = header_h + (20 * s)
        margin = self.padding
        card_w = self.width - 2 * margin
        
        for area_name, items in sections:
            # Section Title
            font_section = self._get_font(18, bold=True)
            current_draw.text((margin, y), f"{area_name} ({len(items)})", font=font_section, fill=(40, 40, 40))
            y += 30 * s
            
            # Cards
            item_h = 160 * s # Height per card
            
            for item in items:
                # Check Page Break
                if y + item_h > MAX_H - (60 * s):
                    self._draw_footer(current_draw, MAX_H)
                    pages.append(current_img)
                    current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                    current_draw = ImageDraw.Draw(current_img)
                    header_h = self._draw_header(current_draw, report_title, "")
                    y = header_h + (20 * s)


                # Draw Card Background
                current_draw.rounded_rectangle([(margin, y), (margin + card_w, y + item_h - (10*s))], radius=int(6*s), fill=self.card_color)
                
                # Content
                inner_y = y + (20 * s)
                px = margin + (20 * s)
                
                # Job Title
                job_title = str(item.get("job") or "Sem Job ID")
                font_title = self._get_font(20, bold=True)
                current_draw.text((px, inner_y), f"JOB: {job_title}", font=font_title, fill=(255,255,255))
                
                inner_y += 35 * s
                
                # Grid
                font_lbl = self._get_font(10, bold=True)
                font_val = self._get_font(14, bold=False)
                col1 = px
                col2 = px + (200 * s)
                col3 = px + (400 * s)
                
                # Row 1
                # Cliente | Data
                client_id = item.get("cliente_id") or "NA"
                cnpj = item.get("cnpj") or "NA"
                draw_field(current_draw, col1, inner_y, "CLIENTE / CNPJ", f"{client_id} | {cnpj}", font_lbl, font_val, s)
                
                dt_cad = item.get("data_cadastro")
                if dt_cad:
                    try: dt_str = datetime.strptime(str(dt_cad)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except: dt_str = str(dt_cad)
                else: dt_str = "-"
                
                draw_field(current_draw, col2, inner_y, "DATA CADASTRO", dt_str, font_lbl, font_val, s)
                
                # Check financial for Tax
                if area_name == "TAX":
                    diag = item.get("estimativa_credito")
                    if diag and float(diag) > 0:
                         draw_field(current_draw, col3, inner_y, "DIAGNÓSTICO", fmt_money(float(diag)), font_lbl, font_val, s, is_money=True)
                
                # Helper to sanitize NULL strings
                def sanitize(val):
                    s = str(val).strip()
                    if s.upper() in ["NULL", "NONE", "NA", ""]: return "Não Informado"
                    return s

                # Row 2 (Commercial Rep instead of Revenue)
                inner_y += 50 * s
                raw_resp = item.get("responsavel_comercial")
                resp_comercial = sanitize(raw_resp)
                
                # Truncate if too long
                if len(resp_comercial) > 25: resp_comercial = resp_comercial[:25] + "..."
                
                draw_field(current_draw, col1, inner_y, "RESPONSÁVEL COMERCIAL", resp_comercial, font_lbl, font_val, s)
                     
                divisao = sanitize(item.get("job_divisao"))
                draw_field(current_draw, col2, inner_y, "DIVISÃO", divisao, font_lbl, font_val, s)

                y += item_h
                
            y += 20 * s # Space between sections
            
        self._draw_footer(current_draw, MAX_H)
        pages.append(current_img)
        
        if pages:
            pages[0].save(output_path, save_all=True, append_images=pages[1:])
        return output_path

def draw_field(draw, x, y, label, value, f_lbl, f_val, s, is_money=False):
    draw.text((x, y), label, font=f_lbl, fill=(160,160,160))
    val_color = (255,255,255)
    if is_money: val_color = (133, 187, 101) # Green
    draw.text((x, y + (15*s)), str(value), font=f_val, fill=val_color)

def fmt_money(val):
    if val is None: return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
