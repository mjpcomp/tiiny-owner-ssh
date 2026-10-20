"""Host-side state operations for the experimental owner SSH utility."""
import base64
import hashlib
import os
import pathlib
import signal
import stat
import subprocess

PATHS = ('/etc/ssh/owner_authorized_keys', '/etc/ssh/owner_authorized_keys/root', '/etc/ssh/sshd_config.d/00-owner-access.conf')
CONF = b'# Owner-managed key access\nPermitRootLogin prohibit-password\nAuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2 /etc/ssh/owner_authorized_keys/%u\n'

def checked(root, path):
    current = pathlib.Path(root)
    for part in pathlib.PurePosixPath(path).parts[1:]:
        current = current / part
        if current.is_symlink():
            raise RuntimeError('Symlink in managed path; refusing')
    return current

def snapshot(root, path):
    p = checked(root, path)
    try:
        s = p.stat()
    except FileNotFoundError:
        return {'exists': False}
    record = {'exists': True, 'mode': stat.S_IMODE(s.st_mode), 'uid': s.st_uid, 'gid': s.st_gid}
    if stat.S_ISREG(s.st_mode):
        record['kind'] = 'file'
        record['data'] = base64.b64encode(p.read_bytes()).decode()
    elif stat.S_ISDIR(s.st_mode):
        record['kind'] = 'directory'
    else:
        raise RuntimeError('Unsupported managed path type')
    return record

def identity(root):
    def read(path):
        if str(root)=='/host' and path=='/etc/os-release':
            return subprocess.check_output(['chroot','/host','cat',path])
        return checked(root,path).read_bytes()
    return {'machine_id_sha256': hashlib.sha256(read('/etc/machine-id')).hexdigest(),
            'ssh_host_key': read('/etc/ssh/ssh_host_ed25519_key.pub').decode().strip(),
            'os_release_sha256': hashlib.sha256(read('/etc/os-release')).hexdigest(),
            'sshd_config_sha256': hashlib.sha256(read('/etc/ssh/sshd_config')).hexdigest()}

def capture(root):
    return {'identity':identity(root), 'paths':{p:snapshot(root,p) for p in PATHS}}

def desired(before, public_key):
    fields=public_key.split()
    if len(fields)<2 or fields[0]!='ssh-ed25519' or '\n' in public_key or '\r' in public_key:
        raise RuntimeError('Invalid owner public key')
    records=before['paths']
    directory, keyfile, config=(records[p] for p in PATHS)
    if directory.get('exists') and directory.get('kind')!='directory':
        raise RuntimeError('Owner directory is not a directory')
    for r in (keyfile,config):
        if r.get('exists') and r.get('kind')!='file':
            raise RuntimeError('Expected regular file')
    if config.get('exists') and base64.b64decode(config['data'])!=CONF:
        raise RuntimeError('Different owner configuration already exists')
    old=base64.b64decode(keyfile['data']) if keyfile.get('exists') else b''
    text=old.decode('utf-8')
    # Avoid claiming we introduced a key that already existed at this managed location.
    if any(line.split()[:2]==fields[:2] for line in text.splitlines()):
        raise RuntimeError('Owner key already present in baseline')
    updated=old+(b'' if not old or old.endswith(b'\n') else b'\n')+public_key.encode()+b'\n'
    def regular(data,mode):
        return {'exists':True,'kind':'file','mode':mode,'uid':0,'gid':0,'data':base64.b64encode(data).decode()}
    return {'identity':before['identity'],'paths':{
        PATHS[0]:{'exists':True,'kind':'directory','mode':0o700,'uid':0,'gid':0},
        PATHS[1]:regular(updated,0o600), PATHS[2]:regular(CONF,0o644)}}

def write_state(root, target):
    # Files are changed only after the caller has compared all current state.
    for path in PATHS:
        record=target['paths'][path]
        p=checked(root,path)
        if record['exists']:
            if record['kind']=='directory':
                p.mkdir(exist_ok=True)
            else:
                p.write_bytes(base64.b64decode(record['data'],validate=True))
            os.chown(p,record['uid'],record['gid'])
            os.chmod(p,record['mode'])
    for path in reversed(PATHS):
        record=target['paths'][path]
        p=checked(root,path)
        if not record['exists'] and p.exists():
            if p.is_dir():
                p.rmdir()  # Refuse to remove unrelated contents.
            else:
                p.unlink()

def validate():
    subprocess.run(['chroot','/host','/usr/sbin/sshd','-t'],check=True,capture_output=True)

def reload_ssh():
    pid=int(pathlib.Path('/host/run/sshd.pid').read_text())
    if pathlib.Path('/proc/%s/comm'%pid).read_text().strip()!='sshd':
        raise RuntimeError('SSH PID check failed')
    os.kill(pid,signal.SIGHUP)

def dispatch(payload):
    root='/host'
    if subprocess.check_output(['chroot',root,'findmnt','-n','-o','FSTYPE','/etc'],text=True).strip()!='overlay':
        raise RuntimeError('Unexpected /etc filesystem')
    if payload.get('action') != 'backup':
        subprocess.run(['chroot',root,'systemctl','is-enabled','ssh'],check=True,capture_output=True)
    if not checked(root,'/etc/ssh/sshd_config.d').is_dir():
        raise RuntimeError('SSH drop-in directory missing')
    current=capture(root)
    action=payload['action']
    if action=='backup':
        validate()
        return {'ok':True,'state':current,'ssh_unit_info':_owner_ssh_unit_info(root)}
    before=payload['before']
    after=desired(before,payload['public_key'])
    if action=='install':
        expected,target=before,after
    elif action=='restore':
        expected,target=after,before
    else:
        raise RuntimeError('Unknown action')
    if current==target:
        validate()
        reload_ssh()
        return {'ok':True,'state':current,'already_in_target_state':True}
    if current!=expected:
        raise RuntimeError('Managed files, metadata, or identity differ from expected state; refusing')
    try:
        write_state(root,target)
        validate()
        reload_ssh()
        result=capture(root)
        if result!=target:
            raise RuntimeError('Post-change state verification failed')
    except Exception:
        try:
            write_state(root,expected)
            validate()
            reload_ssh()
        except Exception:
            raise RuntimeError('Operation failed and rollback failed; manual recovery required') from None
        raise RuntimeError('Operation failed; prior managed state restored') from None
    return {'ok':True,'state':result}


def _owner_ssh_unit_info(root):
    known={'enabled','enabled-runtime','disabled','static','indirect','masked','masked-runtime','alias','generated','transient','linked','linked-runtime','not-found','bad'}
    rows=[]
    for unit in ('ssh.service','sshd.service','ssh.socket','sshd.socket'):
        try:
            p=subprocess.run(['chroot',str(root),'systemctl','is-enabled',unit],capture_output=True,text=True,timeout=10)
            words=p.stdout.strip().splitlines()
            state=words[0].strip() if len(words)==1 and words[0].strip() in known else 'unrecognized-output' if p.stdout.strip() else 'no-output'
            stderr=p.stderr.lower()
            category='none'
            if stderr:
                if 'does not exist' in stderr or 'not found' in stderr:category='unit-not-found'
                elif 'connect to bus' in stderr:category='bus-unavailable'
                elif 'read-only file system' in stderr:category='read-only-filesystem'
                elif 'permission denied' in stderr or 'operation not permitted' in stderr:category='permission-denied'
                elif 'chroot' in stderr:category='chroot-context'
                else:category='other-stderr-hidden'
            rows.append({'unit':unit,'state':state,'exit_code':p.returncode,'stderr_category':category})
        except Exception as error:
            rows.append({'unit':unit,'exception_type':type(error).__name__})
    return rows
