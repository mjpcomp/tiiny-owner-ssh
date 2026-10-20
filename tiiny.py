"""Friendly launcher for the tested Tiiny backup/access engines. No device logic is changed."""
import argparse
import importlib.util
import ipaddress
import os
import pathlib
import shutil
import subprocess
import sys

ACTIONS=('check','backup','install','restore')
REQUIRED=('tiiny_token_check.py','tiiny_auth_check.py','tiiny_owner.py','tiiny_host_state.py',
          'tiiny_backup_ready.py','tiiny_access.py','tiiny_access_host.py')

def default_state_dir():
    base=pathlib.Path(os.environ['LOCALAPPDATA']) if os.environ.get('LOCALAPPDATA') else pathlib.Path.home()/'.local/state'
    return base/'TiinyOwnerSSH'/'device-baseline'

def ipv4(value):
    try:return str(ipaddress.IPv4Address(value))
    except ValueError:raise argparse.ArgumentTypeError('Enter a valid IPv4 address') from None

def choose_action():
    print('1 Check state (default)\n2 Backup original state\n3 Install owner SSH\n4 Restore original state\nQ Quit')
    options={'':'check','1':'check','2':'backup','3':'install','4':'restore','q':None,'quit':None}
    while True:
        value=input('Action [1]: ').strip().lower()
        if value in options:return options[value]
        if value in ACTIONS:return value
        print('Choose 1-4, an action name, or Q.')

def ask_ip():
    while True:
        try:return ipv4(input('Tiiny IPv4 address: ').strip())
        except argparse.ArgumentTypeError:print('Invalid IPv4 address; please try again.')

def build_command(action,host,state,key=None,root=None):
    root=pathlib.Path(root) if root else pathlib.Path(__file__).resolve().parent
    script='tiiny_backup_ready.py' if action=='backup' else 'tiiny_access.py'
    command=[sys.executable,str(root/script),action,host,'--state-dir',str(state)]
    if key is not None:command+=['--key',str(key)]
    return command

def wait_for_engine(command,root):
    process=subprocess.Popen(command,cwd=str(root))
    while True:
        try:return process.wait()
        except KeyboardInterrupt:
            print('\nWaiting for the engine to finish its interrupt handling/cleanup. The launcher will not kill it.',flush=True)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',nargs='?',choices=ACTIONS)
    parser.add_argument('host',nargs='?',type=ipv4,help='device IPv4; prompted if omitted')
    parser.add_argument('--ip',dest='ip_option',type=ipv4,help='alternative to positional IPv4')
    parser.add_argument('--state-dir',type=pathlib.Path,default=default_state_dir())
    parser.add_argument('--key',type=pathlib.Path,help='override the existing private-key path')
    parser.add_argument('--dry-run',action='store_true',help='show the invocation without executing it')
    args=parser.parse_args(argv)
    if args.host and args.ip_option and args.host!=args.ip_option:parser.error('Positional IP and --ip disagree')
    try:
        action=args.action or choose_action()
        if action is None:return 0
        host=args.host or args.ip_option or ask_ip()
        state=args.state_dir.expanduser().resolve()
        key=args.key.expanduser().resolve() if args.key else None
        root=pathlib.Path(__file__).resolve().parent
        missing=[name for name in REQUIRED if not (root/name).is_file()]
        if missing:print('Missing runtime files:',', '.join(missing));return 2
        command=build_command(action,host,state,key,root)
        print('Action:',action,'Device:',host)
        print('Private state directory:',state)
        if args.dry_run:
            print('DRY RUN: no engine executed, no device contacted, no state files created.')
            print(subprocess.list2cmdline(command));return 0
        if action!='backup' and not (state/'baseline.json').is_file():
            print('No saved baseline found. Use backup only on the original state; do not recreate an installed-state baseline.');return 2
        if action=='backup' and (state/'baseline.json').exists():
            print('Baseline already exists; refusing to replace it. Use check/install/restore with that baseline.');return 2
        if importlib.util.find_spec('cramjam') is None:
            print('Missing cramjam. Install with this Python interpreter: python -m pip install -r requirements.txt');return 2
        if not shutil.which('ssh'):print('Windows/OpenSSH client not found; install the SSH client first.');return 2
        print('The engine will request its existing typed confirmation. No confirmation is bypassed.',flush=True)
        return wait_for_engine(command,root)
    except (EOFError,KeyboardInterrupt):print('\nCancelled before engine execution.');return 130
    except OSError as error:print('Local launch error:',type(error).__name__);return 2

if __name__=='__main__':sys.exit(main())
