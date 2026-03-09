from datetime import datetime, timedelta


def get_periodo_semanal():
    """Retorna a data de sexta-feira passada até ontem, formatada."""
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    dias_para_sexta = (hoje.weekday() - 4) % 7
    if dias_para_sexta == 0:
        dias_para_sexta = 7
    ultima_sexta = hoje - timedelta(days=dias_para_sexta)
    return f"{ultima_sexta.strftime('%d/%m')} a {ontem.strftime('%d/%m')}"
