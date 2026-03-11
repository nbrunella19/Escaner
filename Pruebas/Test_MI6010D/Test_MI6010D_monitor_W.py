"""
Monitor script for MI6010D: applies configuration, reads ratios and monitors STB.
If it receives 2 ratios and then no data for a short interval, it sends 'W' (continue)
to try to resume the measurement. Prints raw/decoded messages and STB values.

Usage:
    python Pruebas/Test_MI6010D_monitor_W.py --address GPIB0::15::INSTR --m 10
"""

import argparse
import time
import logging
import pyvisa


def configure_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.getLogger('pyvisa').setLevel(logging.DEBUG)


def open_inst(address, timeout=20000):
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(address)
    inst.write_termination = '\n'
    inst.read_termination = '\n'
    inst.timeout = timeout
    return rm, inst


def safe_write(inst, cmd, pause=0.15):
    try:
        inst.write(cmd)
        logging.info("WROTE: %s", repr(cmd))
    except Exception as e:
        logging.warning("Write('%s') failed: %s", cmd, e)
    time.sleep(pause)


def read_one(inst):
    """Try to read using read(); on timeout attempt read_raw() and decode."""
    try:
        s = inst.read()
        logging.debug("READ repr: %r", s)
        if isinstance(s, bytes):
            try:
                s = s.decode('ascii', errors='replace')
            except Exception:
                s = str(s)
        return s.strip() if isinstance(s, str) else str(s).strip()
    except Exception as e:
        logging.debug("read() exception: %s; trying read_raw()", e)
        try:
            raw = inst.read_raw()
            logging.debug("RAW repr: %r", raw)
            try:
                decoded = raw.decode('ascii', errors='replace').strip()
            except Exception:
                decoded = str(raw).strip()
            return decoded
        except Exception as e2:
            logging.debug("read_raw() failed: %s", e2)
            raise


def get_stb(inst):
    try:
        if hasattr(inst, 'read_stb'):
            return inst.read_stb()
        return None
    except Exception as e:
        logging.debug("read_stb() error: %s", e)
        return None


def apply_config(inst, rs, rx, ix, t, m, j=None):
    safe_write(inst, 'R')    # remote
    safe_write(inst, 'S')    # toggle standby
    safe_write(inst, 's')    # choose Rs as standard (like working script)
    safe_write(inst, f'A{rs}')
    safe_write(inst, f'r{rx}')
    safe_write(inst, f'I{ix}')
    safe_write(inst, f'T{t}')
    safe_write(inst, f'M{m}')
    if j is not None:
        safe_write(inst, f'J{j}')


def monitor_and_continue(inst, expected, wait_after_two=5, max_continue_attempts=3):
    ratios = []
    last_data_time = time.time()
    continue_attempts = 0

    timeout_loop_start = time.time()
    while len(ratios) < expected and (time.time() - timeout_loop_start) < max(600, expected * 10):
        try:
            stb = get_stb(inst)
            logging.info("STB: %r | Ratios so far: %d", stb, len(ratios))

            try:
                s = read_one(inst)
            except Exception as e:
                logging.debug("Read failed: %s", e)
                s = ''

            if s:
                logging.info("RECV: %r", s)
                last_data_time = time.time()
                if s.startswith('&'):
                    try:
                        ratios.append(float(s[1:]))
                        logging.info("Parsed ratio #%d = %r", len(ratios), ratios[-1])
                    except Exception as e:
                        logging.warning("Could not parse ratio from %r: %s", s, e)
                elif s.startswith('E'):
                    logging.error("Device error message: %s", s)
                    break
                else:
                    logging.debug("Other message: %s", s)

            else:
                # no data this cycle
                # if we have at least 2 ratios and no new data for wait_after_two seconds -> send W
                if len(ratios) >= 2 and (time.time() - last_data_time) > wait_after_two:
                    if continue_attempts < max_continue_attempts:
                        logging.info("No new data for %.1fs after 2+ ratios — sending 'W' to continue (attempt %d)", time.time() - last_data_time, continue_attempts + 1)
                        safe_write(inst, 'W')
                        continue_attempts += 1
                        # give device a little time to respond
                        time.sleep(0.5)
                        last_data_time = time.time()
                        continue
                    else:
                        logging.warning("Reached max continue attempts (%d). Stopping monitor.", max_continue_attempts)
                        break

                time.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("User interrupted")
            break

    return ratios


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--address', '-a', default='GPIB0::15::INSTR')
    p.add_argument('--expected', '-n', type=int, default=10)
    p.add_argument('--rs', type=float, default=1.0)
    p.add_argument('--rx', type=float, default=1.0)
    p.add_argument('--ix', type=float, default=0.1)
    p.add_argument('--t', type=int, default=8)
    p.add_argument('--m', type=int, default=10)
    p.add_argument('--j', type=int, default=None)
    p.add_argument('--wait-after-two', type=float, default=5.0)
    p.add_argument('--max-continue', type=int, default=3)
    return p.parse_args()


if __name__ == '__main__':
    configure_logging()
    args = parse_args()

    logging.info("Opening %s", args.address)
    try:
        rm, inst = open_inst(args.address)
    except Exception as e:
        logging.error("Failed to open instrument: %s", e)
        raise

    logging.info("Applying configuration: Rs=%s Rx=%s Ix=%s T=%s M=%s J=%s", args.rs, args.rx, args.ix, args.t, args.m, args.j)
    apply_config(inst, args.rs, args.rx, args.ix, args.t, args.m, j=args.j)

    logging.info("Starting monitor loop — expecting %d measurements", args.expected)
    results = monitor_and_continue(inst, args.expected, wait_after_two=args.wait_after_two, max_continue_attempts=args.max_continue)

    logging.info("Done. Collected %d ratios", len(results))
    for i, v in enumerate(results, 1):
        print(f"[{i}] {v}")

    try:
        inst.close()
        rm.close()
    except Exception:
        pass
