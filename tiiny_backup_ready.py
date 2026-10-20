"""Backup-only compatibility runner for the tested Tiiny application image.
Requires the original preview files in the same folder. Does not edit them.
"""
import hashlib
import json
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import tiiny_owner as owner

IMAGE='registry.tiiny.cloud/wa-odysseus-searxng:v0.1'

def backup_compose(body):
    if not isinstance(body,dict) or not isinstance(body.get('compose_file'),str):
        raise RuntimeError('Unexpected service creation body')
    result=dict(body)
    compose=json.loads(result['compose_file'])
    services=compose.get('services')
    if not isinstance(services,dict) or set(services)!={'setup'}:
        raise RuntimeError('Unexpected backup service layout')
    setup=services['setup']
    if setup.get('image')!=IMAGE or setup.get('pull_policy')!='never':
        raise RuntimeError('Backup image/pull policy mismatch')
    if setup.get('network_mode')!='none' or setup.get('volumes')!=['/:/host:ro','aibox_connectors_config:/report']:
        raise RuntimeError('Backup host mount must be read-only; unexpected mounts refused')
    # Backup has no reason to inspect host processes or reload sshd.
    setup.pop('pid',None)
    setup['read_only']=True
    result['compose_file']=json.dumps(compose)
    return result

class CompatibleSession(owner.Session):
    def start(self):
        self._stream=None;self._thread=None;self._stop=threading.Event()
        print('Creating temporary connector:',self.name,flush=True)
        created=self.connector('','POST',{'name':self.name,
            'description':'Temporary owner SSH baseline backup; no SSH configuration changes',
            'transport':'stdio','command':'python3','arguments':['-u','-c',owner.MCP],
            'runEnvironment':'tiiny','enabled':True,'timeout_seconds':45})
        self.mcp=str(created['id'])
        owner.save_new(self.work/('connector-'+self.name+'.json'),{'id':self.mcp,'name':self.name})
        self.image=IMAGE
        self.deployment_hash=hashlib.sha256(owner.canonical({'bootstrap_image_reference':IMAGE})).hexdigest()
        print('Using capability-tested image; skipping the unsupported port-5555 discovery route.',flush=True)
    def request(self,path,method='GET',body=None,stream=False):
        req=urllib.request.Request('http://'+self.host+path,method=method,
            data=None if body is None else json.dumps(body).encode(),headers={
            'Host':'agent-services.api.tiiny','Authorization':'Bearer '+self.token,
            'Content-Type':'application/json','Accept':'application/json, text/event-stream' if stream else 'application/json'})
        try:response=self.opener.open(req,timeout=15 if stream else 45)
        except urllib.error.HTTPError as error:
            raise RuntimeError('Services API HTTP '+str(error.code)+' for '+method) from None
        print('Services API:',method,'HTTP',response.status,flush=True)
        if stream:return response
        with response:
            raw=response.read(8*1024*1024+1)
            if len(raw)>8*1024*1024:raise RuntimeError('Service response exceeds size limit')
            return json.loads(raw or b'{}')
    def device(self,port,path,method='GET',body=None):
        if port!=8880:raise RuntimeError('Unsupported device-local API call refused by compatibility runner')
        if method=='POST' and path=='/api/services':
            body=backup_compose(body)
            print('Creating backup service: host mount read-only; no host PID namespace.',flush=True)
        if method=='POST' and path.endswith('/start'):
            self._stream=self.request(path+'/stream',method,body,True)
            def consume():
                try:
                    while not self._stop.is_set():
                        line=self._stream.readline(4096)
                        if not line:break
                except Exception:
                    pass  # Stream contents/errors are not a trusted operation result.
                finally:
                    try:self._stream.close()
                    except Exception:pass
            self._thread=threading.Thread(target=consume,daemon=True)
            self._thread.start()
            print('Startup stream opened; checking backup report without waiting for stream completion.',flush=True)
            return {}
        return self.request(path,method,body)
    def run(self,payload):
        if payload.get('action')!='backup':raise RuntimeError('This runner refuses install and restore')
        result=super().run(payload)
        info=result.get('ssh_unit_info')
        if info is not None:
            print('SSH UNIT BASELINE:',json.dumps(info,indent=2),flush=True)
            owner.save_new(self.work/('ssh-units-'+self.name+'.json'),info)
        return result
    def close(self):
        print('Cleaning backup resources:',self.name,flush=True)
        failures=[]
        deleted=not self.service
        if self.service:
            try:
                self.device(8880,'/api/services/'+self.name,'DELETE');deleted=True
            except Exception:failures.append('service deletion')
            try:
                listed=self.device(8880,'/api/services')
                absent=isinstance(listed,list) and not any(isinstance(x,dict) and (str(x.get('id'))==self.name or x.get('name')==self.name) for x in listed)
                print('Temporary service absent from management list:',absent,flush=True)
                if not absent:failures.append('service absence verification')
            except Exception:failures.append('service-list check')
        if hasattr(self,'_stop'):self._stop.set()
        if getattr(self,'_thread',None):
            self._thread.join(timeout=2)
            if self._thread.is_alive():print('Startup reader still closing; it is a daemon thread and does not block exit.',flush=True)
        if self.mcp:
            if deleted:
                try:
                    output=self.remote("import json,pathlib;p=pathlib.Path('/data/connectors/%s.json');p.unlink(missing_ok=True);print(json.dumps({'report_absent':not p.exists()}))"%self.name)
                    absent=json.loads(output).get('report_absent') is True
                    print('Temporary report absent:',absent,flush=True)
                    if not absent:failures.append('report absence verification')
                except Exception:failures.append('report cleanup')
            try:self.connector('/'+self.mcp,'DELETE')
            except Exception:failures.append('connector deletion')
            try:
                listed=self.connector()
                absent=isinstance(listed,list) and not any(isinstance(x,dict) and (str(x.get('id'))==self.mcp or x.get('name')==self.name) for x in listed)
                print('Temporary connector absence verified:',absent,flush=True)
                if not absent:failures.append('connector absence verification')
            except Exception:failures.append('connector-list check')
        else:failures.append('no connector ID; inspect named resource if creation was ambiguous')
        self.cleanup_ok=not failures
        owner.save_new(self.work/('cleanup-'+self.name+'.json'),{'name':self.name,'verified':self.cleanup_ok,'warnings':failures})
        if failures:print('CLEANUP WARNING:', '; '.join(failures), 'Resource:',self.name,flush=True)
        else:print('Cleanup checks passed.',flush=True)

original_save=owner.save_new

def main():
    if len(sys.argv)<2 or sys.argv[1]!='backup':
        print('Only backup is supported: python tiiny_backup_ready.py backup DEVICE_IP --state-dir DIRECTORY')
        return 2
    owner.Session=CompatibleSession
    # The original main compares the saved backup to its in-memory data. Update that data in place.
    def save(path,data):
        if path.name=='baseline.json' and isinstance(data,dict) and isinstance(data.get('data'),dict):
            payload=data['data']
            payload['firmware_check']='OS-release, main SSH configuration, and device identity hashes only. Bootstrap image reference is NOT a firmware/deployment-version check.'
            payload['bootstrap_image_reference']=IMAGE
            payload['discovery_method']='Explicit capability-tested image and services virtual host; no port-5555 discovery.'
            data=owner.envelope(payload)
        original_save(path,data)
    owner.save_new=save
    print('Backup-only runner. Install/restore are refused. Existing baseline overwrite protection remains active.')
    return owner.main()

if __name__=='__main__':
    try:sys.exit(main())
    except (Exception,KeyboardInterrupt) as error:
        print('STOPPED:',str(error) if isinstance(error,RuntimeError) else type(error).__name__)
        print('Preserve the state directory. No SSH changes were requested; inspect cleanup output.')
        sys.exit(1)
