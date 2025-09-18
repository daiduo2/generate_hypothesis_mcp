#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2024/11/2 19:08
# @Author : 桐
# @QQ:1041264242
# 注意事项：
import warnings
import agentscope
from agentscope import msghub
from agentscope.agents import DialogAgent, UserAgent
from agentscope.message import Msg
from app.core.config import OUTPUT_PATH
import os
from app.core.tpl import tpl_env

# 抑制SQLAlchemy相关警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")
warnings.filterwarnings("ignore", message=".*SQLAlchemy.*")

model_configs = [
    {
        "config_name": "qwen-max-2025-01-25",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
        "api_key": "sk-586f6f96d2704df6901e31de27fda2fe",
    },
    {
        "config_name": "qwen-plus",
        "model_type": "dashscope_chat",
        "model_name": "qwen-plus",
        "api_key": "sk-586f6f96d2704df6901e31de27fda2fe",
    },
    {
        "config_name": "glm-4-long",
        "model_type": "openai_chat",
        "model_name": "glm-4-long",
        "api_key": "1cf7ad6057486482907576343cdfad25.Pj3NWFDgjyjNqDVK",
        "client_args": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        },
    },
    {
        "config_name": "deepseek-chat",
        "model_type": "openai_chat",
        "model_name": "deepseek-chat",
        "api_key": "sk-80cc66e836004e6ca698eb35206dd418",
        "client_args": {
            "base_url": "https://api.deepseek.com/v1",
        },
    },
    {
        "config_name": "moonshot-v1-8k",
        "model_type": "openai_chat",
        "model_name": "moonshot-v1-8k",
        "api_key": "sk-u66x82yZ6tMcjRMOwkKouZDHrhrLmLGl3ghjOlxOBUuvw6MD",
        "client_args": {
            "base_url": "https://api.moonshot.cn/v1",
        },
    },
    {
        "config_name": "gemini-2.5-flash",
        "model_type": "gemini_chat",
        "model_name": "gemini-2.5-flash",
        "api_key": "AIzaSyCRuZMYqpQZAt7wlSsqXGjXcwxUekrrH4s",
    },
    {
        "config_name": "hunyuan-large",
        "model_type": "openai_chat",
        "model_name": "hunyuan-large",
        "api_key": "sk-O5wisGpuwAS6FM7ICWtOM049vWYyEGq3opa4wSf920zeimW4",
        "client_args": {
            "base_url": "https://api.hunyuan.cloud.tencent.com/v1",
        },
    }
    # {
    #     "config_name": "chatgpt-4o-latest",
    #     "model_type": "openai_chat",
    #     "model_name": "chatgpt-4o-latest",
    #     "api_key": "sk-gT9nO93CQQKoNb1KTUuGIeV1b05DUkYF0ZJjngcDev12RiuY",
    #
    #     "client_args": {
    #         "base_url": "https://api.openai-proxy.org/v1/",
    #     },
    # },
]


def moa_idea_iteration(topic="", user_prompt="", user_id="", task=None):
    """
    MOA思想迭代函数
    
    Args:
        topic: 研究主题
        user_prompt: 用户提示
        user_id: 用户ID
        task: 任务对象
    
    Returns:
        str: 聚合后的内容
    """
    file_path_prefix = fr"{OUTPUT_PATH}/{user_id}/{task.id}/{topic}/MOA"
    # 读取模型配置
    agentscope.init(model_configs=model_configs)

    system_prompt = "You are a research expert whose primary goal is to identify promising, new, and key scientific problems based on existing scientific literature, in order to aid researchers in discovering novel and significant research opportunities that can advance the field."

    # 创建一个对话智能体和一个用户智能体
    dialogAgent_Gemini = DialogAgent(name="Gemini", model_config_name="glm-4-long", sys_prompt=system_prompt)
    dialogAgent_Qwen = DialogAgent(name="Qwen", model_config_name="qwen-plus", sys_prompt=system_prompt)
    dialogAgent_DeepSeek = DialogAgent(name="DeepSeek", model_config_name="deepseek-chat", sys_prompt=system_prompt)

    dialogAgent_AC = DialogAgent(name="AC", model_config_name="deepseek-chat", sys_prompt=system_prompt)

    dialogAgent_Reviewer = DialogAgent(name="Reviewer", model_config_name="deepseek-chat", sys_prompt=system_prompt)

    Gemini_message = dialogAgent_Gemini(Msg(name="User", role="user", content=user_prompt))
    Qwen_message = dialogAgent_Qwen(Msg(name="User", role="user", content=user_prompt))
    DeepSeek_message = dialogAgent_DeepSeek(Msg(name="User", role="user", content=user_prompt))

    os.makedirs(file_path_prefix, exist_ok=True)
    with open(fr"{file_path_prefix}/Qwen_{topic}_moa.md", 'w', encoding='utf-8') as f:
        f.write(Qwen_message.content)
    with open(fr"{file_path_prefix}/DeepSeek_{topic}_moa.md", 'w', encoding='utf-8') as f:
        f.write(DeepSeek_message.content)
    with open(fr"{file_path_prefix}/Kimi_{topic}_moa.md", 'w', encoding='utf-8') as f:
        f.write(Gemini_message.content)

    aggregation_tpl = tpl_env.get_template("prompt/moa/moa_idea_iteration_aggregation.tpl")
    data = {
        "Qwen_message": Qwen_message.content,
        "DeepSeek_message": DeepSeek_message.content,
        "Gemini_message": Gemini_message.content,
    }
    aggregation = aggregation_tpl.render(data=data)

    AC_message = dialogAgent_AC(Msg(name="User", role="user", content=aggregation))

    with open(fr"{file_path_prefix}/AC_{topic}_moa.md", 'w', encoding='utf-8') as f:
        f.write(AC_message.content)

    reviewer_prompt_tpl = tpl_env.get_template("prompt/moa/reviewer_prompt.tpl")
    Reviewer_prompt = reviewer_prompt_tpl.render()

    Reviewer_message = dialogAgent_Reviewer(Msg(name="User", role="user", content=Reviewer_prompt))

    with open(fr"{file_path_prefix}/Reviewer_{topic}_moa.md", 'w', encoding='utf-8') as f:
        f.write(Reviewer_message.content)

    # 打印模型 API 的使用情况
    agentscope.print_llm_usage()

    return AC_message.content


def moa_model(model_configs, agent_list, topic, user_prompt, systeam_prompt, ac_prompt="", ac_systeam="", stage=""):
    """
    MOA模型函数
    
    Args:
        model_configs: 模型配置
        agent_list: 智能体列表
        topic: 主题
        user_prompt: 用户提示
        systeam_prompt: 系统提示
        ac_prompt: AC提示
        ac_systeam: AC系统提示
        stage: 阶段
    """
    # 读取模型配置
    agentscope.init(model_configs=model_configs)
    system_prompt = ("You are an research expert whose primary goal "
                     "is to identify promising, new, and key scientific problems based on existing scientific "
                     "literature, in order to aid researchers in discovering novel and significant research "
                     "opportunities that can advance the field.")
    agents = {}

    for llm in agent_list['helper']:
        agent = DialogAgent(name=llm, model_config_name=llm, sys_prompt=system_prompt)
        agents[llm] = agent

    messages = {}
    for agent_key in agents:
        agent = agents[agent_key]
        message = agent(Msg(name="user", role="user", content=user_prompt))
        messages[agent_key] = message

    for message_key in messages:
        with open(
                fr"{OUTPUT_PATH}/{topic}/MOA/{message_key}_{topic}_{stage}.md",
                'w', encoding='utf-8') as f:
            f.write(messages[message_key].content)

    if ac_prompt != "" and agent_list['main'] != "":
        AC = DialogAgent(name="AC", model_config_name=agent_list['main'], sys_prompt=ac_systeam)
        AC_message = AC(Msg(name="user", role="user", content=ac_prompt))
        with open(
                fr"{OUTPUT_PATH}/{topic}/MOA/AC_{topic}_{stage}.md",
                'w', encoding='utf-8') as f:
            f.write(AC_message.content)

    # 打印模型 API 的使用情况
    agentscope.print_llm_usage()


def moa_table(model_configs=model_configs, topic='', draft='', user_id='', task=None):
    """
    MOA表格函数
    
    Args:
        model_configs: 模型配置
        topic: 主题
        draft: 草稿
        user_id: 用户ID
        task: 任务对象
    """
    file_path_prefix = fr"{OUTPUT_PATH}/{user_id}/{task.id}/{topic}/MOA"
    # test_tpl = tpl_env.get_template("prompt/moa/moa_test.tpl")
    # draft = test_tpl.render()

    # agentscope.studio.init()
    agentscope.init(model_configs=model_configs)  # ,logger_level="DEBUG",save_log=True

    role = ("You are a seminar reviewer responsible for evaluating research idea drafts. When reviewing, take into "
            "account the content of the draft as well as feedback from other reviewers. While recognizing the value "
            "in others' comments, your focus should be on providing a unique perspective that enhances and optimizes "
            "the draft. Your feedback should be concise, consisting of a well-constructed paragraph that builds on "
            "the ongoing discussion without replicating other reviewers' suggestions. Always strive to present your "
            "distinct viewpoint.")
    viewer = """Act a moderator in a seminar.  After the four reviewers have completed their evaluations, 
    you will need to comprehensively analyze the content of the idea draft as well as the valuable review comments 
    provided by each reviewer. Based on this, you are required to systematically summarize and integrate these review 
    opinions, ensuring that all key feedback and suggestions are accurately and comprehensively considered. The 
    output should strictly follow the format below: # Overall Opinions:

    # Iterative Optimization Search Keywords:
    - [Keyword 1]
    - [Keyword 2]
    - ..."""

    dialogAgent_Qwen = DialogAgent(name="Reviewer 1", model_config_name="qwen-plus", sys_prompt=role)  #"qwen-max-0919"
    dialogAgent_Gemini = DialogAgent(name="Reviewer 2", model_config_name="glm-4-long",
                                     sys_prompt=role)  # "gemini-1.5-flash"
    dialogAgent_DeepSeek = DialogAgent(name="Reviewer 3", model_config_name="deepseek-chat", sys_prompt=role)
    # userAgent = UserAgent(name="Reviewer 4")

    dialogAgent_Viewer = DialogAgent(name="Viewer", model_config_name="deepseek-chat", sys_prompt=viewer)

    with msghub(participants=[dialogAgent_Gemini, dialogAgent_Qwen, dialogAgent_DeepSeek,
                              dialogAgent_Viewer]) as hub:
        # Broadcast a message to all participants
        hub.broadcast(Msg(name="Host", role="user",
                          content=f"Welcome to join the seminar chat! Now, The idea draft we need to discuss as "
                                  f"follows:\n{draft}"))

        dialogAgent_Qwen()
        dialogAgent_Gemini()
        dialogAgent_DeepSeek()
        # userAgent()
        viewer_message = dialogAgent_Viewer()

    with open(fr"{file_path_prefix}/{topic}_review_moa.md", 'w', encoding='utf-8') as f:
        f.write(viewer_message.content)

    # 打印模型 API 的使用情况
    agentscope.print_llm_usage()
