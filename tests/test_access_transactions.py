"""POSIX host-state regression tests. System checks and signals are mocked."""
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import tiiny_access_host as host
KEY='ssh-ed25519 c3ludGhldGljLXB1YmxpYy10ZXN0LW9ubHk= test-only'

class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
        (self.root/'etc/ssh/sshd_config.d').mkdir(parents=True)
        for name,value in {'etc/machine-id':b'synthetic','etc/os-release':b'ID=test\n',
            'etc/ssh/ssh_host_ed25519_key.pub':KEY.encode(),'etc/ssh/sshd_config':b'PermitRootLogin no\n'}.items():
            (self.root/name).write_bytes(value)
        self.before=host.capture(self.root);self.original_desired=host.desired
        def desired(before,key):
            result=self.original_desired(before,key)
            for record in result['paths'].values():
                if record['exists']:record['uid']=os.getuid();record['gid']=os.getgid()
            return result
        self.patches=[patch.object(host,'environment'),patch.object(host,'offline_units',return_value=True),
            patch.object(host,'listener',return_value=23456),patch.object(host,'reload_ssh'),patch.object(host,'validate'),
            patch.object(host,'effective',side_effect=self.settings),patch.object(host,'desired',side_effect=desired)]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def settings(self,root):
        installed=(self.root/'etc/ssh/sshd_config.d/00-owner-access.conf').exists()
        return {'permitrootlogin':'prohibit-password' if installed else 'no','pubkeyauthentication':'yes',
            'authorizedkeysfile':'.ssh/authorized_keys .ssh/authorized_keys2'+(' /etc/ssh/owner_authorized_keys/%u' if installed else ''),
            'pidfile':'/run/sshd.pid','ports':[3588]}
    def run_action(self,action):return host.dispatch({'action':action,'before':self.before,'public_key':KEY},self.root)
    def assert_baseline(self):self.assertEqual(host.capture(self.root),self.before)
    def test_roundtrip(self):
        self.assertTrue(self.run_action('install')['files_changed']);self.run_action('restore');self.assert_baseline()
    def test_noop_restore(self):
        self.assertFalse(self.run_action('restore')['files_changed']);host.reload_ssh.assert_not_called()
    def test_readonly_check(self):
        self.assertTrue(self.run_action('check')['at_baseline']);self.assert_baseline();host.reload_ssh.assert_not_called()
    def test_idempotent_install(self):
        self.run_action('install');host.reload_ssh.reset_mock()
        self.assertFalse(self.run_action('install')['files_changed']);host.reload_ssh.assert_not_called()
    def test_config_conflict(self):
        (self.root/'etc/ssh/sshd_config.d/00-owner-access.conf').write_text('unexpected')
        with self.assertRaises(RuntimeError):self.run_action('install')
        host.reload_ssh.assert_not_called()
    def test_identity_conflict(self):
        (self.root/'etc/machine-id').write_text('different')
        with self.assertRaises(RuntimeError):self.run_action('install')
        host.reload_ssh.assert_not_called()
    def test_disabled_unit(self):
        self.run_action('install');host.offline_units.return_value=False;self.run_action('restore');self.assert_baseline()
        with self.assertRaises(RuntimeError):self.run_action('install')
    def test_validation_rollback(self):
        host.validate.side_effect=[None,RuntimeError('synthetic'),None]
        with self.assertRaisesRegex(RuntimeError,'prior files/configuration restored'):self.run_action('install')
        self.assert_baseline()
    def test_reload_rollback(self):
        host.reload_ssh.side_effect=[RuntimeError('synthetic'),None]
        with self.assertRaisesRegex(RuntimeError,'prior files/configuration restored'):self.run_action('install')
        self.assert_baseline()
    def test_restore_conflict(self):
        self.run_action('install');p=self.root/'etc/ssh/owner_authorized_keys/root';p.write_text('keep')
        with self.assertRaises(RuntimeError):self.run_action('restore')
        self.assertEqual(p.read_text(),'keep')
    def test_existing_bytes(self):
        d=self.root/'etc/ssh/owner_authorized_keys';d.mkdir(mode=0o750)
        p=d/'root';p.write_bytes(b'# original no newline');p.chmod(0o640)
        self.before=host.capture(self.root);self.run_action('install');self.run_action('restore');self.assert_baseline()
    def test_symlink(self):
        (self.root/'etc/ssh/sshd_config.d/00-owner-access.conf').symlink_to(self.root/'etc/os-release')
        with self.assertRaises(RuntimeError):self.run_action('install')
    def test_hardlink(self):
        os.link(self.root/'etc/os-release',self.root/'etc/ssh/sshd_config.d/00-owner-access.conf')
        with self.assertRaises(RuntimeError):self.run_action('install')
    def test_unrelated_content(self):
        self.run_action('install');p=self.root/'etc/ssh/owner_authorized_keys/unrelated';p.write_text('keep')
        with self.assertRaises(RuntimeError):self.run_action('restore')
        self.assertEqual(p.read_text(),'keep')
    def test_custom_key_paths(self):
        host.effective.side_effect=None
        host.effective.return_value={'permitrootlogin':'no','pubkeyauthentication':'yes','authorizedkeysfile':'/custom','ports':[3588]}
        with self.assertRaises(RuntimeError):self.run_action('install')
        self.assert_baseline()
    def test_root_target_metadata(self):
        self.assertTrue(all(r['uid']==0 and r['gid']==0 for r in self.original_desired(self.before,KEY)['paths'].values()))

if __name__=='__main__':unittest.main()
