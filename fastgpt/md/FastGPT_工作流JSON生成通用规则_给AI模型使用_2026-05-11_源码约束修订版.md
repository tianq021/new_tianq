# FastGPT 工作流 JSON 生成通用规则（给 AI 模型使用｜源码约束修订版）

版本：2026-05-11 修订版  
用途：让 AI 根据用户一句话需求，生成 **可导入 FastGPT 的工作流 JSON** 或 **工作流模板**。如果存在必须手动配置的内容，必须明确提醒用户手动填写。

---

## 0. 最高原则

本文件不是让 AI 凭空创造 FastGPT 节点结构。

正确目标：

> 用户只输入一句话，AI 自动判断工作流类型，匹配已验证模板，生成 FastGPT JSON 或工作流模板；如果涉及模型、知识库、API、数据库、字段、文件上传等无法自动确定的配置，必须明确列出【需要手动配置】。

必须遵守：

1. 能自动生成的自动生成。
2. 不能确定的绝不编造。
3. 需要用户或平台手动配置的，必须提醒。
4. 没有已验证模板时，只能生成最小骨架或设计方案，不能硬造复杂 JSON。

---

## 1. 最终目标

用户可能只说一句话，例如：

```text
做一个翻译助手
```

```text
做一个会议纪要整理助手
```

```text
做一个票据识别助手
```

```text
做一个知识库问答助手
```

AI 需要完成：

1. 理解用户一句话需求。
2. 判断属于哪类工作流。
3. 匹配最接近的已验证工作流模板。
4. 生成可导入 FastGPT 的 JSON，或者生成工作流模板。
5. 对无法从一句话中确定的配置，明确列出【需要手动配置】。
6. 禁止编造平台私有信息。
7. 最后执行自检，避免生成导入后不能跑的 JSON。

---

## 2. 三种生成结果类型

### A 类：可以直接生成完整 JSON

适合简单文本处理类工作流：

```text
翻译助手
文本总结助手
文本润色助手
会议纪要整理助手
简单分类助手
简单问答助手
输入校验助手
```

常用结构：

```text
流程开始 workflowStart
→ 输入检查 code
→ 判断器 ifElseNode
→ AI 对话 chatNode
→ 指定回复 answerNode
```

仍要提醒：

```text
导入后请检查 AI 模型是否已选择；如果平台默认模型不可用，需要手动选择模型。
```

### B 类：可以生成 JSON 模板，但必须提醒手动配置

适合依赖平台资源的工作流：

```text
知识库问答助手
文件解析助手
图片识别助手
CSV 数据清洗助手
票据识别助手
文本字段提取助手
HTTP 请求助手
```

必须提醒：

```text
AI 模型需要手动选择
知识库需要手动绑定
上传文件类型需要手动检查
HTTP URL / Header / API Key 需要手动填写
提取字段需要按实际业务补充
```

### C 类：不能直接生成完整 JSON，只能生成设计方案或半成品模板

高风险或依赖真实环境的工作流：

```text
数据库入库
调用企业内部 API
调用第三方支付
复杂 API 鉴权
私有工具调用
多层 Agent 工具调用
复杂循环批处理
复杂表单交互
```

只能输出：

```text
基础骨架 JSON
+
需要手动配置清单
+
推荐节点连接方式
+
测试建议
```

---

## 3. FastGPT 源码实现事实

FastGPT 工作流节点不是靠“节点名字”运行，而是靠：

```text
flowNodeType
inputs
outputs
edges
chatConfig
```

核心实现链路：

```text
节点类型枚举
→ 节点模板库
→ 前端画布渲染组件
→ 保存/加载适配
→ 后端 dispatch 执行器
```

因此 AI 生成 JSON 时，必须使用源码中真实存在的：

```text
flowNodeType
NodeInputKeyEnum
NodeOutputKeyEnum
FlowNodeInputTypeEnum
WorkflowIOValueTypeEnum
```

常用源码路径：

```text
packages/global/core/workflow/node/constant.ts
```

定义：

```text
FlowNodeTypeEnum
FlowNodeInputTypeEnum
FlowNodeOutputTypeEnum
```

```text
packages/global/core/workflow/constants.ts
```

定义：

```text
NodeInputKeyEnum
NodeOutputKeyEnum
WorkflowIOValueTypeEnum
变量类型
HTTP ContentTypes
```

```text
packages/global/core/workflow/template/constants.ts
```

注册系统节点模板：

```text
AiChatModule
AssignedAnswerModule
ClassifyQuestionModule
ContextExtractModule
DatasetSearchModule
HttpNode468
WorkflowStart
IfElseNode
ReadFilesNode
CodeNode
TextEditorNode
```

```text
projects/app/src/pageComponents/app/detail/WorkflowComponents/Flow/index.tsx
```

前端 ReactFlow 根据 `flowNodeType` 映射节点 UI。

```text
projects/app/src/web/core/workflow/utils.ts
```

处理：

```text
nodeTemplate2FlowNode
storeNode2FlowNode
checkWorkflowNodeAndConnection
变量引用校验
节点连通性校验
```

```text
packages/service/core/workflow/dispatch/constants.ts
```

后端 callbackMap：

```text
flowNodeType → dispatch 执行函数
```

---

## 4. 基础 JSON 顶层结构

推荐普通导入结构：

```json
{
  "nodes": [],
  "edges": [],
  "chatConfig": {}
}
```

每个节点推荐至少包含：

```json
{
  "nodeId": "唯一节点ID",
  "name": "节点名称",
  "intro": "节点说明",
  "avatar": "core/workflow/template/xxx",
  "flowNodeType": "chatNode",
  "position": {
    "x": 100,
    "y": 100
  },
  "version": "481",
  "inputs": [],
  "outputs": []
}
```

重要要求：

```text
nodeId 必须唯一。
flowNodeType 必须是真实枚举值。
position 必须存在。
inputs / outputs 必须存在，即使为空数组。
```

---

## 5. inputs 与 outputs 规则

输入项常见结构：

```json
{
  "key": "userChatInput",
  "renderTypeList": ["reference", "textarea"],
  "valueType": "string",
  "label": "用户问题",
  "required": true,
  "value": ["448745", "userChatInput"],
  "selectedTypeIndex": 0
}
```

输出项常见结构：

```json
{
  "id": "answerText",
  "key": "answerText",
  "label": "AI 回复内容",
  "valueType": "string",
  "type": "static"
}
```

注意：

```text
引用上游输出时，引用的是 output.id。
通常 output.id 与 output.key 一样，但不要永远假设一样。
```

---

## 6. 变量引用规则

### 6.1 普通字段引用

```json
["上游节点ID", "输出ID"]
```

例：

```json
["448745", "userChatInput"]
```

```json
["ai_translate", "answerText"]
```

### 6.2 文件列表引用

文件上传列表必须使用二维数组：

```json
[["流程开始节点ID", "userFiles"]]
```

例：

```json
[["448745", "userFiles"]]
```

不要写成：

```json
["448745", "userFiles"]
```

原因：

```text
fileUrlList 的 valueType 是 arrayString。
源码前端添加节点时，默认 fileUrlList = [[workflowStartNodeId, userFiles]]。
```

### 6.3 文本模板插值

文本拼接、PromptEditor、文本模板中可以使用：

```text
{{$nodeId.outputId$}}
```

例：

```text
会议摘要：
{{$ai_summary.answerText$}}
```

```text
文档解析内容：
{{$read_files.system_text$}}
```

### 6.4 selectedTypeIndex 比 connected 更关键

旧导出里可能有：

```json
"connected": true
```

但当前源码判断引用类型的关键是：

```text
renderTypeList[selectedTypeIndex] 是否等于 reference
```

因此引用上游时应写：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "selectedTypeIndex": 1,
  "value": ["ai_translate", "answerText"]
}
```

`connected` 可以作为旧版兼容字段保留，但不能把它当核心规则。

---

## 7. edges 与 handle 规则

普通连线：

```json
{
  "source": "源节点ID",
  "target": "目标节点ID",
  "sourceHandle": "源节点ID-source-right",
  "targetHandle": "目标节点ID-target-left"
}
```

例：

```json
{
  "source": "448745",
  "target": "ai_translate",
  "sourceHandle": "448745-source-right",
  "targetHandle": "ai_translate-target-left"
}
```

---

## 8. 分支 handle 规则

### 8.1 ifElseNode 判断器

判断器分支不是 `true/false`。

正确 sourceHandle：

```text
节点ID-source-IF
节点ID-source-ELSE
节点ID-source-ELSE IF 1
```

例：

```json
{
  "source": "check_valid",
  "target": "ai_translate",
  "sourceHandle": "check_valid-source-IF",
  "targetHandle": "ai_translate-target-left"
}
```

```json
{
  "source": "check_valid",
  "target": "answer_invalid",
  "sourceHandle": "check_valid-source-ELSE",
  "targetHandle": "answer_invalid-target-left"
}
```

### 8.2 classifyQuestion 问题分类

问题分类节点的分支 handle 使用 `agents.key`，不是 `agents.value`。

例：

```json
"agents": [
  {
    "key": "translate",
    "value": "用户想翻译文本"
  },
  {
    "key": "other",
    "value": "其他问题"
  }
]
```

对应分支：

```text
classify_node-source-translate
classify_node-source-other
```

---

## 9. 常用节点源码约束

### 9.1 systemConfig / userGuide：系统配置节点

真实 flowNodeType：

```text
userGuide
```

源码枚举：

```text
FlowNodeTypeEnum.systemConfig = "userGuide"
```

用途：

```text
配置欢迎语、变量、问题引导、TTS、语音输入、定时触发等。
```

注意：

```text
源码模板 SystemConfigNode 本身 inputs 为空。
但空应用模板里会生成带 welcomeText / variables / questionGuide / tts / whisper / scheduleTrigger 的 userGuide 节点。
```

推荐生成时保留兼容写法，但不要只依赖 userGuide；同时写好 chatConfig。

---

### 9.2 workflowStart：流程开始

真实 flowNodeType：

```text
workflowStart
```

默认输入：

```text
userChatInput
```

默认输出：

```text
userChatInput
```

如果需要文件上传，追加输出：

```json
{
  "id": "userFiles",
  "key": "userFiles",
  "label": "用户文件",
  "description": "用户上传的文件",
  "type": "static",
  "valueType": "arrayString"
}
```

并且必须配置：

```text
chatConfig.fileSelectConfig
```

---

### 9.3 chatNode：AI 对话节点

真实 flowNodeType：

```text
chatNode
```

核心 inputs：

```text
model
temperature
maxToken
isResponseAnswerText
systemPrompt
history
quoteQA
fileUrlList
userChatInput
aiChatVision
aiChatReasoning
aiChatResponseFormat
aiChatJsonSchema
```

核心 outputs：

```text
history
answerText
reasoningText
system_error_text
```

关键提醒：

```text
model 可以留空用于导入后手动选择。
但运行前必须选择有效模型。
如果平台模型配置坏了，JSON 正确也会失败。
```

中间 AI 节点建议：

```json
"isResponseAnswerText": false
```

最终输出交给 `answerNode`，避免中间内容直接显示给用户。

---

### 9.4 answerNode：指定回复节点

真实 flowNodeType：

```text
answerNode
```

源码模板只有一个 input：

```text
key: text
renderTypeList: [textarea, reference]
valueType: any
```

引用 AI 输出时：

```json
{
  "key": "text",
  "renderTypeList": ["textarea", "reference"],
  "valueType": "any",
  "required": true,
  "label": "回复内容",
  "value": ["ai_translate", "answerText"],
  "selectedTypeIndex": 1
}
```

固定文本回复时：

```json
{
  "key": "text",
  "renderTypeList": ["textarea", "reference"],
  "valueType": "any",
  "required": true,
  "label": "回复内容",
  "value": "请输入需要处理的文本。"
}
```

---

### 9.5 ifElseNode：判断器节点

真实 flowNodeType：

```text
ifElseNode
```

核心 input：

```text
ifElseList
```

输出：

```text
ifElseResult
```

判断器示例：

```json
{
  "key": "ifElseList",
  "renderTypeList": ["hidden"],
  "valueType": "any",
  "label": "",
  "value": [
    {
      "condition": "AND",
      "list": [
        {
          "variable": ["check_input", "is_valid"],
          "condition": "equalTo",
          "value": "yes",
          "valueType": "input"
        }
      ]
    }
  ]
}
```

合法条件包括：

```text
equalTo
notEqual
isEmpty
isNotEmpty
include
notInclude
startWith
endWith
reg
greaterThan
greaterThanOrEqualTo
lessThan
lessThanOrEqualTo
lengthEqualTo
lengthNotEqualTo
lengthGreaterThan
lengthGreaterThanOrEqualTo
lengthLessThan
lengthLessThanOrEqualTo
```

---

### 9.6 code：代码运行节点

真实 flowNodeType：

```text
code
```

规则：

```text
代码 return 了什么字段，outputs 就必须声明什么字段。
否则后续节点引用时可能找不到 output。
```

例如代码：

```javascript
function main(params) {
  const text = String(params.text || '').trim();

  if (!text) {
    return {
      is_valid: 'no',
      cleaned_text: '',
      reason: 'empty'
    };
  }

  return {
    is_valid: 'yes',
    cleaned_text: text,
    reason: 'valid'
  };
}
```

对应 outputs 必须包含：

```text
is_valid
cleaned_text
reason
system_rawResponse
error
```

---

### 9.7 readFiles：文档解析节点

真实 flowNodeType：

```text
readFiles
```

核心 input：

```text
fileUrlList
```

valueType：

```text
arrayString
```

必须用二维引用：

```json
[["448745", "userFiles"]]
```

核心 outputs：

```text
system_text
system_rawResponse
system_error_text
```

正确引用文档解析结果：

```json
["read_files", "system_text"]
```

错误写法：

```json
["read_files", "text"]
```

必须提醒：

```text
需要在 chatConfig.fileSelectConfig 中打开文件上传。
```

---

### 9.8 datasetSearchNode：知识库搜索节点

真实 flowNodeType：

```text
datasetSearchNode
```

核心 inputs：

```text
datasets
similarity
limit
searchMode
embeddingWeight
usingReRank
rerankModel
userChatInput
collectionFilterMatch
```

输出：

```text
quoteQA
```

注意：

```text
datasets 是必填项，valueType 是 selectDataset。
AI 禁止编造 datasetId。
如果用户只说“做知识库问答助手”，只能生成骨架，并提醒导入后手动绑定知识库。
```

---

### 9.9 classifyQuestion：问题分类节点

真实 flowNodeType：

```text
classifyQuestion
```

核心 inputs：

```text
model
systemPrompt
history
userChatInput
agents
```

输出：

```text
cqResult
```

关键规则：

```text
分支 handle 使用 agents.key。
cqResult 返回的是 agents.value。
```

---

### 9.10 contentExtract：文本内容提取节点

真实 flowNodeType：

```text
contentExtract
```

核心 inputs：

```text
model
description
history
content
extractKeys
```

outputs：

```text
success
fields
system_error_text
```

注意：

```text
extractKeys 不能瞎写。
用户没有说明提取字段时，必须提醒手动配置。
```

extractKeys 格式大致为：

```json
[
  {
    "key": "invoice_no",
    "desc": "票据编号",
    "valueType": "string",
    "required": false,
    "enum": []
  }
]
```

---

### 9.11 httpRequest468：HTTP 请求节点

真实 flowNodeType：

```text
httpRequest468
```

核心 inputs：

```text
system_httpMethod
system_httpTimeout
system_httpReqUrl
system_header_secret
system_httpHeader
system_httpParams
system_httpJsonBody
system_httpFormBody
system_httpContentType
```

outputs：

```text
system_addOutputParam
httpRawResponse
error
```

禁止编造：

```text
URL
Authorization
API Key
Token
Cookie
数据库接口
私有服务地址
```

如果用户没有提供接口信息，必须提醒：

```text
导入后请手动填写接口 URL、请求方法、请求头、请求体和输出字段提取规则。
```

---

### 9.12 textEditor：文本拼接节点

真实 flowNodeType：

```text
textEditor
```

核心 input：

```text
system_textareaInput
```

output：

```text
system_text
```

适合把变量拼到提示词或 Markdown 中：

```text
用户原文：
{{$448745.userChatInput$}}

解析内容：
{{$read_files.system_text$}}
```

注意：

```text
textEditor 不是 answerNode。
textEditor 只生成拼接文本，最终输出仍建议连接 answerNode。
```

---

## 10. chatConfig 规则

基础文本助手：

```json
"chatConfig": {}
```

文档解析：

```json
"chatConfig": {
  "fileSelectConfig": {
    "canSelectFile": true,
    "canSelectImg": false,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 5,
    "customPdfParse": false
  }
}
```

图片识别：

```json
"chatConfig": {
  "fileSelectConfig": {
    "canSelectFile": false,
    "canSelectImg": true,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 5,
    "customPdfParse": false
  }
}
```

注意：

```text
打开图片上传不代表模型一定能看图。
AI 节点还需要使用支持 vision 的模型。
```

---

## 11. 禁止编造清单

AI 生成 JSON 时禁止编造：

```text
datasetId
collectionId
toolId
pluginId
API Key
Authorization
Cookie
数据库连接
数据库账号
数据库密码
私有模型 ID
私有模型名称
企业内部接口地址
用户真实业务表名
用户真实存储过程
```

可以生成占位提醒：

```text
【需要手动配置】导入后请在知识库搜索节点中选择知识库。
```

但不能写：

```json
"datasetId": "fake_dataset_id"
```

---

## 12. 必须手动配置提醒规则

只要工作流涉及以下内容，必须在结果中列出【需要手动配置】：

| 场景 | 必须提醒 |
|---|---|
| AI 节点 | 模型需要手动选择或确认 |
| 知识库搜索 | 需要手动绑定知识库 |
| 文档解析 | 需要打开文件上传并检查支持格式 |
| 图片识别 | 需要支持视觉模型 |
| 文本提取 | 需要确认 extractKeys 字段 |
| HTTP 请求 | 需要填写 URL、Header、Body、鉴权 |
| 数据库入库 | 需要手动配置数据库节点或后端接口 |
| 外部工具 | 需要真实 toolId/pluginId |
| 私有 API | 需要用户提供接口文档 |
| 业务字段 | 需要根据实际业务调整提示词 |

标准提醒格式：

```text
【需要手动配置】
1. AI 模型：导入后请在 FastGPT 页面手动选择可用模型。
2. 知识库：导入后请在知识库搜索节点手动绑定知识库。
3. API Key：禁止写入 JSON，请在平台安全配置或后端环境变量中配置。
4. 数据库连接：本模板不包含真实数据库连接，请手动配置。
5. 业务字段：请根据实际业务修改提示词和提取字段。
```

---

## 13. 一句话需求识别规则

收到一句话需求后，按顺序判断：

```text
1. 是否纯文本处理？
   是：使用文本类模板。

2. 是否需要文件上传？
   是：添加 fileSelectConfig、workflowStart.userFiles、readFiles 或视觉 AI 节点。

3. 是否需要知识库？
   是：添加 datasetSearchNode，但提醒手动绑定知识库。

4. 是否需要分类分支？
   是：使用 classifyQuestion 或 ifElseNode。

5. 是否需要外部接口？
   是：添加 httpRequest468 骨架，但提醒手动填写接口。

6. 是否需要数据库？
   是：只生成前置整理流程，不生成真实数据库连接。

7. 是否超出已验证模板？
   是：输出设计方案或最小骨架，不硬造。
```

---

## 14. 工作流模板选择表

| 用户一句话 | 类型 | 推荐模板 | 是否可完整生成 |
|---|---|---|---|
| 做一个翻译助手 | 文本处理 | start → code → ifElse → AI → answer | 可以 |
| 做一个文本总结助手 | 文本处理 | start → code → ifElse → AI → answer | 可以 |
| 做一个会议纪要行动项助手 | 文本提取/总结 | start → code → ifElse → AI → answer | 可以 |
| 做一个知识库问答助手 | 知识库 | start → datasetSearch → AI → answer | 模板，需要手动绑定知识库 |
| 做一个文件解析助手 | 文件 | start(files) → readFiles → AI → answer | 模板，需要文件上传配置 |
| 做一个图片识别助手 | 图片 | start(files) → AI vision → answer | 模板，需要视觉模型 |
| 做一个票据识别入库助手 | 文件/图片/数据库 | start → 分流 → AI提取 → 校验 → 入库 | 半成品，需要手动配置数据库 |
| 做一个调用接口助手 | HTTP | start → httpRequest → answer/AI | 模板，需要手动填写接口 |
| 做一个数据库查询助手 | 数据库 | start → HTTP/数据库节点 → AI → answer | 设计方案，需要真实连接 |

---

## 15. 标准生成流程

AI 应按以下步骤生成：

```text
步骤 1：识别需求类型
步骤 2：选择已验证模板
步骤 3：确定是否需要手动配置
步骤 4：生成 nodes
步骤 5：生成 edges
步骤 6：生成 chatConfig
步骤 7：自检变量引用
步骤 8：自检分支 handle
步骤 9：输出 JSON 文件
步骤 10：输出需要手动配置清单和测试文本
```

标准输出格式：

```text
【生成结果】
已生成：完整 JSON / 工作流模板 / 设计方案

【工作流类型】
例如：翻译助手

【自动生成内容】
1. 节点结构
2. 连线结构
3. 基础提示词
4. 判断逻辑
5. chatConfig

【需要手动配置】
1. AI 模型：导入后手动选择
2. 知识库：如有知识库节点，手动绑定
3. API Key：禁止写入 JSON
4. 数据库连接：禁止自动生成
5. 业务字段：按实际需求修改

【测试建议】
给出 3-5 条测试文本
```

---

## 16. 自检清单

### 16.1 节点检查

```text
nodeId 是否唯一
flowNodeType 是否真实存在
每个节点是否有 inputs 和 outputs
position 是否存在
```

### 16.2 连线检查

```text
edge.source 是否存在
edge.target 是否存在
sourceHandle 是否符合规则
targetHandle 是否符合规则
所有非系统节点是否从 workflowStart 可达
是否有孤立节点
```

### 16.3 变量引用检查

```text
["nodeId", "outputId"] 中 nodeId 是否存在
outputId 是否在该节点 outputs 中存在
fileUrlList 是否使用二维数组
answerNode 引用时 selectedTypeIndex 是否为 1
```

### 16.4 判断器检查

```text
ifElseList 是否为空
condition 是否是 AND / OR
variable 是否有值
condition 是否是合法枚举
valueType 是否是 input / reference
sourceHandle 是否使用 IF / ELSE / ELSE IF 1
```

### 16.5 代码节点检查

```text
代码 return 的字段是否全部声明为 outputs
outputs 的 id/key 是否和 return 字段一致
后续引用是否真实存在
```

### 16.6 AI 节点检查

```text
model 是否被编造
中间 AI 节点 isResponseAnswerText 是否为 false
最终是否用 answerNode 输出
userChatInput 是否引用正确
fileUrlList 是否引用正确
```

### 16.7 手动配置检查

```text
是否编造 datasetId
是否编造 API Key
是否编造数据库连接
是否编造 toolId/pluginId
是否漏写需要手动配置清单
```

---

## 17. 常见错误与修复

### 错误 1：readFiles 引用 text

错误：

```json
["read_files", "text"]
```

正确：

```json
["read_files", "system_text"]
```

### 错误 2：fileUrlList 写成一维数组

错误：

```json
["448745", "userFiles"]
```

正确：

```json
[["448745", "userFiles"]]
```

### 错误 3：判断器分支写 true/false

错误：

```text
check_valid-source-true
check_valid-source-false
```

正确：

```text
check_valid-source-IF
check_valid-source-ELSE
```

### 错误 4：分类节点分支使用 value

错误：

```text
classify-source-用户想翻译文本
```

正确：

```text
classify-source-translate
```

### 错误 5：AI 模型写死私有模型名

错误：

```json
"value": "qwen-plus-private-xxx"
```

正确：

```text
留空或提醒导入后手动选择。
```

### 错误 6：代码 return 字段没有 outputs

错误代码：

```javascript
return { is_valid: 'yes' };
```

但 outputs 没有：

```json
{
  "id": "is_valid",
  "key": "is_valid"
}
```

修复：

```text
补充 dynamic output。
```

### 错误 7：answerNode 引用了上游，但 selectedTypeIndex 还是 0

错误：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "value": ["ai", "answerText"],
  "selectedTypeIndex": 0
}
```

正确：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "value": ["ai", "answerText"],
  "selectedTypeIndex": 1
}
```

### 错误 8：知识库节点编造 datasets

错误：

```json
"value": [{ "datasetId": "fake_id" }]
```

正确：

```json
"value": []
```

并提醒：

```text
导入后手动绑定知识库。
```

---

## 18. 已验证的简单文本类模板结构

适用于：

```text
翻译助手
总结助手
润色助手
会议纪要整理助手
```

结构：

```text
userGuide
workflowStart
code 检查输入
ifElseNode 判断有效性
chatNode AI处理
answerNode 输出结果
answerNode 无效输入提示
```

节点连接：

```text
workflowStart → code
code → ifElseNode
ifElseNode IF → chatNode
ifElseNode ELSE → answer_invalid
chatNode → answer_final
```

判断逻辑：

```text
code.is_valid == yes → IF
否则 → ELSE
```

手动提醒：

```text
AI 模型需要导入后确认。
```

---

## 19. 输入校验代码模板

适合文本处理类工作流：

```javascript
function main(params) {
  const input =
    params.text ??
    params.user_input ??
    params.userChatInput ??
    params.data1 ??
    '';

  const raw = String(input).trim();

  if (!raw) {
    return {
      is_valid: 'no',
      cleaned_text: '',
      reason: 'empty'
    };
  }

  const compact = raw.replace(/\s+/g, '');

  if (/^\d+$/.test(compact)) {
    return {
      is_valid: 'no',
      cleaned_text: raw,
      reason: 'only_number'
    };
  }

  if (/^[\p{P}\p{S}]+$/u.test(compact)) {
    return {
      is_valid: 'no',
      cleaned_text: raw,
      reason: 'only_symbol'
    };
  }

  if (/^[A-Za-z]$/.test(compact)) {
    return {
      is_valid: 'no',
      cleaned_text: raw,
      reason: 'single_letter'
    };
  }

  if (/^[\u4e00-\u9fa5]$/.test(compact)) {
    return {
      is_valid: 'no',
      cleaned_text: raw,
      reason: 'single_chinese_char'
    };
  }

  return {
    is_valid: 'yes',
    cleaned_text: raw,
    reason: 'valid'
  };
}
```

对应 outputs 必须包含：

```text
is_valid
cleaned_text
reason
system_rawResponse
error
```

---

## 20. 翻译助手模板提示词

```text
你是一个专业翻译助手。

任务：
1. 自动判断用户输入语言。
2. 如果用户输入主要是中文，翻译成自然、准确的英文。
3. 如果用户输入主要是英文，翻译成自然、准确的中文。
4. 只输出译文，不要解释。
5. 不要输出 Markdown。
6. 不要添加多余说明。
7. 如果原文语法不完整，也尽量翻译成自然表达。
```

AI 节点 userChatInput 推荐引用：

```json
["check_input", "cleaned_text"]
```

---

## 21. 知识库问答模板

结构：

```text
workflowStart
→ datasetSearchNode
→ chatNode
→ answerNode
```

必须提醒：

```text
【需要手动配置】
1. 导入后请在知识库搜索节点中绑定知识库。
2. 导入后请在 AI 节点选择可用模型。
3. 如果需要 rerank，请手动配置 rerank 模型。
```

AI 提示词：

```text
你是知识库问答助手。
请优先根据知识库引用内容回答。
如果知识库中没有答案，请明确说明“知识库中未找到相关信息”，不要编造。
```

AI 节点 quoteQA 引用：

```json
["dataset_search", "quoteQA"]
```

---

## 22. 文件解析模板

结构：

```text
workflowStart(file)
→ readFiles
→ chatNode
→ answerNode
```

必须配置：

```text
workflowStart outputs 追加 userFiles
chatConfig.fileSelectConfig 打开文件上传
readFiles.fileUrlList = [["448745", "userFiles"]]
AI.userChatInput = ["read_files", "system_text"]
```

必须提醒：

```text
【需要手动配置】
1. 导入后请检查文件上传类型是否符合需求。
2. PDF/Word/Excel/CSV 的解析效果取决于平台文档解析能力。
3. 图片 OCR 不一定适合 readFiles，图片识别建议走视觉模型。
```

---

## 23. 图片识别模板

结构：

```text
workflowStart(image)
→ chatNode(vision)
→ answerNode
```

注意：

```text
图片可以直接传给支持视觉的 AI 节点。
不一定需要 readFiles。
```

必须配置：

```text
chatConfig.fileSelectConfig.canSelectImg = true
workflowStart outputs 追加 userFiles
AI.fileUrlList = [["448745", "userFiles"]]
AI.aiChatVision = true
```

必须提醒：

```text
导入后请确认选择的模型支持图片/视觉能力。
```

---

## 24. 票据识别模板

推荐结构：

```text
workflowStart(file/image)
→ code 分析后缀
→ ifElseNode 分流
   → 图片分支：AI 视觉提取
   → 文档分支：readFiles → AI 文本提取
→ code 合并结果
→ code 金额校验
→ answerNode 输出
```

如果要入库：

```text
→ HTTP/数据库节点
```

但必须提醒：

```text
【需要手动配置】
1. 数据库连接不能自动生成。
2. 存储过程名称、表名、字段名需要手动填写。
3. API Key / 数据库密码禁止写入 JSON。
4. 图片识别需要视觉模型。
5. 文档解析需要开启文件上传。
```

---

## 25. HTTP 请求模板

结构：

```text
workflowStart
→ code 整理请求参数
→ httpRequest468
→ answerNode 或 chatNode
```

必须提醒：

```text
【需要手动配置】
1. system_httpReqUrl：接口地址。
2. system_httpHeader：鉴权 Header。
3. system_httpJsonBody：请求体。
4. system_addOutputParam：响应字段提取。
5. API Key 不要写进公开 JSON。
```

---

## 26. 不允许做的事情

生成 JSON 时禁止：

```text
1. 凭空发明 flowNodeType。
2. 凭空发明 input key。
3. 凭空发明 output id。
4. 编造 datasetId。
5. 编造 toolId。
6. 编造 API Key。
7. 编造数据库连接。
8. 把所有节点都叫 node1/node2 且不声明含义。
9. 使用 true/false 作为 ifElse 分支 handle。
10. 使用 readFiles.text。
11. fileUrlList 使用一维引用。
12. answerNode 引用上游但 selectedTypeIndex 仍为 0。
13. 复杂需求没有模板也硬造完整 JSON。
14. 把 Markdown 解释和 JSON 混在一个 .json 文件里。
```

---

## 27. 推荐给其他 AI 的系统提示词

可以把下面内容作为“生成器 AI”的系统提示词核心：

```text
你是 FastGPT 工作流 JSON 生成器。

你的任务：
根据用户一句话需求，生成 FastGPT 工作流 JSON 或工作流模板。

最高规则：
1. 不能凭空创造 FastGPT 节点结构。
2. 只能使用已知 flowNodeType 和已验证节点母版。
3. 能自动生成的就生成。
4. 不能确定的内容必须列入【需要手动配置】。
5. 禁止编造 datasetId、toolId、API Key、数据库连接、私有模型 ID。
6. 如果需求超出模板能力，只生成最小骨架或设计方案，不硬造复杂 JSON。
7. 生成后必须自检节点 ID、连线、变量引用、分支 handle、代码 outputs、文件引用格式。

变量引用规则：
- 普通引用：["nodeId", "outputId"]
- 文件引用：[["nodeId", "userFiles"]]
- 文本插值：{{$nodeId.outputId$}}

分支规则：
- ifElseNode：nodeId-source-IF / nodeId-source-ELSE / nodeId-source-ELSE IF 1
- classifyQuestion：nodeId-source-${agents.key}

readFiles 输出：
- system_text
- system_rawResponse
- system_error_text

answerNode：
- 输入 key 是 text。
- 引用上游时 selectedTypeIndex 必须为 1。

最终输出：
1. JSON 文件或 JSON 文本。
2. 自动生成内容说明。
3. 需要手动配置清单。
4. 测试文本。
```

---

## 28. 版本差异提醒

FastGPT 不同版本可能改变：

```text
节点模板 inputs
outputs
version
chatConfig 字段
文件上传配置
AI 模型配置方式
知识库参数
```

如果导入后节点显示异常，优先操作：

```text
1. 在当前平台手动创建同类节点。
2. 导出 JSON。
3. 对比 inputs / outputs / version / chatConfig。
4. 再更新模板。
```

---

## 29. 最终总结

这个文件的核心不是“万能生成”，而是“可控生成”。

最终目标：

```text
一句话需求
→ 判断工作流类型
→ 匹配已验证模板
→ 生成 JSON 或模板
→ 标出必须手动配置项
→ 自检
→ 给测试文本
```

最重要原则：

> AI 只能根据源码真实节点和已验证模板生成工作流。不能确定的地方必须提醒手动填写，绝不能编造。
