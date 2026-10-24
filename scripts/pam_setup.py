#!/usr/bin/env python3
"""Explicit root-only setup; importing this module never changes the system."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

MODULE = Path('/usr/local/lib/security/pam_howdy_choice.so')
STATE = Path('/var/lib/omarchy-howdy-manual')
PAM_DIR = Path('/etc/pam.d')
HOWDY = Path('/usr/lib/security/pam_howdy.so')
BEGIN = '# BEGIN omarchy-howdy-manual\n'
END = '# END omarchy-howdy-manual\n'
GATE = f'auth [success=ignore ignore=1 default=die] {MODULE}\n'
BLOCK = BEGIN + GATE + 'auth sufficient pam_howdy.so\n' + END


def configure(text):
    """Only accept a simple, already configured Howdy-first authentication stack."""
    if BEGIN in text or END in text:
        raise ValueError('Already managed; use the recorded installation state')
    lines = text.splitlines(keepends=True)
    auth = [(i, line) for i, line in enumerate(lines) if re.match(r'^\s*-?auth\s', line)]
    if not auth or not any(re.match(r'^\s*auth\s+include\s+system-auth\s*$', l) for _, l in auth):
        raise ValueError('Expected an existing system-auth password fallback')
    first = auth[0][0]
    # Adopt the initial local prototype without enabling face auth on a new service.
    if lines[first] == GATE:
        first_howdy = first + 1
    else:
        first_howdy = first
    pattern = r'^\s*auth\s+sufficient\s+pam_howdy\.so(?:\s+workaround=(?:native|input|native-input))?\s*$'
    if first_howdy >= len(lines) or not re.match(pattern, lines[first_howdy]):
        raise ValueError('Howdy must already be the first auth method; custom PAM stacks need manual review')
    following = [line for i, line in auth if i > first_howdy]
    if len(following) != 1 or not re.match(r'^\s*auth\s+include\s+system-auth\s*$', following[0]):
        raise ValueError('Expected only system-auth after Howdy; custom auth branches need manual review')
    if sum('pam_howdy.so' in l for _, l in auth) != 1:
        raise ValueError('Expected exactly one Howdy auth line')
    if any('pam_howdy_choice.so' in l for i, l in auth if i != first):
        raise ValueError('Unexpected duplicate choice module')
    return ''.join(lines[:first]) + BLOCK + ''.join(lines[first_howdy + 1:])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode):
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def root_owned(path, directory=False):
    info = path.lstat()
    expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not expected or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError(f'Expected a root-owned, non-writable {"directory" if directory else "file"}: {path}')


def install(services, binary):
    if STATE.exists():
        raise ValueError(f'Installation state already exists at {STATE}; remove the managed setup before reinstalling')
    if not HOWDY.is_file():
        raise ValueError('Install and configure Howdy Next before using this helper')
    originals, applied = {}, {}
    for name in services:
        path = PAM_DIR / name
        root_owned(path)
        originals[name] = path.read_text()
        applied[name] = configure(originals[name])
    module = binary.read_bytes()
    if not module.startswith(b'\x7fELF'):
        raise ValueError('Expected the compiled PAM module; run make first')
    previous = None
    if MODULE.exists() or MODULE.is_symlink():
        root_owned(MODULE)
        previous = MODULE.read_bytes()
        if previous != module:
            raise ValueError('A different choice module already exists; review it before replacing')
    for path in (MODULE.parent.parent.parent, MODULE.parent.parent, STATE.parent, PAM_DIR):
        root_owned(path, directory=True)
    MODULE.parent.mkdir(mode=0o755, exist_ok=True)
    root_owned(MODULE.parent, directory=True)
    STATE.mkdir(mode=0o700)
    state = {'original': originals, 'applied': applied, 'module_sha256': digest(module), 'previous_module': previous is not None}
    if previous is not None:
        atomic_write(STATE / 'module.before', previous, 0o600)
    # Save recovery data before touching any active PAM file.
    atomic_write(STATE / 'state.json', (json.dumps(state, indent=2) + '\n').encode(), 0o600)
    try:
        atomic_write(MODULE, module, 0o755)
        for name, text in applied.items():
            atomic_write(PAM_DIR / name, text.encode(), 0o644)
    except BaseException:
        for name, text in originals.items():
            atomic_write(PAM_DIR / name, text.encode(), 0o644)
        if previous is not None:
            atomic_write(MODULE, previous, 0o755)
        elif MODULE.exists():
            MODULE.unlink()
        STATE.rename(STATE.with_name('omarchy-howdy-manual-failed-' + str(os.getpid())))
        raise
    print('Manual choice installed for ' + ', '.join(services) + '. Backup: ' + str(STATE))


def remove():
    root_owned(STATE, directory=True)
    root_owned(STATE / 'state.json')
    state = json.loads((STATE / 'state.json').read_text())
    if not set(state['original']) <= {'sudo', 'polkit-1'} or set(state['original']) != set(state['applied']):
        raise ValueError('Invalid recovery state')
    root_owned(MODULE)
    if digest(MODULE.read_bytes()) != state['module_sha256']:
        raise ValueError('PAM module changed; refusing to overwrite newer work')
    for name, expected in state['applied'].items():
        path = PAM_DIR / name
        root_owned(path)
        if path.read_text() != expected:
            raise ValueError(f'{path} changed; merge the backup manually rather than overwriting newer work')
    previous = None
    if state['previous_module']:
        root_owned(STATE / 'module.before')
        previous = (STATE / 'module.before').read_bytes()
    module = MODULE.read_bytes()
    try:
        for name, text in state['original'].items():
            atomic_write(PAM_DIR / name, text.encode(), 0o644)
        if previous is not None:
            atomic_write(MODULE, previous, 0o755)
        else:
            MODULE.unlink()
    except BaseException:
        atomic_write(MODULE, module, 0o755)
        for name, text in state['applied'].items():
            atomic_write(PAM_DIR / name, text.encode(), 0o644)
        raise
    saved = STATE.with_name('omarchy-howdy-manual-restored-' + str(os.getpid()))
    STATE.rename(saved)
    print('Original authentication restored. Recovery record retained at ' + str(saved))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'remove'))
    parser.add_argument('--sudo', action='store_true', help='also gate sudo (it must already use Howdy)')
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Run with sudo in a terminal, or pkexec without a terminal')
    try:
        if args.action == 'install':
            install(['polkit-1', 'sudo'] if args.sudo else ['polkit-1'], Path(__file__).resolve().parents[1] / 'build/pam_howdy_choice.so')
        else:
            remove()
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
