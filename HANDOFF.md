# Entrega del proyecto Dance Match Lab

Este documento esta dirigido al equipo que continuara el proyecto. Resume el estado real del prototipo, como ponerlo en marcha, las decisiones tecnicas ya tomadas y el trabajo que sigue pendiente.

Ultima revision de esta entrega: 2026-08-25.

## Objetivo actual

Dance Match Lab compara dos secuencias de baile:

1. Un video se usa como referencia.
2. Un segundo video se usa como ejecucion a evaluar.
3. MediaPipe extrae landmarks corporales.
4. El proyecto genera features biomecanicas.
5. DTW alinea temporalmente ambas secuencias.
6. La interfaz presenta similitud global, resultados por grupos corporales y resultados por intervalos.

El proyecto es un prototipo experimental. No es una herramienta clinica ni su puntaje debe interpretarse como una medicion definitiva de calidad artistica.

## Estado recibido

Actualmente esta verificado que el proyecto puede:

- Instalarse localmente con `uv` y Python 3.10.
- Abrir videos proporcionados por el usuario.
- Extraer landmarks de pose con MediaPipe.
- Generar y guardar landmarks `.npy` y features `.npz`.
- Procesar uno, varios o todos los videos de `videos/`.
- Comparar dos archivos de video distintos.
- Reutilizar automaticamente resultados previamente procesados.
- Mostrar landmarks y angulos desde una camara o un video local.
- Abrir una interfaz Tkinter con ambas secuencias.
- Ejecutar un reporte en consola sin abrir la interfaz.

No se incluyen videos de ejemplo, resultados procesados ni datasets. Cada persona debe agregar sus propios videos localmente.

## Primer arranque

Desde la raiz del repositorio:

```powershell
uv python install 3.10
uv sync --locked
uv run --locked python app\src\test_env.py
```

El ultimo comando debe mostrar las versiones de Python, OpenCV, MediaPipe, NumPy, SciPy y Pillow, y confirmar que el modelo de pose fue cargado.

Despues, agrega dos archivos:

```text
videos/
  baile_referencia.mp4
  baile_usuario.mp4
```

Ejecuta una comparacion completa:

```powershell
.\run_dance_compare.ps1 `
  --reference-video videos\baile_referencia.mp4 `
  --user-video videos\baile_usuario.mp4 `
  --cache-missing
```

La guia detallada de uso esta en [README.md](README.md).

## Mapa del codigo

| Archivo | Responsabilidad | Modificar cuando |
|---|---|---|
| `app/src/dance_compare_ui.py` | CLI principal, carga de videos, cache e interfaz Tkinter | Se cambie la experiencia de comparacion o sus argumentos |
| `app/src/dance_similarity.py` | Seleccion de features, normalizacion, DTW, puntajes e intervalos | Se ajuste el algoritmo de similitud |
| `app/src/biomech_features.py` | Calculo de features biomecanicas y temporales | Se agreguen o corrijan variables corporales |
| `app/src/funciones_pose_engine.py` | MediaPipe, conversion de landmarks, angulos y dibujo | Se cambie la extraccion o visualizacion de pose |
| `app/src/landmark_saving.py` | Preprocesamiento de uno o varios videos | Se cambie el formato o almacenamiento del cache |
| `app/src/realtime_landmarks.py` | Visualizacion desde camara o video | Se mejoren controles o captura en tiempo real |
| `app/src/test_env.py` | Prueba rapida de dependencias | Se agregue una dependencia critica |
| `run_dance_compare.ps1` | Lanzador de Windows mediante `uv` | Se cambie la entrada principal |
| `pyproject.toml` | Dependencias directas y version de Python admitida | Se agreguen o retiren librerias |
| `uv.lock` | Versiones exactas resueltas por `uv` | Se modifique `pyproject.toml` o se actualicen dependencias |

## Flujos principales

### Revisar landmarks antes de comparar

Camara principal:

```powershell
uv run --locked python app\src\realtime_landmarks.py --camera 0
```

Video local:

```powershell
uv run --locked python app\src\realtime_landmarks.py --video videos\baile_usuario.mp4
```

Presiona `Q` para cerrar la ventana.

### Preprocesar videos

```powershell
uv run --locked python app\src\landmark_saving.py videos\baile_referencia.mp4 videos\baile_usuario.mp4
```

Sin rutas, procesa todos los videos compatibles ubicados directamente en `videos/`:

```powershell
uv run --locked python app\src\landmark_saving.py
```

### Comparar sin interfaz

```powershell
.\run_dance_compare.ps1 `
  --reference-video videos\baile_referencia.mp4 `
  --user-video videos\baile_usuario.mp4 `
  --cache-missing `
  --headless-report
```

## Archivos generados

El cache usa el nombre base del video:

```text
output/
  landmarks/
    baile_referencia_landmarks.npy
    baile_usuario_landmarks.npy
  features/
    baile_referencia_features.npz
    baile_usuario_features.npz
```

Los `.npy` contienen landmarks por cuadro. Los `.npz` contienen la matriz `X`, `feature_names` y `frame_ids`.

Las carpetas existen en Git gracias a archivos `.gitkeep`, pero su contenido esta ignorado. No se deben confirmar videos, caches, modelos grandes ni informacion privada.

## Decisiones tecnicas vigentes

- `uv` es el unico gestor principal del entorno y las dependencias.
- `.python-version` fija Python 3.10 para el flujo recomendado.
- `pyproject.toml` declara dependencias directas y `uv.lock` garantiza instalaciones reproducibles.
- El flujo es completamente local y no usa servicios externos, base de datos ni secretos.
- Ningun video esta codificado como referencia fija; el usuario siempre indica `--reference-video`.
- Los nombres de los caches se derivan del nombre base de cada video.
- La interfaz principal usa Tkinter; el visor de tiempo real usa una ventana de OpenCV.
- La comparacion se enfoca en una sola persona visible por video.

## Limitaciones y deuda tecnica

1. **Puntaje sin calibracion formal.** Los pesos, umbrales y mensajes son heuristicas y necesitan validarse con ejemplos etiquetados.
2. **Sin pruebas automatizadas.** Hay validaciones manuales, pero todavia no existe una suite de tests unitarios o de integracion.
3. **Procesamiento sin indicador de progreso.** Videos largos pueden tardar y la interfaz no muestra avance, tiempo restante ni cancelacion.
4. **Cache identificado solo por nombre.** Dos videos diferentes con el mismo nombre base pueden reutilizar archivos incorrectos. Conviene guardar metadata o un hash del video.
5. **Un solo sujeto.** MediaPipe Pose y el pipeline actual asumen una persona principal.
6. **Sensibilidad a la captura.** Angulo, encuadre, iluminacion, oclusiones y calidad del video afectan el resultado.
7. **Sin exportacion de reportes.** El modo headless imprime resultados, pero no los guarda como JSON o CSV.
8. **Estructura basada en scripts.** `app/src` funciona por imports locales; todavia no esta organizado como un paquete Python instalable.
9. **Manejo de errores basico.** El preprocesador continua con el siguiente archivo, pero faltan errores tipados, logs y mensajes de recuperacion consistentes.
10. **Terminologia interna heredada.** Algunas variables internas todavia se llaman `benchmark`; para el usuario toda referencia es general y se presenta como `reference` o `referencia`.

Los avisos de TensorFlow Lite o protobuf emitidos por MediaPipe durante el arranque no han impedido el funcionamiento verificado, pero deben revisarse al actualizar MediaPipe.

## Backlog recomendado

### Prioridad 0: asegurar la base

- Crear tests unitarios para angulos, normalizacion, seleccion de features y DTW.
- Crear fixtures pequenos y legales que no dependan de los videos originales.
- Validar que un cache pertenece al video correcto mediante metadata o hash.
- Exportar el reporte headless a JSON.
- Documentar un caso esperado de comparacion con resultados reproducibles.

### Prioridad 1: mejorar la experiencia

- Agregar selectores de archivos para referencia y usuario.
- Mostrar progreso durante la extraccion y permitir cancelar.
- Permitir configurar pesos y umbrales sin editar el codigo.
- Mostrar explicaciones mas claras por articulacion o grupo corporal.
- Guardar un video anotado con landmarks y resultados.

### Prioridad 2: validar el modelo

- Reunir un conjunto de intentos etiquetados con consentimiento de las personas participantes.
- Calibrar puntajes y etiquetas con evaluacion humana.
- Estudiar invariancia frente a camara, escala, lateralidad y diferencias corporales.
- Evaluar otros metodos de alineacion o modelos temporales.

## Comprobaciones antes de integrar cambios

Como minimo, ejecutar:

```powershell
uv lock --check
uv sync --locked
uv pip check
uv run --locked python -m compileall -q app
uv run --locked python app\src\test_env.py
uv run --locked python app\src\dance_compare_ui.py --help
uv run --locked python app\src\landmark_saving.py --help
uv run --locked python app\src\realtime_landmarks.py --help
```

Cuando se modifique el pipeline, tambien se debe procesar un video corto y comparar dos secuencias antes de integrar el cambio.

## Como actualizar dependencias

- Agregar una dependencia: `uv add paquete`.
- Retirar una dependencia: `uv remove paquete`.
- Comprobar el lock: `uv lock --check`.
- Instalar exactamente el lock: `uv sync --locked`.

No se debe editar `uv.lock` manualmente.

## Criterio para una entrega saludable

El proyecto se considera listo para entregar cuando una persona nueva puede:

1. Clonar el repositorio.
2. Instalarlo siguiendo el README.
3. Agregar dos videos propios sin modificar el codigo.
4. Verificar landmarks.
5. Procesar y comparar ambas secuencias.
6. Entender las limitaciones del puntaje.
7. Ejecutar las comprobaciones basicas antes de contribuir.

Las decisiones futuras de producto, interfaz y calibracion quedan a cargo del equipo que continua el proyecto.
