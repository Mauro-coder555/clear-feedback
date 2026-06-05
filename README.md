# clear-feedback

Aplicación local de escritorio para analizar respuestas abiertas de formularios, encuestas y feedback de usuarios.

clear-feedback ayuda a transformar texto libre en insights accionables: temas recurrentes, porcentajes de mención, ejemplos representativos, acciones sugeridas y reportes exportables.

---

## Índice

- [Qué problema resuelve](#qué-problema-resuelve)
- [Por qué existe](#por-qué-existe)
- [Para quién es útil](#para-quién-es-útil)
- [Casos de uso reales](#casos-de-uso-reales)
- [Características principales](#características-principales)
- [Herramientas utilizadas](#herramientas-utilizadas)
- [Arquitectura local-first](#arquitectura-local-first)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Cómo usarlo paso a paso](#cómo-usarlo-paso-a-paso)
- [Cómo importar un CSV](#cómo-importar-un-csv)
- [Uso de IA local con Ollama](#uso-de-ia-local-con-ollama)
- [Cómo interpretar los resultados](#cómo-interpretar-los-resultados)
- [Cómo exportar reportes](#cómo-exportar-reportes)
- [Cómo funciona internamente](#cómo-funciona-internamente)
- [Estructura de carpetas](#estructura-de-carpetas)
- [Tests](#tests)
- [Limitaciones actuales](#limitaciones-actuales)
- [Mejoras futuras](#mejoras-futuras)

---

## Qué problema resuelve

Muchas encuestas, formularios o espacios de feedback reciben grandes volúmenes de respuestas abiertas. Leer todo manualmente es lento, subjetivo y difícil de convertir en decisiones concretas.

clear-feedback permite analizar esas respuestas para entender rápidamente:

- qué temas se repiten;
- qué problemas aparecen con mayor frecuencia;
- qué oportunidades de mejora existen;
- qué señales positivas o negativas aparecen;
- qué acciones concretas se podrían tomar.

---

## Por qué existe

El feedback abierto suele contener información valiosa, pero muchas veces queda enterrado en filas de un CSV.

La idea del proyecto es pasar de esto:

> “Tengo muchas respuestas abiertas y no sé por dónde empezar.”

a esto:

> “Ya sé cuáles son los principales temas, qué porcentaje de personas los mencionó y qué acciones puedo tomar.”

---

## Para quién es útil

clear-feedback está pensado para personas no técnicas que necesitan entender feedback abierto de forma clara.

Puede ser útil para equipos de:

- Producto;
- Educación;
- Customer Success;
- Soporte;
- Operaciones;
- Investigación de usuarios;
- People / HR;
- Programas de formación;
- Equipos que trabajan con encuestas internas o externas.

---

## Casos de uso reales

Algunos ejemplos:

- analizar respuestas abiertas de una encuesta post-curso;
- detectar problemas recurrentes en feedback de estudiantes;
- resumir comentarios de usuarios después de un lanzamiento;
- identificar oportunidades de mejora en programas educativos;
- encontrar patrones en formularios de soporte;
- transformar comentarios dispersos en un reporte ejecutivo.

---

## Características principales

- Aplicación de escritorio con GUI.
- Importación de archivos CSV.
- Selección manual de la columna de feedback.
- Vista previa de respuestas.
- Limpieza básica de texto.
- Opción para eliminar duplicados exactos.
- Clasificación inicial por categorías y keywords.
- Detección de themes mediante reglas configurables.
- Análisis opcional con IA local usando Ollama.
- Ejecución de IA en segundo plano para evitar congelar la GUI.
- Barra de progreso y mensajes de estado durante el análisis.
- Resumen ejecutivo con las 3 principales acciones a tomar.
- Exportación de reportes en Markdown.
- Exportación de CSV enriquecido.
- Funcionamiento local-first.
- Sin login.
- Sin nube obligatoria.
- Sin envío de datos a servicios externos.

---

## Herramientas utilizadas

| Herramienta | Uso |
|---|---|
| 🐍 Python | Lenguaje principal |
| 🖥️ PySide6 | Interfaz gráfica de escritorio |
| 📊 pandas | Lectura y procesamiento de CSV |
| 🧪 pytest | Tests del flujo central |
| 🧠 Ollama | IA local opcional |
| 📝 Markdown | Exportación de reportes |
| 📁 JSON | Configuración local de categorías y themes |
| 🧵 QThread | Ejecución en background para evitar congelar la GUI |

---

## Arquitectura local-first

clear-feedback está diseñado para ejecutarse localmente en la computadora del usuario.

Esto significa que:

- no requiere login;
- no requiere nube;
- no requiere una base de datos externa;
- no envía datos sensibles a servicios externos;
- puede funcionar solo con reglas locales;
- puede usar IA local si Ollama está instalado.

La IA es opcional. Si no se usa Ollama, la aplicación sigue funcionando con reglas de keywords y themes configurables.

---

## Instalación

Primero creá y activá un entorno virtual.

En Windows:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

Luego instalá las dependencias:

```bash
pip install -r requirements.txt
```

---

## Ejecución

Para abrir la aplicación:

```bash
python src/main.py
```

---

## Cómo usarlo paso a paso

1. Abrí la aplicación.
2. Hacé clic en **Import CSV**.
3. Seleccioná el archivo CSV con respuestas abiertas.
4. Elegí la columna que contiene el feedback.
5. Decidí si querés eliminar duplicados exactos.
6. Activá o desactivá **Use local AI with Ollama**.
7. Elegí el modelo local.
8. Elegí el límite de respuestas a analizar con IA.
9. Ejecutá el análisis.
10. Revisá el resumen principal en la pestaña **Summary**.
11. Usá **Review** solo si necesitás auditar comentarios individuales.
12. Exportá el reporte o el CSV enriquecido desde **Export**.

---

## Cómo importar un CSV

El archivo debe estar en formato `.csv`.

Ejemplo mínimo:

```csv
id,feedback
1,"Necesito más ejercicios prácticos."
2,"La plataforma es clara y fácil de usar."
3,"Me costó entender la explicación inicial."
```

La aplicación permite elegir manualmente cuál columna contiene el texto libre.

---

## Uso de IA local con Ollama

clear-feedback puede usar Ollama para detectar themes dinámicos según el contenido de cada formulario.

Esto permite analizar formularios distintos sin tener que configurar manualmente keywords específicas para cada caso.

Para usar IA local:

1. Instalá Ollama.
2. Descargá un modelo, por ejemplo:

```bash
ollama pull llama3.2:3b
```

3. Verificá que Ollama funcione:

```bash
ollama list
```

4. En la app, activá:

```text
Use local AI with Ollama
```

5. Ejecutá el análisis.

La IA local se usa para:

- detectar themes recurrentes;
- agrupar comentarios similares;
- calcular cobertura;
- sugerir acciones;
- generar reportes más accionables.

La app ejecuta el análisis de IA en background usando `QThread`, por lo que la interfaz no debería congelarse mientras Ollama procesa el feedback.

---

## Cómo interpretar los resultados

La pestaña **Summary** está pensada para responder rápidamente:

- cuáles son las 3 cosas más importantes a revisar;
- cuántas respuestas cubre cada insight;
- qué porcentaje representa;
- qué acción concreta se recomienda;
- cuántas respuestas quedaron cubiertas o no agrupadas.

Métricas principales:

| Métrica | Significado |
|---|---|
| Responses analyzed | Cantidad de respuestas analizadas |
| Covered by insights | Respuestas asociadas a algún insight |
| Not grouped | Respuestas no asignadas a ningún insight claro |
| Coverage | Porcentaje de respuestas cubiertas por insights |

La pestaña **Review** no es la vista principal. Está pensada para auditar comentarios individuales cuando haga falta.

---

## Cómo exportar reportes

Desde la pestaña **Export** podés generar:

### AI report

Reporte Markdown con:

- resumen ejecutivo;
- principales insights;
- cantidad y porcentaje por insight;
- acciones sugeridas;
- ejemplos representativos;
- metodología.

### Keyword report

Reporte Markdown basado en reglas locales de categorías y themes.

### Enriched CSV

Archivo CSV con información adicional por comentario, como:

- texto original;
- texto limpio;
- categoría asignada;
- theme asignado;
- keywords detectadas.

---

## Cómo funciona internamente

El flujo principal es:

```text
CSV
→ importación
→ selección de columna
→ limpieza de texto
→ deduplicación opcional
→ clasificación por keywords
→ detección de themes locales
→ análisis con IA local opcional
→ resumen visual
→ exportación Markdown / CSV
```

Cuando se usa IA local, el flujo se amplía así:

```text
feedback limpio
→ detección de themes globales con Ollama
→ asignación de respuestas a themes detectados
→ cálculo de menciones, cobertura y porcentajes
→ generación de acciones sugeridas
```

Módulos principales:

| Módulo | Responsabilidad |
|---|---|
| `importer.py` | Importar CSV y detectar columnas |
| `cleaner.py` | Normalizar texto y crear feedback items |
| `classifier.py` | Clasificación básica por categorías |
| `theme_classifier.py` | Clasificación por themes locales |
| `ai_analyzer.py` | Análisis opcional con Ollama |
| `analyzer.py` | Métricas y resúmenes por reglas |
| `exporter.py` | Exportación de CSV enriquecido |
| `report.py` | Reporte Markdown basado en reglas |
| `report_ai.py` | Reporte Markdown con IA |
| `app.py` | Interfaz gráfica principal y worker en background |

---

## Estructura de carpetas

```text
clear-feedback/
├── README.md
├── requirements.txt
├── pytest.ini
├── src/
│   ├── main.py
│   ├── app.py
│   ├── models.py
│   ├── report.py
│   ├── report_ai.py
│   ├── core/
│   │   ├── importer.py
│   │   ├── cleaner.py
│   │   ├── classifier.py
│   │   ├── theme_classifier.py
│   │   ├── ai_analyzer.py
│   │   ├── analyzer.py
│   │   ├── exporter.py
│   │   └── config.py
│   └── data/
│       ├── examples/
│       │   └── sample_feedback.csv
│       ├── configs/
│       │   ├── default_categories.json
│       │   └── default_themes.json
│       └── exports/
└── tests/
    ├── test_core_flow.py
    └── test_ai_flow_manual.py
```

---

## Tests

Para correr los tests normales:

```bash
python -m pytest
```

El test de IA está marcado como opcional porque requiere Ollama y puede tardar más.

Para correrlo manualmente en PowerShell:

```bash
$env:CLEAR_FEEDBACK_RUN_AI_TEST="1"
python -m pytest tests/test_ai_flow_manual.py -s
```

---

## Limitaciones actuales

- La calidad de la IA depende del modelo local usado.
- Modelos pequeños pueden agrupar mal algunos comentarios.
- El análisis con IA puede tardar en equipos con poca memoria o sin GPU.
- El CSV enriquecido actual se basa principalmente en la clasificación por reglas.
- La detección de themes con IA todavía puede requerir ajustes de prompt para mejorar precisión.
- No hay empaquetado como `.exe` todavía.
- No hay importación de Excel en esta versión.
- La edición manual de categorías o themes desde la GUI todavía no está implementada.

---

## Mejoras futuras

- Edición manual de categorías y themes desde la tabla Review.
- Exportación de un único reporte combinado.
- Importación de Excel.
- Selector visual de modelos Ollama instalados.
- Cancelación de análisis en progreso.
- Mejor manejo de errores cuando Ollama no está disponible.
- Mejor detección de idioma.
- Agrupación semántica más robusta.
- Comparación entre formularios.
- Empaquetado como aplicación instalable para Windows.
- Exportación PDF.
- Guardado de proyectos locales.
- Mejoras de accesibilidad visual.
- Edición de configuración desde la propia GUI.

---

## Estado del proyecto

El MVP actual ya permite:

- importar CSV;
- seleccionar columna de feedback;
- ver preview;
- limpiar y deduplicar texto;
- analizar con reglas locales;
- analizar con IA local usando Ollama;
- mostrar progreso durante el análisis;
- evitar congelar la GUI mientras corre la IA;
- ver un resumen ejecutivo simple;
- exportar reportes Markdown;
- exportar CSV enriquecido.

clear-feedback ya tiene una primera versión usable para convertir feedback abierto en insights accionables de forma local.
