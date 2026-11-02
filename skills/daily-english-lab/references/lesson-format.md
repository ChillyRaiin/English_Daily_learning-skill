# 讲义数据与生成

脚本只负责排版和可重复的机械检查；选题、事实核验、英语质量、题目与答案正确性仍由助手完成。输入为 UTF-8 JSON：

```json
{
  "date": "2026-11-02",
  "title": "Gradient Descent: Learning by Following the Slope",
  "topic": "Machine learning",
  "level": "CET-6",
  "total_minutes": 54,
  "timing": [
    {"label": "Preview", "minutes": 2},
    {"label": "Reading", "minutes": 9},
    {"label": "Chunks", "minutes": 8},
    {"label": "Reasoning", "minutes": 7},
    {"label": "Listening", "minutes": 13},
    {"label": "Retelling", "minutes": 7},
    {"label": "Writing", "minutes": 5},
    {"label": "Quick check", "minutes": 3}
  ],
  "blocks": [
    {"heading": "Reading", "kind": "reading", "paragraphs": ["An original English teaching passage is supplied as paragraphs."]},
    {"heading": "Chunks", "table": {"headers": ["Phrase", "Meaning and example"], "rows": [["take a small step", "Make a limited change. We take a small step before checking the result."]]}},
    {"heading": "Reasoning", "items": ["Explain how the evidence supports the conclusion."]},
    {"heading": "Answer key", "kind": "answer-key", "break_before": true, "paragraphs": ["State the answer, its reasoning and any limits."]}
  ],
  "sources": [
    {"title": "Google Machine Learning Crash Course: Gradient descent", "url": "https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent", "accessed": "2026-11-02"}
  ],
  "chinese_notes": []
}
```

这是格式示例，内容长度不代表成品标准。正式填写所有训练环节、450–650 词正文、8 个词块、4 个问题、听力链接和播放范围、输出任务、轻量路径及答案。答案块必须在所有练习之后。Reading 标注 `Original teaching passage`，正文后列事实来源；节选改用实际许可与准确标注。

块支持 `paragraphs`、`items`、`table`、`answer_lines`（0–12）、`break_before` 和 `keep_together`。短选择题用 `keep_together: true` 让题干和选项同页；不要把超过一页的正文或大表格设为整块不分页。`kind: reading` 用于统计阅读词数；`kind: answer-key` 使脚本检查答案置后。`chinese_notes` 为 `{heading, paragraphs}` 列表，非空才生成独立中文 PDF。不要把参考文件里的示例句当作用户真实训练内容。

生成（请换成当前实际路径，使用宿主提供的 Python）：

```text
python scripts/build_lesson.py --input lesson.json --output-dir outputs/2026-11-02 --stem English_Lab_2026-11-02
```

指定可嵌入 TrueType 字体时使用 `--font`、`--bold-font`、`--cjk-font`；主题背景可用 `--background '#F5EBD9'`。不指定时主讲义采用 ReportLab 自带的 Vera 字体；中文附页尝试本机常用字体，找不到就明确失败，不回退到未嵌入 STSong。脚本不会下载或分发字体。

每次在新目录试运行，或使用不同 `--stem`；默认拒绝覆盖已有同名输出。一次输出：

- 主讲义 `.pdf`、`.md`。
- 可选 `-zh-notes.pdf`、`-zh-notes.md`。
- `-validation.json`：实际字体嵌入、映射、缺字与文字完整性检查。
- `-pages/`：每个 PDF 的逐页 PNG，交付前实际查看。

脚本使用 ReportLab、pypdf、pypdfium2（见根目录 `requirements.txt`）。先检测宿主依赖；有捆绑运行时则优先使用，不固定某台电脑路径。PDF 写出后由 pypdf 重新读取实际字体结构，不仅检查源字体存在。PDFium 渲染失败或字体未嵌入均返回非零状态；脚本成功也仍须视觉检查。
