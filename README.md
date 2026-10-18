# Star Multi-Agent Public Opinion Monitor

> 尚舆分析平台 — 多专家圆桌讨论的 AI 深度舆情研究平台

输入一个舆情主题，系统并发调度 **Insight（数据挖掘）** 与 **Media（全网检索）** 两个研究智能体产出分维度报告，再由 **Host（主持人）** 智能体按维度交叉研判、裁决，最终生成综合舆情分析报告，全流程进度通过 SSE 实时推送至前端工作台。

## 系统架构

```
                        ┌──────────────────────────────┐
                        │        Vue3 前端工作台        │
                        │  配置 / 研究 / 圆桌讨论 / 报告  │
                        └──────────┬───────────────────┘
                          REST     │     SSE (/api/events/stream)
                        ┌──────────┴───────────────────┐
                        │        FastAPI 应用层          │
                        │  routers(rest/sse) + services │
                        └──────────┬───────────────────┘
                                   │ 事件总线 (pub/sub)
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────┴────────┐        ┌────────┴────────┐        ┌────────┴────────┐
│ Insight Agent  │        │  Media Agent    │        │  Host Agent     │
│ 检索→重排→聚类   │        │ 规划→搜索→摘要    │        │ 配对→研判→裁决    │
│ →章节规划→摘要   │        │ →格式化→落盘      │        │ →最终报告→落盘    │
│ →格式化→落盘     │        └─────────────────┘        └─────────────────┘
└───────┬────────┘                   │                        │
        │              SECTION_READY 事件 + 讨论消息              │
┌───────┴────────────────────────────┴────────────────────────┴────────┐
│                    Report Engine 报告生成引擎                          │
│     汇总三方输入 → LLM 生成 Markdown → 渲染 HTML → 双格式落盘/下载       │
└──────────────────────────────────────────────────────────────────────┘
```

- **Insight Agent**：MySQL 舆情库只读查询 + Milvus 混合检索（BGE-M3 稠密/稀疏双通道、RRF 融合、时间窗口过滤），KMeans 语义聚类分桶，按章节分配证据并逐章摘要
- **Media Agent**：Tavily / Bocha / Anspire 多提供方可切换的全网搜索，分章节规划搜索词、检索、摘要
- **Host Agent**：监听章节就绪事件，配对存储管理双源同维度结论，LLM 交叉研判（携带近三次历史研判保持连贯），汇总生成裁判报告，失败优雅降级
- **Report Engine**：校验三方输入就绪 → LLM 生成综合报告 → Markdown 渲染 HTML → 双格式落盘，任务状态机支持轮询与下载

## 技术栈

| 层次 | 技术 |
| --- | --- |
| Web 框架 | FastAPI、uvicorn、sse-starlette |
| 智能体编排 | LangGraph、LangChain、OpenAI 兼容协议 |
| 数据存储 | MySQL（SQLAlchemy 异步只读）、Milvus（pymilvus）、本地文件 |
| 向量检索 | FlagEmbedding（BGE-M3）、scikit-learn（KMeans） |
| 搜索服务 | Tavily、Bocha、Anspire |
| 配置与日志 | pydantic-settings（.env 热更新）、loguru（按角色分文件） |
| 前端 | Vue3 + Vite（SSE 实时进度、报告在线预览与导出） |

## 目录结构

```
star_sentiment_analyse/
├── main.py                     # 启动入口 (uvicorn)
├── app/                        # FastAPI 应用层
│   ├── app.py                  # 路由挂载 + 生命周期管理
│   ├── routers/rest/           # research / host / report / config 接口
│   ├── routers/sse/            # SSE 事件流接口
│   ├── services/               # 业务服务层
│   └── schemas/                # Pydantic 请求/响应模型
├── engines/                    # 智能体引擎层
│   ├── contracts/              # 全局配置、角色、维度、证据定义
│   ├── orchestration/          # 并发调度 insight + media 研究
│   ├── insight_agent/          # 数据挖掘智能体 (LangGraph + MySQL/Milvus)
│   ├── media_agent/            # 全网检索智能体 (LangGraph + 搜索 API)
│   ├── host_agent/             # 主持人圆桌研判图
│   ├── report_engine/          # 综合报告生成与 HTML 渲染
│   └── common/                 # LLM 客户端、事件总线、节点基类、日志
├── front/                      # Vue3 前端
├── data/report/                # 生成的报告产物 (host/insight/media/综合)
└── test/                       # 测试
```

## 快速开始

### 1. 安装依赖

```bash
# 后端 (uv)
uv sync
# 或 pip
pip install -e .

# 需要 Insight 私域检索时安装 ML 依赖
uv sync --extra ml

# 前端
cd front && npm install
```

### 2. 配置环境变量

复制下方配置到 `.env`（该文件包含密钥，已被 `.gitignore` 忽略）：

```env
# 服务
HOST=0.0.0.0
PORT=5000

# 数据库 (舆情库只读)
DB_DIALECT=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=media_crawler_v1

# 各角色 LLM (OpenAI 兼容协议，按角色独立配置)
INSIGHT_ENGINE_API_KEY=sk-xxx
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=kimi-k2.6
INSIGHT_ENGINE_MODEL_PROVIDER=openai

MEDIA_ENGINE_API_KEY=sk-xxx
MEDIA_ENGINE_BASE_URL=https://api.openai-proxy.org/v1
MEDIA_ENGINE_MODEL_NAME=gemini-2.5-pro
MEDIA_ENGINE_MODEL_PROVIDER=openai

REPORT_ENGINE_API_KEY=sk-xxx
REPORT_ENGINE_BASE_URL=https://api.deepseek.com
REPORT_ENGINE_MODEL_NAME=deepseek-chat
REPORT_ENGINE_MODEL_PROVIDER=openai

HOST_API_KEY=sk-xxx
HOST_BASE_URL=https://api.deepseek.com
HOST_MODEL_NAME=deepseek-chat
HOST_MODEL_PROVIDER=openai

# 搜索提供方: TavilyAPI | BochaAPI | AnspireAPI
SEARCH_SWITCH=TavilyAPI
TAVILY_API_KEY=tvly-xxx

# Milvus 向量检索 (可选)
INSIGHT_VECTOR_ENABLED=true
MILVUS_URI=tcp://localhost:19530
INSIGHT_EMBEDDING_MODEL=BAAI/bge-m3
```

> 所有配置均可通过前端「配置」页面在线修改，接口写回 `.env` 并热加载，**无需重启服务**。

### 3. 启动

```bash
# 后端
uv run main.py

# 前端 (另开终端)
cd front && npm run dev
```

浏览器访问前端开发地址，依次体验：**配置 → 研究 → 圆桌讨论 → 报告**。

## API 一览

### 研究

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/research` | 启动研究（并发执行 insight + media） |
| GET | `/api/research/latest` | 获取最新研究报告 |
| GET | `/api/events/stream` | SSE 实时进度事件流 |

### 主持人圆桌

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/host/start` | 启动主持人研判 |
| GET | `/api/host/stop` | 停止主持人研判 |
| GET | `/api/host/discussion` | 获取讨论区发言记录 |

### 综合报告

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/report/status` | 查询三方输入就绪状态 |
| POST | `/api/report/generate` | 异步生成综合报告 |
| GET | `/api/report/result/{task_id}` | 获取 HTML 报告内容 |
| GET | `/api/report/download/{task_id}/{file_type}` | 下载 html / md 报告 |

### 系统配置

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/config` | 读取当前配置 |
| POST | `/api/config` | 更新配置并热加载 |

## 核心特性

- **多智能体全链路**：Insight + Media 并发研究 → Host 圆桌交叉研判 → 综合报告生成，端到端自动产出结构化舆情分析报告
- **实时可观测**：SSE 推送角色进度、状态、百分比与异常，多客户端并发事件隔离，可实时观测完整推理过程
- **混合检索与聚类**：Milvus 稠密/稀疏双通道召回 + RRF 融合 + 时间窗口过滤，KMeans 语义聚类去重分桶
- **交叉研判机制**：双源章节配对校验、LLM 裁决携带历史研判上下文、Markdown 统一清洗、失败重试降级
- **平台化能力**：配置热更新不重启、报告任务状态机、按角色分级日志、报告 HTML/Markdown 在线预览与导出
