#!/usr/bin/python3
#coding:utf-8
import configparser
import os
import sys
sys.path.append("..")

from util.logger import logger

resourcesPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"resources")  ## 工程路径

'''
获取正确的环境配置文件
'''
def getConfig():
    config_file = os.path.normpath(os.path.join(resourcesPath,"app.config"))
    config = configparser.ConfigParser()
    config.read(config_file)  # 此处是utf-8

    env_active = config.get('env','env_active')
    if env_active is None:
        return config
    config_file = os.path.normpath(os.path.join(resourcesPath,"app-" + env_active + ".config"))
    config = configparser.ConfigParser()
    config.read(config_file)  # 此处是utf-8
    return config

'''
更新配置文件中节点的值
nodeName : 节点名称
value: 更新后的值
'''
def updateConfig(nodeName,value):
    if nodeName is None or str(nodeName).strip() == '':
        logger.info("nodeName is None or nodeName is empty")
        return
    else:
        config_file = os.path.normpath(os.path.join(resourcesPath, "app.config"))
        config = configparser.ConfigParser()
        config.read(config_file)  # 此处是utf-8
        oldValue = config[nodeName]
        config[nodeName] = value
        logger.info("update app.config node: " + nodeName + "from " + str(oldValue) + " to " + str(value))


'''
更新配置文件中某节点下的属性值
section: 节点名称
attrName : 属性名称
value: 更新后的值
'''


def updateConfig(section,attrName, value):
    if section is None or str(attrName).strip() == '':
        logger.info("section is None or nodeName is empty")
        return
    else:
        config_file = os.path.normpath(os.path.join(resourcesPath, "app.config"))
        config = configparser.ConfigParser()
        config.read(config_file)  # 此处是utf-8
        oldValue = config[section][attrName]
        config.set(section,attrName,value)
        with open(config_file, 'w') as fw:  # 循环写入
            config.write(fw)
        logger.info("update app.config [: " + section + "]["+ attrName +"] from " + str(oldValue) + " to " + str(value))


if __name__ == '__main__':
    getConfig()
