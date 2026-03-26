#!/usr/bin/env python3
"""
wav_to_h.py — Convert WAV audio files to C header files for ESP32-C3 I2S playback.

Usage:
    python wav_to_h.py sound.wav                  # produces sound.h
    python wav_to_h.py sound.wav -o my_sound.h    # custom output name
    python wav_to_h.py *.wav                       # batch convert multiple files
    python wav_to_h.py sound.wav --resample 16000  # resample to 16 kHz
    python wav_to_h.py sound.wav --mono            # force mono
    python wav_to_h.py sound.wav --bits 16         # force 16-bit depth

Output header contains:
    - Raw PCM sample array  (const uint8_t / int16_t)
    - Metadata defines      (SAMPLE_RATE, CHANNELS, BITS_PER_SAMPLE, DATA_LEN)

Dependencies (install via pip):
    pip install numpy soundfile
    Optional resampling: pip install scipy
"""

import argparse
import os
import re
import sys
import wave
import struct
from pathlib import Path
from datetime import datetime

# ── optional heavy deps ──────────────────────────────────────────────────────
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

try:
    from scipy.signal import resample_poly
    from math import gcd
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ── helpers ──────────────────────────────────────────────────────────────────

def sanitize_name(name: str) -> str:
    """Turn a filename stem into a valid C identifier."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name[0].isdigit():
        name = "_" + name
    return name.upper()


def read_wav(path: str):
    """
    Read a WAV file and return (samples_bytes, sample_rate, n_channels, bits).
    Uses soundfile when available (supports float32 WAVs, 24-bit, etc.),
    falls back to the stdlib wave module.
    """
    if HAS_SOUNDFILE:
        data, rate = sf.read(path, always_2d=True, dtype="int16")
        # soundfile returns (frames, channels) shaped int16 array
        n_channels = data.shape[1]
        bits = 16
        raw = data.tobytes()
        return raw, rate, n_channels, bits

    # stdlib fallback — handles standard 8/16-bit PCM only
    with wave.open(path, "rb") as wf:
        rate       = wf.getframerate()
        n_channels = wf.getnchannels()
        bits       = wf.getsampwidth() * 8
        raw        = wf.readframes(wf.getnframes())
    return raw, rate, n_channels, bits


def to_mono_int16(raw: bytes, n_channels: int, bits: int) -> bytes:
    """Mix down to mono int16, averaging across channels."""
    if not HAS_NUMPY:
        raise RuntimeError("numpy is required for channel/bit conversion. pip install numpy")

    dtype = np.int16 if bits == 16 else np.int8
    samples = np.frombuffer(raw, dtype=dtype)

    # Normalise non-16-bit to int16 range
    if bits == 8:
        # 8-bit WAV is unsigned; convert to signed int16
        samples = (samples.astype(np.int16) - 128) * 256
    elif bits == 32:
        samples = (samples.astype(np.int32) >> 16).astype(np.int16)

    if n_channels > 1:
        samples = samples.reshape(-1, n_channels)
        samples = samples.mean(axis=1).astype(np.int16)

    return samples.tobytes()


def resample(raw: bytes, orig_rate: int, target_rate: int) -> bytes:
    """Resample int16 mono PCM to a new sample rate."""
    if not HAS_NUMPY:
        raise RuntimeError("numpy is required for resampling. pip install numpy")
    if not HAS_SCIPY:
        raise RuntimeError("scipy is required for resampling. pip install scipy")

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    g = gcd(target_rate, orig_rate)
    up, down = target_rate // g, orig_rate // g
    resampled = resample_poly(samples, up, down)
    return np.clip(resampled, -32768, 32767).astype(np.int16).tobytes()


def bytes_to_c_array(data: bytes, var_name: str, bits: int, cols: int = 16) -> str:
    """Format raw bytes as a C uint8_t or int16_t array literal."""
    lines = []
    if bits == 16:
        # Emit as int16_t so the I2S driver gets the right sign
        dtype_str = "int16_t"
        values = struct.unpack(f"<{len(data)//2}h", data)
        for i in range(0, len(values), cols // 2):
            chunk = values[i : i + cols // 2]
            lines.append("    " + ", ".join(f"{v:6d}" for v in chunk) + ",")
        array_decl = (
            f"const {dtype_str} {var_name}[] = {{\n"
            + "\n".join(lines)
            + "\n};"
        )
        length = len(values)
    else:
        dtype_str = "uint8_t"
        for i in range(0, len(data), cols):
            chunk = data[i : i + cols]
            lines.append("    " + ", ".join(f"0x{b:02X}" for b in chunk) + ",")
        array_decl = (
            f"const {dtype_str} {var_name}[] = {{\n"
            + "\n".join(lines)
            + "\n};"
        )
        length = len(data)

    return array_decl, dtype_str, length


def generate_header(
    wav_path: str,
    out_path: str,
    force_mono: bool,
    target_bits: int | None,
    target_rate: int | None,
):
    print(f"  Reading  : {wav_path}")
    raw, rate, n_channels, bits = read_wav(wav_path)

    print(f"  Source   : {rate} Hz, {n_channels}ch, {bits}-bit — {len(raw)} bytes")

    # ── channel / bit conversion ─────────────────────────────────────────────
    out_channels = 1 if force_mono else n_channels

    need_convert = force_mono and n_channels > 1
    need_convert = need_convert or (target_bits is not None and target_bits != bits)

    if need_convert:
        raw = to_mono_int16(raw, n_channels, bits)
        bits = 16
        n_channels = 1
        out_channels = 1

    # ── resampling ───────────────────────────────────────────────────────────
    if target_rate and target_rate != rate:
        if n_channels > 1:
            raw = to_mono_int16(raw, n_channels, bits)
            n_channels = 1
            out_channels = 1
        print(f"  Resample : {rate} Hz → {target_rate} Hz")
        raw = resample(raw, rate, target_rate)
        rate = target_rate

    # Override bit depth after all conversions
    if target_bits:
        bits = target_bits

    # ── names ────────────────────────────────────────────────────────────────
    stem      = Path(wav_path).stem
    c_name    = sanitize_name(stem)
    guard     = f"_{c_name}_H"

    array_body, dtype_str, n_elements = bytes_to_c_array(raw, c_name, bits)

    # ── header text ──────────────────────────────────────────────────────────
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""\
/**
 * @file {Path(out_path).name}
 * @brief Auto-generated PCM audio data for ESP32-C3 I2S playback.
 *
 * Source     : {Path(wav_path).name}
 * Generated  : {now}
 * Sample rate: {rate} Hz
 * Channels   : {out_channels}
 * Bit depth  : {bits}-bit
 * Samples    : {n_elements}
 *
 * ── Minimal ESP32-C3 I2S playback example ────────────────────────────────
 *
 * #include "{Path(out_path).name}"
 *
 * i2s_chan_handle_t tx_handle;
 *
 * i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(
 *     I2S_NUM_AUTO, I2S_ROLE_MASTER);
 * i2s_new_channel(&chan_cfg, &tx_handle, NULL);
 *
 * i2s_std_config_t std_cfg = {{
 *     .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG({c_name}_SAMPLE_RATE),
 *     .slot_cfg = I2S_STD_MSB_SLOT_DEFAULT_CONFIG(
 *                     I2S_DATA_BIT_WIDTH_{bits}BIT,
 *                     {'I2S_SLOT_MODE_MONO' if out_channels == 1 else 'I2S_SLOT_MODE_STEREO'}),
 *     .gpio_cfg = {{
 *         .mclk = I2S_GPIO_UNUSED,
 *         .bclk = GPIO_NUM_6,   // ← adjust to your wiring
 *         .ws   = GPIO_NUM_7,
 *         .dout = GPIO_NUM_8,
 *         .din  = I2S_GPIO_UNUSED,
 *     }},
 * }};
 * i2s_channel_init_std_mode(tx_handle, &std_cfg);
 * i2s_channel_enable(tx_handle);
 *
 * size_t bytes_written = 0;
 * i2s_channel_write(tx_handle, {c_name},
 *                   {c_name}_DATA_LEN, &bytes_written, portMAX_DELAY);
 * ─────────────────────────────────────────────────────────────────────────
 */

#ifndef {guard}
#define {guard}

#include <stdint.h>

/* ── Metadata ─────────────────────────────────────────────────────────── */
#define {c_name}_SAMPLE_RATE      {rate}U
#define {c_name}_CHANNELS         {out_channels}U
#define {c_name}_BITS_PER_SAMPLE  {bits}U
#define {c_name}_DATA_LEN         {len(raw)}U   /* bytes */
#define {c_name}_NUM_SAMPLES      {n_elements}U

/* ── PCM data ─────────────────────────────────────────────────────────── */
{array_body}

#endif /* {guard} */
"""

    Path(out_path).write_text(header, encoding="utf-8")
    print(f"  Output   : {out_path}  ({len(raw):,} bytes → {n_elements:,} {dtype_str} samples)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert WAV file(s) to C header(s) for ESP32-C3 I2S playback."
    )
    p.add_argument("wav_files", nargs="+", help="Input WAV file(s)")
    p.add_argument("-o", "--output",   default=None,
                   help="Output .h file (only valid for single input)")
    p.add_argument("--mono",           action="store_true",
                   help="Mix down to mono (recommended for small MCUs)")
    p.add_argument("--bits",           type=int, choices=[8, 16, 32], default=None,
                   help="Force output bit depth (default: keep source depth)")
    p.add_argument("--resample",       type=int, default=None, metavar="RATE",
                   help="Resample to target rate in Hz, e.g. 16000 (requires scipy)")
    return p.parse_args()


def check_deps(args):
    missing = []
    if not HAS_NUMPY:
        missing.append("numpy")
    if not HAS_SOUNDFILE:
        # stdlib wave can handle simple 8/16-bit PCM; warn but don't abort
        print("  [warn] soundfile not installed — complex WAVs (24-bit, float) "
              "may fail. pip install soundfile")
    if args.resample and not HAS_SCIPY:
        missing.append("scipy")
    if missing:
        print(f"  [error] Missing required packages: {', '.join(missing)}")
        print(f"          Run: pip install {' '.join(missing)}")
        sys.exit(1)


def main():
    args = parse_args()
    check_deps(args)

    if args.output and len(args.wav_files) > 1:
        print("[error] -o/--output can only be used with a single input file.")
        sys.exit(1)

    for wav in args.wav_files:
        if not os.path.isfile(wav):
            print(f"[skip] Not found: {wav}")
            continue

        out = args.output if args.output else str(Path(wav).with_suffix(".h"))
        print(f"\n[{Path(wav).name}]")

        try:
            generate_header(
                wav_path    = wav,
                out_path    = out,
                force_mono  = args.mono,
                target_bits = args.bits,
                target_rate = args.resample,
            )
        except Exception as exc:
            print(f"  [error] {exc}")
            raise

    print("\nDone.")


if __name__ == "__main__":
    main()
