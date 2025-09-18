#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2024/9/21 23:07
# @Author : 桐
# @QQ:1041264242
# 注意事项：
from celery import current_task
from app.core.celery import celery_app
from app.utils.arxiv_api import search_paper
from app.utils.llm_api import LLMClient
from app.core.prompt import PAPER_GENERATION_PROMPT
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def generate_research_paper(self, keyword: str, search_paper_num: int = 5) -> Dict[str, Any]:
    """
    生成研究论文的异步任务
    
    Args:
        keyword: 研究关键词
        search_paper_num: 搜索论文数量
        
    Returns:
        Dict[str, Any]: 生成结果
    """
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': '开始搜索相关论文...'}
        )
        
        # 搜索相关论文
        logger.info(f"开始搜索关键词: {keyword}")
        papers = search_paper([keyword], Limit=search_paper_num)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': '正在生成研究论文...'}
        )
        
        # 使用LLM生成论文
        llm_client = LLMClient()
        
        # 构建提示词
        papers_text = "\n\n".join([
            f"标题: {paper['title']}\n摘要: {paper['abstract']}\n作者: {paper['authors']}\n发布时间: {paper['time']}"
            for paper in papers[:5]  # 限制论文数量
        ])
        
        prompt = PAPER_GENERATION_PROMPT.format(
            keyword=keyword,
            papers=papers_text
        )
        
        # 生成论文
        generated_paper = llm_client.generate_text(prompt)
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': '完成论文生成'}
        )
        
        result = {
            'keyword': keyword,
            'paper_count': len(papers),
            'generated_paper': generated_paper,
            'source_papers': papers[:5],
            'status': 'SUCCESS'
        }
        
        logger.info(f"成功生成关键词 '{keyword}' 的研究论文")
        return result
        
    except Exception as e:
        logger.error(f"生成研究论文失败: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': '生成失败'}
        )
        raise e