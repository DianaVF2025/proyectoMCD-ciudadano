from pathlib import Path
import json

import pandas as pd
import streamlit as st

from motor_inferencia import MotorRecomendacionCNSC, ADVERTENCIA


st.set_page_config(
    page_title="Orientador de vacantes CNSC",
    page_icon="🧭",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent


@st.cache_resource
def cargar_motor():
    return MotorRecomendacionCNSC(
        ruta_paquete=BASE_DIR / "paquete_modelo_cnsc_v1.joblib",
        ruta_catalogo=BASE_DIR / "catalogo_opec_prototipo.joblib",
        ruta_metadata=BASE_DIR / "metadata_modelo.json",
    )


def nueva_formacion():
    return {"nivel": "PROFESIONAL", "titulo": ""}


def nueva_experiencia():
    return {
        "cargo": "",
        "empresa": "",
        "funciones": "",
        "tipo": "Profesional",
        "fecha_inicio": "",
        "fecha_fin": "",
    }


def inicializar_estado():
    if "formaciones" not in st.session_state:
        st.session_state.formaciones = [nueva_formacion()]
    if "experiencias" not in st.session_state:
        st.session_state.experiencias = [nueva_experiencia()]


def render_formaciones():
    st.subheader("1. Formación académica")
    st.caption("Registre al menos una formación. Puede agregar varias.")
    niveles = ["BACHILLER", "TECNICO", "TECNOLOGO", "PROFESIONAL", "ESPECIALIZACION", "MAESTRIA", "DOCTORADO"]

    for i, formacion in enumerate(st.session_state.formaciones):
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            nivel_actual = formacion.get("nivel", "PROFESIONAL")
            indice = niveles.index(nivel_actual) if nivel_actual in niveles else niveles.index("PROFESIONAL")
            formacion["nivel"] = c1.selectbox(
                "Nivel",
                niveles,
                index=indice,
                key=f"nivel_{i}",
            )
            formacion["titulo"] = c2.text_input(
                "Título / programa",
                value=formacion.get("titulo", ""),
                placeholder="Ej. Ingeniería Industrial",
                key=f"titulo_{i}",
            )
            if len(st.session_state.formaciones) > 1:
                if st.button("Eliminar formación", key=f"del_form_{i}"):
                    st.session_state.formaciones.pop(i)
                    st.rerun()

    if st.button("+ Agregar otra formación"):
        st.session_state.formaciones.append(nueva_formacion())
        st.rerun()


def render_experiencias():
    st.subheader("2. Experiencia laboral")
    st.caption("Registre sus experiencias laborales. La fecha final puede dejarse vacía si el empleo está vigente.")
    tipos = ["Profesional", "Relacionada", "General", "Docente", "Otra"]

    for i, experiencia in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1, c2 = st.columns(2)
            experiencia["cargo"] = c1.text_input(
                "Cargo",
                value=experiencia.get("cargo", ""),
                placeholder="Ej. Profesional especializado",
                key=f"cargo_{i}",
            )
            experiencia["empresa"] = c2.text_input(
                "Entidad / empresa",
                value=experiencia.get("empresa", ""),
                placeholder="Ej. Entidad pública",
                key=f"empresa_{i}",
            )
            experiencia["funciones"] = st.text_area(
                "Funciones principales",
                value=experiencia.get("funciones", ""),
                placeholder="Describa brevemente sus funciones y responsabilidades.",
                key=f"funciones_{i}",
            )
            c3, c4, c5 = st.columns(3)
            tipo_actual = experiencia.get("tipo", "Profesional")
            indice_tipo = tipos.index(tipo_actual) if tipo_actual in tipos else 0
            experiencia["tipo"] = c3.selectbox(
                "Tipo de experiencia",
                tipos,
                index=indice_tipo,
                key=f"tipo_{i}",
            )
            experiencia["fecha_inicio"] = c4.text_input(
                "Fecha inicio",
                value=experiencia.get("fecha_inicio", ""),
                placeholder="AAAA-MM-DD",
                key=f"inicio_{i}",
            )
            experiencia["fecha_fin"] = c5.text_input(
                "Fecha fin",
                value=experiencia.get("fecha_fin", ""),
                placeholder="AAAA-MM-DD o vacío",
                key=f"fin_{i}",
            )
            if st.button("Eliminar experiencia", key=f"del_exp_{i}"):
                st.session_state.experiencias.pop(i)
                st.rerun()

    if st.button("+ Agregar otra experiencia"):
        st.session_state.experiencias.append(nueva_experiencia())
        st.rerun()


def construir_perfil():
    formaciones = []
    for f in st.session_state.formaciones:
        if f.get("titulo", "").strip():
            formaciones.append({"nivel": f["nivel"], "titulo": f["titulo"].strip()})

    experiencias = []
    for e in st.session_state.experiencias:
        if e.get("cargo", "").strip() or e.get("funciones", "").strip():
            experiencias.append(
                {
                    "cargo": e.get("cargo", "").strip(),
                    "empresa": e.get("empresa", "").strip(),
                    "funciones": e.get("funciones", "").strip(),
                    "tipo": e.get("tipo", "Profesional"),
                    "fecha_inicio": e.get("fecha_inicio", "").strip(),
                    "fecha_fin": e.get("fecha_fin", "").strip() or None,
                }
            )
    return {"formaciones": formaciones, "experiencias": experiencias}


def mostrar_resultados(resultado):
    st.success(f"Se encontraron {resultado['total_elegibles']} oportunidades elegibles en el catálogo del prototipo.")
    st.info(ADVERTENCIA)

    recomendaciones = resultado.get("recomendaciones", [])
    if not recomendaciones:
        st.warning("No se encontraron vacantes elegibles para el perfil registrado.")
        return

    df = pd.DataFrame(recomendaciones)
    columnas = [
        "codigo_opec",
        "denominacion",
        "entidad",
        "departamento",
        "municipio",
        "nivel",
        "grado",
        "asignacion_basica",
        "indice_compatibilidad",
        "nivel_compatibilidad",
        "cumple_vrm",
    ]
    columnas = [c for c in columnas if c in df.columns]
    st.subheader("Oportunidades recomendadas")
    st.dataframe(df[columnas], use_container_width=True, hide_index=True)

    st.subheader("Detalle")
    for rec in recomendaciones:
        titulo = f"{rec.get('codigo_opec', 'OPEC')} · {rec.get('denominacion', '')} · {rec.get('indice_compatibilidad', 0):.1f}%"
        with st.expander(titulo):
            c1, c2, c3 = st.columns(3)
            c1.metric("Índice de compatibilidad", f"{rec.get('indice_compatibilidad', 0):.1f}%")
            c2.metric("Nivel", rec.get("nivel_compatibilidad", ""))
            c3.metric("VRM", "Cumple" if rec.get("cumple_vrm") else "No cumple")
            st.write(f"**Entidad:** {rec.get('entidad', '')}")
            st.write(f"**Ubicación:** {rec.get('municipio', '')}, {rec.get('departamento', '')}")
            st.write(f"**Nivel / grado:** {rec.get('nivel', '')} / {rec.get('grado', '')}")
            st.write(f"**Asignación básica:** {rec.get('asignacion_basica', '')}")
            st.write(f"**Propósito:** {rec.get('proposito', '')}")
            st.write(f"**Requisitos:** {rec.get('requisitos', '')}")
            st.write(f"**Justificación:** {rec.get('justificacion', '')}")
            st.caption(rec.get("advertencia", ADVERTENCIA))


def main():
    inicializar_estado()
    motor = cargar_motor()

    st.title("🧭 Orientador de oportunidades laborales públicas")
    st.write(
        "Ingrese su formación y experiencia. El prototipo compara su perfil con un catálogo histórico OPEC "
        "y presenta las oportunidades elegibles ordenadas mediante un índice de compatibilidad."
    )
    st.warning(ADVERTENCIA)

    with st.sidebar:
        st.header("Acerca del prototipo")
        st.write("Proyecto académico de Maestría en Ciencia de Datos.")
        st.write(f"**Modelo:** {motor.metadata.get('modelo_seleccionado', 'No especificado')}")
        st.write(f"**Versión:** {motor.metadata.get('version_modelo', 'v1')}")
        st.write(f"**Catálogo:** {motor.metadata.get('catalogo', 'OPEC histórica 2024')}")
        st.caption("La información oficial debe verificarse siempre en las fuentes de la CNSC.")

    render_formaciones()
    render_experiencias()

    st.subheader("3. Generar orientación")
    top_n = st.slider("Número máximo de recomendaciones", min_value=1, max_value=50, value=10)

    if st.button("Calcular índice de compatibilidad", type="primary", use_container_width=True):
        perfil = construir_perfil()
        try:
            resultado = motor.recomendar(perfil, top_n=top_n)
            mostrar_resultados(resultado)
        except Exception as exc:
            st.error(f"No fue posible procesar el perfil: {exc}")

    with st.expander("Ver ejemplo de perfil en JSON"):
        ejemplo = json.loads((BASE_DIR / "ejemplo_perfil.json").read_text(encoding="utf-8"))
        st.json(ejemplo)


if __name__ == "__main__":
    main()
