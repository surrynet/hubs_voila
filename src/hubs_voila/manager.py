import os
import sys
import getopt
import json
import signal
from subprocess import run, getoutput
from threading import Thread

from hubs_voila.proxy import Proxy

def usage():
    print('''hubs_voila [ACTION] [OPTIONS] [NOTEBOOK_FILENAME]

Voila 서버 실행과 configurable-http-proxy의 사용을 단순화한 운영툴이다.

Actions
=======
status
    현재 서비스 중인 proxy 상태
create
    Voila 서버와 proxy 경로를 생성한다.
remove
    Voila 서버와 proxy 경로를 제거한다.

Options
=======
-p, --port <Int>
    Voila 서버의 포트
-s, --suffix <String>
    JupyterHub에서 Voila 서버의 접근 경로 /voila/<String>
    브라우저 접근시 "http://JUPYTERHUB_HOST:PORT/voila/<String>"
-b, --back <String(light|dark)>
    바탕 테마로 기본값은 'light'이다.
-e, --enable_nbextensions
    nbextensions 사용유무
    default: False
-t, --template
    템플릿
    gridstack
    vuetify-default
-h, --help
    도움말

Example
-------
    hubs_voila create -s moon -p 8866 moon.ipynb
    hubs_voila remove -s moon
    hubs_voila status
    ''')

def voila_run(suffix, port, source_code, theme, template, enable_nbextensions):
    cmd = ['voila',
         '--no-browser',
         '--back=' + theme,
         '--port=' + str(port),
         '--enable_nbextensions=' + str(enable_nbextensions),
         '--server_url=/voila/' + suffix,
         '--base_url=/voila/' + suffix + '/',
        source_code 
        ] 
    if template is not None:
        cmd.extend(['--template=' + template])
        if template == 'gridstack':
            cmd.extend([
                '--VoilaConfiguration.resources={"gridstack": {"show_handles": True}}'])
    run(cmd)
    
   
def main():
    target = None
    source_code = None
    port = None
    suffix = None
    theme = 'light'
    template = None
    enable_nbextensions = False
    help = False
    action = 'status'

    try:
        jupyterhub_user = os.environ['JUPYTERHUB_USER']

        if len(sys.argv) > 1 and sys.argv[1]:
            action = sys.argv[1]
            if action in ('-h', '--help'):
                help = True
            elif action not in ('create', 'remove', 'status'):
                raise getopt.GetoptError('ACTION: ' + action)
        else:
            raise getopt.GetoptError('OPTIONS')
            
 
        opts, args = getopt.getopt(sys.argv[2:], 'p:s:b:t:eh', ['port=', 'suffix=', 'theme=', 'template=', 'enable_nbextensions', 'help'])
        for o, a in opts:
            if o in ('-p', '--port'):
                port = a
            elif o in ('-s', '--suffix'):
                suffix = a
            elif o in ('-b', '--back'):
                theme = a
            elif o in ('-t', '--template'):
                template = a
            elif o in ('-e', '--enable_nbextensions'):
                enable_nbextensions = True
            elif o in ('-h', '--help'):
                help = True
            else:
                assert 'Unhandled options'

        if help:
            usage()
            sys.exit(0)
            
        proxy = Proxy()
        method = getattr(proxy, action)
        
        def handler(signum, frame):
            proxy.remove(suffix)
        
        signal.signal(
            signal.SIGINT,
            handler
        )
        if action == 'create':
            if port is None or suffix is None:
                raise getopt.GetoptError('port or suffix is None')
            target = 'http://jupyter-' + jupyterhub_user + ':' + port
            if os.path.isfile(args[0]):
                source_code = args[0]
            else:
                raise getopt.GetoptError('{} file is not exist'.format(args[0]))
            method(suffix, target)
            ret = json.dumps(proxy.status())
            if ret != '{}':
                print(ret)
            t = Thread(target=voila_run, args=(suffix, port, source_code, theme, template, enable_nbextensions))
            t.start()
            t.join()
        elif action == 'remove':
            if suffix is None:
                raise getopt.GetoptError('suffix is None')
            pslist = getoutput("ps -elf | grep hubs_voila | grep '\(--suffix\|-s\)\([= ]\)\?{} ' | grep -v grep | grep -v remove".format(suffix)).split('\n')
            if len(pslist) > 0 and pslist[0] != '':
                for ps in pslist:
                    item = ps.split()
                    pgid = item[3]
                    os.killpg(int(pgid), signal.SIGINT)
                    method(suffix)
                    print('Stop: ' + ' '.join(item[14:]))
        else:
            method()
            ret = json.dumps(proxy.status())
            if ret != '{}':
                print(ret)
            
    except Exception as e:
        proxy.remove(suffix)
        raise e
    
    sys.exit(0)
