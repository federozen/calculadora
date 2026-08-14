# Developer / Production Bootstrap · 3.8.55

Este paquete reduce el handoff a dos trabajos externos: **conectar el feed Opta real** y **desplegar la infraestructura**. La matemática sigue detrás de `lpf_services.calculate()`.

## Arranque rápido

```bash
make install-dev
make check
make acceptance
make api
```

Swagger queda en `/docs`; health en `/health`; readiness en `/ready`.

Para staging sin Opta:

```bash
python tools/build_snapshot.py tests/fixtures/production/golden_provider_payload.json snapshot.json
export LPF_SNAPSHOT_FILE=$PWD/snapshot.json
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

La API inyecta ese snapshot si el request no lo envía. Cuando exista Opta, reemplazar el loader por uno que construya la misma foto canónica; los endpoints no cambian.

## Endpoints HTTP v1

- `GET /health`
- `GET /ready`
- `GET /v1/capabilities`
- `POST /v1/standings`
- `POST /v1/preview`
- `POST /v1/objective-points`
- `POST /v1/objective-chances`
- `POST /v1/definition`
- `POST /v1/relegation`
- `POST /v1/competition-batch`

`ContractError` se mapea a HTTP 422. La capa HTTP no contiene reglas LPF.

## Opta

`providers/opta.py` fija tres piezas:

```text
OptaTransport.load_bundle()
        ↓
OptaNormalizer.normalize()
        ↓
OptaProvider.load() -> ProviderData
        ↓
snapshot schema 3
```

La plantilla no inventa endpoints ni campos porque esos detalles dependen del producto Opta contratado. Desarrollo sólo debe implementar transporte + normalización y demostrar que una foto equivalente produce el mismo `snapshot_id` que Current/CSV.

## Empaquetado

`pyproject.toml` declara explícitamente los módulos runtime y los paquetes `api`/`providers`; `legacy`, `data`, tests, herramientas e históricos quedan fuera del wheel. La dependencia de Streamlit pasa al extra `ui`; una imagen API puede instalar `.[api]` sin traer Streamlit.

Construcción de imagen de referencia:

```bash
docker build -f Dockerfile.api -t calculadora-lpf-api .
```

## Bundle mínimo de runtime

El repo completo sigue siendo la fuente de desarrollo. Para una entrega operativa puede generarse:

```bash
make runtime-bundle
```

`tools/build_runtime_bundle.py` incluye sólo los módulos Python declarados en Setuptools, `api/`, `providers/`, contrato/documentación esencial y archivos de contenedor. Excluye `tests/`, `legacy/`, `_original_referencia/`, patches y herramientas de desarrollo.

## Acceptance kit

`make acceptance` ejecuta, sin red externa:

1. snapshot canónico desde ProviderData;
2. los **7 casos dorados**, uno por cada operación pública;
3. health/readiness/capabilities;
4. smoke HTTP de cálculo;
5. verificación del `snapshot_id`.

Fixtures:

- `tests/fixtures/production/golden_provider_payload.json`
- `tests/fixtures/production/golden_cases.json`

Son sintéticos y existen para congelar contratos, no para representar una tabla LPF real.

## Definition of Done para Desarrollo

Antes de producción deberían estar verdes estos puntos:

- OptaTransport y OptaNormalizer implementados con payloads reales.
- IDs Opta ↔ nombres canónicos validados.
- Snapshot schema 3 válido y trazabilidad real.
- Misma foto competitiva → mismo `snapshot_id`.
- `make check` verde en CI.
- `make acceptance` verde con Opta además de los fixtures sintéticos.
- `/health` y `/ready` monitorizados.
- Autenticación/rate limiting definidos según infraestructura de AGEA si la API no es exclusivamente interna.
- Secrets fuera del repositorio.
- Logs, timeouts y alertas integrados con la plataforma de despliegue.
- Pruebas de carga sobre `objective_chances` y endpoints que disparan simulación.

## Plazo orientativo después del handoff

Con acceso a credenciales, documentación y ejemplos reales de Opta desde el día 1:

- **1–2 días:** levantar repo, API y staging con snapshot de archivo.
- **2–5 días:** transporte/normalizador Opta + equivalencia de snapshot.
- **2–4 días:** infraestructura, secrets, logs, health/readiness y pruebas integradas.
- **2–5 días:** validación editorial/casos reales + carga + salida controlada.

Un equipo de dos desarrolladores puede apuntar a **staging en 3–5 días hábiles** y a una **primera producción en 7–12 días hábiles**, siempre que Opta y la infraestructura estén disponibles sin bloqueos. Si el feed contratado requiere investigación o faltan IDs/documentación, ese riesgo queda fuera del código y puede extender el plazo.
