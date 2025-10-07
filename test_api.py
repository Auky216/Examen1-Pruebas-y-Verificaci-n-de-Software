import pytest
from datetime import date, datetime, timedelta
from models import Autor, Libro, Copia, Lector, EstadoCopia, BioAlert, Prestamo, Suscripcion
from service import BibliotecaService


@pytest.fixture
def autor_somerville():
    return Autor(nombre="Somerville", fecha_nacimiento=date(1950, 1, 1))


@pytest.fixture
def autor_pressman():
    return Autor(nombre="Pressman", fecha_nacimiento=date(1945, 5, 15))


@pytest.fixture
def libro_se(autor_somerville):
    return Libro(nombre="Software Engineering", anio=2020, autor=autor_somerville)


@pytest.fixture
def libro_se_10th(autor_somerville):
    return Libro(nombre="Software Engineering 10th Edition", anio=2015, autor=autor_somerville)


@pytest.fixture
def biblioteca():
    service = BibliotecaService()
    service.bio_alert._suscripciones = {}
    return service


@pytest.fixture
def lector_test():
    return Lector(id="L001", nombre="Juan Perez", email="juan@example.com")


@pytest.fixture
def lector_test2():
    return Lector(id="L002", nombre="Maria Lopez", email="maria@example.com")


def test_crear_autor(autor_somerville):
    assert autor_somerville.nombre == "Somerville"
    assert autor_somerville.fecha_nacimiento == date(1950, 1, 1)


def test_crear_autor_pressman(autor_pressman):
    assert autor_pressman.nombre == "Pressman"
    assert autor_pressman.fecha_nacimiento == date(1945, 5, 15)


def test_crear_libro(libro_se, autor_somerville):
    assert libro_se.nombre == "Software Engineering"
    assert libro_se.anio == 2020
    assert libro_se.autor.nombre == "Somerville"
    assert libro_se.id is not None


def test_crear_libro_con_id_personalizado(autor_somerville):
    libro = Libro(nombre="Test Book", anio=2023, autor=autor_somerville, id="custom_id")
    assert libro.id == "custom_id"


def test_libro_id_generado_automaticamente(autor_somerville):
    libro = Libro(nombre="Software Engineering", anio=2020, autor=autor_somerville)
    assert "Software_Engineering" in libro.id
    assert "Somerville" in libro.id
    assert "2020" in libro.id


def test_crear_copia(libro_se):
    copia = Copia(id="C001", libro=libro_se)
    assert copia.id == "C001"
    assert copia.estado == EstadoCopia.DISPONIBLE
    assert copia.libro.nombre == "Software Engineering"


def test_crear_copia_con_estado_inicial(libro_se):
    copia = Copia(id="C001", libro=libro_se, estado=EstadoCopia.EN_REPARACION)
    assert copia.estado == EstadoCopia.EN_REPARACION


def test_agregar_libro_biblioteca(biblioteca, libro_se):
    libro_agregado = biblioteca.agregar_libro(libro_se)
    assert libro_se.id in biblioteca.libros
    assert biblioteca.libros[libro_se.id] == libro_agregado


def test_agregar_multiples_libros(biblioteca, libro_se, libro_se_10th):
    biblioteca.agregar_libro(libro_se)
    biblioteca.agregar_libro(libro_se_10th)
    assert len(biblioteca.libros) == 2


def test_agregar_copia_biblioteca(biblioteca, libro_se):
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    assert "C001" in biblioteca.copias
    assert libro_se.id in biblioteca.libros


def test_agregar_copia_agrega_libro_automaticamente(biblioteca, libro_se):
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    assert libro_se.id in biblioteca.libros


def test_contar_copias_libro(biblioteca, libro_se):
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro_se)
    copia3 = Copia(id="C003", libro=libro_se)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    biblioteca.agregar_copia(copia3)
    
    assert biblioteca.contar_copias_libro(libro_se.id) == 3


def test_contar_copias_libro_inexistente(biblioteca):
    assert biblioteca.contar_copias_libro("libro_inexistente") == 0


def test_obtener_copias_libro(biblioteca, libro_se):
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro_se)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    
    copias = biblioteca.obtener_copias_libro(libro_se.id)
    assert len(copias) == 2
    assert all(c.libro.id == libro_se.id for c in copias)


def test_obtener_libros_por_autor(biblioteca, autor_somerville):
    libro1 = Libro(nombre="Software Engineering 8th", anio=2006, autor=autor_somerville)
    libro2 = Libro(nombre="Software Engineering 9th", anio=2010, autor=autor_somerville)
    libro3 = Libro(nombre="Software Engineering 10th", anio=2015, autor=autor_somerville)
    
    biblioteca.agregar_libro(libro1)
    biblioteca.agregar_libro(libro2)
    biblioteca.agregar_libro(libro3)
    
    libros = biblioteca.obtener_libros_por_autor("Somerville")
    assert len(libros) == 3


def test_obtener_libros_por_autor_case_insensitive(biblioteca, autor_somerville):
    libro = Libro(nombre="Software Engineering", anio=2020, autor=autor_somerville)
    biblioteca.agregar_libro(libro)
    
    libros_lower = biblioteca.obtener_libros_por_autor("somerville")
    libros_upper = biblioteca.obtener_libros_por_autor("SOMERVILLE")
    
    assert len(libros_lower) == 1
    assert len(libros_upper) == 1


def test_obtener_libros_autor_inexistente(biblioteca):
    libros = biblioteca.obtener_libros_por_autor("Autor Inexistente")
    assert len(libros) == 0


def test_agregar_lector(biblioteca, lector_test):
    biblioteca.agregar_lector(lector_test)
    assert lector_test.id in biblioteca.lectores


def test_lector_puede_prestar(lector_test):
    assert lector_test.puede_prestar() is True
    assert len(lector_test.prestamos_activos) == 0


def test_lector_inicializado_correctamente():
    lector = Lector(id="L999", nombre="Test User", email="test@test.com")
    assert lector.dias_suspension == 0
    assert lector.fecha_fin_suspension is None
    assert len(lector.prestamos_activos) == 0


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


def test_prestar_libro_lector_inexistente(biblioteca):
    with pytest.raises(ValueError, match="Lector no encontrado"):
        biblioteca.prestar_libro("L999", "C001")


def test_prestar_libro_copia_inexistente(biblioteca, lector_test):
    biblioteca.agregar_lector(lector_test)
    with pytest.raises(ValueError, match="Copia no encontrada"):
        biblioteca.prestar_libro(lector_test.id, "C999")


def test_prestar_libro_cambia_estado(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    prestamo = biblioteca.prestar_libro(lector_test.id, copia.id)
    
    assert copia.estado == EstadoCopia.PRESTADA
    assert len(lector_test.prestamos_activos) == 1
    assert prestamo.copia.id == "C001"


def test_prestamo_tiene_fecha_devolucion_30_dias(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    prestamo = biblioteca.prestar_libro(lector_test.id, copia.id)
    dias_diferencia = (prestamo.fecha_devolucion_esperada - prestamo.fecha_prestamo).days
    
    assert dias_diferencia == 30


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


def test_devolver_libro_lector_inexistente(biblioteca):
    with pytest.raises(ValueError, match="Lector no encontrado"):
        biblioteca.devolver_libro("L999", "C001")


def test_devolver_libro_inexistente(biblioteca, lector_test):
    biblioteca.agregar_lector(lector_test)
    
    with pytest.raises(ValueError, match="Préstamo no encontrado"):
        biblioteca.devolver_libro(lector_test.id, "C999")


def test_lector_suspendido_no_puede_prestar(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    lector_test.aplicar_multa(5)
    
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="suspendido"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_lector_esta_suspendido(lector_test):
    assert lector_test.esta_suspendido() is False
    lector_test.aplicar_multa(3)
    assert lector_test.esta_suspendido() is True


def test_lector_suspension_expira(lector_test):
    lector_test.aplicar_multa(1)
    lector_test.fecha_fin_suspension = date.today() - timedelta(days=1)
    assert lector_test.esta_suspendido() is False


def test_aplicar_multa_suma_dias(lector_test):
    lector_test.aplicar_multa(3)
    assert lector_test.dias_suspension == 6
    
    lector_test.aplicar_multa(2)
    assert lector_test.dias_suspension == 10


def test_aplicar_multa_extiende_fecha(lector_test):
    lector_test.aplicar_multa(2)
    fecha1 = lector_test.fecha_fin_suspension
    
    lector_test.aplicar_multa(3)
    fecha2 = lector_test.fecha_fin_suspension
    
    assert fecha2 > fecha1


def test_bioalert_singleton():
    bio1 = BioAlert()
    bio2 = BioAlert()
    assert bio1 is bio2


def test_bioalert_mantiene_estado():
    bio1 = BioAlert()
    bio1._suscripciones["test"] = []
    
    bio2 = BioAlert()
    assert "test" in bio2._suscripciones


def test_suscribir_lector_bioalert(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_libro(libro_se)
    
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    
    suscripciones = biblioteca.bio_alert.obtener_suscripciones(libro_se.id)
    assert len(suscripciones) == 1
    assert suscripciones[0].lector.id == lector_test.id


def test_suscribir_lector_inexistente(biblioteca):
    with pytest.raises(ValueError, match="Lector no encontrado"):
        biblioteca.suscribir_lector("L999", "libro_id")


def test_suscribir_libro_inexistente(biblioteca, lector_test):
    biblioteca.agregar_lector(lector_test)
    with pytest.raises(ValueError, match="Libro no encontrado"):
        biblioteca.suscribir_lector(lector_test.id, "libro_inexistente")


def test_multiples_suscripciones_mismo_libro(biblioteca, lector_test, lector_test2, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_lector(lector_test2)
    biblioteca.agregar_libro(libro_se)
    
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    biblioteca.suscribir_lector(lector_test2.id, libro_se.id)
    
    suscripciones = biblioteca.bio_alert.obtener_suscripciones(libro_se.id)
    assert len(suscripciones) == 2


def test_notificar_disponibilidad(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_libro(libro_se)
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    
    emails = biblioteca.bio_alert.notificar_disponibilidad(libro_se.id)
    
    assert len(emails) == 1
    assert lector_test.email in emails


def test_notificar_disponibilidad_libro_sin_suscripciones(biblioteca):
    emails = biblioteca.bio_alert.notificar_disponibilidad("libro_sin_suscripciones")
    assert len(emails) == 0


def test_limpiar_suscripciones(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_libro(libro_se)
    biblioteca.suscribir_lector(lector_test.id, libro_se.id)
    
    biblioteca.bio_alert.limpiar_suscripciones(libro_se.id)
    suscripciones = biblioteca.bio_alert.obtener_suscripciones(libro_se.id)
    
    assert len(suscripciones) == 0


def test_limpiar_suscripciones_libro_inexistente(biblioteca):
    biblioteca.bio_alert.limpiar_suscripciones("libro_inexistente")
    suscripciones = biblioteca.bio_alert.obtener_suscripciones("libro_inexistente")
    assert len(suscripciones) == 0


def test_copias_disponibles(biblioteca, libro_se):
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro_se, estado=EstadoCopia.PRESTADA)
    copia3 = Copia(id="C003", libro=libro_se)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    biblioteca.agregar_copia(copia3)
    
    disponibles = biblioteca.obtener_copias_disponibles(libro_se.id)
    assert len(disponibles) == 2


def test_copias_disponibles_libro_sin_copias(biblioteca):
    disponibles = biblioteca.obtener_copias_disponibles("libro_sin_copias")
    assert len(disponibles) == 0


def test_cambiar_estado_copia(biblioteca, libro_se):
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    biblioteca.cambiar_estado_copia("C001", EstadoCopia.EN_REPARACION)
    assert copia.estado == EstadoCopia.EN_REPARACION


def test_cambiar_estado_copia_inexistente(biblioteca):
    with pytest.raises(ValueError, match="Copia no encontrada"):
        biblioteca.cambiar_estado_copia("C999", EstadoCopia.EN_REPARACION)


def test_todos_los_estados_copia():
    estados = [
        EstadoCopia.DISPONIBLE,
        EstadoCopia.PRESTADA,
        EstadoCopia.RESERVADA,
        EstadoCopia.CON_RETRASO,
        EstadoCopia.EN_REPARACION
    ]
    assert len(estados) == 5


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


def test_prestamo_sin_retraso():
    autor = Autor(nombre="Test", fecha_nacimiento=date(1950, 1, 1))
    libro = Libro(nombre="Test Book", anio=2020, autor=autor)
    copia = Copia(id="C001", libro=libro)
    
    prestamo = Prestamo(
        copia=copia,
        fecha_prestamo=datetime.now(),
        fecha_devolucion_esperada=datetime.now() + timedelta(days=30)
    )
    
    assert prestamo.calcular_dias_retraso() == 0
    assert prestamo.esta_retrasado() is False


def test_prestamo_con_devolucion_real(libro_se):
    copia = Copia(id="C001", libro=libro_se)
    prestamo = Prestamo(
        copia=copia,
        fecha_prestamo=datetime.now() - timedelta(days=35),
        fecha_devolucion_esperada=datetime.now() - timedelta(days=5),
        fecha_devolucion_real=datetime.now() - timedelta(days=2)
    )
    
    assert prestamo.calcular_dias_retraso() == 3


def test_prestar_copia_no_disponible(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se, estado=EstadoCopia.EN_REPARACION)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="no disponible"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_prestar_copia_reservada(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se, estado=EstadoCopia.RESERVADA)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="no disponible"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_prestar_copia_con_retraso(biblioteca, lector_test, libro_se):
    biblioteca.agregar_lector(lector_test)
    copia = Copia(id="C001", libro=libro_se, estado=EstadoCopia.CON_RETRASO)
    biblioteca.agregar_copia(copia)
    
    with pytest.raises(ValueError, match="no disponible"):
        biblioteca.prestar_libro(lector_test.id, copia.id)


def test_suscripcion_tiene_fecha(lector_test, libro_se):
    suscripcion = Suscripcion(lector=lector_test, libro_id=libro_se.id)
    assert suscripcion.fecha_suscripcion is not None
    assert isinstance(suscripcion.fecha_suscripcion, datetime)


def test_devolucion_notifica_suscriptores(biblioteca, lector_test, lector_test2, libro_se):
    biblioteca.agregar_lector(lector_test)
    biblioteca.agregar_lector(lector_test2)
    biblioteca.agregar_libro(libro_se)
    
    copia = Copia(id="C001", libro=libro_se)
    biblioteca.agregar_copia(copia)
    
    biblioteca.suscribir_lector(lector_test2.id, libro_se.id)
    biblioteca.prestar_libro(lector_test.id, copia.id)
    
    resultado = biblioteca.devolver_libro(lector_test.id, copia.id)
    
    assert len(resultado["emails_notificados"]) == 1
    assert lector_test2.email in resultado["emails_notificados"]


def test_multiples_prestamos_mismo_lector(biblioteca, lector_test, libro_se, autor_pressman):
    biblioteca.agregar_lector(lector_test)
    
    libro2 = Libro(nombre="Otro Libro", anio=2021, autor=autor_pressman)
    
    copia1 = Copia(id="C001", libro=libro_se)
    copia2 = Copia(id="C002", libro=libro2)
    
    biblioteca.agregar_copia(copia1)
    biblioteca.agregar_copia(copia2)
    
    biblioteca.prestar_libro(lector_test.id, copia1.id)
    biblioteca.prestar_libro(lector_test.id, copia2.id)
    
    assert len(lector_test.prestamos_activos) == 2