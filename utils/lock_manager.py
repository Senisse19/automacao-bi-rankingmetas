import atexit
import os
import time

from utils.logger import get_logger

logger = get_logger("lock_manager")


class LockManager:
    """
    Gerencia o arquivo de trava (lock file) para garantir que apenas uma instância
    do scheduler esteja rodando. Implementa verificação de heartbeat para travas estagnadas.
    """

    def __init__(self, lock_file="scheduler.lock", heartbeat_interval=10):
        self.lock_file = lock_file
        self.heartbeat_interval = heartbeat_interval
        self.last_heartbeat = 0
        self.pid = os.getpid()

    def acquire(self):
        """Tenta adquirir o lock. Retorna True se sucesso, False se falha."""
        if os.path.exists(self.lock_file):
            try:
                # HEARTBEAT CHECK: Se o arquivo existir e não for atualizado há > 60s, é stale.
                mtime = os.path.getmtime(self.lock_file)
                if time.time() - mtime > 60:
                    logger.warning(
                        f"⚠️ Lock file antigo encontrado (última atualização há {time.time() - mtime:.0f}s). "
                        "Assumindo crash anterior e removendo."
                    )
                    try:
                        os.remove(self.lock_file)
                    except OSError:
                        pass  # Race condition
                else:
                    # Ainda está ativo (heartbeat recente)
                    with open(self.lock_file, "r") as f:
                        existing_pid = f.read().strip()
                    logger.critical(f"❌ Scheduler já está rodando (PID {existing_pid}, Heartbeat < 60s). Abortando.")
                    return False
            except OSError:
                pass  # File deletion race condition

        # Criar Lock
        try:
            with open(self.lock_file, "w") as f:
                f.write(str(self.pid))

            atexit.register(self.release)
            logger.info(f"🔒 Single Instance Lock adquirido (PID {self.pid})")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar lock file: {e}")
            return False

    def release(self):
        """Remove o arquivo de lock."""
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
                logger.info("🔓 Lock file removido.")
            except OSError:
                pass

    def update_heartbeat(self):
        """Atualiza o timestamp do arquivo para indicar atividade."""
        if time.time() - self.last_heartbeat > self.heartbeat_interval:
            if os.path.exists(self.lock_file):
                try:
                    os.utime(self.lock_file, None)
                except OSError:
                    pass
            self.last_heartbeat = time.time()
