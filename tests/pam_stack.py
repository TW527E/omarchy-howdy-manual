from pathlib import Path
import subprocess
import tempfile

build = Path(__file__).resolve().parents[1] / 'build'
with tempfile.TemporaryDirectory(prefix='howdy-pam-test-') as directory:
    for name, face, password in [('face-ok', True, False), ('face-denied', False, False), ('password-ok', False, True), ('both-denied', False, False)]:
        face_module = f'{build}/test_backend.so face' if face else 'pam_deny.so'
        pass_module = f'{build}/test_backend.so password' if password else 'pam_deny.so'
        Path(directory, name).write_text(f'auth [success=ignore ignore=1 default=die] {build}/pam_howdy_choice.so\nauth sufficient {face_module}\nauth required {pass_module}\n')
    subprocess.run([str(build / 'test_choice'), directory], check=True)
