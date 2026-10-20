"""Launcher tests use only temporary files and mocked child processes. No device access."""
import argparse
import contextlib
import importlib.util
import io
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
import tiiny

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
        for name in tiiny.REQUIRED:(self.root/name).write_text('# test placeholder\n')
        self.state=self.root/'private-state';self.state.mkdir();(self.state/'baseline.json').write_text('{}')
        self.patches=[patch.object(tiiny,'__file__',str(self.root/'tiiny.py')),
            patch.object(tiiny.importlib.util,'find_spec',return_value=object()),patch.object(tiiny.shutil,'which',return_value='ssh'),
            patch.object(tiiny.subprocess,'Popen'),patch('sys.stdout',new_callable=io.StringIO)]
        self.mocks=[p.start() for p in self.patches]
        self.child=self.mocks[3].return_value;self.child.wait.return_value=0
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def call(self,*args):return tiiny.main([*args,'--state-dir',str(self.state)])
    def test_explicit_ip(self):
        with patch('builtins.input',side_effect=AssertionError('Unexpected prompt')):
            self.assertEqual(self.call('check','192.0.2.10'),0)
        self.assertIn('192.0.2.10',self.mocks[3].call_args.args[0])
    def test_prompted_ip(self):
        with patch('builtins.input',return_value='192.0.2.10') as prompt:self.assertEqual(self.call('check'),0)
        self.assertEqual(prompt.call_count,1)
    def test_menu_and_ip(self):
        with patch('builtins.input',side_effect=['1','192.0.2.10']):self.assertEqual(self.call(),0)
    def test_invalid_prompt_retried(self):
        with patch('builtins.input',side_effect=['bad','192.0.2.10']):self.assertEqual(self.call('check'),0)
    def test_ip_flag(self):
        self.assertEqual(self.call('restore','--ip','192.0.2.10'),0)
    def test_quit_does_not_launch(self):
        with patch('builtins.input',return_value='q'):self.assertEqual(self.call(),0)
        self.mocks[3].assert_not_called()
    def test_dry_run_no_child(self):
        self.assertEqual(self.call('check','192.0.2.10','--dry-run'),0);self.mocks[3].assert_not_called()
    def test_missing_baseline_blocks_restore(self):
        (self.state/'baseline.json').unlink()
        self.assertEqual(self.call('restore','192.0.2.10'),2);self.mocks[3].assert_not_called()
    def test_existing_baseline_blocks_backup(self):
        self.assertEqual(self.call('backup','192.0.2.10'),2);self.mocks[3].assert_not_called()
    def test_backup_routed_correctly(self):
        (self.state/'baseline.json').unlink()
        self.assertEqual(self.call('backup','192.0.2.10'),0)
        self.assertTrue(self.mocks[3].call_args.args[0][1].endswith('tiiny_backup_ready.py'))
    def test_same_interpreter_and_key_forwarded(self):
        key=self.root/'key with spaces'
        self.assertEqual(self.call('check','192.0.2.10','--key',str(key)),0)
        command=self.mocks[3].call_args.args[0]
        self.assertEqual(command[0],sys.executable);self.assertEqual(command[-2:],['--key',str(key)])
    def test_child_exit_code_preserved(self):
        self.child.wait.return_value=2;self.assertEqual(self.call('check','192.0.2.10'),2)
    def test_interrupt_waits_for_child_cleanup(self):
        self.child.wait.side_effect=[KeyboardInterrupt,0]
        self.assertEqual(self.call('check','192.0.2.10'),0)
        self.assertEqual(self.child.wait.call_count,2);self.child.kill.assert_not_called()
    def test_missing_module_blocks_launch(self):
        (self.root/'tiiny_owner.py').unlink()
        self.assertEqual(self.call('check','192.0.2.10'),2);self.mocks[3].assert_not_called()
    def test_default_windows_state_location(self):
        with patch.dict(os.environ,{'LOCALAPPDATA':str(self.root)}):
            self.assertEqual(tiiny.default_state_dir(),self.root/'TiinyOwnerSSH/device-baseline')
    def test_invalid_cli_ip_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
            self.call('check','not-an-ip')
        self.assertEqual(error.exception.code,2);self.mocks[3].assert_not_called()

if __name__=='__main__':unittest.main()
