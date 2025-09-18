# Generate Hypothesis MCP

基于MCP协议的AI研究论文生成工具 - AstroInsight Research Assistant

## 项目简介

这是一个基于Model Context Protocol (MCP) 的研究论文生成工具，能够自动化地进行学术研究和论文生成流程。该工具集成了多个AI模型和学术数据源，提供从关键词搜索到完整论文生成的端到端解决方案。

## 主要功能

- **智能论文搜索**: 基于关键词自动搜索相关学术论文
- **事实信息提取**: 从学术论文中提取关键事实和信息
- **假设生成**: 基于提取的信息生成研究假设
- **技术优化**: 对研究思路进行技术层面的优化
- **多智能体协作**: 使用MoA (Mixture of Agents) 方法进行协作优化
- **人机协作**: 支持人工干预和指导的研究流程

## 技术架构

- **MCP协议**: 基于FastMCP实现的服务器
- **多模型支持**: 集成DeepSeek、Qwen等多个AI模型
- **异步任务处理**: 支持长时间运行的研究任务
- **实时状态跟踪**: 提供任务进度和状态监控

## 安装和使用

### 环境要求

- Python 3.8+
- 相关依赖包（见requirements.txt）

### 配置

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 配置API密钥：
```
DEEPSEEK_API_TOKEN=your_deepseek_token
QWEN_API_TOKEN=your_qwen_token
MINERU_API_TOKEN=your_mineru_token
```

### 启动服务

```bash
python astroinsight_optimized_fastmcp.py
```

### MCP工具使用

该项目提供以下MCP工具：

1. **generate_research_paper**: 生成研究论文
2. **get_task_status**: 获取任务状态
3. **list_active_tasks**: 列出活跃任务

## 项目结构

```
├── app/                    # 应用核心代码
│   ├── api/               # API接口
│   ├── core/              # 核心功能模块
│   ├── task/              # 任务处理
│   └── utils/             # 工具函数
├── astroinsight_optimized_fastmcp.py  # MCP服务器主文件
├── main.py                # 主要业务逻辑
├── requirements.txt       # 依赖包列表
└── README.md             # 项目说明

```

## 开发规范

### Git提交规范

- `feat`: 增加新功能
- `fix`: 修复问题/BUG
- `style`: 代码风格相关无影响运行结果的
- `perf`: 优化/性能提升
- `refactor`: 重构
- `revert`: 撤销修改
- `test`: 测试相关
- `docs`: 文档/注释
- `chore`: 依赖更新/脚手架配置修改等

### 编码规范

- Python文件编码为 `utf-8`
- 遵循PEP 8代码风格
- 添加必要的函数和类注释

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。