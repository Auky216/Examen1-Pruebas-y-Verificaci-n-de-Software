from fastapi import FastAPI, HTTPException
from typing import List
from datetime import date
from models import Libro, Autor, Copia, Lector, EstadoCopia
from service import BibliotecaService
from pydantic import BaseModel

app = FastAPI(title="Sistema de Biblioteca")
biblioteca = BibliotecaService()


class LibroRequest(BaseModel):
    nombre: str
    anio: int
    autor_nombre: str
    autor_fecha_nacimiento: str


class CopiaRequest(BaseModel):
    id: str
    libro_id: str


class LectorRequest(BaseModel):
    id: str
    nombre: str
    email: str


class PrestamoRequest(BaseModel):
    lector_id: str
    copia_id: str


class DevolucionRequest(BaseModel):
    lector_id: str
    copia_id: str


class SuscripcionRequest(BaseModel):
    lector_id: str
    libro_id: str


@app.post("/libros/", response_model=dict)
def crear_libro(libro_req: LibroRequest):
    try:
        autor = Autor(
            nombre=libro_req.autor_nombre,
            fecha_nacimiento=date.fromisoformat(libro_req.autor_fecha_nacimiento)
        )
        libro = Libro(nombre=libro_req.nombre, anio=libro_req.anio, autor=autor)
        biblioteca.agregar_libro(libro)
        return {"mensaje": "Libro creado exitosamente", "libro_id": libro.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/copias/", response_model=dict)
def crear_copia(copia_req: CopiaRequest):
    try:
        if copia_req.libro_id not in biblioteca.libros:
            raise ValueError("Libro no encontrado")
        
        libro = biblioteca.libros[copia_req.libro_id]
        copia = Copia(id=copia_req.id, libro=libro)
        biblioteca.agregar_copia(copia)
        return {"mensaje": "Copia creada exitosamente", "copia_id": copia.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/lectores/", response_model=dict)
def crear_lector(lector_req: LectorRequest):
    try:
        lector = Lector(id=lector_req.id, nombre=lector_req.nombre, email=lector_req.email)
        biblioteca.agregar_lector(lector)
        return {"mensaje": "Lector creado exitosamente", "lector_id": lector.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/libros/autor/{nombre_autor}")
def obtener_libros_autor(nombre_autor: str):
    libros = biblioteca.obtener_libros_por_autor(nombre_autor)
    return {
        "autor": nombre_autor,
        "cantidad": len(libros),
        "libros": [{"nombre": l.nombre, "anio": l.anio, "id": l.id} for l in libros]
    }


@app.get("/libros/{libro_id}/copias")
def obtener_copias(libro_id: str):
    copias = biblioteca.obtener_copias_libro(libro_id)
    return {
        "libro_id": libro_id,
        "cantidad_copias": len(copias),
        "copias": [{"id": c.id, "estado": c.estado} for c in copias]
    }


@app.post("/prestamos/")
def realizar_prestamo(prestamo_req: PrestamoRequest):
    try:
        prestamo = biblioteca.prestar_libro(prestamo_req.lector_id, prestamo_req.copia_id)
        return {
            "mensaje": "Préstamo realizado exitosamente",
            "fecha_devolucion": prestamo.fecha_devolucion_esperada.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/devoluciones/")
def realizar_devolucion(devolucion_req: DevolucionRequest):
    try:
        resultado = biblioteca.devolver_libro(devolucion_req.lector_id, devolucion_req.copia_id)
        return {
            "mensaje": "Devolución realizada exitosamente",
            "dias_retraso": resultado["dias_retraso"],
            "multa_dias": resultado["multa_aplicada"],
            "notificaciones_enviadas": len(resultado["emails_notificados"])
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/suscripciones/")
def crear_suscripcion(suscripcion_req: SuscripcionRequest):
    try:
        biblioteca.suscribir_lector(suscripcion_req.lector_id, suscripcion_req.libro_id)
        return {"mensaje": "Suscripción realizada exitosamente en BioAlert"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/lectores/{lector_id}")
def obtener_lector(lector_id: str):
    if lector_id not in biblioteca.lectores:
        raise HTTPException(status_code=404, detail="Lector no encontrado")
    
    lector = biblioteca.lectores[lector_id]
    return {
        "id": lector.id,
        "nombre": lector.nombre,
        "email": lector.email,
        "prestamos_activos": len(lector.prestamos_activos),
        "suspendido": lector.esta_suspendido(),
        "fecha_fin_suspension": lector.fecha_fin_suspension.isoformat() if lector.fecha_fin_suspension else None
    }


@app.get("/")
def root():
    return {"mensaje": "Sistema de Biblioteca API - Activo"}