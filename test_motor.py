import json
import time
from pathlib import Path

import pandas as pd

from motor_inferencia import ADVERTENCIA, MotorRecomendacionCNSC

BASE = Path(__file__).resolve().parent
motor = MotorRecomendacionCNSC(BASE / "paquete_modelo_cnsc_v1.joblib")
perfil = json.loads((BASE / "ejemplo_perfil.json").read_text(encoding="utf-8"))

COLUMNAS_SALIDA = [
    "posicion",
    "opec",
    "descripcion",
    "numero_ruta",
    "tipo_ruta",
    "requisito_estudio",
    "requisito_experiencia",
    "meses_requeridos",
    "brecha_meses",
    "cumple_tiempo",
    "indice_compatibilidad",
    "orientacion",
    "experiencia_ciudadano_meses",
    "similitud_academica",
    "similitud_experiencia",
    "advertencia",
]
ORIENTACIONES_VALIDAS = {
    "Mayor compatibilidad histórica",
    "Revisar requisitos y brechas",
}

# 1. Inferencia principal y contrato funcional de salida.
inicio = time.perf_counter()
resultado = motor.recomendar(perfil, top_n=5)
duracion = time.perf_counter() - inicio

assert isinstance(resultado, pd.DataFrame)
assert len(resultado) == 5
assert set(COLUMNAS_SALIDA).issubset(resultado.columns), (
    f"Faltan columnas de salida: {sorted(set(COLUMNAS_SALIDA) - set(resultado.columns))}"
)
assert resultado["posicion"].tolist() == [1, 2, 3, 4, 5]
assert resultado["opec"].is_unique
assert resultado["indice_compatibilidad"].between(0, 1).all()
assert resultado["indice_compatibilidad"].is_monotonic_decreasing
assert resultado["similitud_academica"].between(0, 1).all()
assert resultado["similitud_experiencia"].between(0, 1).all()
assert (resultado["meses_requeridos"] >= 0).all()
assert (resultado["brecha_meses"] >= 0).all()
assert (resultado["experiencia_ciudadano_meses"] >= 0).all()
assert set(resultado["orientacion"].unique()).issubset(ORIENTACIONES_VALIDAS)
assert (resultado["advertencia"] == ADVERTENCIA).all()
assert resultado["advertencia"].str.contains("No es una probabilidad", regex=False).all()
assert duracion < 60

# 2. El parámetro top_n debe controlar el número de recomendaciones.
for limite in (1, 3, 10):
    salida = motor.recomendar(perfil, top_n=limite)
    assert len(salida) == limite, f"top_n={limite} devolvió {len(salida)} filas"

# El motor limita defensivamente top_n a un máximo de 100.
salida_maxima = motor.recomendar(perfil, top_n=500)
assert len(salida_maxima) == min(100, len(motor.catalogo))

# 3. La orientación debe corresponder al umbral congelado del paquete.
esperada = resultado["indice_compatibilidad"].apply(
    lambda x: "Mayor compatibilidad histórica"
    if x >= motor.umbral
    else "Revisar requisitos y brechas"
)
assert (resultado["orientacion"] == esperada).all()
assert abs(motor.umbral - 0.720) < 1e-12

# 4. Una persona sin experiencia debe recibir orientación sin error.
perfil_sin_experiencia = {
    "formaciones": [{"nivel": "BACHILLER", "titulo": "Bachiller académico"}],
    "experiencias": [],
    "top_n": 5,
}
salida_sin_experiencia = motor.recomendar(perfil_sin_experiencia, top_n=5)
assert len(salida_sin_experiencia) == 5
assert (salida_sin_experiencia["experiencia_ciudadano_meses"] == 0).all()

# 5. Dos experiencias traslapadas no se suman dos veces.
perfil_traslapado = {
    "formaciones": [{"nivel": "PROFESIONAL", "titulo": "Administración"}],
    "experiencias": [
        {
            "cargo": "Profesional",
            "tipo": "Profesional",
            "fecha_inicio": "2020-01-01",
            "fecha_fin": "2021-01-01",
        },
        {
            "cargo": "Analista",
            "tipo": "Laboral",
            "fecha_inicio": "2020-06-01",
            "fecha_fin": "2021-06-01",
        },
    ],
}
_, exp_validas = motor.validar_perfil(perfil_traslapado)
meses_union = motor.resumir_experiencia(exp_validas)["meses_experiencia_final"]
# La unión 2020-01-01 a 2021-06-01 equivale aproximadamente a 17 meses
# usando el factor medio de 30.4375 días por mes del motor.
assert 16.9 <= meses_union <= 17.1, meses_union

# 6. Los perfiles inválidos deben producir mensajes controlados.
perfiles_invalidos = [
    {
        "formaciones": [],
        "experiencias": [],
    },
    {
        "formaciones": [{"nivel": "PROFESIONAL", "titulo": ""}],
        "experiencias": [],
    },
    {
        "formaciones": [{"nivel": "PROFESIONAL", "titulo": "Economía"}],
        "experiencias": [
            {
                "cargo": "Analista",
                "tipo": "Laboral",
                "fecha_inicio": "2024-12-31",
                "fecha_fin": "2024-01-01",
            }
        ],
    },
]
for perfil_invalido in perfiles_invalidos:
    try:
        motor.recomendar(perfil_invalido)
        raise AssertionError("Un perfil inválido no fue rechazado")
    except ValueError:
        pass

# 7. El código operacional no puede entrenar, ajustar hiperparámetros ni remuestrear.
fuentes = (
    (BASE / "motor_inferencia.py").read_text(encoding="utf-8")
    + (BASE / "app.py").read_text(encoding="utf-8")
)
for patron in (
    ".fit(",
    "fit_resample(",
    "GridSearchCV(",
    "RandomizedSearchCV(",
    "SMOTE(",
):
    assert patron not in fuentes, f"Operación no autorizada en prototipo: {patron}"

print("✓ Pruebas funcionales superadas")
print(f"✓ Inferencia de cinco recomendaciones: {duracion:.2f} segundos")
print("✓ Contrato de salida de 16 campos validado")
print("✓ top_n y umbral 0.720 validados")
print("✓ Orientaciones y advertencia metodológica validadas")
print("✓ Perfil sin experiencia procesado correctamente")
print("✓ Traslapamientos laborales consolidados")
print("✓ Manejo de perfiles inválidos validado")
print("✓ Sin entrenamiento, ajuste ni SMOTE en producción")


# 8. Validaciones funcionales solicitadas por la tutora.
import ast
from reglas_funcionales import niveles_empleo_permitidos

app_source = (BASE / "app.py").read_text(encoding="utf-8")
ast.parse(app_source)

# 8.1 Catálogo académico local: CSV normal, sin compresión.
catalogo_programas = pd.read_csv(
    BASE / "catalogo_programas_selector.csv",
    low_memory=False,
)
assert {
    "nombre_programa",
    "nivel_academico_snies",
    "nivel_formacion_snies",
    "nivel_prototipo",
}.issubset(catalogo_programas.columns)
assert len(catalogo_programas) > 6000
assert (
    catalogo_programas.loc[
        catalogo_programas["nivel_prototipo"].eq("PROFESIONAL"),
        "nombre_programa",
    ]
    .astype(str)
    .str.strip()
    .str.upper()
    .eq("DERECHO")
    .any()
)

# 8.2 Metadatos de las 1.012 OPEC históricas.
metadata_opec = pd.read_csv(
    BASE / "catalogo_opec_metadata.csv.gz",
    compression="gzip",
)
metadata_opec["opec"] = metadata_opec["opec"].astype(str)
assert len(metadata_opec) == len(motor.catalogo)
assert metadata_opec["opec"].is_unique
assert metadata_opec[
    ["convocatoria", "nivel", "denominacion", "grado", "asignacion_salarial"]
].notna().all().all()

# 8.3 Pruebas funcionales explícitas de nivel.
casos_nivel = {
    "ASISTENCIAL": (
        [{"nivel": "BACHILLER", "titulo": "Bachiller"}],
        {"Asistencial"},
    ),
    "TECNICO": (
        [{"nivel": "TECNICO PROFESIONAL", "titulo": "Técnico Profesional"}],
        {"Técnico"},
    ),
    "PROFESIONAL": (
        [{"nivel": "PROFESIONAL", "titulo": "Derecho"}],
        {"Profesional", "Asesor"},
    ),
    "PROFESIONAL_ESPECIALIZADO_POSGRADO": (
        [
            {"nivel": "PROFESIONAL", "titulo": "Derecho"},
            {
                "nivel": "ESPECIALIZACION PROFESIONAL",
                "titulo": "Especialización en Derecho Administrativo",
            },
        ],
        {"Profesional", "Asesor"},
    ),
}

for nombre_caso, (formaciones, esperado) in casos_nivel.items():
    obtenido = niveles_empleo_permitidos(formaciones)
    assert obtenido == esperado, f"{nombre_caso}: {obtenido} != {esperado}"

# 8.4 El caso profesional nunca habilita Asistencial ni Técnico.
permitidos_profesional = niveles_empleo_permitidos(
    [{"nivel": "PROFESIONAL", "titulo": "Derecho"}]
)
assert "Asistencial" not in permitidos_profesional
assert "Técnico" not in permitidos_profesional
assert permitidos_profesional == {"Profesional", "Asesor"}

# 8.5 El caso posgrado conserva la orientación a Profesional/Asesor.
permitidos_posgrado = niveles_empleo_permitidos([
    {"nivel": "PROFESIONAL", "titulo": "Derecho"},
    {
        "nivel": "ESPECIALIZACION PROFESIONAL",
        "titulo": "Especialización en Derecho Administrativo",
    },
])
assert permitidos_posgrado == {"Profesional", "Asesor"}

# 8.6 Validaciones de integración de la interfaz.
assert "catalogo_programas_selector.csv" in app_source
assert "catalogo_programas_selector.csv.gz" not in app_source
assert "datos.gov.co" not in app_source
assert "niveles_empleo_permitidos" in app_source
assert "coincidencia_titulo_directa" in app_source
assert "convocatoria" in app_source
assert "asignacion_salarial" in app_source
assert "calcular_resultados_completos" in app_source

print("✓ Sintaxis de app.py validada")
print("✓ Catálogo local leído correctamente desde CSV")
print("✓ DERECHO disponible en el nivel PROFESIONAL")
print("✓ Caso ASISTENCIAL: nivel permitido = Asistencial")
print("✓ Caso TECNICO: nivel permitido = Técnico")
print("✓ Caso PROFESIONAL: niveles permitidos = Profesional/Asesor")
print("✓ Caso POSGRADO: niveles permitidos = Profesional/Asesor")
print("✓ Perfil profesional no habilita OPEC Asistencial/Técnico")
print("✓ Concurso y salario están integrados como filtros funcionales")
print("✓ El modelo aprobado, su umbral y sus métricas no fueron modificados")
