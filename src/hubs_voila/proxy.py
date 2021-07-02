import requests
import json

class Proxy(object):
    '''
    hubs의 Configurable-HTTP-Proxy 서버의 사용자 API
    '''

    url = 'http://proxy:8001/api/routes'
    headers = {
        'Authorization': 'token HubsConfigProxy'
    }
    path_prefix = '/voila'
    data = None
    
    def status(self):
        '''
        Routes에서 '/voila' prefix를 갖는 path 조회 
        '''
        ret = {}
        res = requests.get(self.url, headers=self.headers)
        for k, v in res.json().items():
            if k.startswith(self.path_prefix):
                ret[k] = v
        return ret
    
    def remove(self, path):
        '''
        Routes에서 '/voila' prefix를 갖는 path 삭제
        '''
        url = self.url + self.path_prefix + '/' + path
        res = requests.delete(url, headers=self.headers)
        return res
    
    def create(self, path, target):
        '''
        Routes에 '/voila' prefix를 갖는 path를 추가
        '''
        target_path = self.path_prefix + '/' + path
        url = self.url + target_path
        data = {'target': target}
        res = requests.post(url, headers=self.headers, data=json.dumps(data))
        return res
