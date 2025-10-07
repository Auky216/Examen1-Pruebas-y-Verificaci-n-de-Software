from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models import Libro, Copia, Lector, Prestamo, EstadoCopia, BioAlert


class BibliotecaService:
    def __init__(self):
        self.libros: Dict[str, Libro] = {}
        self.copias: Dict[str, Copia] = {}
        self.lectores: Dict[str, Lector] = {}
        self.bio_alert = BioAlert()

    def agregar_libro(self, libro: Libro) -> Libro:
        self.libros[libro.id] = libro
        return libro

    def agregar_copia(self, copia: Copia) -> Copia:
        if copia.libro.id not in self.libros:
            self.agregar_libro(copia.libro)
        self.copias[copia.id] = copia
        return copia

    def agregar_lector(self, lector: Lector) -> Lector:
        self.lectores[lector.id] = lector
        return lector

    def obtener_libros_por_autor(self, nombre_autor: str) -> List[Libro]:
        return [
            libro for libro in self.libros.values()
            if libro.autor.nombre.lower() == nombre_autor.lower()
        ]

    def contar_copias_libro(self, libro_id: str) -> int:
        return sum(1 for copia in self.copias.values() if copia.libro.id == libro_id)

    def obtener_copias_libro(self, libro_id: str) -> List[Copia]:
        return [copia for copia in self.copias.values() if copia.libro.id == libro_id]

    def prestar_libro(self, lector_id: str, copia_id: str) -> Prestamo:
        if lector_id not in self.lectores:
            raise ValueError("Lector no encontrado")
        
        if copia_id not in self.copias:
            raise ValueError("Copia no encontrada")
        
        lector = self.lectores[lector_id]
        copia = self.copias[copia_id]

        if not lector.puede_prestar():
            if lector.esta_suspendido():
                raise ValueError(f"Lector suspendido hasta {lector.fecha_fin_suspension}")
            raise ValueError("Lector tiene el máximo de préstamos (3)")

        if copia.estado != EstadoCopia.DISPONIBLE:
            raise ValueError(f"Copia no disponible. Estado: {copia.estado}")

        fecha_prestamo = datetime.now()
        fecha_devolucion = fecha_prestamo + timedelta(days=30)

        prestamo = Prestamo(
            copia=copia,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion_esperada=fecha_devolucion
        )

        copia.estado = EstadoCopia.PRESTADA
        lector.prestamos_activos.append(prestamo)

        return prestamo

    def devolver_libro(self, lector_id: str, copia_id: str) -> dict:
        if lector_id not in self.lectores:
            raise ValueError("Lector no encontrado")

        lector = self.lectores[lector_id]
        prestamo_encontrado = None

        for prestamo in lector.prestamos_activos:
            if prestamo.copia.id == copia_id:
                prestamo_encontrado = prestamo
                break

        if prestamo_encontrado is None:
            raise ValueError("Préstamo no encontrado")

        prestamo_encontrado.fecha_devolucion_real = datetime.now()
        dias_retraso = prestamo_encontrado.calcular_dias_retraso()

        if dias_retraso > 0:
            lector.aplicar_multa(dias_retraso)
            prestamo_encontrado.copia.estado = EstadoCopia.CON_RETRASO
        
        prestamo_encontrado.copia.estado = EstadoCopia.DISPONIBLE
        lector.prestamos_activos.remove(prestamo_encontrado)

        emails_notificados = self.bio_alert.notificar_disponibilidad(
            prestamo_encontrado.copia.libro.id
        )

        return {
            "dias_retraso": dias_retraso,
            "multa_aplicada": dias_retraso * 2 if dias_retraso > 0 else 0,
            "emails_notificados": emails_notificados
        }

    def suscribir_lector(self, lector_id: str, libro_id: str):
        if lector_id not in self.lectores:
            raise ValueError("Lector no encontrado")
        
        if libro_id not in self.libros:
            raise ValueError("Libro no encontrado")

        lector = self.lectores[lector_id]
        self.bio_alert.suscribir(lector, libro_id)

    def cambiar_estado_copia(self, copia_id: str, nuevo_estado: EstadoCopia):
        if copia_id not in self.copias:
            raise ValueError("Copia no encontrada")
        
        self.copias[copia_id].estado = nuevo_estado

    def obtener_copias_disponibles(self, libro_id: str) -> List[Copia]:
        return [
            copia for copia in self.copias.values()
            if copia.libro.id == libro_id and copia.estado == EstadoCopia.DISPONIBLE
        ]