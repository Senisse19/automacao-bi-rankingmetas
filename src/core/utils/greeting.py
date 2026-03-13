from datetime import datetime


def get_saudacao():
    """Retorna a saudação correta baseada no horário atual (bom dia, boa tarde, boa noite)."""
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        return "bom dia"
    elif hora_atual < 18:
        return "boa tarde"
    else:
        return "boa noite"
