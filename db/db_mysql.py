'''
处理与mysql相关的信息
'''
#coding:utf-8
import sys

sys.path.append("..")

import pymysql


from config.config import getConfig
from util.logger import logger

'''
获取数据库连接
'''
conn = None
def getMysqlConnect():
    '''
    获取mysql 的连接信息
    :return: 与mysql 的连接
    '''
  
    try:
        configure = getConfig()
        host = configure['mysql']['host']
        username = configure['mysql']['username']
        password = configure['mysql']['password']
        database = configure['mysql']['database']
        port = configure.getint('mysql','port')
        charset = configure['mysql']['charset']
        # connect_timeout = configure['mysql'].getint('connect_timeout') or 100

        conn = pymysql.connect(host=host, user=username, passwd=password, db=database, port=port, charset=charset ,autocommit=False,cursorclass=pymysql.cursors.Cursor)
    except  :
        logger.error('connect mysql failure', exc_info=1)
    return conn


def loadDictionary():
    ''''
    获取所有的本地词库数据
    @:return : 聚类后的文章列表
    '''
    keywords = []
    try:
        with getMysqlConnect() as conn:
            sql = 'SELECT word,freq,tag  FROM keyword_dic'
            conn.execute(sql)
            result = conn.fetchall()

            for record in result:
                keywords.append(list(record))
    except Exception as e:
        logger.error("get keyword data error", exc_info=1)
    return keywords

def clearDbData():
    '''
    清除所有的关注点数据
    :return: None
    '''
    with getMysqlConnect() as conn:
        sql = "truncate table t_consumer_comment_focus "
        conn.execute(sql)
        logger.info("成功清除t_consumer_comment_focus表中的所有记录")

def saveDataToDb(subjectId, subjectType,commentType,result):
    import datetime
    if result is None:
        logger.info('结果为空')
    else:
        try:
            with getMysqlConnect() as conn:
                data = []
                date = datetime.datetime.now()
                sql = 'INSERT INTO t_consumer_comment_focus(id,subject_id,subject_type,comment_type,keyword,num,create_time,update_time) VALUES(null,%s,%s,%s,%s,%s,%s,%s)'
                for keyword, num in result:
                    data.append((int(subjectId),subjectType,commentType,keyword,num,date,date))
                # conn.execute(sql)
                num = conn.executemany(sql,data)
                logger.info("插入{0}条记录".format(num))

        except Exception as e:
            logger.error("get keyword data error", exc_info=1)

def findAllShopId():
    '''
    查找所有店铺的id
    :return: 店铺id 的set
    '''
    try:
        with getMysqlConnect() as conn:
            sql = 'select distinct shop_id from t_shop_info where shop_status = 0'
            conn.execute(sql)
            result = conn.fetchall()
            logger.info("查找到{0}条有效的店铺id记录".format(len(result)))
            return [key[0] for key in result]

    except :
        logger.error("get shopId data failure", exc_info=1)
        return None

def findAllMallId():
    '''
    查找所有商场的id
    :return: 商场id 的set
    '''
    try:
        with getMysqlConnect() as conn:
            sql = 'select distinct mall_id from t_mall_info where business_status = 0'
            conn.execute(sql)
            result = conn.fetchall()
            logger.info("查找到{0}条的商场id记录".format(len(result)))
            return [key[0] for key in result]
    except :
        logger.error("get mallid data failure", exc_info=1)
    return None



if __name__ == '__main__':
   res =  findAllMallId()
   print(res)


