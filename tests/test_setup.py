import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('setup', Path(__file__).resolve().parents[1] / 'scripts/pam_setup.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class SetupTests(unittest.TestCase):
    def test_supported_modes_preserve_password_and_account_stack(self):
        for option in ['', ' workaround=native', ' workaround=native-input', ' workaround=input']:
            original = '#%PAM-1.0\nauth sufficient pam_howdy.so' + option + '\nauth include system-auth\naccount include system-auth\n'
            result = setup.configure(original)
            self.assertEqual(result, '#%PAM-1.0\n' + setup.BLOCK + 'auth include system-auth\naccount include system-auth\n')

    def test_adopts_prototype(self):
        original = setup.GATE + 'auth sufficient pam_howdy.so\nauth include system-auth\n'
        self.assertEqual(setup.configure(original), setup.BLOCK + 'auth include system-auth\n')

    def test_refuses_unsafe_or_unknown_stacks(self):
        for text in [
            'auth sufficient pam_howdy.so\n',
            'auth sufficient pam_unix.so\nauth sufficient pam_howdy.so\nauth include system-auth\n',
            'auth sufficient pam_howdy.so\nauth sufficient pam_howdy.so\nauth include system-auth\n',
            'auth required pam_howdy.so\nauth include system-auth\n',
            'auth sufficient pam_howdy.so unknown=option\nauth include system-auth\n',
            'auth sufficient pam_howdy.so\nauth sufficient pam_permit.so\nauth include system-auth\n',
            setup.BLOCK + 'auth include system-auth\n',
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                setup.configure(text)

    def test_atomic_write_replaces_without_following_target_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'pam')
            other = Path(directory, 'unrelated')
            other.write_bytes(b'keep')
            target.symlink_to(other)
            setup.atomic_write(target, b'replacement', 0o600)
            self.assertEqual(other.read_bytes(), b'keep')
            self.assertFalse(target.is_symlink())
            self.assertEqual(target.read_bytes(), b'replacement')
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name, value in {
            'MODULE': self.root / 'usr/local/lib/security/pam_howdy_choice.so',
            'STATE': self.root / 'var/lib/omarchy-howdy-manual',
            'PAM_DIR': self.root / 'etc/pam.d',
            'HOWDY': self.root / 'usr/lib/security/pam_howdy.so',
        }.items():
            value.parent.mkdir(parents=True, exist_ok=True)
            mock = patch.object(setup, name, value)
            mock.start()
            self.addCleanup(mock.stop)
        setup.PAM_DIR.mkdir(exist_ok=True)
        setup.HOWDY.write_bytes(b'installed-howdy')
        self.original = 'auth sufficient pam_howdy.so workaround=native\nauth include system-auth\n'
        for service in ['polkit-1', 'sudo']:
            (setup.PAM_DIR / service).write_text(self.original)
        self.binary = self.root / 'built.so'
        self.binary.write_bytes(b'\x7fELFtest-module')
        # Only the temporary tree's ownership check is bypassed; no real system paths are used.
        mock = patch.object(setup, 'root_owned')
        mock.start()
        self.addCleanup(mock.stop)

    def test_install_remove_roundtrip(self):
        setup.install(['polkit-1', 'sudo'], self.binary)
        self.assertEqual(setup.MODULE.read_bytes(), self.binary.read_bytes())
        self.assertIn(setup.BEGIN, (setup.PAM_DIR / 'polkit-1').read_text())
        setup.remove()
        for service in ['polkit-1', 'sudo']:
            self.assertEqual((setup.PAM_DIR / service).read_text(), self.original)
        self.assertFalse(setup.MODULE.exists())
        self.assertFalse(setup.STATE.exists())

    def test_remove_preserves_preexisting_prototype_module(self):
        setup.MODULE.write_bytes(self.binary.read_bytes())
        original = setup.GATE + 'auth sufficient pam_howdy.so\nauth include system-auth\n'
        (setup.PAM_DIR / 'polkit-1').write_text(original)
        setup.install(['polkit-1'], self.binary)
        setup.remove()
        self.assertEqual(setup.MODULE.read_bytes(), self.binary.read_bytes())
        self.assertEqual((setup.PAM_DIR / 'polkit-1').read_text(), original)

    def test_refuse_remove_after_user_changes_pam(self):
        setup.install(['polkit-1'], self.binary)
        path = setup.PAM_DIR / 'polkit-1'
        changed = path.read_text() + '# later user change\n'
        path.write_text(changed)
        with self.assertRaises(ValueError):
            setup.remove()
        self.assertEqual(path.read_text(), changed)
        self.assertTrue(setup.MODULE.exists())

    def test_refuse_duplicate_install_without_overwriting_backup(self):
        setup.install(['polkit-1'], self.binary)
        state = (setup.STATE / 'state.json').read_bytes()
        with self.assertRaises(ValueError):
            setup.install(['polkit-1'], self.binary)
        self.assertEqual((setup.STATE / 'state.json').read_bytes(), state)

    def test_failed_install_restores_both_pam_files(self):
        write = setup.atomic_write
        failed = False
        def fail_second(path, data, mode):
            nonlocal failed
            if path == setup.PAM_DIR / 'sudo' and not failed:
                failed = True
                raise OSError('simulated write failure')
            write(path, data, mode)
        with patch.object(setup, 'atomic_write', fail_second), self.assertRaises(OSError):
            setup.install(['polkit-1', 'sudo'], self.binary)
        for service in ['polkit-1', 'sudo']:
            self.assertEqual((setup.PAM_DIR / service).read_text(), self.original)
        self.assertFalse(setup.MODULE.exists())

        self.assertFalse(setup.STATE.exists())

    def test_failed_remove_restores_managed_configuration(self):
        setup.install(['polkit-1', 'sudo'], self.binary)
        expected = (setup.PAM_DIR / 'polkit-1').read_text()
        write = setup.atomic_write
        failed = False
        def fail_second(path, data, mode):
            nonlocal failed
            if path == setup.PAM_DIR / 'sudo' and not failed:
                failed = True
                raise OSError('simulated write failure')
            write(path, data, mode)
        with patch.object(setup, 'atomic_write', fail_second), self.assertRaises(OSError):
            setup.remove()
        for service in ['polkit-1', 'sudo']:
            self.assertEqual((setup.PAM_DIR / service).read_text(), expected)
        self.assertEqual(setup.MODULE.read_bytes(), self.binary.read_bytes())
