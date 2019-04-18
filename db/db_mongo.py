'''
处理与mongodb相关的信息
'''
#coding:utf-8

# coding:utf-8
import sys

from config.config import getConfig
from constant.const import const
from db.db_redis import exists

sys.path.append("..")
from util.logger import logger
from datetime import datetime,timedelta
import pymongo

dtFormat = '%Y-%m-%d %H:%M:%S'
dateFormat = '%Y-%m-%d'


def parseDateParam(date=None):
    '''
    处理日期参数，获取数据的起始日期。兼容字符串类型和时间类型的参数
    :param date: 时间参数
    :return: 查询的起始时间
    '''
    if date is None or date.strip() == '':
        return datetime.strptime(datetime.now().strftime(dateFormat),dateFormat)
    elif isinstance(date, str) and date.find("-") > 0:
        # 字符串类型的时间格式
        if len(date.strip()) == 10:
            format = dateFormat
        elif date.find(" ") > 0 and len(date.strip()) == 19:
            format = dtFormat
        else:
            logger.error('字符串格式的时间参数不正确,参数:{0}'.format(date))
            return None

        return datetime.strptime(date, format)
    elif isinstance(date, datetime):
        return date
    else:
        logger.error('时间格式参数不正确，参数：{0}'.format(date) )
        return None

def getMongoConn():
    '''
    获取mongodb client 的连接
    :return: client
    '''
    configure = getConfig()
    host = configure['mongodb']['host']
    username = configure['mongodb']['username']
    password = configure['mongodb']['password']
    database = configure['mongodb']['database']
    port = configure.getint('mongodb', 'port')
    client = pymongo.MongoClient(host= host ,port = port,tz_aware = True,maxPoolSize= 10,maxIdleTimeMS = 20000,connectTimeoutMS=20000)
    return client[database]


def generateQuery(subjectIdField, subjectType, starttime, ids):
    '''
    生成mongodb 查询需要的query条件
    :param subjectIdField: 主体查询的相关字段
    :param subjectType:  主体（商场/店铺） 内容
    :param starttime: 起始时间
    :param ids: id 集合
    :return: mongodb 查询条件
    '''
    ## 如果redis 中存在这个商场或店铺的好评/差评数据，则增量处理。否则，全量处理
    # key: 店铺标识 / 商场标识_评论类型_店铺 / 商场id
    query = {}
    key = const.REDIS_DIR + const.UNDER_LINE.join([str(subjectType), "?", "*"])
    try:
        num = exists(key)
    except:
        num = 0
        logger.error("redis 判断key:{0}是否存在出错".format(key),exc_info = 1)
    if num > 0:
        # 已经有数据存在，则增量处理
        query = {"createTime": {"$ge": starttime }}
    else:
        ## 没有数据存在，则全量处理 , 默认处理时间为后1天
        starttime = starttime + timedelta(days=1)
        query = {"createTime": {"$lt": starttime}}

    ## 支持批量查询多个商场/或者店铺的id, 防止一次性查询过多数据，导致程序奔溃。
    if ids is not None and isinstance(ids, (list, set)):
        query[subjectIdField] = {"$in": ids}
    return query


def getMongoData(collection = None, date = None ,subjectIdField= None, ids = None):
    '''
    获取指定collection 的数据.可以一次性获取所有商场/店铺的当天（或指定时间内）的数据
    为了防止数据量太大，也可以一次性的获取小批量数据
    :param collection mongodb的表
    :param subjectIdField 主体字段id
    :param date: 日期
    :param ids list 或者set 类型，表示店铺或者商场的id 集合
    :return: 查询结果,字典类型  key0: 商场id , key2(内层字典的key): neg(负面内容) ,pos（正面的内容）,type（商场/店铺）
    '''
    if collection is None :
        logger.error('参数不正确，没有指定要查询的表')
        return None
    starttime = parseDateParam(date)
    if starttime is None:
        return None

    ## 执行查询
    conn = getMongoConn()

    if collection == 'Mall_Comment_Info':
        subjectIdField = "mallId" if subjectIdField is None else subjectIdField
        subjectType = const.MALL_COMMENT
    else :
        subjectIdField = "shopId" if subjectIdField is None else subjectIdField
        subjectType = const.SHOP_COMMENT

    ## 生成mongodb需要查询的query 参数
    query = generateQuery(subjectIdField,subjectType,starttime,ids)

    logger.info('相关的查询条件为空,param: {0},{1},{2}，{3}'.format(subjectIdField,subjectType,starttime,ids))

    result = conn[collection].find(query,{subjectIdField,"commentLevel","content"})
    commentMap = {}
    for res in result:
        if res.get(subjectIdField) is not None:
            subjectId = res.get(subjectIdField)
            if res.get('content') is not None:
                if res.get('commentLevel') < const.NEGATIVE_SCORE_LEVEL:
                    if commentMap.get(subjectId) is not None and commentMap.get(subjectId).get('neg') is not None:
                        commentMap.get(subjectId)["neg"].append(res.get('content'))
                    else:
                        content = {}
                        content["neg"] = [res.get('content')]
                        content["type"] = subjectType
                        commentMap[subjectId] = content

                elif res.get('commentLevel') >= const.POSITIVE_SCORE_LEVEL:
                    if commentMap.get(subjectId) is not None and commentMap.get(subjectId).get('pos') is not None:
                        commentMap.get(subjectId)["pos"].append(res.get('content'))
                    else:
                        content = {}
                        content["pos"] = [res.get('content')]
                        content["type"] = subjectType
                        commentMap[subjectId] = content

    return commentMap



if  __name__ == '__main__':
    logger.info("类型不正确，{0}".format(1))
    date = None
    getMongoData(collection='Mall_Comment_Info', date=None)