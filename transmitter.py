import numpy as np
import sounddevice as sd
import base64
import sys
import os

SAMPLE_RATE = 44100
BIT_DURATION = 0.1  # 100ms per bit
FREQ_MARK = 1500
FREQ_SPACE = 1000

SYNC_WORD = '1010101010101010'  # 16-bit alternating pattern for alignment

# --- CRC8 Function ---
def crc8(data_bytes):
    crc = 0
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc

# --- Add CRC to plain text ---
def add_crc_to_text(text):
    data = text.encode('ascii')
    crc_val = crc8(data)
    return text + chr(crc_val)

# --- Encode text to Base64 then bits ---
def text_to_base64_bits(text):
    base64_bytes = base64.b64encode(text.encode('ascii'))
    return ''.join(f'{byte:08b}' for byte in base64_bytes)

# --- Prepare full bitstream with sync ---
def prepare_message_to_transmit(msg):
    msg_crc = add_crc_to_text(msg)
    bits = SYNC_WORD + text_to_base64_bits(msg_crc)
    return bits

# --- Tone Generation ---
def generate_tone(freq, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return 0.5 * np.sin(2 * np.pi * freq * t)

def play_fsk(bits):
    signal = np.concatenate([
        generate_tone(FREQ_MARK if bit == '1' else FREQ_SPACE, BIT_DURATION)
        for bit in bits
    ])
    sd.play(signal, samplerate=SAMPLE_RATE)
    sd.wait()

# --- New function: Transmit a text file ---
def transmit_file(filepath):
    if not os.path.exists(filepath):
        print(f"! File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        content = f.read()

    print(f"📤 Transmitting file: {filepath} ({len(content)} chars)")
    bits = prepare_message_to_transmit(content)
    print(f"Transmitting {len(bits)} bits...")
    play_fsk(bits)
    print("--Transmission complete--")

# --- Command-line interface or call from other script ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transmitter.py <path/to/textfile>")
    else:
        transmit_file(sys.argv[1])
