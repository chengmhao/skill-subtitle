---
name: subtitle-to-pdfbook
description: 将双语字幕文件转换为A4规格PDF台词本；当用户需要制作字幕台词本、双语字幕导出PDF、字幕内容整理打印时使用
dependency:
  python:
    - reportlab==4.0.7
    - srt==3.5.3
    - webvtt-py==0.4.6
    - ass==0.5.2
---

# 双语字幕转PDF台词本

## 任务目标
- 将双语字幕文件（SRT/VTT/ASS）转换为格式化的PDF台词本
- 支持A4纸张大小（210mm × 297mm），表格形式展示
- 左列显示字幕1内容，右列显示字幕2内容
- 无底色，清晰的表格边框

## 前置准备
- 依赖说明：scripts脚本所需的依赖包
  ```
  reportlab==4.0.7
  srt==3.5.3
  webvtt-py==0.4.6
  ass==0.5.2
  ```

## 输入要求
- 支持的字幕格式：SRT、VTT、ASS
- 双语字幕输入方式：
  1. **双文件模式**：提供两个字幕文件（如 `movie_zh.srt` 和 `movie_en.srt`）
  2. **单文件双语模式**：一个字幕文件包含双语内容（需按格式规范组织）

## 操作步骤

### 1. 准备字幕文件
- 确认字幕文件格式（SRT/VTT/ASS）
- 确认双语模式：
  - 双文件模式：两个字幕文件的时间轴需对应
  - 单文件模式：参考 [references/subtitle_format.md](references/subtitle_format.md) 中的格式规范

### 2. 执行转换
调用脚本生成PDF台词本：

```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 <字幕文件1路径> \
  --subtitle2 <字幕文件2路径> \
  --output <输出PDF路径> \
  [--title <台词本标题>]
```

**参数说明**：
- `--subtitle1`：字幕文件1路径（左列内容）
- `--subtitle2`：字幕文件2路径（右列内容）
- `--output`：输出PDF文件路径
- `--title`：可选，台词本标题（默认：双语台词本）
- `--font`：可选，指定字体路径（支持中文）

**单文件双语模式**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --single-file <双语字幕文件路径> \
  --output <输出PDF路径>
```

### 3. 验证输出
- 检查生成的PDF文件大小是否为A4纸张（210mm × 297mm）
- 确认表格布局正确显示
- 验证字幕内容完整性

## 英语单词高亮功能

支持对英语字幕中的特定单词进行高亮显示，便于词汇学习和记忆。

### 高亮释义功能

1. 高亮单词使用指定颜色标记（默认：深红色 #631511）
2. 系统自动收集高亮单词，每10个不重复单词为一组
3. 释义集中展示在下一行台词下方，占用两列空间
4. 已高亮单词不重复展示释义

示例效果：
```
| I want to abandon this plan. | 我想放弃这个计划。 |
| abandon vt. 放弃；abound vi. 大量存在；abroad adv. 在国外；... | |
```

### 词汇难度等级

按难度从低到高排列：

| 等级 | 词汇类型 | 说明 |
|------|----------|------|
| Level 1 | 四级 (CET4) | 基础词汇 |
| Level 2 | 六级 (CET6) = 专四 (TEM4) | 中级词汇 |
| Level 3 | 专八 (TEM8) = 考研 (Kaoyan) | 中高级词汇 |
| Level 4 | 雅思 (IELTS) = 托福 (TOEFL) | 高级词汇 |
| Level 5 | GMAT = GRE = SAT | 顶级词汇 |

### 高亮规则

**选择某个等级时，自动包含该等级及更高等级的所有词汇**

例如：
- 选择 `--highlight-cet4`：高亮四级 + 六级 + 专四 + 专八 + 考研 + 雅思 + 托福 + GMAT + GRE + SAT
- 选择 `--highlight-cet6`：高亮六级 + 专四 + 专八 + 考研 + 雅思 + 托福 + GMAT + GRE + SAT
- 选择 `--highlight-ielts`：高亮雅思 + 托福 + GMAT + GRE + SAT
- 选择 `--highlight-gre`：高亮 GRE + SAT

### 按难度等级高亮

| 参数 | 说明 | 高亮范围 |
|------|------|----------|
| `--highlight-cet4` | 四级及以上 | Level 1-5 全部 |
| `--highlight-cet6` | 六级及以上 | Level 2-5 |
| `--highlight-tem4` | 专四及以上 | Level 2-5 |
| `--highlight-tem8` | 专八及以上 | Level 3-5 |
| `--highlight-kaoyan` | 考研及以上 | Level 3-5 |
| `--highlight-ielts` | 雅思及以上 | Level 4-5 |
| `--highlight-toefl` | 托福及以上 | Level 4-5 |
| `--highlight-gmat` | GMAT及以上 | Level 5 |
| `--highlight-gre` | GRE及以上 | Level 5 |
| `--highlight-sat` | SAT词汇 | Level 5 |
| `--highlight-words` | 自定义词汇 | 用户指定 |

### 按分类高亮

| 参数 | 说明 | 包含词汇 |
|------|------|----------|
| `--highlight-hot` | 热门单词 | 四级、六级、考研 |
| `--highlight-college` | 大学单词 | 四级、六级、考研、专四、专八 |
| `--highlight-abroad` | 出国单词 | 雅思、托福、GMAT、GRE、SAT |

### 使用示例

**高亮四级及以上所有词汇**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-cet4
```

**高亮六级及以上词汇**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-cet6
```

**高亮专八及以上词汇（专八+考研+雅思+托福+GMAT+GRE+SAT）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-tem8
```

**高亮雅思及以上词汇（雅思+托福+GMAT+GRE+SAT）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-ielts
```

**高亮GMAT词汇（GMAT+GRE+SAT）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-gmat
```

**高亮GRE词汇（GRE+SAT）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-gre
```

**高亮热门单词（四级+六级+考研）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-hot
```

**高亮大学单词（四级+六级+考研+专四+专八）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-college
```

**高亮出国单词（雅思+托福+GMAT+GRE+SAT）**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-abroad
```

**同时使用自定义词汇**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-cet4 \
  --highlight-words "important,significant"
```

**组合使用分类高亮和等级高亮**：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-hot \
  --highlight-abroad
```

### 词汇量参考

| 词汇类型 | 词汇量 |
|----------|--------|
| 四级 (CET4) | 约1200个 |
| 六级 (CET6) | 约1200个 |
| 专四 (TEM4) | 约600个 |
| 专八 (TEM8) | 约650个 |
| 考研 (Kaoyan) | 约700个 |
| 雅思 (IELTS) | 约1800个 |
| 托福 (TOEFL) | 约2500个 |
| GMAT | 约2100个 |
| GRE | 约6500个 |
| SAT | 约3500个 |

**高亮四级时总计约15000个词汇会被高亮**

### 自定义高亮词汇

使用 `--highlight-words` 参数指定需要高亮的单词：

**方式一：直接指定单词（逗号分隔）**
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-words "important,significant,meaningful"
```

**方式二：指定词汇文件**
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-words words.txt
```

词汇文件格式（每行一个单词，支持带释义）：
```
important
significant	adj. 重要的
meaningful
```

### 自定义高亮样式

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--highlight-color` | 高亮文字颜色 | #631511（深红色） |
| `--highlight-column` | 高亮列：1=左列, 2=右列, 3=两列 | 2（右列） |

**示例：自定义高亮样式**
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --highlight-cet4 \
  --highlight-color "#ff0000" \
  --highlight-column 2
```

## 资源索引
- 核心脚本：[scripts/bilingual_subtitle_to_pdf.py](scripts/bilingual_subtitle_to_pdf.py)
  - 功能：解析字幕文件并生成PDF台词本
  - 支持格式：SRT、VTT、ASS
  - 支持单词高亮及释义显示功能
- 格式规范：[references/subtitle_format.md](references/subtitle_format.md)
  - 字幕格式详细说明
  - 双语字幕组织规范
  - 时间轴对齐要求
- 初高中词汇（带释义）：[references/school_words_with_def.txt](references/school_words_with_def.txt)
  - 包含约5400个初高中核心词汇及释义
  - 用于释义显示功能
- 全部词汇释义：[references/all_words_with_def.txt](references/all_words_with_def.txt)
  - 包含约14700个单词及其释义
  - 来源：四级、六级、专八、考研、雅思、托福、GMAT、GRE、SAT词汇库
  - 用于高亮单词时显示释义
- 四级词汇：[references/cet4_words.txt](references/cet4_words.txt)
  - 包含约1200个四级核心词汇
  - 用于 `--highlight-cet4` 功能
- 六级词汇：[references/cet6_words.txt](references/cet6_words.txt)
  - 包含约1200个六级核心词汇
  - 用于 `--highlight-cet6` 功能
- 专四词汇：[references/tem4_words.txt](references/tem4_words.txt)
  - 包含约600个专四核心词汇
  - 用于 `--highlight-tem4` 功能
- 专八词汇：[references/tem8_words.txt](references/tem8_words.txt)
  - 包含约650个专八核心词汇（已过滤初高中词汇）
  - 用于 `--highlight-tem8` 功能
- 考研词汇：[references/kaoyan_words.txt](references/kaoyan_words.txt)
  - 包含约700个考研核心词汇（已过滤初高中词汇）
  - 用于 `--highlight-kaoyan` 功能
- 雅思词汇：[references/ielts_words.txt](references/ielts_words.txt)
  - 包含约1800个雅思核心词汇（已过滤四六级、专四、高中词汇及停用词）
  - 用于 `--highlight-ielts` 功能
- 托福词汇：[references/toefl_words.txt](references/toefl_words.txt)
  - 包含约2500个托福核心词汇（已过滤四六级、专四、高中词汇及停用词）
  - 用于 `--highlight-toefl` 功能
- GMAT词汇：[references/gmat_words.txt](references/gmat_words.txt)
  - 包含约2100个GMAT核心词汇（已过滤四六级、专四、高中词汇及停用词）
  - 用于 `--highlight-gmat` 功能
- GRE词汇：[references/gre_words.txt](references/gre_words.txt)
  - 包含约6500个GRE核心词汇（已过滤四六级、专四、高中词汇及停用词）
  - 用于 `--highlight-gre` 功能
- SAT词汇：[references/sat_words.txt](references/sat_words.txt)
  - 包含约3500个SAT核心词汇（已过滤初高中词汇）
  - 用于 `--highlight-sat` 功能

## 中文字体支持

脚本会自动检测系统中可用的中文字体，无需手动配置。支持的中文字体包括：

**Linux 系统**：
- 文泉驿微米黑 (wqy-microhei)
- 文泉驿正黑 (wqy-zenhei)
- 思源黑体 (Noto Sans CJK)
- 其他支持中文的字体

**macOS 系统**：
- 苹方 (PingFang)
- 黑体-简 (STHeiti)
- 冬青黑体 (Hiragino Sans GB)

**Windows 系统**：
- 微软雅黑 (msyh)
- 黑体 (simhei)
- 宋体 (simsun)

如果系统中没有检测到中文字体，可以通过 `--font` 参数手动指定字体文件路径：

```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --font /path/to/chinese_font.ttf
```

## 注意事项
- 双文件模式下，两个字幕文件的时间轴应保持一致，否则可能出现内容错位
- 建议使用UTF-8编码的字幕文件以避免乱码
- 生成的PDF采用A4纸张规格（210mm × 297mm），适合打印
- 中文字体会自动检测，如检测失败请手动指定字体路径
- 表格形式展示，无底色，便于阅读和打印
- 单词高亮功能仅对英文单词生效，支持四六级、专四专八、考研、雅思托福、GMAT、GRE、SAT词汇及自定义词汇
- 可同时使用多个高亮参数，词汇会合并
- 分类高亮（热门/大学/出国）可与难度等级高亮组合使用
