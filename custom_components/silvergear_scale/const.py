"""Constantes para la integración Silvergear Smart Food Scale (Art.No 4454)."""

DOMAIN = "silvergear_scale"

# UUIDs descubiertos por inspección GATT (nRF Connect) sobre el dispositivo real.
# El servicio 0xFFB0 no está registrado en el Bluetooth SIG: es un servicio
# propietario típico de chips BLE OEM chinos reutilizados por varias marcas
# blancas (Silvergear/Karsten International, y probablemente otras).
SERVICE_UUID = "0000ffb0-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "0000ffb2-0000-1000-8000-00805f9b34fb"  # NOTIFY, envía el peso
CHAR_WRITE_UUID = "0000ffb1-0000-1000-8000-00805f9b34fb"  # WRITE, comandos a la báscula

# Formato del paquete de notificación (19 bytes), confirmado con varias
# muestras (checksum verificado en todas):
#   byte 0-1:  AC 40              -> cabecera fija
#   byte 2:    tipo de payload: 01=valor numérico simple; 00=formato
#              especial (NO es exclusivo de sobrecarga: la unidad
#              compuesta "lb:oz" también usa 00, probablemente porque
#              libras+onzas no cabe en un único número continuo).
#              Para distinguir sobrecarga de lb:oz hay que mirar también
#              el byte 3 (ver OVERLOAD_UNIT_CODES más abajo).
#   byte 3:    unidad (ver NOTIFY_UNIT_MAP)
#   byte 4-6:  peso/valor crudo en miligramos, entero de 24 bits big-endian
#              (con tipo=00 no está claro que este campo sea un peso
#              fiable en todos los casos; en la sobrecarga parecía el
#              último crudo antes de saturar, y en lb:oz podría tener
#              una estructura distinta ya que no lo hemos investigado)
#   byte 7-16: sin uso / ceros
#   byte 17:   A6, constante en todas las muestras
#   byte 18:   checksum = (suma de bytes 0-17 + 20) mod 256
HEADER_PREFIX = b"\xac\x40"
MSG_TYPE_OFFSET = 2
MSG_TYPE_WEIGHT = 0x01
MSG_TYPE_SPECIAL = 0x00  # antes llamado "overload"; ver nota arriba
WEIGHT_OFFSET = 4
WEIGHT_LENGTH = 3

# Códigos de unidad (byte 3) con tipo=MSG_TYPE_SPECIAL que NO son
# sobrecarga, para no dar falsos positivos en el binary_sensor.
# 0x20 = lb:oz, confirmado por captura real (no es una sobrecarga).
SPECIAL_NON_OVERLOAD_UNIT_CODES = {0x20}

# Comandos de cambio de unidad, capturados con registro HCI de Bluetooth
# (app Nutridays) y verificados manualmente reenviándolos tal cual con
# nRF Connect. Formato: AC 40 02 <código_unidad> + relleno + 2 bytes finales
# cuyo algoritmo exacto NO hemos logrado determinar (no coincide con ningún
# CRC16 estándar probado) — por eso se guardan como paquetes fijos en vez de
# calcularse dinámicamente. Confirmado que son reutilizables entre conexiones
# distintas a la de la captura original.
# oz y lb(oz) no se soportan a propósito (no interesaban para este uso).
UNIT_WRITE_COMMANDS: dict[str, bytes] = {
    "g": bytes.fromhex("ac4002000000000000000000000000000000d2d4"),
    "ml": bytes.fromhex("ac4002010000000000000000000000000000d2d5"),
    "ml(m)": bytes.fromhex("ac4002050000000000000000000000000000d2d9"),
}

# Mapeo del byte de unidad tal como aparece en las notificaciones de peso
# (posición 3 del paquete). g/ml/ml(m) son las únicas seleccionables desde
# el "select" de HA (ver UNIT_WRITE_COMMANDS); lb:oz/fl'oz/fl'oz(m) solo se
# alcanzan con el botón físico y se listan aquí solo para que current_option
# no salga "desconocido" si el usuario las selecciona a mano.
NOTIFY_UNIT_MAP: dict[int, str] = {
    0x00: "g",
    0x10: "ml",
    0x20: "lb:oz",
    0x50: "ml(m)",
    0x60: "fl'oz",
    0x70: "fl'oz(m)",
}

