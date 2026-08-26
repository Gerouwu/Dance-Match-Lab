# Dance Match Lab

Dance Match Lab es un prototipo general para comparar dos secuencias de baile mediante landmarks corporales, angulos articulares y caracteristicas biomecanicas. Un video se toma como referencia y el otro como la ejecucion que se desea evaluar; el proyecto no depende de un video, identificador o coreografia especificos.

El sistema presenta ambas secuencias lado a lado con landmarks, conexiones del esqueleto y angulos relevantes. Tambien calcula similitud global, resultados por grupos corporales y resultados por intervalos usando Dynamic Time Warping (DTW).

El objetivo es una comparacion flexible de coreografias, no una evaluacion clinica rigida. El algoritmo tolera diferencias naturales de tiempo, velocidad, amplitud y estilo, y selecciona las features mas utiles generadas por `biomech_features.py`.

La interfaz muestra puntajes globales, metricas por segmentos y mensajes interpretativos como `Excellent`, `Good`, `Out of Sync` o `Different Movement`.

## Estado actual

Este es un prototipo experimental. Actualmente permite:

- Comparar dos videos de baile proporcionados por el usuario.
- Extraer landmarks con MediaPipe.
- Visualizar ambas secuencias lado a lado.
- Dibujar esqueleto y angulos articulares seleccionados.
- Calcular similitud global con DTW.
- Calcular resultados de brazos, piernas, torso y movimiento.
- Generar metricas y feedback por intervalos.

## Estructura del proyecto

```text
.
|-- app/
|   `-- src/
|       |-- biomech_features.py        # Extraccion de features biomecanicas
|       |-- dance_compare_ui.py        # Interfaz y entrada principal
|       |-- dance_similarity.py        # DTW, puntajes, seleccion e intervalos
|       |-- funciones_pose_engine.py   # Extraccion y dibujo con MediaPipe
|       |-- landmark_saving.py         # Procesamiento de uno o varios videos
|       |-- realtime_landmarks.py      # Landmarks desde camara o video
|       `-- test_env.py                # Validacion del entorno
|-- output/
|   |-- features/                      # Matrices procesadas, no versionadas
|   `-- landmarks/                     # Landmarks procesados, no versionados
|-- videos/                            # Videos locales, no versionados
|-- pyproject.toml                     # Dependencias directas
|-- uv.lock                            # Versiones reproducibles
`-- run_dance_compare.ps1              # Lanzador para Windows
```

## Requisitos

El proyecto usa [uv](https://docs.astral.sh/uv/) para instalar Python y las dependencias bloqueadas.

Dependencias principales:

- Python 3.10
- OpenCV
- MediaPipe
- NumPy
- SciPy
- Pillow
- Tkinter

Tkinter viene incluido con la instalacion estandar de CPython en Windows. La interfaz principal usa Tkinter.

## Preparar el entorno

Instala `uv`, clona el repositorio y ejecuta:

```powershell
uv python install 3.10
uv sync --locked
```

`uv` crea `.venv` y utiliza la version definida en `.python-version`. Verifica el entorno sin activarlo manualmente:

```powershell
uv run --locked python app\src\test_env.py
```

Ejecuta los comandos del proyecto mediante `uv run --locked` para usar las versiones exactas de `uv.lock`.

## Agregar videos propios

El repositorio no incluye los videos usados durante el desarrollo por su tamano y privacidad. Cada usuario debe proporcionar sus propios archivos.

1. Crea la carpeta local `videos/` si todavia no existe:

```powershell
New-Item -ItemType Directory -Force videos
```

2. Copia o arrastra al menos dos videos dentro de esa carpeta. Por ejemplo:

```text
videos/
  baile_referencia.mp4
  baile_usuario.mp4
```

Tambien puedes pasar rutas absolutas y conservar los archivos en otra ubicacion. Se admiten los formatos que OpenCV pueda abrir; para este flujo se recomiendan `.mp4`, `.avi`, `.mov` o `.mkv`.

Para mejorar la deteccion:

- Muestra el cuerpo completo durante la mayor parte del video.
- Usa iluminacion suficiente y evita oclusiones.
- Procura que solo aparezca una persona principal.
- Usa un encuadre y angulo de camara parecidos en ambas secuencias.
- Emplea nombres de archivo distintos, porque el nombre se usa para identificar el cache.

La estructura vacia de `videos/`, `output/landmarks/` y `output/features/` si se versiona para que aparezca al clonar el repositorio. Su contenido permanece ignorado por Git: los videos y resultados procesados son locales y no deben subirse al repositorio.

## Ver landmarks en tiempo real

Para abrir la camara principal y dibujar el esqueleto y los angulos en tiempo real:

```powershell
uv run --locked python app\src\realtime_landmarks.py --camera 0
```

Si tienes varias camaras, prueba `--camera 1` o `--camera 2`. Para visualizar los landmarks sobre un video local:

```powershell
uv run --locked python app\src\realtime_landmarks.py --video videos\baile_usuario.mp4
```

La camara se refleja horizontalmente de forma predeterminada; los archivos de video no. Puedes cambiarlo con `--mirror` o `--no-mirror`. Presiona `Q` dentro de la ventana para salir.

## Procesar videos

No es obligatorio preprocesar manualmente. La comparacion puede extraer y guardar landmarks/features de ambos videos al usar `--cache-missing`.

Para procesarlos antes de comparar:

```powershell
uv run --locked python app\src\landmark_saving.py videos\baile_referencia.mp4 videos\baile_usuario.mp4
```

Si no pasas rutas, el comando procesa todos los videos compatibles que encuentre directamente en `videos/`:

```powershell
uv run --locked python app\src\landmark_saving.py
```

Los resultados se guardan como:

```text
output/
  landmarks/
    baile_referencia_landmarks.npy
    baile_usuario_landmarks.npy
  features/
    baile_referencia_features.npz
    baile_usuario_features.npz
```

## Comparar dos videos

El primer archivo representa la secuencia de referencia. El segundo representa la secuencia que se desea comparar.

En Windows, abre la interfaz con:

```powershell
.\run_dance_compare.ps1 `
  --reference-video videos\baile_referencia.mp4 `
  --user-video videos\baile_usuario.mp4 `
  --cache-missing
```

El comando equivalente en cualquier sistema es:

```powershell
uv run --locked python app/src/dance_compare_ui.py --reference-video videos/baile_referencia.mp4 --user-video videos/baile_usuario.mp4 --cache-missing
```

Para calcular e imprimir el reporte sin abrir la interfaz:

```powershell
.\run_dance_compare.ps1 --reference-video videos\baile_referencia.mp4 --user-video videos\baile_usuario.mp4 --cache-missing --headless-report
```

Para comprobar el flujo comparando un video consigo mismo:

```powershell
.\run_dance_compare.ps1 --reference-video videos\baile_referencia.mp4 --demo --cache-missing --headless-report
```

La primera ejecucion tarda mas porque extrae los landmarks y las features. Las siguientes ejecuciones reutilizan automaticamente los archivos de `output/` cuyo nombre coincide con el nombre del video.

## Controles de la interfaz

Cuando la interfaz esta abierta:

- `Space`: pausar o continuar.
- `R`: reiniciar la reproduccion.
- `Q` o `Esc`: cerrar.

## Como funciona la comparacion

El proceso tiene cuatro etapas:

1. Extraer landmarks corporales de cada video con MediaPipe Pose.
2. Convertirlos en features biomecanicas.
3. Seleccionar y normalizar las features relevantes para baile.
4. Alinear ambas secuencias con DTW y convertir las distancias en puntajes.

DTW permite comparar una misma coreografia aunque existan retrasos o diferencias de velocidad, por lo que resulta mas flexible que comparar los videos cuadro por cuadro.

## Features utilizadas

El conjunto biomecanico puede contener cientos de columnas. El puntaje prioriza:

- Landmarks corporales normalizados.
- Angulos articulares principales.
- Orientaciones y longitudes de segmentos.
- Distancias corporales importantes.
- Velocidades y energia de movimiento.
- Simetria, tronco y postura.

Se descartan o reducen:

- Escala corporal sin normalizar.
- Flags individuales de visibilidad.
- Aceleraciones con mucho ruido.
- Features con demasiados valores faltantes.

Las features seleccionadas se normalizan antes de aplicar DTW.

## Puntajes

El sistema calcula:

- Similitud global de `0` a `100`.
- Puntajes de brazos, piernas, torso y movimiento.
- Puntajes por intervalos.
- Mensajes interpretativos por segmento.

Los mensajes son deliberadamente flexibles:

- `Excellent`: patron, postura y ritmo muy similares.
- `Good`: similitud aceptable con variaciones naturales.
- `Out of Sync`: movimiento parecido con diferencia temporal.
- `Different Movement`: diferencia biomecanica clara respecto de la referencia.

## Usar landmarks y features preprocesados

Si los archivos fueron procesados con `landmark_saving.py` y conservan el nombre esperado dentro de `output/`, se cargan automaticamente. Tambien pueden indicarse rutas explicitas:

```powershell
.\run_dance_compare.ps1 `
  --reference-video videos\baile_referencia.mp4 `
  --reference-landmarks output\landmarks\baile_referencia_landmarks.npy `
  --reference-features output\features\baile_referencia_features.npz `
  --user-video videos\baile_usuario.mp4 `
  --user-landmarks output\landmarks\baile_usuario_landmarks.npy `
  --user-features output\features\baile_usuario_features.npz
```

Formatos de landmarks admitidos:

- `.npy` guardado como pares `(frame_id, landmarks)`.
- `.csv` con `33 * (x, y, z)` coordenadas.
- `.csv` con `33 * (x, y, z, visibility)` coordenadas.

Si falta la visibilidad, se completa con `1.0`.

## Flujo recomendado de desarrollo

1. Guarda cada video con un nombre descriptivo y unico.
2. Usa `uv run --locked` o `run_dance_compare.ps1`.
3. Revisa primero la deteccion con `realtime_landmarks.py`.
4. Genera o conserva landmarks/features para experimentos repetidos.
5. Ajusta los pesos en `dance_similarity.py` a medida que evolucione el modelo.

## Limitaciones

- No es una herramienta de evaluacion biomecanica clinica.
- El puntaje es heuristico y requiere calibracion con mas ejemplos.
- El angulo, encuadre, oclusiones y calidad de deteccion afectan los resultados.
- DTW tolera diferencias temporales, pero no corrige coreografias completamente distintas.
- Los mensajes actuales se basan en reglas y deben validarse con usuarios reales.

## Ideas futuras

- Selector visual de archivos.
- Exportacion de reportes a CSV o JSON.
- Videos anotados con el resultado.
- Catalogo de coreografias de referencia.
- Puntajes por articulacion.
- Feedback temporal mas preciso.
- Calibracion con intentos de baile etiquetados.

## License

MIT License
