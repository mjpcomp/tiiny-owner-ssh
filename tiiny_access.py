"""Paired experimental owner SSH install/restore, using an existing verified baseline.
Never backs up over baseline.json. Requires the working backup preview modules.
"""
import argparse
import hashlib
import ipaddress
import json
import pathlib
import subprocess
import sys
import threading
import time
import uuid
import tiiny_owner as owner
from tiiny_backup_ready import CompatibleSession, IMAGE

class AccessSession(CompatibleSession):
    def __init__(self,host,token,work,action):
        super().__init__(host,token,work)
        self.action=action
    def start(self):
        self._stream=None;self._thread=None;self._stop=threading.Event()
        print('Creating temporary management connector:',self.name,flush=True)
        created=self.connector('','POST',{'name':self.name,'description':'Temporary owner SSH '+self.action+' helper',
            'transport':'stdio','command':'python3','arguments':['-u','-c',owner.MCP],
            'runEnvironment':'tiiny','enabled':True,'timeout_seconds':45})
        self.mcp=str(created['id'])
        owner.save_new(self.work/('connector-'+self.name+'.json'),{'id':self.mcp,'name':self.name})
        self.image=IMAGE
    def device(self,port,path,method='GET',body=None):
        if port!=8880:raise RuntimeError('Unexpected device API route')
        if method=='POST' and path=='/api/services':
            compose=json.loads(body['compose_file'])
            setup=compose.get('services',{}).get('setup',{})
            mode='ro' if self.action=='check' else 'rw'
            expected=['/:/host:'+mode,'aibox_connectors_config:/report']
            if setup.get('image')!=IMAGE or setup.get('pull_policy')!='never' or setup.get('network_mode')!='none' or setup.get('volumes')!=expected:
                raise RuntimeError('Unexpected execution-container configuration')
            setup['read_only']=True
            if self.action=='check':setup.pop('pid',None)
            elif setup.get('pid')!='host':raise RuntimeError('Host PID namespace required for targeted SSH reload')
            body=dict(body);body['compose_file']=json.dumps(compose)
            print('Temporary '+self.action+' service: host mount '+mode+'; container network disabled.',flush=True)
            return self.request(path,method,body)
        # Existing tested stream handling and read/delete routes.
        return super().device(port,path,method,body)
    def run_action(self,payload):
        if payload['action']!=self.action:raise RuntimeError('Action mismatch')
        source=pathlib.Path(__file__).with_name('tiiny_access_host.py').read_text(encoding='utf-8-sig')
        setup='import json,pathlib,time\n'+source+'\n'
        setup+='\ntry:\n result=dispatch('+repr(payload)+')\nexcept Exception as error:\n result={"ok":False,"error":str(error)}\n'
        setup+='pathlib.Path('+repr('/report/'+self.name+'.json')+').write_text(json.dumps(result))\ntime.sleep(180)\n'
        mode='ro' if self.action=='check' else 'rw'
        service={'image':IMAGE,'pull_policy':'never','user':'0:0','entrypoint':['python3','-c',setup],
            'restart':'no','network_mode':'none','read_only':True,
            'volumes':['/:/host:'+mode,'aibox_connectors_config:/report']}
        if self.action!='check':service['pid']='host'
        compose={'services':{'setup':service},'volumes':{'aibox_connectors_config':{'external':True}}}
        self.service=True
        self.device(8880,'/api/services','POST',{'id':self.name,'name':self.name,'compose_file':json.dumps(compose)})
        self.device(8880,'/api/services/'+self.name+'/start','POST')
        for attempt in range(25):
            try:
                raw=self.remote("import pathlib;p=pathlib.Path('/data/connectors/%s.json');print(p.read_text() if p.exists() else '{}')"%self.name)
                report=json.loads(raw)
            except ValueError:raise RuntimeError('Non-JSON report output; contents hidden') from None
            if report:
                if not report.get('ok'):raise RuntimeError(report.get('error','Host operation failed'))
                return report
            time.sleep(2)
        raise RuntimeError('No host report; operation outcome unknown until restore/state check')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['check','install','restore'])
    parser.add_argument('host',type=lambda v:str(ipaddress.IPv4Address(v)))
    parser.add_argument('--state-dir',required=True,type=pathlib.Path)
    parser.add_argument('--key',type=pathlib.Path,default=pathlib.Path.home()/'.ssh/tiiny_owner_ed25519')
    args=parser.parse_args()
    work=args.state_dir.expanduser().resolve()
    baseline_file=work/'baseline.json';original=baseline_file.read_bytes()
    baseline=owner.load_backup(baseline_file)
    if baseline.get('host')!=args.host:raise RuntimeError('Target address differs from baseline')
    if baseline.get('bootstrap_image_reference')!=IMAGE:raise RuntimeError('Image differs from baseline')
    key=args.key.expanduser().resolve()
    public_key=baseline['public_key']
    if args.action=='install':
        pub=pathlib.Path(str(key)+'.pub')
        if not key.is_file() or not pub.is_file() or pub.read_text(encoding='utf-8-sig').strip()!=public_key:
            raise RuntimeError('Installation key pair does not match baseline')
    known=work/'known_hosts';config=work/'ssh_config'
    expected='[%s]:3588 %s\n'%(args.host,' '.join(baseline['before']['identity']['ssh_host_key'].split()[:2]))
    if known.read_text()!=expected:raise RuntimeError('Saved host-key pin differs from baseline')
    if not config.is_file() or any(line.strip() and not line.lstrip().startswith('#') for line in config.read_text().splitlines()):
        raise RuntimeError('Isolated SSH configuration contains unexpected options')
    print('Baseline integrity: OK. Action:',args.action)
    print('check is read-only; install/restore mount the host read/write and share its PID namespace.')
    print('Only owner-key/drop-in state is managed; no systemctl enable/start/restart requests.')
    print('Installation permits key-based root authentication and retains existing authorized-key search files.')
    print('On installation or final-login failure, the tool will attempt management-based restoration.')
    print('Restore refuses unrelated file/configuration changes; manual recovery can still be necessary.')
    if input('Type '+args.action.upper()+' to proceed: ').strip()!=args.action.upper():print('Cancelled.');return 0
    token=owner.read_token()
    def transaction(action):
        session=AccessSession(args.host,token,work,action)
        owner.save_new(work/('plan-'+session.name+'.json'),{'action':action,'baseline_sha256':hashlib.sha256(original).hexdigest(),'resource':session.name})
        try:
            session.start()
            report=session.run_action({'action':action,'before':baseline['before'],'public_key':public_key})
            owner.save_new(work/(action+'-'+session.name+'.json'),owner.envelope(report))
        finally:
            session.close()
            if baseline_file.read_bytes()!=original:raise RuntimeError('Baseline bytes unexpectedly changed; stop')
        return report,session.cleanup_ok
    def prove_rejection():
        # Restore does not require the private key: offer the public key preserved in the baseline.
        public_base=work/('owner-public-probe-'+uuid.uuid4().hex[:10])
        pub=pathlib.Path(str(public_base)+'.pub')
        try:
            with pub.open('x',encoding='ascii') as f:f.write(public_key+'\n')
            owner.rejection_probe(args.host,public_base,known,config)
        finally:
            if pub.exists():pub.unlink()
    if args.action=='check':
        report,clean=transaction('check')
        print('Baseline state:',report['at_baseline'],'Installed state:',report['at_installed_state'])
        print('Native ssh.service enabled offline:',report['ssh_service_enabled_offline'])
        print('Listener verified:',report['listener_verified'])
        print('Effective settings:',json.dumps(report['settings']))
        return 0 if clean else 2
    if args.action=='restore':
        report,clean=transaction('restore')
        prove_rejection()
        print('RESTORED: managed state matches baseline; owner public key rejected on a fresh connection.')
        print('Close any separately opened SSH sessions yourself. Existing connections are not revoked by this tool.')
        return 0 if clean else 2
    try:
        report,clean=transaction('install')
        print('Verifying fresh root SSH. Enter the LOCAL key passphrase if prompted.',flush=True)
        subprocess.run(owner.ssh_command(args.host,key,known,config)+['test "$(id -u)" = 0 && id'],check=True)
    except (Exception,KeyboardInterrupt) as error:
        print('Installation/verification did not complete. Attempting baseline restoration.',flush=True)
        try:
            rollback,rollback_clean=transaction('restore')
            prove_rejection()
            print('AUTOMATIC RESTORE VERIFIED: baseline files restored and owner key rejected.')
            if not rollback_clean:print('Cleanup warnings remain; inspect named resources.')
        except (Exception,KeyboardInterrupt):
            print('AUTOMATIC RESTORE NOT VERIFIED. Preserve baseline; rerun restore or seek manual recovery.')
        return 1
    print('INSTALLED: fresh root SSH verified. Keep the entire private state directory for restore.')
    print('To connect, use the original key and the saved known_hosts/ssh_config files; see ACCESS_PREVIEW.md.')
    return 0 if clean else 2

if __name__=='__main__':
    try:sys.exit(main())
    except (Exception,KeyboardInterrupt) as error:
        print('STOPPED:',str(error) if isinstance(error,RuntimeError) else type(error).__name__)
        print('Do not assume a failed operation made no changes. Preserve the baseline and inspect cleanup.')
        sys.exit(1)
