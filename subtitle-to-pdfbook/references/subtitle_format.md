# 字幕格式规范

## 支持的字幕格式

### 1. SRT (SubRip)

**文件扩展名**: `.srt`

**格式结构**:
```
序号
开始时间 --> 结束时间
字幕内容

1
00:00:01,000 --> 00:00:04,000
你好，欢迎观看

2
00:00:05,000 --> 00:00:08,000
这是一段测试字幕
```

**时间格式**: `HH:MM:SS,mmm` (时:分:秒,毫秒)

**特点**:
- 最常用的字幕格式
- 简单易读
- 支持多行字幕

---

### 2. VTT (WebVTT)

**文件扩展名**: `.vtt`

**格式结构**:
```vtt
WEBVTT

1
00:00:01.000 --> 00:00:04.000
你好，欢迎观看

2
00:00:05.000 --> 00:00:08.000
这是一段测试字幕
```

**时间格式**: `HH:MM:SS.mmm` 或 `MM:SS.mmm` (时:分:秒.毫秒)

**特点**:
- Web标准格式
- 支持样式和定位
- 与SRT类似但更灵活

---

### 3. ASS/SSA (Advanced SubStation Alpha)

**文件扩展名**: `.ass` 或 `.ssa`

**格式结构**:
```ass
[Script Info]
Title: 字幕标题
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,16,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,你好，欢迎观看
Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,这是一段测试字幕
```

**时间格式**: `H:MM:SS.cc` (时:分:秒.厘秒)

**特点**:
- 支持丰富的样式
- 支持特效和动画
- 常用于动漫字幕

---

## 双语字幕输入要求

### 模式一：双文件模式（推荐）

提供两个独立的字幕文件，程序会自动根据时间轴对齐。

**要求**:
- 两个字幕文件的时间轴应基本一致
- 文件格式可以不同（如一个SRT一个VTT）
- 时间偏差不超过1秒为佳

**示例**:
```
movie_zh.srt    ← 中文字幕
movie_en.srt    ← 英文字幕
```

**使用方式**:
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 movie_zh.srt \
  --subtitle2 movie_en.srt \
  --output output.pdf
```

---

### 模式二：单文件双语模式

一个字幕文件包含双语内容，需要按规范组织。

#### 2.1 行交替格式

每条字幕包含两行，第一行为语言1，第二行为语言2：

```srt
1
00:00:01,000 --> 00:00:04,000
你好，欢迎观看
Hello, welcome to watch

2
00:00:05,000 --> 00:00:08,000
这是一段测试字幕
This is a test subtitle
```

#### 2.2 分隔符格式

每条字幕用特定分隔符分开两种语言：

```srt
1
00:00:01,000 --> 00:00:04,000
你好，欢迎观看 | Hello, welcome to watch

2
00:00:05,000 --> 00:00:08,000
这是一段测试字幕 | This is a test subtitle
```

**常用分隔符**:
- `|` (竖线)
- `//` (双斜线)
- `---` (三短横线)

---

## 时间轴对齐规则

当两个字幕文件的时间轴不完全一致时，程序采用以下规则：

1. **重叠匹配**: 如果两个字幕的时间范围有重叠，则配对
2. **单侧显示**: 如果某个时间点只有一个字幕，则另一侧显示空白
3. **顺序保持**: 严格按时间顺序排列

**示例**:

| 字幕1时间 | 字幕2时间 | 结果 |
|----------|----------|------|
| 0-2秒 | 0-2秒 | 配对显示 |
| 2-4秒 | 2.5-4.5秒 | 配对显示（有重叠） |
| 4-6秒 | 无 | 左侧显示，右侧空白 |
| 无 | 6-8秒 | 左侧空白，右侧显示 |

---

## 文件编码要求

- **推荐**: UTF-8 (无BOM)
- **支持**: UTF-8 with BOM, GBK, GB2312
- **注意**: 非UTF-8编码可能导致乱码

---

## 字幕质量检查清单

在使用本工具前，建议检查字幕文件：

- [ ] 字幕文件可正常播放
- [ ] 时间轴连续无跳跃
- [ ] 文字无乱码
- [ ] 双语字幕时间轴基本对齐
- [ ] 文件格式与扩展名匹配

---

## 常见问题

### Q1: 字幕时间轴不一致怎么办？

**A**: 建议使用字幕编辑工具（如Subtitle Edit、Aegisub）调整时间轴后再使用。

### Q2: 生成的PDF中文显示为方框？

**A**: 需要指定支持中文的字体：
```bash
python scripts/bilingual_subtitle_to_pdf.py \
  --subtitle1 zh.srt \
  --subtitle2 en.srt \
  --output output.pdf \
  --font /path/to/chinese_font.ttf
```

### Q3: ASS字幕的样式会保留吗？

**A**: 不会。PDF台词本会提取纯文本内容，样式由PDF模板决定。

### Q4: 可以自定义PDF样式吗？

**A**: 可以修改脚本中的 `PDFGenerator` 类来调整：
- 页面大小（PAGE_WIDTH, PAGE_HEIGHT）
- 边距（MARGIN）
- 字号（LINE_HEIGHT）
- 列宽比例
