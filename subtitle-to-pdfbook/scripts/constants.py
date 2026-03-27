#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bilingual_subtitle_to_pdf.py 的配置常量。"""


class LanguageConstants:
    """语言检测与语言名称映射常量。"""

    DEFAULT_LANG_CODE = "en"

    LANGUAGE_NAMES = {
        "zh": "中文",
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "ja": "日本語",
        "ko": "한국어",
        "pt": "Português",
        "ru": "Русский",
        "it": "Italiano",
        "ar": "العربية",
        "th": "ไทย",
        "vi": "Tiếng Việt",
        "nl": "Nederlands",
        "pl": "Polski",
        "tr": "Türkçe",
        "id": "Bahasa Indonesia",
        "ms": "Bahasa Melayu",
    }

    SCRIPT_PATTERNS = {
        "chinese": r"[\u4e00-\u9fff]",
        "japanese": r"[\u3040-\u309f\u30a0-\u30ff]",
        "korean": r"[\uac00-\ud7af]",
        "arabic": r"[\u0600-\u06ff]",
        "thai": r"[\u0e00-\u0e7f]",
        "cyrillic": r"[\u0400-\u04ff]",
    }

    SCRIPT_RATIO_THRESHOLDS = {
        "zh": 0.1,
        "ja": 0.05,
        "ko": 0.05,
        "ar": 0.05,
        "th": 0.05,
        "ru": 0.1,
    }

    LATIN_FEATURE_WORDS = {
        "en": (
            "the", "is", "are", "was", "were", "have", "has", "had", "will", "would",
            "can", "could", "should", "may", "might", "must", "this", "that", "these",
            "those", "what", "which", "who", "when", "where", "why", "how", "not", "but",
        ),
        "es": ("el", "los", "las", "que", "y", "una", "por", "con", "para", "muy", "tengo", "tiene"),
        "fr": ("le", "les", "du", "des", "est", "une", "dans", "avec", "vous", "nous", "je", "tu"),
        "de": ("der", "die", "das", "und", "ist", "eine", "den", "von", "mit", "für", "ich", "du"),
        "pt": ("os", "que", "do", "da", "em", "uma", "para", "com", "você", "não", "sou"),
        "it": ("il", "lo", "di", "che", "una", "per", "con", "sono", "essere", "hanno"),
    }

    LATIN_MIN_SCORE = 2


class VocabConstants:
    """词汇等级、分类与文件映射常量。"""

    REFERENCES_DIRNAME = "references"
    DEFINITIONS_FILENAME = "all_words_with_def.txt"

    CATEGORY_HOT = "hot"
    CATEGORY_COLLEGE = "college"
    CATEGORY_ABROAD = "abroad"

    WORD_LEVELS = {
        "cet4": 1,
        "cet6": 2,
        "tem4": 2,
        "tem8": 3,
        "kaoyan": 3,
        "ielts": 4,
        "toefl": 4,
        "gmat": 5,
        "gre": 5,
        "sat": 5,
    }

    HIGHLIGHT_CATEGORIES = {
        CATEGORY_HOT: ["cet4", "cet6", "kaoyan"],
        CATEGORY_COLLEGE: ["cet4", "cet6", "kaoyan", "tem4", "tem8"],
        CATEGORY_ABROAD: ["ielts", "toefl", "gmat", "gre", "sat"],
    }

    VOCAB_FILENAMES = {
        "cet4": "cet4_words.txt",
        "cet6": "cet6_words.txt",
        "tem4": "tem4_words.txt",
        "tem8": "tem8_words.txt",
        "kaoyan": "kaoyan_words.txt",
        "ielts": "ielts_words.txt",
        "toefl": "toefl_words.txt",
        "gmat": "gmat_words.txt",
        "gre": "gre_words.txt",
        "sat": "sat_words.txt",
    }

    LEVEL_DISPLAY_NAMES = {
        1: "四级",
        2: "六级/专四",
        3: "专八/考研",
        4: "雅思/托福",
        5: "GMAT/GRE/SAT",
    }


class TextConstants:
    """文本处理相关常量。"""

    HTML_STYLE_TAG_PATTERN = r"</?[iIbBuU]>"
    HTML_FONT_TAG_PATTERN = r"</?[fF][oO][nN][tT][^>]*>"
    ASS_STYLE_TAG_PATTERN = r"\{\\[^}]*\}"
    ASS_INLINE_TAG_PATTERN = r"\{[^}]*\}"
    VTT_COLOR_TAG_PATTERN = r"</?c(\.[^>]*)?>"
    ASS_K_TAG_PATTERN = r"\{\\[kK][^}]*\}"
    WHITESPACE_PATTERN = r"\s+"

    ENGLISH_WORD_PATTERN = r"[a-zA-Z]+(?:'[a-zA-Z]+)?"
    DEFINITION_MAX_LENGTH = 30


class FontConstants:
    """字体检测和注册相关常量。"""

    DEFAULT_FONT_NAME = "Helvetica"
    CHINESE_FONT_NAME = "ChineseFont"
    TTC_SUBFONT_INDEX = 0

    SYSTEM_FONT_CANDIDATES = {
        "Linux": [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/source-han/SourceHanSansCN-Regular.ttf",
            "/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.ttf",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
        ],
        "Darwin": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ],
        "Windows": [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simkai.ttf",
        ],
    }

    FC_LIST_CMD = ["fc-list", ":lang=zh", "file"]
    FC_LIST_TIMEOUT_SECONDS = 5


class PdfLayoutConstants:
    """PDF 布局尺寸相关常量（单位在使用处换算）。"""

    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297

    PAGE_MARGIN_LEFT_MM = 20
    PAGE_MARGIN_RIGHT_MM = 20
    PAGE_MARGIN_TOP_MM = 15
    PAGE_MARGIN_BOTTOM_MM = 5

    PAGE_NUMBER_RIGHT_MARGIN_MM = 20
    PAGE_NUMBER_TOP_MARGIN_MM = 15

    TITLE_SPACER_MM = 10
    TITLE_BLOCK_RESERVED_MM = 35

    TIMESTAMP_COLUMN_WIDTH_MM = 15
    TOTAL_HORIZONTAL_MARGIN_MM = 40

    HEADER_HEIGHT_MM = 8
    ROW_PADDING_MM = 1.5
    SAFETY_MARGIN_MM = 4

    WRAP_CALC_MAX_HEIGHT_MM = 1000


class PdfStyleConstants:
    """PDF 样式和默认视觉参数。"""

    DEFAULT_HIGHLIGHT_TEXT_COLOR = "#631511"

    TITLE_FONT_SIZE = 24
    TITLE_SPACE_AFTER = 20
    TITLE_SPACE_BEFORE = 10

    CELL_FONT_SIZE = 11
    CELL_LEADING = 14

    HEADER_FONT_SIZE = 12
    HEADER_LEADING = 15

    TIMESTAMP_FONT_SIZE = 9
    DEFINITION_FONT_SIZE = 9
    DEFINITION_BASE_FONT_SIZE = 10
    DEFINITION_BASE_LEADING = 14
    PAGE_NUMBER_FONT_SIZE = 10

    TABLE_HEADER_BOTTOM_PADDING = 2
    TABLE_HEADER_TOP_PADDING = 2

    TABLE_CELL_LEFT_PADDING = 4
    TABLE_CELL_RIGHT_PADDING = 4
    TABLE_CELL_BOTTOM_PADDING = 1
    TABLE_CELL_TOP_PADDING = 1

    TABLE_HEADER_LINE_WIDTH = 1
    TABLE_CONTENT_LINE_WIDTH = 0.5
    TABLE_DEFINITION_LINE_WIDTH = 0

    DEFINITION_BACKGROUND_RGB = (0.95, 0.95, 0.95)


class CliConstants:
    """CLI 默认值与约束常量。"""

    DEFAULT_TITLE = "双语台词本"
    DEFAULT_HIGHLIGHT_COLOR = PdfStyleConstants.DEFAULT_HIGHLIGHT_TEXT_COLOR
    HIGHLIGHT_COLUMN_LEFT = 1
    HIGHLIGHT_COLUMN_RIGHT = 2
    HIGHLIGHT_COLUMN_BOTH = 3
    DEFAULT_HIGHLIGHT_COLUMN = 2
    HIGHLIGHT_COLUMN_CHOICES = (1, 2, 3)
