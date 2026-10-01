"""Reglas funcionales de presentación del prototipo ciudadano.

Estas reglas no modifican el modelo predictivo, sus variables, vectorizadores,
umbral ni métricas. Únicamente restringen los niveles de empleo que se muestran
según el nivel académico declarado por el ciudadano.
"""

JERARQUIA_ACADEMICA = {
    "EDUCACION BASICA PRIMARIA": 1,
    "EDUCACION BASICA SECUNDARIA": 2,
    "BACHILLER": 3,
    "NORMALISTA": 4,
    "TECNICO PROFESIONAL": 5,
    "TECNOLOGICO": 6,
    "PROFESIONAL": 7,
    "ESPECIALIZACION PROFESIONAL": 10,
    "MAESTRIA": 11,
    "DOCTORADO": 12,
    "POSTDOCTORADO": 13,
}


def jerarquia_perfil(formaciones):
    return max(
        (
            JERARQUIA_ACADEMICA.get(
                str(f.get("nivel", "")).upper(),
                0,
            )
            for f in formaciones
        ),
        default=0,
    )


def niveles_empleo_permitidos(formaciones):
    """Niveles de empleo permitidos para presentación en el prototipo."""
    nivel = jerarquia_perfil(formaciones)

    if nivel >= 7:
        return {"Profesional", "Asesor"}

    if nivel in (5, 6):
        return {"Técnico"}

    if nivel in (1, 2, 3, 4):
        return {"Asistencial"}

    return set()
