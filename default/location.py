# -*- coding:utf-8 -*-

import hashlib

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