'''
处理与mysql相关的信息
'''
#coding:utf-8
import sys
sys.path.append("..")
from config.config import getConfig
import redis

config = getConfig()
pool = redis.ConnectionPool(host=config['redis']['host'], port=config.getint('redis','port'),password = config['redis']['password'],db=config.getint('redis','database'), decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379

def getRedisConn(key):
    r = redis.Redis(connection_pool = pool)
    return r.get(key)

def getKey(key):
    r = redis.Redis(connection_pool = pool)
    result = r.get(key)

    return result

def putValue(key,value):
    r = redis.Redis(connection_pool = pool)
    r.set(key,value)

def exists(key):
    '''
    返回包含key的记录数
    :param key: redis的键
    :return:
    '''
    r = redis.Redis(connection_pool=pool)
    return r.exists(key)

if __name__=='__main__':
    import json
    result = getKey("1_1_2039")
    print(json.dumps(result))


