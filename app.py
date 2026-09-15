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
    """Carga únicamente el paquete congelado aprobado para inferencia."""
    return MotorRecomendacionCNSC(BASE_DIR / "paquete_modelo_cnsc_v1.joblib")


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
    niveles = [
        "BACHILLER", "TECNICO PROFESIONAL", "TECNOLOGICO", "PROFESIONAL",
        "ESPECIALIZACION PROFESIONAL", "MAESTRIA", "DOCTORADO"
    ]

    for i, formacion in enumerate(st.session_state.formaciones):
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            nivel_actual = formacion.get("nivel", "PROFESIONAL")
            indice = niveles.index(nivel_actual) if nivel_actual in niveles else niveles.index("PROFESIONAL")
            formacion["nivel"] = c1.selectbox("Nivel", niveles, index=indice, key=f"nivel_{i}")
            formacion["titulo"] = c2.text_input(
                "Título / programa",
                value=formacion.get("titulo", ""),
                placeholder="Ej. Ingeniería Industrial",
                key=f"titulo_{i}",
            )
            if len(st.session_state.formaciones) > 1 and st.button("Eliminar formación", key=f"del_form_{i}"):
                st.session_state.formaciones.pop(i)
                st.rerun()

    if st.button("+ Agregar otra formación"):
        st.session_state.formaciones.append(nueva_formacion())
        st.rerun()


def render_experiencias():
    st.subheader("2. Experiencia laboral")
    st.caption("La experiencia es opcional. Si registra una, indique cargo y fecha de inicio.")
    tipos = ["Profesional", "Profesional relacionada", "Relacionada", "Específica", "Docente", "Laboral", "Otra"]

    for i, experiencia in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1, c2 = st.columns(2)
            experiencia["cargo"] = c1.text_input("Cargo", value=experiencia.get("cargo", ""), placeholder="Ej. Profesional especializado", key=f"cargo_{i}")
            experiencia["empresa"] = c2.text_input("Entidad / empresa", value=experiencia.get("empresa", ""), placeholder="Ej. Entidad pública", key=f"empresa_{i}")
            experiencia["funciones"] = st.text_area("Funciones principales", value=experiencia.get("funciones", ""), placeholder="Describa brevemente sus funciones y responsabilidades.", key=f"funciones_{i}")
            c3, c4, c5 = st.columns(3)
            tipo_actual = experiencia.get("tipo", "Profesional")
            indice_tipo = tipos.index(tipo_actual) if tipo_actual in tipos else 0
            experiencia["tipo"] = c3.selectbox("Tipo de experiencia", tipos, index=indice_tipo, key=f"tipo_{i}")
            experiencia["fecha_inicio"] = c4.text_input("Fecha inicio", value=experiencia.get("fecha_inicio", ""), placeholder="AAAA-MM-DD", key=f"inicio_{i}")
            experiencia["fecha_fin"] = c5.text_input("Fecha fin", value=experiencia.get("fecha_fin", ""), placeholder="AAAA-MM-DD o vacío", key=f"fin_{i}")
            if st.button("Eliminar experiencia", key=f"del_exp_{i}"):
                st.session_state.experiencias.pop(i)
                st.rerun()

    if st.button("+ Agregar otra experiencia"):
        st.session_state.experiencias.append(nueva_experiencia())
        st.rerun()


def construir_perfil():
    formaciones = [
        {"nivel": f["nivel"], "titulo": f["titulo"].strip()}
        for f in st.session_state.formaciones
        if f.get("titulo", "").strip()
    ]

    experiencias = []
    for e in st.session_state.experiencias:
        cargo = e.get("cargo", "").strip()
        funciones = e.get("funciones", "").strip()
        if cargo or funciones:
            experiencias.append({
                "cargo": cargo,
                "empresa": e.get("empresa", "").strip(),
                "funciones": funciones,
                "tipo": e.get("tipo", "Profesional"),
                "fecha_inicio": e.get("fecha_inicio", "").strip(),
                "fecha_fin": e.get("fecha_fin", "").strip() or None,
            })
    return {"formaciones": formaciones, "experiencias": experiencias}


def mostrar_resultados(resultado: pd.DataFrame):
    """Presenta exactamente la salida producida por MotorRecomendacionCNSC.recomendar()."""
    st.success(f"Se generaron {len(resultado)} recomendaciones orientativas del catálogo histórico del prototipo.")
    st.info(ADVERTENCIA)

    if resultado.empty:
        st.warning("No se generaron recomendaciones para el perfil registrado.")
        return

    df = resultado.copy()
    df["indice_compatibilidad_pct"] = (df["indice_compatibilidad"] * 100).round(1)
    df["brecha_meses"] = df["brecha_meses"].round(1)
    df["experiencia_ciudadano_meses"] = df["experiencia_ciudadano_meses"].round(1)

    columnas = [
        "posicion", "opec", "descripcion", "indice_compatibilidad_pct",
        "orientacion", "tipo_ruta", "meses_requeridos", "brecha_meses"
    ]
    columnas = [c for c in columnas if c in df.columns]
    vista = df[columnas].rename(columns={
        "posicion": "Posición",
        "opec": "OPEC",
        "descripcion": "Descripción",
        "indice_compatibilidad_pct": "Índice de compatibilidad (%)",
        "orientacion": "Orientación",
        "tipo_ruta": "Ruta evaluada",
        "meses_requeridos": "Meses requeridos",
        "brecha_meses": "Brecha de experiencia (meses)",
    })

    st.subheader("Oportunidades recomendadas")
    st.dataframe(vista, use_container_width=True, hide_index=True)

    st.subheader("Detalle de las recomendaciones")
    for _, rec in df.iterrows():
        titulo = f"#{int(rec['posicion'])} · OPEC {rec['opec']} · {rec['indice_compatibilidad_pct']:.1f}%"
        with st.expander(titulo):
            c1, c2, c3 = st.columns(3)
            c1.metric("Índice de compatibilidad", f"{rec['indice_compatibilidad_pct']:.1f}%")
            c2.metric("Experiencia registrada", f"{rec['experiencia_ciudadano_meses']:.1f} meses")
            c3.metric("Brecha de experiencia", f"{rec['brecha_meses']:.1f} meses")
            st.write(f"**Descripción:** {rec.get('descripcion', '')}")
            st.write(f"**Orientación:** {rec.get('orientacion', '')}")
            st.write(f"**Ruta evaluada:** {rec.get('tipo_ruta', '')} — ruta {rec.get('numero_ruta', '')}")
            st.write(f"**Requisito de estudio:** {rec.get('requisito_estudio', '')}")
            st.write(f"**Requisito de experiencia:** {rec.get('requisito_experiencia', '')}")
            st.write(f"**Meses requeridos:** {rec.get('meses_requeridos', 0):.1f}")
            st.write(f"**Similitud académica:** {rec.get('similitud_academica', 0):.3f}")
            st.write(f"**Similitud de experiencia:** {rec.get('similitud_experiencia', 0):.3f}")
            st.caption(rec.get("advertencia", ADVERTENCIA))


def main():
    inicializar_estado()
    motor = cargar_motor()

    st.title("🧭 Orientador de oportunidades laborales públicas")
    st.write(
        "Ingrese su formación y experiencia. El prototipo compara su perfil con un catálogo histórico OPEC "
        "y presenta un ranking orientativo mediante un índice de compatibilidad."
    )
    st.warning(ADVERTENCIA)

    with st.sidebar:
        st.header("Acerca del prototipo")
        st.write("Proyecto académico de Maestría en Ciencia de Datos.")
        st.write(f"**Modelo:** {motor.metadata.get('nombre_modelo', motor.metadata.get('modelo_seleccionado', 'No especificado'))}")
        st.write(f"**Versión:** {motor.metadata.get('version', motor.metadata.get('version_modelo', 'v1'))}")
        st.write(f"**Catálogo:** {motor.metadata.get('catalogo', 'Histórico OPEC 2024')}")
        st.caption("La información oficial y los requisitos deben verificarse siempre en las fuentes de la CNSC.")

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
