# -*- coding: utf-8 -*-
"""
«QALBGA YETIB BORADIGAN SO‘ZLAR»
Kitobning asosiy birlashtiruvchi ma'lumotlar moduli
"""

from book_data import BOOK_INFO, AUTHOR_NOTE, FINAL_LETTER, LIFE_CONCLUSIONS
from chapters_part1 import CHAPTERS_1_TO_5
from chapters_part2 import CHAPTERS_6_TO_10
from chapters_part3 import CHAPTERS_11_TO_15
from chapters_part4 import CHAPTERS_16_TO_20
from quotes_100 import TOP_100_QUOTES

ALL_CHAPTERS = (
    CHAPTERS_1_TO_5 +
    CHAPTERS_6_TO_10 +
    CHAPTERS_11_TO_15 +
    CHAPTERS_16_TO_20
)

def get_chapter(chapter_id: int):
    for ch in ALL_CHAPTERS:
        if ch["id"] == chapter_id:
            return ch
    return None

def get_all_chapters():
    return ALL_CHAPTERS

def get_quotes():
    return TOP_100_QUOTES
