"""Constantes para la integración Silvergear Smart Food Scale (Art.No 4454)."""

DOMAIN = "silvergear_scale"

# UUIDs descubiertos por inspección GATT (nRF Connect) sobre el dispositivo real.
# El servicio 0xFFB0 no está registrado en el Bluetooth SIG: es un servicio
# propietario típico de chips BLE OEM chinos reutilizados por varias marcas
# blancas (Silvergear/Karsten International, y probablemente otras).
SERVICE_UUID = "0000ffb0-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "0000ffb2-0000-1000-8000-00805f9b34fb"  # NOTIFY, envía el peso
CHAR_WRITE_UUID = "0000ffb1-0000-1000-8000-00805f9b34fb"  # WRITE, comandos a la báscula

# Formato del paquete de notificación (19 bytes), confirmado con 5 muestras:
#   byte 0-2:  AC 40 01           -> cabecera fija
#   byte 3:    unidad (00=g, 10=ml; resto de unidades sin confirmar)
#   byte 4-6:  peso en miligramos, entero de 24 bits big-endian
#   byte 7-16: sin uso / ceros
#   byte 17:   A6, constante en todas las muestras
#   byte 18:   checksum = (suma de bytes 0-17 + 20) mod 256
PACKET_HEADER = b"\xac\x40\x01"
WEIGHT_OFFSET = 4
WEIGHT_LENGTH = 3

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
# (posición 3 del paquete AC-40-01). Solo confirmado para g y ml; "ml(m)"
# se seleccionó pero no capturamos su notificación de peso para confirmar
# su código, así que no aparece aquí (current_option quedará "desconocido"
# si la báscula está en esa unidad).
NOTIFY_UNIT_MAP: dict[int, str] = {
    0x00: "g",
    0x10: "ml",
}

