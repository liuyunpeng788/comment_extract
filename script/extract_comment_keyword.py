import datetime
import multiprocessing
import sys
sys.path.append("..")

from operator import itemgetter
import jieba_fast as jieba
import jieba_fast.analyse as jiebaAnalyse
from flask import *
from gevent.pywsgi import WSGIServer
from jieba_fast.analyse.tfidf import IDFLoader, DEFAULT_IDF
from constant.const import const
from db.db_mongo import getMongoData
from db.db_mysql import saveDataToDb, clearDbData, findAllShopId, findAllMallId
from util.logger import logger

from config.config import updateConfig, getConfig
from datetime import datetime

dictionary = '../resources/dict.txt'
stop_file = '../resources/stopWord.txt'
data_file = '../resources/data.txt'
app = Flask(__name__)

jiebaAnalyse.set_stop_words(stop_file)
stopWords = set()
# 读取文件
def readFile(filename , mode = 'r',encoding = 'utf8'):
    data = []
    with open(filename, mode, encoding= encoding) as f:
        for line in f:
            data.append(line.strip())
        # for no, word in enumerate(f):
        #     data.append(word)
    return data


# 获取结果
def getAnalyseData(data,topK = 50, allowPOS =['n'] , withFlag = True,withWeight = False):
    '''
    获取关注点分词结果
    :param data: 数据集合 ，只包含正面或者负面
    :param topK: 默认获取前多少个
    :param allowPOS: 只选取指定词性的词语
    :param withFlag: 是否返回词性
    :param withWeight: 是否返回权重
    :return: topK 个词汇及其出现的次数
    '''
    if checkDataParam(data) == False:
        return None


    # data = readFile(data_file)
    allowPOS = frozenset(allowPOS)
    words = jieba.posseg.dt.cut(" ".join(data))
    idf_freq, median_idf = IDFLoader(None or DEFAULT_IDF).get_idf()
    freq = {}
    word_count= {}
    for w in words:
        if allowPOS:
            if w.flag not in allowPOS:
                continue
            elif not withFlag:
                w = w.word
        wc = w.word if allowPOS and withFlag else w
        if len(wc.strip()) < 2 or wc.lower() in jiebaAnalyse.default_tfidf.stop_words:
            continue
        freq[w] = freq.get(w, 0.0) + 1.0
        word_count[wc] = word_count.get(wc, 1) + 1
    total = sum(freq.values())
    for k in freq:
        kw = k.word if allowPOS and withFlag else k
        freq[k] *= idf_freq.get(kw, median_idf) / total

    if withWeight:
        tags = sorted(freq.items(), key=itemgetter(1), reverse=True)
    else:
        tags = sorted(freq, key=freq.__getitem__, reverse=True)
    if topK:
        res = []
        for w ,weigth in tags[:topK]:
            if withWeight:
                res.append((w.word, word_count[w.word]))
            else:
                res.append((w,word_count[w]))

        res = sorted(res,key = itemgetter(1),reverse=True)
        return res
    else:
        return tags


def checkDataParam(data):
    '''
    数据参数检测
    :param data: 数据
    :return: 如果符合要求，则返回True,否则，返回 False
    '''
    if isinstance(data, str):
        data = [data]
        return True
    elif isinstance(data, (list, set)):
        if len(data) <= 0:
            logger.error('参数data为空')
            return False
        elif not isinstance(data[0], str):
            logger.error('参数data中元素的类型不对，需要传递一个字符串类型的list')
            return False
        else:
            return True
    else:
        logger.error('参数类型不对，需要传递一个字符串或者字符串类型的list')
        return False

def processMongoData(collection = None,ids = None,date = None):
    '''
    多线程处理mongo数据信息
    :param collection: 表
    :param ids: 对应的ids
    :return: none
    '''
    # key0: 商场id , key2(内层字典的key): neg(负面内容) ,pos（正面的内容）,type（商场/店铺）
    commentMap = getMongoData(collection = collection,ids = ids, date = date)  ## 获取mongodb中的评论数据
    if len(commentMap) == 0:
        logger.info('没有获取到数据,param:{0},{1}'.format(collection,ids))
    else:
        for key, value in commentMap.items():
            for commentType in ['pos','neg']:
                ## 处理好评数据
                if value is None or value.get(commentType) is None:
                    continue
                result = getAnalyseData(value[commentType])
                if result is None:
                    continue
                ## 将缓存中的前50 跟当前的结果相比，如果当前词出现在缓存中，则直接将该词的出现次数相加。
                ## 如果缓存中不存在，则直接缓存当前值。对所有词根据词频进行排序，取前50 缓存，前50保存到数据库
                result = MergeHistroyFromES(key,value["type"],const.NEGATIVE_COMMENT, result)
                if result is not None:
                    saveDataToDb(key, value["type"] , commentType, result)
                result = None

    commentMap = None  ## 将所有的对象都置空，防止出现内存泄漏的情况


def MergeHistroyFromES(subjectId,subjectType,commentType,result):
    '''
    与历史评论数据的结果进行合并操作
    将结果保存到redis中 ，key: 店铺标识/商场标识_评论类型_店铺/商场id
    :param subjectId: 主体商场或者店铺 id
    :param subjectType: 店铺（1） 或者商场（0）
    :param commentType:  好评（0）或者 差评（1）
    :param result: tuple类型列表  0:词 1: 词频 .一共50条记录
    :return: 排名前20的结果
    '''
    from db.db_redis import getKey,putValue
    import json

    if result is None :
        logger.info("词频列表为空，不做任何操作")
        return None

    ### key :  店铺标识/商场标识_评论类型_店铺/商场id
    key = const.REDIS_DIR + const.UNDER_LINE.join([ str(subjectType),str(commentType), str(subjectId) ])
    redisResult = getKey(key)

    if redisResult is None:
        dictFreq = {}
        for word,freq in result:
            dictFreq[word] = freq
        # putValue(key,json.dumps(dict))
    else:
        dictFreq = json.loads(redisResult)
        for word,freq in result:
            if dictFreq.get(word) is None:
                dictFreq[word] += freq
            else:
                dictFreq[word] = freq
    res = sorted(dictFreq.items(),key=lambda item:item[1],reverse= True)
    putValue(key, json.dumps(dict(res[:50]),ensure_ascii=False).encode('utf8'))
    return res[:20]


@app.route("/joycity/commentExtract", methods=['GET','POST'])
def apiInvoke():
    '''
    api 调用该接口，执行评论提取流程
    :return: 成功：true  失败：false
    '''
    # stopWords = set(readFile(stop_file))
    response = {}
    start = datetime.now()
    try:
        if request.method == 'GET':
            strDate = request.args.get('date', None)
        else:
            strDate = request.get_json()['date']

        env = 'dev'
        if len(sys.argv) == 2:
            env = sys.argv[1]
        updateConfig('env', 'env_active', env)
        configure = getConfig()
        clearDbData()
        poolSize = configure.getint('pool', 'poolSize')  ## 线程池大小
        collections = ["Mall_Comment_Info", "Shop_Comment_Info"]  ## mongodb 待分析的表

        ## 每次处理的数量
        batchSize = configure.getint('pool', 'batchSize')
        batchSize = 100 if batchSize is None else batchSize
        shopIds = findAllShopId()
        mallIds = findAllMallId()
        for collection in collections:
            ids = shopIds if collection == 'Shop_Comment_Info' else mallIds
            ## 每次创建 POOL_SIZE 个线程 ，一共创建size/POOL_SIZE 个
            t1 = datetime.now()
            pool = multiprocessing.Pool(processes=poolSize)  # 创建POOL_SIZE个进程
            i = 0
            while i < len(ids):
                logger.info("i = {0} ".format(i))
                if (i + batchSize) >= len(ids):
                    logger.info("最后一批数据，索引范围：{0}-{1}".format(i, len(ids)))
                    subset = ids[i:]
                else:
                    subset = ids[i: i + batchSize]
                # processMongoData(collection,subset, strDate)
                pool.apply_async(processMongoData, args=(collection,subset, strDate,))
                i += batchSize
            #
            pool.close()  ## 关闭进程
            pool.join()  ## 等待所有进程执行完成
            t2 = datetime.now()
            logger.info("处理{0}数据耗时{1}s".format(collection,(t2-t1).seconds))

        end = datetime.now()
        logger.info("spend time:{0}s".format((end - start)))
        response["code"] = 200
        response["msg"] = "执行成功。耗时{0}s".format((end - start).seconds)
    except :
        end = datetime.now()
        logger.error("exception now",exc_info=1)
        response["code"] = 501
        response["msg"] = "程序异常。耗时{0}s".format((end - start).seconds)
    # stopWords = None  ##  清空，防止内存不释放
    return json.dumps(response)

if __name__=='__main__':
    # apiInvoke()
    app.config['JSON_AS_ASCII'] = False
    WSGIServer(('0.0.0.0', 9006), app).serve_forever()












