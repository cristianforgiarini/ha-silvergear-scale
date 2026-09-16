"""Constantes para la integración Silvergear Smart Food Scale (Art.No 4454)."""

DOMAIN = "silvergear_scale"

# UUIDs descubiertos por inspección GATT (nRF Connect) sobre el dispositivo real.
# El servicio 0xFFB0 no está registrado en el Bluetooth SIG: es un servicio
# propietario típico de chips BLE OEM chinos reutilizados por varias marcas
# blancas (Silvergear/Karsten International, y probablemente otras).
SERVICE_UUID = "0000ffb0-0000-1000-8000-00805f9b34fb"
CHAR_NOTIFY_UUID = "0000ffb2-0000-1000-8000-00805f9b34fb"  # NOTIFY, envía el peso
CHAR_WRITE_UUID = "0000ffb1-0000-1000-8000-00805f9b34fb"  # WRITE, sin explorar aún

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
