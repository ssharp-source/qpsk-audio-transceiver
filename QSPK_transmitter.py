import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
from scipy.signal import upfirdn

# === Config Parameters ===
SYMBOL_RATE = 1125        # symbols per second
SAMPLES_PER_SYMBOL = 20   # Oversampling factor
CARRIER_FREQ = 1500       # Hz (center frequency for real modulation)
SAMPLE_RATE = SYMBOL_RATE * SAMPLES_PER_SYMBOL
DURATION_SEC = 2          # total signal duration
NUM_SYMBOLS = int(DURATION_SEC * SYMBOL_RATE)

# === Gray Code Mapping for QPSK ===
gray_map = {
    (0, 0): 1 + 1j,
    (0, 1): -1 + 1j,
    (1, 1): -1 - 1j,
    (1, 0): 1 - 1j
}

def bits_to_qpsk_symbols(bits):
    symbols = []
    for i in range(0, len(bits), 2):
        bit_pair = (bits[i], bits[i+1])
        symbols.append(gray_map[bit_pair])
    return np.array(symbols)

# === Generate Root Raised Cosine (RRC) Filter ===
def rrc_filter(num_taps=101, beta=0.35):
    N = num_taps
    t = np.arange(-N//2, N//2 + 1)
    t = t / SAMPLES_PER_SYMBOL
    pi = np.pi
    eps = 1e-8  # avoid div by zero

    def sinc(x): return np.sinc(x)
    def denom(x): return 1 - (4 * beta * x)**2 + eps

    h = (sinc(t) * np.cos(pi * beta * t)) / denom(t)
    h /= np.sqrt(np.sum(h**2))  # normalize
    return h

# === Signal Generation ===
def generate_qpsk_waveform():
    # 1. Create known preamble (8 symbols)
    preamble_bits = [0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1]
    preamble_syms = bits_to_qpsk_symbols(preamble_bits)

    # 2. Create random data bits
    num_data_bits = 2 * NUM_SYMBOLS - len(preamble_bits)
    data_bits = np.random.randint(0, 2, num_data_bits)
    data_syms = bits_to_qpsk_symbols(data_bits)

    # 3. Combine
    all_syms = np.concatenate([preamble_syms, data_syms])

    # 4. Upsample + apply RRC
    rrc = rrc_filter()
    i_signal = upfirdn(rrc, all_syms.real, up=SAMPLES_PER_SYMBOL)
    q_signal = upfirdn(rrc, all_syms.imag, up=SAMPLES_PER_SYMBOL)

    # 5. Baseband complex signal
    baseband = i_signal + 1j * q_signal

    # 6. Carrier modulation to real signal
    t = np.arange(len(baseband)) / SAMPLE_RATE
    carrier = np.exp(2j * np.pi * CARRIER_FREQ * t)
    real_signal = np.real(baseband * carrier)

    return baseband, real_signal, all_syms

# === Generate and Plot ===
baseband, real_signal, symbols = generate_qpsk_waveform()

# Plot Constellation (baseband symbols only, no RRC)
plt.figure(figsize=(6, 6))
plt.scatter(np.real(symbols), np.imag(symbols), c='blue', s=5)
plt.title("QPSK Constellation (Gray-coded)")
plt.xlabel("In-phase (I)")
plt.ylabel("Quadrature (Q)")
plt.grid(True)
plt.axis('equal')
plt.show()

# Plot real-valued waveform
plt.figure(figsize=(12, 3))
plt.plot(real_signal[:1000])  # show 1000 samples (~first 0.02 sec)
plt.title("Carrier-Modulated QPSK Signal")
plt.xlabel("Sample Index")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()

# === Play audio signal (toggle off if needed) ===
sd.play(real_signal, samplerate=SAMPLE_RATE)
sd.wait()
