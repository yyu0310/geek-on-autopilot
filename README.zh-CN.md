[English](README.md) | [繁體中文](README.zh-TW.md) | 简体中文

# geek-on-autopilot

十二个让 Claude Code 更顺手的自定义斜杠命令。

## 解决的问题

- AI 训练数据有截止日期，时效性问题的答案不可靠
- Claude 官方文档更新快，不知道去哪查
- 其他 AI 厂商也每周更新，消息散在博客、文档与更新日志里
- AI 写出来的文字有 AI 味，需要手动润色
- 中文文案有 AI 味，英文规则扫不出来
- Session 结束后不知道自己做了什么，没有留下记录
- Marp 演示文稿导出前没有统一的 QA 流程
- Pandoc 默认字体不支持中英混排，导出 PDF 字体很丑
- AI 回答医疗问题会自信地幻觉，又没有权威来源可查

## 命令一览

| 命令 | 功能 |
|---|---|
| `/latest` | 强制联网搜索，禁止仅依赖训练数据回答时效性问题 |
| `/claude-docs` | 直连路由至 Claude 官方文档，附来源 URL |
| `/latest-ai` | 查 Claude 以外的 AI 厂商官方消息，或整理近一周更新 |
| `/no-ai-trace` | 扫描 AI 写作痕迹，17 条规则逐条检查 |
| `/no-ai-trace-lite` | 内部文档用，3 项 grep 加 4 项快扫 |
| `/no-ai-trace-zh` | 中文文案专用的 AI 痕迹检查 |
| `/session-review` | Session 收尾六模块盘点，45 行以内 |
| `/marp-export` | Marp 演示文稿 QA、导出 PDF、验收输出 |
| `/open-source-skill` | 安全扫描、清理、推入开源 repo 全流程 |
| `/md-to-pdf` | MD 转 PDF，套用 PingFang TC 字体模板 |
| `/recover-from-log` | 从 session log 救回被改坏或误删的文件内容 |
| `/med-check` | 医疗问题查权威文献作答，禁用训练数据 |

## 安装

需要 [Claude Code](https://claude.ai/code)。

```bash
git clone https://github.com/yyu0310/geek-on-autopilot.git
cd geek-on-autopilot

# 安装全部命令
for f in *.md; do
  ln -sf "$(pwd)/$f" ~/.claude/commands/"$f"
done
```

只安装需要的：

```bash
ln -sf "$(pwd)/latest.md" ~/.claude/commands/latest.md
```

安装后在 Claude Code 输入 `/latest`、`/claude-docs` 等即可使用。

`/md-to-pdf` 与 `/marp-export` 会调用 repo 根目录的 Python 脚本（`md2pdf.py`、`marp_export.py`），clone 下来的文件夹请留在原位，命令会从那里执行脚本。

## 命令说明

### `/latest`

强制联网搜索，回答时效性问题。AI 训练数据有截止日期，AI 前沿技术、版本支持状态、API 变动等问题，训练数据中的答案视为过时参考，不是结论。

```
/latest Claude Code 最新版本有什么新功能？
```

---

### `/claude-docs`

根据问题类型，直接获取对应的 Claude 官方文档页面，附来源 URL。路由表涵盖 API 参数、模型规格、Prompt Caching、Tool Use、MCP、Agent Skills 等 20+ 个主题。

```
/claude-docs prompt caching 怎么用？
/claude-docs 最新模型有哪些？
```

---

### `/latest-ai`

从各家 AI 公司的官方文档、新闻页与更新日志回答前沿 AI 问题，不靠训练数据。`/claude-docs` 管 Claude，`/latest-ai` 管其他所有厂商与跨家汇总。给问题就路由到相关公司的官方来源，不给问题就整理近一周的产品更新，先扫主要厂商。

```
/latest-ai OpenAI 这个月有调整 API 价格吗？
/latest-ai                     # 近一周汇总
```

---

### `/no-ai-trace`、`/no-ai-trace-lite`、`/no-ai-trace-zh`

三个 AI 写作痕迹检查器，按手上的文字类型挑一个：

| 命令 | 适用 | 检查方式 |
|---|---|---|
| `/no-ai-trace` | 对外英文文案：README、帖子、PR、邮件 | 17 条规则，列出违规原句与修改建议，最后给出语气总评 |
| `/no-ai-trace-lite` | 内部工作文档：提案、日志、架构说明 | 3 项机械 grep 加 4 项语义快扫，每次改完都能快速跑 |
| `/no-ai-trace-zh` | 中文文案 | Z1 到 Z11 中文专属规则，如元叙事标签、否定前提对比、翻译腔，另含基础检查 |

```
/no-ai-trace                    # 检查对话中最近一次的文案输出
/no-ai-trace [粘贴要检查的文字]
/no-ai-trace-lite docs/proposal.md
/no-ai-trace-zh [粘贴要检查的中文]
```

`/no-ai-trace` 的 17 条规则涵盖：术语堆砌、否定前提句、能力名词化、破折号与分号、自问自答、过渡词、碎句排比等常见 AI 写作痕迹。

---

### `/session-review`

Claude Code session 结束前的六模块盘点：

1. **精华蒸馏**：本次的重要决策、新知识点、值得记住的洞察（最多 8 条）
2. **遗漏事项**：只抓真正掉出所有追踪系统的事（⬜ 待执行 / ❓ 待确认）
3. **已规划事项**：未完成但已有归属的事，明确标示不算遗漏
4. **Memory 建议**：哪些值得存入 Claude 的记忆系统
5. **文档检查**：代码有改动的话，相关文档是否已同步更新
6. **QA 证据盘点**：有写代码的话，有没有跑过实际命令并留有输出

全部输出在 45 行以内。多个 session 并行做同一件事时，会一起蒸馏。

---

### `/marp-export`

Marp 演示文稿提交前 QA 加导出 PDF，由 repo 根目录的 `marp_export.py` 执行：

1. `qa` 扫描草稿标记（`TODO`、`FIXME`、`TBD`、`XXX` 与 `【` 括号），并确认本地图片都存在
2. `export` 用 `npx` 与 `@marp-team/marp-cli` 生成 PDF
3. `verify` 确认 PDF 存在、不是空文件，且比源文件新

需要：Node.js 与 Python 3

```
/marp-export                   # 导出 IDE 当前打开的 .md 文件
/marp-export /path/to/file.md
```

---

### `/open-source-skill`

将个人 skill 开源的完整 SOP。自动扫描个人路径、账号识别符、外部依赖等六类安全问题，列出问题等确认，清理后更新三语 README 和 llms.txt，最后 commit + push。

需要一次性设置：在 skill 文件顶部填入你的 repo 本地路径和 GitHub URL。

```
/open-source-skill session-review
/open-source-skill                  # 从 IDE 当前打开的 skill 开始
```

---

### `/md-to-pdf`

将 Markdown 文件转为 PDF，字体使用 PingFang TC（苹方-繁）。PingFang TC 是中英混排 PDF 渲染 bug 最少的字体，Mac 生态免费内置，Windows / Linux 需另购。repo 根目录的 `md2pdf.py` 执行整条流程：先 lint 扫描 pandoc 已知陷阱，再用 pandoc 搭配随附的 `reference_pingfang.docx` 模板转 DOCX，接着用 LibreOffice 转 PDF，最后用 `pdffonts` 检查，直到所有字体都是 PingFang TC 才放行。另有 `--strip` 输出不分页的长条版，以及 `wordcount` 字数上限检查。

全程本地转换，不依赖任何第三方服务，文档内容不会传出去，适合有隐私顾虑的工作文档。这个工具针对中文与中英混合文档，纯英文文件会过不了字体检查。

需要：Python 3、pandoc、LibreOffice、poppler（`brew install pandoc poppler && brew install --cask libreoffice`）

```
/md-to-pdf                    # 转换 IDE 当前打开的 .md 文件
/md-to-pdf /path/to/file.md
```

---

### `/recover-from-log`

当 Claude Code 的某次操作（`/simplify`、误删、误改）把文件弄坏时，从 session log 捞回原始内容还原。每个 session 的 `.jsonl` 都存了完整对话，包含每次 Read 过的文件原文和每次 Edit 的 `old_string`，被改之前的版本还在里面。skill 会诊断是哪个 session、哪次操作造成的，捞出原版，外科手术式还原：保留好的修正，而不是无脑整段回退。

它也处理一个尖锐的陷阱。skill 名称（例如 `simplify`）会被注入到每个 session 的 skill 列表，裸 grep 几乎会命中所有 session。这个 skill 改成命中实际的命令调用，并排除当前 session，才锁定真正的元凶。

```
/recover-from-log [文件名]
```

---

### `/med-check`

回答医疗/健康问题时，强迫用权威医界文献作答，而不是会在健康主题上危险幻觉的训练数据。强制「先检索再回答」的流程：Cochrane 系统性回顾、临床指南、PubMed 原始研究（走免费 E-utilities API，无需密钥）、WHO/CDC/FDA/NIH 等权威卫生机构。每个结论标证据等级（有实证／证据不足／互相矛盾）、标不确定性、附 PMID 引用；查不到就老实说查不到，绝不脑补。它会先拦急症红旗症状并提醒就医。

此为文献整理辅助，非医疗诊断。

```
/med-check [你的健康问题]
/med-check                     # 用对话中最近一个健康问题
```

## 许可证

MIT
