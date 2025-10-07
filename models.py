from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class EstadoCopia(str, Enum):
    DISPONIBLE = "disponible"
    PRESTADA = "prestada"
    RESERVADA = "reservada"
    CON_RETRASO = "con_retraso"
    EN_REPARACION = "en_reparacion"


class Autor(BaseModel):
    nombre: str
    fecha_nacimiento: date


class Libro(BaseModel):
    nombre: str
    anio: int
    autor: Autor
    id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = f"{self.nombre}_{self.autor.nombre}_{self.anio}".replace(" ", "_")


class Copia(BaseModel):
    id: str
    libro: Libro
    estado: EstadoCopia = EstadoCopia.DISPONIBLE


class Prestamo(BaseModel):
    copia: Copia
    fecha_prestamo: datetime
    fecha_devolucion_esperada: datetime
    fecha_devolucion_real: Optional[datetime] = None

    def calcular_dias_retraso(self) -> int:
        fecha_comparacion = self.fecha_devolucion_real or datetime.now()
        if fecha_comparacion > self.fecha_devolucion_esperada:
            return (fecha_comparacion - self.fecha_devolucion_esperada).days
        return 0

    def esta_retrasado(self) -> bool:
        return self.calcular_dias_retraso() > 0


class Lector(BaseModel):
    id: str
    nombre: str
    email: str
    prestamos_activos: List[Prestamo] = Field(default_factory=list)
    dias_suspension: int = 0
    fecha_fin_suspension: Optional[date] = None

    def puede_prestar(self) -> bool:
        if self.esta_suspendido():
            return False
        return len(self.prestamos_activos) < 3

    def esta_suspendido(self) -> bool:
        if self.fecha_fin_suspension is None:
            return False
        return date.today() <= self.fecha_fin_suspension

    def aplicar_multa(self, dias_retraso: int):
        dias_multa = dias_retraso * 2
        self.dias_suspension += dias_multa
        if self.fecha_fin_suspension is None:
            self.fecha_fin_suspension = date.today() + timedelta(days=dias_multa)
        else:
            self.fecha_fin_suspension += timedelta(days=dias_multa)


class Suscripcion(BaseModel):
    lector: Lector
    libro_id: str
    fecha_suscripcion: datetime = Field(default_factory=datetime.now)


class BioAlert:
    _instance = None
    _suscripciones: Dict[str, List[Suscripcion]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BioAlert, cls).__new__(cls)
            cls._instance._suscripciones = {}
        return cls._instance

    def suscribir(self, lector: Lector, libro_id: str):
        if libro_id not in self._suscripciones:
            self._suscripciones[libro_id] = []
        
        suscripcion = Suscripcion(lector=lector, libro_id=libro_id)
        self._suscripciones[libro_id].append(suscripcion)

    def notificar_disponibilidad(self, libro_id: str) -> List[str]:
        if libro_id not in self._suscripciones:
            return []
        
        emails_notificados = []
        for suscripcion in self._suscripciones[libro_id]:
            emails_notificados.append(suscripcion.lector.email)
        
        return emails_notificados

    def obtener_suscripciones(self, libro_id: str) -> List[Suscripcion]:
        return self._suscripciones.get(libro_id, [])

    def limpiar_suscripciones(self, libro_id: str):
        if libro_id in self._suscripciones:
            del self._suscripciones[libro_id]