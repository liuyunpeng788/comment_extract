'''
商场/店铺评论
'''
import pytz
# import tzlocal

## 用不上，废弃
class CommentInfoPo:

    # NOTE: pytz.reference.LocalTimezone() would produce wrong result here

    ## You could use `tzlocal` module to get local timezone on Unix and Win32
    # from tzlocal import get_localzone # $ pip install tzlocal

    # # get local timezone
    # local_tz = get_localzone()

    def utc_to_local(self,utc_dt):
        local_tz = pytz.timezone('Asia/Shanghai')  # use your local timezone name here
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)  # .normalize might be unnecessary


    def __init__(self,subjectId,subjectType, commentLevel=None,content=None,commentTime=None):
       self.subjectId = subjectId #商场/店铺id
       self.commentType = subjectType ## 0 表示商场，1表示店铺
       self.commentLevel = commentLevel #评论评分/评星
       self.content = content #评论内容
       self.commentTime = self.utc_to_local(commentTime) #评论时间








