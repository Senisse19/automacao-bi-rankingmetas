from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
from .base_renderer import BaseRenderer

class JobsRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        self.bg_color = (195, 195, 195)    
        self.card_color = (31, 31, 31)
        self.accent_color = (213, 174, 119)
        self.scale = 4
        self.padding = 20 * self.scale
        self.width = 650 * self.scale
        
        self.AREA_MAP = {
            "Tax": [1, 4, 5, 6, 10, 11, 37, 42, 14, 15],
            "Corporate": [2, 3, 9, 13, 21, 33, 23, 39],
            "Agro": [16],
            "Energy": [17],
            "Bank & Finance": [27, 32, 22, 18],
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

    def generate_jobs_report(self, new_jobs, cancelled_jobs, report_title="RELATÓRIO DE JOBS", output_path="jobs_report.pdf"):
        s = self.scale
        MAX_H = 1000 * s
        
        pages = []
        
        # Initialize First Page
        current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
        current_draw = ImageDraw.Draw(current_img)
        
        # Main Header
        header_h = self._draw_header(current_draw, report_title, "")
        y = header_h + (30 * s)
        
        # Helper to process datasets
        def process_dataset(data):
            grouped = {}
            for item in data:
                mid = item.get("modelo_negocio")
                area = self._get_area(mid)
                if area not in grouped: grouped[area] = []
                grouped[area].append(item)
            
            area_order = ["Tax", "Corporate", "Agro", "Energy", "Bank & Finance", "Education", "Outros"]
            sections = []
            for a in area_order:
                if a in grouped and grouped[a]:
                    sections.append((a.upper(), grouped[a]))
            return sections

        # DATASETS
        # 1. New Jobs
        # 2. Cancelled Jobs
        
        datasets = []
        if new_jobs and len(new_jobs) > 0:
            datasets.append({
                "title": "NOVOS JOBS",
                "color": (74, 222, 128), # Green
                "side_bar": (74, 222, 128),
                "data": process_dataset(new_jobs)
            })
            
        if cancelled_jobs and len(cancelled_jobs) > 0:
            datasets.append({
                "title": "JOBS CANCELADOS",
                "color": (248, 113, 113), # Red
                "side_bar": (248, 113, 113),
                "data": process_dataset(cancelled_jobs)
            })

        margin = self.padding
        card_w = self.width - 2 * margin

        for ds in datasets:
            # SECTION HEADER (New Page if needed? No, continuous flow preferred unless almost full)
            if y > MAX_H - (150 * s):
                self._draw_footer(current_draw, MAX_H)
                pages.append(current_img)
                current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                current_draw = ImageDraw.Draw(current_img)
                header_h = self._draw_header(current_draw, report_title, "Continuação")
                y = header_h + (30 * s)

            # Draw Big Title for "NOVOS JOBS" / "CANCELADOS"
            font_ds = self._get_font(24, bold=True)
            # Box for title
            # current_draw.rectangle([(margin, y), (margin + card_w, y + 60*s)], fill=self.card_color)
            current_draw.text((margin, y), ds["title"], font=font_ds, fill=(40,40,40)) 
            # Underline
            current_draw.line([(margin, y + 35*s), (margin + 300*s, y + 35*s)], fill=ds["color"], width=int(3*s))
            y += 60 * s

            for area_name, items in ds["data"]:
                # Area Subheader
                if y > MAX_H - (100 * s):
                    self._draw_footer(current_draw, MAX_H)
                    pages.append(current_img)
                    current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                    current_draw = ImageDraw.Draw(current_img)
                    header_h = self._draw_header(current_draw, report_title, "Continuação")
                    y = header_h + (30 * s)
                
                font_sec = self._get_font(16, bold=True)
                current_draw.text((margin, y), f"{area_name} ({len(items)})", font=font_sec, fill=(80, 80, 80))
                y += 25 * s
                
                # Cards
                item_h = 160 * s
                
                for item in items:
                    if y + item_h > MAX_H - (60 * s):
                        self._draw_footer(current_draw, MAX_H)
                        pages.append(current_img)
                        current_img = Image.new("RGB", (self.width, MAX_H), self.bg_color)
                        current_draw = ImageDraw.Draw(current_img)
                        header_h = self._draw_header(current_draw, report_title, "Continuação")
                        y = header_h + (30 * s)

                    # Card Background
                    current_draw.rounded_rectangle([(margin, y), (margin + card_w, y + item_h - (10*s))], radius=int(6*s), fill=self.card_color)
                    
                    # Side Bar Color
                    current_draw.rounded_rectangle([(margin, y), (margin + (6*s), y + item_h - (10*s))], radius=int(6*s), fill=ds["side_bar"])
                    # Fix rounded corners on left side by overdrawing? No need for perfection.
                    
                    # Content
                    inner_y = y + (20 * s)
                    px = margin + (25 * s) # Shifted for sidebar
                    
                    # Job Title
                    job_title = str(item.get("job") or item.get("id") or "Sem ID")
                    font_title = self._get_font(20, bold=True)
                    current_draw.text((px, inner_y), f"JOB: {job_title}", font=font_title, fill=(255,255,255))
                    
                    inner_y += 35 * s
                    
                    font_lbl = self._get_font(10, bold=True)
                    font_val = self._get_font(14, bold=False)
                    col1 = px
                    col2 = px + (200 * s)
                    col3 = px + (400 * s)
                    
                    # Row 1
                    client_id = item.get("cliente_id") or "NA"
                    cnpj = item.get("cnpj") or "NA"
                    draw_field(current_draw, col1, inner_y, "CLIENTE / CNPJ", f"{client_id} | {cnpj}", font_lbl, font_val, s)
                    
                    # Date Logic (Cadastro vs Cancelamento)
                    if ds["title"] == "JOBS CANCELADOS":
                        dt_raw = item.get("data_cancelamento")
                        lbl_date = "DATA CANCELAMENTO"
                    else:
                        dt_raw = item.get("data_cadastro")
                        lbl_date = "DATA CADASTRO"
                        
                    if dt_raw:
                        try: dt_str = datetime.strptime(str(dt_raw)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                        except: dt_str = str(dt_raw)
                    else: dt_str = "-"
                    
                    draw_field(current_draw, col2, inner_y, lbl_date, dt_str, font_lbl, font_val, s)
                    
                     # Row 2 (Commercial Rep instead of Revenue)
                    inner_y_row2 = inner_y + (50 * s)
                    
                    def sanitize(val):
                        s = str(val).strip()
                        if s.upper() in ["NULL", "NONE", "NA", ""]: return "Não Informado"
                        return s
                    
                    raw_resp = item.get("responsavel_comercial")
                    resp_comercial = sanitize(raw_resp)
                    if len(resp_comercial) > 25: resp_comercial = resp_comercial[:25] + "..."
                    draw_field(current_draw, col1, inner_y_row2, "RESPONSÁVEL COMERCIAL", resp_comercial, font_lbl, font_val, s)
                    
                    divisao = sanitize(item.get("job_divisao"))
                    draw_field(current_draw, col2, inner_y_row2, "DIVISÃO", divisao, font_lbl, font_val, s)

                    y += item_h
                
                y += 20 * s # Space between areas
            
            y += 40 * s # Space between Datasets

        self._draw_footer(current_draw, MAX_H)
        pages.append(current_img)
        
        if pages:
            pages[0].save(output_path, save_all=True, append_images=pages[1:])
        return output_path

def draw_field(draw, x, y, label, value, f_lbl, f_val, s, is_money=False):
    draw.text((x, y), label, font=f_lbl, fill=(160,160,160))
    val_color = (255,255,255)
    if is_money: val_color = (133, 187, 101) 
    draw.text((x, y + (15*s)), str(value), font=f_val, fill=val_color)

def fmt_money(val):
    if val is None: return "R$ 0,00"
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
