# Orientador de oportunidades laborales del sector público colombiano

**Proyecto de Maestría en Ciencia de Datos**  
**Proyecto:** *Realizar un análisis y diseño de un modelo predictivo para la recomendación de oportunidades laborales en el ámbito gubernamental*  
**Autores:** Diana Vásquez · Germán Mahecha

## Prototipo

Este repositorio contiene la versión final del prototipo ciudadano para orientar la exploración de oportunidades laborales OPEC del sector público colombiano.

**Aplicación web:** https://proyectomcd-ciudadano-kqhpti4jdjkht2npkkquff.streamlit.app/

El usuario registra su formación académica y experiencia laboral. El sistema conserva la salida del modelo predictivo aprobado como **índice de compatibilidad histórica** y, posteriormente, aplica una capa funcional de presentación para ayudar a interpretar las oportunidades disponibles.

> **Advertencia:** el índice de compatibilidad es una orientación basada en información histórica. No es una probabilidad de selección, no garantiza superar la Verificación de Requisitos Mínimos (VRM) y no reemplaza la verificación oficial de la CNSC.

## Ajustes funcionales finales

La versión final incorpora los ajustes solicitados durante la revisión académica:

1. **Nivel académico y nivel del empleo**
   - Bachiller → oportunidades de nivel Asistencial.
   - Técnico profesional / Tecnológico → oportunidades de nivel Técnico.
   - Profesional → oportunidades de nivel Profesional / Asesor.
   - Especialización, Maestría o Doctorado → oportunidades de nivel Profesional / Asesor.
   - La capa funcional evita que un perfil profesional sea priorizado con OPEC de nivel Asistencial o Técnico.

2. **Buscador académico basado en información del SNIES**
   - El selector utiliza un catálogo local de programas académicos derivado de información del SNIES.
   - La búsqueda se realiza por nombre de programa.
   - No se crean equivalencias académicas ni homologaciones automáticas.

3. **Concurso / proceso de selección**
   - Cada resultado muestra el concurso o proceso de selección asociado a la OPEC.
   - También puede utilizarse como filtro funcional.

4. **Rango salarial**
   - El usuario puede seleccionar un rango de asignación salarial.
   - Este filtro se aplica después de la inferencia y **no modifica el modelo ni el índice de compatibilidad histórica**.

5. **Pruebas funcionales por nivel**
   - PF-01: Bachiller / Asistencial.
   - PF-02: Tecnológico / Técnico.
   - PF-03: Profesional.
   - PF-04: Profesional especializado / Posgrado.
   - PF-05: Profesional + Especialización + Maestría.

## Modelo predictivo aprobado

El prototipo conserva sin modificación el modelo seleccionado durante la fase experimental:

- **Algoritmo:** `HistGradientBoostingClassifier`
- **Representación textual:** TF-IDF
- **Artefacto:** `paquete_modelo_cnsc_v1.joblib`
- **Umbral aprobado:** `0.720`
- Se mantienen congeladas las variables, vectorizadores y transformaciones del modelo.
- No se realiza entrenamiento, ajuste de hiperparámetros ni SMOTE durante la ejecución del prototipo.

### Métricas aprobadas de validación temporal

| Métrica | Resultado |
|---|---:|
| Accuracy | 0.7103 |
| Precision | 0.8187 |
| Recall — supera VRM | 0.7417 |
| Recall — no supera VRM | 0.6418 |
| F1 | 0.7783 |
| ROC-AUC | 0.7685 |
| Balanced Accuracy | 0.6917 |
| Umbral | **0.720** |

Estas métricas corresponden a la evaluación aprobada del modelo y no son recalculadas ni sustituidas por la aplicación.

## Arquitectura funcional

```text
Perfil ciudadano
      ↓
Formación académica + experiencia
      ↓
MODELO PREDICTIVO APROBADO
(HistGradientBoosting + TF-IDF)
      ↓
Índice de compatibilidad histórica
      ↓
Capa funcional de presentación
      ├── coincidencia textual académica
      ├── nivel del empleo
      ├── concurso / proceso de selección
      ├── rango salarial
      └── contraste informativo de requisitos
      ↓
Oportunidades para explorar
```

La capa funcional **no altera la salida del modelo**. Su finalidad es organizar y presentar la información de manera coherente para el ciudadano.

## Pruebas funcionales finales

| Prueba | Perfil utilizado | Resultado esperado |
|---|---|---|
| PF-01 | Bachiller | Solo nivel Asistencial |
| PF-02 | Tecnología en Administración de Empresas | Solo nivel Técnico |
| PF-03 | Profesional en Ingeniería Industrial | Nivel Profesional / Asesor |
| PF-04 | Profesional + Especialización | Nivel Profesional / Asesor, incluyendo oportunidades especializadas cuando corresponda |
| PF-05 | Derecho + Especialización + Maestría | Nivel Profesional / Asesor con contraste de requisitos de posgrado |

Las pruebas verifican además que:

- el catálogo académico se carga correctamente;
- programas como **DERECHO** están disponibles en el nivel Profesional;
- el concurso/proceso de selección se muestra en los resultados;
- el salario funciona como filtro posterior a la inferencia;
- un perfil profesional no habilita oportunidades Asistenciales o Técnicas;
- el índice histórico conserva exactamente la salida del modelo aprobado.

## Contenido principal del repositorio

| Archivo | Función |
|---|---|
| `app.py` | Interfaz ciudadana desarrollada en Streamlit |
| `motor_inferencia.py` | Preparación de variables e inferencia del modelo aprobado |
| `reglas_funcionales.py` | Reglas de presentación por nivel académico/empleo |
| `paquete_modelo_cnsc_v1.joblib` | Modelo, vectorizadores y componentes congelados |
| `catalogo_opec_prototipo.joblib` | Catálogo histórico de OPEC utilizado por el prototipo |
| `catalogo_opec_metadata.csv.gz` | Nivel, convocatoria, salario, denominación y grado de las OPEC históricas |
| `catalogo_programas_selector.csv` | Catálogo local de programas académicos derivado de información SNIES |
| `metadata_modelo.json` | Metadatos y especificaciones del modelo |
| `contrato_entrada.json` | Estructura esperada del perfil ciudadano |
| `contrato_salida.json` | Estructura de salida del motor |
| `ejemplo_perfil.json` | Ejemplo de perfil |
| `test_motor.py` | Pruebas del motor y de la capa funcional |
| `requirements.txt` | Dependencias del proyecto |
| `ejecutar.bat` | Validación y ejecución automatizada en Windows |
| `Dockerfile` | Configuración alternativa mediante contenedor |

## Ejecución local

Se recomienda **Python 3.11**.

### Windows

```bat
git clone https://github.com/DianaVF2025/proyectoMCD-ciudadano.git
cd proyectoMCD-ciudadano
ejecutar.bat
```

El archivo `ejecutar.bat`:

1. verifica los archivos necesarios;
2. prepara el entorno virtual;
3. instala las dependencias;
4. ejecuta las pruebas funcionales;
5. inicia la interfaz Streamlit.

### Ejecución manual

```bash
python -m venv venv
```

En Windows:

```bat
venv\Scripts\activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

En macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
python test_motor.py
streamlit run app.py
```

## Interpretación de resultados

La **compatibilidad histórica** es el resultado principal del modelo aprobado.

La coincidencia académica presentada en la interfaz corresponde a una **coincidencia textual directa** entre el programa declarado y los requisitos registrados de la OPEC. No representa una certificación de cumplimiento académico.

La experiencia se muestra como apoyo para comparar el tiempo registrado por el ciudadano con el tiempo indicado en la oportunidad. Cuando la OPEC exige experiencia relacionada o específica, deben revisarse además las funciones y demás condiciones.

## Alcance y limitaciones

- Prototipo de alcance académico y demostrativo.
- Utiliza un catálogo histórico de OPEC.
- No determina admisión ni elegibilidad.
- No certifica cumplimiento de requisitos mínimos.
- No establece equivalencias académicas propias.
- No realiza clasificación automática por NBC.
- No sustituye los procesos, plataformas ni decisiones oficiales de la CNSC.

## Nota institucional

Este proyecto **no es una herramienta oficial de la Comisión Nacional del Servicio Civil (CNSC)**. Las decisiones sobre admisión, VRM y procesos de selección corresponden exclusivamente a las entidades y procedimientos oficiales aplicables.

---
**Maestría en Ciencia de Datos — Prototipo académico**
