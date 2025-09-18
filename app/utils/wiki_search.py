#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2024/7/7 14:06
# @Author : 桐
# @QQ:1041264242
# 注意事项：

import json
import re
import time
import requests
from app.core.config import Proxies


# 用于获取Wikipedia上的简介内容
def remove_html_tags(text):
    """
    移除HTML标签
    
    Args:
        text (str): 包含HTML标签的文本
    
    Returns:
        str: 移除HTML标签后的文本
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def get_description(text):
    """
    从搜索结果中获取描述信息
    
    Args:
        text (dict): 搜索结果字典
    
    Returns:
        list: 描述信息列表
    """
    descriptions = []

    try:
        for item in text['search']:
            descriptions.append(item['description'])
        # print(descriptions)
    except:
        print("description is null !")

    # print("get_description ok!")
    return descriptions


def get_wikipedia_intro(entity_data, lang):
    """
    获取Wikipedia简介
    
    Args:
        entity_data (dict): 实体数据
        lang (str): 语言代码
    
    Returns:
        str: Wikipedia简介内容
    """
    wikipedia_intro = ''
    if 'sitelinks' in entity_data and f'{lang}wiki' in entity_data['sitelinks']:
        wikipedia_title = entity_data['sitelinks'][f'{lang}wiki']['title']
        wikipedia_url = 'https://en.wikipedia.org/w/api.php' if lang == 'en' else 'https://zh.wikipedia.org/w/api.php'
        wikipedia_params = {
            'action': 'query',
            'format': 'json',
            'titles': wikipedia_title,
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'converttitles': True
        }
        while True:
            try:
                wikipedia_response = requests.get(wikipedia_url, wikipedia_params, proxies=Proxies)
                break
            except requests.exceptions.RequestException as e:
                print("获取Wikipedia文章内容错误，等待60s后重试...")
                time.sleep(60)

        wikipedia_data = wikipedia_response.json()
        page_id = next(iter(wikipedia_data['query']['pages']))
        wikipedia_intro = wikipedia_data['query']['pages'][page_id]['extract']
        wikipedia_intro = remove_html_tags(wikipedia_intro)
    return wikipedia_intro


def search(query, language='en', limit=3):
    """
    在Wikidata中搜索实体
    
    Args:
        query (str): 搜索查询
        language (str): 语言代码，默认为'en'
        limit (int): 返回结果数量限制，默认为3
    
    Returns:
        dict: 搜索结果JSON数据
    """
    url = "https://www.wikidata.org/w/api.php"

    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': {query},  # 搜索文本
        'language': {language},  # 查询语言（英文）
        'type': 'item',
        'limit': {limit}  # 返回最大数目
    }

    # 访问
    get = requests.get(url=url, params=params, proxies=Proxies)
    # 转为json数据
    re_json = get.json()

    return re_json


def search_detailed(id, language='en'):
    """
    获取实体的详细信息
    
    Args:
        id (str): 实体ID
        language (str): 语言代码，默认为'en'
    
    Returns:
        dict: 实体详细信息JSON数据
    """
    url = "https://www.wikidata.org/w/api.php"

    params = {
        'ids': {id},  # 实体id,可多个，比如'Q123|Q456'
        'action': 'wbgetentities',
        'format': 'json',
        'language': {language},
    }

    # 访问
    get = requests.get(url=url, params=params, proxies=Proxies)
    # 转为json数据
    re_json = get.json()

    print(json.dumps(re_json["entities"][id]["descriptions"]["en"], ensure_ascii=False, indent=2))

    return re_json