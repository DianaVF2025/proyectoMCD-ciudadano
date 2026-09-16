from pathlib import Path
import json
import re
import unicodedata

import pandas as pd
import streamlit as st

from motor_inferencia import MotorRecomendacionCNSC, ADVERTENCIA

st.set_page_config(page_title="Orientador de oportunidades laborales públicas", page_icon="🧭", layout="wide")
BASE_DIR = Path(__file__).resolve().parent

@st.cache_resource
def cargar_motor():
    return MotorRecomendacionCNSC(BASE_DIR / "paquete_modelo_cnsc_v1.joblib")

def normalizar_para_coincidencia(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "").lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()

def nueva_formacion(): return {"nivel": "PROFESIONAL", "titulo": ""}
def nueva_experiencia(): return {"cargo": "", "empresa": "", "funciones": "", "tipo": "Profesional", "fecha_inicio": "", "fecha_fin": ""}

def inicializar_estado():
    if "formaciones" not in st.session_state: st.session_state.formaciones = [nueva_formacion()]
    if "experiencias" not in st.session_state: st.session_state.experiencias = [nueva_experiencia()]

def render_formaciones():
    st.markdown("### 🎓 1. Cuéntanos sobre tu formación")
    st.caption("Registra tu nivel académico y el nombre de tu título o programa. Puedes agregar más de una formación.")
    niveles=["BACHILLER","TECNICO PROFESIONAL","TECNOLOGICO","PROFESIONAL","ESPECIALIZACION PROFESIONAL","MAESTRIA","DOCTORADO"]
    for i,f in enumerate(st.session_state.formaciones):
        with st.container(border=True):
            c1,c2=st.columns([1,2]); actual=f.get("nivel","PROFESIONAL")
            f["nivel"]=c1.selectbox("Nivel académico",niveles,index=niveles.index(actual) if actual in niveles else 3,key=f"nivel_{i}")
            f["titulo"]=c2.text_input("Título o programa académico",value=f.get("titulo",""),placeholder="Ej. Ingeniería Industrial, Matemáticas o Medicina Veterinaria",key=f"titulo_{i}")
            if len(st.session_state.formaciones)>1 and st.button("Eliminar formación",key=f"del_form_{i}"): st.session_state.formaciones.pop(i); st.rerun()
    if st.button("＋ Agregar otra formación"): st.session_state.formaciones.append(nueva_formacion()); st.rerun()

def render_experiencias():
    st.markdown("### 💼 2. Cuéntanos sobre tu experiencia")
    st.caption("Registra tu experiencia de forma objetiva: cargo, entidad o empresa, funciones y fechas. El prototipo no te pide decidir si una experiencia es relacionada o específica.")
    tipos=["Profesional","Docente","Laboral","Otra"]
    for i,e in enumerate(st.session_state.experiencias):
        with st.container(border=True):
            c1,c2=st.columns(2); e["cargo"]=c1.text_input("Cargo",value=e.get("cargo",""),key=f"cargo_{i}"); e["empresa"]=c2.text_input("Entidad / empresa",value=e.get("empresa",""),key=f"empresa_{i}")
            e["funciones"]=st.text_area("Funciones principales",value=e.get("funciones",""),placeholder="Describe brevemente las principales funciones realizadas",key=f"funciones_{i}")
            c3,c4,c5=st.columns(3); actual=e.get("tipo","Profesional"); actual=actual if actual in tipos else "Profesional"
            e["tipo"]=c3.selectbox("Tipo de experiencia",tipos,index=tipos.index(actual),help="Selecciona únicamente la naturaleza general de la experiencia.",key=f"tipo_{i}")
            e["fecha_inicio"]=c4.text_input("Fecha de inicio",value=e.get("fecha_inicio",""),placeholder="AAAA-MM-DD",key=f"inicio_{i}"); e["fecha_fin"]=c5.text_input("Fecha de finalización",value=e.get("fecha_fin",""),placeholder="AAAA-MM-DD o vacío si continúa",key=f"fin_{i}")
            if st.button("Eliminar experiencia",key=f"del_exp_{i}"): st.session_state.experiencias.pop(i); st.rerun()
    if st.button("＋ Agregar otra experiencia"): st.session_state.experiencias.append(nueva_experiencia()); st.rerun()

def construir_perfil():
    fs=[{"nivel":f["nivel"],"titulo":f["titulo"].strip()} for f in st.session_state.formaciones if f.get("titulo","").strip()]; es=[]
    for e in st.session_state.experiencias:
        cargo,func=e.get("cargo","").strip(),e.get("funciones","").strip()
        if cargo or func: es.append({"cargo":cargo,"empresa":e.get("empresa","").strip(),"funciones":func,"tipo":e.get("tipo","Profesional"),"fecha_inicio":e.get("fecha_inicio","").strip(),"fecha_fin":e.get("fecha_fin","").strip() or None})
    return {"formaciones":fs,"experiencias":es}

def obtener_rutas_originales(motor,opec):
    c=motor.catalogo[motor.catalogo["opec"].astype(str)==str(opec)]
    if c.empty:return []
    rutas=c.iloc[0].get("rutas_requisitos",[])
    if isinstance(rutas,str):
        try:rutas=json.loads(rutas)
        except json.JSONDecodeError:return []
    return rutas if isinstance(rutas,list) else []

def componentes_alternativas(motor,opec):
    salida=[]
    for i,ruta in enumerate(obtener_rutas_originales(motor,opec),start=1):
        for clave,etiqueta in (("requisito_principal","Requisito principal"),("requisito_alternativo","Requisito alternativo")):
            req=(ruta or {}).get(clave,{}) or {}; estudio=str(req.get("estudio") or "").strip(); exp=str(req.get("experiencia") or "").strip(); meses=req.get("tiempomin")
            if estudio or exp or meses not in (None,""):salida.append({"numero":i,"tipo":etiqueta,"estudio":estudio,"experiencia":exp,"meses":meses})
    return salida

def coincidencia_componente(c,formaciones):
    req=normalizar_para_coincidencia(c.get("estudio",""))
    return any((t:=normalizar_para_coincidencia(f.get("titulo",""))) and t in req for f in formaciones)

def coincidencia_directa_titulo(motor,opec,formaciones): return any(coincidencia_componente(c,formaciones) for c in componentes_alternativas(motor,opec))

def aplicar_priorizacion_formacion(resultado,motor,formaciones,top_n):
    if resultado.empty:return resultado
    df=resultado.copy(); df["coincidencia_titulo_directa"]=df["opec"].apply(lambda x:coincidencia_directa_titulo(motor,x,formaciones)); df=pd.concat([df[df["coincidencia_titulo_directa"]],df[~df["coincidencia_titulo_directa"]]],ignore_index=True).head(top_n).copy(); df["posicion"]=range(1,len(df)+1); return df

def mostrar_contraste(motor,opec,formaciones,meses_ciudadano):
    comps=componentes_alternativas(motor,opec); identificados=[c for c in comps if coincidencia_componente(c,formaciones)]; titulos=", ".join(f.get("titulo","") for f in formaciones if f.get("titulo","").strip()) or "No registrada"
    st.markdown("#### 🔎 Tu perfil frente a los requisitos de la OPEC")
    st.caption("Este contraste es informativo y no modifica el índice de compatibilidad histórica.")
    izquierda,derecha=st.columns(2)
    with izquierda:
        with st.container(border=True):
            st.markdown("##### 👤 Tu perfil registrado"); st.write(f"**🎓 Formación:** {titulos}"); st.write(f"**💼 Experiencia total:** {meses_ciudadano:.1f} meses")
    with derecha:
        with st.container(border=True):
            st.markdown(f"##### 📋 Requisitos de la OPEC {opec}")
            if identificados:
                c=identificados[0]; st.write(f"**🎓 Formación registrada:** {c['estudio'] or 'No especificada'}"); st.write(f"**💼 Experiencia registrada:** {c['experiencia'] or 'No especificada'}")
                if c["meses"] not in (None,""): st.write(f"**⏱️ Tiempo mínimo:** {c['meses']} meses")
            elif comps:
                c=comps[0]; st.write(f"**🎓 Formación registrada:** {c['estudio'] or 'No especificada'}"); st.write(f"**💼 Experiencia registrada:** {c['experiencia'] or 'No especificada'}")
                if c["meses"] not in (None,""): st.write(f"**⏱️ Tiempo mínimo:** {c['meses']} meses")
            else: st.write("No se encontraron requisitos disponibles en el catálogo histórico.")
    with st.container(border=True):
        st.markdown("##### Resultado del contraste")
        if identificados: st.success("🎓 **Formación:** coincidencia textual directa identificada en al menos una alternativa académica registrada.")
        else: st.info("🎓 **Formación:** no se identificó coincidencia textual directa con las alternativas académicas registradas.")
        candidatos=identificados if identificados else comps
        if candidatos:
            c=candidatos[0]
            try:
                req=float(c["meses"])
                if req==0: st.info("💼 **Experiencia:** esta alternativa registra 0 meses como tiempo mínimo. Esto no determina el cumplimiento de los demás requisitos.")
                elif meses_ciudadano>=req: st.info(f"💼 **Experiencia:** el perfil registra {meses_ciudadano:.1f} meses y la alternativa indica {req:.1f} meses como mínimo. Si exige experiencia relacionada o específica, deben revisarse también las funciones.")
                else: st.warning(f"💼 **Experiencia:** el perfil registra {meses_ciudadano:.1f} meses y la alternativa indica {req:.1f} meses como mínimo. El tiempo registrado es inferior al indicado.")
            except (TypeError,ValueError): pass
    with st.expander("Ver todas las alternativas de requisitos registradas"):
        if not comps: st.write("No se encontraron requisitos para esta oportunidad en el catálogo histórico.")
        for c in comps:
            marca=" · coincidencia académica identificada" if coincidencia_componente(c,formaciones) else ""
            st.markdown(f"**Opción de requisitos {c['numero']} · {c['tipo']}{marca}**")
            if c["estudio"]: st.write(f"Estudios: {c['estudio']}")
            if c["experiencia"]: st.write(f"Experiencia: {c['experiencia']}")
            if c["meses"] not in (None,""): st.write(f"Tiempo mínimo registrado: {c['meses']} meses")
            st.divider()

def mostrar_resultados(resultado,motor,formaciones):
    if resultado.empty: st.warning("No se encontraron oportunidades para el perfil registrado."); return
    df=resultado.copy(); df["indice_compatibilidad_pct"]=(df["indice_compatibilidad"]*100).round(1); df["experiencia_ciudadano_meses"]=df["experiencia_ciudadano_meses"].round(1)
    if "coincidencia_titulo_directa" not in df: df["coincidencia_titulo_directa"]=False
    cantidad=int(df["coincidencia_titulo_directa"].sum()); st.success(f"Encontramos {len(df)} oportunidades para explorar. En {cantidad} se identificó además coincidencia académica directa en al menos una alternativa registrada.")
    st.info("💡 **Cómo leer tus resultados:** la compatibilidad histórica es el resultado principal del modelo aprobado. El contraste de requisitos te ayuda a interpretar cada oportunidad antes de postularte.")
    vista=df[["posicion","opec","descripcion","indice_compatibilidad_pct","coincidencia_titulo_directa"]].rename(columns={"posicion":"Posición","opec":"OPEC","descripcion":"Oportunidad","indice_compatibilidad_pct":"Compatibilidad histórica (%)","coincidencia_titulo_directa":"Formación"}); vista["Formación"]=vista["Formación"].map({True:"Coincidencia identificada",False:"Sin coincidencia directa"})
    st.markdown("### 🎯 Oportunidades orientadas por compatibilidad"); st.caption("El índice conserva exactamente la salida del modelo predictivo aprobado. No es un porcentaje de cumplimiento de requisitos."); st.dataframe(vista,use_container_width=True,hide_index=True)
    st.markdown("### 📌 Explora cada oportunidad")
    for _,rec in df.iterrows():
        with st.expander(f"#{int(rec['posicion'])} · OPEC {rec['opec']} · Compatibilidad histórica {rec['indice_compatibilidad_pct']:.1f}%"):
            c1,c2,c3=st.columns([1,1,1.4]); c1.metric("🎯 Compatibilidad histórica",f"{rec['indice_compatibilidad_pct']:.1f}%"); c2.metric("💼 Experiencia registrada",f"{rec['experiencia_ciudadano_meses']:.1f} meses")
            with c3:
                st.info("El índice es generado por el modelo aprobado a partir de patrones históricos. **No representa porcentaje de cumplimiento ni probabilidad de selección.**")
            with st.expander("ⓘ ¿Qué significa la compatibilidad histórica?"):
                st.write("El modelo considera conjuntamente múltiples variables históricas del perfil y de la oportunidad. Por ello, una OPEC puede presentar un índice alto sin coincidencia académica directa, mientras otra puede presentar coincidencia académica y un índice menor. El valor final no se atribuye a una sola variable.")
            st.write(f"**📄 Descripción de la oportunidad:** {rec.get('descripcion','')}")
            mostrar_contraste(motor,rec["opec"],formaciones,float(rec["experiencia_ciudadano_meses"]))
            st.warning("⚠️ **Antes de postularte:** revisa los requisitos completos de la convocatoria. Este contraste es orientativo y no constituye una verificación oficial de cumplimiento.")
            st.caption(rec.get("advertencia",ADVERTENCIA))

def main():
    inicializar_estado(); motor=cargar_motor()
    st.title("🧭 Orientador de oportunidades laborales del sector público")
    st.markdown("#### Encuentra oportunidades con mayor compatibilidad histórica con tu perfil")
    st.write("Registra tu formación y experiencia. El modelo predictivo aprobado analizará tu perfil y organizará las oportunidades OPEC para ayudarte a identificar cuáles explorar primero.")
    with st.expander("ⓘ ¿Qué significa compatibilidad histórica?"):
        st.write("Es el índice generado por el modelo predictivo aprobado a partir de patrones históricos y múltiples características del perfil y de las oportunidades. Sirve para orientar la búsqueda; no es una probabilidad de selección ni un porcentaje de cumplimiento de requisitos.")
    with st.sidebar:
        st.header("Acerca del prototipo"); st.write("Proyecto académico de Maestría en Ciencia de Datos."); st.write(f"**Modelo:** {motor.metadata.get('nombre_modelo',motor.metadata.get('modelo_seleccionado','No especificado'))}"); st.write(f"**Versión:** {motor.metadata.get('version',motor.metadata.get('version_modelo','v1'))}"); st.caption("El modelo, sus vectorizadores, variables, umbral y métricas aprobadas permanecen congelados.")
    st.divider(); render_formaciones(); st.divider(); render_experiencias(); st.divider()
    st.markdown("### 🔎 3. Consulta tus oportunidades")
    st.write("El modelo comparará tu perfil con las oportunidades disponibles y las organizará según su **índice de compatibilidad histórica**.")
    top_n=st.slider("Número de oportunidades a mostrar",1,20,10)
    if st.button("🔎 Consultar oportunidades compatibles",type="primary",use_container_width=True):
        try:
            perfil=construir_perfil(); resultado_modelo=motor.recomendar(perfil,top_n=len(motor.catalogo)); resultado=aplicar_priorizacion_formacion(resultado_modelo,motor,perfil["formaciones"],top_n); mostrar_resultados(resultado,motor,perfil["formaciones"])
        except Exception as exc: st.error(f"No fue posible generar la orientación: {exc}")

if __name__=="__main__": main()
