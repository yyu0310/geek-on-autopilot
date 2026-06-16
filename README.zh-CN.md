[English](README.md) | [繁體中文](README.zh-TW.md) | 简体中文

# geek-on-autopilot

五个让 Claude Code 更顺手的自定义斜杠命令。

## 解决的问题

- AI 训练数据有截止日期，时效性问题的答案不可靠
- Claude 官方文档更新快，不知道去哪查
- AI 写出来的文字有 AI 味，需要手动润色
- Session 结束后不知道自己做了什么，没有留下记录
- Marp 演示文稿导出前没有统一的 QA 流程
- Pandoc 默认字体不支持中英混排，导出 PDF 字体很丑

## 命令一览

| 命令 | 功能 |
|---|---|
| `/latest` | 强制联网搜索，禁止仅依赖训练数据回答时效性问题 |
| `/claude-docs` | 直连路由至 Claude 官方文档，附来源 URL |
| `/no-ai-trace` | 扫描 AI 写作痕迹，17 条规则逐条检查 |
| `/session-review` | Session 收尾四模块盘点，35 行以内 |
| `/marp-export` | Marp 演示文稿 QA 检查后导出 PDF |
| `/open-source-skill` | 安全扫描、清理、推入开源 repo 全流程 |
| `/local-md-to-pdf` | MD 转 PDF，套用 PingFang TC 字体模板 |

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

### `/no-ai-trace`

扫描文案的 AI 写作痕迹。按 17 条规则逐条检查，列出违规原句和修改建议，最后给出语气总评。

```
/no-ai-trace                    # 检查对话中最近一次的文案输出
/no-ai-trace [粘贴要检查的文字]
```

17 条规则涵盖：术语堆砌、否定前提句、能力名词化、破折号滥用、自问自答、过渡词、碎句排比等常见 AI 写作痕迹。

---

### `/session-review`

Claude Code session 结束前的四模块盘点：

1. **精华蒸馏** — 本次的重要决策、新知识点、值得记住的洞察（最多 8 条）
2. **遗漏事项** — 对话中提到但未完成的事（⬜ 待执行 / ❓ 待确认）
3. **Memory 建议** — 哪些值得存入 Claude 的记忆系统
4. **文档检查** — 代码有改动的话，相关文档是否已同步更新

全部输出在 35 行以内。

---

### `/marp-export`

Marp 演示文稿提交前 QA + 导出 PDF：

1. 扫描草稿标记（`【` 开头的备注），有的话等确认清除
2. 确认 `assets/` 图片都存在
3. 导出 PDF，报告路径和文件大小

需要：Node.js（使用 `npx` 执行 `@marp-team/marp-cli`）

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

### `/local-md-to-pdf`

将 Markdown 文件转为 PDF，字体使用 PingFang TC（苹方-繁）。PingFang TC 是中英混排 PDF 渲染 bug 最少的字体，Mac 生态免费内置，Windows / Linux 需另购。流程分两步：先用 pandoc 转 DOCX，再用 LibreOffice 转 PDF。转换前会先扫描格式陷阱（序号列表前是否有空行），避免 pandoc 解析出错。`reference_pingfang.docx` 字体模板已包含在 repo 中，clone 后设置一个路径即可使用。

全程本地转换，不依赖任何第三方服务，文档内容不会传出去，适合有隐私顾虑的工作文档。

需要：pandoc、LibreOffice（`brew install pandoc && brew install --cask libreoffice`）

```
/local-md-to-pdf                    # 转换 IDE 当前打开的 .md 文件
/local-md-to-pdf /path/to/file.md
```

## 许可证

MIT
