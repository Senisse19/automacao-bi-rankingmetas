from run_unidades import UnidadesAutomation

if __name__ == "__main__":
    print("=== Gerando Relatório Diário de Unidades (SEM ENVIO) ===")
    automation = UnidadesAutomation()
    # Execute only daily, no weekly, and DO NOT SEND (generate_only=True)
    automation.process_reports(daily=True, weekly=False, generate_only=True)
    print("\n[OK] Processo finalizado.")
