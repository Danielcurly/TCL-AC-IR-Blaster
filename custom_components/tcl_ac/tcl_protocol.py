# TCL AC Protocol Implementation V11
# Derived from reverse engineering 70+ manual captures

import io, base64
from struct import pack

def emit_literal_blocks(out, data):
    for i in range(0, len(data), 32):
        emit_literal_block(out, data[i:i+32])

def emit_literal_block(out, data):
    length = len(data) - 1
    out.write(bytes([length]))
    out.write(data)

def emit_distance_block(out, length, distance):
    distance -= 1
    length -= 2
    block = bytearray()
    if length >= 7:
        block.append(length - 7)
        length = 7
    block.insert(0, length << 5 | distance >> 8)
    block.append(distance & 0xFF)
    out.write(block)

def compress_level1(out, data):
    W = 2**13
    L_max = 255+9
    block_start = pos = 0
    while pos < len(data):
        best = None
        for d in range(1, min(pos, W) + 1):
            length = 0
            limit = min(L_max, len(data) - pos)
            start = pos - d
            while length < limit and data[pos + length] == data[start + length]:
                length += 1
            if length >= 3:
                best = (length, d)
                break
        if best:
            emit_literal_blocks(out, data[block_start:pos])
            emit_distance_block(out, best[0], best[1])
            pos += best[0]
            block_start = pos
        else:
            pos += 1
    emit_literal_blocks(out, data[block_start:pos])

def encode_ir(signal):
    payload = b''.join(pack('<H', t) for t in signal)
    out = io.BytesIO()
    compress_level1(out, payload)
    return base64.b64encode(out.getvalue()).decode('ascii')


# Protocol Mappings
FAN_SPEED = { 'auto': 0xE5, 'high': 0xC5, 'medium': 0xA5, 'low': 0x85 }
MODE_BASE = { 'heat': 0x7F, 'cool': 0xDF, 'dry': 0xBF, 'fan_only': 0x9F, 'auto': 0xFF }

def generate_tcl_bytes(mode, temp, speed, quiet=False, turbo=False, eco=False, swing=False, timer_horas=0, power_off=False):
    b = [0] * 12
    # B0-B1: Timer
    b[0] = 0xFF if timer_horas == 0 else (0x5F - timer_horas)
    b[1] = (~b[0]) & 0xFF
    
    # B2-B3: Funciones Especiales
    b[2] = 0xFF
    if quiet: b[2] &= ~0x40
    if turbo: b[2] &= ~0x08
    if eco:   b[2] &= ~0x10
    b[3] = (~b[2]) & 0xFF
    
    # B4-B5: Control / Flags
    if power_off:        b[4] = 0xFF
    elif quiet:          b[4] = 0xF1
    elif turbo:          b[4] = 0xF5
    elif eco:            b[4] = 0xF2
    elif swing:          b[4] = 0xFB
    elif timer_horas > 0: b[4] = 0xF9
    else:
        if mode == 'auto': b[4] = 0xFA
        elif mode == 'dry':  b[4] = 0xFE
        else:              b[4] = 0xFC
    b[5] = (~b[4]) & 0xFF
    
    # B6-B7: Fan Speed
    b[6] = FAN_SPEED.get(speed, 0xE5)
    if quiet:    b[6] = 0x85   # Quiet forces low
    if swing:    b[6] = 0xD9   # Swing bypass value
    if power_off: b[6] |= 0x02  # OFF bit
    b[7] = (~b[6]) & 0xFF
    
    # B8-B9: Temp + Mode
    base = MODE_BASE.get(mode, 0xDF)
    b[8] = base - (int(temp) - 16)
    b[9] = (~b[8]) & 0xFF
    
    # B10-B11: Footer
    b[10] = 0xAA
    b[11] = 0x55
    return b

def bytes_to_signal(tcl_bytes):
    signal = [6000, 7400]
    for byte_val in tcl_bytes:
        for bit_idx in range(8):
            bit = (byte_val >> bit_idx) & 1
            signal.append(500)
            signal.append(1700 if bit else 600)
    signal.extend([500, 7400, 500])
    return signal

def generate_code(mode, temp, speed, quiet=False, turbo=False, eco=False, swing=False, timer_horas=0, power_off=False):
    tcl_bytes = generate_tcl_bytes(mode, temp, speed, quiet, turbo, eco, swing, timer_horas, power_off)
    signal = bytes_to_signal(tcl_bytes)
    return encode_ir(signal)
