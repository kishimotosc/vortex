# -*- coding:utf-8 -*-

import hashlib
import os
import cPickle as pickle
import json
import fcntl
import time

def check_responses_save(setting, responses):
    n_ok = 0
    for response in responses:
        if response[1] is True:
            n_ok += 1
    n_responses = len(responses)
    flag = n_ok > n_responses / 2
    all_ok = n_ok == n_responses
    return flag, all_ok

def check_responses_load(setting, responses):
    ### 有効なバージョン一覧の作成
    version_list = []
    version_dict = {}
    for response in responses:
        if response[1] is True:
            version_list.append(response[4])
            version_dict[response[4]] = response[3]
    if version_list == []:
        return False, False, None, None
    
    ### 一貫性チェック
    n_responses = len(responses)
    version_keys = version_dict.keys()
    version_keys.sort(reverse=True)
    count_list   = []
    for version_key in version_keys:
        count_list.append(version_list.count(version_key))
    count_max = max(count_list)
    if count_max > n_responses / 2:
        flag = True
        version = version_keys[count_list.index(count_max)]
        value   = version_dict[version]
    else:
        flag = False
    all_ok = count_max == n_responses
    
    return flag, all_ok, value, version

def function_set(data, parameter):
    flag    = True
    value   = None
    message = ''
    
    [column, value,] = parameter
    data[column] = value
    return flag, message, value

def function_get(data, parameter):
    flag    = True
    value   = None
    message = ''
    
    [column,] = parameter
    value = data[column]
    return flag, message, value

functions = {
    'set'   : function_set,
    'get'   : function_get,
}

class V_Exception(Exception):
    pass

class V_ExceptionVersion(V_Exception):
    pass

class V_ExceptionDoesNotExist(V_Exception):
    pass

def get_locations(setting, request_handler):
    ### data_keyから保存先ホスト情報を得る
    ### (ロードバランサのホスト情報, ノードのホスト情報) のリストを返す
    locations = []
    
    ### ハッシュ値方式
    data_key   = request_handler.get_argument('v_key')
    hashed_value = int(hashlib.md5(data_key).hexdigest(), 16)
    for (host_load_balancer, hosts_node) in setting.V_TORNADO_MAP.items():
        n_hosts = len(hosts_node)
        host_node = hosts_node[hashed_value % n_hosts]
        locations.append((host_load_balancer, host_node))
    
    return locations

def _get_lock(fo, request_handler):
    system_limit = float(request_handler.get_argument('v_limit')) # sec
    system_sleep = float(request_handler.get_argument('v_sleep')) # sec
    
    start = time.time()
    while True:
        try:
            if system_limit < 0:
                ### ロックを取得できるまで待つ
                fcntl.flock(fo.fileno(), fcntl.LOCK_EX)
                return True, ''
            else:
                ### ロックを取得できなければ処理が戻ってIOErrorが発生する
                fcntl.flock(fo.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
                return True, ''
        except IOError:
            if time.time() - start < system_limit:
                time.sleep(system_sleep)
                continue
            else:
                ### 例外送出
                message = 'failed to lock'
                return False, message

def _release_lock(fo):
    fcntl.flock(fo.fileno(), fcntl.LOCK_UN)

def _get_file_directory(setting, request_handler):
    user      = request_handler.get_argument('v_user')
    workspace = request_handler.get_argument('v_workspace') # DB
    document  = request_handler.get_argument('v_document')  # table
    
    return os.sep.join([setting.V_DATA_ROOT, user, workspace, document])

def _get_file_path(setting, request_handler):
    key = request_handler.get_argument('v_key')
    
    file_directory = _get_file_directory(setting, request_handler)
    return os.sep.join([file_directory, key])

def _do_function(request_handler, data):
    v_function  = request_handler.get_argument('v_function')
    v_parameter = json.loads(request_handler.get_argument('v_parameter'))
    
    flag, message, value = functions[v_function](data, v_parameter)
    if flag:
        return value
    else:
        raise V_Exception(message)

def local_load(setting, request_handler):
    ### 保存先パスの作成
    file_path = _get_file_path(setting, request_handler)
    ### 既にファイルがあるかチェック
    if os.path.exists(file_path):
        ### オープン
        fo = open(file_path, 'r+')
        ### ロック
        flag, message = _get_lock(fo, request_handler)
        if not flag:
            _release_lock(fo)
            fo.close()
            raise V_Exception(message)
        ### データ読み込み
        data = pickle.load(fo)
        ### 削除状態かどうかチェック
        if data['_#active'] == False:
            message = 'deleted'
            raise V_ExceptionDoesNotExist(message)
    else:
        message = 'does not exist'
        raise V_ExceptionDoesNotExist(message)
    
    ### 関数の実行
    value = _do_function(request_handler, data)
    
    ### ロック解除
    _release_lock(fo)
    fo.close()
    
    return value, data['_#version']

def local_save(setting, request_handler, mode):
    ### 保存先パスの作成
    file_path = _get_file_path(setting, request_handler)
    ### 既にファイルがあるかチェック
    if os.path.exists(file_path):
        ### オープン
        fo = open(file_path, 'r+')
        ### ロック
        flag, message = _get_lock(fo, request_handler)
        if not flag:
            _release_lock(fo)
            fo.close()
            raise V_Exception(message)
        ### データ読み込み
        data = pickle.load(fo)
        fo.seek(0)
    else:
        ### まだデータが作られていないので削除モード時なら例外送出
        if mode == 'delete':
            message = 'does not exist'
            raise V_ExceptionDoesNotExist(message)
        ### ディレクトリがあるかチェック
        directory_path = _get_file_directory(setting, request_handler)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        ### 新規ファイル
        fo = open(file_path, 'w')
        ### ロック
        flag, message = _get_lock(fo, request_handler)
        if not flag:
            _release_lock(fo)
            fo.close()
            raise V_Exception(message)
        ### 初期データ
        data = {
            '_#active' : True,
            '_#version': 0,
        }
    
    ### データ更新
    v_version   = int(request_handler.get_argument('v_version'))
    if mode == 'save':
        if v_version > data['_#version'] or data['_#active'] == False:
            ### 関数の実行
            value = _do_function(request_handler, data)
            data['_#active'] = True
        else:
            message = '%s -> %s' % (data['_#version'], v_version)
            raise V_ExceptionVersion(message)
    elif mode == 'delete':
        if data['_#active'] == False:
            ### 2重削除は例外送出
            message = 'deleted'
            raise V_ExceptionDoesNotExist(message)
        else:
            if v_version > data['_#version']:
                ### データ削除
                for name in data.keys():
                    if not name.startswith('_#'):
                        del data[name]
                ### 削除マーク付与
                data['_#active'] = False
            else:
                message = '%s -> %s' % (data['_#version'], v_version)
                raise V_ExceptionVersion(message)
    else:
        message = 'invalid parameter: mode = %s' % mode
        raise V_Exception(message)
    
    ### バージョンの更新
    data['_#version'] = v_version
    ### ディスクへの同期
    pickle.dump(data, fo)
    fo.flush()
    os.fsync(fo.fileno())
    ### ロック解除
    _release_lock(fo)
    fo.close()
