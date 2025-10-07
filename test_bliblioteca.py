import pytest
from datetime import date, datetime, timedelta
from models import Autor, Libro, Copia, Lector, EstadoCopia, BioAlert, Prestamo
from service import BibliotecaService


@pytest.fixture
def autor_somerville():
    return Autor(nombre="Somerville", fecha_nacimiento=date(1950, 1, 1))


@pytest.fixture
def libro_se(autor_somerville):
    return Libro(nombre="Software Engineering", anio=2020, autor=autor_somerville)


@pytest.fixture
def biblioteca():
    return BibliotecaService()


@pytest.fixture
def lector_test():
    return Lector(id="L001", nombre="Juan Perez", email="juan@example.com")


def test_crear_autor(autor_somerville):
    assert autor_somerville.nombre == "Somerville"
    assert autor_somerville.fecha_nacimiento == date(1950, 1, 1)


def test_crear_libro(libro_se, autor_somerville):
    assert libro_se.nombre == "Software Engineering"
    assert libro_se.anio == 2020
    assert libro_se.autor.nombre == "Somerville"
    assert libro_se.id is not None


def test_crear_copia(libro_se):
    copia = Copia(id="C001", libro=libro_se)
    assert copia.id == "C001"
    assert copia.estado == EstadoCopia.DISPONIBLE
    assert copia.libro.nombre == "Software Engineering"


def test_agregar_libro_biblioteca(biblioteca, libro_se):
    libro_agregado = biblioteca.agregar_libro(libro_se)
    assert libro_se.id in biblioteca.libros
    assert biblioteca.libros[libro_se.id] == libro_agregado


def test_agregar_copia_biblioteca(biblioteca, libro_se):
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    assert "C001" in biblioteca.copias
    assert libro_se.id in biblioteca.libros


def test_contar_copias_libro(biblioteca, libro_se):
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro_se)
    copia3 = Copia(id="C003", libro=libro_se)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    biblioteca.agregar_copia(copia3)
    
    assert biblioteca.contar_copias_libro(libro_se.id) == 3


def test_obtener_libros_por_autor(biblioteca, autor_somerville):
    libro1 = Libro(nombre="Software Engineering 8th", anio=2006, autor=autor_somerville)
    libro2 = Libro(nombre="Software Engineering 9th", anio=2010, autor=autor_somerville)
    libro3 = Libro(nombre="Software Engineering 10th", anio=2015, autor=autor_somerville)
    
    biblioteca.agregar_libro(libro1)
    biblioteca.agregar_libro(libro2)
    biblioteca.agregar_libro(libro3)
    
    libros = biblioteca.obtener_libros_por_autor("Somerville")
    assert len(libros) == 3


def test_lector_puede_prestar(lector_test):
    assert lector_test.puede_prestar() is True
    assert len(lector_test.prestamos_activos) == 0


def test_lector_maximo_prestamos(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    
    for i in range(3):
        copia = Copia(id=f"C00{i+1}", libro=libro_se)
        biblioteca.agregar_copia(copia)
        biblioteca.prestar_libro(lector_test.id, copia.id)
    
    assert len(lector_test.prestamos_activos) == 3
    assert lector_test.puede_prestar() is False


def test_prestar_libro_error_maximo_prestamos(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    
    for i in range(3):
        copia = Copia(id=f"C00{i+1}", libro=libro_se)
        biblioteca.agregar_copia(copia)
        biblioteca.prestar_libro(lector_test.id, copia.id)
    
    copia4 = Copia(id="C004", libro=libro_se)
    biblioteca.agregar_copia(copia4)
    
    with pytest.raises(ValueError, match="máximo de préstamos"):
        biblioteca.prestar_libro(lector_test.id, copia4.id)


def test_prestar_libro_cambia_estado(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    prestamo = biblioteca.prestar_libro(lector_test.id, copia.id)
    
    assert copia.estado == EstadoCopia.PRESTADA
    assert len(lector_test.prestamos_activos) == 1
    assert prestamo.copia.id == "C001"


def test_devolver_libro_sin_retraso(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    biblioteca.prestar_libro(lector_test.id, copia.id)
    resultado = biblioteca.devolver_libro(lector_test.id, copia.id)
    
    assert resultado["dias_retraso"] == 0
    assert resultado["multa_aplicada"] == 0
    assert copia.estado == EstadoCopia.DISPONIBLE
    assert len(lector_test.prestamos_activos) == 0


def test_devolver_libro_con_retraso(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    prestamo = biblioteca.prestar_libro(lector_test.id, copia.id)
    prestamo.fecha_devolucion_esperada = datetime.now() - timedelta(days=5)
    
    resultado = biblioteca.devolver_libro(lector_test.id, copia.id)
    
    assert resultado["dias_retraso"] == 5
    assert resultado["multa_aplicada"] == 10
    assert lector_test.dias_suspension == 10


def test_lector_suspendido_no_puede_prestar(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    lector_test.aplicar_multa(5)
    
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="suspendido"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_bioalert_singleton():
    bio1 = BioAlert()
    bio2 = BioAlert()
    assert bio1 is bio2


def test_suscribir_lector_bioalert(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_libro(libro_se)
    
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    
    suscripciones = biblioteca.bio_alert.obtener_suscripciones(libro_se.id)
    assert len(suscripciones) == 1
    assert suscripciones[0].lector.id == lector_test.id


def test_notificar_disponibilidad(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_libro(libro_se)
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    
    emails = biblioteca.bio_alert.notificar_disponibilidad(libro_se.id)
    
    assert len(emails) == 1
    assert lector_test.email in emails


def test_copias_disponibles(biblioteca, libro_se):
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro_se, estado=EstadoCopia.PRESTADA)
    copia3 = Copia(id="C003", libro=libro_se)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    biblioteca.agregar_copia(copia3)
    
    disponibles = biblioteca.obtener_copias_disponibles(libro_se.id)
    assert len(disponibles) == 2


def test_cambiar_estado_copia(biblioteca, libro_se):
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    biblioteca.cambiar_estado_copia("C001", EstadoCopia.EN_REPARACION)
    assert copia.estado == EstadoCopia.EN_REPARACION


def test_prestamo_calcula_dias_retraso():
    autor = Autor(nombre="Test", fecha_nacimiento=date(1950, 1, 1))
    libro = Libro(nombre="Test Book", anio=2020, autor=autor)
    copia = Copia(id="C001", libro=libro)
    
    prestamo = Prestamo(
        copia=copia,
        fecha_prestamo=datetime.now() - timedelta(days=35),
        fecha_devolucion_esperada=datetime.now() - timedelta(days=5)
    )
    
    assert prestamo.calcular_dias_retraso() == 5
    assert prestamo.esta_retrasado() is True


def test_prestar_copia_no_disponible(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se, estado=EstadoCopia.EN_REPARACION)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="no disponible"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_devolver_libro_inexistente(biblioteca, lector_test):
    biblioteca.agregar_lector(lector_test)
    
    with pytest.raises(ValueError, match="Préstamo no encontrado"):
        biblioteca.devolver_libro(lector_test.id, "C999")