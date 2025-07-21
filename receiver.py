import numpy as np
import sounddevice as sd
from scipy.fft import fft
import base64

SAMPLE_RATE = 44100
BIT_DURATION = 0.1
CHUNK_SIZE = int(SAMPLE_RATE * BIT_DURATION)

FREQ_MARK = 1500
FREQ_SPACE = 1000
THRESHOLD = 0.3
SYNC_WORD = '1010101010101010'

def detect_bit(chunk):
    fft_result = np.abs(fft(chunk))
    freqs = np.fft.fftfreq(len(chunk), 1/SAMPLE_RATE)

    pos_freqs = freqs[:len(freqs)//2]
    pos_fft = fft_result[:len(freqs)//2]

    def band_energy(freq, bw=50):
        band = (pos_freqs > freq - bw) & (pos_freqs < freq + bw)
        return np.mean(pos_fft[band])

    energy_mark = band_energy(FREQ_MARK)
    energy_space = band_energy(FREQ_SPACE)

    if energy_mark > energy_space and energy_mark > THRESHOLD:
        return '1'
    elif energy_space > THRESHOLD:
        return '0'
    else:
        return None

def record(duration_sec):
    print("Listening for", duration_sec, "seconds...")
    recording = sd.rec(int(SAMPLE_RATE * duration_sec), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    return recording[:, 0]

def extract_bits(signal):
    bits = ''
    for i in range(0, len(signal), CHUNK_SIZE):
        chunk = signal[i:i+CHUNK_SIZE]
        if len(chunk) < CHUNK_SIZE:
            break
        bit = detect_bit(chunk)
        if bit:
            bits += bit
    return bits

def find_sync(bitstream):
    idx = bitstream.find(SYNC_WORD)
    return idx + len(SYNC_WORD) if idx != -1 else -1

def bits_to_bytes(bits):
    return bytearray(int(bits[i:i+8], 2) for i in range(0, len(bits), 8) if len(bits[i:i+8]) == 8)

def decode_base64_with_crc(bits):
    byte_array = bits_to_bytes(bits)
    try:
        base64_str = byte_array.decode('ascii')
        decoded = base64.b64decode(base64_str).decode('ascii')
        payload, crc_char = decoded[:-1], decoded[-1]
        valid_crc = crc8(payload.encode('ascii')) == ord(crc_char)
        return payload if valid_crc else "[CRC ERROR]"
    except Exception as e:
        return "[Decode Error]"

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


def run_receiver(duration_sec=5):
    signal = record(duration_sec)
    bits = extract_bits(signal)

    if len(bits) > 20:  # Basic noise floor test
        print(f"Received signal: {len(bits)} bits")
        return True  # Channel is busy
    return False  # Channel is free


if __name__ == "__main__":
    signal = record(duration_sec=5)
    bitstream = extract_bits(signal)
    print(f"Total bits received: {len(bitstream)}")

    start = find_sync(bitstream)
    if start != -1:
        data_bits = bitstream[start:]
        print("Decoding payload...")
        decoded = decode_base64_with_crc(data_bits)
        print("Decoded message:", decoded)
    else:
        print("Sync word not found.")
