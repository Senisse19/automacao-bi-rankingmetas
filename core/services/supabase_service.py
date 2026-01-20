import os
import requests
import json
from dotenv import load_dotenv

# Force reload of .env
load_dotenv()

class SupabaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        # Try standard/backend env vars first, then frontend/legacy ones
        self.url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip()
        anon_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip()
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
        
        # Use Service Role Key to bypass RLS (Required for Backend Scripts)
        self.key = service_key
        
        if not self.key or self.key == "":
             # Fallback warning or check
             print("⚠ Aviso: SERVICE_ROLE_KEY não encontrada. Tentando Anon Key (pode falhar com RLS)...")
             self.key = anon_key 
        
        if not self.url or not self.key:
            print("❌ Erro: Credenciais do Supabase não encontradas no .env")
            return

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }


    def _get(self, table, params=None):
        """Helper para fazer requests GET na API REST."""
        try:
            endpoint = f"{self.url}/rest/v1/{table}"
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro HTTP Supabase ({table}): {e}")
            return []

    def get_active_schedules(self):
        """Busca todos os agendamentos ativos e seus destinatários."""
        if not self.url:
            return []

        try:
            # 1. Fetch schedules with definitions
            # Supabase API syntax for join: select=*,definition:automation_definitions(*)
            params = {
                # Fetch schedule, its direct template (if any), definition, and definition's default template
                "select": "*, template:automation_templates(*), definition:automation_definitions(*, default_template:automation_templates(*))",
                "active": "eq.true"
            }
            schedules = self._get("automation_schedules", params)
            
            if not schedules:
                return []

            # 2. Fetch recipients
            # To optimize, we could do one big query or multiple.
            # Let's fetch all recipients for active schedules.
            # Simplest is one query per schedule as before, or one big query if we had schedule_ids.
            # Let's stick to simple logic: for each schedule, fetch recipients.
            
            for sched in schedules:
                # Query automation_recipients join automation_contacts
                rec_params = {
                    "select": "contact:automation_contacts(*)",
                    "schedule_id": f"eq.{sched['id']}"
                }
                # Also filter where contact is active? 
                # The join syntax checks foreign key. To filter on joined table:
                # automation_contacts.active=eq.true.
                # Syntax: select=contact:automation_contacts(*)&contact.active=eq.true
                # But we have map table.
                
                resp_data = self._get("automation_recipients", rec_params)
                
                # Flatten and filter active
                contacts = []
                for r in resp_data:
                    c = r.get('contact')
                    if c and c.get('active'):
                        contacts.append(c)
                
                sched['recipients'] = contacts

            return schedules

        except Exception as e:
            print(f"❌ Erro ao buscar agendamentos do Supabase: {e}")
            return []

    def check_welcome_sent(self, contact_id):
        """Verifica se já enviamos mensagem de boas-vindas para este contato."""
        try:
            # Check in 'automation_logs' table for type='welcome_msg'
            params = {
                "contact_id": f"eq.{contact_id}",
                "event_type": "eq.welcome_msg",
                "select": "id"
            }
            logs = self._get("automation_logs", params)
            return len(logs) > 0
        except Exception:
            # Fallback safe: se der erro (tabela nao existe), assume que já enviou para não floodar
            return True

    def log_event(self, event_type, details, contact_id=None):
        """Registra um evento de execução no Supabase."""
        try:
            payload = {
                "event_type": event_type,
                "details": details,  # dict
                "contact_id": contact_id
            }
            # Remove keys with None values (like contact_id if unused) to avoid FK errors if strict
            # but JSON payload usually handles null fine if column allows it.
            
            endpoint = f"{self.url}/rest/v1/automation_logs"
            resp = requests.post(endpoint, headers=self.headers, json=payload)
            if resp.status_code >= 400:
                print(f"⚠ Falha ao gravar log {event_type}: {resp.text}")
        except Exception as e:
            print(f"⚠ Erro ao gravar log {event_type}: {e}")

    def mark_welcome_sent(self, contact_id):
        """Registra que enviamos boas-vindas."""
        self.log_event("welcome_msg", {"timestamp": "now()"}, contact_id)

    def get_template_by_name(self, name):
        """Busca um template pelo nome exato."""
        try:
            params = {
                "name": f"eq.{name}",
                "select": "*"
            }
            templates = self._get("automation_templates", params)
            if templates:
                return templates[0]
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar template '{name}': {e}")
            return None

    # --- Job Queue Methods ---

    def get_pending_jobs(self):
        """Busca jobs pendentes na fila de execução."""
        try:
            params = {
                "status": "eq.pending",
                "select": "*",
                "order": "created_at.asc"
            }
            return self._get("automation_queue", params)
        except Exception as e:
            print(f"❌ Erro ao buscar jobs pendentes: {e}")
            return []

    def update_job_status(self, job_id, status, logs=None):
        """Atualiza o status de um job na fila."""
        try:
            payload = { "status": status, "updated_at": "now()" }
            if logs:
                payload["logs"] = logs
            
            endpoint = f"{self.url}/rest/v1/automation_queue?id=eq.{job_id}"
            resp = requests.patch(endpoint, headers=self.headers, json=payload)
            if resp.status_code >= 400:
                print(f"⚠ Falha ao atualizar job {job_id}: {resp.text}")
        except Exception as e:
            print(f"⚠ Erro ao atualizar job {job_id}: {e}")

    def get_schedule_by_id(self, schedule_id):
        """Busca detalhes de um agendamento específico."""
        try:
            params = {
                "id": f"eq.{schedule_id}",
                "select": "*, definition:automation_definitions(*)"
            }
            data = self._get("automation_schedules", params)
            return data[0] if data else None
        except Exception as e:
            print(f"❌ Erro ao buscar schedule {schedule_id}: {e}")
            return None

    # --- Configuration Methods ---

    _settings_cache = {}
    _settings_last_fetch = 0

    def get_setting(self, key, default=None):
        """Busca uma configuração do sistema (com cache de 5 minutos)."""
        import time
        now = time.time()
        
        # Check cache if fresh (300s = 5min)
        if key in self._settings_cache and (now - self._settings_last_fetch < 300):
            return self._settings_cache[key]
            
        try:
            # Fetch specific key from DB
            params = {
                "key": f"eq.{key}",
                "select": "value"
            }
            data = self._get("system_settings", params)
            if data:
                val = data[0]['value']
                self._settings_cache[key] = val
                self._settings_last_fetch = now
                return val
            else:
                return default
        except Exception as e:
            print(f"⚠ Erro ao buscar setting '{key}': {e}")
            return default

    # --- Report Snapshot Methods ---

    def save_report_snapshot(self, report_type: str, date_ref: str, data: dict) -> str | None:
        """
        Salva um snapshot do relatório para geração de link dinâmico.
        Retorna o ID do relatório criado (UUID) ou None em caso de erro.
        """
        try:
            payload = {
                "type": report_type,
                "date_ref": date_ref,
                "data": data,
                "created_at": "now()"
            }
            endpoint = f"{self.url}/rest/v1/automation_reports"
            # Return representation to get the ID back
            headers = self.headers.copy()
            headers["Prefer"] = "return=representation"
            
            resp = requests.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                 print(f"⚠ Falha ao salvar snapshot do relatório: {resp.text}")
                 return None
            
            result = resp.json()
            if result and len(result) > 0:
                report_id = result[0].get('id')
                print(f"✅ Snapshot salvo com sucesso: {report_id}")
                return report_id
            return None
        except Exception as e:
            print(f"⚠ Erro ao salvar snapshot: {e}")
            return None

    def upsert_data(self, table: str, data: list | dict, on_conflict: str = "id") -> bool:
        """
        Realiza um UPSERT (Insert ou Update) na tabela especificada.
        Utiliza o header 'Prefer: resolution=merge-duplicates'.
        Args:
            table: Nome da tabela
            data: Dicionário ou Lista de Dicionários com os dados.
            on_conflict: Coluna para verificação de duplicidade (default: id)
        """
        try:
            endpoint = f"{self.url}/rest/v1/{table}?on_conflict={on_conflict}"
            headers = self.headers.copy()
            headers["Prefer"] = "resolution=merge-duplicates"
            
            resp = requests.post(endpoint, headers=headers, json=data)
            if resp.status_code >= 400:
                print(f"⚠ Falha ao fazer upsert em {table}: {resp.text}")
                return False
            return True
        except Exception as e:
            print(f"⚠ Erro ao fazer upsert em {table}: {e}")
            return False

    def get_all_ids(self, table: str) -> set:
        """Retorna um set com todos os IDs da tabela para validação rápida."""
        try:
            # Fetch minimal data
            endpoint = f"{self.url}/rest/v1/{table}?select=id"
            resp = requests.get(endpoint, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return {str(item['id']) for item in data}
        except Exception as e:
            print(f"⚠ Erro ao buscar IDs de {table}: {e}")
            return set()

if __name__ == "__main__":
    # Teste
    svc = SupabaseService()
    schedules = svc.get_active_schedules()
    print(f"Encontrados {len(schedules)} agendamentos ativos.")
    for s in schedules:
        def_name = s.get('definition', {}).get('name', 'Unknown')
        recipients = s.get('recipients', [])
        print(f"- [{s['scheduled_time']}] {s['name']} ({def_name}) -> {len(recipients)} contatos")

