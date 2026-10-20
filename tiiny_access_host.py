"""Host-side state operations for the experimental owner SSH utility."""
import base64
import hashlib
import os
import pathlib
import signal
import stat
import subprocess
import uuid
import re

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
        if s.st_nlink != 1:
            raise RuntimeError('Hard-linked managed file; refusing')
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


def write_state(root,target):
    for path in PATHS:
        record=target['paths'][path]
        p=checked(root,path)
        if record['exists']:
            if record['kind']=='directory':
                p.mkdir(exist_ok=True)
                os.chown(p,record['uid'],record['gid']);os.chmod(p,record['mode'])
            else:
                temporary=p.with_name('.owner-ssh-'+uuid.uuid4().hex)
                try:
                    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'wb') as f:
                        f.write(base64.b64decode(record['data'],validate=True))
                        f.flush();os.fchown(f.fileno(),record['uid'],record['gid'])
                        os.fchmod(f.fileno(),record['mode']);os.fsync(f.fileno())
                    os.replace(temporary,p)
                finally:
                    if temporary.exists():temporary.unlink()
    for path in reversed(PATHS):
        p=checked(root,path)
        if not target['paths'][path]['exists'] and p.exists():
            if p.is_dir():p.rmdir()
            else:p.unlink()

def validate(root):
    subprocess.run(['chroot',str(root),'/usr/sbin/sshd','-t'],check=True,capture_output=True,timeout=15)

def effective(root):
    p=subprocess.run(['chroot',str(root),'/usr/sbin/sshd','-T'],check=True,capture_output=True,text=True,timeout=15)
    result={}
    for line in p.stdout.splitlines():
        key,_,value=line.partition(' ')
        if key in ('permitrootlogin','pubkeyauthentication','authorizedkeysfile','pidfile'):
            result[key]=value
        elif key=='port':result.setdefault('ports',[]).append(int(value))
    return result

def offline_units(root):
    p=subprocess.run(['chroot',str(root),'systemctl','--root=/','is-enabled','ssh.service'],capture_output=True,text=True,timeout=15)
    return p.returncode==0 and p.stdout.strip()=='enabled'

def listener(root,signal_namespace):
    pid=int(checked(root,'/run/sshd.pid').read_text().strip())
    if pid<=1:raise RuntimeError('Invalid SSH listener PID')
    proc=pathlib.Path('/proc') if signal_namespace else checked(root,'/proc')
    directory=proc/str(pid)
    if (directory/'comm').read_text().strip()!='sshd':raise RuntimeError('SSH listener PID check failed')
    arguments=(directory/'cmdline').read_bytes().replace(b'\x00',b' ').decode('utf-8',errors='replace')
    if re.search(r'(?:^|\s)-(?:f|o)',arguments):raise RuntimeError('Listener has a custom configuration override; refusing')
    return pid

def reload_ssh(root,pid):
    if listener(root,True)!=pid:raise RuntimeError('SSH listener changed before reload')
    os.kill(pid,signal.SIGHUP)

def environment(root):
    kind=subprocess.check_output(['chroot',str(root),'findmnt','-n','-o','FSTYPE','/etc'],text=True).strip()
    if kind!='overlay':raise RuntimeError('Unexpected /etc persistence layout')
    if not checked(root,'/etc/ssh/sshd_config.d').is_dir():raise RuntimeError('Missing SSH drop-in directory')

def installed_policy(settings):
    return (settings.get('permitrootlogin') in ('prohibit-password','without-password')
            and settings.get('pubkeyauthentication')=='yes'
            and '/etc/ssh/owner_authorized_keys/%u' in settings.get('authorizedkeysfile','').split()
            and 3588 in settings.get('ports',[]))

def dispatch(payload,root='/host'):
    action=payload.get('action')
    if action not in ('check','install','restore'):raise RuntimeError('Unsupported operation')
    before=payload['before'];after=desired(before,payload['public_key'])
    environment(root)
    current=capture(root)
    if current['identity']!=before['identity']:raise RuntimeError('Device/configuration identity changed; refusing')
    if current!=before and current!=after:raise RuntimeError('Managed files or metadata differ from both known states; refusing')
    validate(root)
    settings=effective(root)
    enabled=offline_units(root)
    pid=listener(root,action!='check')
    if action=='check':
        return {'ok':True,'state':current,'at_baseline':current==before,'at_installed_state':current==after,
            'ssh_service_enabled_offline':enabled,'listener_verified':True,
            'settings':{k:v for k,v in settings.items() if k!='authorizedkeysfile'}}
    target=after if action=='install' else before
    if current==target:
        if action=='restore' and settings.get('permitrootlogin')!='no':
            raise RuntimeError('Files match baseline but effective root policy is not no; review other configuration')
        if action=='install' and not installed_policy(settings):raise RuntimeError('Installed files are present but effective policy differs')
        return {'ok':True,'state':current,'already_in_target_state':True,'files_changed':False}
    if action=='install':
        if not enabled:raise RuntimeError('Native ssh.service not confirmed enabled offline')
        if settings.get('permitrootlogin')!='no' or settings.get('pubkeyauthentication')!='yes':
            raise RuntimeError('Baseline effective authentication differs from the reviewed preflight')
        if settings.get('authorizedkeysfile','').split()!=['.ssh/authorized_keys','.ssh/authorized_keys2']:
            raise RuntimeError('Customized AuthorizedKeysFile baseline; refusing to replace its search paths')
    try:
        write_state(root,target)
        validate(root)
        new_settings=effective(root)
        if action=='install' and not installed_policy(new_settings):raise RuntimeError('Owner drop-in does not produce the intended effective policy')
        if action=='restore' and new_settings.get('permitrootlogin')!='no':raise RuntimeError('Restored configuration does not disable root login as expected')
        if capture(root)!=target:raise RuntimeError('Managed-state read-back failed')
        reload_ssh(root,pid)
    except Exception:
        try:
            write_state(root,current)
            validate(root)
            if capture(root)!=current or effective(root)!=settings:raise RuntimeError('Rollback state mismatch')
            reload_ssh(root,pid)
        except Exception:
            raise RuntimeError('Operation failed and rollback is unverified; preserve baseline and seek manual recovery') from None
        raise RuntimeError('Operation failed; prior files/configuration restored and reload requested') from None
    return {'ok':True,'state':capture(root),'files_changed':True,'reload_requested':True,
            'effective_root_policy':new_settings.get('permitrootlogin')}
