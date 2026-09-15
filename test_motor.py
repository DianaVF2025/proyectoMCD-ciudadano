import json
import time
from pathlib import Path

from motor_inferencia import MotorRecomendacionCNSC

BASE = Path(__file__).resolve().parent
motor = MotorRecomendacionCNSC(BASE / "paquete_modelo_cnsc_v1.joblib")
perfil = json.loads((BASE / "ejemplo_perfil.json").read_text(encoding="utf-8"))

inicio = time.perf_counter()
resultado = motor.recomendar(perfil, top_n=5)
duracion = time.perf_counter() - inicio
assert len(resultado) == 5
assert resultado["opec"].is_unique
assert resultado["indice_compatibilidad"].between(0, 1).all()
assert resultado["indice_compatibilidad"].is_monotonic_decreasing
assert resultado["advertencia"].str.contains("No es una probabilidad").all()
assert duracion < 60

# Una persona sin experiencia debe recibir orientación sin error.
perfil_sin_experiencia = {
    "formaciones": [{"nivel": "BACHILLER", "titulo": "Bachiller académico"}],
    "experiencias": [], "top_n": 5
}
assert len(motor.recomendar(perfil_sin_experiencia, top_n=5)) == 5

# Dos experiencias traslapadas no se suman dos veces.
perfil_traslapado = {
    "formaciones": [{"nivel": "PROFESIONAL", "titulo": "Administración"}],
    "experiencias": [
        {"cargo": "Profesional", "tipo": "Experiencia profesional",
         "fecha_inicio": "2020-01-01", "fecha_fin": "2021-01-01"},
        {"cargo": "Analista", "tipo": "Experiencia laboral",
         "fecha_inicio": "2020-06-01", "fecha_fin": "2021-06-01"}
    ]
}
_, exp_validas = motor.validar_perfil(perfil_traslapado)
meses_union = motor.resumir_experiencia(exp_validas)["meses_experiencia_final"]
# La unión 2020-01-01 a 2021-06-01 equivale aproximadamente a 17 meses
# usando el factor medio de 30.4375 días por mes del motor.
assert 16.9 <= meses_union <= 17.1, meses_union

# Las fechas imposibles deben producir un mensaje controlado.
perfil_invalido = {
    "formaciones": [{"nivel": "PROFESIONAL", "titulo": "Economía"}],
    "experiencias": [{"cargo": "Analista", "tipo": "Laboral",
                       "fecha_inicio": "2024-12-31", "fecha_fin": "2024-01-01"}]
}
try:
    motor.recomendar(perfil_invalido)
    raise AssertionError("La fecha imposible no fue rechazada")
except ValueError:
    pass

# El código operacional no puede entrenar ni remuestrear.
fuentes = (
    (BASE / "motor_inferencia.py").read_text(encoding="utf-8")
    + (BASE / "app.py").read_text(encoding="utf-8")
)
for patron in (".fit(", "fit_resample(", "GridSearchCV(", "RandomizedSearchCV(", "SMOTE("):
    assert patron not in fuentes, f"Operación no autorizada en prototipo: {patron}"

print("✓ Pruebas funcionales superadas")
print(f"✓ Inferencia de cinco recomendaciones: {duracion:.2f} segundos")
print("✓ Traslapamientos laborales consolidados")
print("✓ Manejo de errores validado")
print("✓ Sin entrenamiento ni SMOTE en producción")
