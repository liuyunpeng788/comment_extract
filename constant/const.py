
class const():
    '''
    常量信息
    '''
    POSITIVE_SCORE_LEVEL = 4 ##好评的参照值
    NEGATIVE_SCORE_LEVEL = 3 ##差评的参照值
    MALL_COMMENT = 0 ## 商场评论
    SHOP_COMMENT = 1 ## 店铺评论
    POSITIVE_COMMENT = 0 ## 好评
    NEGATIVE_COMMENT = 1 ## 差评

    ## redis
    REDIS_DIR = 'JOYCITY:REDIS:COMMENT:'
    UNDER_LINE = '_'  ## 下划线，redis 中，key 的连接符

