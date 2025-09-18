#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2024/7/7 14:06
# @Author : 桐
# @QQ:1041264242
# 注意事项：

import requests
import zipfile
import os
import pandas as pd
import time
from app.core.config import OUTPUT_PATH


def download_zip_file(url, save_path):
    """
    下载ZIP文件
    
    Args:
        url (str): ZIP文件的URL
        save_path (str): 保存路径
    
    Returns:
        bool: 下载是否成功
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        print(f"下载ZIP文件失败: {e}")
        return False


def find_md_files_in_zip(zip_path):
    """
    在ZIP文件中查找MD文件
    
    Args:
        zip_path (str): ZIP文件路径
    
    Returns:
        list: MD文件列表
    """
    md_files = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.md'):
                    md_files.append(file_info.filename)
    except Exception as e:
        print(f"读取ZIP文件失败: {e}")
    
    return md_files


def extract_pdf_name(pdf_path):
    """
    从PDF路径中提取文件名（不含扩展名）
    
    Args:
        pdf_path (str): PDF文件路径
    
    Returns:
        str: 文件名（不含扩展名）
    """
    return os.path.splitext(os.path.basename(pdf_path))[0]


def download_file_mineruapi(url, save_path):
    """
    通过MinerU API下载文件
    
    Args:
        url (str): 文件URL
        save_path (str): 保存路径
    
    Returns:
        bool: 下载是否成功
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"文件下载成功: {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"下载文件时发生网络错误: {e}")
        return False
    except Exception as e:
        print(f"下载文件时发生未知错误: {e}")
        return False


def pdf2md_mineruapi(pdf_path, output_path):
    """
    使用MinerU API将PDF转换为Markdown
    
    Args:
        pdf_path (str): PDF文件路径
        output_path (str): 输出路径
    
    Returns:
        str: 转换后的Markdown文件路径，如果失败返回None
    """
    # 读取Excel文件
    excel_path = os.path.join(OUTPUT_PATH, 'mineruapi.xlsx')
    
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"Excel文件不存在: {excel_path}")
        return None
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return None
    
    # 获取第一行的API信息
    if len(df) == 0:
        print("Excel文件为空")
        return None
    
    api_url = df.iloc[0]['api_url']
    api_key = df.iloc[0]['api_key']
    
    # 上传PDF文件
    upload_url = f"{api_url}/upload"
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': f'Bearer {api_key}'}
            
            response = requests.post(upload_url, files=files, headers=headers)
            response.raise_for_status()
            
            upload_result = response.json()
            file_id = upload_result.get('file_id')
            
            if not file_id:
                print("上传失败，未获取到file_id")
                return None
    
    except Exception as e:
        print(f"上传PDF文件失败: {e}")
        return None
    
    # 开始转换
    convert_url = f"{api_url}/convert"
    convert_data = {
        'file_id': file_id,
        'output_format': 'markdown'
    }
    
    try:
        headers = {'Authorization': f'Bearer {api_key}'}
        response = requests.post(convert_url, json=convert_data, headers=headers)
        response.raise_for_status()
        
        convert_result = response.json()
        task_id = convert_result.get('task_id')
        
        if not task_id:
            print("转换失败，未获取到task_id")
            return None
    
    except Exception as e:
        print(f"开始转换失败: {e}")
        return None
    
    # 轮询转换状态
    status_url = f"{api_url}/status/{task_id}"
    
    while True:
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get(status_url, headers=headers)
            response.raise_for_status()
            
            status_result = response.json()
            status = status_result.get('status')
            
            if status == 'completed':
                download_url = status_result.get('download_url')
                if download_url:
                    # 下载转换后的文件
                    pdf_name = extract_pdf_name(pdf_path)
                    md_file_path = os.path.join(output_path, f"{pdf_name}.md")
                    
                    if download_file_mineruapi(download_url, md_file_path):
                        return md_file_path
                    else:
                        return None
                else:
                    print("转换完成但未获取到下载链接")
                    return None
            
            elif status == 'failed':
                print("转换失败")
                return None
            
            else:
                print(f"转换中，当前状态: {status}")
                time.sleep(5)  # 等待5秒后再次查询
        
        except Exception as e:
            print(f"查询转换状态失败: {e}")
            return None