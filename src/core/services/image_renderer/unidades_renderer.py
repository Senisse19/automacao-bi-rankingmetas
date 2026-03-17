from datetime import datetime

from PIL import Image, ImageDraw

from .base_renderer import BaseRenderer


class UnidadesRenderer(BaseRenderer):
    """
    Renderizador para relatórios de Unidades.
    Layout: 3 cards KPI + tabelas de Novas Unidades e Mortalidade.
    """

    def __init__(self):
        super().__init__()
        self.accent_color = (213, 174, 119)
        self.gold_color = (213, 174, 119)
        self.scale = 1

    def generate_unidades_reports(self, data, report_type="daily", output_path="unidades_report.png"):
        """
        Gera relatório de Unidades com layout de tabela (estilo INA).
        """
        self.width = 950
        margin = 30
        padding = 18

        summary = data.get("summary", {})
        new_units = data.get("new", [])
        cancelled_units = data.get("cancelled", [])

        # Título / data
        try:
            date_str = datetime.strptime(data["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except (ValueError, KeyError):
            date_str = data.get("date", datetime.now().strftime("%d/%m/%Y"))

        if report_type == "weekly" and "start_date" in data:
            try:
                start_str = datetime.strptime(data["start_date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                start_str = data["start_date"]
            date_display = f"{start_str} a {date_str}"
            title_text = "RELATÓRIO DE UNIDADES SEMANAL"
        else:
            date_display = date_str
            title_text = "RELATÓRIO DE UNIDADES DIÁRIO"

        # KPIs
        novas = summary.get("novas_unidades", len(new_units))
        pagantes = summary.get("unidades_pagantes", 0)
        mortalidade = summary.get("unidades_inativadas", len(cancelled_units))

        # Constantes de layout
        header_h = 70
        kpi_h = 90
        section_title_h = 88
        table_hdr_h = 44
        row_h = 38

        def table_block_h(n_rows):
            return table_hdr_h + (max(n_rows, 1) * row_h) + 20

        total_h = (
            header_h + padding
            + kpi_h + padding * 2
            + section_title_h + table_block_h(len(new_units)) + padding * 2
            + section_title_h + table_block_h(len(cancelled_units)) + padding * 2
            + 50  # footer
        )

        img = Image.new("RGB", (self.width, total_h), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 1. Cabeçalho (usa _draw_header da base: fundo cinza + logo GS com fonte serif)
        y = self._draw_header(draw, title_text, date_display) + padding

        # 2. Cards KPI
        kpis = [
            ("NOVAS UNIDADES", novas),
            ("UNIDADES PAGANTES", pagantes),
            ("MORTALIDADE", mortalidade),
        ]
        gap = 15
        kpi_card_w = (self.width - 2 * margin - (len(kpis) - 1) * gap) / len(kpis)

        font_kpi_label = self._get_font(11, bold=True)
        font_kpi_value = self._get_font(30, bold=True)

        for i, (label, val) in enumerate(kpis):
            x = margin + i * (kpi_card_w + gap)
            draw.rounded_rectangle(
                [(x, y), (x + kpi_card_w, y + kpi_h)],
                radius=10,
                fill=self.card_color,
                outline=self.accent_color,
                width=2,
            )
            lb = draw.textbbox((0, 0), label, font=font_kpi_label)
            lw = lb[2] - lb[0]
            draw.text((x + (kpi_card_w - lw) / 2, y + 12), label, font=font_kpi_label, fill=self.muted_text)

            vs = str(val)
            vb = draw.textbbox((0, 0), vs, font=font_kpi_value)
            vw = vb[2] - vb[0]
            draw.text((x + (kpi_card_w - vw) / 2, y + 36), vs, font=font_kpi_value, fill=self.accent_color)

        y += kpi_h + padding * 2

        # 3. Seção Novas Unidades
        y = self._draw_table_section(
            draw, y, "NOVAS UNIDADES", novas, new_units,
            row_h, table_hdr_h, section_title_h, margin, padding,
        )

        # 4. Seção Mortalidade
        self._draw_table_section(
            draw, y, "MORTALIDADE", mortalidade, cancelled_units,
            row_h, table_hdr_h, section_title_h, margin, padding,
        )

        # 5. Rodapé
        self._draw_footer(draw, total_h)

        img.save(output_path, "PNG")
        return output_path

    def _draw_table_section(self, draw, y, title, count, units, row_h, table_hdr_h, section_title_h, margin, padding):
        """Desenha título da seção com contagem + tabela de unidades."""
        inner_w = self.width - 2 * margin
        inner_x = margin + 15

        font_title = self._get_font(14, bold=True)
        font_count = self._get_font(34, bold=True)
        font_head = self._get_font(10, bold=True)
        font_row = self._get_font(12)
        font_row_bold = self._get_font(12, bold=True)

        # Título da seção (texto escuro sobre fundo cinza claro)
        draw.text((margin, y), title, font=font_title, fill=self.card_color)
        y += 22
        draw.text((margin, y), str(count), font=font_count, fill=self.card_color)
        y += section_title_h - 22

        # Colunas: (label, x_offset, width, align)
        cols = [
            ("NOME DA UNIDADE", 0,   280, "left"),
            ("UF",             292,   45, "center"),
            ("NOME DO MODELO", 349,  175, "left"),
            ("UNIDADE",        536,   70, "center"),
            ("VALOR",          618,  155, "right"),
            ("ANOS",           785,   60, "center"),
        ]

        # Card de fundo
        num_rows = max(len(units), 1)
        total_table_h = table_hdr_h + (num_rows * row_h) + 20

        draw.rounded_rectangle(
            [(margin, y), (margin + inner_w, y + total_table_h)],
            radius=12,
            fill=self.card_color,
        )

        # Cabeçalho da tabela
        hdr_y = y + 14
        for label, offset, width, align in cols:
            cx = inner_x + offset
            bbox = draw.textbbox((0, 0), label, font=font_head)
            tw = bbox[2] - bbox[0]
            if align == "center":
                tx = cx + (width - tw) / 2
            elif align == "right":
                tx = cx + width - tw
            else:
                tx = cx
            draw.text((tx, hdr_y), label, font=font_head, fill=self.accent_color)

        # Linha separadora
        sep_y = y + table_hdr_h - 8
        draw.line(
            [(margin + 10, sep_y), (margin + inner_w - 10, sep_y)],
            fill=self.accent_color,
            width=1,
        )

        if not units:
            msg = "Nenhum registro encontrado"
            bbox = draw.textbbox((0, 0), msg, font=font_row)
            mw = bbox[2] - bbox[0]
            draw.text(
                (margin + (inner_w - mw) / 2, sep_y + 15),
                msg, font=font_row, fill=self.muted_text,
            )
        else:
            def fmt_money(val):
                if not val and val != 0:
                    return "R$ 0,00"
                try:
                    return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except (ValueError, TypeError):
                    return str(val)

            def trunc(text, n: int = 38) -> str:
                s = str(text) if text else ""
                limit = n - 2
                return s[:limit] + ".." if len(s) > n else s

            for i, item in enumerate(units):
                row_y = y + table_hdr_h + (i * row_h)
                cy = row_y + row_h // 2

                # Zebra striping
                if i % 2 == 1:
                    draw.rectangle(
                        [(margin + 2, row_y), (margin + inner_w - 2, row_y + row_h)],
                        fill=(42, 42, 42),
                    )

                def _str(v) -> str:
                    """Retorna '-' para valores vazios/nulos do Power BI."""
                    if v is None:
                        return "-"
                    s = str(v).strip()
                    return s if s else "-"

                nome_raw = item.get("Nome", item.get("nome"))
                nome_s = str(nome_raw).strip() if nome_raw is not None else ""
                nome = trunc(nome_s if nome_s else "- Sem Cadastro -", 38)

                uf = _str(item.get("UF", item.get("uf")))
                modelo_raw = item.get("Modelo", item.get("modelo"))
                modelo = trunc(_str(modelo_raw), 24)
                codigo = _str(item.get("Codigo", item.get("codigo")))
                valor = fmt_money(item.get("Valor", item.get("valor", 0)))
                anos = _str(item.get("Anos", item.get("anos_contrato", item.get("anos"))))

                row_vals = [
                    (nome,   "left",   font_row_bold, self.accent_color),
                    (uf,     "center", font_row,      self.text_color),
                    (modelo, "left",   font_row,      self.text_color),
                    (codigo, "center", font_row,      self.text_color),
                    (valor,  "right",  font_row,      self.text_color),
                    (anos,   "center", font_row,      self.text_color),
                ]

                for (text, align, font, color), (_, offset, width, _) in zip(row_vals, cols):
                    cx = inner_x + offset
                    bbox = draw.textbbox((0, 0), text, font=font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]

                    if align == "center":
                        tx = cx + (width - tw) / 2
                    elif align == "right":
                        tx = cx + width - tw
                    else:
                        tx = cx

                    ty = cy - th // 2
                    draw.text((tx, ty), text, font=font, fill=color)

        return y + total_table_h + padding * 2
