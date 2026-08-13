# Guía de datos y auditoría

## Objetivo

Evitar que una fórmula correcta se aplique sobre una tabla vieja o incompatible.

## Prioridad de fuentes

1. Resultado partido a partido confirmado.
2. Fixture oficial vigente.
3. Tabla de zonas actualizada.
4. Foto fija del Apertura validada.
5. Tabla Anual directa validada.
6. Inferencia por PJ como último recurso.

## Semáforo

- **Verde:** la base puede utilizarse.
- **Amarillo:** hay inferencias o advertencias; revisar antes de publicar.
- **Rojo:** el dominio afectado está bloqueado.

Un bloqueo de Promedios no debería impedir una ficha de playoffs. Un bloqueo de Tabla Anual sí impide copas y descenso por Anual.

## Postergados

Cada encuentro conserva la jornada original. Nunca se asume que las primeras N fechas fueron las jugadas.

Si faltan marcadores explícitos, la aplicación puede inferir algunos partidos por PJ, pero los marca como `played_inferred`. Completarlos elimina la ambigüedad.

## Tabla Anual

La Anual preferida se obtiene con:

```text
Apertura fijo + Clausura actual
```

Por eso, al cargar un resultado del Clausura, la Anual se mueve automáticamente.

Si no existe una foto confiable del Apertura, la Anual directa debe cumplir todos los controles. Si no los cumple, las cuentas de copas quedan bloqueadas.

## Promedios

Revisar:

- puntos históricos;
- PJ históricos;
- puntos y PJ de la temporada actual;
- recién ascendidos;
- nombres y aliases.

## Procedimiento de actualización

1. Cargar la fuente nueva.
2. Abrir Datos y auditoría.
3. Comparar equipos, PJ, puntos, goles y pendientes.
4. Corregir aliases o marcadores faltantes.
5. Reconciliar.
6. Volver al Explorador.
7. Descargar un respaldo antes de una carga masiva.

La actualización automática coteja los resultados de ESPN y FutbolArgentino.com. Puede completar una fuente parcial con otra, pero sólo aplica la foto si los marcadores reconstruyen exactamente las estadísticas publicadas de ambas zonas. Una respuesta incompleta nunca reemplaza la última base válida.

Playwright queda como alternativa futura únicamente si el proveedor deja de entregar los partidos en el HTML inicial. En la implementación actual no agrega precisión y encarece el despliegue con un navegador completo.

## Conflictos

No corregir una inconsistencia editando solamente la Tabla Anual. Primero comprobar:

- si falta un resultado;
- si un postergado aparece como jugado;
- si la zona está atrasada;
- si la foto del Apertura fue derivada desde una Anual inconsistente;
- si un alias generó dos equipos diferentes.


## Copa Argentina

La aplicación guarda una foto de los equipos que siguen en competencia porque esa información puede cambiar las líneas de Libertadores y Sudamericana.

En **Datos y auditoría** se puede:

1. editar la lista manualmente;
2. cotejar partidos pendientes con ESPN;
3. restaurar la foto de octavos incluida;
4. abrir el fixture oficial;
5. registrar al reemplazo de ARGENTINA 3 si el campeón ya tenía plaza.

La fuente oficial debe prevalecer. El cotejo ESPN no se aplica cuando devuelve una fase incompleta.

## Trazabilidad y frescura del snapshot · 3.8.50

Cada snapshot canónico nuevo conserva metadatos de procedencia separados de los cálculos:

- **Snapshot ID:** huella del contenido competitivo. Sirve para demostrar que dos proveedores entregaron la misma foto aunque tengan distinta procedencia.
- **Fuente / proveedor:** quién entregó la entrada (`current`, `csv`, futuro `opta`) y qué fuentes concretas declaró.
- **Actualizado / data as of:** timestamp informado por la fuente. Si no existe, la app muestra que la antigüedad es desconocida; no inventa una hora.
- **Cobertura:** cantidad de resultados confirmados, pendientes, partidos del fixture, última fecha oficial con resultados confirmados y fecha máxima del fixture.
- **Calidad:** `ok`, `warning` o `blocked`, cantidad de incidencias y dominios bloqueados.

En **Datos y auditoría → Contrato público usado por Streamlit** se puede ver esta información antes de publicar una conclusión. `generated_at` es la hora de construcción del snapshot y no debe confundirse con la hora de actualización de la fuente.

Para una integración externa, `ProviderData.provenance` debe usar timestamps ISO-8601 y no debe deducir frescura a partir del número de fecha ni del PJ. Un futuro OptaProvider debe trasladar el timestamp real que entregue Opta; si no existe, debe dejarlo vacío.
