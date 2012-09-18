# -*- coding:utf-8 -*-

### Tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.gen
### Python
import optparse
import os
import imp
import urllib, urllib2
import json
import traceback
import functools

### Global variables
setting = None
manager = None

class V_ApiBase(tornado.web.RequestHandler):
    def get(self):
        self.post()
    
    def _callback(self, http_response, callback):
        if http_response.code == 200:
            data = http_response.body.split('\r\n\r\n')
            response = json.loads(data[1])
            callback(response)
        else:
            http_response.rethrow()
    
    def api_do_core(self, mode, location, http_client, as_local, callback):
        
        _callback = functools.partial(self._callback, callback=callback)
        
        try:
            if is_local(setting, location):
                ### ローカルで保存/読み込み
                # print 'local :', location
                if mode == 'save' or mode == 'delete':
                    manager.local_save(setting, self, mode)
                    response = [location, True, None]
                elif mode == 'load':
                    value, version = manager.local_load(setting, self)
                    response = [location, True, None, value, version]
                else:
                    raise manager.V_Exception('invalid parameter: mode = %s' % mode)
            else:
                if as_local:
                    if is_direct(setting, location):
                        ### ノードに直接向ける
                        host = location[1]
                    else:
                        ### 違うグループなのでロードバランサに向ける
                        host = location[0]
                else:
                    ### 同じグループ内の他のノードに向ける
                    host = location[1]
                # print 'remote:', location
                if mode == 'save':
                    target_handler = V_ApiSaveRemote
                elif mode == 'load':
                    target_handler = V_ApiLoadRemote
                elif mode == 'delete':
                    target_handler = V_ApiDeleteRemote
                else:
                    raise manager.V_Exception('invalid parameter: mode = %s' % mode)
                url = '%s://%s:%s%s' % (host[0], host[1], host[2], nh_url_mapper[target_handler][0])
                arguments = self.request.arguments
                arguments['v_location'] = json.dumps(location)
                if True:
                    request = tornado.httpclient.HTTPRequest(
                        url,
                        method='POST',
                        connect_timeout=setting.V_TIMEOUT_CONNECT,
                        request_timeout=setting.V_TIMEOUT_REQUEST,
                    )
                    body = urllib.urlencode(arguments, True)
                    http_client.fetch(url, _callback, method='POST', body=body, connect_timeout=setting.V_TIMEOUT_CONNECT, request_timeout=setting.V_TIMEOUT_REQUEST)
                    return
                else:
                    arguments_url_encoded = urllib.urlencode(arguments, True)
                    response_encoded = urllib2.urlopen(url, arguments_url_encoded).read()
                    response = json.loads(response_encoded)
        except:
            if mode == 'save' or mode == 'delete':
                response = [location, False, traceback.format_exc()]
            elif mode == 'load':
                response = [location, False, traceback.format_exc(), None, None]
            else:
                raise manager.V_Exception('invalid parameter: mode = %s' % mode)
        callback(response)
    
    @tornado.web.asynchronous
    @tornado.gen.engine
    def api_do_local(self, mode):
        responses = []
        tasks = []
        
        http_client = tornado.httpclient.AsyncHTTPClient()
        locations = manager.get_locations(setting, self)
        for location in locations:
            task = tornado.gen.Task(self.api_do_core, mode, location, http_client, as_local=True)
            tasks.append(task)
        responses = yield tasks
        
        if mode == 'save' or mode == 'delete':
            flag, all_ok = manager.check_responses_save(setting, responses)
            result = json.dumps([flag, all_ok, responses])
        elif mode == 'load':
            flag, all_ok, value, version = manager.check_responses_load(setting, responses)
            result = json.dumps([flag, all_ok, responses, value, version])
        else:
            raise manager.V_Exception('invalid parameter: mode = %s' % mode)
        
        if all_ok:
            self.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s" % (len(result), result))
        else:
            self.write("HTTP/1.1 500 OK\r\nContent-Length: %d\r\n\r\n%s" % (len(result), result))
        self.finish()
    
    @tornado.web.asynchronous
    @tornado.gen.engine
    def api_do_remote(self, mode):
        http_client = tornado.httpclient.AsyncHTTPClient()
        
        location_temp = json.loads(self.get_argument('v_location'))
        location = (tuple(location_temp[0]), tuple(location_temp[1]))
        response = yield tornado.gen.Task(self.api_do_core, mode, location, http_client, as_local=False)
        result = json.dumps(response)
        self.write("HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n%s" % (len(result), result))
        self.finish()

class V_ApiSave(V_ApiBase):
    def post(self):
        self.api_do_local(mode='save')

class V_ApiSaveRemote(V_ApiBase):
    def post(self):
        self.api_do_remote(mode='save')

class V_ApiLoad(V_ApiBase):
    def post(self):
        self.api_do_local(mode='load')

class V_ApiLoadRemote(V_ApiBase):
    def post(self):
        self.api_do_remote(mode='load')

class V_ApiDelete(V_ApiBase):
    def post(self):
        self.api_do_local(mode='delete')

class V_ApiDeleteRemote(V_ApiBase):
    def post(self):
        self.api_do_remote(mode='delete')

### URL mapper
nh_url_mapper = {
    V_ApiSave        : (r"/v_save", None),
    V_ApiSaveRemote  : (r"/v_save_remote", None),
    V_ApiLoad        : (r"/v_load", None),
    V_ApiLoadRemote  : (r"/v_load_remote", None),
    V_ApiDelete      : (r"/v_delete", None),
    V_ApiDeleteRemote: (r"/v_delete_remote", None),
}

def is_direct(setting, location):
    if tuple(location[0]) == setting.V_TORNADO_SELF[0]:
        return True
    elif location[0][0] is None:
        return True
    else:
        return False

def is_local(setting, location):
    if is_direct(setting, location):
        if tuple(location[1]) == setting.V_TORNADO_SELF[1]:
            return True
        else:
            return False
    else:
        return False

def get_application_data():
    application_data = []
    for item_key, item_value in nh_url_mapper.items():
        if item_value[1] is None:
            application_data.append((item_value[0], item_key))
        else:
            application_data.append((item_value[0], item_key, item_value[1]))
    return application_data

def get_application():
    application = tornado.web.Application(
        get_application_data(),
        debug = setting.V_AUTO_RELOAD,
    )
    return application

def start_server():
    application = get_application()
    server = tornado.httpserver.HTTPServer(application, no_keep_alive=setting.V_NO_KEEP_ALIVE)
    server.bind(setting.V_TORNADO_SELF[1][2])
    server.start(setting.V_N_SERVERS)
    tornado.ioloop.IOLoop.instance().start()

def parse_options():
    parser = optparse.OptionParser()
    parser.add_option(
        "-s",
        "--setting",
        dest    = "setting",
        metavar = "FILENAME",
        help    = "[required] setting file name",
    )
    parser.add_option(
        "-m",
        "--manager",
        dest    = "manager",
        metavar = "FILENAME",
        help    = "[required] manager file name",
    )
    options, args = parser.parse_args()
    
    if options.setting == None or options.manager == None:
        parser.print_help()
        sys.exit(0)
    return options, args

def load_module(module_path):
    path_dir, path_file = os.path.split(module_path)
    if path_dir:
        search_path = [path_dir,]
    else:
        search_path = ['.',]
    fp, path_name, description = imp.find_module(path_file, search_path)
    return imp.load_module(path_file, fp, path_name, description)

def main():
    options, args = parse_options()
    
    ### 設定ファイルの読み込み
    global setting
    setting = load_module(options.setting)
    
    ### マネージャファイルの読み込み
    global manager
    manager = load_module(options.manager)
    
    ### サーバの起動
    start_server()

if __name__ == "__main__":
    main()
