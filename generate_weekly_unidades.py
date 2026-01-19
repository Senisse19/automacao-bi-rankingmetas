from run_unidades import UnidadesAutomation

if __name__ == "__main__":
    print("=== Gerando Relatório Semanal de Unidades (SEM ENVIO) ===")
    automation = UnidadesAutomation()
    # Execute only weekly, no daily, and DO NOT SEND (generate_only=True)
    automation.process_reports(daily=False, weekly=True, force_weekly=True, generate_only=True)
    print("\n[OK] Processo finalizado.")
