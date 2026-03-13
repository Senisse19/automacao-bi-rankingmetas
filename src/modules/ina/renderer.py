"""
Renderizador do Painel INA (Inadimplência).
Exibe 7 cards de KPIs + Top 10 de clientes inadimplentes até 90 dias.
"""

from datetime import datetime

from PIL import Image, ImageDraw

from src.core.base.base_renderer import BaseRenderer


class InaRenderer(BaseRenderer):
    """Renderizador do Painel INA."""

    # Mapeamento de campos Power BI → labels de exibição no card
    CARD_LABELS = [
        ("Card_Vencendo_Hoje", "VENCENDO HOJE"),
        ("Card_Inadimplencia_Ate_2_Dias", "CONCILIAÇÃO (D+2)"),
        ("Card_Inadimplencia_3_Mais_Dias", "INADIMPLÊNCIA (D+3)"),
        ("Card_QtdAtraso", "QUANTIDADE TÍTULOS"),
        ("Card_Media_Atraso",            "MÉDIA DIAS EM ATRASO"),
        ("Card_INTERCOMPANY",            "INADIMPLÊNCIA INTERCOMPANY"),
        ("Card_Inadimplencia_TOTAL",     "INADIMPLÊNCIA TOTAL"),
    ]

    def generate_image(self, kpis, top10, output_path="ina_report_global.png"):
        """
        Gera a imagem do relatório INA.
        kpis: dict {campo_pbi: valor_formatado}
        top10: list[dict] com nome_fantasia, Valor e Dias_Atraso
        """
        self.width = 800

        # Layout: 7 cards em 2 colunas (3 linhas completas + 1 card centralizado)
        # Altura: Header(90) + KPIs(290) + Gap(20) + Tabela + Footer(50)
        num_items = len(top10) if top10 else 0
        table_height = 70 + (num_items * 45) + 50
        kpi_section_h = 290  # 4 linhas × 65px + gaps

        total_height = 90 + kpi_section_h + 30 + table_height + 60

        img = Image.new("RGB", (self.width, total_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Data de referência para exibição no cabeçalho (Hoje D-0)
        data_posicao = datetime.now().strftime("%d/%m/%Y")

        # 1. Cabeçalho
        sub_text = f"Posição: Hoje ({data_posicao})"
        header_h = self._draw_header(draw, "PAINEL DE INADIMPLÊNCIA", sub_text)

        y = header_h + 20

        # 2. Cards de KPI
        self._draw_kpi_cards(draw, y, kpis)
        y += kpi_section_h + 30

        # 3. Tabela Top 10
        self._draw_top10_table(draw, y, top10)

        # 4. Rodapé
        self._draw_footer(draw, total_height)

        img.save(output_path)
        return output_path

    def _draw_kpi_cards(self, draw, start_y, kpis):
        """
        Desenha os 7 cards em grid de 2 colunas.
        Layout: 3 linhas de 2 + 1 card centralizado na última linha.
        """
        margin = 30
        gap = 15
        card_h = 65
        card_w = (self.width - 2 * margin - gap) / 2

        font_label = self._get_font(11, bold=True)
        font_value = self._get_font(17, bold=True)

        for i, (campo, label) in enumerate(self.CARD_LABELS):
            valor = kpis.get(campo, "-")
            is_last = i == len(self.CARD_LABELS) - 1  # 7° card centralizado

            if is_last:
                # Último card ocupa toda a largura (com margem lateral)
                x = margin
                y = start_y + (i // 2) * (card_h + gap)
                w = self.width - 2 * margin
            else:
                col = i % 2
                row = i // 2
                x = margin + col * (card_w + gap)
                y = start_y + row * (card_h + gap)
                w = card_w

            # Destaque dourado nos cards principais (Vencendo Hoje, Intercompany e Total)
            is_destaque = i in (0, 5, len(self.CARD_LABELS) - 1)
            outline_color = self.accent_color if is_destaque else self.card_color

            draw.rounded_rectangle(
                [(x, y), (x + w, y + card_h)],
                radius=10,
                fill=self.card_color,
                outline=outline_color,
                width=2 if is_destaque else 0,
            )

            # Texto do label (suporta \n)
            label_fill = self.accent_color if is_destaque else self.muted_text
            draw.text((x + 15, y + 10), label, font=font_label, fill=label_fill, spacing=2)
            # Valor
            val_str = str(valor) if valor is not None else "-"
            draw.text((x + 15, y + 33), val_str, font=font_value, fill=self.text_color)

    def _draw_top10_table(self, draw, start_y, top10):
        """Desenha a tabela Top 10 de inadimplentes até 90 dias."""
        margin = 30
        num_rows = len(top10) if top10 else 1
        row_h = 45
        header_h_space = 60
        table_h = header_h_space + (num_rows * row_h) + 50

        # Card de fundo escuro
        card_bg = (15, 15, 15)
        draw.rounded_rectangle(
            [(margin, start_y), (self.width - margin, start_y + table_h)],
            radius=15,
            fill=card_bg,
            outline=(40, 40, 40),
            width=1,
        )

        inner_x = margin + 20
        current_y = start_y + 20

        draw.text(
            (inner_x, current_y),
            "TOP 10 INADIMPLÊNCIA ATÉ 90 DIAS",
            font=self._get_font(18, bold=True),
            fill=self.accent_color,
        )

        # Cabeçalho das colunas
        header_y = current_y + 40
        col_rank_x = inner_x
        col_name_x = inner_x + 40
        col_days_x = self.width - margin - 200
        col_val_x = self.width - margin - 30

        font_head = self._get_font(12, bold=True)
        draw.text((col_rank_x, header_y), "#", font=font_head, fill=(255, 255, 255))
        draw.text((col_name_x, header_y), "CLIENTE", font=font_head, fill=(255, 255, 255))
        draw.text((col_days_x, header_y), "DIAS", font=font_head, fill=(255, 255, 255), anchor="mt")
        draw.text((col_val_x, header_y), "VALOR", font=font_head, fill=(255, 255, 255), anchor="rt")

        # Linha separadora
        line_y = header_y + 25
        draw.line([(inner_x, line_y), (self.width - margin - 20, line_y)], fill=(60, 60, 60), width=1)

        row_start_y = line_y + 15
        font_row = self._get_font(14)
        font_bold = self._get_font(14, bold=True)

        card_left = margin + 2
        card_right = self.width - margin - 2
        card_bottom = start_y + table_h - 2

        if not top10:
            draw.text(
                (self.width // 2, row_start_y + 20),
                "Nenhum dado encontrado.",
                font=font_row,
                fill=self.muted_text,
                anchor="mm",
            )
            return

        for i, item in enumerate(top10):
            row_y = row_start_y + (i * row_h)
            cy = row_y + row_h // 2  # centro vertical

            # Listagem zebra (linhas alternadas)
            if i % 2 == 1:
                is_last_row = i == len(top10) - 1
                row_bottom = min(row_y + row_h, card_bottom)
                if is_last_row:
                    draw.rounded_rectangle(
                        [(card_left, row_y), (card_right, row_bottom)],
                        radius=15,
                        fill=(28, 28, 28),
                    )
                    draw.rectangle(
                        [(card_left, row_y), (card_right, row_y + 15)],
                        fill=(28, 28, 28),
                    )
                else:
                    draw.rectangle([(card_left, row_y), (card_right, row_bottom)], fill=(28, 28, 28))

            # Dados do item
            import html as _html

            nome = item.get("nome_fantasia", "Desconhecido")
            nome = _html.unescape(str(nome))
            if len(nome) > 32:
                nome = nome[:29] + "..."

            dias_raw = item.get("Dias_Atraso")
            if dias_raw is not None:
                try:
                    dias_str = f"{int(float(dias_raw))} dias"
                except Exception:
                    dias_str = str(dias_raw)
            else:
                dias_str = "-"

            val_raw = item.get("Valor")
            if isinstance(val_raw, (int, float)):
                val_str = f"R$ {val_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                val_str = str(val_raw) if val_raw else "-"

            draw.text((col_rank_x, cy), f"{i + 1}", font=font_bold, fill=self.accent_color, anchor="lm")
            draw.text((col_name_x, cy), nome, font=font_row, fill=(220, 220, 220), anchor="lm")
            draw.text((col_days_x, cy), dias_str, font=font_row, fill=(200, 200, 200), anchor="mm")
            draw.text((col_val_x, cy), val_str, font=font_bold, fill=(255, 255, 255), anchor="rm")
