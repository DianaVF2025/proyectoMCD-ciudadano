from pathlib import Path
import json
import re
import unicodedata

import joblib
import numpy as np
import pandas as pd


ADVERTENCIA = (
    "El índice de compatibilidad es una orientación basada en información "
    "histórica. No es una probabilidad, no garantiza superar la VRM y no "
    "reemplaza la verificación oficial de la CNSC."
)

JERARQUIA_ACADEMICA = {
    "EDUCACION BASICA PRIMARIA": 1, "EDUCACION BASICA SECUNDARIA": 2,
    "BACHILLER": 3, "NORMALISTA": 4, "TECNICO PROFESIONAL": 5,
    "TECNOLOGICO": 6, "PROFESIONAL": 7,
    "ESPECIALIZACION TECNICA PROFESIONAL": 8,
    "ESPECIALIZACION TECNOLOGICA": 9, "ESPECIALIZACION PROFESIONAL": 10,
    "MAESTRIA": 11, "DOCTORADO": 12, "POSTDOCTORADO": 13,
    "EDUCACION INFORMAL": 0, "FORMACION LABORAL": 0,
    "FORMACION PENITENCIARIA": 0,
}
NIVELES_SUPERIOR = {"TECNICO PROFESIONAL", "TECNOLOGICO", "PROFESIONAL", "ESPECIALIZACION TECNICA PROFESIONAL", "ESPECIALIZACION TECNOLOGICA", "ESPECIALIZACION PROFESIONAL", "MAESTRIA", "DOCTORADO", "POSTDOCTORADO"}
NIVELES_BASICA_MEDIA = {"EDUCACION BASICA PRIMARIA", "EDUCACION BASICA SECUNDARIA", "BACHILLER", "NORMALISTA"}


def normalizar_texto(valor):
    if valor is None: return ""
    texto = unicodedata.normalize("NFKD", str(valor).lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def nivel_canonico(valor): return normalizar_texto(valor).upper()


def tokens(texto):
    vacias = {"de", "del", "la", "las", "el", "los", "y", "o", "en", "con", "para", "por", "un", "una", "como", "que", "se", "al", "a", "su", "sus", "experiencia", "titulo"}
    return {token for token in re.findall(r"[a-z0-9]+", normalizar_texto(texto)) if len(token) > 2 and token not in vacias}


def jaccard(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb: return 0.0
    return len(ta & tb) / len(ta | tb)


def numero(valor):
    try: return 0.0 if valor is None or pd.isna(valor) else float(valor)
    except (TypeError, ValueError): return 0.0


def clasificar_tipo_experiencia(valor):
    texto = normalizar_texto(valor)
    if "profesional relacionada" in texto: return "profesional_relacionada"
    if "profesional especifica" in texto: return "profesional_especifica"
    if "relacionad" in texto: return "relacionada"
    if "especific" in texto: return "especifica"
    if "profesional" in texto: return "profesional"
    if "docente" in texto: return "docente"
    if "laboral" in texto: return "laboral"
    return "otra"


def unir_intervalos(intervalos):
    if not intervalos: return 0
    ordenados = sorted(intervalos, key=lambda x: x[0])
    inicio_actual, fin_actual = ordenados[0]
    dias = 0
    for inicio, fin in ordenados[1:]:
        if inicio <= fin_actual: fin_actual = max(fin_actual, fin)
        else:
            dias += max((fin_actual - inicio_actual).days, 0)
            inicio_actual, fin_actual = inicio, fin
    dias += max((fin_actual - inicio_actual).days, 0)
    return dias


def componentes_rutas(rutas):
    if isinstance(rutas, str):
        try: rutas = json.loads(rutas)
        except json.JSONDecodeError: rutas = []
    if not isinstance(rutas, list): rutas = []
    componentes = []
    for ruta in rutas:
        numero_ruta = (ruta or {}).get("numero_ruta")
        for tipo in ("requisito_principal", "requisito_alternativo"):
            requisito = (ruta or {}).get(tipo, {}) or {}
            estudio = str(requisito.get("estudio") or "").strip()
            experiencia = str(requisito.get("experiencia") or "").strip()
            meses = max(numero(requisito.get("tiempomin")), 0.0)
            if estudio or experiencia or meses != 0:
                componentes.append({"numero_ruta": numero_ruta, "tipo_ruta": tipo, "estudio": estudio, "experiencia": experiencia, "meses_requeridos": meses})
    return componentes


class MotorRecomendacionCNSC:
    def __init__(self, ruta_paquete):
        self.ruta_paquete = Path(ruta_paquete)
        if not self.ruta_paquete.exists(): raise FileNotFoundError(f"No se encontró el paquete: {self.ruta_paquete}")
        paquete = joblib.load(self.ruta_paquete)
        requeridas = {"modelo", "vectorizadores_tfidf", "variables_modelo", "columnas_experiencia_tipo", "umbral", "catalogo_opec", "metadata"}
        faltantes = requeridas - set(paquete)
        if faltantes: raise ValueError(f"Paquete incompleto: {sorted(faltantes)}")
        self.modelo = paquete["modelo"]
        self.vectorizadores = paquete["vectorizadores_tfidf"]
        self.variables = list(paquete["variables_modelo"])
        self.columnas_tipo = list(paquete["columnas_experiencia_tipo"])
        self.umbral = float(paquete["umbral"])
        self.catalogo = paquete["catalogo_opec"].copy()
        self.metadata = paquete["metadata"]
        if not np.isclose(self.umbral, 0.720): raise ValueError("El umbral del paquete no corresponde al modelo aprobado.")

    def validar_perfil(self, perfil):
        if not isinstance(perfil, dict): raise ValueError("El perfil debe ser un objeto con formación y experiencia.")
        formaciones, experiencias = perfil.get("formaciones"), perfil.get("experiencias")
        if not isinstance(formaciones, list) or len(formaciones) == 0: raise ValueError("Registre al menos una formación académica.")
        if not isinstance(experiencias, list): raise ValueError("El campo experiencias debe ser una lista; puede estar vacía.")
        for i, formacion in enumerate(formaciones, start=1):
            if not str(formacion.get("nivel", "")).strip(): raise ValueError(f"La formación {i} no tiene nivel educativo.")
            if not str(formacion.get("titulo", "")).strip(): raise ValueError(f"La formación {i} no tiene título o denominación.")
        hoy = pd.Timestamp.today().normalize(); experiencias_validas = []
        for i, experiencia in enumerate(experiencias, start=1):
            if not str(experiencia.get("cargo", "")).strip(): raise ValueError(f"La experiencia {i} no tiene cargo.")
            inicio = pd.to_datetime(experiencia.get("fecha_inicio"), errors="coerce")
            fin_valor = experiencia.get("fecha_fin")
            fin = hoy if fin_valor in (None, "") else pd.to_datetime(fin_valor, errors="coerce")
            if pd.isna(inicio) or pd.isna(fin): raise ValueError(f"La experiencia {i} contiene una fecha inválida.")
            if inicio > fin: raise ValueError(f"La experiencia {i} inicia después de su finalización.")
            if inicio > hoy or fin > hoy: raise ValueError(f"La experiencia {i} contiene fechas futuras.")
            copia = dict(experiencia); copia["inicio_dt"] = inicio.normalize(); copia["fin_dt"] = fin.normalize(); copia["tipo_canonico"] = clasificar_tipo_experiencia(experiencia.get("tipo", "")); experiencias_validas.append(copia)
        return formaciones, experiencias_validas

    def resumir_formacion(self, formaciones):
        niveles = [nivel_canonico(f.get("nivel")) for f in formaciones]
        textos = [normalizar_texto(f"{f.get('nivel', '')} {f.get('titulo', '')}") for f in formaciones]
        return {"perfil_academico_final": " | ".join(t for t in textos if t), "cantidad_superior_formal": sum(n in NIVELES_SUPERIOR for n in niveles), "cantidad_educacion_basica_media": sum(n in NIVELES_BASICA_MEDIA for n in niveles), "cantidad_educacion_informal": sum(n == "EDUCACION INFORMAL" for n in niveles), "cantidad_formacion_laboral": sum(n == "FORMACION LABORAL" for n in niveles), "cantidad_formacion_normalista": sum(n == "NORMALISTA" for n in niveles), "cantidad_formacion_penitenciaria": sum(n == "FORMACION PENITENCIARIA" for n in niveles), "jerarquia_academica_maxima_final": max((JERARQUIA_ACADEMICA.get(n, 0) for n in niveles), default=0)}

    def resumir_experiencia(self, experiencias):
        intervalos = [(e["inicio_dt"], e["fin_dt"]) for e in experiencias]
        meses_total = unir_intervalos(intervalos) / 30.4375
        resumen = {"tiene_experiencia_previa": int(bool(experiencias)), "cantidad_experiencias_final": len(experiencias), "meses_experiencia_final": meses_total, "texto_experiencia": " | ".join(normalizar_texto(f"{e.get('cargo', '')} {e.get('empresa', '')} {e.get('funciones', '')}") for e in experiencias)}
        for columna in self.columnas_tipo: resumen[columna] = 0.0
        por_tipo = {}
        for experiencia in experiencias: por_tipo.setdefault(experiencia["tipo_canonico"], []).append((experiencia["inicio_dt"], experiencia["fin_dt"]))
        for tipo, intervalos_tipo in por_tipo.items():
            columna = f"meses_experiencia_{tipo}"
            if columna in resumen: resumen[columna] = unir_intervalos(intervalos_tipo) / 30.4375
        return resumen

    def evaluar_rutas(self, rutas, perfil_academico, texto_experiencia, meses_persona):
        componentes = componentes_rutas(rutas); resultados = []
        for componente in componentes:
            meses_req = componente["meses_requeridos"]; cumple = int(meses_req == 0 or meses_persona >= meses_req); brecha = max(meses_req - meses_persona, 0.0); sim_exp = jaccard(texto_experiencia, componente["experiencia"]) if componente["experiencia"] else 0.0; sim_acad = jaccard(perfil_academico, componente["estudio"]) if componente["estudio"] else 0.0
            resultado = dict(componente); resultado.update({"cumple_tiempo": cumple, "brecha_meses": brecha, "sim_exp": sim_exp, "sim_acad": sim_acad, "puntaje_academico": 0.45 * cumple + 0.25 * sim_exp + 0.30 * sim_acad}); resultados.append(resultado)
        if not resultados:
            vacio = {"numero_ruta": None, "tipo_ruta": "SIN_RUTA", "estudio": "", "experiencia": "", "meses_requeridos": 0.0, "cumple_tiempo": 0, "brecha_meses": 0.0, "sim_exp": 0.0, "sim_acad": 0.0, "puntaje_academico": 0.0}
            return {"rutas_evaluadas_final": 0, "rutas_cumplen_tiempo": 0, "cumple_tiempo_alguna_ruta": 0, "meses_requeridos_mejor_ruta": 0.0, "brecha_meses_mejor_ruta": 0.0}, vacio
        mejor = max(resultados, key=lambda x: x["puntaje_academico"])
        return {"rutas_evaluadas_final": len(resultados), "rutas_cumplen_tiempo": sum(x["cumple_tiempo"] for x in resultados), "cumple_tiempo_alguna_ruta": int(any(x["cumple_tiempo"] for x in resultados)), "meses_requeridos_mejor_ruta": mejor["meses_requeridos"], "brecha_meses_mejor_ruta": mejor["brecha_meses"]}, mejor

    def preparar_matriz(self, perfil):
        formaciones, experiencias = self.validar_perfil(perfil); academia = self.resumir_formacion(formaciones); experiencia = self.resumir_experiencia(experiencias); filas, detalles = [], []
        for _, vacante in self.catalogo.iterrows():
            fila = {**academia, **experiencia}; rutas = vacante.get("rutas_requisitos", []); variables_ruta, mejor = self.evaluar_rutas(rutas, academia["perfil_academico_final"], experiencia["texto_experiencia"], experiencia["meses_experiencia_final"]); fila.update(variables_ruta); componentes = componentes_rutas(rutas); estudios = [normalizar_texto(x["estudio"]) for x in componentes if x["estudio"]]; textos_exp = [normalizar_texto(x["experiencia"]) for x in componentes if x["experiencia"]]; meses = [x["meses_requeridos"] for x in componentes]
            fila.update({"requisito_estudio_texto": " | ".join(dict.fromkeys(estudios)), "requisito_experiencia_texto": " | ".join(dict.fromkeys(textos_exp)), "rutas_textuales": max(len(estudios), len(textos_exp), 0), "meses_requisito_minimo_rutas": min(meses) if meses else 0.0, "meses_requisito_maximo_rutas": max(meses) if meses else 0.0}); req = max(fila["meses_requeridos_mejor_ruta"], 1.0); fila["brecha_experiencia_relativa"] = min(fila["brecha_meses_mejor_ruta"] / req, 1.0); filas.append(fila)
            detalles.append({"opec": vacante["opec"], "descripcion": vacante.get("descripcion", ""), "numero_ruta": mejor["numero_ruta"], "tipo_ruta": mejor["tipo_ruta"], "requisito_estudio": mejor["estudio"], "requisito_experiencia": mejor["experiencia"], "meses_requeridos": mejor["meses_requeridos"], "brecha_meses": mejor["brecha_meses"], "cumple_tiempo": mejor["cumple_tiempo"]})
        matriz = pd.DataFrame(filas); detalle = pd.DataFrame(detalles)
        for tema, col_perfil, col_requisito in (("academica", "perfil_academico_final", "requisito_estudio_texto"), ("experiencia", "texto_experiencia", "requisito_experiencia_texto")):
            for analizador in ("word", "char"):
                vectorizador = self.vectorizadores[(tema, analizador)]; a = vectorizador.transform(matriz[col_perfil].fillna("")); b = vectorizador.transform(matriz[col_requisito].fillna("")); matriz[f"similitud_{tema}_tfidf_{analizador}"] = np.asarray(a.multiply(b).sum(axis=1)).ravel()
        meses_relacionados = matriz.get("meses_experiencia_relacionada", pd.Series(0.0, index=matriz.index)); matriz["fortaleza_experiencia_relacionada"] = np.log1p(meses_relacionados) * matriz["similitud_experiencia_tfidf_word"]
        matriz["compatibilidad_semantica"] = 0.40 * matriz["similitud_academica_tfidf_word"] + 0.20 * matriz["similitud_academica_tfidf_char"] + 0.25 * matriz["similitud_experiencia_tfidf_word"] + 0.15 * matriz["similitud_experiencia_tfidf_char"]
        for variable in self.variables:
            if variable not in matriz.columns: matriz[variable] = 0.0
        X = matriz[self.variables].replace([np.inf, -np.inf], np.nan).fillna(0)
        return X, matriz, detalle, experiencia

    def recomendar(self, perfil, top_n=None):
        X, matriz, detalle, resumen_experiencia = self.preparar_matriz(perfil); indices = self.modelo.predict_proba(X)[:, 1]; resultado = detalle.copy(); resultado["indice_compatibilidad"] = indices; resultado["orientacion"] = np.where(indices >= self.umbral, "Mayor compatibilidad histórica", "Revisar requisitos y brechas"); resultado["experiencia_ciudadano_meses"] = resumen_experiencia["meses_experiencia_final"]; resultado["similitud_academica"] = matriz["similitud_academica_tfidf_word"].to_numpy(); resultado["similitud_experiencia"] = matriz["similitud_experiencia_tfidf_word"].to_numpy(); resultado["advertencia"] = ADVERTENCIA; resultado = resultado.sort_values(["indice_compatibilidad", "brecha_meses"], ascending=[False, True]).reset_index(drop=True); resultado.insert(0, "posicion", np.arange(1, len(resultado) + 1)); limite = top_n if top_n is not None else perfil.get("top_n", 10); limite = int(max(1, min(int(limite), 100))); return resultado.head(limite).copy()
