# FastGPT 单节点母版与工作流拼接规则（给 AI 模型使用）

版本：2026-05-11  
定位：给其他 AI 模型看的“节点写法 + 连接规则 + 拼装规则”文档。  
目标：让 AI 模型至少知道 FastGPT 工作流 JSON 的节点应该怎么写、节点之间怎么连、哪些地方不能编造、哪些地方必须提醒用户手动配置。

---

## 0. 最重要的原则

本文件不是让 AI 自由幻想 FastGPT 节点。

AI 只能做：

1. 识别用户一句话需求；
2. 选择真实存在的 FastGPT 节点类型；
3. 使用本文件里的“单节点母版”生成节点；
4. 按连接规则生成 edges；
5. 对无法确定的内容明确提醒“需要手动配置”。

AI 禁止做：

1. 禁止编造不存在的 `flowNodeType`；
2. 禁止编造 `datasetId`、`toolId`、`pluginId`；
3. 禁止编造 API Key、数据库连接、账号密码；
4. 禁止编造私有模型名；
5. 禁止把普通文本引用、文件数组引用、文本插值混成一种；
6. 禁止把判断器分支写成 `true/false`；
7. 禁止把问题分类节点分支写成分类名称，应该使用 `agents.key`。

一句话目标应该写成：

```text
一句话生成对应 FastGPT 工作流 JSON 或工作流模板。
能自动确定的内容自动生成；
不能确定或涉及平台私有配置的内容，必须提醒用户手动填写。
```

---

## 1. FastGPT 工作流 JSON 的基本结构

一个可导入工作流通常包含：

```json
{
  "nodes": [],
  "edges": [],
  "chatConfig": {}
}
```

有些导出文件可能还带应用名称、头像、类型等外层字段，但最核心的是：

```text
nodes      节点列表
edges      节点连接线
chatConfig 应用聊天配置，比如文件上传、开场白、变量等
```

---

## 2. 单个节点的基本结构

每个节点一般长这样：

```json
{
  "nodeId": "node_start",
  "name": "流程开始",
  "intro": "",
  "avatar": "core/workflow/template/workflowStart",
  "flowNodeType": "workflowStart",
  "position": {
    "x": 0,
    "y": 0
  },
  "version": "481",
  "inputs": [],
  "outputs": []
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `nodeId` | 当前工作流内唯一 ID，不能重复 |
| `name` | 节点显示名称 |
| `intro` | 节点说明，可为空 |
| `avatar` | 节点图标路径，建议参考母版 |
| `flowNodeType` | 真正决定节点类型的字段，不能乱写 |
| `position` | 画布位置 |
| `version` | 平台节点版本，常见 `481` |
| `inputs` | 节点输入配置 |
| `outputs` | 节点输出配置 |

---

## 3. input 输入项结构

常见 input：

```json
{
  "key": "userChatInput",
  "renderTypeList": ["reference", "textarea"],
  "valueType": "string",
  "label": "用户问题",
  "required": true,
  "value": ["node_start", "userChatInput"],
  "selectedTypeIndex": 0
}
```

重要字段：

| 字段 | 说明 |
|---|---|
| `key` | 输入参数名，后端运行时用它取值 |
| `renderTypeList` | 这个输入可以用什么 UI 类型 |
| `valueType` | 值类型，如 `string`、`number`、`boolean`、`arrayString`、`any` |
| `value` | 实际值，可以是固定文本，也可以是引用 |
| `required` | 是否必填 |
| `selectedTypeIndex` | 当前使用 `renderTypeList` 的第几个类型 |

### 3.1 `selectedTypeIndex` 比 `connected` 更关键

如果：

```json
"renderTypeList": ["textarea", "reference"]
```

那么：

```json
"selectedTypeIndex": 0
```

表示使用固定文本输入。

```json
"selectedTypeIndex": 1
```

表示使用引用。

部分旧导出里可能有：

```json
"connected": true
```

可以保留兼容，但真正关键是：

```text
renderTypeList + selectedTypeIndex + value
```

---

## 4. output 输出项结构

常见 output：

```json
{
  "id": "answerText",
  "key": "answerText",
  "label": "AI 回复内容",
  "valueType": "string",
  "type": "static"
}
```

重要字段：

| 字段 | 说明 |
|---|---|
| `id` | 被其他节点引用时用的输出 ID |
| `key` | 输出 key，通常和 id 一致 |
| `label` | 显示名称 |
| `valueType` | 输出值类型 |
| `type` | 常见 `static`、`dynamic`、`error` |

引用上游输出时，必须引用 `outputs` 中真实存在的 `id`。

---

## 5. 变量引用规则

### 5.1 单字段引用

普通文本、数字、布尔、对象等单个值引用：

```json
["上游节点ID", "输出ID"]
```

例：

```json
["node_start", "userChatInput"]
```

AI 节点引用用户输入：

```json
{
  "key": "userChatInput",
  "renderTypeList": ["reference", "textarea"],
  "valueType": "string",
  "required": true,
  "value": ["node_start", "userChatInput"],
  "selectedTypeIndex": 0
}
```

如果 `renderTypeList` 是：

```json
["textarea", "reference"]
```

那引用时要写：

```json
"selectedTypeIndex": 1
```

---

### 5.2 文件列表引用

文件上传不是单引用，而是二维数组引用。

正确：

```json
[["node_start", "userFiles"]]
```

错误：

```json
["node_start", "userFiles"]
```

文件解析节点 `readFiles.fileUrlList` 应该这样写：

```json
{
  "key": "fileUrlList",
  "renderTypeList": ["reference"],
  "valueType": "arrayString",
  "label": "文件链接",
  "required": true,
  "value": [["node_start", "userFiles"]]
}
```

---

### 5.3 文本插值引用

文本拼接、提示词、固定回复中可以使用插值格式：

```text
{{$节点ID.输出ID$}}
```

例：

```text
请根据下面内容生成总结：

{{$read_files.system_text$}}
```

适合：

```text
textEditor 文本拼接节点
AI systemPrompt
answerNode 固定文本混排
```

---

## 6. 边 edges 的基本结构

普通连接线：

```json
{
  "source": "node_start",
  "target": "node_ai",
  "sourceHandle": "node_start-source-right",
  "targetHandle": "node_ai-target-left"
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `source` | 起点节点 ID |
| `target` | 终点节点 ID |
| `sourceHandle` | 起点 handle |
| `targetHandle` | 终点 handle |

普通节点一般用：

```text
sourceHandle = `${sourceNodeId}-source-right`
targetHandle = `${targetNodeId}-target-left`
```

---

## 7. 分支节点连接规则

### 7.1 判断器 ifElseNode 分支

判断器分支不是 `true/false`。

判断器分支 handle 是：

```text
节点ID-source-IF
节点ID-source-ELSE
节点ID-source-ELSE IF 1
节点ID-source-ELSE IF 2
```

单个 IF + ELSE 示例：

```json
[
  {
    "source": "node_if",
    "target": "node_valid_ai",
    "sourceHandle": "node_if-source-IF",
    "targetHandle": "node_valid_ai-target-left"
  },
  {
    "source": "node_if",
    "target": "node_invalid_answer",
    "sourceHandle": "node_if-source-ELSE",
    "targetHandle": "node_invalid_answer-target-left"
  }
]
```

---

### 7.2 问题分类 classifyQuestion 分支

分类节点分支 handle 使用 `agents.key`，不是 `agents.value`。

如果 agents 是：

```json
[
  {
    "key": "translate",
    "value": "翻译类问题"
  },
  {
    "key": "summary",
    "value": "总结类问题"
  },
  {
    "key": "other",
    "value": "其他问题"
  }
]
```

那么分支连接是：

```json
[
  {
    "source": "node_classify",
    "target": "node_translate_ai",
    "sourceHandle": "node_classify-source-translate",
    "targetHandle": "node_translate_ai-target-left"
  },
  {
    "source": "node_classify",
    "target": "node_summary_ai",
    "sourceHandle": "node_classify-source-summary",
    "targetHandle": "node_summary_ai-target-left"
  },
  {
    "source": "node_classify",
    "target": "node_other_answer",
    "sourceHandle": "node_classify-source-other",
    "targetHandle": "node_other_answer-target-left"
  }
]
```

---

# 8. 单节点母版库

下面是常用单节点母版。AI 生成工作流时，应从这些母版复制，再修改：

```text
nodeId
name
position
输入 value
提示词
动态 outputs
```

---

## 8.1 系统配置节点 userGuide / systemConfig

用途：保存开场白、聊天变量、问题引导、语音配置、文件上传配置相关兼容信息。

母版：

```json
{
  "nodeId": "userGuide",
  "name": "系统配置",
  "intro": "可以配置应用的系统参数",
  "avatar": "core/workflow/template/systemConfig",
  "flowNodeType": "userGuide",
  "position": {
    "x": -1000,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "welcomeText",
      "renderTypeList": ["hidden"],
      "valueType": "string",
      "label": "core.app.Welcome Text",
      "value": ""
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
      "valueType": "any",
      "label": "core.app.Question Guide",
      "value": {
        "open": false
      }
    },
    {
      "key": "tts",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "label": "",
      "value": {
        "type": "web"
      }
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

注意：

```text
systemConfig 节点本身不参与运行连线。
建议保留，但不要把业务逻辑写在这里。
```

---

## 8.2 流程开始节点 workflowStart：纯文本版

用途：接收用户输入文本。

母版：

```json
{
  "nodeId": "node_start",
  "name": "流程开始",
  "intro": "",
  "avatar": "core/workflow/template/workflowStart",
  "flowNodeType": "workflowStart",
  "position": {
    "x": 0,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "用户问题",
      "required": true,
      "toolDescription": "用户问题"
    }
  ],
  "outputs": [
    {
      "id": "userChatInput",
      "key": "userChatInput",
      "label": "用户问题",
      "valueType": "string",
      "type": "static"
    }
  ]
}
```

---

## 8.3 流程开始节点 workflowStart：文件上传版

用途：接收用户输入文本 + 上传文件。

母版：

```json
{
  "nodeId": "node_start",
  "name": "流程开始",
  "intro": "",
  "avatar": "core/workflow/template/workflowStart",
  "flowNodeType": "workflowStart",
  "position": {
    "x": 0,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "用户问题",
      "required": true,
      "toolDescription": "用户问题"
    }
  ],
  "outputs": [
    {
      "id": "userChatInput",
      "key": "userChatInput",
      "label": "用户问题",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "userFiles",
      "key": "userFiles",
      "label": "用户上传文件",
      "description": "用户上传的文件链接列表",
      "type": "static",
      "valueType": "arrayString"
    }
  ]
}
```

文件上传版必须同时设置 `chatConfig.fileSelectConfig`，见后文。

---

## 8.4 AI 对话节点 chatNode

用途：调用大模型处理文本、翻译、总结、分类解释、生成结构化内容等。

母版：

```json
{
  "nodeId": "node_ai",
  "name": "AI 对话",
  "intro": "AI 对话节点",
  "avatar": "core/workflow/template/aiChat",
  "flowNodeType": "chatNode",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["settingLLMModel", "reference"],
      "label": "AI 模型",
      "valueType": "string"
    },
    {
      "key": "temperature",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "number"
    },
    {
      "key": "maxToken",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "number"
    },
    {
      "key": "isResponseAnswerText",
      "renderTypeList": ["hidden"],
      "label": "",
      "value": false,
      "valueType": "boolean"
    },
    {
      "key": "aiChatQuoteRole",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string",
      "value": "system"
    },
    {
      "key": "quoteTemplate",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string"
    },
    {
      "key": "quotePrompt",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string"
    },
    {
      "key": "aiChatVision",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "boolean",
      "value": true
    },
    {
      "key": "aiChatReasoning",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "boolean",
      "value": true
    },
    {
      "key": "systemPrompt",
      "renderTypeList": ["textarea", "reference"],
      "maxLength": 100000,
      "isRichText": true,
      "valueType": "string",
      "label": "提示词",
      "value": "你是一个有帮助的 AI 助手。"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "聊天记录",
      "required": true,
      "min": 0,
      "max": 50,
      "value": 6
    },
    {
      "key": "quoteQA",
      "renderTypeList": ["settingDatasetQuotePrompt"],
      "label": "",
      "debugLabel": "知识库引用",
      "description": "",
      "valueType": "datasetQuote"
    },
    {
      "key": "fileUrlList",
      "renderTypeList": ["reference", "input"],
      "label": "用户上传文件",
      "debugLabel": "用户上传文件",
      "description": "用户上传文件链接",
      "valueType": "arrayString"
    },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "用户问题",
      "required": true,
      "toolDescription": "用户问题",
      "value": ["node_start", "userChatInput"],
      "selectedTypeIndex": 0
    }
  ],
  "outputs": [
    {
      "id": "history",
      "key": "history",
      "required": true,
      "label": "新的上下文",
      "description": "新的上下文",
      "valueType": "chatHistory",
      "type": "static"
    },
    {
      "id": "answerText",
      "key": "answerText",
      "required": true,
      "label": "AI 回复内容",
      "description": "AI 回复内容",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "reasoningText",
      "key": "reasoningText",
      "required": false,
      "label": "推理内容",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "type": "error",
      "valueType": "string",
      "label": "错误信息"
    }
  ]
}
```

注意：

```text
1. 中间 AI 节点建议 isResponseAnswerText=false，避免中间结果直接输出给用户。
2. 最终输出建议使用 answerNode。
3. model 可以留空，但导入后必须手动选择可用模型。
4. 如果平台模型配置坏了，JSON 正确也无法运行。
```

---

## 8.5 指定回复节点 answerNode

用途：把固定文本或上游变量输出给用户。

### 8.5.1 固定文本版

```json
{
  "nodeId": "node_answer",
  "name": "指定回复",
  "intro": "指定回复内容",
  "avatar": "core/workflow/template/reply",
  "flowNodeType": "answerNode",
  "position": {
    "x": 1000,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "text",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "any",
      "required": true,
      "isRichText": false,
      "maxLength": 100000,
      "label": "回复内容",
      "value": "请输入需要处理的文本。"
    }
  ],
  "outputs": []
}
```

### 8.5.2 引用上游 AI 输出版

```json
{
  "nodeId": "node_answer",
  "name": "指定回复",
  "intro": "指定回复内容",
  "avatar": "core/workflow/template/reply",
  "flowNodeType": "answerNode",
  "position": {
    "x": 1000,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "text",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "any",
      "required": true,
      "isRichText": false,
      "maxLength": 100000,
      "label": "回复内容",
      "value": ["node_ai", "answerText"],
      "selectedTypeIndex": 1
    }
  ],
  "outputs": []
}
```

---

## 8.6 判断器节点 ifElseNode

用途：按条件分支执行。

母版：

```json
{
  "nodeId": "node_if",
  "name": "判断器",
  "intro": "根据条件执行不同分支",
  "avatar": "core/workflow/template/ifelse",
  "flowNodeType": "ifElseNode",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
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
              "variable": ["node_check", "is_valid"],
              "condition": "equalTo",
              "value": "yes",
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

常用条件：

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
lessThan
greaterThanOrEqualTo
lessThanOrEqualTo
lengthEqualTo
lengthGreaterThan
lengthLessThan
```

连接分支：

```text
node_if-source-IF
node_if-source-ELSE
node_if-source-ELSE IF 1
```

---

## 8.7 代码运行节点 code

用途：输入校验、字段整理、JSON 清洗、格式转换、简单计算。

母版：

```json
{
  "nodeId": "node_code",
  "name": "代码运行",
  "intro": "执行 JS 代码",
  "avatar": "core/workflow/template/codeRun",
  "flowNodeType": "code",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "system_addInputParam",
      "renderTypeList": ["addInputParam"],
      "valueType": "dynamic",
      "label": "",
      "required": false,
      "description": "接收前方节点输出作为代码参数",
      "customInputConfig": {
        "selectValueTypeList": ["string", "number", "boolean", "object", "arrayString", "arrayNumber", "arrayBoolean", "arrayObject", "arrayAny", "any", "chatHistory", "datasetQuote", "dynamic", "selectDataset"],
        "showDescription": false,
        "showDefaultValue": true
      }
    },
    {
      "key": "text",
      "renderTypeList": ["reference"],
      "valueType": "string",
      "canEdit": true,
      "label": "text",
      "required": true,
      "value": ["node_start", "userChatInput"]
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
      "value": "function main(params) {\n  const text = String(params.text || '').trim();\n  if (!text) {\n    return { is_valid: 'no', cleaned_text: '', reason: 'empty' };\n  }\n  return { is_valid: 'yes', cleaned_text: text, reason: 'valid' };\n}"
    }
  ],
  "outputs": [
    {
      "id": "system_addOutputParam",
      "key": "system_addOutputParam",
      "type": "dynamic",
      "valueType": "dynamic",
      "label": ""
    },
    {
      "id": "system_rawResponse",
      "key": "system_rawResponse",
      "label": "完整响应数据",
      "valueType": "object",
      "type": "static"
    },
    {
      "id": "is_valid",
      "type": "dynamic",
      "key": "is_valid",
      "valueType": "string",
      "label": "is_valid"
    },
    {
      "id": "cleaned_text",
      "type": "dynamic",
      "key": "cleaned_text",
      "valueType": "string",
      "label": "cleaned_text"
    },
    {
      "id": "reason",
      "type": "dynamic",
      "key": "reason",
      "valueType": "string",
      "label": "reason"
    },
    {
      "id": "error",
      "key": "error",
      "label": "错误信息",
      "valueType": "string",
      "type": "error"
    }
  ]
}
```

关键规则：

```text
代码 return 什么字段，outputs 里就必须声明什么字段。
例如 return { is_valid, cleaned_text }，
outputs 里就必须有 is_valid 和 cleaned_text。
```

---

## 8.8 文档解析节点 readFiles

用途：把上传文件解析成文本。

母版：

```json
{
  "nodeId": "node_read_files",
  "name": "文档解析",
  "intro": "读取并解析用户上传文件",
  "avatar": "core/workflow/template/readFiles",
  "flowNodeType": "readFiles",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "fileUrlList",
      "renderTypeList": ["reference"],
      "valueType": "arrayString",
      "label": "文件链接",
      "required": true,
      "value": [["node_start", "userFiles"]]
    }
  ],
  "outputs": [
    {
      "id": "system_text",
      "key": "system_text",
      "label": "文档解析结果",
      "description": "文档解析出的文本内容",
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "system_rawResponse",
      "key": "system_rawResponse",
      "label": "原始响应",
      "description": "文档解析原始响应",
      "valueType": "arrayObject",
      "type": "static"
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "type": "error",
      "valueType": "string",
      "label": "错误信息"
    }
  ]
}
```

关键规则：

```text
文档解析结果引用必须用：
["node_read_files", "system_text"]

不要写：
["node_read_files", "text"]
```

---

## 8.9 知识库搜索节点 datasetSearchNode

用途：从知识库检索内容。

母版：

```json
{
  "nodeId": "node_dataset_search",
  "name": "知识库搜索",
  "intro": "从知识库中搜索相关内容",
  "avatar": "core/workflow/template/datasetSearch",
  "flowNodeType": "datasetSearchNode",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "datasets",
      "renderTypeList": ["selectDataset", "reference"],
      "label": "选择知识库",
      "value": [],
      "valueType": "selectDataset",
      "required": true
    },
    {
      "key": "similarity",
      "renderTypeList": ["selectDatasetParamsModal"],
      "label": "",
      "value": 0.4,
      "valueType": "number"
    },
    {
      "key": "limit",
      "renderTypeList": ["hidden"],
      "label": "",
      "value": 5000,
      "valueType": "number"
    },
    {
      "key": "searchMode",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string",
      "value": "embedding"
    },
    {
      "key": "embeddingWeight",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "number",
      "value": 0.5
    },
    {
      "key": "usingReRank",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "boolean",
      "value": false
    },
    {
      "key": "rerankModel",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string"
    },
    {
      "key": "rerankWeight",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "number",
      "value": 0.5
    },
    {
      "key": "datasetSearchUsingExtensionQuery",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "boolean",
      "value": true
    },
    {
      "key": "datasetSearchExtensionModel",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string"
    },
    {
      "key": "datasetSearchExtensionBg",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "string",
      "value": ""
    },
    {
      "key": "authTmbId",
      "renderTypeList": ["hidden"],
      "label": "",
      "valueType": "boolean",
      "value": false
    },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "搜索内容",
      "required": true,
      "value": ["node_start", "userChatInput"],
      "selectedTypeIndex": 0
    },
    {
      "key": "collectionFilterMatch",
      "renderTypeList": ["textarea", "reference"],
      "label": "集合元数据过滤",
      "valueType": "string"
    }
  ],
  "outputs": [
    {
      "id": "quoteQA",
      "key": "quoteQA",
      "label": "知识库引用",
      "type": "static",
      "valueType": "datasetQuote"
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "type": "error",
      "valueType": "string",
      "label": "错误信息"
    }
  ]
}
```

必须提醒：

```text
导入后需要手动绑定知识库。
禁止编造 datasetId。
```

AI 节点使用知识库结果时：

```json
{
  "key": "quoteQA",
  "renderTypeList": ["settingDatasetQuotePrompt"],
  "valueType": "datasetQuote",
  "value": ["node_dataset_search", "quoteQA"]
}
```

---

## 8.10 问题分类节点 classifyQuestion

用途：用 AI 判断用户问题属于哪个分类，然后分支执行。

母版：

```json
{
  "nodeId": "node_classify",
  "name": "问题分类",
  "intro": "根据用户输入进行问题分类",
  "avatar": "core/workflow/template/questionClassify",
  "flowNodeType": "classifyQuestion",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["selectLLMModel", "reference"],
      "label": "AI 模型",
      "required": true,
      "valueType": "string"
    },
    {
      "key": "systemPrompt",
      "renderTypeList": ["textarea", "reference"],
      "maxLength": 100000,
      "isRichText": true,
      "valueType": "string",
      "label": "分类背景",
      "value": "请根据用户输入判断问题类型。"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "聊天记录",
      "required": true,
      "min": 0,
      "max": 50,
      "value": 6
    },
    {
      "key": "userChatInput",
      "renderTypeList": ["reference", "textarea"],
      "valueType": "string",
      "label": "用户问题",
      "required": true,
      "value": ["node_start", "userChatInput"],
      "selectedTypeIndex": 0
    },
    {
      "key": "agents",
      "renderTypeList": ["custom"],
      "valueType": "any",
      "label": "",
      "value": [
        {
          "value": "翻译类问题",
          "key": "translate"
        },
        {
          "value": "总结类问题",
          "key": "summary"
        },
        {
          "value": "其他问题",
          "key": "other"
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
      "type": "static"
    }
  ]
}
```

分支规则：

```text
分类节点输出给下游分支时，sourceHandle 使用 agents.key：

node_classify-source-translate
node_classify-source-summary
node_classify-source-other
```

必须提醒：

```text
模型需要手动选择。
分类 key 不能重复。
分支 handle 必须用 key，不是 value。
```

---

## 8.11 文本内容提取节点 contentExtract

用途：从文本里提取结构化字段。

母版：

```json
{
  "nodeId": "node_extract",
  "name": "文本内容提取",
  "intro": "从文本中提取结构化字段",
  "avatar": "core/workflow/template/extractJson",
  "flowNodeType": "contentExtract",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "model",
      "renderTypeList": ["selectLLMModel", "reference"],
      "label": "AI 模型",
      "required": true,
      "valueType": "string"
    },
    {
      "key": "description",
      "renderTypeList": ["textarea", "reference"],
      "valueType": "string",
      "label": "提取要求描述",
      "value": "请根据字段配置，从文本中提取结构化信息。"
    },
    {
      "key": "history",
      "renderTypeList": ["numberInput", "reference"],
      "valueType": "chatHistory",
      "label": "聊天记录",
      "required": true,
      "min": 0,
      "max": 50,
      "value": 6
    },
    {
      "key": "content",
      "renderTypeList": ["reference", "textarea"],
      "label": "待提取文本",
      "required": true,
      "valueType": "string",
      "value": ["node_start", "userChatInput"],
      "selectedTypeIndex": 0
    },
    {
      "key": "extractKeys",
      "renderTypeList": ["custom"],
      "label": "",
      "valueType": "any",
      "description": "目标字段配置",
      "value": []
    }
  ],
  "outputs": [
    {
      "id": "success",
      "key": "success",
      "label": "是否完整提取",
      "required": true,
      "valueType": "boolean",
      "type": "static"
    },
    {
      "id": "fields",
      "key": "fields",
      "label": "完整提取结果",
      "required": true,
      "valueType": "string",
      "type": "static"
    },
    {
      "id": "system_error_text",
      "key": "system_error_text",
      "type": "error",
      "valueType": "string",
      "label": "错误信息"
    }
  ]
}
```

`extractKeys` 示例：

```json
[
  {
    "key": "name",
    "desc": "姓名",
    "valueType": "string",
    "required": true,
    "enum": []
  },
  {
    "key": "amount",
    "desc": "金额",
    "valueType": "number",
    "required": false,
    "enum": []
  }
]
```

必须提醒：

```text
如果用户没有说明要提取哪些字段，extractKeys 不能乱编。
需要用户手动补充字段，或者让 AI 先询问字段。
```

---

## 8.12 HTTP 请求节点 httpRequest468

用途：调用外部接口。

母版：

```json
{
  "nodeId": "node_http",
  "name": "HTTP 请求",
  "intro": "可以发出 HTTP 请求，实现联网搜索、数据库查询等操作",
  "avatar": "core/workflow/template/httpRequest",
  "flowNodeType": "httpRequest468",
  "showStatus": true,
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "system_addInputParam",
      "renderTypeList": ["addInputParam"],
      "valueType": "dynamic",
      "label": "",
      "required": false,
      "description": "HTTP 动态输入"
    },
    {
      "key": "system_httpMethod",
      "renderTypeList": ["custom"],
      "valueType": "string",
      "label": "",
      "value": "POST",
      "required": true
    },
    {
      "key": "system_httpTimeout",
      "renderTypeList": ["custom"],
      "valueType": "number",
      "label": "",
      "value": 30,
      "min": 5,
      "max": 600,
      "required": true
    },
    {
      "key": "system_httpReqUrl",
      "renderTypeList": ["hidden"],
      "valueType": "string",
      "label": "",
      "description": "HTTP 请求地址",
      "placeholder": "https://api.example.com/endpoint",
      "required": false,
      "value": ""
    },
    {
      "key": "system_header_secret",
      "renderTypeList": ["hidden"],
      "valueType": "object",
      "label": "",
      "required": false
    },
    {
      "key": "system_httpHeader",
      "renderTypeList": ["custom"],
      "valueType": "any",
      "value": [],
      "label": "",
      "description": "请求头",
      "required": false
    },
    {
      "key": "system_httpParams",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "value": [],
      "label": "",
      "required": false
    },
    {
      "key": "system_httpJsonBody",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "value": "",
      "label": "",
      "required": false
    },
    {
      "key": "system_httpFormBody",
      "renderTypeList": ["hidden"],
      "valueType": "any",
      "value": [],
      "label": "",
      "required": false
    },
    {
      "key": "system_httpContentType",
      "renderTypeList": ["hidden"],
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
      "label": "输出字段提取"
    },
    {
      "id": "httpRawResponse",
      "key": "httpRawResponse",
      "required": true,
      "label": "原始响应",
      "description": "HTTP 请求原始响应",
      "valueType": "any",
      "type": "static"
    },
    {
      "id": "error",
      "key": "error",
      "label": "请求错误",
      "valueType": "string",
      "type": "error"
    }
  ]
}
```

必须提醒：

```text
接口 URL 需要手动填写。
API Key / Authorization 需要手动填写。
请求参数需要手动填写。
输出字段提取需要手动配置。
禁止编造真实 token。
```

---

## 8.13 文本拼接节点 textEditor

用途：拼接文本、整理提示词、组合多个变量。

母版：

```json
{
  "nodeId": "node_text_editor",
  "name": "文本拼接",
  "intro": "拼接文本和变量",
  "avatar": "core/workflow/template/textConcat",
  "flowNodeType": "textEditor",
  "position": {
    "x": 500,
    "y": 0
  },
  "version": "481",
  "inputs": [
    {
      "key": "system_textareaInput",
      "renderTypeList": ["textarea"],
      "valueType": "string",
      "required": true,
      "label": "拼接文本",
      "value": "用户输入：{{$node_start.userChatInput$}}"
    }
  ],
  "outputs": [
    {
      "id": "system_text",
      "key": "system_text",
      "label": "拼接结果",
      "type": "static",
      "valueType": "string"
    }
  ]
}
```

注意：

```text
文本拼接节点适合使用 {{$nodeId.outputId$}} 这种插值格式。
输出引用用 ["node_text_editor", "system_text"]。
```

---

# 9. chatConfig 配置规则

## 9.1 普通文本应用

```json
"chatConfig": {}
```

或者：

```json
"chatConfig": {
  "welcomeText": "",
  "variables": [],
  "questionGuide": {
    "open": false
  }
}
```

---

## 9.2 文件上传应用

如果工作流要使用上传文件，必须设置：

```json
"chatConfig": {
  "fileSelectConfig": {
    "canSelectFile": true,
    "canSelectImg": true,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 10
  }
}
```

如果只允许文档：

```json
"chatConfig": {
  "fileSelectConfig": {
    "canSelectFile": true,
    "canSelectImg": false,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 10
  }
}
```

如果只允许图片：

```json
"chatConfig": {
  "fileSelectConfig": {
    "canSelectFile": false,
    "canSelectImg": true,
    "canSelectVideo": false,
    "canSelectAudio": false,
    "maxFiles": 10
  }
}
```

---

# 10. 节点拼装流程

AI 根据一句话生成工作流时，按下面步骤：

```text
1. 理解用户需求
2. 判断工作流类型
3. 选择需要的单节点母版
4. 给每个节点分配唯一 nodeId
5. 设置节点 position
6. 修改节点提示词、代码、条件
7. 设置变量引用
8. 生成 edges
9. 生成 chatConfig
10. 列出需要手动配置项
11. 自检
```

---

# 11. 简单工作流拼装示例

## 11.1 翻译助手

用户一句话：

```text
做一个翻译助手
```

推荐节点：

```text
userGuide
node_start workflowStart
node_check code
node_if ifElseNode
node_ai chatNode
node_answer answerNode
node_invalid_answer answerNode
```

连接：

```text
node_start -> node_check
node_check -> node_if
node_if IF -> node_ai
node_ai -> node_answer
node_if ELSE -> node_invalid_answer
```

关键配置：

```text
node_check:
检查输入是否为空、纯数字、纯符号、单个无意义字符。
返回 is_valid / cleaned_text / reason。

node_if:
判断 ["node_check","is_valid"] equalTo "yes"

node_ai:
systemPrompt = 自动判断中英方向，只输出译文，不输出解释。
userChatInput = ["node_check","cleaned_text"]

node_answer:
text = ["node_ai","answerText"]

node_invalid_answer:
text = "请输入需要翻译的文本，例如：I want to learn data analysis。"
```

需要手动配置：

```text
AI 模型需要导入后手动选择。
```

---

## 11.2 文本总结助手

用户一句话：

```text
做一个文本总结助手
```

推荐节点：

```text
userGuide
node_start workflowStart
node_ai chatNode
node_answer answerNode
```

连接：

```text
node_start -> node_ai
node_ai -> node_answer
```

关键配置：

```text
node_ai.systemPrompt:
你是文本总结助手。请提炼用户输入内容的核心观点、关键细节和结论。输出结构清晰的 Markdown。
```

需要手动配置：

```text
AI 模型需要导入后手动选择。
```

---

## 11.3 文本润色助手

推荐节点：

```text
workflowStart -> chatNode -> answerNode
```

提示词：

```text
你是中文写作润色助手。请在不改变原意的基础上，让表达更自然、清晰、正式。只输出润色后的文本。
```

---

## 11.4 简单会议纪要助手

推荐节点：

```text
workflowStart -> code输入校验 -> ifElseNode -> chatNode -> answerNode
                                      ELSE -> invalid answerNode
```

AI 提示词：

```text
你是会议纪要整理助手。
请从用户输入的会议记录中整理：
1. 会议类型
2. 会议摘要
3. 关键决策
4. 行动项表格：任务、负责人、截止时间、备注
5. 风险或待确认事项

如果原文不是会议记录，请说明无法整理。
```

需要手动配置：

```text
AI 模型需要导入后手动选择。
如果老师要求固定格式，需要手动修改提示词。
```

---

# 12. 中等工作流拼装示例

## 12.1 文件总结助手

用户一句话：

```text
做一个上传文件总结助手
```

推荐节点：

```text
userGuide
node_start workflowStart 文件版
node_read_files readFiles
node_ai chatNode
node_answer answerNode
```

连接：

```text
node_start -> node_read_files
node_read_files -> node_ai
node_ai -> node_answer
```

关键引用：

```text
node_read_files.fileUrlList = [["node_start", "userFiles"]]
node_ai.userChatInput = ["node_read_files", "system_text"]
node_answer.text = ["node_ai", "answerText"]
```

需要手动配置：

```text
1. chatConfig.fileSelectConfig 需要开启文件上传。
2. AI 模型需要手动选择。
3. 如果只允许 PDF/DOCX/CSV，需要检查平台文件上传限制。
```

---

## 12.2 知识库问答助手

用户一句话：

```text
做一个知识库问答助手
```

推荐节点：

```text
workflowStart
datasetSearchNode
chatNode
answerNode
```

连接：

```text
node_start -> node_dataset_search
node_dataset_search -> node_ai
node_ai -> node_answer
```

关键引用：

```text
node_dataset_search.userChatInput = ["node_start", "userChatInput"]
node_ai.quoteQA = ["node_dataset_search", "quoteQA"]
node_ai.userChatInput = ["node_start", "userChatInput"]
```

AI 提示词：

```text
你是知识库问答助手。
请优先根据知识库引用内容回答。
如果知识库中没有相关信息，请明确说明“知识库中未找到相关内容”，不要编造。
```

需要手动配置：

```text
1. 知识库搜索节点需要手动绑定知识库。
2. AI 模型需要手动选择。
3. 相似度、召回数量、重排模型可根据效果手动调整。
禁止编造 datasetId。
```

---

## 12.3 文本字段提取助手

用户一句话：

```text
做一个从文本里提取姓名、电话、金额的助手
```

推荐节点：

```text
workflowStart
contentExtract
answerNode
```

连接：

```text
node_start -> node_extract
node_extract -> node_answer
```

关键配置：

```json
"extractKeys": [
  {
    "key": "name",
    "desc": "姓名",
    "valueType": "string",
    "required": false,
    "enum": []
  },
  {
    "key": "phone",
    "desc": "手机号",
    "valueType": "string",
    "required": false,
    "enum": []
  },
  {
    "key": "amount",
    "desc": "金额",
    "valueType": "number",
    "required": false,
    "enum": []
  }
]
```

需要手动配置：

```text
AI 模型需要手动选择。
如果用户没有说明字段，必须提醒手动填写 extractKeys。
```

---

## 12.4 HTTP 接口助手

用户一句话：

```text
做一个调用接口查询天气的助手
```

推荐节点：

```text
workflowStart
httpRequest468
answerNode 或 chatNode -> answerNode
```

连接：

```text
node_start -> node_http
node_http -> node_answer
```

需要手动配置：

```text
1. HTTP 请求地址需要手动填写。
2. API Key / Authorization 需要手动填写。
3. 请求参数需要手动配置。
4. 输出字段提取需要手动配置。
5. 禁止 AI 编造真实接口密钥。
```

---

# 13. 需要手动配置的内容清单

只要涉及以下内容，AI 必须提醒：

```text
1. AI 模型
   - 导入后手动选择。
   - 不要编造私有模型名。

2. 知识库
   - datasetSearchNode 需要手动绑定知识库。
   - 禁止编造 datasetId。

3. HTTP/API
   - URL、Header、API Key、Body 需要手动填写。
   - 禁止编造 token。

4. 数据库
   - 数据库连接、账号密码、表名、存储过程需要手动填写。
   - 禁止生成真实连接信息。

5. 工具/插件
   - toolId、pluginId、appId 需要用户提供或手动选择。
   - 禁止编造。

6. 文件上传
   - 需要设置 chatConfig.fileSelectConfig。
   - fileUrlList 必须用二维数组引用。

7. 文本提取字段
   - extractKeys 需要根据业务手动配置。
   - 用户没说字段时不能乱编。

8. 复杂业务规则
   - 用户没说明规则时，只能给默认模板和提醒。
```

---

# 14. 自检清单

AI 输出 JSON 前必须检查：

```text
1. nodes 是否存在。
2. edges 是否存在。
3. chatConfig 是否存在。
4. 每个 nodeId 是否唯一。
5. 每条 edge 的 source 是否存在。
6. 每条 edge 的 target 是否存在。
7. 普通 edge handle 是否符合：
   sourceNodeId-source-right
   targetNodeId-target-left

8. ifElseNode 分支 handle 是否符合：
   nodeId-source-IF
   nodeId-source-ELSE
   nodeId-source-ELSE IF 1

9. classifyQuestion 分支 handle 是否使用 agents.key。

10. 所有 input.value 引用的 nodeId 是否存在。
11. 所有 input.value 引用的 outputId 是否存在。
12. 文件引用是否使用二维数组：
    [["node_start", "userFiles"]]

13. readFiles 输出是否引用 system_text。
14. answerNode 引用上游变量时 selectedTypeIndex 是否正确。
15. 代码节点 return 字段是否都在 outputs 中声明。
16. 知识库、API、数据库、模型是否有手动配置提醒。
17. 是否编造了 datasetId、toolId、API Key、数据库连接。
```

---

# 15. 常见错误与修复

## 错误 1：文档解析输出写成 text

错误：

```json
["node_read_files", "text"]
```

正确：

```json
["node_read_files", "system_text"]
```

---

## 错误 2：文件上传引用写成一维数组

错误：

```json
["node_start", "userFiles"]
```

正确：

```json
[["node_start", "userFiles"]]
```

---

## 错误 3：判断器分支写成 true/false

错误：

```text
node_if-source-true
node_if-source-false
```

正确：

```text
node_if-source-IF
node_if-source-ELSE
```

---

## 错误 4：分类节点分支使用分类名称

错误：

```text
node_classify-source-翻译类问题
```

正确：

```text
node_classify-source-translate
```

其中 `translate` 是 `agents.key`。

---

## 错误 5：AI 节点模型乱写

错误：

```json
"value": "qwen-plus-private-xxx"
```

正确：

```text
模型字段可以留空，导入后手动选择。
或者使用用户明确提供的平台可用模型名。
```

---

## 错误 6：知识库节点编造 datasetId

错误：

```json
"value": [{"datasetId": "fake_dataset_id"}]
```

正确：

```json
"value": []
```

并提醒：

```text
导入后请在知识库搜索节点中手动选择知识库。
```

---

## 错误 7：代码节点输出没声明

代码：

```js
return {
  cleaned_text: text,
  is_valid: 'yes'
}
```

outputs 必须有：

```json
[
  {
    "id": "cleaned_text",
    "key": "cleaned_text",
    "type": "dynamic",
    "valueType": "string",
    "label": "cleaned_text"
  },
  {
    "id": "is_valid",
    "key": "is_valid",
    "type": "dynamic",
    "valueType": "string",
    "label": "is_valid"
  }
]
```

---

# 16. AI 生成工作流时的标准回复格式

AI 最终回复建议固定为：

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

如果用户要求“直接给 JSON 文件”，则不要把解释混在 JSON 里。  
如果用户要求“复制 JSON”，只输出纯 JSON，不要 Markdown 包裹。  
如果用户要求“文档说明”，可以输出 Markdown 文档。

---

# 17. 最终结论

要实现“一句话生成 FastGPT 工作流”，最稳方式不是让 AI 自由写完整 JSON，而是：

```text
一句话需求
↓
AI 判断工作流类型
↓
选择单节点母版
↓
替换 nodeId、position、提示词、输入引用
↓
按规则生成 edges
↓
生成 chatConfig
↓
列出需要手动配置项
↓
自检
↓
输出 JSON 或工作流模板
```

核心思想：

```text
节点母版必须准。
连接规则必须准。
不能确定的配置必须提醒手动填写。
AI 不允许编造平台私有配置。
```
