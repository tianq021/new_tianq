# FastGPT 总规范辅助补丁：测试 JSON + 未知错误 + 自检增强

版本：2026-05-12 patch-01  
用途：给其他 AI 模型使用，作为《FastGPT AI模型专用工作流 JSON 生成总规范》的辅助补丁。  
定位：**不是替代源文件，而是追加测试证据、未知错误处理协议、自检增强规则和文件上传修正案例。**

---

## 0. 使用顺序

AI 模型生成 FastGPT 工作流 JSON 时，应按以下顺序使用资料：

1. 先读源文件：`FastGPT_AI模型专用_工作流JSON生成总规范_整合版_2026-05-12.md/txt`。
2. 再读本补丁：用于补充最新测试 JSON、未知错误、文件上传、运行失败排查和自检增强。
3. 如果源文件与本补丁发生冲突：
   - 以真实导出测试 JSON 为最高证据；
   - 以本补丁新增规则修正源文件中的旧判断；
   - 如果仍无法确定，必须要求最小复现，不允许编造。

---

## 1. 本补丁新增内容总览

本补丁新增：

- 全部测试 JSON 证据索引；
- 文件上传 + 文档解析失败案例修正；
- `workflowStart.userFiles` 强制检查；
- `readFiles.fileUrlList` 强制引用规则；
- “自检正常但运行失败”的未知错误兜底协议；
- JSON 静态自检清单增强项；
- 节点资源类错误不可自动修复规则；
- 最小复现测试路线。

---

## 2. 已测试 JSON 证据索引

> 说明：这些 JSON 文件是本轮真实导出或修正后的测试证据。AI 不应盲目复制其中 nodeId；复用时必须重新生成唯一 nodeId，并同步 edges 和变量引用。

| 测试文件 | nodes | edges | flowNodeType | pluginId | sha256前16位 |
|---|---:|---:|---|---|---|
| `数据库.json` | - | - | `解析失败/文本` | `-` | `0e22b7baf20d1833` |
| `工具调用.json` | - | - | `解析失败/文本` | `-` | `d75f0d8a66c9d2bf` |
| `工具调用 (1).json` | - | - | `解析失败/文本` | `-` | `6ce7c69be9c3e12a` |
| `工具调用(1).json` | - | - | `解析失败/文本` | `-` | `cd7b10cd7a398f57` |
| `用户选择 userSelect.json` | - | - | `解析失败/文本` | `-` | `cab963e2a35815b0` |
| `表单输入 formInput。.json` | - | - | `解析失败/文本` | `-` | `e676f49550c6339f` |
| `表单输入 formInput。 (1).json` | - | - | `解析失败/文本` | `-` | `90f7287bda7730ea` |
| `表单输入 formInput。 (2).json` | - | - | `解析失败/文本` | `-` | `7e879e89db1f3405` |
| `变量更新 variableUpdate。.json` | - | - | `解析失败/文本` | `-` | `70f734c50fe3de9e` |
| `批量执行 loop.json` | - | - | `解析失败/文本` | `-` | `46d9a5faebe5f681` |
| `自定义工具变量 toolParams.json` | - | - | `解析失败/文本` | `-` | `880b3c3c2a753f82` |
| `企业微信 webhook.json` | - | - | `解析失败/文本` | `-` | `c93d0ec445866837` |
| `钉钉 webhook.json` | - | - | `解析失败/文本` | `-` | `1c2abc0d7f450547` |
| `飞书 webhook.json` | - | - | `解析失败/文本` | `-` | `c91ee74a9991cce9` |
| `1111111.json` | - | - | `解析失败/文本` | `-` | `ed0251d622635add` |
| `11.json` | - | - | `解析失败/文本` | `-` | `96f18a6770a89088` |
| `粘贴的文本 (1)(58).txt` | 6 | 4 | `userGuide, workflowStart, readFiles, textEditor, chatNode, answerNode` | `-` | `12b8d51ae301d610` |
| `FastGPT_上传文件并总结内容_修正版_2026-05-12.json` | 6 | 4 | `userGuide, workflowStart, readFiles, textEditor, chatNode, answerNode` | `-` | `0d3087bbebd7d30c` |

---

## 3. 重要修正：文件上传 + 文档解析工作流

### 3.1 失败根因

本轮测试发现，部分 AI 生成的“上传文件并总结内容”工作流看起来结构完整，但运行失败。根因通常不是 `readFiles` 节点不存在，而是文件引用错误。

错误写法：

```json
"value": [["start", "userChatInput"]]
```

这表示把用户输入文本当作文件链接数组传给文档解析，必然不稳定或失败。

正确写法：

```json
"value": [["start", "userFiles"]]
```

### 3.2 三个强制条件

凡是使用 `readFiles` 解析上传文件，必须同时满足：

```text
1. workflowStart.outputs 中存在 userFiles；
2. chatConfig.fileSelectConfig 开启文件上传；
3. readFiles.inputs.fileUrlList.value = [[workflowStart节点ID, "userFiles"]]。
```

缺任何一个，都不能声称“文件上传 + 文档解析已实现”。

### 3.3 反向禁止规则

如果 `workflowStart.outputs` 没有 `userFiles`，则任何节点都不能引用：

```json
["workflowStart节点ID", "userFiles"]
```

如果用户需求必须上传文件，但当前母版没有 `userFiles`，AI 应输出：

```text
当前 workflowStart 母版不支持文件上传输出，需要使用文件上传版 workflowStart 或让平台手动开启文件上传后导出母版。
```

### 3.4 answerNode 输出建议

`answerNode.text` 输出上游结果时，优先使用文本插值：

```text
{$aiChat.answerText$}
```

如果使用数组引用：

```json
["aiChat", "answerText"]
```

必须确认该输入 UI 处于 `reference` 模式，否则可能被平台当作普通文本或出现显示异常。

---

## 4. 未知错误兜底协议

### 4.1 定义

当静态 JSON 自检没有发现明显错误，但用户仍反馈：

- 导入失败；
- 运行失败；
- 节点没有输出；
- 流程中断；
- 结果为空；
- 用户无法说清楚哪里错；
- 平台没有清晰报错；

则进入：

```text
UNKNOWN_RUNTIME_ERROR
```

### 4.2 最高原则

```text
静态自检正常 ≠ 工作流一定能运行成功。
未知错误不能盲目重写整个 JSON。
必须先收集运行证据或做最小复现。
```

AI 禁止回答：

```text
我自检正常，所以应该没问题。
```

应回答：

```text
静态自检未发现明显结构错误，但运行失败仍可能来自运行时配置、平台资源、模型服务、文件上传、权限、插件、数据库、网络或节点版本差异。需要进入未知错误排查流程，先做最小复现。
```

### 4.3 证据收集清单

未知错误时，AI 应要求或引导用户提供：

```text
1. 当前完整 JSON；
2. FastGPT 运行详情截图；
3. 报错文字；
4. 哪个节点最后执行成功；
5. 哪个节点开始没有输出；
6. 用户输入内容；
7. 上传文件类型；
8. 是否手动修改过 JSON；
9. FastGPT 版本 / 云版或私有版；
10. 模型是否可用；
11. 知识库、数据库、webhook、appModule 是否已手动配置。
```

### 4.4 高概率排查顺序

未知错误优先按以下顺序排查：

```text
A. workflowStart 是否真实具备被引用输出，例如 userFiles；
B. 所有引用是否指向 outputs.id，而不是 key/label；
C. readFiles.fileUrlList 是否是 [[start,userFiles]]；
D. answerNode 是否使用正确引用方式；
E. 模型是否可用，是否支持视觉或文件；
F. 知识库、数据库、webhook、appModule.pluginId 是否依赖真实平台资源；
G. catchError 是否导致错误直接中断；
H. 节点是否为当前平台版本支持；
I. 导入后平台是否自动改写字段；
J. 是否是平台服务异常、权限或网络问题。
```

---

## 5. 最小复现原则

未知错误时，不要修改大流程。先按节点类别做最小复现：

| 错误方向 | 最小复现结构 |
|---|---|
| 文件上传 / 文档解析 | `workflowStart + readFiles + answerNode` |
| AI 节点 | `workflowStart + chatNode + answerNode` |
| 数据库 | `code 固定 SQL + 数据库连接 tool + answerNode` |
| webhook | `workflowStart + webhook tool + 固定成功 answerNode` |
| appModule | `workflowStart + appModule + answerNode` |
| loop | `固定数组 + loopStart + loopEnd + loopArray` |
| tools 工具调用 | `workflowStart + tools + 一个 selectedTools 工具 + stopTool + answerNode` |

每次只改一个可疑点，记录测试结果，不允许一次性重写整个工作流。

---

## 6. 自检清单增强项

在源文件原有自检清单后追加：

```text
19. 如果自检通过但运行失败，不得认定 JSON 正确；必须进入 UNKNOWN_RUNTIME_ERROR 流程。
20. 未知错误优先做最小复现，不允许重写整个工作流。
21. 没有运行详情时，只能给排查路径，不能编造错误原因。
22. 平台资源类错误不能通过改 JSON 解决，必须提醒用户检查模型、知识库、数据库、插件、权限、网络和服务状态。
23. 使用 readFiles 时，workflowStart.outputs 必须有 userFiles。
24. readFiles.fileUrlList 必须是二维数组 [[workflowStart节点ID,"userFiles"]]。
25. 不允许把 userChatInput 当成 fileUrlList 传给 readFiles。
26. 如果 JSON 里存在 [[start,"userFiles"]]，必须检查 start.outputs 是否真的声明 userFiles。
27. 如果 chatConfig.fileSelectConfig 未开启文件上传，不能声称该工作流支持上传文件。
28. answerNode 使用数组引用时，必须确认输入处于 reference 模式；否则优先使用 {$nodeId.outputId$} 插值。
```

---

## 7. 不可自动修复项

以下错误不能靠 AI 自己改 JSON 解决：

```text
模型不可用或模型名不存在；
知识库未绑定或 datasetId 属于别的账号；
数据库连接、账号、密码、host、port 未配置；
webhook URL、secret、token 未配置；
appModule.pluginId 不存在或属于别的应用；
文件上传权限未开启；
平台版本不支持某节点；
平台服务异常、网络超时、插件权限不足。
```

处理方式：列入【需要手动配置】，并给出最小测试方案。

---

## 8. 本补丁建议合并位置

建议把本补丁内容合并到源文件中的以下位置：

```text
1. “变量引用规则”后追加：文件上传 userFiles 强制规则；
2. “readFiles 文档解析”节点后追加：文件上传三条件；
3. “answerNode 指定回复”后追加：数组引用 vs 文本插值规则；
4. “JSON 自检清单”后追加：第 19-28 条增强项；
5. “错误回修协议”中新增：UNKNOWN_RUNTIME_ERROR；
6. “最小复现测试”新增：按节点类别拆分测试。
```

---

## 9. 给 AI 模型的执行口令

当用户让你生成 FastGPT 工作流 JSON 时，必须执行：

```text
先按源文件选择母版；
再按本补丁检查测试 JSON 证据；
凡涉及文件上传，强制检查 userFiles / fileSelectConfig / readFiles.fileUrlList；
凡遇到自检正常但运行失败，进入 UNKNOWN_RUNTIME_ERROR；
凡涉及真实资源 ID、密钥、模型、数据库、webhook、appModule.pluginId，不得编造；
输出 JSON 前必须执行静态自检清单。
```
