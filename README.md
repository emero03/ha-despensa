# Despensa

Integración de Home Assistant para llevar el inventario de lo que tienes en casa. Se ve como un armario: cada balda es una sección (frutas, lácteos, despensa, limpieza…) con los mismos iconos y colores que [Cesta](https://github.com/emero03/ha-cesta), y cada producto muestra cuántas unidades te quedan.

- **Enlazada con Cesta**: lo que marcas como comprado en la Cesta se suma aquí solo, en su balda. Si en la Cesta pulsas «Deshacer», se resta.
- **Stock mínimo por producto**: al llegar a él, el producto sale con una **!** en la esquina superior derecha y pasa a «Por reponer».
- **Botón «Añadir a la Cesta»** en cada producto, y «Añadir lo que falta a la Cesta» para todos a la vez (o automático al llegar al mínimo, si lo activas).
- **Voz**: «He usado dos latas de atún», «Se ha acabado la leche», «¿Cuánto arroz queda?», «¿Qué falta?», «Añade lo que falta a la cesta».
- **Movimientos**: qué se ha usado, qué ha llegado de la Cesta y qué se ha corregido, con **Deshacer**.
- **Unidades por compra**: si siempre compras la leche en pack de 6, cada compra suma 6. Si en la Cesta pones «6 uds» de detalle, suma 6 esa vez.
- **Panel en la barra lateral**, **tarjeta para paneles de control**, **sensor «Por reponer»**, **evento al llegar al mínimo** y **acciones** para automatizaciones.

Todo se guarda en local, en tu Home Assistant. No usa servicios externos.

## Cómo se enlaza con Cesta

Despensa no modifica Cesta. Escucha sus cambios (igual que su panel) y:

| En Cesta… | En Despensa… |
| --- | --- |
| Marcas algo como comprado (panel, tarjeta, `todo.cesta` o voz) | Suma las unidades. Si no estaba, lo crea en su balda con el icono de Cesta. |
| Pulsas «Deshacer» justo después | Resta lo que había sumado. |
| Vuelves a añadir a la lista algo de «Comprado recientemente» | No cambia nada: sí lo compraste. |
| Cambias el orden o los colores de los departamentos | Las baldas cambian igual. |
| Tienes un producto en la lista | Su icono lleva un carrito y no se vuelve a añadir. |

Lo que compraste antes de instalar Despensa no se importa. Si quitas un producto de la despensa con «Quitar y no añadirlo al comprarlo en la Cesta», las compras de ese producto se ignoran (se puede deshacer en ⚙️ Ajustes).

Sin Cesta, Despensa funciona igual (con las secciones de serie); solo faltan los botones de la Cesta.

## Instalación

### Con HACS (recomendado)

1. Sube esta carpeta a un repositorio de GitHub.
2. En HACS → menú ⋮ → **Repositorios personalizados**, añade la URL del repositorio con el tipo **Integración**.
3. Busca **Despensa** en HACS, instálala y reinicia Home Assistant.
4. Ve a **Ajustes → Dispositivos y servicios → Añadir integración** y busca **Despensa**.

### Manual

1. Copia la carpeta `custom_components/despensa` dentro de `config/custom_components/` de tu Home Assistant.
2. Reinicia Home Assistant.
3. **Ajustes → Dispositivos y servicios → Añadir integración → Despensa**.

Al añadirla aparece **Despensa** en la barra lateral. Requiere Home Assistant 2025.1 o posterior (probada en 2026.2, junto a Cesta 1.0.0).

## Uso

| Gesto | Qué hace |
| --- | --- |
| Escribir en «Añadir a la despensa…» | Busca en el catálogo y en lo que ya tienes. Si ya lo tienes, suma uno; si no, lo añade con 1. |
| Escribir varios separados por comas | `arroz, garbanzos, sal` + Intro los añade todos. |
| Tocar un producto | Abre su ficha: **−** / **+** para usar o reponer, «Se ha acabado», «Añadir a la Cesta», el mínimo, la unidad (bricks, latas…) y cuánto suma cada compra. |
| «Nombre, icono y balda» en la ficha | Cambia el nombre, el emoji o la balda. Los cambios se guardan al cerrar la ficha. |
| Chips de arriba | **Todo**, **Por reponer** (solo lo que lleva **!**) y **En la Cesta**. |
| «Añadir … a la Cesta» en «Por reponer» | Añade a la Cesta todo lo que ha llegado al mínimo y aún no está en la lista. |
| Tocar un movimiento | Abre la ficha de ese producto. |
| ⚙️ Ajustes | Mínimo para productos nuevos, qué hacer con lo que llega de la Cesta, Cesta automática y frases de voz. |

### El stock mínimo y la **!**

Cada producto tiene su propio mínimo («Avisar cuando queden»). Cuando el stock llega a ese número (o baja de él), aparece la **!**: ámbar si aún queda algo, roja si se ha acabado. Con «Sin aviso» no sale nunca.

Los productos nuevos empiezan con mínimo 0 (avisa al acabarse); puedes cambiarlo en ⚙️ Ajustes.

## Tarjeta para paneles de control

Edita un panel → **Añadir tarjeta** → **Despensa**, o en YAML:

```yaml
type: custom:despensa-card
title: Nevera                 # opcional
departments:                  # opcional: solo estas baldas (id o nombre)
  - lacteos
  - Carnicería
  - bebidas
filter: low                   # opcional: empezar mostrando solo lo que hay que reponer
show_low: true                # opcional: sección «Por reponer»
show_log: true                # opcional: sección «Movimientos»
```

Con `departments` puedes tener una tarjeta por mueble real: la nevera, el armario de limpieza, el del baño…

## Voz

### Assist (Home Assistant Voice, la app del móvil, el reloj, satélites ESPHome)

Funciona sin configurar nada: al cargar, Despensa registra estas frases en español en Assist.

| Dices | Hace |
| --- | --- |
| «He usado dos latas de atún», «Hemos gastado un yogur», «Apunta que he cogido el último huevo» | Resta y lo apunta como usado. |
| «Se ha acabado la leche», «He terminado el café», «He gastado todo el arroz» | Lo deja a cero. |
| «He comprado tres paquetes de pasta», «Añade garbanzos a la despensa» | Suma (o lo crea). |
| «¿Cuánto arroz queda?», «¿Nos quedan huevos?», «¿Hay atún en la despensa?» | Dice cuánto queda. |
| «¿Qué falta?», «¿Qué hay que comprar?», «¿Qué se está acabando?» | Lee lo que está por reponer. |
| «Añade lo que falta a la cesta» | Lo pasa todo a la Cesta. |

Entiende cantidades en número o en palabra («dos», «media docena», «un par de»), quita «latas de», «bricks de», «paquetes de»… para encontrar el producto, y reconoce singular y plural sin tildes («yogur» → Yogures, «atun» → Atún en lata). Si hay dos productos parecidos («atún» con Atún en lata y Atún fresco), te dice cuáles para que lo repitas con el nombre exacto.

Las frases no tapan las de Home Assistant (luces, temporizadores, persianas…): los tests lo comprueban con miles de frases de ejemplo de Assist en español. Se pueden desactivar en ⚙️ Ajustes.

Para añadir a la lista un producto suelto, usa la propia Cesta: «Añade leche a la lista Cesta».

### Agentes de conversación con IA

Si usas un agente con IA (OpenAI, Claude, Google Gemini, Ollama…) con la opción **Controlar Home Assistant** (API de Assist), ese agente ve las acciones de Despensa como herramientas y las usa cuando le hablas de la despensa con tus propias palabras.

### Alexa

Despensa registra los intents `DespensaUseItem`, `DespensaEmptyItem`, `DespensaAddItem`, `DespensaGetStock`, `DespensaListLow` y `DespensaAddLowToCesta`, que la integración [Alexa (skill personalizada)](https://www.home-assistant.io/integrations/alexa.intent/) de Home Assistant entiende sin `intent_script`. En `alexa/modelo-es-ES.json` tienes el modelo de interacción listo para pegar en la consola de desarrolladores de Alexa (nombre de invocación: «mi despensa»). Se usa así: «Alexa, dile a mi despensa que he usado dos latas de atún».

Necesita que tu Home Assistant sea accesible desde internet por HTTPS (Nabu Casa o tu propio dominio). Google Assistant no permite frases personalizadas; con Google, usa la app de Home Assistant como asistente del móvil.

## Sensor y evento

- `sensor.despensa_por_reponer`: cuántos productos han llegado a su mínimo. Atributos: `productos` (nombres), `detalle` (stock, mínimo, unidad, si está en la Cesta…), `texto` (lista lista para una notificación), `total` y `agotados`.
- Evento `despensa_low_stock` cuando un producto llega a su mínimo, con `name`, `icon`, `stock`, `min_stock`, `unit` e `in_cesta`.

## Acciones

- `despensa.use_item`: `name`, `quantity` (1 por defecto). Resta y lo apunta como usado.
- `despensa.add_item`: `name`, `quantity`, `min_stock`, `unit`, `department`, `icon`. Suma, o crea el producto.
- `despensa.set_stock`: `name`, `stock`, `min_stock`. Corrige el stock (por ejemplo, tras hacer inventario).
- `despensa.get_items`: `low_only`, `department`. Devuelve `count`, `items` y `text`.
- `despensa.add_low_to_cesta`: añade a la Cesta lo que está por reponer. Devuelve `count` y `added`.

Todas aceptan el nombre sin tildes y en singular o plural.

## Automatizaciones

Aviso en el móvil cuando algo llega al mínimo:

```yaml
alias: Despensa al mínimo
triggers:
  - trigger: event
    event_type: despensa_low_stock
actions:
  - action: notify.mobile_app_mi_movil
    data:
      title: "{{ trigger.event.data.icon }} Queda poco: {{ trigger.event.data.name }}"
      message: >
        Quedan {{ trigger.event.data.stock }}.
        {{ 'Ya está en la Cesta.' if trigger.event.data.in_cesta else 'Ábrela para añadirlo a la Cesta.' }}
```

Etiqueta NFC en la cafetera: cada vez que la lees, una cápsula menos:

```yaml
alias: Cápsula de café usada
triggers:
  - trigger: tag
    tag_id: cafetera
actions:
  - action: despensa.use_item
    data:
      name: Cápsulas de café
```

Antes de ir a comprar, pasar a la Cesta lo que falta y mandarte la lista (con la acción `cesta.get_items` de Cesta):

```yaml
alias: Lista antes del súper
triggers:
  - trigger: zone
    entity_id: person.m
    zone: zone.supermercado
    event: enter
actions:
  - action: despensa.add_low_to_cesta
  - action: cesta.get_items
    data:
      store: Supermercado
    response_variable: cesta
  - if: "{{ cesta.count > 0 }}"
    then:
      - action: notify.mobile_app_mi_movil
        data:
          title: "🛒 {{ cesta.count }} productos"
          message: "{{ cesta.text }}"
```

## Datos

Se guardan en `config/.storage/despensa` y se incluyen en las copias de seguridad de Home Assistant. Si eliminas la integración, se borran.

## Desarrollo

```bash
pip install pytest-homeassistant-custom-component
CESTA_REPO=../ha-cesta pytest     # tests; los de Cesta se saltan si no está
python3 tools/build_preview.py    # regenera preview/despensa-preview.html
```

`preview/despensa-preview.html` es una demo que funciona sin Home Assistant: usa el mismo `despensa.js` de la integración con un backend simulado (`preview/mock-backend.js`) que incluye una Cesta y un Assist de prueba.

Estructura:

```
custom_components/despensa/
  __init__.py          carga, panel lateral, tarjeta y ficheros estáticos
  manager.py           inventario, mínimos, movimientos y deshacer
  cesta_bridge.py      sincronización con Cesta (compras, deshacer, baldas, añadir a la lista)
  voice.py             intents y frases de Assist; entiende cantidades y nombres
  catalog.py           el mismo catálogo de productos que Cesta (icono + sección)
  websocket.py         API que usa el panel (despensa/*)
  services.py          acciones despensa.*
  sensor.py            sensor «Por reponer»
  config_flow.py       alta desde Dispositivos y servicios
  frontend/despensa.js panel <despensa-panel> y tarjeta <despensa-card>, sin dependencias
alexa/modelo-es-ES.json  modelo de interacción para una skill de Alexa
```
