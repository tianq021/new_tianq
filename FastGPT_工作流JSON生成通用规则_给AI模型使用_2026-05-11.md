# FastGPT 工作流 JSON 生成通用规则（给 AI 模型使用）

版本：2026-05-11  
适用场景：让 AI 模型根据用户一句话需求，生成可导入 FastGPT 的工作流 JSON，或生成可手动配置的工作流模板。  
参考环境：FastGPT 云版 4.15.0 实测经验。  
核心目标：其他 AI 模型看完本文件后，可以按白名单节点、母版结构、组合模板和自检规则生成稳定的 FastGPT 工作流 JSON。

---

## 0. 总原则

FastGPT 工作流 JSON 生成不是让 AI 自由编造 `nodes / edges / chatConfig`，而是：

```text
用户需求
↓
理解意图
↓
选择已验证模板
↓
使用白名单节点母版
↓
替换少量参数
↓
生成 nodes / edges / chatConfig
↓
执行自检
↓
输出 JSON 文件
```

### 0.1 必须遵守的最高规则

1. 只能使用本文档中列出的白名单节点。
2. 未验证节点不要自动生成。
3. 不要写死 `datasetId`、`toolId`、API Key、数据库连接、私有模型 ID、用户文件 URL、`chatConfig._id`。
4. 节点 ID 必须唯一。
5. 每条边的 `source` 和 `target` 必须存在。
6. 每个变量引用 `['nodeId', 'outputId']` 中，`nodeId` 必须存在，`outputId` 必须在该节点 outputs 中存在。
7. 代码节点 `return` 的字段必须在 outputs 中声明。
8. 中间 AI 节点必须关闭直接输出，只让最终 answerNode 输出。
9. 固定文本和变量引用的写法不同，不能混用。
10. 生成后必须执行自检，不通过就不要交付。

---

## 1. FastGPT 工作流 JSON 顶层结构

### 1.1 顶层只保留 3 个字段

```json
{
  "nodes": [],
  "edges": [],
  "chatConfig": {}
}
```

不要输出其他顶层字段，尤其不要写：

```text
_id
appId
userId
teamId
datasetId
toolId
chatConfig._id
```

### 1.2 nodes

`nodes` 是节点数组，每个节点通常包含：

```json
{
  "nodeId": "unique_node_id",
  "name": "节点名称",
  "intro": "节点说明",
  "avatar": "core/workflow/template/...",
  "flowNodeType": "节点类型",
  "position": { "x": 0, "y": 0 },
  "version": "481",
  "inputs": [],
  "outputs": []
}
```

必须有：

```text
nodeId
name
flowNodeType
position
inputs
outputs
```

### 1.3 edges

`edges` 是连线数组。

普通连线：

```json
{
  "source": "source_node_id",
  "target": "target_node_id",
  "sourceHandle": "source_node_id-source-right",
  "targetHandle": "target_node_id-target-left"
}
```

判断器分支和问题分类分支有特殊 handle，后面单独说明。

### 1.4 chatConfig

推荐基础结构：

```json
{
  "variables": [],
  "scheduledTriggerConfig": {
    "cronString": "",
    "timezone": "Asia/Shanghai",
    "defaultPrompt": ""
  },
  "questionGuide": false,
  "ttsConfig": { "type": "web" },
  "whisperConfig": {
    "open": false,
    "autoSend": false,
    "autoTTSResponse": false
  },
  "chatInputGuide": {
    "open": false,
    "textList": [],
    "customUrl": ""
  },
  "instruction": "",
  "autoExecute": {
    "open": false,
    "defaultPrompt": ""
  },
  "welcomeText": "",
  "fileSelectConfig": {
    "canSelectFile": false,
    "canSelectImg": false,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 0
  }
}
```

需要文件上传时：

```json
"fileSelectConfig": {
  "canSelectFile": true,
  "canSelectImg": true,
  "canSelectVideo": false,
  "canSelectAudio": false,
  "canSelectCustomFileExtension": true,
  "customFileExtensionList": [".txt", ".md", ".pdf", ".docx", ".csv", ".xlsx", ".png", ".jpg", ".jpeg"],
  "maxFiles": 10
}
```

---

## 2. 变量引用规则

### 2.1 基础引用格式

FastGPT 变量引用使用数组：

```json
["上游节点ID", "输出ID"]
```

常见引用：

```json
["448745", "userChatInput"]
["code_node", "result"]
["ai_node", "answerText"]
["read_files", "system_text"]
```

### 2.2 变量引用输入字段写法

经验规则：变量引用字段尽量只写 `value`，不要强行写 `connected`、`selectedTypeIndex`，否则在某些节点中可能被识别成手动文本。

推荐：

```json
{
  "key": "userChatInput",
  "renderTypeList": ["reference", "textarea"],
  "valueType": "string",
  "label": "用户问题",
  "required": true,
  "value": ["448745", "userChatInput"]
}
```

不推荐在 AI 节点、分类节点、提取节点的用户输入里强行写：

```json
"connected": true,
"selectedTypeIndex": 1
```

### 2.3 固定文本和变量引用的区别

固定文本 answerNode：

```json
"connected": false,
"selectedTypeIndex": 0
```

变量引用 answerNode：

```json
"connected": true,
"selectedTypeIndex": 1
```

这是指定回复节点中最容易出错的地方。

---

## 3. 已验证节点白名单

以下节点可用于自动生成或半自动生成。

| 节点 | flowNodeType | 状态 | 说明 |
|---|---|---|---|
| 系统配置 | userGuide | tested | 工作流系统配置 |
| 流程开始 | workflowStart | tested | 获取用户输入，可输出 userChatInput/userFiles |
| 指定回复 | answerNode | tested | 固定文本或引用变量回复 |
| 代码运行 | code | tested | JS 处理、拼接、判断、清洗 |
| 判断器 | ifElseNode | tested | IF/ELSE 分支 |
| HTTP 请求 | httpRequest468 | tested GET | GET 已验证，POST/鉴权需单测 |
| 文档解析 | readFiles | tested | 读取 txt/pdf/docx/csv/xlsx 等上传文件 |
| AI 对话 | chatNode | tested | 基础 AI 对话、提取、摘要 |
| 知识库搜索 | datasetSearchNode | tested basic | 需手动绑定知识库或留空配置 |
| 问题分类 | classifyQuestion | structure tested | 分支结构可用，分类效果依赖描述 |
| 文本内容提取 | contentExtract | structure tested | 空结构可用，字段配置需单测 |
| 文本拼接 | textEditor | structure tested | 空结构可用，复杂变量需手动验证 |

---

## 4. 暂不推荐自动生成的高风险节点

以下节点暂时不要放入自动生成白名单，除非已经单独导出母版并测试成功。

| 节点 | 原因 |
|---|---|
| 用户选择 userSelect | 交互节点，分支 handle 和运行状态复杂 |
| 表单输入 formInput | 交互节点，表单字段结构复杂 |
| 工具调用 tools | 依赖工具列表、工具 ID、模型能力 |
| 变量更新 variableUpdate | 依赖全局变量配置，空配置可能不合法 |
| 批量执行 loop | 需要循环体/内部子流程，结构复杂，容易导致画布错误 |

原则：

```text
不知道真实导出结构时，不要猜。
```

---

## 5. 节点 JSON 母版库

下面是可复用的节点母版。生成时用占位符替换，例如：

```text
{{nodeId}}
{{name}}
{{x}}
{{y}}
{{reply_text}}
{{system_prompt}}
```

---

### 5.1 系统配置 userGuide 母版

```json
{
  "nodeId": "userGuide",
  "name": "系统配置",
  "intro": "可以配置应用的系统参数",
  "avatar": "core/workflow/template/systemConfig",
  "flowNodeType": "userGuide",
  "position": { "x": -1000, "y": 200 },
  "version": "481",
  "inputs": [
    {
      "key": "welcomeText",
      "renderTypeList": ["hidden"],
      "valueType": "string",
      "label": "core.app.Welcome Text",
      "value": "{{welcome_text}}"
    },
    {
      "key": "variables",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "label": "core.app.Chat Variable",
      "value": []
    },
    {
      "key": "questionGuide",
      "renderTypeList": ["hidden"],
      "valueType": "boolean",
      "label": "core.app.Question Guide",
      "value": false
    },
    {
      "key": "tts",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "label": "",
      "value": { "type": "web" }
    },
    {
      "key": "whisper",
      "renderTypeList": ["hidden"],
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
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "label": "",
      "value": null
    }
  ],
  "outputs": []
}
```

---

### 5.2 流程开始 workflowStart 母版

无文件上传：

```json
{
  "nodeId": "448745",
  "name": "流程开始",
  "intro": "",
  "avatar": "core/workflow/template/workflowStart",
  "flowNodeType": "workflowStart",
  "position": { "x": -1000, "y": 650 },
  "version": "481",
  "inputs": [
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
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
```

需要文件上传时，在 outputs 追加：

```json
{
  "id": "userFiles",
  "key": "userFiles",
  "label": "app:workflow.user_file_input",
  "description": "app:workflow.user_file_input_desc",
  "type": "static",
  "valueType": "arrayString"
}
```

并且 chatConfig 中打开 fileSelectConfig。

---

### 5.3 指定回复 answerNode 固定文本母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "该模块可以直接回复一段指定的内容。",
  "avatar": "core/workflow/template/reply",
  "flowNodeType": "answerNode",
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "inputs": [
    {
      "key": "text",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "any",
      "label": "core.module.input.label.Response content",
      "description": "core.module.input.description.Response content",
      "placeholder": "core.module.input.description.Response content",
      "required": true,
      "value": "{{reply_text}}",
      "connected": false,
      "selectedTypeIndex": 0
    }
  ],
  "outputs": []
}
```

---

### 5.4 指定回复 answerNode 变量引用母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "该模块可以直接回复一段指定的内容。",
  "avatar": "core/workflow/template/reply",
  "flowNodeType": "answerNode",
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "inputs": [
    {
      "key": "text",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "any",
      "label": "core.module.input.label.Response content",
      "description": "core.module.input.description.Response content",
      "placeholder": "core.module.input.description.Response content",
      "required": true,
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"],
      "connected": true,
      "selectedTypeIndex": 1
    }
  ],
  "outputs": []
}
```

---

### 5.5 代码运行 code 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "执行一段简单的脚本代码，通常用于进行复杂的数据处理。",
  "avatar": "core/workflow/template/codeRun",
  "flowNodeType": "code",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "482",
  "catchError": true,
  "inputs": [
    {
      "key": "system_addInputParam",
      "renderTypeList": ["addInputParam"],
      "valueType": "dynamic",
      "label": "",
      "required": false,
      "description": "workflow:these_variables_will_be_input_parameters_for_code_execution",
      "customInputConfig": {
        "selectValueTypeList": [
          "string", "number", "boolean", "object", "arrayString", "arrayNumber",
          "arrayBoolean", "arrayObject", "arrayAny", "any", "chatHistory",
          "datasetQuote", "dynamic", "selectDataset", "selectApp"
        ],
        "showDescription": false,
        "showDefaultValue": true
      }
    },
    {
      "key": "{{inputKey}}",
      "label": "{{inputKey}}",
      "renderTypeList": ["reference"],
      "valueType": "string",
      "required": true,
      "canEdit": true,
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"]
    },
    {
      "key": "codeType",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string",
      "value": "js"
    },
    {
      "key": "code",
      "renderTypeList": ["custom"],
      "label": "",
      "valueType": "string",
      "value": "{{js_code}}"
    }
  ],
  "outputs": [
    {
      "id": "system_rawResponse",
      "key": "system_rawResponse",
      "label": "workflow:full_response_data",
      "valueType": "object",
      "type": "static"
    },
    {
      "id": "error",
      "key": "error",
      "label": "workflow:error_text",
      "valueType": "string",
      "type": "error"
    },
    {
      "id": "system_addOutputParam",
      "key": "system_addOutputParam",
      "type": "dynamic",
      "valueType": "dynamic",
      "label": "",
      "customFieldConfig": {
        "selectValueTypeList": [
          "string", "number", "boolean", "object", "arrayString", "arrayNumber",
          "arrayBoolean", "arrayObject", "arrayAny", "any", "chatHistory",
          "datasetQuote", "dynamic", "selectDataset", "selectApp"
        ],
        "showDescription": false,
        "showDefaultValue": false
      },
      "description": "将代码中 return 的对象作为输出，传递给后续的节点。变量名需要对应 return 的 key"
    },
    {
      "id": "result",
      "key": "result",
      "label": "result",
      "valueType": "string",
      "type": "dynamic"
    }
  ]
}
```

代码必须：

```javascript
function main(params) {
  return { result: "..." };
}
```

---

### 5.6 AI 对话 chatNode 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "AI 大模型对话节点。",
  "avatar": "core/workflow/template/aiChat",
  "flowNodeType": "chatNode",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "4.9.7",
  "catchError": false,
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["settingLLMModel", "reference"],
      "label": "common:core.module.input.label.aiModel",
      "valueType": "string",
      "value": ""
    },
    { "key": "temperature", "renderTypeList": ["hidden"], "label": "", "valueType": "number", "value": 0 },
    { "key": "maxToken", "renderTypeList": ["hidden"], "label": "", "valueType": "number", "value": 2000 },
    { "key": "isResponseAnswerText", "renderTypeList": ["hidden"], "label": "", "value": {{isResponseAnswerText}}, "valueType": "boolean" },
    { "key": "aiChatQuoteRole", "renderTypeList": ["hidden"], "label": "", "valueType": "string", "value": "system" },
    { "key": "quoteTemplate", "renderTypeList": ["hidden"], "label": "", "valueType": "string" },
    { "key": "quotePrompt", "renderTypeList": ["hidden"], "label": "", "valueType": "string" },
    { "key": "aiChatVision", "renderTypeList": ["hidden"], "label": "", "valueType": "boolean", "value": true },
    { "key": "aiChatReasoning", "renderTypeList": ["hidden"], "label": "", "valueType": "boolean", "value": true },
    { "key": "aiChatTopP", "renderTypeList": ["hidden"], "label": "", "valueType": "number" },
    { "key": "aiChatStopSign", "renderTypeList": ["hidden"], "label": "", "valueType": "string" },
    { "key": "aiChatResponseFormat", "renderTypeList": ["hidden"], "label": "", "valueType": "string" },
    { "key": "aiChatJsonSchema", "renderTypeList": ["hidden"], "label": "", "valueType": "string" },
    {
      "key": "systemPrompt",
      "renderTypeList": ["textarea", "reference"],
      "maxLength": 100000,
      "isRichText": true,
      "valueType": "string",
      "label": "common:core.ai.Prompt",
      "description": "common:core.app.tip.systemPromptTip",
      "placeholder": "common:core.app.tip.chatNodeSystemPromptTip",
      "value": "{{system_prompt}}"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "common:core.module.input.label.chat history",
      "description": "workflow:max_dialog_rounds",
      "required": true,
      "min": 0,
      "max": 50,
      "value": 0
    },
    {
      "key": "quoteQA",
      "renderTypeList": ["settingDatasetQuotePrompt"],
      "label": "",
      "debugLabel": "知识库引用",
      "valueType": "datasetQuote",
      "description": ""
    },
    {
      "key": "fileUrlList",
      "renderTypeList": ["reference", "input"],
      "label": "app:workflow.user_file_input",
      "debugLabel": "文件链接",
      "description": "app:workflow.user_file_input_desc",
      "valueType": "arrayString",
      "value": []
    },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "workflow:user_question",
      "toolDescription": "用户问题",
      "required": true,
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"],
      "debugLabel": ""
    }
  ],
  "outputs": [
    {
      "id": "history",
      "key": "history",
      "required": true,
      "label": "common:core.module.output.label.New context",
      "description": "将本次回复内容拼接上历史记录，作为新的上下文返回",
      "valueType": "chatHistory",
      "type": "static"
    },
    {
      "id": "answerText",
      "key": "answerText",
      "required": true,
      "label": "common:core.module.output.label.Ai response content",
      "description": "将在 stream 回复完毕后触发",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "reasoningText",
      "key": "reasoningText",
      "required": false,
      "label": "workflow:reasoning_text",
      "valueType": "string",
      "type": "static",
      "invalid": true
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "type": "error",
      "valueType": "string",
      "label": "workflow:error_text"
    }
  ]
}
```

说明：

```text
中间 AI 节点：isResponseAnswerText=false
基础聊天且没有后续节点：isResponseAnswerText=true 或直接接 answerNode
```

---

### 5.7 判断器 ifElseNode 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "IF 条件成立走 IF 分支，否则走 ELSE 分支。",
  "avatar": "core/workflow/template/ifelse",
  "flowNodeType": "ifElseNode",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "inputs": [
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
              "variable": ["{{sourceNodeId}}", "{{sourceOutputId}}"],
              "condition": "equalTo",
              "value": {{expectedValue}},
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
      "type": "static"
    }
  ]
}
```

分支连线：

```text
IF:   {{nodeId}}-source-IF
ELSE: {{nodeId}}-source-ELSE
```

---

### 5.8 问题分类 classifyQuestion 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "{{name}}",
  "intro": "根据用户的历史记录和当前问题判断该次提问的类型。",
  "avatar": "core/workflow/template/questionClassify",
  "flowNodeType": "classifyQuestion",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "4.9.2",
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["selectLLMModel", "reference"],
      "label": "common:core.module.input.label.aiModel",
      "required": true,
      "valueType": "string",
      "llmModelType": "classify",
      "value": ""
    },
    {
      "key": "systemPrompt",
      "renderTypeList": ["textarea", "reference"],
      "maxLength": 100000,
      "isRichText": true,
      "valueType": "string",
      "label": "common:core.module.input.label.Background",
      "description": "common:core.module.input.description.Background",
      "placeholder": "common:core.module.input.placeholder.Classify background",
      "value": "{{classify_prompt}}"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "common:core.module.input.label.chat history",
      "description": "workflow:max_dialog_rounds",
      "required": true,
      "min": 0,
      "max": 50,
      "value": 0
    },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "workflow:user_question",
      "toolDescription": "用户输入的问题（问题需要完善）",
      "required": true,
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"]
    },
    {
      "renderTypeList": ["custom"],
      "valueType": "any",
      "label": "",
      "key": "agents",
      "value": [
        { "value": "{{class1_description}}", "key": "class1" },
        { "value": "{{class2_description}}", "key": "class2" }
      ]
    }
  ],
  "outputs": [
    {
      "id": "cqResult",
      "key": "cqResult",
      "required": true,
      "label": "workflow:classification_result",
      "valueType": "string",
      "type": "static"
    }
  ]
}
```

分支连线：

```text
class1: {{nodeId}}-source-class1
class2: {{nodeId}}-source-class2
```

---

### 5.9 知识库搜索 datasetSearchNode 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "知识库搜索",
  "intro": "导入后请手动选择知识库。",
  "avatar": "core/workflow/template/datasetSearch",
  "flowNodeType": "datasetSearchNode",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "inputs": [
    {
      "key": "datasets",
      "renderTypeList": ["selectDataset", "reference"],
      "label": "core.module.input.label.Select dataset",
      "value": [],
      "valueType": "selectDataset",
      "list": [],
      "required": true
    },
    { "key": "similarity", "renderTypeList": ["selectDatasetParamsModal"], "label": "", "value": 0.4, "valueType": "number" },
    { "key": "limit", "renderTypeList": ["hidden"], "label": "", "value": 5000, "valueType": "number" },
    { "key": "searchMode", "renderTypeList": ["hidden"], "label": "", "value": "embedding", "valueType": "string" },
    { "key": "usingReRank", "renderTypeList": ["hidden"], "label": "", "value": false, "valueType": "boolean" },
    { "key": "datasetSearchUsingExtensionQuery", "renderTypeList": ["hidden"], "label": "", "value": false, "valueType": "boolean" },
    { "key": "datasetSearchExtensionModel", "renderTypeList": ["hidden"], "label": "", "value": "", "valueType": "string" },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "label": "用户问题",
      "required": true,
      "valueType": "string",
      "toolDescription": "需要检索的内容",
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"]
    }
  ],
  "outputs": [
    {
      "id": "quoteQA",
      "key": "quoteQA",
      "label": "core.module.Dataset quote.label",
      "description": "特殊数组格式，搜索结果为空时返回空数组。",
      "type": "static",
      "valueType": "datasetQuote"
    }
  ]
}
```

注意：

```text
不要写死 datasetId。
导入后由用户手动选择知识库。
```

---

### 5.10 文档解析 readFiles 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "文档解析",
  "intro": "读取用户上传文件内容。",
  "avatar": "core/workflow/template/readFiles",
  "flowNodeType": "readFiles",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "4.9.2",
  "inputs": [
    {
      "key": "fileUrlList",
      "renderTypeList": ["reference"],
      "valueType": "arrayString",
      "label": "文件链接",
      "required": true,
      "value": ["448745", "userFiles"]
    }
  ],
  "outputs": [
    {
      "id": "system_text",
      "key": "system_text",
      "label": "文档解析结果",
      "description": "读取到的文件文本内容。",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "system_rawResponse",
      "key": "system_rawResponse",
      "label": "原始响应",
      "valueType": "arrayObject",
      "type": "static"
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "label": "错误信息",
      "valueType": "string",
      "type": "error"
    }
  ]
}
```

下游引用文本结果：

```json
["{{readFilesNodeId}}", "system_text"]
```

不要写成：

```text
text
rawResponse
error
```

---

### 5.11 HTTP 请求 httpRequest468 母版（GET）

```json
{
  "nodeId": "{{nodeId}}",
  "name": "HTTP 请求",
  "intro": "GET 请求节点。",
  "avatar": "core/workflow/template/httpRequest",
  "flowNodeType": "httpRequest468",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "catchError": true,
  "inputs": [
    {
      "key": "system_addInputParam",
      "renderTypeList": ["addInputParam"],
      "valueType": "dynamic",
      "label": "",
      "required": false,
      "description": "common:core.module.input.description.HTTP Dynamic Input",
      "customInputConfig": {
        "selectValueTypeList": [
          "string", "number", "boolean", "object", "arrayString", "arrayNumber",
          "arrayBoolean", "arrayObject", "arrayAny", "any", "chatHistory",
          "datasetQuote", "dynamic", "selectDataset", "selectApp"
        ],
        "showDescription": false,
        "showDefaultValue": true
      }
    },
    { "key": "system_httpMethod", "renderTypeList": ["custom"], "valueType": "string", "label": "", "value": "GET", "required": true },
    { "key": "system_httpTimeout", "renderTypeList": ["custom"], "valueType": "number", "label": "", "value": 30, "min": 5, "max": 600, "required": true },
    { "key": "system_httpReqUrl", "renderTypeList": ["hidden"], "valueType": "string", "label": "", "value": "{{url}}", "required": false },
    { "key": "system_header_secret", "renderTypeList": ["hidden"], "valueType": "object", "label": "", "value": {}, "required": false },
    { "key": "system_httpHeader", "renderTypeList": ["custom"], "valueType": "any", "value": [], "label": "", "required": false },
    { "key": "system_httpParams", "renderTypeList": ["hidden"], "valueType": "any", "value": [], "label": "", "required": false },
    { "key": "system_httpJsonBody", "renderTypeList": ["hidden"], "valueType": "any", "value": "", "label": "", "required": false },
    { "key": "system_httpFormBody", "renderTypeList": ["hidden"], "valueType": "any", "value": [], "label": "", "required": false },
    { "key": "system_httpContentType", "renderTypeList": ["hidden"], "valueType": "string", "value": "json", "label": "", "required": false }
  ],
  "outputs": [
    {
      "id": "httpRawResponse",
      "key": "httpRawResponse",
      "required": true,
      "label": "workflow:raw_response",
      "description": "HTTP请求的原始响应。",
      "valueType": "any",
      "type": "static"
    },
    {
      "id": "error",
      "key": "error",
      "label": "workflow:error_text",
      "valueType": "string",
      "type": "error"
    },
    {
      "id": "system_addOutputParam",
      "key": "system_addOutputParam",
      "type": "dynamic",
      "valueType": "dynamic",
      "label": "输出字段提取"
    }
  ]
}
```

下游引用：

```json
["{{httpNodeId}}", "httpRawResponse"]
```

---

### 5.12 文本内容提取 contentExtract 母版

结构可用，但字段配置需要业务补充。

```json
{
  "nodeId": "{{nodeId}}",
  "name": "文本内容提取",
  "intro": "导入后请手动选择模型、填写提取要求并添加目标字段。",
  "avatar": "core/workflow/template/extract",
  "flowNodeType": "contentExtract",
  "showStatus": true,
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "481",
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["selectLLMModel", "reference"],
      "label": "core.module.input.label.aiModel",
      "required": true,
      "valueType": "string",
      "value": ""
    },
    {
      "key": "description",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "string",
      "label": "提取要求描述",
      "description": "给AI一些对应的背景知识或要求描述，引导AI更好的完成任务。该输入框可使用全局变量。",
      "placeholder": "",
      "value": "{{extract_description}}"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "core.module.input.label.chat history",
      "required": true,
      "min": 0,
      "max": 30,
      "value": 0
    },
    {
      "key": "content",
      "renderTypeList": ["reference", "textarea"],
      "label": "需要提取的文本",
      "required": true,
      "valueType": "string",
      "toolDescription": "需要提取的内容",
      "value": ["{{sourceNodeId}}", "{{sourceOutputId}}"]
    },
    {
      "key": "extractKeys",
      "renderTypeList": ["custom"],
      "label": "",
      "valueType": "any",
      "description": "由描述和 key 组成一个目标字段，可提取多个目标字段。",
      "value": []
    }
  ],
  "outputs": [
    {
      "id": "success",
      "key": "success",
      "label": "字段完全提取",
      "valueType": "boolean",
      "type": "static"
    },
    {
      "id": "fields",
      "key": "fields",
      "label": "完整提取结果",
      "description": "一个 JSON 字符串。",
      "valueType": "string",
      "type": "static"
    }
  ]
}
```

如果不配置 extractKeys，输出 `{}` 是正常的。

---

### 5.13 文本拼接 textEditor 母版

```json
{
  "nodeId": "{{nodeId}}",
  "name": "文本拼接",
  "intro": "导入后可手动填写拼接文本。",
  "avatar": "core/workflow/template/textConcat",
  "flowNodeType": "textEditor",
  "position": { "x": {{x}}, "y": {{y}} },
  "version": "486",
  "inputs": [
    {
      "key": "system_addInputParam",
      "renderTypeList": ["addInputParam"],
      "valueType": "dynamic",
      "label": "",
      "required": false,
      "description": "workflow:dynamic_input_description_concat",
      "customInputConfig": {
        "selectValueTypeList": [
          "string", "number", "boolean", "object", "arrayString", "arrayNumber",
          "arrayBoolean", "arrayObject", "arrayAny", "any", "chatHistory",
          "datasetQuote", "dynamic", "selectDataset", "selectApp"
        ],
        "showDescription": false,
        "showDefaultValue": false
      }
    },
    {
      "key": "system_textareaInput",
      "renderTypeList": ["textarea"],
      "valueType": "string",
      "required": true,
      "label": "拼接文本",
      "placeholder": "workflow:input_variable_list",
      "value": "{{concat_text}}"
    }
  ],
  "outputs": [
    {
      "id": "system_text",
      "key": "system_text",
      "label": "workflow:concatenation_result",
      "type": "static",
      "valueType": "string",
      "description": ""
    }
  ]
}
```

注意：如果文本拼接变量不好配置，可以优先用代码节点拼接字符串，代码节点更稳定。

---

## 6. 工作流组合模板库

### 6.1 固定回复模板 simple_reply.basic.v1

适用：用户要求输入任意内容后固定回复。

```text
workflowStart -> answerNode
```

必要节点：

```text
userGuide
workflowStart
answerNode 固定文本
```

---

### 6.2 无输入代码任务 code_task.no_input.v1

适用：随机数、验证码、UUID、当前时间、固定计算。

```text
workflowStart -> code -> answerNode
```

代码示例：

```javascript
function main(params) {
  const n = Math.floor(100000 + Math.random() * 900000);
  return { result: String(n) };
}
```

---

### 6.3 有输入代码任务 code_task.with_input.v1

适用：统计字数、转大写、判断手机号、提取数字、文本清洗。

```text
workflowStart -> code(userChatInput) -> answerNode
```

代码示例：

```javascript
function main(params) {
  const text = String(params.user_input || '');
  return { result: String(text.length) };
}
```

---

### 6.4 AI 对话模板 ai_chat.basic.v1

适用：普通问答助手、学习助手、总结助手。

```text
workflowStart -> chatNode -> answerNode
```

中间没有后续处理时，可以让 chatNode 直接输出；如果接 answerNode，建议 `isResponseAnswerText=false`，由 answerNode 统一输出。

---

### 6.5 知识库问答模板 kb_qa.basic.v1

适用：知识库客服、文档问答、模板检索。

```text
workflowStart -> datasetSearchNode -> chatNode -> answerNode
```

注意：

```text
不要写死 datasetId。
导入后手动选择知识库。
chatNode 的 quoteQA 需要引用 datasetSearchNode.quoteQA 时，必须用真实导出结构再验证；如果不确定，先把 datasetSearchNode 输出给 answerNode 观察。
```

---

### 6.6 文件解析模板 readfiles.basic.v1

适用：上传 TXT/PDF/DOCX/CSV/XLSX 并读取内容。

```text
workflowStart(userFiles) -> readFiles -> answerNode
```

注意：

```text
workflowStart.outputs 必须有 userFiles。
chatConfig.fileSelectConfig 必须开启文件上传。
readFiles.fileUrlList 引用 ["448745", "userFiles"]。
```

---

### 6.7 判断器分支模板 if_else.basic.v1

适用：判断是否为空、是否等于某值、是否通过校验。

```text
workflowStart/code -> ifElseNode -> IF answer / ELSE answer
```

推荐：复杂判断先用 code 输出 boolean，再由 ifElseNode 判断 boolean。

---

### 6.8 问题分类分支模板 classify_route.basic.v1

适用：意图识别、语义路由、任务类型分类。

```text
workflowStart -> classifyQuestion -> 分类1分支 / 分类2分支 / 其他分支
```

注意：

```text
分类描述必须具体，不能只写“分类1”“分类2”。
数字精确分流不适合问题分类，应用代码节点或判断器。
```

---

### 6.9 AI 结构化 JSON 提取模板 ai_extract_json.basic.v1

适用：从自然语言提取姓名、手机号、日期、金额、行动项等结构化信息。

推荐结构：

```text
workflowStart -> chatNode(isResponseAnswerText=false) -> code_clean_json -> answerNode
```

如果只教学演示，也可以：

```text
workflowStart -> chatNode(JSON only) -> answerNode
```

但更稳定的是加代码节点清洗 Markdown 代码块。

---

### 6.10 HTTP GET 模板 http_get.basic.v1

适用：公开 GET API 调用。

```text
workflowStart -> httpRequest468 -> answerNode
```

注意：POST、鉴权、动态 header、动态 body 需要单独验证。

---

## 7. 用户需求到模板的选择规则

| 用户需求关键词 | 推荐模板 |
|---|---|
| 固定回复、回复 hello、输入任意内容都回复 | simple_reply.basic.v1 |
| 随机数、验证码、UUID、当前时间 | code_task.no_input.v1 |
| 统计字数、手机号判断、文本清洗、转大写 | code_task.with_input.v1 |
| AI 助手、聊天机器人、学习助手、回答问题 | ai_chat.basic.v1 |
| 知识库客服、根据知识库回答、搜索模板 | kb_qa.basic.v1 |
| 上传文件、PDF、DOCX、CSV、读取文档 | readfiles.basic.v1 |
| 如果……否则……、条件分支 | if_else.basic.v1 |
| 按问题类型分流、意图识别 | classify_route.basic.v1 |
| 提取字段、整理 JSON、信息抽取 | ai_extract_json.basic.v1 或 contentExtract |
| 调用接口、HTTP GET | http_get.basic.v1 |

---

## 8. 生成流程

其他 AI 生成工作流 JSON 时，按下面步骤执行：

### 第 1 步：理解需求

输出内部 plan：

```json
{
  "user_need": "用户想做什么",
  "workflow_type": "code_task_with_input",
  "template_id": "code_task.with_input.v1",
  "reason": "为什么选这个模板"
}
```

### 第 2 步：选择模板

只从组合模板库选择。

### 第 3 步：选择节点

只从白名单节点选择。

### 第 4 步：生成 nodeId

建议命名规则：

```text
workflowStart 固定用 448745
reply_xxx
code_xxx
ai_xxx
if_xxx
classify_xxx
read_files_xxx
http_xxx
```

### 第 5 步：生成 nodes

从节点母版复制，不要凭空编写未知字段。

### 第 6 步：生成 edges

普通边：

```text
sourceHandle = sourceNodeId-source-right
targetHandle = targetNodeId-target-left
```

分类边：

```text
sourceHandle = classifyNodeId-source-classKey
```

判断器边：

```text
sourceHandle = ifNodeId-source-IF
sourceHandle = ifNodeId-source-ELSE
```

### 第 7 步：生成 chatConfig

按是否文件上传决定 fileSelectConfig。

### 第 8 步：自检

必须执行第 9 章自检清单。

---

## 9. 自检清单

生成完 JSON 后逐项检查。

### 9.1 节点检查

```text
[ ] 顶层是否只有 nodes、edges、chatConfig
[ ] 每个 nodeId 是否唯一
[ ] 每个节点是否有 position.x / position.y
[ ] 每个节点是否有 flowNodeType
[ ] 每个节点是否有 inputs / outputs
[ ] 是否使用了高风险未验证节点
```

### 9.2 连线检查

```text
[ ] 每条 edge.source 是否存在于 nodes
[ ] 每条 edge.target 是否存在于 nodes
[ ] 普通边 handle 是否是 nodeId-source-right / nodeId-target-left
[ ] 判断器 IF/ELSE handle 是否正确
[ ] 问题分类 class key handle 是否正确
```

### 9.3 变量引用检查

```text
[ ] 每个 [nodeId, outputId] 的 nodeId 是否存在
[ ] outputId 是否在该节点 outputs.id 中存在
[ ] workflowStart.userChatInput 是否存在
[ ] 使用 userFiles 时 workflowStart.outputs 是否声明 userFiles
[ ] 使用 readFiles 时 chatConfig.fileSelectConfig 是否开启
```

### 9.4 answerNode 检查

```text
[ ] answerNode 输入 key 是否是 text
[ ] 固定文本是否 connected=false selectedTypeIndex=0
[ ] 变量引用是否 connected=true selectedTypeIndex=1
[ ] 变量引用是否引用了真实 output.id
```

### 9.5 code 节点检查

```text
[ ] JS 是否包含 function main(params)
[ ] 是否 return object
[ ] return 的字段是否在 outputs 中声明
[ ] outputs 的 id 和 key 是否与 return 字段一致
```

### 9.6 AI 节点检查

```text
[ ] 中间 AI 节点 isResponseAnswerText=false
[ ] 最终输出是否只由 answerNode 展示
[ ] 模型字段是否未写死不可用模型
[ ] 用户问题引用是否正确
```

### 9.7 禁止项检查

```text
[ ] 不包含 API Key
[ ] 不包含数据库连接
[ ] 不包含 datasetId
[ ] 不包含 toolId
[ ] 不包含真实用户文件 URL
[ ] 不包含 chatConfig._id
```

---

## 10. 最小完整示例：固定回复工作流

```json
{
  "nodes": [
    {
      "nodeId": "userGuide",
      "name": "系统配置",
      "intro": "可以配置应用的系统参数",
      "avatar": "core/workflow/template/systemConfig",
      "flowNodeType": "userGuide",
      "position": { "x": -1000, "y": 200 },
      "version": "481",
      "inputs": [
        { "key": "welcomeText", "renderTypeList": ["hidden"], "valueType": "string", "label": "core.app.Welcome Text", "value": "这是一个固定回复工作流。" },
        { "key": "variables", "renderTypeList": ["hidden"], "valueType": "any", "label": "core.app.Chat Variable", "value": [] },
        { "key": "questionGuide", "renderTypeList": ["hidden"], "valueType": "boolean", "label": "core.app.Question Guide", "value": false },
        { "key": "tts", "renderTypeList": ["hidden"], "valueType": "any", "label": "", "value": { "type": "web" } },
        { "key": "whisper", "renderTypeList": ["hidden"], "valueType": "any", "label": "", "value": { "open": false, "autoSend": false, "autoTTSResponse": false } },
        { "key": "scheduleTrigger", "renderTypeList": ["hidden"], "valueType": "any", "label": "", "value": null }
      ],
      "outputs": []
    },
    {
      "nodeId": "448745",
      "name": "流程开始",
      "intro": "",
      "avatar": "core/workflow/template/workflowStart",
      "flowNodeType": "workflowStart",
      "position": { "x": -1000, "y": 650 },
      "version": "481",
      "inputs": [
        { "key": "userChatInput", "renderTypeList": ["reference", "textarea"], "valueType": "string", "label": "workflow:user_question", "required": true, "toolDescription": "用户问题", "debugLabel": "" }
      ],
      "outputs": [
        { "id": "userChatInput", "key": "userChatInput", "label": "common:core.module.input.label.user question", "type": "static", "valueType": "string", "description": "" }
      ]
    },
    {
      "nodeId": "reply_fixed",
      "name": "指定回复",
      "intro": "该模块可以直接回复一段指定的内容。",
      "avatar": "core/workflow/template/reply",
      "flowNodeType": "answerNode",
      "position": { "x": -400, "y": 650 },
      "version": "481",
      "inputs": [
        {
          "key": "text",
          "renderTypeList": ["textarea", "reference"],
          "valueType": "any",
          "label": "core.module.input.label.Response content",
          "description": "core.module.input.description.Response content",
          "placeholder": "core.module.input.description.Response content",
          "required": true,
          "value": "hello",
          "connected": false,
          "selectedTypeIndex": 0
        }
      ],
      "outputs": []
    }
  ],
  "edges": [
    {
      "source": "448745",
      "target": "reply_fixed",
      "sourceHandle": "448745-source-right",
      "targetHandle": "reply_fixed-target-left"
    }
  ],
  "chatConfig": {
    "variables": [],
    "scheduledTriggerConfig": { "cronString": "", "timezone": "Asia/Shanghai", "defaultPrompt": "" },
    "questionGuide": false,
    "ttsConfig": { "type": "web" },
    "whisperConfig": { "open": false, "autoSend": false, "autoTTSResponse": false },
    "chatInputGuide": { "open": false, "textList": [], "customUrl": "" },
    "instruction": "",
    "autoExecute": { "open": false, "defaultPrompt": "" },
    "welcomeText": "这是一个固定回复工作流。",
    "fileSelectConfig": { "canSelectFile": false, "canSelectImg": false, "canSelectVideo": false, "canSelectAudio": false, "maxFiles": 0 }
  }
}
```

---

## 11. 测试方法

### 11.1 导入后先看画布

```text
1. 页面是否炸
2. 节点是否显示
3. 连线是否显示
4. 用户问题是否显示为“流程开始 > 用户问题”
5. answerNode 是否显示为固定文本或正确变量引用
```

### 11.2 逐节点测试

不要一开始生成很多高风险节点。推荐：

```text
固定回复
代码节点
判断器
HTTP GET
文档解析
AI 对话
知识库搜索
问题分类
文本提取
文本拼接
```

### 11.3 组合测试

先只组合已验证节点：

```text
workflowStart
├─ code -> answer
├─ ifElse -> answer/answer
├─ http -> answer
├─ readFiles -> answer
├─ chatNode -> answer
└─ datasetSearch -> answer
```

不要把用户选择、表单输入、工具调用、变量更新、批量执行混在一个大文件中。

---

## 12. 常见错误与修复

### 12.1 前端报 position undefined

可能原因：

```text
1. 某条 edge 指向不存在的节点；
2. 某个高风险节点结构不完整；
3. 批量执行、工具调用、用户选择、表单输入等节点 handle 猜错；
4. 节点缺少 position。
```

修复：

```text
1. 删除高风险节点；
2. 单独测试节点；
3. 检查 edge.source/target；
4. 检查每个节点 position。
```

### 12.2 变量引用变成文本

表现：

```text
输入框显示 ["448745", "userChatInput"]
```

修复：

```text
变量引用字段只写 value，不强行写 connected / selectedTypeIndex。
answerNode 例外：answerNode 固定文本和变量引用需要 selectedTypeIndex。
```

### 12.3 中间 AI 输出泄露

表现：

```text
用户看到中间 JSON、表格、摘要，然后又看到最终结果。
```

修复：

```text
中间 AI 节点 isResponseAnswerText=false。
只让最后 answerNode 输出。
```

### 12.4 代码节点输出为空

原因：

```text
return 字段未在 outputs 声明。
```

修复：

```text
return { result: "..." }
outputs 里必须有 id=result key=result。
```

### 12.5 readFiles 没有内容

检查：

```text
workflowStart 是否有 userFiles 输出；
chatConfig.fileSelectConfig 是否开启文件上传；
readFiles.fileUrlList 是否引用 ["448745", "userFiles"]；
用户是否真的上传了文件。
```

---

## 13. 给其他 AI 模型的强制指令

如果你是另一个 AI 模型，请严格执行：

```text
你不是在自由创作 FastGPT JSON。
你是在根据已验证母版替换参数生成 JSON。

必须：
1. 先判断用户需求属于哪个模板。
2. 只使用白名单节点。
3. 复制节点母版，不要猜测未知字段。
4. 不要写死 datasetId、toolId、API Key、数据库连接、私有模型 ID。
5. 固定回复使用 answerNode 固定文本写法。
6. 中间 AI 节点必须关闭直接输出。
7. 所有 code return 字段必须声明 outputs。
8. 所有 edges source/target 必须存在。
9. 所有变量引用必须指向真实 outputs.id。
10. 生成后必须执行自检清单。
11. 如果需求需要未验证节点，输出“需要手动搭建母版”，不要强行生成完整 JSON。
```

---

## 14. 最终建议

稳定路线：

```text
简单需求：直接生成完整 JSON。
复杂需求：先生成节点方案或使用已验证组合模板。
未知节点：先手动搭建并导出母版，再加入白名单。
```

目前可稳定生成的核心能力：

```text
固定回复
代码处理
判断分支
HTTP GET
文档解析
AI 对话
知识库搜索
问题分类结构
文本内容提取结构
文本拼接结构
```

暂不稳定自动生成：

```text
用户选择
表单输入
工具调用
变量更新
批量执行
数据库连接
复杂插件调用
```

