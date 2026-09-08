# Dance Match Lab — Visión del Proyecto

## 1. Visión general

**Dance Match Lab** es una plataforma interactiva de baile y actividad física orientada principalmente a estudiantes en contextos escolares.

La visión del proyecto es transformar el baile en una experiencia de ejercicio accesible, interactiva y motivante. En lugar de limitarse a reproducir un video que el estudiante debe imitar, la aplicación busca ser capaz de **interpretar su movimiento, compararlo con una coreografía de referencia y proporcionar retroalimentación sobre su ejecución**.

La experiencia propuesta puede resumirse como:

> **Bailar → analizar el movimiento → recibir feedback → progresar → obtener recompensas → seguir participando.**

El objetivo final no es evaluar qué tan "bien" baila una persona en términos artísticos, sino utilizar tecnología de análisis de movimiento para incentivar la actividad física de una manera entretenida y comprensible para estudiantes.

---

## 2. Problema y oportunidad

Las actividades tradicionales de ejercicio pueden resultar repetitivas o poco atractivas para algunos estudiantes. El baile ofrece una alternativa que combina:

- actividad física;
- coordinación;
- movimiento corporal;
- música;
- aprendizaje de secuencias;
- interacción;
- progresión personal;
- entretenimiento.

Dance Match Lab busca aprovechar estas características mediante una aplicación capaz de convertir una coreografía en una experiencia interactiva.

El estudiante podría seleccionar una coreografía disponible dentro de la plataforma, aprenderla, realizarla frente a una cámara y recibir posteriormente información sobre su ejecución.

La tecnología funciona como una capa adicional sobre la actividad física: **el centro de la experiencia continúa siendo bailar y moverse.**

---

# 3. Experiencia propuesta

Una sesión típica podría seguir el siguiente flujo:

1. El estudiante ingresa a la aplicación.
2. Explora las coreografías disponibles.
3. Selecciona una canción o rutina.
4. Observa la coreografía de referencia.
5. Realiza el baile frente a la cámara.
6. El sistema analiza su movimiento.
7. El estudiante recibe un resultado comprensible.
8. Obtiene progreso y recompensas por participar.
9. Puede intentar mejorar su ejecución o seleccionar una nueva coreografía.

A medida que utiliza la aplicación, puede observar su progreso y participar en diferentes retos o actividades.

El sistema debe favorecer principalmente la **constancia, participación y actividad física**, evitando convertir la experiencia exclusivamente en una competencia por obtener el puntaje biomecánico más alto.

---

# 4. Motor de análisis de baile

Actualmente, el componente tecnológico principal desarrollado es el **motor de análisis y comparación de movimiento**.

Este motor constituye la base sobre la cual puede construirse posteriormente la experiencia completa de Dance Match Lab.

## 4.1 Coreografía de referencia

Cada actividad parte de una ejecución de referencia.

Esta ejecución representa la secuencia de movimientos que el estudiante intentará seguir.

El sistema procesa el movimiento de referencia para obtener una representación computacional de la coreografía que posteriormente pueda compararse con la ejecución del estudiante.

## 4.2 Estimación de pose

A partir del video se realiza estimación de pose humana.

En lugar de analizar directamente todos los píxeles de la imagen, el sistema identifica **landmarks corporales** que representan puntos relevantes del cuerpo.

Esto permite transformar un video en una secuencia temporal de posiciones corporales.

Conceptualmente:

```text
Video
  ↓
Estimación de pose
  ↓
Landmarks corporales
  ↓
Representación del movimiento
```

Este enfoque permite concentrar el análisis en el movimiento corporal y reducir la dependencia de características visuales irrelevantes como ropa, apariencia o fondo.

## 4.3 Extracción de características biomecánicas

Los landmarks por sí solos no representan completamente la calidad o similitud de un movimiento.

Por ello, el motor transforma las posiciones corporales en diferentes características útiles para comparar ejecuciones, incluyendo elementos relacionados con:

- ángulos articulares;
- orientación de segmentos;
- distancias corporales;
- movimiento relativo de diferentes regiones;
- postura;
- simetría;
- velocidad del movimiento;
- características del tronco;
- relaciones espaciales entre articulaciones.

De esta manera, el sistema intenta comparar **cómo se mueve el cuerpo**, y no simplemente si dos coordenadas aparecen exactamente en la misma posición de la imagen.

## 4.4 Alineación temporal

Dos personas pueden ejecutar correctamente una misma coreografía sin hacerlo exactamente a la misma velocidad.

Por esta razón, una comparación estricta frame por frame sería insuficiente.

El motor utiliza técnicas de alineación temporal para encontrar correspondencias entre diferentes momentos de ambas ejecuciones.

Conceptualmente:

```text
Coreografía de referencia
        ↓
Características biomecánicas
        ↓
       DTW
        ↑
Características biomecánicas
        ↑
Ejecución del estudiante
```

El uso de **Dynamic Time Warping (DTW)** permite comparar secuencias incluso cuando existen pequeñas diferencias en el ritmo o velocidad con la que se realizan determinados movimientos.

## 4.5 Scoring

Una vez alineadas las ejecuciones, el sistema puede calcular medidas de similitud.

Estas medidas pueden convertirse posteriormente en información comprensible para el estudiante.

Por ejemplo:

- similitud general;
- desempeño por regiones corporales;
- identificación de segmentos con mayor diferencia;
- evolución durante diferentes partes de la coreografía.

El propósito del score no debería ser emitir una valoración clínica ni determinar objetivamente quién "baila mejor".

Su función dentro de Dance Match Lab es proporcionar **feedback interactivo que motive al estudiante a repetir, explorar y mejorar su movimiento**.

---

# 5. De motor tecnológico a producto

El motor actual resuelve principalmente el problema técnico:

> **¿Cómo comparar computacionalmente dos ejecuciones de una coreografía?**

La visión completa de Dance Match Lab va más allá.

El siguiente paso consiste en convertir este motor en una experiencia diseñada alrededor del estudiante.

```text
                    DANCE MATCH LAB

                 ┌─────────────────┐
                 │  Coreografías   │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │     Bailar      │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ Motor de baile  │
                 │ Pose + análisis │
                 │ + DTW + scoring │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │    Feedback     │
                 └────────┬────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
        ┌───────────┐          ┌─────────────┐
        │ Progreso  │          │ Recompensas │
        └─────┬─────┘          └──────┬──────┘
              └───────────┬───────────┘
                          ↓
                 Nuevas actividades
```

---

# 6. Gamificación y recompensas

La gamificación puede convertirse en uno de los principales mecanismos de adherencia de la plataforma.

El estudiante podría obtener recompensas por acciones como:

- completar una coreografía;
- realizar actividad física regularmente;
- probar nuevas rutinas;
- completar retos;
- mantener rachas de actividad;
- mejorar respecto a sus propios resultados;
- participar en actividades colectivas;
- alcanzar determinados objetivos.

Las recompensas podrían representarse mediante:

- puntos;
- experiencia;
- niveles;
- logros;
- insignias;
- elementos visuales desbloqueables;
- nuevos retos;
- contenido adicional.

Un principio importante sería **recompensar la participación y la constancia**, no únicamente el desempeño.

Un estudiante que realiza actividad física regularmente debería poder progresar aunque su similitud con la coreografía de referencia no sea perfecta.

---

# 7. Componente social

A largo plazo, Dance Match Lab puede incorporar determinadas dinámicas características de una red social, pero diseñadas específicamente para un entorno educativo.

El objetivo social no sería construir una plataforma centrada en publicar información personal de estudiantes, sino utilizar mecanismos sociales para aumentar la motivación.

Algunas posibilidades incluyen:

- retos entre grupos;
- objetivos colectivos;
- logros compartidos;
- actividades de curso;
- rankings cuidadosamente diseñados;
- desafíos de coreografías;
- progreso colectivo;
- eventos o campañas escolares.

Esto permitiría generar una sensación de comunidad alrededor de la actividad física sin requerir necesariamente un modelo tradicional de perfiles públicos, fotografías, videos personales o publicaciones abiertas.

---

# 8. Privacidad como principio de arquitectura

Debido a que Dance Match Lab está pensado para contextos escolares y potencialmente para menores de edad, la privacidad no debe tratarse únicamente como una política escrita.

Debe formar parte de la **arquitectura técnica del sistema**.

El principio general es:

> **Si un dato personal no necesita existir en el servidor, no debería enviarse al servidor.**

---

## 8.1 Procesamiento local

Siempre que sea técnicamente viable, el procesamiento del video y la estimación de movimiento deberían realizarse **localmente en el dispositivo**.

Idealmente:

```text
Cámara
  ↓
Procesamiento local
  ↓
Estimación de pose
  ↓
Análisis del movimiento
  ↓
Resultado
```

en lugar de:

```text
Cámara
  ↓
Video
  ↓
Internet
  ↓
Servidor
  ↓
Procesamiento
```

Esto permitiría reducir considerablemente la cantidad de información sensible que abandona el dispositivo.

---

## 8.2 No almacenar videos por defecto

Los videos utilizados para analizar el movimiento no deberían almacenarse permanentemente por defecto.

Una vez realizada la inferencia necesaria, el material visual podría descartarse.

Esto reduce riesgos asociados a:

- imágenes de menores;
- identificación facial;
- filtraciones;
- accesos no autorizados;
- reutilización posterior del contenido;
- almacenamiento innecesario de información personal.

---

## 8.3 Minimización de datos

La plataforma debería recolectar únicamente la información estrictamente necesaria para proporcionar sus funciones.

Siempre que sea posible, el progreso podría representarse mediante datos no directamente identificables, como:

```text
Sesión completada
Puntaje
Coreografía
Progreso
Logros
```

sin necesidad de almacenar el video original utilizado para producirlos.

Incluso estos datos deberán evaluarse según su necesidad antes de decidir almacenarlos.

---

# 9. Privacidad en las funciones sociales

La incorporación de características sociales no debe implicar automáticamente convertir a los estudiantes en perfiles públicamente identificables.

Por diseño se debería evitar publicar innecesariamente:

- nombres completos;
- fotografías;
- videos de estudiantes;
- información académica;
- ubicación;
- datos biométricos;
- identificadores personales;
- historial individual de actividad.

Las interacciones sociales podrían construirse utilizando representaciones como:

- avatares;
- alias controlados;
- equipos;
- grupos;
- clases;
- logros;
- métricas agregadas.

Por ejemplo, en lugar de publicar:

> "Juan Pérez obtuvo 87 % bailando X"

el sistema podría mostrar dinámicas colectivas como:

> "El grupo completó 124 sesiones esta semana."

El objetivo es obtener los beneficios motivacionales de una experiencia social **sin convertir la exposición de datos personales en un requisito para participar**.

---

# 10. Separación entre análisis y vigilancia

Dance Match Lab no está concebido como un sistema de vigilancia de estudiantes.

El hecho de utilizar visión por computador para interpretar movimiento no implica que la plataforma necesite identificar permanentemente a la persona que aparece frente a la cámara.

Existe una diferencia fundamental entre:

**analizar un cuerpo para interpretar un movimiento**

y

**identificar a una persona a partir de su cuerpo o rostro.**

El proyecto debe intentar mantenerse deliberadamente en el primer escenario.

La cámara funciona como un sensor temporal para interpretar movimiento durante una actividad, no como un mecanismo destinado a construir registros audiovisuales permanentes de los estudiantes.

---

# 11. Principios del producto

El desarrollo futuro de Dance Match Lab debería mantener los siguientes principios:

### Movimiento primero

La finalidad principal es incentivar actividad física mediante el baile.

### Feedback antes que evaluación

El análisis computacional debe ayudar al estudiante a interactuar con la actividad, no funcionar como una evaluación clínica.

### Progreso personal

La plataforma debería valorar la mejora respecto al propio estudiante y no solamente la comparación entre personas.

### Participación recompensada

La constancia y realización de actividad física deben tener valor dentro del sistema independientemente del nivel de habilidad.

### Social sin exposición innecesaria

Las dinámicas sociales deben diseñarse para proporcionar motivación sin depender de la publicación de información personal.

### Minimización de datos

Recolectar y conservar únicamente aquello estrictamente necesario.

### Procesamiento local cuando sea posible

La arquitectura debe favorecer que imágenes, video y análisis sensibles permanezcan dentro del dispositivo.

### Privacidad por diseño

Las decisiones sobre nuevas funcionalidades deben considerar sus implicaciones de privacidad desde su concepción y no únicamente después de implementarlas.

---

# 12. Estado actual y visión futura

Es importante diferenciar lo que constituye actualmente el proyecto de aquello que representa su evolución prevista.

## Estado actual

Actualmente se ha desarrollado principalmente la base tecnológica necesaria para analizar y comparar ejecuciones de baile.

El trabajo realizado incluye el pipeline relacionado con:

- procesamiento de video;
- estimación de pose;
- landmarks corporales;
- extracción de características;
- representación biomecánica;
- alineación temporal;
- comparación de ejecuciones;
- generación de scores y feedback.

Este componente constituye el **motor de baile de Dance Match Lab**.

## Visión futura

La visión de producto contempla construir sobre este motor:

- catálogo de coreografías;
- experiencia interactiva para estudiantes;
- sistema de progreso;
- recompensas;
- niveles y logros;
- retos individuales y colectivos;
- actividades escolares;
- componentes sociales seguros;
- feedback progresivamente más útil;
- arquitectura orientada a privacidad;
- procesamiento local cuando sea técnicamente viable.

Por tanto, el motor de comparación no constituye por sí solo el producto final.

Es la infraestructura tecnológica que permite construir una plataforma más amplia orientada a utilizar **baile, tecnología y gamificación para incentivar la actividad física en estudiantes**.

---

# 13. Objetivo a largo plazo

Dance Match Lab busca explorar una forma diferente de relacionar tecnología y actividad física dentro del contexto educativo.

La visión final es una plataforma donde un estudiante pueda abrir una coreografía, bailar, recibir feedback automático, avanzar, desbloquear recompensas y participar en experiencias con otros estudiantes sin que para ello sea necesario convertir sus videos o datos personales en contenido almacenado o públicamente disponible.

En una frase:

> **Dance Match Lab busca convertir el ejercicio mediante baile en una experiencia interactiva, medible, progresiva, social y divertida, utilizando análisis de movimiento mientras mantiene la privacidad como una restricción fundamental de diseño.**
