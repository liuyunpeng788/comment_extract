import sys
import warnings
import multiprocessing
import sys
from operator import itemgetter

import jieba_fast as jieba
import jieba_fast.analyse as jiebaAnalyse
from jieba_fast.analyse.tfidf import IDFLoader, DEFAULT_IDF
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

from db.db_mysql import loadDictionary

sys.path.append("..")
from config.config import updateConfig, getConfig

dictionary = '../resources/dict.txt'
stop_file = '../resources/stopWord.txt'
data_file = '../resources/data.txt'


'''
从mysql词库表中加载数据到文件
每隔1h重新更新一次
'''
def loadDicDataToFile():
    record = loadDictionary()

    with open(dictionary,'w',encoding='utf8') as f:
        for line in record:
            f.write("\t".join([line[0],str(line[1]),line[2]]) + " \n")

def tfidf_keywords():
    # 00、读取文件,一行就是一个文档，将所有文档输出到一个list中
    corpus = []
    for line in open(data_file, 'r',encoding='utf8').readlines():
        corpus.append(" ".join(jiebaAnalyse.extract_tags(line, topK=50, allowPOS=['n'])))

    # 01、构建词频矩阵，将文本中的词语转换成词频矩阵
    vectorizer = CountVectorizer()
    # a[i][j]:表示j词在第i个文本中的词频
    X = vectorizer.fit_transform(corpus)
    # print(X) # 词频矩阵

    # 02、构建TFIDF权值
    transformer = TfidfTransformer()
    # 计算tfidf值
    tfidf = transformer.fit_transform(X)

    # 03、获取词袋模型中的关键词
    word = vectorizer.get_feature_names()

    # tfidf矩阵
    weight = tfidf.toarray()

    # 打印特征文本
    print(len(word))
    for i in range(len(weight)):
        for j in range(len(word)):
            print(word[j],weight[i][j])

    # 打印权重
    # for i in range(len(weight)):
    #     for j in range(len(word)):
    #         print( weight[i][j])


def  extract_tag():
    ## 分词 ieba_fast
    jieba.load_userdict(dictionary)

    data = []
    jiebaAnalyse.set_stop_words("../resources/stopWord.txt")
    with open(data_file, 'r', encoding='utf8') as f:
        for no,line in enumerate(f):
            data.append(jiebaAnalyse.extract_tags(line, topK=50, allowPOS=['n']))

    print(data)


def getData(topK = 20,withFlag = True,withWeight = False):
    jiebaAnalyse.set_stop_words("../resources/stopWord.txt")
    stopWords = set()
    with open("../resources/stopWord.txt",'r',encoding='utf8') as f:
        for no, word in enumerate(f):
            stopWords.add(word)

    data = []
    with open(data_file, 'r', encoding='utf8') as f:
        for no, line in enumerate(f):
            data.append(line.strip())
            # data.extend(jiebaAnalyse.extract_tags(line, topK=50, allowPOS=['n']))
    # text, weigth = jiebaAnalyse.extract_tags(" ".join(data), topK=20, allowPOS=['n'], withWeight=True)
    # print(text)

    #  test

    allowPOS = frozenset(['n'])
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
        if len(wc.strip()) < 2 or wc.lower() in stopWords:
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

def wordCould():
    from wordcloud import WordCloud
    data = []
    jiebaAnalyse.set_stop_words(stop_words_path=stop_file)
    with open(data_file, 'r', encoding='utf8') as f:
        for no, line in enumerate(f):
            data.append(line.strip())
            # data.extend(jiebaAnalyse.extract_tags(line, topK=50, allowPOS=['n']))
    text = jiebaAnalyse.extract_tags(" ".join(data), topK=20, allowPOS=['n'], withWeight=True)
    # print(text)
    wordcloud = WordCloud(font_path='../resources/simsun.ttf').generate(" ".join(text))

    import matplotlib.pyplot as plt
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.show()


if __name__=='__main__':
    env = 'dev'
    if len(sys.argv) == 2:
        env = sys.argv[1]
    configure = updateConfig('env', 'env_active', env)
    configure = getConfig()

    # 加载词库到默认路径
    # loadDicDataToFile()

    ## extract_tag:
    # extract_tag()

    ## tf-idf
    # tfidf_keywords()

    #cloud
    # wordCould()

    ##get data
    getData()




