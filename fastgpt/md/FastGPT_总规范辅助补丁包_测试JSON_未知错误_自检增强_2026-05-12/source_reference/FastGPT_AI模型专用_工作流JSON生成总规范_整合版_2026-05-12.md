# FastGPT 工作流 JSON 生成总规范（AI 模型专用整合版）

版本：2026-05-12 整合版  
用途：**给其他 AI 模型 / 代码生成器 / 自动化生成器使用**。  
定位：本文件不是面向普通用户的教程，而是面向 AI 的“生成规则 + 节点母版 + 拼接规则 + 自检回修协议 + 冲突说明”的统一规范。

---

## 0. 使用本文件的最高指令

AI 生成 FastGPT 工作流 JSON 时，必须遵守以下优先级：

1. **只使用本文档中真实出现过的 `flowNodeType`、`pluginId`、`toolId`、输入输出结构。**
2. **不得编造**不存在的节点类型，例如 `databaseNode`、`webhookNode`、`agentNode`、`fileJudgeNode`、`receiptExtractNode`。
3. **不得编造私有配置**，包括数据库账号密码、API Key、知识库 ID、真实 webhook 地址、真实应用 `pluginId`。
4. 生成复杂工作流时，优先使用“已测试节点母版 + 明确连线规则 + 自检清单”。
5. 不确定的内容必须输出到【需要手动配置】或【需要再次导出母版确认】，不能硬猜。
6. 工作流 JSON 生成后，必须进行静态自检：节点 ID、边、handle、变量引用、输出 ID、私有配置、文件上传、错误捕获、循环子节点。

---

## 1. 本整合版替代的原始文件

本文件把以下资料合并到一个 AI 可直接读取的统一文件中：

- `FastGPT_单节点母版与工作流拼接规则_给AI模型使用_2026-05-11_整改版.md`
- `FastGPT_工作流JSON错误自检与回修协议_给AI模型使用_2026-05-11.md`
- `FastGPT_工作流JSON生成通用规则_给AI模型使用_2026-05-11_源码约束整改版.md`
- `FastGPT_JSON自检清单_2026-05-12.txt`
- `FastGPT_单节点母版大全_已测试与注意事项_2026-05-12.md`
- `FastGPT_单节点母版库_已测试_2026-05-12.json`
- `FastGPT_工作流JSON生成通用规则_帮助总结_2026-05-11.txt`

合并原则：

- 把同一个节点的**结构、输入、输出、连线、注意事项、自检规则**放在同一节。
- 把通用规则放在前面，把节点母版放在中间，把自检和回修协议放在后面。
- 保留所有关键冲突和已发现坑点。
- 把“给用户看的解释”改写成“给 AI 模型执行的规则”。

---

## 2. FastGPT 工作流 JSON 顶层结构

标准可导入结构：

```json
{
  "nodes": [],
  "edges": [],
  "chatConfig": {}
}
```

顶层要求：

| 字段 | 要求 |
|---|---|
| `nodes` | 必须是数组 |
| `edges` | 必须是数组 |
| `chatConfig` | 必须是对象，可为空对象 |
| `nodeId` | 全局唯一，不得重复 |
| `flowNodeType` | 必须来自已知真实节点类型 |
| `position` | 每个节点建议保留 |
| `inputs` / `outputs` | 即使为空，也应保留数组 |

禁止写死或编造的内容：

```text
chatConfig._id
真实 appId / userId / teamId
真实 datasetId
真实 API Key / Token
真实数据库账号密码
真实 webhook 地址
用户私有应用 appModule.pluginId
```

例外：**系统工具的固定 `pluginId/toolId` 可以复用**，例如 `systemTool-fetchUrl`、`systemTool-databaseConnection`。但 `appModule.pluginId` 不是系统固定 ID，必须来自用户真实导出。

---

## 3. 变量引用规则

### 3.1 input.value 中的节点输出引用

格式：

```json
["节点ID", "输出ID"]
```

例：

```json
["448745", "userChatInput"]
```

要求：

- 第一个元素必须是已存在的 `nodeId` 或特殊全局变量节点 `VARIABLE_NODE_ID`。
- 第二个元素必须是该节点 `outputs.id` 中真实存在的输出 ID。
- 不能只看 `outputs.key` 或 UI 显示名。

### 3.2 文件列表引用

文件上传 / 文件链接列表必须是二维数组：

```json
[["流程开始节点ID", "userFiles"]]
```

错误写法：

```json
["流程开始节点ID", "userFiles"]
```

注意：如果 `workflowStart.outputs` 里没有 `userFiles`，任何 `[[workflowStart, userFiles]]` 都是悬空引用。

### 3.3 文本插值引用

在 `answerNode.text`、`textEditor`、`systemPrompt`、`formInput.description` 等文本区域中，使用：

```text
{{$节点ID.输出ID$}}
```

例：

```text
{{$ai_translate.answerText$}}
{{$read_files.system_text$}}
{{$VARIABLE_NODE_ID.cTime$}}
```

要求：同样必须检查 `输出ID` 是否真实存在于目标节点 `outputs.id`。

### 3.4 全局变量特殊节点

全局变量使用：

```text
VARIABLE_NODE_ID
```

引用：

```text
{{$VARIABLE_NODE_ID.userId$}}
{{$VARIABLE_NODE_ID.appId$}}
{{$VARIABLE_NODE_ID.cTime$}}
```

在 `variableUpdate.updateList` 中也用 `VARIABLE_NODE_ID` 表示全局变量目标或来源。

---

## 4. edges 连线和 handle 规则

### 4.1 普通连线

```json
{
  "source": "源节点ID",
  "target": "目标节点ID",
  "sourceHandle": "源节点ID-source-right",
  "targetHandle": "目标节点ID-target-left"
}
```

### 4.2 判断器 ifElseNode 分支

判断器分支不是 `true/false`。正确格式：

```text
节点ID-source-IF
节点ID-source-ELSE IF 1
节点ID-source-ELSE IF 2
节点ID-source-ELSE
```

### 4.3 用户选择 userSelect 分支

分支 handle 由选项 key 决定：

```text
用户选择节点ID-source-选项key
```

如果 `userSelectOptions` 为：

```json
[
  {"value": "选项1", "key": "option1"},
  {"value": "选项2", "key": "option2"}
]
```

则 edges 应使用：

```text
userSelectNode-source-option1
userSelectNode-source-option2
```

### 4.4 问题分类 classifyQuestion 分支

分支 handle 使用 `agents.key`，不是 `agents.value`。

### 4.5 工具调用 tools 挂载

工具调用节点挂载工具使用特殊边，不是普通边：

```json
{
  "sourceHandle": "selectedTools",
  "targetHandle": "selectedTools"
}
```

典型结构：

```text
流程开始 → 工具调用 → 指定回复
工具调用 --selectedTools--> AI对话/知识库/工具节点
工具内部流程 → 工具调用终止 stopTool
```

### 4.6 catchError 错误捕获分支

当节点 `catchError: true` 且接错误分支时，错误出口 handle：

```text
节点ID-source_catch-right
```

普通成功出口仍是：

```text
节点ID-source-right
```

---

## 5. 节点状态总表

| key | 节点 | flowNodeType | pluginId | 主要 inputs | 主要 outputs |
| --- | --- | --- | --- | --- | --- |
| userGuide | 系统配置 | userGuide |  | welcomeText, variables, questionGuide, tts, whisper, scheduleTrigger |  |
| workflowStart | 流程开始 | workflowStart |  | userChatInput | userChatInput |
| answerNode | 指定回复 | answerNode |  | text |  |
| code | 代码运行 | code |  | system_addInputParam, data1, data2, codeType, code | system_addOutputParam, system_rawResponse, qLUQfhG0ILRX, gR0mkQpJ4Og8, error |
| ifElseNode | 判断器 | ifElseNode |  | ifElseList | ifElseResult |
| chatNode | AI 对话 | chatNode |  | model, temperature, maxToken, isResponseAnswerText, aiChatQuoteRole, quoteTemplate, quotePrompt, aiChatVision… | history, answerText, reasoningText, system_error_text |
| datasetSearchNode | 知识库搜索 | datasetSearchNode |  | datasets, similarity, limit, searchMode, embeddingWeight, usingReRank, rerankModel, rerankWeight… | quoteQA, system_error_text |
| classifyQuestion | 问题分类 | classifyQuestion |  | model, systemPrompt, history, userChatInput, agents | cqResult |
| contentExtract | 文本内容提取 | contentExtract |  | model, description, history, content, extractKeys | success, fields, system_error_text |
| textEditor | 文本拼接 | textEditor |  | system_textareaInput | system_text |
| readFiles | 文档解析 | readFiles |  | fileUrlList | system_text, system_rawResponse, system_error_text |
| httpRequest468 | HTTP 请求 | httpRequest468 |  | system_addInputParam, system_httpMethod, system_httpTimeout, system_httpReqUrl, system_header_secret, system_httpHeader, system_httpParams, system_httpJsonBody… | system_addOutputParam, httpRawResponse, error |
| tools | 工具调用 | tools |  | model, temperature, maxToken, isResponseAnswerText, aiChatVision, aiChatReasoning, aiChatTopP, aiChatStopSign… | answerText, system_error_text |
| stopTool | 工具调用终止 | stopTool |  |  |  |
| toolParams | 自定义工具变量（工具调用辅助节点） | toolParams |  | name | name |
| databaseConnection | 数据库连接 | tool | systemTool-databaseConnection | system_input_config, sql | result, system_error_text |
| fetchUrl | 网页内容抓取 | tool | systemTool-fetchUrl | url | title, result, system_error_text |
| weworkWebhook | 企业微信 webhook | tool | systemTool-WeWorkWebhook | webhookUrl, message | system_error_text |
| dingTalkWebhook | 钉钉 webhook | tool | systemTool-DingTalkWebhook | webhookUrl, secret, message | system_error_text |
| feishuWebhook | 飞书 webhook | tool | systemTool-feishu | content, hook_url | result, system_error_text |
| userSelect | 用户选择 | userSelect |  | description, userSelectOptions | selectResult |
| formInput | 表单输入（全类型） | formInput |  | description, userInputForms | formInputResult, 文本, 密码, 这是数字输入框, 单选, 多选克框, 开关, 时间点… |
| variableUpdate_1 | 变量更新 #1 | variableUpdate |  | updateList |  |
| variableUpdate_2 | 变量更新 #2 | variableUpdate |  | updateList |  |
| loop | 批量执行 | loop |  | loopInputArray, childrenNodeIdList, nodeWidth, nodeHeight, loopNodeInputHeight | loopArray |
| loopStart | 循环开始 | loopStart |  | loopStartInput, loopStartIndex | loopStartIndex, loopStartInput |
| loopEnd | 循环结束 | loopEnd |  | loopEndInput |  |
| appModule_1 | 应用调用 appModule #1 | appModule | 69ef2881b180ca8df8d5c846 | system_forbid_stream, history, userChatInput | history, answerText, system_error_text |
| appModule_2 | 应用调用 appModule #2 | appModule | 69fd3ae6b180ca8df8df0bc0 | system_forbid_stream, history, userChatInput | history, answerText, system_error_text |

---

## 6. 节点母版与生成规则

### 6.1 系统配置 `userGuide`

用途：保存开场白、聊天变量、问题引导、语音配置、文件上传配置、定时触发占位等。通常不参与业务连线。

核心输入：

```text
welcomeText
variables
questionGuide
tts
whisper
scheduleTrigger
```

规则：

- `userGuide` 可保留在 `nodes` 中。
- 不要把业务逻辑写到 `userGuide`。
- 自动执行不在 `userGuide`，而在 `chatConfig.autoExecute`。
- 定时触发配置在 `chatConfig.scheduledTriggerConfig` 和/或 `userGuide.scheduleTrigger` 相关区域，生成时不要编造 cron 逻辑。

---

### 6.2 流程开始 `workflowStart`

用途：接收用户输入。

标准文本输出：

```text
userChatInput
```

注意：

- 纯文本版只有 `userChatInput`。
- 如果要支持文件上传，必须确认 `workflowStart.outputs` 有 `userFiles`。
- 旧测试文件里出现过 `fileUrlList -> [[workflowStart, userFiles]]`，但 `workflowStart` 没有 `userFiles`，这是冲突，最终模板必须修正。

---

### 6.3 指定回复 `answerNode`

用途：最终回复、提示、固定文本输出。

核心输入：

```text
text
```

规则：

- 可以写固定文本。
- 可以用 `{{$nodeId.outputId$}}` 插值。
- 非字符串传入时平台可能自动转字符串。
- 不要引用不存在的输出。
- 如果上游是 webhook 且没有正常输出，就写固定成功提示。

---

### 6.4 AI 对话 `chatNode`

用途：大模型回答、总结、提取、翻译、推理。

常见输入：

```text
model
systemPrompt
history
quoteQA
fileUrlList
userChatInput
isResponseAnswerText
aiChatVision
aiChatReasoning
```

常见输出：

```text
history
answerText
reasoningText（可能 invalid）
system_error_text
```

规则：

- 模型名不能强行写死为用户平台未配置的模型。
- 若引用文件，需要 `fileUrlList` 使用二维数组，并确认上游存在 `userFiles`。
- 最终回复一般通过 `answerNode` 引用 `answerText`。
- 中间 AI 节点是否直接流式输出，视业务设置 `isResponseAnswerText`。

---

### 6.5 知识库搜索 `datasetSearchNode`

用途：从知识库检索引用内容。

关键输入：

```text
datasets
similarity
limit
searchMode
userChatInput
collectionFilterMatch
```

输出：

```text
quoteQA
system_error_text
```

规则：

- `datasets` 里的 `datasetId` 不能编造。
- 没有真实知识库时，必须列入【需要手动配置】。
- 下游 AI 对话通常引用 `quoteQA`。

---

### 6.6 问题分类 `classifyQuestion`

用途：根据用户输入分类并走不同分支。

关键输入：

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

分支规则：

```text
sourceHandle = classifyNodeId-source-agents.key
```

禁止使用 `agents.value` 或中文分类名作为 handle。

---

### 6.7 文本内容提取 `contentExtract`

用途：从文本中提取指定字段。

关键输入：

```text
model
description
history
content
extractKeys
```

输出：

```text
success
fields
system_error_text
```

规则：

- `extractKeys` 是提取字段配置，不能随意空写后假装完成复杂任务。
- `fields` 是 JSON 字符串，不一定是对象。
- 需要 JSON 解析时，后面接代码节点。

---

### 6.8 文本拼接 `textEditor`

用途：拼接、整理、模板化文本。

输入：

```text
system_textareaInput
```

输出：

```text
system_text
```

规则：

- 适合把多个变量用 `{{$nodeId.outputId$}}` 插入到一段文本里。
- 下游引用输出必须用 `system_text`。

---

### 6.9 文档解析 `readFiles`

用途：解析用户上传文档。

输入：

```text
fileUrlList
```

输出：

```text
system_text
system_rawResponse
system_error_text
```

规则：

- `fileUrlList` 必须是二维数组，如 `[["start", "userFiles"]]`。
- 下游引用文档解析文本用 `system_text`，不是 `text`、`content`、`rawText`。

---

### 6.10 HTTP 请求 `httpRequest468`

用途：调用外部 HTTP API。

关键输入：

```text
system_addInputParam
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

输出：

```text
system_addOutputParam
httpRawResponse
error
```

规则：

- URL、Header、Token 不能写死真实值。
- 若需要提取响应字段，配置 `system_addOutputParam`。
- 错误输出是 `error`，不是 `system_error_text`。

---

### 6.11 代码运行 `code`

用途：复杂数据处理、格式清洗、生成 SQL、转换数组等。

关键输入：

```text
system_addInputParam
自定义输入参数
codeType
code
```

输出：

```text
system_addOutputParam
system_rawResponse
动态输出字段
error
```

规则：

- 代码 `return` 的字段必须在 `outputs` 里声明动态输出。
- 下游引用时以 `outputs.id` 为准，不一定等于 return key。
- JS 代码通常形如：

```javascript
function main(params) {
  return { result: "..." }
}
```

---

### 6.12 判断器 `ifElseNode`

用途：条件分支。

输入：

```text
ifElseList
```

输出：

```text
ifElseResult
```

分支 handle：

```text
节点ID-source-IF
节点ID-source-ELSE IF 1
节点ID-source-ELSE
```

条件值类型常见：

```text
input
reference
```

规则：

- 不要写 `true/false` handle。
- `ELSE IF 1` 中间有空格，按导出结构保留。

---

### 6.13 数据库连接 `tool / systemTool-databaseConnection`

数据库连接不是 `databaseNode`，而是系统工具：

```json
{
  "flowNodeType": "tool",
  "pluginId": "systemTool-databaseConnection",
  "toolConfig": {
    "systemTool": {
      "toolId": "systemTool-databaseConnection"
    }
  }
}
```

输入分两类：

1. `system_input_config.inputList`：数据库连接配置
2. `sql`：SQL 语句

连接配置字段：

```text
databaseType: MySQL / PostgreSQL / Microsoft SQL Server
host
port
databaseName
user
password
```

SQL 输入：

```text
sql
```

输出：

```text
result
system_error_text
```

规则：

- 不要继续用 HTTP 请求伪装数据库模块。
- 真实数据库 host/user/password 不能写死。
- 推荐结构：`代码生成 SQL → 数据库连接 → 指定回复 result`。
- SQL 结果格式仍建议进一步实测。

---

### 6.14 工具调用 `tools`

用途：由 AI 自主决定是否调用挂载工具。

核心：

```text
flowNodeType: tools
avatar: core/workflow/template/toolCall
```

输出：

```text
answerText
system_error_text
```

挂载规则：

```json
{
  "sourceHandle": "selectedTools",
  "targetHandle": "selectedTools"
}
```

规则：

- 被挂载的节点不一定是普通流程运行成功，只能说明“可被 tools 挂载”。
- 作为工具内部流程时，通常最后接 `stopTool`。
- 测试文件中出现过 `fileUrlList -> userFiles` 悬空引用，正式模板要修正。

---

### 6.15 工具调用终止 `stopTool`

用途：工具内部执行到这里时强制结束本次工具调用。

结构：

```text
flowNodeType: stopTool
inputs: []
outputs: []
```

规则：

- 只能作为工具调用体系内的终止节点使用。
- 不要期待它有输出。

---

### 6.16 自定义工具变量 `toolParams`（特殊记录）

出现位置：工具调用体系。

结构：

```text
flowNodeType: toolParams
avatar: core/workflow/template/toolParams
```

规则：

- 左侧普通节点列表里未确认有独立入口。
- 不要作为普通主流程节点强行生成。
- 仅作为工具调用辅助结构记录。

---

### 6.17 用户选择 `userSelect`

用途：对话中展示多个按钮/选项，用户选择后进入不同分支。

输入：

```text
description
userSelectOptions
```

`userSelectOptions` 示例：

```json
[
  {"value": "这是选项1", "key": "option1"},
  {"value": "这是选项2", "key": "option2"}
]
```

输出：

```text
selectResult
```

分支规则：

```text
sourceHandle = userSelectNodeId-source-选项key
```

规则：

- `value` 是显示文本。
- `key` 决定分支 handle。
- 每个选项最好都有对应 edge。
- 不要编造 `choice`、`selected`、`optionValue`。

---

### 6.18 表单输入 `formInput`

用途：引导用户填写多个字段。

输入：

```text
description
userInputForms
```

输出：

```text
formInputResult
每个字段的单独输出
```

#### 6.18.1 表单说明支持变量

```text
{{$448745.userChatInput$}}
```

#### 6.18.2 每个字段都会生成输出

- `formInputResult`：完整对象
- 每个字段：单独输出

下游引用：

```text
{{$表单节点ID.formInputResult$}}
{{$表单节点ID.字段输出ID$}}
```

#### 6.18.3 已确认字段类型

| UI 名称 | type | valueType | 关键字段 |
|---|---|---|---|
| 文本输入框 | `input` | `string` | `defaultValue`, `maxLength` |
| 密码 | `password` | `string` | `defaultValue`, `minLength` |
| 数字输入框 | `numberInput` | `number` | `defaultValue`, `min`, `max` |
| 单选框 | `select` | `string` | `list`, `defaultValue` |
| 多选框 | `multipleSelect` | `arrayString` | `list`, `defaultValue` 数组 |
| 开关 | `switch` | `boolean` | `defaultValue` true/false |
| 时间点 | `timePointSelect` | `string` | `timeGranularity`, `timeRangeStart`, `timeRangeEnd` |
| 时间范围 | `timeRangeSelect` | `arrayString` | `defaultValue` 开始/结束数组 |
| 文件上传 | `fileSelect` | `arrayString` | `canLocalUpload`, `canUrlUpload`, `canSelectFile`, `maxFiles` |
| 对话模型选择 | `selectLLMModel` | `string` | `defaultValue` 模型名 |

#### 6.18.4 必填开关

```text
required: true  → 必填
required: false → 非必填
```

#### 6.18.5 时间粒度

已确认：

```text
hour
minute
second
```

时间格式统一建议：

```text
YYYY-MM-DD HH:mm:ss
```

#### 6.18.6 字段改名冲突

如果改字段名，可能出现：

```json
{
  "id": "文本",
  "key": "时间分钟",
  "label": "时间分钟"
}
```

下游引用仍必须看 `outputs.id`：

```text
{{$表单节点ID.文本$}}
```

不能只看 `userInputForms.key`。

---

### 6.19 变量更新 `variableUpdate`

用途：更新指定节点输出值或全局变量。

核心：

```text
flowNodeType: variableUpdate
showStatus: false
outputs: []
```

输入：

```text
updateList
```

更新项结构：

```json
{
  "variable": ["目标节点ID", "目标输出ID或变量名"],
  "value": ["来源节点ID", "来源输出ID或固定值"],
  "valueType": "string",
  "renderType": "reference"
}
```

固定值：

```json
{
  "variable": ["VARIABLE_NODE_ID", "appId"],
  "value": ["", "这是值"],
  "valueType": "string",
  "renderType": "input"
}
```

规则：

- `variableUpdate` 没有 outputs，不能被下游引用输出。
- 更新全局变量时目标节点 ID 是 `VARIABLE_NODE_ID`。
- `renderType: reference` 表示来源是引用。
- `renderType: input` 表示来源是固定值。
- 验证更新效果时，下游必须引用被更新的目标变量。

---

### 6.20 批量执行 `loop / loopStart / loopEnd`

用途：遍历数组，对每个元素执行内部子流程。

必须成套生成：

```text
loop 父节点
loopStart 子节点
loopEnd 子节点
循环体内部节点
```

`loop` 父节点关键输入：

```text
loopInputArray
childrenNodeIdList
nodeWidth
nodeHeight
loopNodeInputHeight
```

输出：

```text
loopArray
```

规则：

- 循环内部节点必须有 `parentNodeId = loop节点ID`。
- `loop.childrenNodeIdList` 必须包含内部子节点 ID。
- `loopStart` 输出：
  - `loopStartIndex`
  - `loopStartInput`
- `loopEnd` 输入：
  - `loopEndInput`
- `loopEndInput` 是每次循环收集进 `loopArray` 的值。
- 循环外引用结果：

```text
{{$loop节点ID.loopArray$}}
```

复杂循环流程应谨慎生成，优先生成最小循环模板。

---

### 6.21 网页内容抓取 `tool / systemTool-fetchUrl`

用途：抓取静态网页内容并输出 Markdown。

核心：

```json
{
  "flowNodeType": "tool",
  "pluginId": "systemTool-fetchUrl",
  "toolConfig": {
    "systemTool": {"toolId": "systemTool-fetchUrl"}
  }
}
```

输入：

```text
url
```

输出：

```text
title
result
system_error_text
```

规则：

- 只支持静态网站抓取。
- `catchError: true` 时可接错误分支。
- 成功分支引用 `title` / `result`。
- 错误分支引用 `system_error_text`。

---

### 6.22 企业微信 webhook `tool / systemTool-WeWorkWebhook`

用途：向企业微信群机器人发送消息。

核心：

```json
{
  "flowNodeType": "tool",
  "pluginId": "systemTool-WeWorkWebhook",
  "toolConfig": {
    "systemTool": {"toolId": "systemTool-WeWorkWebhook"}
  }
}
```

输入：

```text
webhookUrl
message
```

输出：

```text
system_error_text
```

规则：

- `webhookUrl` 和 `message` 都支持 `input/reference`。
- 没有正常 `result` 输出。
- 成功后指定回复写固定文本，例如“企业微信消息已发送”。
- webhook 地址不能写死真实值。

---

### 6.23 钉钉 webhook `tool / systemTool-DingTalkWebhook`

用途：向钉钉机器人发送消息。

核心：

```json
{
  "flowNodeType": "tool",
  "pluginId": "systemTool-DingTalkWebhook",
  "toolConfig": {
    "systemTool": {"toolId": "systemTool-DingTalkWebhook"}
  }
}
```

输入：

```text
webhookUrl
secret
message
```

说明：

- `secret` 是“加签值”。
- 三个输入都支持 `input/reference`。
- 三个输入都是必填。

输出：

```text
system_error_text
```

规则：

- 没有正常 `result` 输出。
- 不要写死真实 webhookUrl 或 secret。
- 成功后指定回复写固定文本。

---

### 6.24 飞书 webhook `tool / systemTool-feishu`

用途：向飞书机器人发送消息。

核心：

```json
{
  "flowNodeType": "tool",
  "pluginId": "systemTool-feishu",
  "toolConfig": {
    "systemTool": {"toolId": "systemTool-feishu"}
  }
}
```

输入：

```text
content
hook_url
```

输出：

```text
result
system_error_text
```

规则：

- 飞书机器人地址字段叫 `hook_url`，不是 `webhookUrl`。
- `content` 支持 `input/reference`。
- 当前导出里 `hook_url` 只显示 `input`。
- 飞书有正常输出 `result`，可以在指定回复引用。

---

### 6.25 应用调用 / Agent 调用 `appModule`

用途：在当前工作流中调用另一个 FastGPT 应用 / Agent / 工作流。

核心：

```json
{
  "flowNodeType": "appModule",
  "avatar": "core/app/type/workflowFill",
  "pluginId": "真实应用ID"
}
```

输入：

```text
system_forbid_stream
history
userChatInput
```

输出：

```text
history
answerText
system_error_text
```

规则：

- `pluginId` 是被调用应用的真实 ID，不能编造。
- `system_forbid_stream: true` 表示禁用嵌套应用流式输出。
- 最终回复通常引用 `answerText`。
- `catchError` 可为 true/false，但错误分支仍建议单独测试。
- 适合“主流程调用子应用”的场景。

---

### 6.26 自动执行 `chatConfig.autoExecute`

自动执行不是节点，而是 `chatConfig` 字段：

```json
{
  "autoExecute": {
    "open": true,
    "defaultPrompt": ""
  }
}
```

规则：

- 不要写进 `nodes`。
- 不要放到 `userGuide`。
- `open: true` 表示启用自动执行。

---

## 7. 系统工具节点差异表

| 节点 | flowNodeType | pluginId/toolId | 输入 | 正常输出 | 错误输出 |
|---|---|---|---|---|---|
| 数据库连接 | `tool` | `systemTool-databaseConnection` | `system_input_config`, `sql` | `result` | `system_error_text` |
| 网页内容抓取 | `tool` | `systemTool-fetchUrl` | `url` | `title`, `result` | `system_error_text` |
| 企业微信 webhook | `tool` | `systemTool-WeWorkWebhook` | `webhookUrl`, `message` | 无 | `system_error_text` |
| 钉钉 webhook | `tool` | `systemTool-DingTalkWebhook` | `webhookUrl`, `secret`, `message` | 无 | `system_error_text` |
| 飞书 webhook | `tool` | `systemTool-feishu` | `content`, `hook_url` | `result` | `system_error_text` |

---

## 8. 生成工作流时的选择策略

### A 类：可直接生成完整 JSON

适合：

```text
固定回复助手
翻译助手
总结助手
简单 AI 对话助手
简单判断分支助手
简单表单收集助手
简单用户选择助手
```

### B 类：可生成模板，但必须手动配置

适合：

```text
知识库问答
HTTP API 调用
网页抓取
数据库执行 SQL
webhook 通知
应用调用 appModule
文件解析
```

必须列出：

```text
需要手动配置模型/知识库/API URL/webhook/数据库/appModule.pluginId
```

### C 类：只能生成半成品或设计方案

适合：

```text
复杂数据库入库
复杂循环批处理
多层工具调用
多子应用编排
私有工具/我的工具
复杂鉴权 API
```

必须避免：

```text
编造 toolId/pluginId/datasetId/secret/password
```

---

## 9. 静态自检清单

生成 JSON 后，AI 必须逐项检查：

1. `nodes`、`edges`、`chatConfig` 是否存在。
2. `nodeId` 是否全局唯一。
3. `flowNodeType` 是否真实存在。
4. `edges.source` / `edges.target` 是否都存在。
5. 普通边 handle 是否为 `sourceId-source-right` / `targetId-target-left`。
6. 判断器分支是否使用 `IF / ELSE IF 1 / ELSE`。
7. 用户选择分支是否使用 `userSelectId-source-选项key`。
8. 工具调用挂载是否使用 `selectedTools`。
9. catchError 错误分支是否使用 `nodeId-source_catch-right`。
10. 所有 `input.value = [nodeId, outputId]` 是否引用真实输出。
11. 所有 `{{$nodeId.outputId$}}` 是否引用真实输出。
12. `workflowStart` 没有 `userFiles` 时，不得引用 `userFiles`。
13. `variableUpdate` 没有 outputs，不得引用它输出。
14. `formInput` 字段引用以 `outputs.id` 为准。
15. `loop` 子节点是否有 `parentNodeId`。
16. `loop.childrenNodeIdList` 是否包含所有内部节点。
17. `loopStart` / `loopEnd` 是否成套存在。
18. 企业微信/钉钉 webhook 不得引用 `result`。
19. 飞书 webhook 可以引用 `result`。
20. `appModule.pluginId` 是否来自真实导出，不能编造。
21. 数据库、webhook、API、secret、password 是否含真实私密值；如有，应改为占位或手动配置说明。
22. 代码节点 return 字段是否在 outputs 声明。
23. HTTP 节点错误输出是 `error`，不是 `system_error_text`。
24. readFiles 输出文本是 `system_text`。
25. contentExtract 输出字段结果是 `fields`。

---

## 10. 错误自检与回修协议

### 10.1 错误等级

#### S1 致命结构错误

包括：

```text
JSON 语法错误
顶层缺 nodes/edges/chatConfig
nodes 或 edges 不是数组
nodeId 重复
flowNodeType 不存在
edge 指向不存在节点
```

处理：必须自动修复。不能确定时移除错误边或标记手动处理，不得编造。

#### S2 运行链路错误

包括：

```text
变量引用不存在
outputId 不存在
代码 return 未声明 outputs
分支 handle 错误
fileUrlList 一维数组
answerNode 引用错误
```

处理：优先自动局部修复。

#### S3 平台配置错误

包括：

```text
模型不可用
知识库未绑定
API URL/Token 未填写
数据库连接未配置
webhook 未配置
appModule.pluginId 不存在
```

处理：不能编造，列入【需要手动配置】。

#### S4 逻辑风险错误

包括：

```text
提示词说支持批量但流程只处理单条
代码只处理 files[0] 但 maxFiles > 1
中间 AI 节点打开流输出导致提前回复
最终没有 answerNode
```

处理：可给建议；不确定业务意图时不要强行改。

### 10.2 回修流程

```text
读取错误信息
→ 判断错误等级
→ 定位节点/输入/输出/边/chatConfig
→ 判断能否自动修复
→ 只修相关局部
→ 再次执行静态自检
→ 输出修复后的 JSON 或手动配置清单
```

### 10.3 禁止的回修行为

```text
不允许为了修复而重写整个工作流
不允许编造缺失配置
不允许删除业务必要节点后假装成功
不允许把错误归因给用户但不给定位
```

---

## 11. 必须保留的冲突与注意事项

1. 工具调用测试中出现的 `fileUrlList -> userFiles`，如果 `workflowStart` 没有 `userFiles` 输出，必须修正。
2. `toolParams` 只作为工具调用辅助结构记录，不当作普通主流程节点。
3. `formInput` 修改字段名后，`outputs.id` 可能残留旧值；引用必须以 `outputs.id` 为准。
4. 企业微信和钉钉 webhook 没有正常 `result` 输出。
5. 飞书 webhook 有 `result` 输出。
6. 数据库连接是 `flowNodeType: tool`，不是数据库专用节点。
7. 网页内容抓取是 `flowNodeType: tool`，不是 `fetchUrlNode`。
8. `appModule.pluginId` 是真实应用 ID，不可凭空生成。
9. `loop` 内部节点必须同时满足 `parentNodeId` 和 `childrenNodeIdList`。
10. `variableUpdate` 没有输出，不可引用。
11. `HTTP` 错误输出是 `error`，系统工具多数是 `system_error_text`。
12. 自动执行属于 `chatConfig.autoExecute`，不是节点。

---

## 12. 推荐输出格式（给 AI 模型）

当用户要求生成 FastGPT 工作流 JSON 时，AI 应输出：

```text
【工作流类型】
【节点结构】
【需要手动配置】
【JSON】
【自检结果】
```

如果用户要求直接给文件，可只生成文件并简单说明：

```text
已生成整合版 JSON/MD/TXT 文件。
需要手动配置项：...
```

---

## 13. 完整机器可读节点母版库

以下 JSON 来自已测试母版库。复用时必须重新生成 `nodeId`，同步修改 `edges`、变量引用、`childrenNodeIdList`、`parentNodeId`。

```json
{
  "name": "FastGPT 单节点母版库（已测试+注意事项）",
  "created_at": "2026-05-12",
  "notes": [
    "nodeId 均来自测试导出文件，复用时应重新生成唯一 nodeId，并同步 edges 与引用。",
    "pluginId / toolId / appModule.pluginId 不可凭空编造；系统工具的 pluginId/toolId 可复用，appModule.pluginId 必须来自用户真实应用。",
    "文件内保留了测试值，生成正式工作流时需要替换占位、删除不必要测试内容。"
  ],
  "templates": [
    {
      "key": "userGuide",
      "title": "系统配置",
      "source_file": "数据库.json",
      "flowNodeType": "userGuide",
      "pluginId": null,
      "node": {
        "nodeId": "userGuide",
        "name": "common:core.module.template.system_config",
        "intro": "common:core.module.template.system_config_info",
        "avatar": "core/workflow/template/systemConfig",
        "flowNodeType": "userGuide",
        "position": {
          "x": 262.2732338817093,
          "y": -476.00241136598146
        },
        "version": "481",
        "inputs": [
          {
            "key": "welcomeText",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "string",
            "label": "core.app.Welcome Text",
            "value": ""
          },
          {
            "key": "variables",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "core.app.Chat Variable",
            "value": []
          },
          {
            "key": "questionGuide",
            "valueType": "any",
            "renderTypeList": [
              "hidden"
            ],
            "label": "core.app.Question Guide",
            "value": {
              "open": false
            }
          },
          {
            "key": "tts",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "",
            "value": {
              "type": "web"
            }
          },
          {
            "key": "whisper",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "",
            "value": {
              "open": false,
              "autoSend": false,
              "autoTTSResponse": false
            }
          },
          {
            "key": "scheduleTrigger",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "",
            "value": null
          }
        ],
        "outputs": []
      }
    },
    {
      "key": "workflowStart",
      "title": "流程开始",
      "source_file": "数据库.json",
      "flowNodeType": "workflowStart",
      "pluginId": null,
      "node": {
        "nodeId": "448745",
        "name": "common:core.module.template.work_start",
        "intro": "",
        "avatar": "core/workflow/template/workflowStart",
        "flowNodeType": "workflowStart",
        "position": {
          "x": 795,
          "y": -345
        },
        "version": "481",
        "inputs": [
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "workflow:user_question",
            "required": true,
            "toolDescription": "用户问题",
            "debugLabel": ""
          }
        ],
        "outputs": [
          {
            "id": "userChatInput",
            "key": "userChatInput",
            "label": "common:core.module.input.label.user question",
            "type": "static",
            "valueType": "string",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "answerNode",
      "title": "指定回复",
      "source_file": "数据库.json",
      "flowNodeType": "answerNode",
      "pluginId": null,
      "node": {
        "nodeId": "tUprh51j3O7zOvXX",
        "name": "指定回复",
        "intro": "该模块可以直接回复一段指定的内容。常用于引导、提示。非字符串内容传入时，会转成字符串进行输出。",
        "avatar": "core/workflow/template/reply",
        "flowNodeType": "answerNode",
        "position": {
          "x": 1859,
          "y": -345
        },
        "inputs": [
          {
            "key": "text",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "valueType": "any",
            "required": true,
            "isRichText": false,
            "maxLength": 100000,
            "label": "回复的内容",
            "description": "可以使用 \\n 来实现连续换行。\n可以通过外部模块输入实现回复，外部模块输入时会覆盖当前填写的内容。\n如传入非字符串类型数据将会自动转成字符串",
            "placeholder": "可以使用 \\n 来实现连续换行。\n可以通过外部模块输入实现回复，外部模块输入时会覆盖当前填写的内容。\n如传入非字符串类型数据将会自动转成字符串",
            "value": ""
          }
        ],
        "outputs": []
      }
    },
    {
      "key": "code",
      "title": "代码运行",
      "source_file": "工具调用(1).json",
      "flowNodeType": "code",
      "pluginId": null,
      "node": {
        "nodeId": "r4NQOYWEOvP0iaNO",
        "name": "代码运行",
        "intro": "执行一段简单的脚本代码，通常用于进行复杂的数据处理。",
        "avatar": "core/workflow/template/codeRun",
        "flowNodeType": "code",
        "showStatus": true,
        "position": {
          "x": 1460,
          "y": 734
        },
        "inputs": [
          {
            "key": "system_addInputParam",
            "renderTypeList": [
              "addInputParam"
            ],
            "valueType": "dynamic",
            "label": "",
            "required": false,
            "description": "这些变量会作为代码的运行的输入参数",
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": true
            }
          },
          {
            "renderTypeList": [
              "reference"
            ],
            "valueType": "string",
            "canEdit": true,
            "key": "data1",
            "label": "data1",
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": true
            },
            "required": true
          },
          {
            "renderTypeList": [
              "reference"
            ],
            "valueType": "string",
            "canEdit": true,
            "key": "data2",
            "label": "data2",
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": true
            },
            "required": true
          },
          {
            "key": "codeType",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string",
            "value": "js"
          },
          {
            "key": "code",
            "renderTypeList": [
              "custom"
            ],
            "label": "",
            "valueType": "string",
            "value": "function main({data1, data2}){\n    \n  return {\n      result: data1,\n      data2\n  }\n}"
          }
        ],
        "outputs": [
          {
            "id": "system_addOutputParam",
            "key": "system_addOutputParam",
            "type": "dynamic",
            "valueType": "dynamic",
            "label": "",
            "customFieldConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": false
            },
            "description": "将代码中 return 的对象作为输出，传递给后续的节点。变量名需要对应 return 的 key",
            "valueDesc": ""
          },
          {
            "id": "system_rawResponse",
            "key": "system_rawResponse",
            "label": "完整响应数据",
            "valueType": "object",
            "type": "static",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "qLUQfhG0ILRX",
            "type": "dynamic",
            "key": "result",
            "valueType": "string",
            "label": "result",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "gR0mkQpJ4Og8",
            "type": "dynamic",
            "key": "data2",
            "valueType": "string",
            "label": "data2",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "error",
            "key": "error",
            "label": "错误信息",
            "valueType": "string",
            "type": "error",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "ifElseNode",
      "title": "判断器",
      "source_file": "批量执行 loop.json",
      "flowNodeType": "ifElseNode",
      "pluginId": null,
      "node": {
        "nodeId": "sPHU4FH6jYDpCeP6",
        "parentNodeId": "iKQlroiTDx0umb22",
        "name": "判断器",
        "intro": "根据一定的条件，执行不同的分支。",
        "avatar": "core/workflow/template/ifelse",
        "flowNodeType": "ifElseNode",
        "showStatus": true,
        "position": {
          "x": 2145,
          "y": -797.4975886340185
        },
        "inputs": [
          {
            "key": "ifElseList",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "",
            "value": [
              {
                "condition": "AND",
                "list": [
                  {
                    "variable": [
                      "vSf7064KOWqeQB12",
                      "loopStartIndex"
                    ],
                    "condition": "equalTo",
                    "value": [
                      "vSf7064KOWqeQB12",
                      "loopStartIndex"
                    ],
                    "valueType": "reference"
                  }
                ]
              },
              {
                "condition": "AND",
                "list": [
                  {
                    "variable": [
                      "448745",
                      "userChatInput"
                    ],
                    "condition": "reg",
                    "value": "*1",
                    "valueType": "input"
                  }
                ]
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "ifElseResult",
            "key": "ifElseResult",
            "label": "判断结果",
            "valueType": "string",
            "type": "static",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "chatNode",
      "title": "AI 对话",
      "source_file": "工具调用.json",
      "flowNodeType": "chatNode",
      "pluginId": null,
      "node": {
        "nodeId": "xAlRWOH4464jV4Ha",
        "name": "AI 对话",
        "intro": "AI 大模型对话",
        "avatar": "core/workflow/template/aiChat",
        "flowNodeType": "chatNode",
        "showStatus": true,
        "position": {
          "x": 870,
          "y": 420
        },
        "version": "4.9.7",
        "inputs": [
          {
            "key": "model",
            "renderTypeList": [
              "settingLLMModel",
              "reference"
            ],
            "label": "AI 模型",
            "valueType": "string",
            "value": "qwen-vl-max"
          },
          {
            "key": "temperature",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "maxToken",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "isResponseAnswerText",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "value": true,
            "valueType": "boolean"
          },
          {
            "key": "aiChatQuoteRole",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string",
            "value": "system"
          },
          {
            "key": "quoteTemplate",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "quotePrompt",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "aiChatVision",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": true
          },
          {
            "key": "aiChatReasoning",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": true
          },
          {
            "key": "aiChatTopP",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "aiChatStopSign",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "aiChatResponseFormat",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "aiChatJsonSchema",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "systemPrompt",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "maxLength": 100000,
            "isRichText": true,
            "valueType": "string",
            "label": "提示词",
            "description": "模型固定的引导词，通过调整该内容，可以引导模型聊天方向。该内容会被固定在上下文的开头。可通过输入 / 插入选择变量\n如果关联了知识库，你还可以通过适当的描述，来引导模型何时去调用知识库搜索。例如：\n你是电影《星际穿越》的助手，当用户询问与《星际穿越》相关的内容时，请搜索知识库并结合搜索结果进行回答。",
            "placeholder": "在此输入提示词"
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "quoteQA",
            "renderTypeList": [
              "settingDatasetQuotePrompt"
            ],
            "label": "",
            "debugLabel": "知识库引用",
            "valueType": "datasetQuote"
          },
          {
            "key": "fileUrlList",
            "renderTypeList": [
              "reference",
              "input"
            ],
            "label": "文件链接",
            "debugLabel": "文件链接",
            "description": "用户上传的文档和图片链接",
            "valueType": "arrayString",
            "value": [
              [
                "448745",
                "userFiles"
              ]
            ]
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "用户问题",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": [
          {
            "id": "history",
            "key": "history",
            "required": true,
            "label": "新的上下文",
            "description": "将本次回复内容拼接上历史记录，作为新的上下文返回",
            "valueType": "chatHistory",
            "valueDesc": "{\n  obj: System | Human | AI;\n  value: string;\n}[]",
            "type": "static"
          },
          {
            "id": "answerText",
            "key": "answerText",
            "required": true,
            "label": "AI 回复内容",
            "description": "将在 stream 回复完毕后触发",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "reasoningText",
            "key": "reasoningText",
            "required": false,
            "label": "思考过程",
            "valueType": "string",
            "type": "static",
            "invalid": true,
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "datasetSearchNode",
      "title": "知识库搜索",
      "source_file": "工具调用 (1).json",
      "flowNodeType": "datasetSearchNode",
      "pluginId": null,
      "node": {
        "nodeId": "fzg52FrlL0HDHJx4",
        "name": "知识库搜索",
        "intro": "调用“语义检索”和“全文检索”能力，从“知识库”中查找可能与问题相关的参考内容",
        "avatar": "core/workflow/template/datasetSearch",
        "flowNodeType": "datasetSearchNode",
        "showStatus": true,
        "position": {
          "x": 120,
          "y": 360
        },
        "version": "4.9.2",
        "inputs": [
          {
            "key": "datasets",
            "renderTypeList": [
              "selectDataset",
              "reference"
            ],
            "label": "选择知识库",
            "value": [],
            "valueType": "selectDataset",
            "required": true,
            "valueDesc": "{\n  datasetId: string;\n}[]"
          },
          {
            "key": "similarity",
            "renderTypeList": [
              "selectDatasetParamsModal"
            ],
            "label": "",
            "value": 0.4,
            "valueType": "number"
          },
          {
            "key": "limit",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "value": 5000,
            "valueType": "number"
          },
          {
            "key": "searchMode",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string",
            "value": "embedding"
          },
          {
            "key": "embeddingWeight",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number",
            "value": 0.5
          },
          {
            "key": "usingReRank",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": false
          },
          {
            "key": "rerankModel",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "rerankWeight",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number",
            "value": 0.5
          },
          {
            "key": "datasetSearchUsingExtensionQuery",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": true
          },
          {
            "key": "datasetSearchExtensionModel",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "datasetSearchExtensionBg",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string",
            "value": ""
          },
          {
            "key": "authTmbId",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": false
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "需要检索的内容",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          },
          {
            "key": "collectionFilterMatch",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "label": "集合元数据过滤",
            "valueType": "string",
            "isPro": true,
            "description": "目前支持标签、创建时间和集合 ID 过滤，需按照以下格式填写：\n{\n  \"tags\": {\n    \"$and\": [\"标签 1\",\"标签 2\"],\n    \"$or\": [\"有 $and 标签时，and 生效，or 不生效\"]\n  },\n  \"createTime\": {\n      \"$gte\": \"YYYY-MM-DD HH:mm 格式即可，集合的创建时间大于该时间\",\n      \"$lte\": \"YYYY-MM-DD HH:mm 格式即可，集合的创建时间小于该时间,可和 $gte 共同使用\"\n  },\n  \"collectionIds\": [\"集合ID1\", \"集合ID2\", \"支持文件夹ID，会自动展开获取所有子集合\"]\n}"
          }
        ],
        "outputs": [
          {
            "id": "quoteQA",
            "key": "quoteQA",
            "label": "知识库引用",
            "description": "特殊数组格式，搜索结果为空时，返回空数组。",
            "type": "static",
            "valueType": "datasetQuote",
            "valueDesc": "{\n  id: string;\n  datasetId: string;\n  collectionId: string;\n  sourceName: string;\n  sourceId?: string;\n  q: string;\n  a: string\n}[]"
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "classifyQuestion",
      "title": "问题分类",
      "source_file": "工具调用(1).json",
      "flowNodeType": "classifyQuestion",
      "pluginId": null,
      "node": {
        "nodeId": "ytA1T11lMkaJGnUy",
        "name": "问题分类",
        "intro": "根据用户的历史记录和当前问题判断该次提问的类型。可以添加多组问题类型，下面是一个模板例子:\n类型1: 打招呼\n类型2: 关于商品“使用”问题\n类型3: 关于商品“购买”问题\n类型4: 其他问题",
        "avatar": "core/workflow/template/questionClassify",
        "flowNodeType": "classifyQuestion",
        "showStatus": true,
        "position": {
          "x": 3000,
          "y": 435
        },
        "version": "4.9.2",
        "inputs": [
          {
            "key": "model",
            "renderTypeList": [
              "selectLLMModel",
              "reference"
            ],
            "label": "AI 模型",
            "required": true,
            "valueType": "string",
            "llmModelType": "classify",
            "value": "qwen-vl-max"
          },
          {
            "key": "systemPrompt",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "maxLength": 100000,
            "isRichText": true,
            "valueType": "string",
            "label": "背景知识",
            "description": "你可以添加一些特定内容的介绍，从而更好的识别用户的问题类型。这个内容通常是给模型介绍一个它不知道的内容。",
            "placeholder": "例如：\n1. AIGC（人工智能生成内容）是指使用人工智能技术自动或半自动地生成数字内容，如文本、图像、音乐、视频等。\n2. AIGC 技术包括但不限于自然语言处理、计算机视觉、机器学习和深度学习。这些技术可以创建新内容或修改现有内容，以满足特定的创意、教育、娱乐或信息需求。"
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "用户输入的问题（问题需要完善）",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          },
          {
            "key": "agents",
            "renderTypeList": [
              "custom"
            ],
            "valueType": "any",
            "label": "",
            "value": [
              {
                "value": "Greeting",
                "key": "wqre"
              },
              {
                "value": "Question regarding xxx",
                "key": "sdfa"
              },
              {
                "value": "Other Questions",
                "key": "agex"
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "cqResult",
            "key": "cqResult",
            "required": true,
            "label": "分类结果",
            "valueType": "string",
            "type": "static",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "contentExtract",
      "title": "文本内容提取",
      "source_file": "工具调用(1).json",
      "flowNodeType": "contentExtract",
      "pluginId": null,
      "node": {
        "nodeId": "fAxboqMNEsct00Im",
        "name": "文本内容提取",
        "intro": "可从文本中提取指定的数据，例如：sql语句、搜索关键词、代码等",
        "avatar": "core/workflow/template/extractJson",
        "flowNodeType": "contentExtract",
        "showStatus": true,
        "position": {
          "x": 1110,
          "y": 810
        },
        "version": "4.9.2",
        "inputs": [
          {
            "key": "model",
            "renderTypeList": [
              "selectLLMModel",
              "reference"
            ],
            "label": "AI 模型",
            "required": true,
            "valueType": "string",
            "llmModelType": "extractFields",
            "value": "qwen-vl-max"
          },
          {
            "key": "description",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "valueType": "string",
            "label": "提取要求描述",
            "description": "给AI一些对应的背景知识或要求描述，引导AI更好的完成任务。\\n该输入框可使用全局变量。",
            "placeholder": "例如: 1. 当前时间为: {{cTime}}。你是一个实验室预约助手，你的任务是帮助用户预约实验室，从文本中获取对应的预约信息。\n2. 你是谷歌搜索助手，需要从文本中提取出合适的搜索词。"
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "content",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "label": "需要提取的文本",
            "required": true,
            "valueType": "string",
            "toolDescription": "需要检索的内容"
          },
          {
            "key": "extractKeys",
            "renderTypeList": [
              "custom"
            ],
            "label": "",
            "valueType": "any",
            "description": "由 '描述' 和 'key' 组成一个目标字段，可提取多个目标字段",
            "value": []
          }
        ],
        "outputs": [
          {
            "id": "success",
            "key": "success",
            "label": "字段完全提取",
            "required": true,
            "description": "提取字段全部填充时返回 true （模型提取或使用默认值均属于成功）",
            "valueType": "boolean",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "fields",
            "key": "fields",
            "label": "完整提取结果",
            "required": true,
            "description": "一个 JSON 字符串，例如：{\"name:\":\"YY\",\"Time\":\"2023/7/2 18:00\"}",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "textEditor",
      "title": "文本拼接",
      "source_file": "工具调用(1).json",
      "flowNodeType": "textEditor",
      "pluginId": null,
      "node": {
        "nodeId": "di64CGcyWGDJv0zc",
        "name": "文本拼接",
        "intro": "可对固定或传入的文本进行加工后输出，非字符串类型数据最终会转成字符串类型。",
        "avatar": "core/workflow/template/textConcat",
        "flowNodeType": "textEditor",
        "position": {
          "x": 2055,
          "y": 765
        },
        "inputs": [
          {
            "key": "system_textareaInput",
            "renderTypeList": [
              "textarea"
            ],
            "valueType": "string",
            "required": true,
            "label": "拼接文本",
            "placeholder": "可输入 / 唤起变量列表"
          }
        ],
        "outputs": [
          {
            "id": "system_text",
            "key": "system_text",
            "label": "拼接结果",
            "type": "static",
            "valueType": "string",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "readFiles",
      "title": "文档解析",
      "source_file": "工具调用(1).json",
      "flowNodeType": "readFiles",
      "pluginId": null,
      "node": {
        "nodeId": "dc83Ikjnc5qAHj7p",
        "name": "文档解析",
        "intro": "解析本轮对话上传的文档，并返回对应文档内容",
        "avatar": "core/workflow/template/readFiles",
        "flowNodeType": "readFiles",
        "showStatus": true,
        "position": {
          "x": 2235,
          "y": -30
        },
        "version": "4.9.2",
        "inputs": [
          {
            "key": "fileUrlList",
            "renderTypeList": [
              "reference"
            ],
            "valueType": "arrayString",
            "label": "文档链接",
            "required": true,
            "value": [
              [
                "448745",
                "userFiles"
              ]
            ]
          }
        ],
        "outputs": [
          {
            "id": "system_text",
            "key": "system_text",
            "label": "文档解析结果",
            "description": "文档原文，由文件名和文档内容组成，多个文件之间通过横线隔开。",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_rawResponse",
            "key": "system_rawResponse",
            "label": "原始响应",
            "description": "工具的原始响应",
            "valueType": "arrayObject",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "httpRequest468",
      "title": "HTTP 请求",
      "source_file": "工具调用(1).json",
      "flowNodeType": "httpRequest468",
      "pluginId": null,
      "node": {
        "nodeId": "aqOhFnosObK1axbs",
        "name": "HTTP 请求",
        "intro": "可以发出一个 HTTP 请求，实现更为复杂的操作（联网搜索、数据库查询等）",
        "avatar": "core/workflow/template/httpRequest",
        "flowNodeType": "httpRequest468",
        "showStatus": true,
        "position": {
          "x": 840,
          "y": 900
        },
        "inputs": [
          {
            "key": "system_addInputParam",
            "renderTypeList": [
              "addInputParam"
            ],
            "valueType": "dynamic",
            "label": "",
            "required": false,
            "description": "接收前方节点的输出值作为变量，这些变量可以被 HTTP 请求参数使用。",
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": true
            },
            "deprecated": false
          },
          {
            "key": "system_httpMethod",
            "renderTypeList": [
              "custom"
            ],
            "valueType": "string",
            "label": "",
            "value": "POST",
            "required": true
          },
          {
            "key": "system_httpTimeout",
            "renderTypeList": [
              "custom"
            ],
            "valueType": "number",
            "label": "",
            "value": 30,
            "min": 5,
            "max": 600,
            "required": true
          },
          {
            "key": "system_httpReqUrl",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "string",
            "label": "",
            "description": "新的 HTTP 请求地址。如果出现两个“请求地址”，可以删除该模块重新加入，会拉取最新的模块配置。",
            "placeholder": "//api.ai.com/getInventory",
            "required": false
          },
          {
            "key": "system_header_secret",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "object",
            "label": "",
            "required": false
          },
          {
            "key": "system_httpHeader",
            "renderTypeList": [
              "custom"
            ],
            "valueType": "any",
            "value": [],
            "label": "",
            "description": "自定义请求头，请严格填入 JSON 字符串。\n1. 确保最后一个属性没有逗号\n2. 确保 key 包含双引号\n例如：{\"Authorization\":\"Bearer xxx\"}",
            "placeholder": "自定义请求头，请严格填入 JSON 字符串。\n1. 确保最后一个属性没有逗号\n2. 确保 key 包含双引号\n例如：{\"Authorization\":\"Bearer xxx\"}",
            "required": false
          },
          {
            "key": "system_httpParams",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "value": [],
            "label": "",
            "required": false
          },
          {
            "key": "system_httpJsonBody",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "value": "",
            "label": "",
            "required": false
          },
          {
            "key": "system_httpFormBody",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "value": [],
            "label": "",
            "required": false
          },
          {
            "key": "system_httpContentType",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "string",
            "value": "json",
            "label": "",
            "required": false
          }
        ],
        "outputs": [
          {
            "id": "system_addOutputParam",
            "key": "system_addOutputParam",
            "type": "dynamic",
            "valueType": "dynamic",
            "label": "输出字段提取",
            "customFieldConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "object",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "arrayObject",
                "arrayAny",
                "any",
                "chatHistory",
                "datasetQuote",
                "dynamic",
                "selectDataset",
                "selectApp"
              ],
              "showDescription": false,
              "showDefaultValue": false
            },
            "description": "可以通过 JSONPath 语法来提取响应值中的指定字段",
            "valueDesc": ""
          },
          {
            "id": "httpRawResponse",
            "key": "httpRawResponse",
            "required": true,
            "label": "原始响应",
            "description": "HTTP请求的原始响应。只能接受字符串或JSON类型响应数据。",
            "valueType": "any",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "error",
            "key": "error",
            "label": "错误信息",
            "valueType": "string",
            "type": "error",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "tools",
      "title": "工具调用",
      "source_file": "工具调用.json",
      "flowNodeType": "tools",
      "pluginId": null,
      "node": {
        "nodeId": "yn72VvTcVIU4yGwf",
        "name": "工具调用",
        "intro": "由 AI 自主决定工具调用。",
        "avatar": "core/workflow/template/toolCall",
        "flowNodeType": "tools",
        "showStatus": true,
        "position": {
          "x": 1215,
          "y": -547.0024113659815
        },
        "version": "4.9.2",
        "inputs": [
          {
            "key": "model",
            "renderTypeList": [
              "settingLLMModel",
              "reference"
            ],
            "label": "AI 模型",
            "valueType": "string",
            "llmModelType": "all",
            "value": "qwen-vl-max"
          },
          {
            "key": "temperature",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "maxToken",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "isResponseAnswerText",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "value": true,
            "valueType": "boolean"
          },
          {
            "key": "aiChatVision",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": true
          },
          {
            "key": "aiChatReasoning",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "boolean",
            "value": true
          },
          {
            "key": "aiChatTopP",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "number"
          },
          {
            "key": "aiChatStopSign",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "aiChatResponseFormat",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "aiChatJsonSchema",
            "renderTypeList": [
              "hidden"
            ],
            "label": "",
            "valueType": "string"
          },
          {
            "key": "systemPrompt",
            "renderTypeList": [
              "textarea",
              "reference"
            ],
            "maxLength": 100000,
            "isRichText": true,
            "valueType": "string",
            "label": "提示词",
            "description": "模型固定的引导词，通过调整该内容，可以引导模型聊天方向。该内容会被固定在上下文的开头。可通过输入 / 插入选择变量\n如果关联了知识库，你还可以通过适当的描述，来引导模型何时去调用知识库搜索。例如：\n你是电影《星际穿越》的助手，当用户询问与《星际穿越》相关的内容时，请搜索知识库并结合搜索结果进行回答。",
            "placeholder": "在此输入提示词"
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "fileUrlList",
            "renderTypeList": [
              "reference",
              "input"
            ],
            "label": "文件链接",
            "debugLabel": "文件链接",
            "description": "用户上传的文档和图片链接",
            "valueType": "arrayString",
            "value": [
              [
                "448745",
                "userFiles"
              ]
            ]
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "用户输入的问题（问题需要完善）",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": [
          {
            "id": "answerText",
            "key": "answerText",
            "label": "AI 回复内容",
            "description": "将在 stream 回复完毕后触发",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "catchError": false
      }
    },
    {
      "key": "stopTool",
      "title": "工具调用终止",
      "source_file": "工具调用.json",
      "flowNodeType": "stopTool",
      "pluginId": null,
      "node": {
        "nodeId": "vcRFD4A04qNbdn7J",
        "name": "工具调用终止#2",
        "intro": "该模块需配置工具调用使用。当该模块被执行时，本次工具调用将会强制结束，并且不再调用AI针对工具调用结果回答问题。",
        "avatar": "core/workflow/template/stopTool",
        "flowNodeType": "stopTool",
        "position": {
          "x": 1650,
          "y": 600
        },
        "inputs": [],
        "outputs": []
      }
    },
    {
      "key": "toolParams",
      "title": "自定义工具变量（工具调用辅助节点）",
      "source_file": "工具调用 (1).json",
      "flowNodeType": "toolParams",
      "pluginId": null,
      "node": {
        "nodeId": "cSidMaxe30EjNK0F",
        "name": "自定义工具变量",
        "intro": "该模块需要配合工具调用使用。可以自定义工具调用参数，并传递到下游节点使用",
        "avatar": "core/workflow/template/toolParams",
        "flowNodeType": "toolParams",
        "position": {
          "x": 1815,
          "y": 283.9975886340185
        },
        "inputs": [
          {
            "valueType": "string",
            "renderTypeList": [
              "reference"
            ],
            "key": "name",
            "label": "name",
            "toolDescription": "这是测试文本",
            "required": true,
            "canEdit": true,
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "object"
              ],
              "showDescription": true
            },
            "enum": ""
          }
        ],
        "outputs": [
          {
            "valueType": "string",
            "renderTypeList": [
              "reference"
            ],
            "key": "name",
            "label": "name",
            "toolDescription": "这是测试文本",
            "required": true,
            "canEdit": true,
            "customInputConfig": {
              "selectValueTypeList": [
                "string",
                "number",
                "boolean",
                "arrayString",
                "arrayNumber",
                "arrayBoolean",
                "object"
              ],
              "showDescription": true
            },
            "enum": "",
            "id": "name",
            "type": "static"
          }
        ]
      }
    },
    {
      "key": "databaseConnection",
      "title": "数据库连接",
      "source_file": "数据库.json",
      "flowNodeType": "tool",
      "pluginId": "systemTool-databaseConnection",
      "node": {
        "nodeId": "ogr5ixpT23XB6hnh",
        "name": "数据库连接",
        "intro": "可连接常用数据库，并执行sql",
        "avatar": "https://minio.com/fastgpt-public/system/plugin/tools/databaseConnection/logo",
        "flowNodeType": "tool",
        "showStatus": true,
        "position": {
          "x": 1215,
          "y": -345
        },
        "version": "",
        "inputs": [
          {
            "key": "system_input_config",
            "label": "",
            "renderTypeList": [
              "hidden"
            ],
            "inputList": [
              {
                "key": "databaseType",
                "label": "数据库类型",
                "required": true,
                "inputType": "select",
                "list": [
                  {
                    "label": "MySQL",
                    "value": "MySQL"
                  },
                  {
                    "label": "PostgreSQL",
                    "value": "PostgreSQL"
                  },
                  {
                    "label": "Microsoft SQL Server",
                    "value": "Microsoft SQL Server"
                  }
                ]
              },
              {
                "key": "host",
                "label": "host",
                "required": true,
                "inputType": "input"
              },
              {
                "key": "port",
                "label": "数据库连接端口号",
                "required": true,
                "inputType": "numberInput"
              },
              {
                "key": "databaseName",
                "label": "数据库名称",
                "required": true,
                "inputType": "input"
              },
              {
                "key": "user",
                "label": "数据库账号",
                "required": true,
                "inputType": "input"
              },
              {
                "key": "password",
                "label": "数据库密码",
                "required": true,
                "inputType": "secret"
              }
            ]
          },
          {
            "key": "sql",
            "label": "sql",
            "defaultValue": "",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "description": "sql语句，可以传入sql语句直接执行",
            "required": true,
            "toolDescription": "sql语句，可以传入sql语句直接执行",
            "list": [
              {
                "label": "",
                "value": ""
              }
            ],
            "value": ""
          }
        ],
        "outputs": [
          {
            "id": "result",
            "type": "static",
            "key": "result",
            "valueType": "object",
            "label": "结果",
            "description": "执行结果",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "systemTool-databaseConnection",
        "toolConfig": {
          "systemTool": {
            "toolId": "systemTool-databaseConnection"
          }
        },
        "catchError": false
      }
    },
    {
      "key": "fetchUrl",
      "title": "网页内容抓取",
      "source_file": "自定义工具变量 toolParams.json",
      "flowNodeType": "tool",
      "pluginId": "systemTool-fetchUrl",
      "node": {
        "nodeId": "l34MtjWe2oWXMDtX",
        "name": "网页内容抓取",
        "intro": "可获取一个网页链接内容，并以 Markdown 格式输出，仅支持获取静态网站。",
        "avatar": "core/workflow/template/fetchUrl",
        "flowNodeType": "tool",
        "showStatus": true,
        "position": {
          "x": 1200,
          "y": -379.00241136598146
        },
        "version": "",
        "inputs": [
          {
            "key": "url",
            "label": "url",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "reference",
              "input"
            ],
            "valueType": "string",
            "description": "需要读取的网页链接",
            "required": true,
            "toolDescription": "需要读取的网页链接",
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": [
          {
            "id": "title",
            "type": "static",
            "key": "title",
            "valueType": "string",
            "label": "网页标题",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "result",
            "type": "static",
            "key": "result",
            "valueType": "string",
            "label": "网页内容",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "systemTool-fetchUrl",
        "toolConfig": {
          "systemTool": {
            "toolId": "systemTool-fetchUrl"
          }
        },
        "catchError": true
      }
    },
    {
      "key": "weworkWebhook",
      "title": "企业微信 webhook",
      "source_file": "企业微信 webhook.json",
      "flowNodeType": "tool",
      "pluginId": "systemTool-WeWorkWebhook",
      "node": {
        "nodeId": "t1SrEAAnBp0UfL8R",
        "name": "企业微信 webhook",
        "intro": "向企业微信机器人发起 webhook 请求。只能内部群使用。",
        "avatar": "plugins/qiwei",
        "flowNodeType": "tool",
        "showStatus": true,
        "position": {
          "x": 1230,
          "y": -379.00241136598146
        },
        "version": "",
        "inputs": [
          {
            "key": "webhookUrl",
            "label": "企微机器人地址",
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "value": ""
          },
          {
            "key": "message",
            "label": "发送的消息",
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "value": "发送的消息"
          }
        ],
        "outputs": [
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "systemTool-WeWorkWebhook",
        "toolConfig": {
          "systemTool": {
            "toolId": "systemTool-WeWorkWebhook"
          }
        },
        "catchError": false
      }
    },
    {
      "key": "dingTalkWebhook",
      "title": "钉钉 webhook",
      "source_file": "钉钉 webhook.json",
      "flowNodeType": "tool",
      "pluginId": "systemTool-DingTalkWebhook",
      "node": {
        "nodeId": "th7rMM7SmnbHYxtz",
        "name": "钉钉 webhook",
        "intro": "向钉钉机器人发起 webhook 请求。",
        "avatar": "plugins/dingding",
        "flowNodeType": "tool",
        "showStatus": true,
        "position": {
          "x": 1185,
          "y": -379.00241136598146
        },
        "version": "",
        "inputs": [
          {
            "key": "webhookUrl",
            "label": "钉钉机器人地址",
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "required": true,
            "value": ""
          },
          {
            "key": "secret",
            "label": "加签值",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "description": "钉钉机器人加签值",
            "required": true,
            "value": ""
          },
          {
            "key": "message",
            "label": "发送的消息",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "description": "发送的消息",
            "required": true,
            "toolDescription": "发送的消息",
            "value": "发送到消息"
          }
        ],
        "outputs": [
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "systemTool-DingTalkWebhook",
        "toolConfig": {
          "systemTool": {
            "toolId": "systemTool-DingTalkWebhook"
          }
        },
        "catchError": false
      }
    },
    {
      "key": "feishuWebhook",
      "title": "飞书 webhook",
      "source_file": "飞书 webhook.json",
      "flowNodeType": "tool",
      "pluginId": "systemTool-feishu",
      "node": {
        "nodeId": "kO6mxDoSI0GEx2yA",
        "name": "飞书 webhook",
        "intro": "向飞书机器人发起 webhook 请求。",
        "avatar": "core/app/templates/plugin-feishu",
        "flowNodeType": "tool",
        "showStatus": true,
        "position": {
          "x": 1200,
          "y": -420
        },
        "version": "",
        "inputs": [
          {
            "key": "content",
            "label": "content",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "input",
              "reference"
            ],
            "valueType": "string",
            "description": "需要发送的消息",
            "required": true,
            "toolDescription": "需要发送的消息"
          },
          {
            "key": "hook_url",
            "label": "hook_url",
            "selectedTypeIndex": 0,
            "renderTypeList": [
              "input"
            ],
            "valueType": "string",
            "description": "飞书机器人地址",
            "required": true
          }
        ],
        "outputs": [
          {
            "id": "result",
            "type": "static",
            "key": "result",
            "valueType": "object",
            "label": "result",
            "valueDesc": "",
            "description": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "systemTool-feishu",
        "toolConfig": {
          "systemTool": {
            "toolId": "systemTool-feishu"
          }
        },
        "catchError": false
      }
    },
    {
      "key": "userSelect",
      "title": "用户选择",
      "source_file": "用户选择 userSelect.json",
      "flowNodeType": "userSelect",
      "pluginId": null,
      "node": {
        "nodeId": "hjyZ5IKUflnaARZS",
        "name": "用户选择",
        "intro": "该模块可配置多个选项，以供对话时选择。不同选项可导向不同工作流支线",
        "avatar": "core/workflow/template/userSelect",
        "flowNodeType": "userSelect",
        "position": {
          "x": 1185,
          "y": -390
        },
        "inputs": [
          {
            "key": "description",
            "renderTypeList": [
              "textarea"
            ],
            "valueType": "string",
            "label": "说明文字",
            "description": "你可以添加一段说明文字，用以向用户说明每个选项代表的含义。",
            "placeholder": "例如: \n冰箱里是否有西红柿？",
            "value": "这是说明文字"
          },
          {
            "renderTypeList": [
              "custom"
            ],
            "valueType": "any",
            "label": "",
            "key": "userSelectOptions",
            "value": [
              {
                "value": "这是选项1",
                "key": "option1"
              },
              {
                "value": "这是选项2",
                "key": "option2"
              },
              {
                "value": "这是选项3",
                "key": "jNIKegS0jwQnUKXR"
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "selectResult",
            "key": "selectResult",
            "required": true,
            "label": "选择结果",
            "valueType": "string",
            "type": "static",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "formInput",
      "title": "表单输入（全类型）",
      "source_file": "表单输入 formInput。 (2).json",
      "flowNodeType": "formInput",
      "pluginId": null,
      "node": {
        "nodeId": "gI9sxln4G2T2uQb3",
        "name": "表单输入",
        "intro": "该模块可以配置多种输入，引导用户输入特定内容。",
        "avatar": "core/workflow/template/formInput",
        "flowNodeType": "formInput",
        "position": {
          "x": 1170,
          "y": -465
        },
        "inputs": [
          {
            "key": "description",
            "renderTypeList": [
              "textarea"
            ],
            "valueType": "string",
            "label": "说明文字",
            "description": "你可以添加一段说明文字，用以向用户说明需要输入的内容",
            "placeholder": "例如：\n补充您的信息",
            "value": "这是说明文字\n还有变量\n\n{{$448745.userChatInput$}}"
          },
          {
            "renderTypeList": [
              "custom"
            ],
            "valueType": "any",
            "label": "",
            "key": "userInputForms",
            "value": [
              {
                "type": "timePointSelect",
                "key": "时间分钟",
                "label": "时间分钟",
                "valueType": "string",
                "description": "时间分钟描述",
                "required": true,
                "defaultValue": "2026-05-01 03:03:00",
                "timeGranularity": "minute",
                "timeRangeStart": "2026-05-01 01:01:00",
                "timeRangeEnd": "2026-05-03 02:02:00"
              },
              {
                "type": "password",
                "key": "密码",
                "label": "密码",
                "valueType": "string",
                "description": "这是密码描述",
                "required": false,
                "defaultValue": "",
                "minLength": 23
              },
              {
                "type": "numberInput",
                "key": "这是数字输入框",
                "label": "这是数字输入框",
                "valueType": "number",
                "description": "这是数字输入框",
                "required": true,
                "defaultValue": 12,
                "max": 255,
                "min": 1
              },
              {
                "type": "select",
                "key": "单选",
                "label": "单选",
                "valueType": "string",
                "description": "这是单选",
                "required": false,
                "defaultValue": "",
                "list": [
                  {
                    "label": "选项1",
                    "value": "选项1"
                  },
                  {
                    "label": "选项2",
                    "value": "选项2"
                  },
                  {
                    "label": "选项3",
                    "value": "选项3"
                  }
                ]
              },
              {
                "type": "multipleSelect",
                "key": "多选克框",
                "label": "多选克框",
                "valueType": "arrayString",
                "description": "这是多选框的描述",
                "required": false,
                "defaultValue": [
                  "选项1",
                  "选项3"
                ],
                "list": [
                  {
                    "label": "选项1",
                    "value": "选项1"
                  },
                  {
                    "label": "选项3",
                    "value": "选项3"
                  },
                  {
                    "label": "选项3",
                    "value": "选项3"
                  }
                ]
              },
              {
                "type": "switch",
                "key": "开关",
                "label": "开关",
                "valueType": "boolean",
                "description": "这是开关",
                "required": false,
                "defaultValue": true
              },
              {
                "type": "timePointSelect",
                "key": "时间点",
                "label": "时间点",
                "valueType": "string",
                "description": "这是时间的的描述框",
                "required": false,
                "defaultValue": "2026-05-02 03:27:14",
                "timeGranularity": "second",
                "timeRangeStart": "2026-05-01 01:23:12",
                "timeRangeEnd": "2026-05-08 02:25:13"
              },
              {
                "type": "timeRangeSelect",
                "key": "时间范围",
                "label": "时间范围",
                "valueType": "arrayString",
                "description": "这是时间范围",
                "required": false,
                "defaultValue": [
                  "2026-05-01 01:05:03",
                  "2026-05-06 02:06:04"
                ],
                "timeGranularity": "second",
                "timeRangeStart": "2026-05-01 01:03:01",
                "timeRangeEnd": "2026-05-13 02:04:02"
              },
              {
                "type": "fileSelect",
                "key": "这是文件上传",
                "label": "这是文件上传",
                "valueType": "arrayString",
                "description": "文件上传的描述",
                "required": true,
                "defaultValue": "",
                "canLocalUpload": true,
                "canUrlUpload": true,
                "canSelectFile": true,
                "canSelectImg": true,
                "canSelectVideo": true,
                "canSelectAudio": true,
                "maxFiles": 20
              },
              {
                "type": "selectLLMModel",
                "key": "ai模型选择",
                "label": "ai模型选择",
                "valueType": "string",
                "description": "描述",
                "required": false,
                "defaultValue": "qwen-vl-max"
              },
              {
                "type": "timePointSelect",
                "key": "时间小时",
                "label": "时间小时",
                "valueType": "string",
                "description": "时间小时描述",
                "required": false,
                "defaultValue": "2026-05-03 02:00:00",
                "timeGranularity": "hour",
                "timeRangeStart": "2026-05-01 01:00:00",
                "timeRangeEnd": "2026-05-03 02:00:00"
              }
            ]
          }
        ],
        "outputs": [
          {
            "id": "formInputResult",
            "key": "formInputResult",
            "required": true,
            "label": "用户完整输入结果",
            "description": "一个包含完整结果的对象",
            "valueType": "object",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "文本",
            "valueType": "string",
            "key": "时间分钟",
            "label": "时间分钟",
            "type": "static"
          },
          {
            "id": "密码",
            "valueType": "string",
            "key": "密码",
            "label": "密码",
            "type": "static"
          },
          {
            "id": "这是数字输入框",
            "valueType": "number",
            "key": "这是数字输入框",
            "label": "这是数字输入框",
            "type": "static"
          },
          {
            "id": "单选",
            "valueType": "string",
            "key": "单选",
            "label": "单选",
            "type": "static"
          },
          {
            "id": "多选克框",
            "valueType": "arrayString",
            "key": "多选克框",
            "label": "多选克框",
            "type": "static"
          },
          {
            "id": "开关",
            "valueType": "boolean",
            "key": "开关",
            "label": "开关",
            "type": "static"
          },
          {
            "id": "时间点",
            "valueType": "string",
            "key": "时间点",
            "label": "时间点",
            "type": "static"
          },
          {
            "id": "时间范围",
            "valueType": "arrayString",
            "key": "时间范围",
            "label": "时间范围",
            "type": "static"
          },
          {
            "id": "这是文件上传",
            "valueType": "arrayString",
            "key": "这是文件上传",
            "label": "这是文件上传",
            "type": "static"
          },
          {
            "id": "ai模型选择",
            "valueType": "string",
            "key": "ai模型选择",
            "label": "ai模型选择",
            "type": "static"
          },
          {
            "id": "时间小时",
            "valueType": "string",
            "key": "时间小时",
            "label": "时间小时",
            "type": "static"
          }
        ]
      }
    },
    {
      "key": "variableUpdate_1",
      "title": "变量更新 #1",
      "source_file": "变量更新 variableUpdate。.json",
      "flowNodeType": "variableUpdate",
      "pluginId": null,
      "node": {
        "nodeId": "koOWYoziwE4nfhU8",
        "name": "变量更新",
        "intro": "可以更新指定节点的输出值或更新全局变量",
        "avatar": "core/workflow/template/variableUpdate",
        "flowNodeType": "variableUpdate",
        "showStatus": false,
        "position": {
          "x": 1155,
          "y": -379.00241136598146
        },
        "inputs": [
          {
            "key": "updateList",
            "valueType": "any",
            "label": "",
            "renderTypeList": [
              "hidden"
            ],
            "value": [
              {
                "variable": [
                  "448745",
                  "userChatInput"
                ],
                "value": [
                  "VARIABLE_NODE_ID",
                  "cTime"
                ],
                "valueType": "string",
                "renderType": "reference"
              }
            ]
          }
        ],
        "outputs": []
      }
    },
    {
      "key": "variableUpdate_2",
      "title": "变量更新 #2",
      "source_file": "变量更新 variableUpdate。.json",
      "flowNodeType": "variableUpdate",
      "pluginId": null,
      "node": {
        "nodeId": "cBd1cqiloBsI2lSt",
        "name": "变量更新#2",
        "intro": "可以更新指定节点的输出值或更新全局变量",
        "avatar": "core/workflow/template/variableUpdate",
        "flowNodeType": "variableUpdate",
        "showStatus": false,
        "position": {
          "x": 1140,
          "y": 0
        },
        "inputs": [
          {
            "key": "updateList",
            "valueType": "any",
            "label": "",
            "renderTypeList": [
              "hidden"
            ],
            "value": [
              {
                "variable": [
                  "VARIABLE_NODE_ID",
                  "appId"
                ],
                "value": [
                  "",
                  "这是值"
                ],
                "valueType": "string",
                "renderType": "input"
              }
            ]
          }
        ],
        "outputs": []
      }
    },
    {
      "key": "loop",
      "title": "批量执行",
      "source_file": "批量执行 loop.json",
      "flowNodeType": "loop",
      "pluginId": null,
      "node": {
        "nodeId": "iKQlroiTDx0umb22",
        "name": "批量执行",
        "intro": "输入一个数组，遍历数组并将每一个数组元素作为输入元素，执行工作流。",
        "avatar": "core/workflow/template/loop",
        "flowNodeType": "loop",
        "showStatus": true,
        "position": {
          "x": 1425,
          "y": -1125
        },
        "inputs": [
          {
            "key": "loopInputArray",
            "renderTypeList": [
              "reference"
            ],
            "valueType": "arrayString",
            "required": true,
            "label": "数组",
            "value": [
              [
                "448745",
                "userChatInput"
              ],
              [
                "VARIABLE_NODE_ID",
                "cTime"
              ]
            ]
          },
          {
            "key": "childrenNodeIdList",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "arrayString",
            "label": "",
            "value": [
              "vSf7064KOWqeQB12",
              "gvCw2PN6PeU3ZVjp",
              "sPHU4FH6jYDpCeP6",
              "tMe5mloMfj86ZKHA",
              "ghmU2gDzrDq86F6X"
            ]
          },
          {
            "key": "nodeWidth",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "number",
            "label": "",
            "value": 2485.3661694085467
          },
          {
            "key": "nodeHeight",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "number",
            "label": "",
            "value": 1391.4855318041111
          },
          {
            "key": "loopNodeInputHeight",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "number",
            "label": "",
            "value": 82
          }
        ],
        "outputs": [
          {
            "id": "loopArray",
            "key": "loopArray",
            "label": "数组执行结果",
            "type": "static",
            "valueType": "arrayString",
            "valueDesc": "",
            "description": ""
          }
        ]
      }
    },
    {
      "key": "loopStart",
      "title": "循环开始",
      "source_file": "批量执行 loop.json",
      "flowNodeType": "loopStart",
      "pluginId": null,
      "node": {
        "nodeId": "vSf7064KOWqeQB12",
        "parentNodeId": "iKQlroiTDx0umb22",
        "name": "开始",
        "avatar": "core/workflow/template/loopStart",
        "flowNodeType": "loopStart",
        "showStatus": false,
        "position": {
          "x": 1494.6338305914535,
          "y": -803.4855318041111
        },
        "inputs": [
          {
            "key": "loopStartInput",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "any",
            "label": "",
            "required": true,
            "value": ""
          },
          {
            "key": "loopStartIndex",
            "renderTypeList": [
              "hidden"
            ],
            "valueType": "number",
            "label": "workflow:Array_element_index"
          }
        ],
        "outputs": [
          {
            "id": "loopStartIndex",
            "key": "loopStartIndex",
            "label": "workflow:Array_element_index",
            "type": "static",
            "valueType": "number"
          },
          {
            "id": "loopStartInput",
            "key": "loopStartInput",
            "label": "数组元素",
            "type": "static",
            "valueType": "string"
          }
        ]
      }
    },
    {
      "key": "loopEnd",
      "title": "循环结束",
      "source_file": "批量执行 loop.json",
      "flowNodeType": "loopEnd",
      "pluginId": null,
      "node": {
        "nodeId": "gvCw2PN6PeU3ZVjp",
        "parentNodeId": "iKQlroiTDx0umb22",
        "name": "结束",
        "avatar": "core/workflow/template/loopEnd",
        "flowNodeType": "loopEnd",
        "showStatus": false,
        "position": {
          "x": 3480,
          "y": -270
        },
        "inputs": [
          {
            "key": "loopEndInput",
            "renderTypeList": [
              "reference"
            ],
            "valueType": "any",
            "label": "",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": []
      }
    },
    {
      "key": "appModule_1",
      "title": "应用调用 appModule #1",
      "source_file": "1111111.json",
      "flowNodeType": "appModule",
      "pluginId": "69ef2881b180ca8df8d5c846",
      "node": {
        "nodeId": "onMlLdYqIjLTVstj",
        "name": "票据识别小助手V5(实验测试版)",
        "intro": "V5 极速四字段识别入库版\n\nV5 是在 V4 完整整合版基础上做出的性能优化版本，主要目标是对齐任务书演示场景，减少不必要的完整识别过程，只提取票据编号、日期、项目名称、合计金额四个核心字段，并快速完成数据库入库。\n\nV5 的核心流程为：流程开始 → 分析文件或图片后缀 → 判断文件类型。图片文件进入图片 AI 识别四字段 JSON，再通过图片 JSON 清洗代码节点整理结果；文档和表格文件先进",
        "avatar": "core/app/type/workflowFill",
        "flowNodeType": "appModule",
        "showStatus": true,
        "position": {
          "x": 1125,
          "y": -675
        },
        "version": "",
        "inputs": [
          {
            "key": "system_forbid_stream",
            "renderTypeList": [
              "switch"
            ],
            "valueType": "boolean",
            "label": "禁用流输出",
            "description": "强制设置嵌套运行的应用，均以非流模式运行",
            "value": true
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "用户输入的问题（问题需要完善）",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": [
          {
            "id": "history",
            "key": "history",
            "required": true,
            "label": "新的上下文",
            "description": "将本次回复内容拼接上历史记录，作为新的上下文返回",
            "valueType": "chatHistory",
            "valueDesc": "{\n  obj: System | Human | AI;\n  value: string;\n}[]",
            "type": "static"
          },
          {
            "id": "answerText",
            "key": "answerText",
            "required": false,
            "label": "AI 回复内容",
            "description": "将在 stream 回复完毕后触发",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "69ef2881b180ca8df8d5c846",
        "catchError": true
      }
    },
    {
      "key": "appModule_2",
      "title": "应用调用 appModule #2",
      "source_file": "1111111.json",
      "flowNodeType": "appModule",
      "pluginId": "69fd3ae6b180ca8df8df0bc0",
      "node": {
        "nodeId": "qixYx5DfuSs5L5XX",
        "name": "翻译 Copy",
        "intro": "",
        "avatar": "core/app/type/workflowFill",
        "flowNodeType": "appModule",
        "showStatus": true,
        "position": {
          "x": 1170,
          "y": 60
        },
        "version": "",
        "inputs": [
          {
            "key": "system_forbid_stream",
            "renderTypeList": [
              "switch"
            ],
            "valueType": "boolean",
            "label": "禁用流输出",
            "description": "强制设置嵌套运行的应用，均以非流模式运行",
            "value": false
          },
          {
            "key": "history",
            "renderTypeList": [
              "numberInput",
              "reference"
            ],
            "valueType": "chatHistory",
            "label": "聊天记录",
            "description": "最多携带多少轮对话记录",
            "required": true,
            "min": 0,
            "max": 50,
            "value": 6
          },
          {
            "key": "userChatInput",
            "renderTypeList": [
              "reference",
              "textarea"
            ],
            "valueType": "string",
            "label": "用户问题",
            "toolDescription": "用户输入的问题（问题需要完善）",
            "required": true,
            "value": [
              "448745",
              "userChatInput"
            ]
          }
        ],
        "outputs": [
          {
            "id": "history",
            "key": "history",
            "required": true,
            "label": "新的上下文",
            "description": "将本次回复内容拼接上历史记录，作为新的上下文返回",
            "valueType": "chatHistory",
            "valueDesc": "{\n  obj: System | Human | AI;\n  value: string;\n}[]",
            "type": "static"
          },
          {
            "id": "answerText",
            "key": "answerText",
            "required": false,
            "label": "AI 回复内容",
            "description": "将在 stream 回复完毕后触发",
            "valueType": "string",
            "type": "static",
            "valueDesc": ""
          },
          {
            "id": "system_error_text",
            "key": "system_error_text",
            "type": "error",
            "valueType": "string",
            "label": "错误信息",
            "valueDesc": "",
            "description": ""
          }
        ],
        "pluginId": "69fd3ae6b180ca8df8df0bc0",
        "catchError": false
      }
    }
  ]
}
```
