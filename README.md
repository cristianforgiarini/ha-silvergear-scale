# Silvergear Smart Food Scale — integración para Home Assistant

Integración no oficial para la báscula de cocina **Silvergear Smart Food
Scale** (Art.No 4454, Karsten International B.V. / Silvergear.eu), que se
empareja de fábrica con la app **Nutridays**.

No existe integración nativa ni componente HACS oficial para este
dispositivo (ni para la mayoría de básculas OEM chinas de marca blanca con
protocolo propietario), así que este componente nace de ingeniería inversa
del protocolo BLE hecha con nRF Connect.

## Requisitos

- Home Assistant con la integración **Bluetooth** activa.
- Un proxy Bluetooth **activo** en rango de la báscula (por ejemplo un ESP32
  con ESPHome y `bluetooth_proxy: active: true`), ya que la báscula no mete
  el peso en el paquete de advertising: hay que mantener una conexión GATT
  abierta y suscribirse a notificaciones.

## Instalación vía HACS

1. HACS → menú (⋮) → **Repositorios personalizados**.
2. Añade la URL de este repositorio, categoría **Integration**.
3. Búscalo en HACS como "Silvergear Smart Food Scale" e instálalo.
4. Reinicia Home Assistant.
5. Debería aparecer solo como dispositivo Bluetooth descubierto; si no,
   añádelo a mano desde Ajustes → Dispositivos y servicios → Añadir
   integración → "Silvergear" e introduce la MAC.

## Instalación manual

Copia `custom_components/silvergear_scale/` dentro de tu carpeta
`config/custom_components/` y reinicia Home Assistant.

## Protocolo (resumen)

- Servicio GATT propietario `0000ffb0-...` (no registrado en el Bluetooth
  SIG).
- Notificaciones de peso en la característica `0000ffb2-...`.
- Paquete de 19 bytes: cabecera fija `AC 40 01`, byte 4 = unidad (`00`=g,
  `10`=ml), bytes 5-7 = peso en miligramos (entero de 24 bits big-endian),
  byte 19 = checksum `(suma bytes 1-18 + 20) mod 256`.

## Estado

- Sensor de peso en gramos: funcional.
- Entidad `select` para cambiar la unidad mostrada en la báscula (`g`,
  `ml`, `ml(m)`), usando comandos capturados por HCI snoop en la
  característica `0xFFB1`: funcional.
- `oz` y `lb(oz)` no se soportan, a propósito (no interesaban para este
  uso; si hicieran falta, se capturarían con el mismo método).
- Limitación conocida: el estado "actual" de la entidad `select` no se
  refleja para `ml(m)` (sale como desconocido), porque esa unidad solo
  se llega a poner desde la app y no se pudo capturar el byte con el
  que la báscula la anuncia en sus notificaciones de peso.
