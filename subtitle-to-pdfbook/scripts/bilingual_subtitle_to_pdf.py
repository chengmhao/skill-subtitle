#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双语字幕转PDF台词本工具

功能：
- 支持SRT、VTT、ASS字幕格式
- 生成A4纸张大小PDF（210mm × 297mm）
- 表格形式展示，两列布局
- 左字幕1，右字幕2
- 自动分页，保持阅读流畅
- 自动检测系统中文字体
- 支持英语单词高亮（按难度等级包含更高难度词汇）

词汇难度等级（从低到高）：
Level 1: 四级 (CET4)
Level 2: 六级 (CET6) = 专四 (TEM4)
Level 3: 专八 (TEM8) = 考研 (Kaoyan)
Level 4: 雅思 (IELTS) = 托福 (TOEFL)
Level 5: GMAT = GRE = SAT

高亮规则：
1. 选择某个等级时，自动包含该等级及更高等级的词汇
2. 分类高亮：热门单词、大学单词、出国单词
"""

import argparse
import platform
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Set, Dict

from constants import (
    CliConstants,
    FontConstants,
    LanguageConstants,
    PdfLayoutConstants,
    PdfStyleConstants,
    TextConstants,
    VocabConstants,
)

# 字幕解析
try:
    import srt
except ImportError:
    srt = None

try:
    import webvtt
except ImportError:
    webvtt = None

try:
    import ass
except ImportError:
    ass = None

# PDF生成
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import mm, inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("错误：缺少reportlab库，请运行: pip install reportlab==4.0.7")
    sys.exit(1)


def detect_language(text: str) -> str:
    """
    检测文本语言
    
    参数:
        text: 文本内容
    
    返回:
        语言代码，如 'zh', 'en', 'es' 等
    """
    if not text:
        return LanguageConstants.DEFAULT_LANG_CODE

    # 统计不同字符类型的比例
    script_counts = {
        script: len(re.findall(pattern, text))
        for script, pattern in LanguageConstants.SCRIPT_PATTERNS.items()
    }

    total_chars = len(text.replace(' ', ''))
    if total_chars == 0:
        total_chars = 1

    # 根据字符比例判断语言
    if script_counts['chinese'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['zh']:
        return 'zh'
    elif script_counts['japanese'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['ja']:
        return 'ja'
    elif script_counts['korean'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['ko']:
        return 'ko'
    elif script_counts['arabic'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['ar']:
        return 'ar'
    elif script_counts['thai'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['th']:
        return 'th'
    elif script_counts['cyrillic'] / total_chars > LanguageConstants.SCRIPT_RATIO_THRESHOLDS['ru']:
        return 'ru'

    # 检测拉丁字母语言（通过常见词汇）
    text_lower = text.lower()

    scores = {}
    for lang_code, lang_words in LanguageConstants.LATIN_FEATURE_WORDS.items():
        pattern = r'\b(' + '|'.join(lang_words) + r')\b'
        scores[lang_code] = len(re.findall(pattern, text_lower))

    # 找出得分最高的语言
    max_lang = max(scores, key=scores.get)
    if scores[max_lang] > LanguageConstants.LATIN_MIN_SCORE:
        return max_lang

    # 默认英语
    return LanguageConstants.DEFAULT_LANG_CODE


def get_language_name(lang_code: str) -> str:
    """
    根据语言代码获取语言显示名称
    
    参数:
        lang_code: 语言代码
    
    返回:
        语言显示名称
    """
    return LanguageConstants.LANGUAGE_NAMES.get(lang_code, lang_code.upper())


def format_timestamp(seconds: float) -> str:
    """
    将秒数格式化为时间轴字符串
    
    参数:
        seconds: 秒数
    
    返回:
        格式化的时间轴，如 "01:30:45" 或 "30:45"（小于1小时不显示小时）
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


class SubtitleEntry:
    """字幕条目类"""
    def __init__(self, index: int, start_time: float, end_time: float, content: str):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.content = content.strip()
    
    def __repr__(self):
        return f"SubtitleEntry({self.index}, {self.start_time:.2f}s-{self.end_time:.2f}s, '{self.content[:20]}...')"


def clean_subtitle_text(text: str) -> str:
    """
    清理字幕文本中的标签和特殊符号
    支持清理: <i>, </i>, <b>, </b>, <u>, </u>, <font ...>, {\\an8}, {\\pos} 等ASS/SSA标签
    """
    # 清理HTML样式标签: <i>, </i>, <b>, </b>, <u>, </u>, <font ...>, </font>
    text = re.sub(TextConstants.HTML_STYLE_TAG_PATTERN, '', text)
    text = re.sub(TextConstants.HTML_FONT_TAG_PATTERN, '', text)
    
    # 清理ASS/SSA样式标签: {\an8}, {\pos(x,y)}, {\b1}, {\i1}, {\u1}, {\b0}, {\i0}, {\u0} 等
    text = re.sub(TextConstants.ASS_STYLE_TAG_PATTERN, '', text)
    
    # 清理其他常见标签: <c.magenta>, </c>, {\k...}, {\K...}
    text = re.sub(TextConstants.VTT_COLOR_TAG_PATTERN, '', text)
    text = re.sub(TextConstants.ASS_K_TAG_PATTERN, '', text)
    
    # 清理多余空白字符
    text = re.sub(TextConstants.WHITESPACE_PATTERN, ' ', text).strip()
    
    return text


def parse_srt(file_path: str) -> List[SubtitleEntry]:
    """解析SRT格式字幕"""
    if srt is None:
        raise ImportError("缺少srt库，请运行: pip install srt==3.5.3")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    subtitles = list(srt.parse(content))
    entries = []
    for idx, sub in enumerate(subtitles, 1):
        start = sub.start.total_seconds()
        end = sub.end.total_seconds()
        text = clean_subtitle_text(sub.content)
        if text:
            entries.append(SubtitleEntry(idx, start, end, text))
    
    return entries


def parse_vtt(file_path: str) -> List[SubtitleEntry]:
    """解析VTT格式字幕"""
    if webvtt is None:
        raise ImportError("缺少webvtt库，请运行: pip install webvtt-py==0.4.6")
    
    vtt = webvtt.read(file_path)
    entries = []
    for idx, caption in enumerate(vtt.captions, 1):
        start_str = caption.start
        end_str = caption.end
        
        def parse_vtt_time(time_str: str) -> float:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
            return 0.0
        
        start = parse_vtt_time(start_str)
        end = parse_vtt_time(end_str)
        text = clean_subtitle_text(caption.text)
        if text:
            entries.append(SubtitleEntry(idx, start, end, text))
    
    return entries


def parse_ass(file_path: str) -> List[SubtitleEntry]:
    """解析ASS/SSA格式字幕"""
    if ass is None:
        raise ImportError("缺少ass库，请运行: pip install ass==0.5.2")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        doc = ass.parse(f)
    
    entries = []
    idx = 1
    for event in doc.events:
        if isinstance(event, ass.document.Dialogue):
            start = event.start.total_seconds()
            end = event.end.total_seconds()
            text = re.sub(TextConstants.ASS_INLINE_TAG_PATTERN, '', event.text)
            text = text.replace('\\N', '\n')
            text = clean_subtitle_text(text)
            if text:
                entries.append(SubtitleEntry(idx, start, end, text))
                idx += 1
    
    return entries


def parse_subtitle(file_path: str) -> List[SubtitleEntry]:
    """自动识别并解析字幕文件"""
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == '.srt':
        return parse_srt(file_path)
    elif ext == '.vtt':
        return parse_vtt(file_path)
    elif ext in ['.ass', '.ssa']:
        return parse_ass(file_path)
    else:
        raise ValueError(f"不支持的字幕格式: {ext}，支持的格式: SRT, VTT, ASS")


def align_subtitles(subs1: List[SubtitleEntry], subs2: List[SubtitleEntry]) -> List[Tuple[SubtitleEntry, SubtitleEntry]]:
    """对齐两个字幕列表"""
    aligned = []
    i, j = 0, 0
    
    while i < len(subs1) and j < len(subs2):
        s1, s2 = subs1[i], subs2[j]
        
        overlap_start = max(s1.start_time, s2.start_time)
        overlap_end = min(s1.end_time, s2.end_time)
        
        if overlap_start < overlap_end:
            aligned.append((s1, s2))
            i += 1
            j += 1
        elif s1.end_time < s2.start_time:
            aligned.append((s1, None))
            i += 1
        else:
            aligned.append((None, s2))
            j += 1
    
    while i < len(subs1):
        aligned.append((subs1[i], None))
        i += 1
    
    while j < len(subs2):
        aligned.append((None, subs2[j]))
        j += 1
    
    return aligned


def find_chinese_font() -> Optional[str]:
    """自动检测系统中的中文字体"""
    system = platform.system()
    
    font_candidates = FontConstants.SYSTEM_FONT_CANDIDATES.get(system, [])
    
    for font_path in font_candidates:
        if Path(font_path).exists():
            return font_path
    
    if system == "Linux":
        try:
            import subprocess
            result = subprocess.run(
                FontConstants.FC_LIST_CMD,
                capture_output=True, text=True, timeout=FontConstants.FC_LIST_TIMEOUT_SECONDS
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines:
                    return lines[0].strip().split(':')[0]
        except Exception:
            pass
    
    return None


def register_chinese_font(font_path: str, font_name: str = FontConstants.CHINESE_FONT_NAME) -> str:
    """注册中文字体"""
    try:
        path = Path(font_path)
        
        if not path.exists():
            raise FileNotFoundError(f"字体文件不存在: {font_path}")
        
        if path.suffix.lower() == '.ttc':
            try:
                pdfmetrics.registerFont(
                    TTFont(font_name, str(path), subfontIndex=FontConstants.TTC_SUBFONT_INDEX)
                )
                return font_name
            except Exception:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                return font_name
        else:
            pdfmetrics.registerFont(TTFont(font_name, str(path)))
            return font_name
    
    except Exception as e:
        raise RuntimeError(f"字体注册失败 ({font_path}): {e}")


def get_page_size() -> Tuple[float, float]:
    """获取A4纸张大小"""
    width = PdfLayoutConstants.A4_WIDTH_MM * mm
    height = PdfLayoutConstants.A4_HEIGHT_MM * mm
    return (width, height)


def load_words_from_file(file_path: Path) -> Tuple[Set[str], Dict[str, str]]:
    """从文件加载词汇"""
    if not file_path.exists():
        print(f"警告：词汇文件不存在: {file_path}")
        return set(), {}
    
    words = set()
    definitions: Dict[str, str] = {}  # 单词到释义的映射
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 支持两种格式：
            # 1. 纯单词：word
            # 2. 带释义：word\t词性\t释义 或 word 释义
            if '\t' in line:
                parts = line.split('\t')
                word = parts[0].strip().lower()
                definition = parts[2].strip() if len(parts) > 2 else (parts[1].strip() if len(parts) > 1 else '')
            elif ' ' in line and not line.startswith(' '):
                parts = line.split(None, 1)
                word = parts[0].strip().lower()
                definition = parts[1].strip() if len(parts) > 1 else ''
            else:
                word = line.lower()
                definition = ''
            
            if word:
                words.add(word)
                if definition:
                    # 只保留第一个释义，避免重复
                    if word not in definitions:
                        definitions[word] = definition
    
    return words, definitions


def load_definitions(skill_dir: Path) -> Dict[str, str]:
    """
    加载合并的释义文件
    
    返回:
        释义字典：key为单词，value为释义
    """
    definitions_file = (
        skill_dir
        / VocabConstants.REFERENCES_DIRNAME
        / VocabConstants.DEFINITIONS_FILENAME
    )
    definitions = {}
    
    if definitions_file.exists():
        with open(definitions_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '\t' in line:
                    parts = line.split('\t', 1)
                    word = parts[0].strip().lower()
                    defn = parts[1].strip() if len(parts) > 1 else ''
                    if word and defn:
                        definitions[word] = defn
        print(f"已加载 {len(definitions)} 个单词释义")
    
    return definitions


def load_all_vocab_files(skill_dir: Path) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    """
    加载所有词汇文件
    
    返回:
        (词汇字典, 释义字典)
        词汇字典：key为词汇类型，value为词汇集合
        释义字典：key为单词，value为释义
    """
    vocab_files = {
        vocab_type: skill_dir / VocabConstants.REFERENCES_DIRNAME / filename
        for vocab_type, filename in VocabConstants.VOCAB_FILENAMES.items()
    }
    
    vocab_dict = {}
    
    for vocab_type, file_path in vocab_files.items():
        words, _ = load_words_from_file(file_path)
        if words:
            vocab_dict[vocab_type] = words
            print(f"已加载 {len(words)} 个 {vocab_type.upper()} 词汇")
    
    # 加载合并的释义文件
    all_definitions = load_definitions(skill_dir)
    
    return vocab_dict, all_definitions


def get_highlight_words_by_level(
    min_level: int,
    vocab_dict: Dict[str, Set[str]]
) -> Set[str]:
    """
    根据难度等级获取需要高亮的词汇
    
    参数:
        min_level: 最低难度等级（包含该等级及更高等级的词汇）
        vocab_dict: 词汇字典
    
    返回:
        需要高亮的词汇集合
    """
    highlight_words = set()
    
    for vocab_type, level in VocabConstants.WORD_LEVELS.items():
        if level >= min_level and vocab_type in vocab_dict:
            highlight_words.update(vocab_dict[vocab_type])
    
    return highlight_words


def get_highlight_words_by_category(
    category: str,
    vocab_dict: Dict[str, Set[str]]
) -> Set[str]:
    """
    根据分类获取需要高亮的词汇
    
    参数:
        category: 分类名称（hot/college/abroad）
        vocab_dict: 词汇字典
    
    返回:
        需要高亮的词汇集合
    """
    highlight_words = set()
    
    if category not in VocabConstants.HIGHLIGHT_CATEGORIES:
        print(f"警告：未知的分类: {category}")
        return highlight_words
    
    vocab_types = VocabConstants.HIGHLIGHT_CATEGORIES[category]
    for vocab_type in vocab_types:
        if vocab_type in vocab_dict:
            highlight_words.update(vocab_dict[vocab_type])
    
    return highlight_words


def load_custom_words(words_input: str) -> Set[str]:
    """加载自定义高亮词汇"""
    words = set()
    
    if Path(words_input).exists():
        with open(words_input, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word and not word.startswith('#'):
                    words.add(word)
        print(f"从文件加载 {len(words)} 个自定义词汇: {words_input}")
    else:
        for word in words_input.split(','):
            word = word.strip().lower()
            if word:
                words.add(word)
        print(f"加载 {len(words)} 个自定义词汇")
    
    return words


def highlight_words_in_text(
    text: str,
    highlight_words: Set[str],
    text_color: str = PdfStyleConstants.DEFAULT_HIGHLIGHT_TEXT_COLOR
) -> Tuple[str, Set[str]]:
    """
    在文本中高亮指定单词
    
    返回:
        (处理后的文本, 本行发现的高亮单词集合)
    """
    if not highlight_words:
        return text, set()
    
    found_words = set()
    
    text = text.replace('&', '&amp;')
    text = text.replace('<br/>', '\n')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('\n', '<br/>')
    
    def replace_word(match):
        word = match.group(0)
        word_lower = word.lower()
        if word_lower in highlight_words:
            found_words.add(word_lower)
            return f'<font color="{text_color}">{word}</font>'
        return word
    
    result = re.sub(TextConstants.ENGLISH_WORD_PATTERN, replace_word, text)
    
    return result, found_words


def format_definition_list(
    words: List[str],
    definitions: Dict[str, str],
    text_color: str = PdfStyleConstants.DEFAULT_HIGHLIGHT_TEXT_COLOR
) -> str:
    """
    格式化单词释义列表
    
    参数:
        words: 单词列表
        definitions: 释义字典
        text_color: 高亮颜色
    
    返回:
        格式化后的HTML字符串（用于Paragraph渲染）
    """
    if not words:
        return ""
    
    items = []
    for word in words:
        defn = definitions.get(word, '')
        if defn:
            # 截取释义，避免过长
            if len(defn) > TextConstants.DEFINITION_MAX_LENGTH:
                defn = defn[:TextConstants.DEFINITION_MAX_LENGTH] + '...'
            items.append(f'<font color="{text_color}">{word}</font> {defn}')
        else:
            items.append(f'<font color="{text_color}">{word}</font>')
    
    return '；'.join(items)


def format_definition_for_canvas(
    words: List[str],
    definitions: Dict[str, str],
    text_color: tuple
) -> List[Tuple[str, bool]]:
    """
    格式化单词释义列表用于Canvas绘制
    
    参数:
        words: 单词列表
        definitions: 释义字典
        text_color: RGB颜色元组 (r, g, b)
    
    返回:
        列表，每个元素是 (文本, 是否高亮) 元组
    """
    if not words:
        return []
    
    items = []
    for word in words:
        defn = definitions.get(word, '')
        if defn:
            if len(defn) > TextConstants.DEFINITION_MAX_LENGTH:
                defn = defn[:TextConstants.DEFINITION_MAX_LENGTH] + '...'
            items.append((word, True))  # 单词需要高亮
            items.append((f' {defn}；', False))  # 释义不高亮
        else:
            items.append((word, True))
            items.append(('；', False))
    
    return items


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """
    将十六进制颜色转换为RGB元组（0-1范围）
    
    参数:
        hex_color: 十六进制颜色字符串，如 "#631511"
    
    返回:
        (r, g, b) 元组，每个值在0-1范围内
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def create_styles(font_name: str) -> dict:
    """创建文本样式"""
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=PdfStyleConstants.TITLE_FONT_SIZE,
        alignment=1,
        spaceAfter=PdfStyleConstants.TITLE_SPACE_AFTER,
        spaceBefore=PdfStyleConstants.TITLE_SPACE_BEFORE,
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=PdfStyleConstants.CELL_FONT_SIZE,
        leading=PdfStyleConstants.CELL_LEADING,
        alignment=0,
        wordWrap='CJK',
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=PdfStyleConstants.HEADER_FONT_SIZE,
        leading=PdfStyleConstants.HEADER_LEADING,
        alignment=1,
    )
    
    return {
        'title': title_style,
        'cell': cell_style,
        'header': header_style,
    }


def add_page_number(canvas_obj, doc, font_name: str = FontConstants.DEFAULT_FONT_NAME, total_pages: int = 0):
    """
    添加页码到PDF右上角
    格式: X 页 / 总 X 页
    """
    page_num = canvas_obj.getPageNumber()
    
    # 如果总页数为0，显示当前页号；否则显示完整信息
    if total_pages > 0:
        text = f"{page_num} 页 / 总 {total_pages} 页"
    else:
        text = f"{page_num} 页"
    
    canvas_obj.saveState()
    canvas_obj.setFont(font_name, PdfStyleConstants.PAGE_NUMBER_FONT_SIZE)
    
    # 计算右上角位置
    page_width = doc.pagesize[0]
    right_margin = PdfLayoutConstants.PAGE_NUMBER_RIGHT_MARGIN_MM * mm
    top_margin = PdfLayoutConstants.PAGE_NUMBER_TOP_MARGIN_MM * mm
    x = page_width - right_margin - canvas_obj.stringWidth(
        text, font_name, PdfStyleConstants.PAGE_NUMBER_FONT_SIZE
    )
    y = doc.pagesize[1] - top_margin
    
    canvas_obj.drawString(x, y, text)
    canvas_obj.restoreState()


def generate_pdf(
    output_path: str,
    aligned_subs: List[Tuple[Optional[SubtitleEntry], Optional[SubtitleEntry]]],
    title: str = CliConstants.DEFAULT_TITLE,
    font_path: Optional[str] = None,
    highlight_words: Optional[Set[str]] = None,
    definitions: Optional[Dict[str, str]] = None,
    highlight_text_color: str = PdfStyleConstants.DEFAULT_HIGHLIGHT_TEXT_COLOR,
    highlight_column: int = CliConstants.DEFAULT_HIGHLIGHT_COLUMN,
    lang1: str = None,
    lang2: str = None
):
    """
    生成PDF台词本
    
    高亮释义逻辑：
    1. 高亮单词用指定颜色标记
    2. 每页的高亮单词收集后，放在页面底部展示
    """
    font_name = FontConstants.DEFAULT_FONT_NAME
    if font_path and Path(font_path).exists():
        try:
            font_name = FontConstants.CHINESE_FONT_NAME
            register_chinese_font(font_path, font_name)
            print(f"使用指定字体: {font_path}")
        except Exception as e:
            print(f"警告：指定字体注册失败: {e}")
            font_name = _auto_detect_font()
    else:
        font_name = _auto_detect_font()
    
    page_size = get_page_size()
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=PdfLayoutConstants.PAGE_MARGIN_LEFT_MM * mm,
        rightMargin=PdfLayoutConstants.PAGE_MARGIN_RIGHT_MM * mm,
        topMargin=PdfLayoutConstants.PAGE_MARGIN_TOP_MM * mm,
        bottomMargin=PdfLayoutConstants.PAGE_MARGIN_BOTTOM_MM * mm,  # 释义现在是表格的一部分，减少下边距
    )
    
    styles = create_styles(font_name)
    
    # 创建释义样式
    base_styles = getSampleStyleSheet()
    defn_style = ParagraphStyle(
        'DefnStyle',
        parent=base_styles['Normal'],
        fontName=font_name,
        fontSize=PdfStyleConstants.DEFINITION_BASE_FONT_SIZE,
        leading=PdfStyleConstants.DEFINITION_BASE_LEADING,
        alignment=0,
        wordWrap='CJK',
    )
    
    story = []
    
    # 标题将在生成页面时添加，这里不再预先添加
    
    table_data = []
    
    # 检测语言并设置表格标题
    if lang1 is None or lang2 is None:
        # 自动检测语言
        all_text1 = " ".join([sub1.content for sub1, sub2 in aligned_subs if sub1])
        all_text2 = " ".join([sub2.content for sub1, sub2 in aligned_subs if sub2])
        if lang1 is None:
            lang1 = detect_language(all_text1)
        if lang2 is None:
            lang2 = detect_language(all_text2)
    
    lang1_name = get_language_name(lang1)
    lang2_name = get_language_name(lang2)
    
    # 创建时间轴样式（比正文小两个字号）
    timestamp_style = ParagraphStyle(
        'TimestampStyle',
        parent=styles['cell'],
        fontSize=PdfStyleConstants.TIMESTAMP_FONT_SIZE,  # 正文11，小两个字号
        textColor=colors.grey,
    )
    
    table_data.append([
        Paragraph("", styles['header']),  # 时间轴列标题为空
        Paragraph(lang1_name, styles['header']),
        Paragraph(lang2_name, styles['header']),
    ])
    
    # 收集所有高亮单词（按页分组）
    all_found_words = []  # 每个元素是该字幕行发现的单词
    seen_words = set()  # 全局已展示过释义的单词
    
    for sub1, sub2 in aligned_subs:
        text1 = sub1.content if sub1 else ""
        text2 = sub2.content if sub2 else ""
        
        # 时间轴（使用第一个字幕的开始时间）
        timestamp = ""
        if sub1:
            timestamp = format_timestamp(sub1.start_time)
        elif sub2:
            timestamp = format_timestamp(sub2.start_time)
        
        text1_raw = text1.replace('\n', '<br/>')
        text2_raw = text2.replace('\n', '<br/>')
        
        found_words_in_row = set()
        
        if highlight_words:
            if highlight_column in [CliConstants.HIGHLIGHT_COLUMN_LEFT, CliConstants.HIGHLIGHT_COLUMN_BOTH] and text1:
                text1_raw, found1 = highlight_words_in_text(text1_raw, highlight_words, highlight_text_color)
                found_words_in_row.update(found1)
            if highlight_column in [CliConstants.HIGHLIGHT_COLUMN_RIGHT, CliConstants.HIGHLIGHT_COLUMN_BOTH] and text2:
                text2_raw, found2 = highlight_words_in_text(text2_raw, highlight_words, highlight_text_color)
                found_words_in_row.update(found2)
        
        # 创建时间轴单元格
        timestamp_cell = Paragraph(timestamp, timestamp_style) if timestamp else Paragraph("", timestamp_style)
        cell1 = Paragraph(text1_raw, styles['cell']) if text1_raw else Paragraph("", styles['cell'])
        cell2 = Paragraph(text2_raw, styles['cell']) if text2_raw else Paragraph("", styles['cell'])
        
        table_data.append([timestamp_cell, cell1, cell2])
        
        # 记录该行发现的单词
        new_words = [w for w in found_words_in_row if w not in seen_words]
        for w in new_words:
            seen_words.add(w)
        all_found_words.append(new_words)
    
    # 创建释义样式
    defn_style = ParagraphStyle(
        'DefnStyle',
        parent=styles['cell'],
        fontSize=PdfStyleConstants.DEFINITION_FONT_SIZE,
        textColor=colors.grey,
    )
    
    # 计算页面可用尺寸（单位：points）
    available_width = page_size[0] - PdfLayoutConstants.TOTAL_HORIZONTAL_MARGIN_MM * mm  # 页面宽度 - 左右边距
    timestamp_width = PdfLayoutConstants.TIMESTAMP_COLUMN_WIDTH_MM * mm  # 时间轴列宽度
    col_width = (available_width - timestamp_width) / 2  # 字幕列宽度
    total_defn_width = available_width  # 释义行总宽度
    
    # 页面可用高度（单位：points）
    available_height0 = (
        page_size[1]
        - PdfLayoutConstants.PAGE_MARGIN_TOP_MM * mm
        - PdfLayoutConstants.PAGE_MARGIN_BOTTOM_MM * mm
        - PdfLayoutConstants.TITLE_BLOCK_RESERVED_MM * mm
    )  # A4高度 - 上边距 - 下边距 - 标题区域
    available_height = (
        page_size[1]
        - PdfLayoutConstants.PAGE_MARGIN_TOP_MM * mm
        - PdfLayoutConstants.PAGE_MARGIN_BOTTOM_MM * mm
    )  # A4高度 - 上边距 - 下边距 - 标题区域
    header_height = PdfLayoutConstants.HEADER_HEIGHT_MM * mm  # 表头高度
    row_padding = PdfLayoutConstants.ROW_PADDING_MM * mm  # 每行的上下padding总和（紧凑布局）
    safety_margin = PdfLayoutConstants.SAFETY_MARGIN_MM * mm  # 安全边距
    
    # 动态计算每页内容
    pages_data = []
    
    # 当前页状态
    current_page_rows = []  # 当前页的行数据
    current_page_words = []  # 当前页收集的单词
    current_height = 0  # 当前页已使用高度（不含表头和释义）
    
    def calculate_row_height(row_data):
        """计算单行的实际高度（返回points单位）"""
        max_height = 0
        for idx, cell in enumerate(row_data):
            if isinstance(cell, Paragraph):
                if idx == 0:  # 时间轴列
                    w = timestamp_width
                elif idx == 1:  # 字幕1列
                    w = col_width
                else:  # 字幕2列
                    w = col_width
                # wrap返回(实际宽度, 实际高度)，单位都是points
                _, h = cell.wrap(w, PdfLayoutConstants.WRAP_CALC_MAX_HEIGHT_MM * mm)
                max_height = max(max_height, h)
        # 加上padding（已经是points单位）
        return max_height + row_padding
    
    def calculate_defn_height(words):
        """计算释义行的实际高度（返回points单位）"""
        if not words or not definitions:
            return 0
        defn_text = format_definition_list(words, definitions, highlight_text_color)
        if not defn_text:
            return 0
        defn_para = Paragraph(defn_text, defn_style)
        _, h = defn_para.wrap(total_defn_width, PdfLayoutConstants.WRAP_CALC_MAX_HEIGHT_MM * mm)
        # 加上padding（已经是points单位）
        return h + row_padding
    
    # 处理表头
    header_row = [
        Paragraph("", styles['header']),
        Paragraph(lang1_name, styles['header']),
        Paragraph(lang2_name, styles['header']),
    ]
    
    # 遍历所有内容行，动态分页
    for i, row in enumerate(table_data):
        if i == 0:
            # 跳过原始表头，使用新的表头
            continue
        
        # 计算该行高度
        row_height = calculate_row_height(row)
        
        # 计算添加该行后的释义高度
        test_words = current_page_words + list(all_found_words[i - 1] if i - 1 < len(all_found_words) else [])
        defn_height = calculate_defn_height(test_words)
        
        # 计算总需要高度：表头 + 当前已用 + 该行 + 释义 + 安全边距
        total_needed = current_height + row_height + defn_height + safety_margin
        
        if total_needed <= (available_height0 if len(pages_data) == 0 else available_height) or len(current_page_rows) == 0:
            # 可以添加到当前页，或者当前页为空（强制添加至少一行）
            current_page_rows.append(row)
            current_page_words = test_words
            current_height += row_height
        else:
            # 需要换页，先保存当前页
            # print(current_height, header_height, defn_height, safety_margin, len(current_page_rows), "current_height")
            pages_data.append((current_page_rows, current_page_words, current_height))
            # 开始新页面
            current_page_rows = [row]
            current_page_words = list(all_found_words[i - 1] if i - 1 < len(all_found_words) else [])
            current_height = row_height
    
    # 保存最后一页
    if current_page_rows:
        pages_data.append((current_page_rows, current_page_words, current_height))
    
    # 为每页创建表格并添加到story
    for page_idx, (page_rows, page_words, page_height) in enumerate(pages_data):
        if page_idx > 0:
            story.append(PageBreak())
        
        if page_idx == 0:
            story.append(Paragraph(title, styles['title']))
            story.append(Spacer(1, PdfLayoutConstants.TITLE_SPACER_MM * mm))
        
        # 构建表格数据：表头 + 内容行 + 释义行
        page_table_data = [header_row]  # 添加表头
        page_table_data.extend(page_rows)  # 添加内容行
        
        # 添加释义行
        is_defn_row = False
        if page_words and definitions:
            defn_text = format_definition_list(page_words, definitions, highlight_text_color)
            if defn_text:
                defn_para = Paragraph(defn_text, defn_style)
                page_table_data.append([defn_para, "", ""])
                is_defn_row = True
        
        page_table = Table(page_table_data, colWidths=[timestamp_width, col_width, col_width])
        last_row_idx = len(page_table_data) - 1
        
        table_style = TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), PdfStyleConstants.HEADER_FONT_SIZE),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), PdfStyleConstants.TABLE_HEADER_BOTTOM_PADDING),
            ('TOPPADDING', (0, 0), (-1, 0), PdfStyleConstants.TABLE_HEADER_TOP_PADDING),
            
            # 内容区域样式
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), PdfStyleConstants.CELL_FONT_SIZE),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), PdfStyleConstants.TABLE_CELL_LEFT_PADDING),
            ('RIGHTPADDING', (0, 0), (-1, -1), PdfStyleConstants.TABLE_CELL_RIGHT_PADDING),
            ('BOTTOMPADDING', (0, 1), (-1, -1), PdfStyleConstants.TABLE_CELL_BOTTOM_PADDING),
            ('TOPPADDING', (0, 1), (-1, -1), PdfStyleConstants.TABLE_CELL_TOP_PADDING),
            
            # 边框样式
            ('LINEBELOW', (0, 0), (-1, 0), PdfStyleConstants.TABLE_HEADER_LINE_WIDTH, colors.black),
            ('LINEBELOW', (1, 1), (-1, -1), PdfStyleConstants.TABLE_CONTENT_LINE_WIDTH, colors.lightgrey),
        ])
        
        # 释义行特殊样式：合并整行（三列）
        if is_defn_row:
            table_style.add('BACKGROUND', (0, last_row_idx), (-1, last_row_idx), 
                          colors.Color(*PdfStyleConstants.DEFINITION_BACKGROUND_RGB))
            table_style.add('SPAN', (0, last_row_idx), (-1, last_row_idx))  # 合并整行
            table_style.add('ALIGN', (0, last_row_idx), (-1, last_row_idx), 'LEFT')
            table_style.add(
                'LINEBELOW',
                (0, last_row_idx),
                (-1, last_row_idx),
                PdfStyleConstants.TABLE_DEFINITION_LINE_WIDTH,
                colors.white
            )
        
        page_table.setStyle(table_style)
        story.append(page_table)
    
    total_pages = len(pages_data)
    
    # 添加页码回调
    def add_page_number_callback(canvas_obj, doc_obj):
        page_num = canvas_obj.getPageNumber()
        text = f"{page_num} 页 / 总 {total_pages} 页"
        canvas_obj.saveState()
        canvas_obj.setFont(font_name, PdfStyleConstants.PAGE_NUMBER_FONT_SIZE)
        page_width = doc_obj.pagesize[0]
        right_margin = PdfLayoutConstants.PAGE_NUMBER_RIGHT_MARGIN_MM * mm
        top_margin = PdfLayoutConstants.PAGE_NUMBER_TOP_MARGIN_MM * mm
        x = page_width - right_margin - canvas_obj.stringWidth(
            text, font_name, PdfStyleConstants.PAGE_NUMBER_FONT_SIZE
        )
        y = doc_obj.pagesize[1] - top_margin
        canvas_obj.drawString(x, y, text)
        canvas_obj.restoreState()
    
    doc.build(story, onFirstPage=add_page_number_callback, onLaterPages=add_page_number_callback)
    
    print(f"PDF生成完成: {output_path}")
    print(f"页面大小: A4纸张 ({PdfLayoutConstants.A4_WIDTH_MM}mm × {PdfLayoutConstants.A4_HEIGHT_MM}mm)")
    print(f"总页数: {total_pages}")
    if highlight_words:
        print(f"已高亮 {len(highlight_words)} 个单词")




def _auto_detect_font() -> str:
    """自动检测并注册中文字体，返回字体名称"""
    detected_font = find_chinese_font()
    
    if detected_font:
        try:
            font_name = FontConstants.CHINESE_FONT_NAME
            register_chinese_font(detected_font, font_name)
            print(f"自动检测到中文字体: {detected_font}")
            return font_name
        except Exception as e:
            print(f"警告：自动检测的字体注册失败: {e}")
            print("警告：未找到可用的中文字体，中文可能显示为方框")
            print("请通过 --font 参数指定中文字体文件路径")
            return FontConstants.DEFAULT_FONT_NAME
    else:
        print("警告：未在系统中检测到中文字体")
        print("请通过 --font 参数指定中文字体文件路径")
        print("推荐安装: 文泉驿微米黑 (wqy-microhei) 或 思源黑体 (Noto Sans CJK)")
        return FontConstants.DEFAULT_FONT_NAME


def get_skill_dir() -> Path:
    """获取当前脚本所在的Skill目录"""
    return Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description='双语字幕转PDF台词本')
    
    parser.add_argument('--subtitle1', '-s1', help='字幕文件1路径（左列）')
    parser.add_argument('--subtitle2', '-s2', help='字幕文件2路径（右列）')
    parser.add_argument('--single-file', '-sf', help='单文件双语模式')
    
    parser.add_argument('--output', '-o', required=True, help='输出PDF文件路径')
    parser.add_argument('--title', '-t', default=CliConstants.DEFAULT_TITLE, help='台词本标题')
    parser.add_argument('--font', '-f', help='自定义字体路径（支持中文）')
    
    # 单词高亮参数 - 按难度等级
    parser.add_argument('--highlight-cet4', action='store_true', 
                        help='高亮四级及以上词汇')
    parser.add_argument('--highlight-cet6', action='store_true', 
                        help='高亮六级及以上词汇')
    parser.add_argument('--highlight-tem4', action='store_true', 
                        help='高亮专四及以上词汇')
    parser.add_argument('--highlight-tem8', action='store_true', 
                        help='高亮专八及以上词汇')
    parser.add_argument('--highlight-kaoyan', action='store_true', 
                        help='高亮考研及以上词汇')
    parser.add_argument('--highlight-ielts', action='store_true', 
                        help='高亮雅思及以上词汇')
    parser.add_argument('--highlight-toefl', action='store_true', 
                        help='高亮托福及以上词汇')
    parser.add_argument('--highlight-gmat', action='store_true', 
                        help='高亮GMAT及以上词汇')
    parser.add_argument('--highlight-gre', action='store_true', 
                        help='高亮GRE及以上词汇')
    parser.add_argument('--highlight-sat', action='store_true', 
                        help='高亮SAT词汇')
    
    # 单词高亮参数 - 按分类
    parser.add_argument('--highlight-hot', action='store_true', 
                        help='高亮热门单词（四级、六级、考研）')
    parser.add_argument('--highlight-college', action='store_true', 
                        help='高亮大学单词（四级、六级、考研、专四、专八）')
    parser.add_argument('--highlight-abroad', action='store_true', 
                        help='高亮出国单词（雅思、托福、GMAT、GRE、SAT）')
    
    parser.add_argument('--highlight-words', '-hw', 
                        help='自定义高亮词汇（文件路径或逗号分隔的词汇）')
    
    parser.add_argument('--highlight-color', '-hc', default=CliConstants.DEFAULT_HIGHLIGHT_COLOR,
                        help=f'高亮文字颜色（默认: {CliConstants.DEFAULT_HIGHLIGHT_COLOR} 深红色）')
    parser.add_argument('--highlight-column', '-hcol', type=int,
                        default=CliConstants.DEFAULT_HIGHLIGHT_COLUMN,
                        choices=CliConstants.HIGHLIGHT_COLUMN_CHOICES,
                        help='高亮列: 1=左列, 2=右列, 3=两列都高亮（默认: 2）')
    
    args = parser.parse_args()
    
    # 解析字幕
    if args.single_file:
        print("单文件模式暂不支持，请提供两个字幕文件")
        sys.exit(1)
    else:
        if not args.subtitle1 or not args.subtitle2:
            print("错误：请提供两个字幕文件路径（--subtitle1 和 --subtitle2）")
            sys.exit(1)
        
        print(f"解析字幕文件1: {args.subtitle1}")
        subs1 = parse_subtitle(args.subtitle1)
        print(f"  共 {len(subs1)} 条字幕")
        
        print(f"解析字幕文件2: {args.subtitle2}")
        subs2 = parse_subtitle(args.subtitle2)
        print(f"  共 {len(subs2)} 条字幕")
        
        print("对齐字幕...")
        aligned = align_subtitles(subs1, subs2)
        print(f"  共 {len(aligned)} 对字幕")
    
    # 加载高亮词汇
    highlight_words = set()
    definitions = {}
    skill_dir = get_skill_dir()
    vocab_dict = None
    
    # 确定最低难度等级
    min_level = 0
    
    if args.highlight_cet4:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['cet4'])
    if args.highlight_cet6:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['cet6'])
    if args.highlight_tem4:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['tem4'])
    if args.highlight_tem8:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['tem8'])
    if args.highlight_kaoyan:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['kaoyan'])
    if args.highlight_ielts:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['ielts'])
    if args.highlight_toefl:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['toefl'])
    if args.highlight_gmat:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['gmat'])
    if args.highlight_gre:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['gre'])
    if args.highlight_sat:
        min_level = max(min_level, VocabConstants.WORD_LEVELS['sat'])
    
    # 按难度等级高亮
    if min_level > 0:
        vocab_dict, definitions = load_all_vocab_files(skill_dir)
        highlight_words = get_highlight_words_by_level(min_level, vocab_dict)
        
        # 显示高亮范围
        print(f"高亮等级: {VocabConstants.LEVEL_DISPLAY_NAMES.get(min_level, '未知')} 及以上")
    
    # 按分类高亮
    if args.highlight_hot or args.highlight_college or args.highlight_abroad:
        if vocab_dict is None:
            vocab_dict, definitions = load_all_vocab_files(skill_dir)
        
        if args.highlight_hot:
            words = get_highlight_words_by_category(VocabConstants.CATEGORY_HOT, vocab_dict)
            highlight_words.update(words)
            print(f"高亮分类: 热门单词 ({len(words)} 个)")
        
        if args.highlight_college:
            words = get_highlight_words_by_category(VocabConstants.CATEGORY_COLLEGE, vocab_dict)
            highlight_words.update(words)
            print(f"高亮分类: 大学单词 ({len(words)} 个)")
        
        if args.highlight_abroad:
            words = get_highlight_words_by_category(VocabConstants.CATEGORY_ABROAD, vocab_dict)
            highlight_words.update(words)
            print(f"高亮分类: 出国单词 ({len(words)} 个)")
    
    if args.highlight_words:
        custom_words = load_custom_words(args.highlight_words)
        highlight_words.update(custom_words)
    
    # 生成PDF
    print(f"生成PDF: {args.output}")
    generate_pdf(
        args.output, 
        aligned, 
        args.title, 
        args.font,
        highlight_words if highlight_words else None,
        definitions if highlight_words else None,
        args.highlight_color,
        args.highlight_column
    )
    
    output_path = Path(args.output)
    if output_path.exists():
        size_kb = output_path.stat().st_size / 1024
        print(f"文件大小: {size_kb:.2f} KB")


if __name__ == '__main__':
    main()
