"""Límite de preguntas por alumno y por minuto (RF-M06).

Con una sola generación a la vez, un alumno que manda muchas preguntas seguidas llena la cola y deja esperando a los
demás. Se cuenta en memoria (ventana deslizante de 60 s) y no se guarda nada: la clave es la IP del navegador hasta
que el Campus pase un identificador opaco del alumno.
"""

import threading
import time
from collections import deque
from collections.abc import Callable


class LimitePorMinuto:
    def __init__(self, maximo: int, ventana: float = 60.0, reloj: Callable[[], float] = time.monotonic):
        self.maximo = maximo
        self.ventana = ventana
        self._reloj = reloj
        self._pedidos: dict[str, deque[float]] = {}
        self._candado = threading.Lock()

    def esperar(self, clave: str) -> float:
        """Registra un pedido. Devuelve 0 si se permite; si no, los segundos que faltan para poder preguntar."""
        if self.maximo <= 0:  # 0 = sin límite
            return 0.0
        ahora = self._reloj()
        with self._candado:
            pedidos = self._pedidos.setdefault(clave, deque())
            while pedidos and ahora - pedidos[0] >= self.ventana:
                pedidos.popleft()
            if len(pedidos) >= self.maximo:
                return self.ventana - (ahora - pedidos[0])
            pedidos.append(ahora)
            self._limpiar(ahora)
            return 0.0

    def _limpiar(self, ahora: float) -> None:
        """Quita las claves sin pedidos recientes, para que la memoria no crezca con cada IP nueva."""
        if len(self._pedidos) < 1000:
            return
        for clave in [c for c, p in self._pedidos.items() if not p or ahora - p[-1] >= self.ventana]:
            del self._pedidos[clave]


def clave_del_alumno(ip: str | None, reenviado_por: str | None, confiar_en_proxy: bool) -> str:
    """Detrás de Nginx todas las consultas llegan desde la IP del proxy: ahí se usa X-Forwarded-For (solo si se
    configuró que hay un proxy de confianza; si no, cualquiera podría inventarse una IP para saltarse el límite)."""
    if confiar_en_proxy and reenviado_por:
        return reenviado_por.split(",")[0].strip()
    return ip or "desconocido"
