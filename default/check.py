# -*- coding:utf-8 -*-

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