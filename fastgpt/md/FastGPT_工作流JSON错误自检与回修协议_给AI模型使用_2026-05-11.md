# FastGPT 工作流 JSON 错误自检与回修机制设计文档

版本：2026-05-11  
用途：给其他 AI 模型使用。  
目标：当 AI 生成 FastGPT 工作流 JSON 后，如果出现导入失败、运行失败、节点异常、变量引用失败、文件解析失败等问题，AI 能根据错误异常进行自检、定位、局部修复、再次自检，并返回修复后的 JSON 或修复建议。

---

## 0. 本文档要解决的问题

你现在已有的几个文件，已经能解决“AI 如何按节点母版生成 FastGPT 工作流 JSON”的问题。

但还缺一层：

> 如果其他 AI 模型生成出来的工作流 JSON 出错了，应该如何让它根据错误信息自己判断哪里错、怎么改、哪些能自动修、哪些必须手动配置。

本文档就是补这一层。

核心目标不是让 AI 重新乱生成一个工作流，而是让 AI 做下面这个闭环：

```text
生成 JSON
↓
静态自检
↓
发现错误
↓
错误分类
↓
定位 nodeId / input / output / edge / chatConfig
↓
判断能否自动修复
↓
局部修复
↓
再次自检
↓
返回修复后的 JSON 或手动配置清单
```

---

## 1. 关键结论

### 1.1 只靠“请你自检一下”不够

如果只在提示词里写：

```text
请你生成完 JSON 后自检。
```

效果不会稳定。

原因是：

1. AI 可能不知道具体检查什么；
2. AI 可能检查了语法，却没检查变量引用；
3. AI 可能发现错误后重新生成整个 JSON，反而改坏原来正确的部分；
4. AI 可能把平台环境错误误判成 JSON 错误；
5. AI 可能为了修复而编造 datasetId、模型名、API Key、数据库连接。

因此必须给 AI 一套固定协议：

```text
错误分类表
+
检查顺序
+
可自动修复规则
+
不可自动修复规则
+
局部修复原则
+
二次自检清单
```

---

### 1.2 最稳方案是“三层机制”

推荐结构：

```text
第一层：静态自检器
第二层：错误分类器
第三层：AI 回修器
```

三层职责不同。

#### 第一层：静态自检器

不运行 FastGPT，只检查 JSON 本身：

```text
JSON 是否能解析
nodes / edges / chatConfig 是否存在
nodeId 是否唯一
flowNodeType 是否真实
edge.source / edge.target 是否存在
变量引用是否存在
fileUrlList 是否二维数组
answerNode 引用上游时 selectedTypeIndex 是否为 1
代码 return 字段是否在 outputs 声明
是否编造 datasetId / API Key / 数据库连接
```

#### 第二层：错误分类器

根据用户提供的报错、截图、日志、运行结果，把错误归类：

```text
JSON 语法错误
顶层结构错误
节点类型错误
input/output 错误
edge 连线错误
handle 分支错误
变量引用错误
文件上传配置错误
AI 模型配置错误
知识库配置错误
HTTP/API 配置错误
数据库配置错误
FastGPT 平台环境错误
```

#### 第三层：AI 回修器

根据错误类别进行局部修复。

原则：

```text
能自动修复的，局部修复；
不能自动确定的，放入【需要手动配置】；
不允许编造平台私有配置；
不允许无意义重写整个工作流。
```

---

## 2. 依据来源与设计依据

### 2.1 来自已上传规则文件的依据

现有规则文件已经明确：

1. FastGPT 工作流 JSON 核心结构是：

```json
{
  "nodes": [],
  "edges": [],
  "chatConfig": {}
}
```

2. AI 不能编造不存在的 `flowNodeType`。
3. AI 不能编造 `datasetId`、`toolId`、`pluginId`、API Key、数据库连接、账号密码、私有模型名。
4. 普通变量引用格式是：

```json
["nodeId", "outputId"]
```

5. 文件上传引用格式必须是二维数组：

```json
[["node_start", "userFiles"]]
```

6. 文本插值格式是：

```text
{{$nodeId.outputId$}}
```

7. 判断器分支不能写 `true/false`，应该写：

```text
node_if-source-IF
node_if-source-ELSE
node_if-source-ELSE IF 1
```

8. 问题分类节点分支必须用 `agents.key`，不能用中文分类名。
9. 代码节点 `return` 了什么字段，`outputs` 里就必须声明什么字段。
10. `readFiles` 的解析结果输出是 `system_text`，不是 `text`。
11. `answerNode` 引用上游变量时，`selectedTypeIndex` 必须为 1。
12. `maxFiles` 必须和实际代码/提示词逻辑一致，不能上传 5 个文件但代码只处理 `files[0]`。

这些内容说明：你的旧文件已经有“生成规则”和“基础自检”，但还需要补充“错误异常回修协议”。

---

### 2.2 来自 FastGPT 官方文档和源码的依据

FastGPT 官方工作流说明里，节点由三部分组成：

```text
inputs
outputs
triggers
```

节点通过连接线顺序执行。上游节点输出可以作为下游节点输入。工作流从 Workflow Start 节点开始，连接线状态会影响后续节点是否执行。

这说明：

```text
错误定位必须围绕 inputs / outputs / edges / triggers / chatConfig。
```

FastGPT 源码中存在真实的 `FlowNodeTypeEnum`，包含：

```text
workflowStart
chatNode
datasetSearchNode
answerNode
classifyQuestion
contentExtract
httpRequest468
ifElseNode
variableUpdate
code
textEditor
readFiles
userSelect
formInput
loop
parallelRun
tool
toolSet
runApp
```

这说明：

```text
flowNodeType 必须来自真实枚举；
AI 不允许凭空写 receiptExtractNode、summaryNode、fileJudgeNode、databaseNode 等不存在节点。
```

FastGPT 源码中还存在真实的 `NodeInputKeyEnum` 与 `NodeOutputKeyEnum`，例如：

```text
NodeInputKeyEnum:
userChatInput
model
systemPrompt
quoteQA
fileUrlList
ifElseList
code
codeType
datasets
system_httpReqUrl
system_httpHeader
system_httpJsonBody

NodeOutputKeyEnum:
userChatInput
userFiles
answerText
reasoningText
system_text
system_rawResponse
system_error_text
quoteQA
cqResult
fields
ifElseResult
httpRawResponse
```

这说明：

```text
input.key 和 output.id/key 不能凭空写；
变量引用必须引用真实存在的 output.id。
```

FastGPT 对话接口支持 `detail=true`，可以返回 `responseData` 等中间运行信息。  
这意味着如果工作流已经导入并运行，可以通过运行详情进一步定位哪个节点报错。

---

## 3. 总体实现目标

最终要实现的不是“生成一个文档”，而是一套能给其他 AI 使用的工作流回修协议。

输入：

```text
1. 用户原始需求
2. 当前工作流 JSON
3. 错误信息 / 报错截图文字 / 控制台日志 / FastGPT 运行详情
4. FastGPT 版本或云版/私有版信息
5. 用户要求：只分析 / 修复 JSON / 输出文件
```

输出：

```text
【错误类型】
【错误等级】
【错误位置】
【错误原因】
【是否能自动修复】
【修复动作】
【仍需手动配置】
【修复后自检结果】
【修复后的 JSON】
```

---

## 4. 错误严重等级

建议把错误分成 4 级。

### S1：致命结构错误

这类错误通常会导致 JSON 无法导入或节点无法识别。

包括：

```text
JSON 语法错误
顶层缺 nodes / edges / chatConfig
nodes 不是数组
edges 不是数组
nodeId 重复
flowNodeType 不存在
edge.source 指向不存在节点
edge.target 指向不存在节点
```

处理策略：

```text
AI 必须自动修复。
如果无法确定正确节点，只能删除错误引用或放入待手动配置，不能编造。
```

---

### S2：运行链路错误

这类错误可能导入成功，但运行失败或节点不执行。

包括：

```text
变量引用不存在
outputId 不存在
代码 return 字段未声明 outputs
判断器分支 handle 错
分类节点分支 handle 错
fileUrlList 一维数组
readFiles 输出引用错误
answerNode selectedTypeIndex 错
```

处理策略：

```text
AI 必须优先自动修复。
只修相关字段，不重写整个工作流。
```

---

### S3：平台配置错误

这类错误不是 JSON 结构错，而是平台资源没配置。

包括：

```text
AI 模型未选择或不可用
视觉模型不支持图片
知识库未绑定
API URL 未填写
Header / Token 未配置
数据库连接未配置
私有工具 toolId 不存在
```

处理策略：

```text
AI 不能编造配置。
必须列入【需要手动配置】。
```

---

### S4：逻辑风险错误

这类错误不一定马上报错，但会导致结果不符合预期。

包括：

```text
maxFiles > 1 但代码只处理 files[0]
提示词说支持批量，但输出不是数组
中间 AI 节点 isResponseAnswerText = true
最终没有 answerNode
提示词要求 JSON 但没有禁止 Markdown
业务字段过多导致提取不稳定
```

处理策略：

```text
AI 应提醒并建议修复。
若修复不会改变用户需求，可以自动修。
若涉及业务选择，需要列入待确认。
```

---

## 5. 错误回修总流程

当用户提供错误信息时，AI 必须按以下流程执行。

```text
步骤 1：读取错误信息
步骤 2：提取关键词
步骤 3：匹配错误类型
步骤 4：定位相关 nodeId / input.key / output.id / edge / chatConfig
步骤 5：判断是否能自动修复
步骤 6：局部修复
步骤 7：再次执行完整自检
步骤 8：输出修复说明和修复后的 JSON
```

禁止行为：

```text
1. 不允许一看到报错就重新生成整个工作流。
2. 不允许把用户已经确认可用的节点大幅改写。
3. 不允许为了修复而编造 datasetId、API Key、数据库连接、私有模型名。
4. 不允许把 JSON 和解释文字混在同一个 .json 文件中。
5. 不允许只说“已修复”但不说明修复点。
```

---

## 6. 生成后静态自检清单

AI 在输出最终 JSON 前必须逐项检查。

### 6.1 JSON 结构检查

```text
1. JSON 是否能被解析。
2. 是否包含 nodes。
3. 是否包含 edges。
4. 是否包含 chatConfig。
5. nodes 是否为数组。
6. edges 是否为数组。
7. chatConfig 是否为对象。
8. 是否混入 Markdown 代码块。
9. 是否混入注释。
10. 是否混入说明文字。
```

修复规则：

```text
如果 JSON 语法错误，先修语法。
如果混入说明文字，拆分为 JSON 文件和说明文档。
```

---

### 6.2 节点检查

```text
1. 每个 node 是否有 nodeId。
2. nodeId 是否唯一。
3. 每个 node 是否有 name。
4. 每个 node 是否有 flowNodeType。
5. flowNodeType 是否属于已知真实节点类型。
6. 每个 node 是否有 position。
7. 每个 node 是否有 inputs。
8. 每个 node 是否有 outputs。
9. inputs 是否为数组。
10. outputs 是否为数组。
```

推荐允许的基础节点类型：

```text
userGuide
workflowStart
chatNode
answerNode
code
ifElseNode
classifyQuestion
readFiles
datasetSearchNode
contentExtract
httpRequest468
textEditor
```

复杂节点如：

```text
variableUpdate
userSelect
formInput
loop
parallelRun
tool
toolSet
runApp
```

只有在有可靠母版或用户明确要求时再生成。否则只写设计方案，不硬造完整 JSON。

---

### 6.3 连线检查

```text
1. 每条 edge.source 是否存在于 nodes。
2. 每条 edge.target 是否存在于 nodes。
3. 每条 edge 是否有 sourceHandle。
4. 每条 edge 是否有 targetHandle。
5. 普通连接 sourceHandle 是否为 nodeId-source-right。
6. 普通连接 targetHandle 是否为 nodeId-target-left。
7. 判断器分支是否使用 nodeId-source-IF / nodeId-source-ELSE。
8. 分类节点分支是否使用 nodeId-source-${agents.key}。
9. 是否存在孤立业务节点。
10. workflowStart 是否能连到主要业务节点。
```

修复规则：

```text
source/target 不存在：修正为真实 nodeId。
普通节点 handle 错：改为 nodeId-source-right / nodeId-target-left。
ifElseNode true/false：改为 IF / ELSE。
classifyQuestion 中文分类名：改为 agents.key。
```

---

### 6.4 变量引用检查

检查所有输入中的引用格式：

```json
["nodeId", "outputId"]
```

必须确认：

```text
1. nodeId 存在。
2. outputId 存在于该节点 outputs 的 id 字段。
3. input.renderTypeList 中包含 reference。
4. selectedTypeIndex 指向 reference 所在的位置。
```

特别规则：

```text
如果 renderTypeList = ["reference", "textarea"]，引用时 selectedTypeIndex 应为 0。
如果 renderTypeList = ["textarea", "reference"]，引用时 selectedTypeIndex 应为 1。
```

注意：

```text
不能机械固定 selectedTypeIndex = 1。
必须看 reference 在 renderTypeList 中的位置。
```

常见情况：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "value": ["ai", "answerText"],
  "selectedTypeIndex": 1
}
```

如果没有 `selectedTypeIndex`，但 value 是数组引用，应自动补上正确索引。

---

### 6.5 文件引用检查

文件上传不是普通单字段引用。

错误：

```json
["node_start", "userFiles"]
```

正确：

```json
[["node_start", "userFiles"]]
```

检查项：

```text
1. workflowStart 是否有 userFiles 输出。
2. chatConfig.fileSelectConfig 是否存在。
3. fileSelectConfig 是否允许对应文件类型。
4. readFiles.fileUrlList 是否是二维数组。
5. AI vision 节点 fileUrlList 是否引用 userFiles。
6. maxFiles 是否和业务逻辑一致。
```

单文件规则：

```text
如果代码或提示词只处理第一份文件，maxFiles 必须为 1。
```

多文件规则：

```text
如果 maxFiles > 1：
1. 代码必须遍历文件。
2. AI 输出应设计成数组。
3. 总结节点应按多文件汇总。
4. 开场白应说明支持多文件。
```

---

### 6.6 readFiles 检查

常见错误：

```json
["read_files", "text"]
```

正确：

```json
["read_files", "system_text"]
```

检查项：

```text
1. readFiles 输入 key 是否为 fileUrlList。
2. fileUrlList 是否二维引用。
3. readFiles outputs 是否包含 system_text。
4. 下游节点是否引用 system_text。
5. 是否错误引用 text。
```

修复规则：

```text
把 ["read_files", "text"] 改成 ["read_files", "system_text"]。
```

---

### 6.7 answerNode 检查

answerNode 是最终输出节点。

检查项：

```text
1. flowNodeType 是否为 answerNode。
2. inputs 中是否有 key = text。
3. 固定文本输出时 selectedTypeIndex 可为 0 或不写。
4. 引用上游输出时，selectedTypeIndex 必须指向 reference。
5. value 是否引用真实存在的 output。
```

错误示例：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "value": ["ai", "answerText"],
  "selectedTypeIndex": 0
}
```

正确示例：

```json
{
  "renderTypeList": ["textarea", "reference"],
  "value": ["ai", "answerText"],
  "selectedTypeIndex": 1
}
```

修复规则：

```text
如果 value 是 ["nodeId", "outputId"]，且 renderTypeList 包含 reference，则 selectedTypeIndex 必须改为 reference 的索引。
```

---

### 6.8 code 节点检查

检查项：

```text
1. inputs 中是否有 key = code。
2. codeType 是否为 js 或 py。
3. 代码中 params.xxx 是否在 inputs 中声明。
4. return 的字段是否都在 outputs 中声明。
5. outputs 的 id/key 是否和 return 字段一致。
6. 下游引用的字段是否真实存在。
```

错误示例：

```javascript
return {
  is_valid: "yes",
  cleaned_text: text
}
```

但 outputs 没有：

```text
is_valid
cleaned_text
```

修复规则：

```text
给 outputs 补充 dynamic output：
id = return 字段名
key = return 字段名
type = dynamic
valueType = 合理类型
label = 字段名
```

注意：

```text
不要随便改代码逻辑。
优先补 outputs。
只有代码明显引用未声明 params 时，才补 inputs 或修改 params 名称。
```

---

### 6.9 ifElseNode 检查

检查项：

```text
1. flowNodeType 是否为 ifElseNode。
2. inputs 中是否有 ifElseList。
3. ifElseList 是否非空。
4. condition 是否为 AND / OR。
5. variable 是否引用真实 output。
6. condition 是否是合法条件。
7. 分支 edge 是否使用 IF / ELSE / ELSE IF 1。
```

错误示例：

```text
node_if-source-true
node_if-source-false
```

正确：

```text
node_if-source-IF
node_if-source-ELSE
```

修复规则：

```text
true 改 IF
false 改 ELSE
elseif 改 ELSE IF 1 / ELSE IF 2
```

---

### 6.10 classifyQuestion 检查

检查项：

```text
1. flowNodeType 是否为 classifyQuestion。
2. inputs 中是否有 agents。
3. agents 是否为数组。
4. 每个 agent 是否有 key 和 value。
5. 分支 edge 是否使用 agents.key。
6. 不允许用 agents.value 作为 sourceHandle。
```

错误示例：

```text
classify-source-用户想翻译文本
```

正确：

```text
classify-source-translate
```

修复规则：

```text
读取 agents 数组。
把 sourceHandle 中的中文 value 映射为对应 key。
如果无法映射，要求用户手动确认分类 key。
```

---

### 6.11 AI 节点检查

检查项：

```text
1. flowNodeType 是否为 chatNode。
2. 是否有 model input。
3. 是否编造私有模型名。
4. 是否有 systemPrompt。
5. 是否有 userChatInput。
6. 中间 AI 节点 isResponseAnswerText 是否为 false。
7. 最终输出是否交给 answerNode。
8. 图片识别是否开启 aiChatVision。
9. JSON 输出是否写明只输出 JSON，禁止 Markdown。
```

修复规则：

```text
模型字段不确定时留空，不编造。
中间 AI 节点 isResponseAnswerText 改为 false。
最终结果通过 answerNode 输出。
图片识别节点提醒导入后选择支持视觉的模型。
```

---

### 6.12 datasetSearchNode 检查

检查项：

```text
1. flowNodeType 是否为 datasetSearchNode。
2. datasets 是否存在。
3. 是否编造 datasetId。
4. userChatInput 是否引用正确。
5. outputs 是否有 quoteQA。
6. 下游 AI 是否引用 quoteQA。
```

错误示例：

```json
"value": [{"datasetId": "fake_dataset_id"}]
```

正确：

```json
"value": []
```

并说明：

```text
导入后请手动绑定知识库。
```

修复规则：

```text
删除伪造 datasetId。
保留 datasets: []。
加入【需要手动配置：知识库】。
```

---

### 6.13 httpRequest468 检查

检查项：

```text
1. flowNodeType 是否为 httpRequest468。
2. system_httpReqUrl 是否为空或占位。
3. system_httpMethod 是否合理。
4. system_httpHeader 是否含敏感信息。
5. system_httpJsonBody / system_httpParams 是否符合用户提供内容。
6. 是否编造 API Key、Token、Cookie。
7. outputs 是否声明需要的字段。
```

修复规则：

```text
没有用户提供接口信息时，不编造。
只生成骨架。
把 URL、Header、Body、鉴权、响应字段提取列入【需要手动配置】。
```

---

### 6.14 数据库相关检查

FastGPT 工作流 JSON 中如果涉及数据库入库，必须谨慎。

禁止自动编造：

```text
数据库地址
数据库账号
数据库密码
表名
存储过程名
字段结构
连接字符串
```

除非用户已经明确提供。

处理策略：

```text
1. 可以生成前置整理 JSON 的节点。
2. 可以生成 SQL 字符串生成节点。
3. 不能生成真实数据库连接配置。
4. 不能编造 sp_save_receipt 这类存储过程，除非用户明确说已有。
5. 必须列入【需要手动配置：数据库连接/存储过程/接口】。
```

---

## 7. 错误异常定位表

下面是给 AI 用的“错误现象 → 优先检查位置 → 修复方式”。

---

### 7.1 导入提示 JSON 格式错误

优先检查：

```text
是否有 Markdown ```json 包裹
是否有说明文字混在 JSON 里
是否有注释
是否少逗号
是否少括号
是否字符串没闭合
是否出现不可见控制字符
```

修复方式：

```text
只保留纯 JSON。
修复语法。
重新解析一次。
```

---

### 7.2 导入后节点不显示

优先检查：

```text
nodes 是否存在
nodeId 是否重复
flowNodeType 是否真实
position 是否存在
inputs / outputs 是否是数组
```

修复方式：

```text
补齐基础字段。
重复 nodeId 改成唯一。
未知 flowNodeType 改成真实节点类型或改为设计方案。
```

---

### 7.3 连线丢失或流程断开

优先检查：

```text
edge.source 是否存在
edge.target 是否存在
sourceHandle 是否正确
targetHandle 是否正确
workflowStart 是否连接到主流程
```

修复方式：

```text
修正 source / target。
普通连线使用 nodeId-source-right / nodeId-target-left。
分支连线按节点类型修正。
```

---

### 7.4 判断器分支不执行

优先检查：

```text
ifElseList 条件是否正确
variable 是否引用真实输出
edge sourceHandle 是否写成 true/false
是否缺 ELSE 分支
```

修复方式：

```text
true → IF
false → ELSE
补充 ELSE 或错误回复节点
修正 variable 引用
```

---

### 7.5 分类节点分支不执行

优先检查：

```text
agents 是否有 key
edge sourceHandle 是否使用 agents.key
是否误用 agents.value 中文分类名
```

修复方式：

```text
根据 agents 映射 value → key。
如果映射失败，要求用户确认分类 key。
```

---

### 7.6 指定回复不显示 AI 结果

优先检查：

```text
answerNode.inputs[key=text]
value 是否为 ["ai_node", "answerText"]
selectedTypeIndex 是否指向 reference
上游 AI outputs 是否有 answerText
```

修复方式：

```text
selectedTypeIndex 改为 reference 索引。
value 改为真实 AI 节点的 answerText。
确保 AI 节点 outputs 有 answerText。
```

---

### 7.7 代码节点结果无法被后续引用

优先检查：

```text
代码 return 字段
outputs 声明字段
后续 value 引用字段
```

修复方式：

```text
outputs 补齐 return 字段。
或者把后续引用改成真实 output.id。
```

---

### 7.8 文档解析没有内容

优先检查：

```text
chatConfig.fileSelectConfig 是否打开
workflowStart 是否有 userFiles
readFiles.fileUrlList 是否二维数组
readFiles outputs 是否有 system_text
下游是否引用 system_text
```

修复方式：

```text
开启 fileSelectConfig。
给 workflowStart 补 userFiles。
fileUrlList 改成 [["node_start", "userFiles"]]。
下游改为 ["read_files", "system_text"]。
```

---

### 7.9 图片识别失败

优先检查：

```text
chatConfig.fileSelectConfig.canSelectImg 是否为 true
workflowStart 是否有 userFiles
AI 节点 fileUrlList 是否引用 userFiles
aiChatVision 是否为 true
模型是否支持视觉
```

修复方式：

```text
开启 canSelectImg。
补 fileUrlList。
aiChatVision 改为 true。
提醒导入后选择支持视觉的模型。
```

---

### 7.10 AI 节点不能运行

优先检查：

```text
model 是否为空
model 是否被编造
平台模型是否可用
是否选择了不支持图片/JSON Schema/推理的模型
```

修复方式：

```text
如果模型不确定，留空。
加入【需要手动配置：AI 模型】。
不要改动其他节点结构。
```

---

### 7.11 知识库搜索失败

优先检查：

```text
datasets 是否为空
是否编造 datasetId
userChatInput 是否引用正确
下游 AI quoteQA 是否引用 quoteQA
```

修复方式：

```text
删除伪造 datasetId。
保留空 datasets。
提醒导入后手动绑定知识库。
```

---

### 7.12 HTTP 请求失败

优先检查：

```text
URL 是否真实
请求方法是否正确
Header 是否缺鉴权
Body 是否缺参数
响应字段 outputs 是否声明
```

修复方式：

```text
如果用户未提供接口文档，不能自动修。
返回需要手动配置清单。
```

---

### 7.13 数据库入库失败

优先检查：

```text
数据库连接是否真实存在
接口地址是否真实提供
SQL 字段是否匹配
存储过程是否存在
入库 JSON 是否符合后端要求
```

修复方式：

```text
如果用户没有提供数据库结构，不能自动修。
只检查前置 JSON 整理逻辑。
数据库连接列入手动配置。
```

---

### 7.14 maxFiles 与逻辑冲突

错误现象：

```text
上传多个文件，但只处理了第一份。
或者提示支持多文件，但输出只有一个对象。
```

优先检查：

```text
chatConfig.fileSelectConfig.maxFiles
代码是否使用 files[0]
AI 提示词是否写“这一份文件”
输出结构是否为数组
```

修复方式：

```text
如果不是明确批量需求，把 maxFiles 改为 1。
如果用户明确批量处理，把代码改成遍历，把 AI 输出改成数组。
```

---

## 8. 可自动修复与不可自动修复边界

### 8.1 可以自动修复

```text
JSON 语法错误
nodeId 重复
edge.source / edge.target 小范围错误
普通 sourceHandle / targetHandle 错误
ifElse true/false handle 错误
classify value handle 错误且能映射 key
fileUrlList 一维数组错误
readFiles.text 错误
answerNode selectedTypeIndex 错误
代码 return 字段未声明 outputs
中间 AI isResponseAnswerText 错误
maxFiles 与单文件逻辑冲突
```

---

### 8.2 不能自动修复，只能提醒

```text
AI 模型不可用
知识库未绑定
datasetId 缺失
API Key 缺失
Authorization 缺失
数据库连接缺失
真实表结构未知
真实接口文档未知
私有工具 toolId 未知
平台服务异常
模型服务异常
```

---

## 9. AI 回修输出格式

当用户发来错误时，AI 必须按这个格式回答。

```text
【错误类型】
例如：变量引用错误 / 文件上传配置错误 / 模型配置错误

【错误等级】
S1 / S2 / S3 / S4

【错误位置】
指出具体 nodeId、input.key、output.id、edge.sourceHandle、chatConfig 字段。

【错误原因】
说明为什么这个写法会导致导入失败或运行失败。

【是否能自动修复】
能 / 不能 / 部分能。

【修复动作】
说明修改了哪些字段，不要笼统写“已优化”。

【仍需手动配置】
列出模型、知识库、API、数据库等无法自动确定内容。

【修复后自检结果】
列出检查通过项。

【修复后的 JSON】
如果用户要求文件，则输出文件。
如果用户要求复制，则只输出纯 JSON。
```

---

## 10. 给其他 AI 的系统提示词

下面这段可以直接放给其他 AI 模型，让它处理 FastGPT 工作流 JSON 错误。

```text
你是 FastGPT 工作流 JSON 自检与回修助手。

你的任务：
当用户提供 FastGPT 工作流 JSON 和错误信息时，你要判断错误位置、错误原因、是否能自动修复，并返回修复后的 JSON。

最高原则：
1. 不允许凭空创造 FastGPT 节点结构。
2. 不允许编造 flowNodeType、input key、output id。
3. 不允许编造 datasetId、toolId、pluginId、API Key、Authorization、数据库连接、私有模型名。
4. 不允许一看到报错就重写整个工作流。
5. 必须先定位错误，再局部修复。
6. 不能自动确定的内容必须放入【需要手动配置】。
7. 修复后必须再次自检。
8. 如果用户要求 JSON 文件，JSON 文件中只能放纯 JSON，不能混入解释文字。

检查顺序：
1. JSON 能否解析。
2. 顶层是否有 nodes、edges、chatConfig。
3. nodeId 是否唯一。
4. flowNodeType 是否真实。
5. inputs / outputs 是否存在。
6. edge.source / edge.target 是否存在。
7. sourceHandle / targetHandle 是否正确。
8. 所有变量引用的 nodeId 和 outputId 是否存在。
9. fileUrlList 是否二维数组。
10. readFiles 是否引用 system_text。
11. answerNode 引用上游时 selectedTypeIndex 是否指向 reference。
12. code 节点 return 字段是否在 outputs 声明。
13. ifElseNode 分支是否使用 IF / ELSE。
14. classifyQuestion 分支是否使用 agents.key。
15. 是否编造 datasetId、toolId、API Key、数据库连接。
16. 是否漏写需要手动配置清单。

输出格式：
【错误类型】
【错误等级】
【错误位置】
【错误原因】
【是否能自动修复】
【修复动作】
【仍需手动配置】
【修复后自检结果】
【修复后的 JSON】
```

---

## 11. 给 AI 的错误分类关键词

AI 可以根据错误关键词优先判断方向。

```text
Unexpected token / JSON parse / invalid JSON
→ JSON 语法错误

Cannot read properties of undefined
→ 变量引用、outputs 缺失、节点字段缺失

node not found / source not found / target not found
→ edge.source 或 edge.target 错误

handle not found / branch not triggered
→ sourceHandle / targetHandle / 分支 handle 错误

fileUrlList / userFiles / no file / upload file
→ 文件上传配置或二维引用错误

system_text / readFiles / document parse
→ readFiles 输出引用错误

answerText / no answer / 指定回复为空
→ answerNode 引用或 selectedTypeIndex 错误

model not found / model unavailable / 模型不可用
→ 平台模型配置错误，不要改 JSON 主结构

dataset / knowledge base / quoteQA
→ 知识库未绑定或 quoteQA 引用错误

API key / Authorization / 401 / 403
→ 鉴权配置错误，不能编造

500 / timeout / service unavailable
→ 可能是外部服务或平台环境错误，需要结合日志判断
```

---

## 12. 如果要做成程序，自检器伪代码

下面是工程化检查思路，不一定要马上实现，但可以给开发或 AI 参考。

```javascript
function validateWorkflow(workflow) {
  const errors = [];
  const warnings = [];

  // 1. 顶层检查
  if (!workflow || typeof workflow !== 'object') {
    errors.push({ level: 'S1', type: 'TOP_LEVEL', msg: 'workflow 不是对象' });
    return { errors, warnings };
  }

  if (!Array.isArray(workflow.nodes)) {
    errors.push({ level: 'S1', type: 'TOP_LEVEL', msg: 'nodes 不是数组' });
  }

  if (!Array.isArray(workflow.edges)) {
    errors.push({ level: 'S1', type: 'TOP_LEVEL', msg: 'edges 不是数组' });
  }

  if (!workflow.chatConfig || typeof workflow.chatConfig !== 'object') {
    warnings.push({ level: 'S4', type: 'CHAT_CONFIG', msg: 'chatConfig 缺失或不是对象' });
  }

  const nodes = workflow.nodes || [];
  const edges = workflow.edges || [];

  // 2. nodeId 检查
  const nodeMap = new Map();
  for (const node of nodes) {
    if (!node.nodeId) {
      errors.push({ level: 'S1', type: 'NODE', msg: '节点缺少 nodeId' });
      continue;
    }
    if (nodeMap.has(node.nodeId)) {
      errors.push({ level: 'S1', type: 'NODE', nodeId: node.nodeId, msg: 'nodeId 重复' });
    }
    nodeMap.set(node.nodeId, node);

    if (!node.flowNodeType) {
      errors.push({ level: 'S1', type: 'NODE', nodeId: node.nodeId, msg: '缺少 flowNodeType' });
    }

    if (!Array.isArray(node.inputs)) {
      errors.push({ level: 'S1', type: 'NODE', nodeId: node.nodeId, msg: 'inputs 不是数组' });
    }

    if (!Array.isArray(node.outputs)) {
      errors.push({ level: 'S1', type: 'NODE', nodeId: node.nodeId, msg: 'outputs 不是数组' });
    }
  }

  // 3. edge 检查
  for (const edge of edges) {
    if (!nodeMap.has(edge.source)) {
      errors.push({ level: 'S1', type: 'EDGE', msg: `edge.source 不存在: ${edge.source}` });
    }
    if (!nodeMap.has(edge.target)) {
      errors.push({ level: 'S1', type: 'EDGE', msg: `edge.target 不存在: ${edge.target}` });
    }
  }

  // 4. 变量引用检查
  function getOutputs(nodeId) {
    const node = nodeMap.get(nodeId);
    return new Set((node?.outputs || []).map(o => o.id));
  }

  for (const node of nodes) {
    for (const input of node.inputs || []) {
      const value = input.value;

      // 普通引用 ["nodeId", "outputId"]
      if (Array.isArray(value) && value.length === 2 && typeof value[0] === 'string') {
        const [refNodeId, refOutputId] = value;
        if (!nodeMap.has(refNodeId)) {
          errors.push({ level: 'S2', type: 'REFERENCE', nodeId: node.nodeId, msg: `引用节点不存在: ${refNodeId}` });
        } else if (!getOutputs(refNodeId).has(refOutputId)) {
          errors.push({ level: 'S2', type: 'REFERENCE', nodeId: node.nodeId, msg: `引用输出不存在: ${refNodeId}.${refOutputId}` });
        }

        const refIndex = (input.renderTypeList || []).indexOf('reference');
        if (refIndex >= 0 && input.selectedTypeIndex !== refIndex) {
          errors.push({ level: 'S2', type: 'REFERENCE', nodeId: node.nodeId, msg: `selectedTypeIndex 未指向 reference` });
        }
      }

      // 文件引用 [["nodeId", "userFiles"]]
      if (input.key === 'fileUrlList') {
        const ok =
          Array.isArray(value) &&
          Array.isArray(value[0]) &&
          value[0].length === 2;

        if (!ok) {
          errors.push({ level: 'S2', type: 'FILE_REFERENCE', nodeId: node.nodeId, msg: 'fileUrlList 必须使用二维数组引用' });
        }
      }
    }
  }

  return { errors, warnings };
}
```

---

## 13. 最推荐的实际使用方式

### 13.1 给其他 AI 生成工作流时

流程：

```text
1. 先让 AI 根据需求生成 JSON。
2. 强制 AI 执行本文档第 6 章自检。
3. 发现错误先修复，不输出未自检 JSON。
4. 输出 JSON 文件时，文件内只放纯 JSON。
5. 另给说明文档写手动配置项和测试建议。
```

---

### 13.2 当用户反馈错误时

流程：

```text
1. 用户提供当前 JSON。
2. 用户提供错误截图或文字。
3. AI 按第 7 章错误定位表分类。
4. 只修改错误位置。
5. 修复后再执行第 6 章自检。
6. 返回修复结果。
```

---

### 13.3 当错误像是平台问题时

如果错误是：

```text
模型不可用
接口超时
平台 AI 节点全部不可用
知识库服务异常
数据库连接失败
```

AI 不应乱改 JSON，而应说明：

```text
这不是工作流 JSON 结构错误，优先检查平台配置或服务状态。
```

---

## 14. 对你现有文件的追加建议

你现在已有：

```text
FastGPT_工作流JSON生成通用规则_给AI模型使用_2026-05-11_源码约束整改版.md
FastGPT_单节点母版与工作流拼接规则_给AI模型使用_2026-05-11_整改版.md
FastGPT_工作流JSON生成通用规则_帮助总结_2026-05-11.txt
```

建议新增第 4 个文件：

```text
FastGPT_工作流JSON错误自检与回修协议_给AI模型使用_2026-05-11.txt
```

它和前面文件的关系：

```text
通用规则文件：告诉 AI 什么能生成、什么不能生成。
单节点母版文件：告诉 AI 节点怎么写、怎么连。
帮助总结文件：说明这些规则有什么价值。
错误回修协议：告诉 AI 出错后怎么查、怎么修、怎么返回。
```

四个文件合起来，才更完整。

---

## 15. 最终结论

要实现“给其他 AI 错误异常，让它自己判断哪里出错、修改并返回”，必须做成下面的闭环：

```text
错误输入
↓
错误分类
↓
字段定位
↓
可修复性判断
↓
局部修复
↓
完整自检
↓
返回修复后的 JSON
```

最重要的原则：

```text
能自动修的，只修错误位置。
不能确定的，绝不编造。
平台配置类错误，提醒手动配置。
修复后必须再次自检。
JSON 文件中只放 JSON，不混解释。
```

一句话总结：

> 让 AI 自检不是让它“凭感觉看一遍”，而是给它一套固定的错误分类、检查清单、修复规则和回修输出格式。这样它才能在 FastGPT 工作流 JSON 出错时，判断是节点错、连线错、变量错、文件配置错、模型配置错，还是平台环境错，然后进行局部修复并返回更稳定的结果。
