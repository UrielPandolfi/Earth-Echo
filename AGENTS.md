# Reglas de Earth Echo

Leé `PROGRESS.md`, `docs/arquitectura.md`, `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y el PNG `Earth Echo Global Environmental Observatory.png` antes de modificar el proyecto. El PNG manda en lo visual. La especificación y el catálogo mandan en el significado de los datos. Esos tres archivos no se editan para “implementar” una fase.

## Datos

- `real` y `demo` son modos explícitos. Un fallo de fuente produce un resultado no disponible, nunca un cambio silencioso a demo.
- Un dato faltante queda `missing` y su valor es `null`. No se reemplaza por cero.
- La probabilidad es `null` salvo que exista una definición. No inventes confianza, causalidad, fechas de desastre ni un estado “saludable”.
- Todo contador sale de una consulta definida. El catálogo tiene 31 fenómenos especificados; eso no es un conteo de señales vivas.
- Conservá origen, unidad, calidad, tiempo y alcance. Las unidades nativas se convierten solo con una función probada.
- El almacenamiento y el transporte usan UTC e ISO 8601 con zona. La interfaz puede mostrar otra zona, pero debe decir cuál.
- GeoJSON usa longitud y latitud en WGS84. Una síntesis regional identifica la región. Una malla no se convierte en pines por comodidad.
- Una geometría que cruza el antimeridiano se parte en partes que no saltan más de 180 grados, y la extensión lo declara.

## Código

- La interfaz, el adaptador del globo, los contratos, los conectores y la ciencia viven separados. La ciencia no se calcula dentro de un componente visual.
- Los modelos Pydantic son la fuente de los contratos. `contracts/schemas/earth-echo.schema.json` y `apps/web/src/domain/generated.ts` se generan y se comprueban; no se editan a mano.
- No crees detectores vacíos ni un sistema de plugins para aparentar avance. Cada capacidad declara si está especificada, conectada, experimental o validada para un alcance.
- No agregues otra librería de mapas, otro servidor ni otra base de datos sin una necesidad ya presente.
- Los comandos deben funcionar con rutas que contienen espacios.
- No pidas secretos por el chat. Nombrá la variable y cómo configurarla en local. No uses el prefijo `VITE_` para tokens.

## Fases

Implementá solo la fase pedida. Actualizá `PROGRESS.md` con evidencia y limitaciones. Las decisiones duraderas van en `docs/arquitectura.md`, sin copiar todo el historial.
