#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2025/8/21 9:58
# @Author : 桐
# @QQ:1041264242
# 注意事项：

import json
import os
import re
import arxiv
import requests
from bs4 import BeautifulSoup
import urllib.parse
from scihub_cn.scihub import SciHub
from app.core.config import OUTPUT_PATH, Proxies
import time
import logging

# 配置日志
logger = logging.getLogger(__name__)


### 下载PDF的保存路径

def check_pdf(file_path):
    """
    检查PDF文件是否能正常打开。

    参数:
    file_path (str): PDF文件路径。

    返回:
    bool: 如果文件能正常打开则返回True，否则返回False。
    """
    # 参数验证：确保file_path是字符串类型且不为空
    if not isinstance(file_path, str) or not file_path:
        logger.warning(f"Invalid file_path parameter: {file_path} (type: {type(file_path)})")
        return False
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            # 读取文件的前5个字节，PDF文件通常以"%PDF-"开头
            # 这里我们读取5个字节是因为"%PDF-"是5个字节（包括百分号）
            header = f.read(5)
            # 检查文件开头是否为"%PDF-"（PDF文件的魔数）
            if header != b'%PDF-':
                # 如果不是PDF开头，则抛出异常
                logger.warning(f"File does not start with PDF header: {file_path}")
                return False
            # 如果需要，可以在这里添加更多的检查逻辑
            return True
    except Exception as e:
        logger.error(f"Error opening PDF file {file_path}: {e}")
        return False


def sanitize_folder_name(folder_name):
    """
    清理文件夹名称，移除非法字符
    
    Args:
        folder_name (str): 原始文件夹名称
    
    Returns:
        str: 清理后的文件夹名称
    """
    # 定义需要替换的违规字符集
    illegal_chars = r'<>:"/\\|\?\*'
    # 使用正则表达式替换违规字符为下划线 _
    sanitized_name = re.sub(f'[{illegal_chars}]', '_', folder_name)
    return sanitized_name


def search_google_scholar(doi):
    """
    在Google Scholar中搜索DOI对应的PDF链接
    
    Args:
        doi (str): 文献的DOI
    
    Returns:
        str: PDF下载链接，如果未找到返回None
    """
    # Google Scholar的搜索URL
    search_url = f"https://scholar.google.com/scholar?q={urllib.parse.quote(doi)}"

    # 模拟请求
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(search_url, headers=headers, proxies=Proxies)

    soup = BeautifulSoup(response.text, 'html.parser')

    # 查找包含[PDF]文本的链接
    pdf_links = []
    for link in soup.find_all('a'):
        if '[PDF]' in link.get_text():
            pdf_links.append(link['href'])

    # 输出找到的链接
    for pdf_link in pdf_links:
        print(pdf_link)
        return pdf_link


def download_pdf_from_google(pdf_url, title, output_path):
    """
    从Google Scholar下载PDF文件
    
    Args:
        pdf_url (str): PDF文件URL
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    save_path = os.path.join(output_path, f"{title}.pdf")

    # 发送HTTP GET请求来获取PDF文件
    try:
        response = requests.get(pdf_url, proxies=Proxies)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    except Exception as e:
        logger.error(f"从Google下载PDF失败: {e}")
        return None


def download_pdf_from_scihub(doi, output_path):
    """
    从Sci-Hub下载PDF文件
    
    Args:
        doi (str): 文献的DOI
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    try:
        sh = SciHub()
        result = sh.download(doi, path=output_path)
        return result
    except Exception as e:
        logger.error(f"从Sci-Hub下载PDF失败: {e}")
        return None


def download_pdf_from_unpaywall(doi, title, output_path, email="z1041264242@gmail.com"):
    """
    从Unpaywall下载PDF文件
    
    Args:
        doi (str): 文献的DOI
        title (str): 文献标题
        output_path (str): 输出路径
        email (str): 邮箱地址
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    
    try:
        response = requests.get(url, proxies=Proxies)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('is_oa') and data.get('best_oa_location'):
            pdf_url = data['best_oa_location']['url_for_pdf']
            if pdf_url:
                return download_pdf_from_google(pdf_url, title, output_path)
        
        return None
    except Exception as e:
        logger.error(f"从Unpaywall下载PDF失败: {e}")
        return None


def download_pdf_from_arxiv(doi, title, output_path):
    """
    从arXiv下载PDF文件
    
    Args:
        doi (str): 文献的DOI或arXiv ID
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    try:
        # 如果DOI包含arxiv，提取arXiv ID
        if 'arxiv' in doi.lower():
            arxiv_id = doi.split('/')[-1]
        else:
            # 尝试通过标题搜索arXiv
            search = arxiv.Search(
                query=title,
                max_results=1,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = list(search.results())
            if not results:
                return None
            
            arxiv_id = results[0].entry_id.split('/')[-1]
        
        # 下载PDF
        paper = next(arxiv.Search(id_list=[arxiv_id]).results())
        save_path = os.path.join(output_path, f"{title}.pdf")
        paper.download_pdf(dirpath=output_path, filename=f"{title}.pdf")
        
        return save_path
    except Exception as e:
        logger.error(f"从arXiv下载PDF失败: {e}")
        return None


def download_pdf_from_crossref(doi, title, output_path):
    """
    从CrossRef获取PDF链接并下载
    
    Args:
        doi (str): 文献的DOI
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    url = f"https://api.crossref.org/works/{doi}"
    
    try:
        response = requests.get(url, proxies=Proxies)
        response.raise_for_status()
        
        data = response.json()
        work = data['message']
        
        # 查找PDF链接
        if 'link' in work:
            for link in work['link']:
                if link.get('content-type') == 'application/pdf':
                    return download_pdf_from_google(link['URL'], title, output_path)
        
        return None
    except Exception as e:
        logger.error(f"从CrossRef下载PDF失败: {e}")
        return None


def getdown_pdf_google_url(doi, title, output_path):
    """
    通过Google搜索获取PDF下载链接
    
    Args:
        doi (str): 文献的DOI
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    pdf_url = search_google_scholar(doi)
    if pdf_url:
        return download_pdf_from_google(pdf_url, title, output_path)
    return None


def download_pdf_from_Giiisp(doi, title, output_path):
    """
    从Giiisp下载PDF文件
    
    Args:
        doi (str): 文献的DOI
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    # Giiisp API配置
    api_config = {
        'base_url': 'https://api.giiisp.com',
        'endpoints': {
            'search': '/search',
            'download': '/download'
        }
    }
    
    # 请求头配置
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    try:
        # 搜索文献
        search_url = api_config['base_url'] + api_config['endpoints']['search']
        search_params = {'doi': doi}
        
        response = requests.get(search_url, params=search_params, headers=headers, proxies=Proxies)
        response.raise_for_status()
        
        search_data = response.json()
        
        if search_data.get('success') and search_data.get('pdf_url'):
            pdf_url = search_data['pdf_url']
            return download_pdf_from_google(pdf_url, title, output_path)
        
        return None
    except Exception as e:
        logger.error(f"从Giiisp下载PDF失败: {e}")
        return None


def download_pdf(doi, title, output_path):
    """
    尝试从多个源下载PDF文件
    
    Args:
        doi (str): 文献的DOI
        title (str): 文献标题
        output_path (str): 输出路径
    
    Returns:
        str: 下载的文件路径，如果失败返回None
    """
    # 清理标题，用作文件名
    clean_title = sanitize_folder_name(title)
    
    # 尝试多个下载源
    download_methods = [
        ('Unpaywall', lambda: download_pdf_from_unpaywall(doi, clean_title, output_path)),
        ('arXiv', lambda: download_pdf_from_arxiv(doi, clean_title, output_path)),
        ('Google Scholar', lambda: getdown_pdf_google_url(doi, clean_title, output_path)),
        ('Sci-Hub', lambda: download_pdf_from_scihub(doi, output_path)),
        ('CrossRef', lambda: download_pdf_from_crossref(doi, clean_title, output_path)),
        ('Giiisp', lambda: download_pdf_from_Giiisp(doi, clean_title, output_path))
    ]
    
    for method_name, method_func in download_methods:
        try:
            logger.info(f"尝试从{method_name}下载PDF...")
            result = method_func()
            if result and os.path.exists(result) and check_pdf(result):
                logger.info(f"成功从{method_name}下载PDF: {result}")
                return result
        except Exception as e:
            logger.error(f"从{method_name}下载失败: {e}")
            continue
    
    logger.warning(f"所有下载方法都失败了，DOI: {doi}")
    return None


def download_all_pdfs(dois, title, topic, user_id, task):
    """
    批量下载PDF文件
    
    Args:
        dois (list): DOI列表
        title (list): 标题列表
        topic (str): 主题
        user_id (str): 用户ID
        task: 任务对象
    
    Returns:
        list: 下载成功的文件路径列表
    """
    if isinstance(dois, str):
        dois = [dois]
    if isinstance(title, str):
        title = [title]
    
    # 创建输出目录
    topic_path = os.path.join(OUTPUT_PATH, sanitize_folder_name(topic))
    os.makedirs(topic_path, exist_ok=True)
    
    downloaded_files = []
    
    for i, doi in enumerate(dois):
        try:
            paper_title = title[i] if i < len(title) else f"paper_{i+1}"
            logger.info(f"开始下载第{i+1}篇文献: {paper_title}")
            
            result = download_pdf(doi, paper_title, topic_path)
            if result:
                downloaded_files.append(result)
                logger.info(f"下载成功: {result}")
            else:
                logger.warning(f"下载失败: {paper_title} (DOI: {doi})")
        
        except Exception as e:
            logger.error(f"下载过程中发生错误: {e}")
            continue
    
    logger.info(f"批量下载完成，成功下载{len(downloaded_files)}个文件")
    return downloaded_files


if __name__ == "__main__":
    print(os.environ)
    dois = '10.1088/1674-4527/19/9/133'
    download_all_pdfs(dois=dois, title='Pulsar Candidates Classification with Deep Convolutional Neural Networks',
                      topic='pulsar candidate classification')