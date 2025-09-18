#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2025/8/19 16:08
# @Author : 桐
# @QQ:1041264242
# 注意事项：
import os
import re

from app.core.prompt import get_related_keyword_prompt, paper_compression_prompt, extract_entity_prompt, \
    extract_tec_entities_prompt, review_mechanism_prompt
from app.utils.llm_api import call_with_deepseek, call_with_deepseek_jsonout, call_with_qwenmax
from app.utils.arxiv_api import search_paper
from app.utils.scholar_download import download_all_pdfs
from app.utils.pdf_to_md import pdf2md_mineruapi
from app.utils.wiki_search import get_description, search
from app.core.config import OUTPUT_PATH, graph
import ast


def SearchKeyWordScore(Keywords):
    """
    计算关键词得分
    
    Args:
        Keywords (list): 关键词列表，每个元素包含entity和importance_score
    
    Returns:
        list: 按综合得分排序的关键词列表
    """
    print(f"\033[1;32m | INFO     | calculate Keyword score... \033[0m")

    for index, keyword in enumerate(Keywords):
        entity = keyword['entity']

        # 定义Cypher查询语句
        query = f"""
        MATCH (n:Words)
        WHERE n.other CONTAINS '\'{entity}\'' OR n.name = '{entity}'
        RETURN n.count,n
        ORDER BY n.count DESC
        LIMIT 1
        """

        # 执行查询并获取结果
        nodes = graph.run(query).data()

        if len(nodes) != 0:
            Keywords[index]['count'] = nodes[0]['n.count']
        else:
            Keywords[index]['count'] = 0

    # 计算最小和最大count值
    min_count = min(item['count'] for item in Keywords)
    max_count = max(item['count'] for item in Keywords)

    # 权重分配
    weight_importance = 0.4
    weight_count = 0.6

    # 计算综合得分
    for item in Keywords:
        # 避免除零错误：当所有count值相同时，给予相同的归一化分数
        if max_count == min_count:
            normalized_count = 0.5  # 默认归一化分数
        else:
            normalized_count = (item['count'] - min_count) / (max_count - min_count)
        
        composite_score = (item['importance_score'] * weight_importance) + (normalized_count * weight_count)
        item['composite_score'] = composite_score

        # 排序并输出结果（可选）
    sorted_data = sorted(Keywords, key=lambda x: x['composite_score'], reverse=True)

    print(f"\033[1;32m | INFO     | calculate Keyword score:OK!\n{sorted_data} \033[0m")

    return sorted_data


def get_related_keyword(Keyword):
    """
    获取相关关键词
    
    Args:
        Keyword (str): 输入关键词
    
    Returns:
        list: 相关关键词列表
    """
    print(f"\033[1;32m | INFO     | geting related keyword... \033[0m")
    user_prompt = get_related_keyword_prompt(Keyword=Keyword)
    result = call_with_deepseek(system_prompt="You are a helpful assistant.", question=user_prompt)

    print(f"\033[1;32m | INFO     | The related keyword is :{result} \033[0m")

    print(f"\033[1;32m | INFO     | geting related keyword:OK! \033[0m")

    return ast.literal_eval(result)


def remove_number_prefix(paragraph):
    """
    移除段落中句子开头的数字前缀
    
    Args:
        paragraph (str): 输入段落
    
    Returns:
        str: 处理后的段落
    """
    # 定义一个正则表达式模式，用于匹配句子开头的数字和随后的句点空格
    pattern = r'^\d+\. |(?<=\n)\d+\. '
    # 利用re.sub函数，将匹配到的部分替换为空字符串，以此移除它
    modified_paragraph = re.sub(pattern, '', paragraph, flags=re.MULTILINE)
    return modified_paragraph


def read_markdown_file(file_path):
    """
    读取Markdown文件内容
    
    Args:
        file_path (str): Markdown文件路径
    
    Returns:
        str: 文件内容，如果读取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        return None


def extract_hypothesis(file, split_section="Hypothesis"):
    """
    从文件中提取假设部分
    
    Args:
        file (str): 文件路径或内容
        split_section (str): 分割标识符
    
    Returns:
        str: 提取的假设内容
    """
    if os.path.isfile(file):
        content = read_markdown_file(file)
    else:
        content = file
    
    if not content:
        return None
    
    # 查找假设部分
    sections = content.split(f"## {split_section}")
    if len(sections) > 1:
        hypothesis_section = sections[1].split("##")[0].strip()
        return hypothesis_section
    
    return None


def paper_compression(doi, title, topic, user_id, task):
    """
    论文压缩处理
    
    Args:
        doi (str): 论文DOI
        title (str): 论文标题
        topic (str): 主题
        user_id (str): 用户ID
        task: 任务对象
    
    Returns:
        str: 压缩后的内容路径
    """
    print(f"\033[1;32m | INFO     | paper compression... \033[0m")
    
    # 下载PDF
    pdf_files = download_all_pdfs([doi], [title], topic, user_id, task)
    if not pdf_files:
        print("PDF下载失败")
        return None
    
    # 转换为Markdown
    topic_path = os.path.join(OUTPUT_PATH, topic)
    md_file = pdf2md_mineruapi(pdf_files[0], topic_path)
    if not md_file:
        print("PDF转Markdown失败")
        return None
    
    # 读取Markdown内容
    content = read_markdown_file(md_file)
    if not content:
        print("读取Markdown文件失败")
        return None
    
    # 使用LLM压缩内容
    system_prompt = "You are a helpful assistant for academic paper compression."
    user_prompt = paper_compression_prompt(content=content)
    
    compressed_content = call_with_deepseek(system_prompt=system_prompt, question=user_prompt)
    
    # 保存压缩后的内容
    compressed_file = os.path.join(topic_path, f"{title}_compressed.md")
    with open(compressed_file, 'w', encoding='utf-8') as f:
        f.write(compressed_content)
    
    print(f"\033[1;32m | INFO     | paper compression:OK! \033[0m")
    return compressed_file


def search_releated_paper(topic, max_paper_num=5, compression=True, user_id="", task=None):
    """
    搜索相关论文
    
    Args:
        topic (str): 搜索主题
        max_paper_num (int): 最大论文数量
        compression (bool): 是否压缩
        user_id (str): 用户ID
        task: 任务对象
    
    Returns:
        list: 搜索到的论文信息列表
    """
    print(f"\033[1;32m | INFO     | search related paper... \033[0m")
    
    # 搜索论文
    papers = search_paper(topic, max_paper_num)
    
    if not papers:
        print("未找到相关论文")
        return []
    
    processed_papers = []
    
    for paper in papers:
        try:
            doi = paper.get('doi', '')
            title = paper.get('title', '')
            
            if compression and doi and title:
                # 压缩论文
                compressed_file = paper_compression(doi, title, topic, user_id, task)
                if compressed_file:
                    paper['compressed_file'] = compressed_file
            
            processed_papers.append(paper)
        
        except Exception as e:
            print(f"处理论文时发生错误: {e}")
            continue
    
    print(f"\033[1;32m | INFO     | search related paper:OK! \033[0m")
    return processed_papers


def extract_message(file, split_section):
    """
    从文件中提取指定部分的消息
    
    Args:
        file (str): 文件路径
        split_section (str): 分割标识符
    
    Returns:
        str: 提取的消息内容
    """
    content = read_markdown_file(file)
    if not content:
        return None
    
    sections = content.split(f"## {split_section}")
    if len(sections) > 1:
        message_section = sections[1].split("##")[0].strip()
        return message_section
    
    return None


def extract_technical_entities(file, split_section):
    """
    提取技术实体
    
    Args:
        file (str): 文件路径
        split_section (str): 分割标识符
    
    Returns:
        list: 技术实体列表
    """
    message = extract_message(file, split_section)
    if not message:
        return []
    
    system_prompt = "You are a helpful assistant for extracting technical entities."
    user_prompt = extract_tec_entities_prompt(message=message)
    
    result = call_with_deepseek_jsonout(system_prompt=system_prompt, question=user_prompt)
    
    try:
        entities = ast.literal_eval(result)
        return entities
    except Exception as e:
        print(f"解析技术实体时发生错误: {e}")
        return []


def extract_message_review(file_path, split_section):
    """
    提取消息并进行审查
    
    Args:
        file_path (str): 文件路径
        split_section (str): 分割标识符
    
    Returns:
        dict: 审查结果
    """
    message = extract_message(file_path, split_section)
    if not message:
        return None
    
    # 提取实体
    system_prompt = "You are a helpful assistant for entity extraction."
    user_prompt = extract_entity_prompt(message=message)
    
    entities_result = call_with_deepseek_jsonout(system_prompt=system_prompt, question=user_prompt)
    
    try:
        entities = ast.literal_eval(entities_result)
    except Exception as e:
        print(f"解析实体时发生错误: {e}")
        entities = []
    
    # 计算关键词得分
    if entities:
        scored_keywords = SearchKeyWordScore(entities)
    else:
        scored_keywords = []
    
    # 获取相关关键词
    if scored_keywords:
        top_keyword = scored_keywords[0]['entity']
        related_keywords = get_related_keyword(top_keyword)
    else:
        related_keywords = []
    
    return {
        'message': message,
        'entities': entities,
        'scored_keywords': scored_keywords,
        'related_keywords': related_keywords
    }


def review_mechanism(topic, draft="", user_id="", task=None):
    """
    审查机制
    
    Args:
        topic (str): 主题
        draft (str): 草稿内容
        user_id (str): 用户ID
        task: 任务对象
    
    Returns:
        str: 审查结果
    """
    print(f"\033[1;32m | INFO     | review mechanism... \033[0m")
    
    # 搜索相关论文
    related_papers = search_releated_paper(topic, max_paper_num=3, compression=True, user_id=user_id, task=task)
    
    # 构建审查提示
    papers_info = ""
    for paper in related_papers:
        papers_info += f"Title: {paper.get('title', '')}\n"
        papers_info += f"Abstract: {paper.get('abstract', '')}\n\n"
    
    system_prompt = "You are a helpful assistant for academic review."
    user_prompt = review_mechanism_prompt(topic=topic, draft=draft, related_papers=papers_info)
    
    review_result = call_with_deepseek(system_prompt=system_prompt, question=user_prompt)
    
    print(f"\033[1;32m | INFO     | review mechanism:OK! \033[0m")
    return review_result


def extract_message_review_moa(file, split_section):
    """
    使用MOA方法提取消息并进行审查
    
    Args:
        file (str): 文件路径
        split_section (str): 分割标识符
    
    Returns:
        dict: MOA审查结果
    """
    from app.core.moa import moa_idea_iteration
    
    message = extract_message(file, split_section)
    if not message:
        return None
    
    # 使用MOA进行想法迭代
    moa_result = moa_idea_iteration(message)
    
    return {
        'original_message': message,
        'moa_result': moa_result
    }