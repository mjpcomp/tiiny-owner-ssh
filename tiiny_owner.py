"""Experimental Tiiny owner SSH backup/install/restore. Use on authorized devices only."""
import argparse
import base64
import hashlib
import ipaddress
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from tiiny_auth_check import read_token, NoRedirect
from tiiny_host_state import desired

MCP = """import json,subprocess,sys
for line in sys.stdin:
 q=json.loads(line)
 if 'id' not in q: continue
 method=q.get('method')
 if method=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'owner-state','version':'1'}}
 elif method=='tools/list': result={'tools':[{'name':'run','description':'Owner state operation','inputSchema':{'type':'object','properties':{'code':{'type':'string'}},'required':['code']}}]}
 elif method=='tools/call':
  p=subprocess.run(['python3','-c',q['params']['arguments']['code']],capture_output=True,text=True,timeout=40)
  result={'content':[{'type':'text','text':p.stdout+p.stderr}],'isError':p.returncode!=0}
 else: result={}
 print(json.dumps({'jsonrpc':'2.0','id':q['id'],'result':result}),flush=True)
"""

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

def save_new(path,data):
    with path.open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2)
        f.flush()
        os.fsync(f.fileno())

def envelope(data):
    return {'sha256':hashlib.sha256(canonical(data)).hexdigest(),'data':data}

def load_backup(path):
    item=json.loads(path.read_text(encoding='utf-8'))
    if item['sha256']!=hashlib.sha256(canonical(item['data'])).hexdigest():
        raise RuntimeError('Backup integrity check failed')
    if item['data'].get('schema')!=1:
        raise RuntimeError('Unsupported backup schema')
    return item['data']

class Session:
    def __init__(self,host,token,work):
        self.host,self.token,self.work=host,token,work
        self.name='owner-state-'+uuid.uuid4().hex[:10]
        self.mcp=None
        self.service=False
        self.cleanup_ok=True
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        save_new(work/('resources-'+self.name+'.json'),{'host':host,'name':self.name})
    def connector(self,path='',method='GET',body=None):
        req=urllib.request.Request('http://'+self.host+'/v1/mcp/servers'+path,
            data=None if body is None else json.dumps(body).encode(),method=method,
            headers={'Host':'connector.api.tiiny','Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        try:
            with self.opener.open(req,timeout=45) as r: return json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as error:
            raise RuntimeError('Connector HTTP '+str(error.code)) from None
    def remote(self,code):
        r=self.connector('/'+self.mcp+'/tools/run/call','POST',{'arguments':{'code':code}})
        text=''.join(x.get('text','') for x in r.get('content',[]))
        if r.get('isError'): raise RuntimeError('Remote bridge operation failed')
        return text.strip()
    def device(self,port,path,method='GET',body=None):
        code='import urllib.request\n'
        code+='r=urllib.request.Request(%r,data=%r,headers=%r,method=%r)\n'%(
            'http://127.0.0.1:'+str(port)+path,None if body is None else json.dumps(body).encode(),
            {'Content-Type':'application/json','Authorization':'Bearer '+self.token},method)
        code+="o=urllib.request.build_opener(urllib.request.ProxyHandler({}))\nprint(o.open(r,timeout=25).read().decode() or '{}')"
        return json.loads(self.remote(code))
    def start(self):
        print('Creating temporary management connector:',self.name,flush=True)
        r=self.connector('','POST',{'description':'Temporary owner SSH backup and restore helper','name':self.name,'transport':'stdio','command':'python3',
            'arguments':['-u','-c',MCP],'runEnvironment':'tiiny','enabled':True,'timeout_seconds':45})
        self.mcp=str(r['id'])
        deployment=self.device(5555,'/api/web/compose/current')
        images=deployment['data']['service_images']
        image=next(x['image'] for x in images if x['service']=='connectors')
        self.image=image
        self.deployment_hash=hashlib.sha256(canonical(sorted(images,key=lambda x:x['service']))).hexdigest()
        save_new(self.work/('connector-'+self.name+'.json'),{'id':self.mcp,'name':self.name})
    def run(self,payload):
        source=pathlib.Path(__file__).with_name('tiiny_host_state.py').read_text(encoding='utf-8')
        setup='import json,pathlib,time\n'+source+'\n'
        setup+='\ntry:\n result=dispatch('+repr(payload)+')\nexcept Exception as error:\n result={"ok":False,"error":str(error)}\n'
        setup+='pathlib.Path('+repr('/report/'+self.name+'.json')+').write_text(json.dumps(result))\ntime.sleep(180)\n'
        compose={'services':{'setup':{'image':self.image,'pull_policy':'never','user':'0:0',
            'entrypoint':['python3','-c',setup],'restart':'no','pid':'host','network_mode':'none',
            'volumes':['/:/host:'+('ro' if payload['action']=='backup' else 'rw'),'aibox_connectors_config:/report']}},
            'volumes':{'aibox_connectors_config':{'external':True}}}
        self.service=True
        self.device(8880,'/api/services','POST',{'id':self.name,'name':self.name,'compose_file':json.dumps(compose)})
        try: self.device(8880,'/api/services/'+self.name+'/start','POST')
        except Exception: print('Checking report after incomplete start request.',flush=True)
        for attempt in range(20):
            result=json.loads(self.remote("import pathlib;p=pathlib.Path('/data/connectors/%s.json');print(p.read_text() if p.exists() else '{}')"%self.name))
            if result:
                if not result.get('ok'): raise RuntimeError(result.get('error','Host operation failed'))
                return result
            time.sleep(2)
        raise RuntimeError('No host operation report; inspect device before retrying')
    def close(self):
        print('Cleaning temporary resources:',self.name,flush=True)
        if self.mcp:
            if self.service:
                try: self.device(8880,'/api/services/'+self.name,'DELETE')
                except Exception: self.cleanup_ok=False
            try: self.remote("import pathlib;pathlib.Path('/data/connectors/%s.json').unlink(missing_ok=True)"%self.name)
            except Exception: self.cleanup_ok=False
            try: self.connector('/'+self.mcp,'DELETE')
            except Exception: self.cleanup_ok=False
            try:
                servers=self.connector()
                if not isinstance(servers,list) or any(str(x.get('id'))==self.mcp or x.get('name')==self.name for x in servers):
                    self.cleanup_ok=False
            except Exception: self.cleanup_ok=False
        else: self.cleanup_ok=False
        print('Cleanup:', 'requests completed; service absence not independently verified' if self.cleanup_ok else 'WARNING: incomplete or unverified; inspect resource '+self.name)
        save_new(self.work/('cleanup-'+self.name+'.json'),{'name':self.name,'requests_completed':self.cleanup_ok,'service_absence_verified':False})

def ssh_command(host,key,known,config,probe=False):
    args=[shutil.which('ssh') or 'ssh','-F',str(config),'-i',str(key)+('.pub' if probe else ''),'-p','3588',
        '-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','PreferredAuthentications=publickey',
        '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no',
        '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(known),'-o','ConnectTimeout=10',
        '-o','BatchMode='+('yes' if probe else 'no')]
    if probe: args+=['-vv']
    return args+['root@'+host]

def rejection_probe(host,key,known,config):
    print('Testing whether the server accepts this owner public key (no signing/passphrase needed).',flush=True)
    p=subprocess.run(ssh_command(host,key,known,config,True)+['true'],capture_output=True,text=True,timeout=25)
    fingerprint='SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(pathlib.Path(str(key)+'.pub').read_text().split()[1])).digest()).decode().rstrip('=')
    log=p.stderr
    if p.returncode==0 or 'Server accepts key:' in log:
        raise RuntimeError('Owner key is accepted by SSH; expected rejection')
    if 'Permission denied' not in log or not any('Offering public key:' in line and fingerprint in line for line in log.splitlines()):
        raise RuntimeError('Could not prove public-key rejection; SSH diagnostics deliberately not saved')
    print('Owner public key was offered and authentication was rejected.',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['backup','install','restore'])
    parser.add_argument('host',type=lambda v:str(ipaddress.IPv4Address(v)))
    parser.add_argument('--state-dir',required=True,type=pathlib.Path)
    parser.add_argument('--key',type=pathlib.Path,default=pathlib.Path.home()/'.ssh/tiiny_owner_ed25519')
    args=parser.parse_args()
    work=args.state_dir.expanduser().resolve()
    # Keep sensitive runtime state outside the source checkout.
    source=pathlib.Path(__file__).resolve().parent
    if work==source or source in work.parents: raise RuntimeError('State directory must be outside the source folder')
    work.mkdir(parents=True,exist_ok=True)
    key=args.key.expanduser().resolve()
    if not key.is_file() or not pathlib.Path(str(key)+'.pub').is_file(): raise RuntimeError('Owner key pair is missing')
    if not shutil.which('ssh'): raise RuntimeError('OpenSSH client missing')
    public_key=pathlib.Path(str(key)+'.pub').read_text(encoding='utf-8-sig').strip()
    backup_file=work/'baseline.json'
    backup=None
    if args.action=='backup':
        if backup_file.exists(): raise RuntimeError('Baseline already exists; refusing to overwrite it')
    else:
        backup=load_backup(backup_file)
        if backup['host']!=args.host or backup['public_key']!=public_key: raise RuntimeError('Target or owner key differs from backup')
        desired(backup['before'],public_key)
    print('Action:',args.action,'Target:',args.host)
    print('Temporary privileged management resources will be created. HTTP is unencrypted.')
    print('Backup reads host files only; install/restore change host SSH files.')
    if input('Type '+args.action.upper()+' to proceed: ').strip()!=args.action.upper():
        print('Cancelled.'); return 0
    session=Session(args.host,read_token(),work)
    try:
        session.start()
        if backup and session.deployment_hash!=backup['deployment_hash']:
            raise RuntimeError('Deployment images changed; refusing blind install/restore')
        if args.action=='backup':
            result=session.run({'action':'backup'})
            before=result['state']
            desired(before,public_key)
            host_key=before['identity']['ssh_host_key'].split()
            if len(host_key)<2 or host_key[0]!='ssh-ed25519': raise RuntimeError('Unexpected host key')
            known=work/'known_hosts'
            config=work/'ssh_config'
            if known.exists() or config.exists(): raise RuntimeError('Local trust files already exist; use a fresh state directory')
            known.write_text('[%s]:3588 %s\n'%(args.host,' '.join(host_key[:2])),encoding='ascii')
            config.write_text('# Isolated owner client configuration\n',encoding='ascii')
            rejection_probe(args.host,key,known,config)
            data={'schema':1,'host':args.host,'public_key':public_key,'before':before,
                'deployment_hash':session.deployment_hash,'firmware_check':'OS-release hash and deployment image references only; not an authoritative firmware version'}
            save_new(backup_file,envelope(data))
            if load_backup(backup_file)!=data: raise RuntimeError('Local backup read-back failed')
            print('SUCCESS: immutable baseline saved and read back. Host SSH files unchanged.')
            print('Keep this state directory private and backed up. Firmware identity check is limited.')
        else:
            known=work/'known_hosts';config=work/'ssh_config'
            if not known.is_file() or not config.is_file(): raise RuntimeError('Saved SSH trust files missing')
            # Trust must still match the original backup, not a replaced known-hosts file.
            expected='[%s]:3588 %s\n'%(args.host,' '.join(backup['before']['identity']['ssh_host_key'].split()[:2]))
            if known.read_text()!=expected or config.read_text()!='# Isolated owner client configuration\n':
                raise RuntimeError('Local trust files changed')
            result=session.run({'action':args.action,'before':backup['before'],'public_key':public_key})
            save_new(work/(args.action+'-'+uuid.uuid4().hex[:10]+'.json'),envelope(result))
            if args.action=='install':
                print('Enter LOCAL private-key passphrase if prompted. No device-password authentication.',flush=True)
                subprocess.run(ssh_command(args.host,key,known,config)+['test "$(id -u)" = 0 && id'],check=True)
                print('SUCCESS: root SSH verified. Restore is available using the saved baseline.')
            else:
                rejection_probe(args.host,key,known,config)
                print('SUCCESS: original managed state restored; owner public key rejected on a fresh connection.')
    finally:
        session.close()
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (Exception,KeyboardInterrupt) as error:
        # Never dump bridge code, response bodies, or tokens through an automatic traceback.
        message=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('STOPPED:',message,file=sys.stderr)
        print('Do not assume a failed operation made no changes. Preserve the state directory.',file=sys.stderr)
        sys.exit(1)
