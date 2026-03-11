"""
Diagnostic script for MI6010D: tests read_termination options and raw reads
Run without modifying existing files; prints raw/decoded responses and serial-poll info.
"""

import logging
import time
import argparse
import sys

import pyvisa

TERMINATORS = ['\n', '\r', '\r\n', None]


def configure_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('pyvisa').setLevel(logging.DEBUG)


def open_instrument(address: str, timeout: int = 20000):
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(address)
    inst.write_termination = '\n'
    inst.read_termination = '\n'
    inst.timeout = timeout
    return rm, inst


def safe_write(inst, cmd: str, pause: float = 0.15):
    try:
        inst.write(cmd)
    except Exception as e:
        print(f"Warning: write('{cmd}') raised: {e}")
    time.sleep(pause)


def get_serial_poll(inst):
    try:
        # read_stb / read_stb() availability may vary by backend
        if hasattr(inst, 'read_stb'):
            return inst.read_stb()
        # fallback: no-op
        return None
    except Exception as e:
        print("Serial poll read error:", e)
        return None


def reset_and_config(inst, rs, rx, ix, t, m, send_stats=False):
    # Try to mimic the working manual sequence
    safe_write(inst, 'R')
    safe_write(inst, 'S')
    # choose Rs as standard (like working script used 's')
    safe_write(inst, 's')

    safe_write(inst, f'A{rs}')
    safe_write(inst, f'r{rx}')
    safe_write(inst, f'I{ix}')
    safe_write(inst, f'T{t}')
    safe_write(inst, f'M{m}')
    if send_stats:
        safe_write(inst, f'J5')


def read_loop(inst, expected, use_raw=False, max_wait=60):
    measurements = []
    start = time.time()
    while len(measurements) < expected and (time.time() - start) < max_wait:
        try:
            if use_raw:
                raw = inst.read_raw()
                print("RAW repr:", repr(raw))
                try:
                    s = raw.decode('ascii', errors='replace').strip()
                except Exception:
                    s = str(raw).strip()
                print("DECODED:", repr(s))
            else:
                s = inst.read()
                # print repr to show terminators/state
                print("READ repr:", repr(s))
                s = s.strip() if isinstance(s, str) else str(s).strip()

            if not s:
                time.sleep(0.05)
                continue

            if s.startswith('&'):
                try:
                    measurements.append(float(s[1:]))
                    print(f"  -> Parsed ratio #{len(measurements)} = {measurements[-1]}")
                except Exception as e:
                    print("  -> Parse error:", e)
            elif s.startswith('E'):
                print("Device error:", s)
                break
            else:
                print("Other message:", s)

        except Exception as e:
            print("Read exception:", e)
            # fallback: try raw once
            try:
                raw = inst.read_raw()
                print("Fallback RAW repr:", repr(raw))
                s = raw.decode('ascii', errors='replace').strip()
                print("Fallback DECODED:", repr(s))
            except Exception as e2:
                # if still failing, wait a bit
                time.sleep(0.1)

    return measurements


def run_diagnostics(address, expected, rs, rx, ix, t, m, send_stats):
    configure_logging()

    print("Opening instrument:", address)
    rm = None
    inst = None
    try:
        rm, inst = open_instrument(address)
    except Exception as e:
        print("Failed to open resource:", e)
        return

    print("Resource opened. Vendor/ID:", getattr(inst, 'manufacturer', None), getattr(inst, 'resource_name', None))

    for term in TERMINATORS:
        print('\n' + '=' * 60)
        print(f"Testing read_termination={repr(term)}")
        inst.read_termination = term
        inst.write_termination = '\n'
        inst.timeout = 20000

        print("Serial poll (before):", get_serial_poll(inst))
        reset_and_config(inst, rs, rx, ix, t, m, send_stats)
        print("Serial poll (after config):", get_serial_poll(inst))

        print("Starting read loop (normal read) — expected:", expected)
        measures = read_loop(inst, expected, use_raw=False, max_wait=max(30, expected * t + 10))
        print(f"Result with read_termination={repr(term)} -> {len(measures)} measurements")

        if len(measures) < expected:
            print("Not enough measurements; trying raw reads fallback")
            measures_raw = read_loop(inst, expected, use_raw=True, max_wait=30)
            print(f"Fallback raw read -> {len(measures_raw)} measurements")

        print('--- end test for', repr(term))

    print('\nClosing instrument')
    try:
        if inst:
            inst.close()
        if rm:
            rm.close()
    except Exception as e:
        print('Error closing instrument:', e)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--address', '-a', default='GPIB0::15::INSTR', help='VISA resource string')
    p.add_argument('--expected', '-n', type=int, default=10, help='Number of expected measurements')
    p.add_argument('--rs', type=float, default=1.0, help='Rs value')
    p.add_argument('--rx', type=float, default=1.0, help='Rx value')
    p.add_argument('--ix', type=float, default=0.1, help='Current Ix (A)')
    p.add_argument('--t', type=int, default=8, help='Reversal time (s)')
    p.add_argument('--m', type=int, default=10, help='Number of measurements (M)')
    p.add_argument('--send-stats', action='store_true', help='Send statistics command J5')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_diagnostics(args.address, args.expected, args.rs, args.rx, args.ix, args.t, args.m, args.send_stats)
