# -*- coding:utf-8 -*-

### 全体のTornadoクラスタ構成
V_TORNADO_MAP = {
    ('http', 'localhost', 9000): [
            ('http', 'localhost', 9001),
            ('http', 'localhost', 9002),
        ],
    ('http', 'localhost', 9100): [
            ('http', 'localhost', 9101),
            ('http', 'localhost', 9102),
        ],
    ('http', 'localhost', 9200): [
            ('http', 'localhost', 9201),
            ('http', 'localhost', 9202),
        ],
}
### 全体のTornadoクラスタ内で自分に該当するもの
# V_TORNADO_SELF = (('http', 'localhost', 9000), ('http', 'localhost', 9000))
# V_TORNADO_SELF = (('http', 'localhost', 9000), ('http', 'localhost', 9001))
# V_TORNADO_SELF = (('http', 'localhost', 9000), ('http', 'localhost', 9002))
# V_TORNADO_SELF = (('http', 'localhost', 9100), ('http', 'localhost', 9100))
# V_TORNADO_SELF = (('http', 'localhost', 9100), ('http', 'localhost', 9101))
# V_TORNADO_SELF = (('http', 'localhost', 9100), ('http', 'localhost', 9102))
# V_TORNADO_SELF = (('http', 'localhost', 9200), ('http', 'localhost', 9200))
# V_TORNADO_SELF = (('http', 'localhost', 9200), ('http', 'localhost', 9201))
# V_TORNADO_SELF = (('http', 'localhost', 9200), ('http', 'localhost', 9202))
### Tornadoサーバのデータ格納のルートディレクトリ
# V_DATA_ROOT = '/disk1/9000/data'
# V_DATA_ROOT = '/disk1/9001/data'
# V_DATA_ROOT = '/disk1/9002/data'
# V_DATA_ROOT = '/disk1/9100/data'
# V_DATA_ROOT = '/disk1/9101/data'
# V_DATA_ROOT = '/disk1/9102/data'
# V_DATA_ROOT = '/disk1/9200/data'
# V_DATA_ROOT = '/disk1/9201/data'
# V_DATA_ROOT = '/disk1/9202/data'
### Tornadoがデバックモードで動作するかどうか
V_AUTO_RELOAD = False
### TornadoがKEEP_ALIVEを使わずに接続を扱うかどうか
V_NO_KEEP_ALIVE = False
### Tornadoが起動させる子プロセスの最大数。一般的にはCPUコア数の2～3倍弱程度。
### ただし、V_AUTO_RELOAD == True なら 1 以外はエラーとなる。
V_N_SERVERS = 6
### Tornadoがデータ転送を行う時の最大接続待ち時間（秒）
V_TIMEOUT_CONNECT = 1.0
### Tornadoがデータ転送を行う時の全体の最大接続時間（秒）
V_TIMEOUT_REQUEST = 3.0
