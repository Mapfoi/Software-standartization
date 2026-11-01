# -*- coding: utf-8 -*-
"""Сборка отчёта lab2б по образцу lab2a."""

import os
import shutil
from copy import deepcopy

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, Inches
from docx.oxml import OxmlElement

BASE = r"D:\Projects\Software-standartization\Lab 2b Boundary value metric"
LAB2 = r"D:\Projects\Software-standartization\Lab 2 Gilb and McCabe metrics"

TEMPLATE = next(f for f in os.listdir(BASE) if f.endswith(".docx") and "lab2a" in f.lower())
OUT_NAME = "Отчет_Вишневский_Ешманский_lab2b.docx"

CODE = r'''package main

import "fmt"

func main() {
	x := 5
	icount := 0

	if x > 10 {
		fmt.Println("gt10")
	} else if x > 0 {
		for i := 0; i < 12; i++ {
			if i == 1 {
				fmt.Println("deep")
			} else {
				switch i {
					case 2:
						icount := 1
					case 5:
						icount := 3
					case 11:
						icount := 6
				}
			}
		}
	} else {
		fmt.Println("other")
	}

	n := 0
	for n < 2 {
		n++
	}

	for {
		break
	}

	for range []int{1, 2} {
		fmt.Println("range")
	}

	switch x {
	case 5:
		fmt.Println("five")
	case 3:
		fmt.Println("three")
		if x > icount {
			fmt.Println("Bigger")
		}
	default:
		fmt.Println("other")
	}
}'''


def set_run_font(run, name="Times New Roman", size=14, bold=None):
    run.font.name = name
    run._element.get_or_add_rPr()
    rFonts = run._element.rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:cs"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def add_para(doc, text="", align=None, bold=False, size=14, space_after=0, space_before=0):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.line_spacing = 1.0
    if text:
        run = p.add_run(text)
        set_run_font(run, size=size, bold=bold)
    return p


def add_code_lines(doc, code):
    for line in code.splitlines():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        # replace tabs with spaces for Word
        run = p.add_run(line.replace("\t", "    "))
        set_run_font(run, name="Courier New", size=11)


def set_cell_text(cell, text, bold=False, size=11, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)


def shade_header_row(row):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "D9E2F3")
        shd.set(qn("w:val"), "clear")
        tcPr.append(shd)


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        set_cell_text(table.rows[0].cells[j], h, bold=True, size=10, center=True)
    shade_header_row(table.rows[0])
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            set_cell_text(table.rows[i + 1].cells[j], str(val), size=9, center=(j > 0))
    if col_widths:
        for row in table.rows:
            for j, w in enumerate(col_widths):
                row.cells[j].width = Cm(w)
    return table


def replace_paragraph_text(paragraph, new_text, bold=None):
    """Заменить текст параграфа, сохранив стиль первого run по возможности."""
    if paragraph.runs:
        first = paragraph.runs[0]
        font_name = first.font.name
        font_size = first.font.size
        was_bold = first.bold if bold is None else bold
        for r in paragraph.runs:
            r.text = ""
        first.text = new_text
        set_run_font(
            first,
            name=font_name or "Times New Roman",
            size=(font_size.pt if font_size else 14),
            bold=was_bold,
        )
    else:
        run = paragraph.add_run(new_text)
        set_run_font(run, bold=bold)


def patch_title_page(doc):
    """Скорректировать номер работы и тему на титульнике."""
    for p in doc.paragraphs:
        t = p.text
        if "по лабораторной работе" in t:
            replace_paragraph_text(p, "  по лабораторной работе №2б")
        elif t.startswith("Тема работы:"):
            replace_paragraph_text(
                p,
                "Тема работы: Метрика граничных значений",
            )


def clear_body_after_title(doc):
    """Удалить всё после 'Минск 2026', оставив sectPr."""
    body = doc.element.body
    keep_until = None
    for child in list(body):
        if child.tag == qn("w:p"):
            texts = [t.text or "" for t in child.iter(qn("w:t"))]
            full = "".join(texts)
            if full.strip().startswith("Минск"):
                keep_until = child
    if keep_until is None:
        raise RuntimeError("Title end (Минск) not found")

    seen = False
    for child in list(body):
        if child is keep_until:
            seen = True
            continue
        if not seen:
            continue
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)

def insert_page_break(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._element.append(br)


def main():
    src = os.path.join(BASE, TEMPLATE)
    dst = os.path.join(BASE, OUT_NAME)
    shutil.copy2(src, dst)

    doc = Document(dst)
    patch_title_page(doc)
    clear_body_after_title(doc)

    # --- Задание ---
    insert_page_break(doc)
    add_para(doc, "Задание", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, space_after=8)

    add_para(
        doc,
        "Составление отчета для расчета метрики граничных значений",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        bold=True,
        size=14,
        space_after=6,
    )
    add_para(
        doc,
        "Для расчета метрики необходимо изобразить код анализируемой программы в виде подробной "
        "схемы алгоритма по ГОСТ 19.701-90. Каждому блоку схемы должен соответствовать один оператор "
        "языка программирования. Оператор множественного выбора изображается в виде вложенных "
        "операторов условия. На основании граф-схемы рассчитать абсолютную Sa и относительную So "
        "граничную сложность программы. Результаты представить в виде таблиц.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=8,
    )
    add_para(
        doc,
        "Анализируемый язык программирования – Go.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=12,
    )

    # --- Код ---
    add_para(doc, "Код анализируемой программы:", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=8)
    add_code_lines(doc, CODE)

    # --- Схемы ---
    insert_page_break(doc)
    add_para(
        doc,
        "Схема алгоритма по ГОСТ 19.701-90",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        size=14,
        space_after=8,
    )

    img1 = os.path.join(LAB2, "flowchart_part1_x3.png")
    img2_photo = os.path.join(BASE, "photo_2_2026-10-15_16-31-58.jpg")
    img2_lab = os.path.join(LAB2, "flowchart_part2_x3.png")

    if os.path.isfile(img1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(img1, width=Cm(14))
        add_para(doc, "Рисунок 1 – схема алгоритма (часть 1)", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=10)

    # Для части 2 предпочитаем фото, где for{} — ромб и есть x > icount
    img2 = img2_photo if os.path.isfile(img2_photo) else img2_lab
    if os.path.isfile(img2):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(img2, width=Cm(12))
        add_para(doc, "Рисунок 2 – схема алгоритма (часть 2)", align=WD_ALIGN_PARAGRAPH.CENTER, size=12, space_after=10)

    add_para(
        doc,
        "Замечание. Блок for { } на схеме изображён ромбом, однако из него выходит только одна стрелка "
        "(к оператору break): условия ветвления нет. По определению метрики граничных значений вершина "
        "с положительной степенью ≤ 1 является принимающей. Поэтому for { } учтён как принимающая "
        "вершина со скорректированной сложностью 1, а не как вершина выбора.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=12,
    )

    # --- Нумерация ---
    insert_page_break(doc)
    add_para(
        doc,
        "Нумерация вершин граф-схемы",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        size=14,
        space_after=8,
    )
    add_para(
        doc,
        "Каждому оператору соответствует один блок. Оператор switch развёрнут во вложенные операторы "
        "условия. Цикл for i := 0; i < 12; i++ представлен блоками инициализации, условия и инкремента. "
        "Цикл for range — инициализацией и условием range. Всего вершин ν = 34.",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=8,
    )

    vertices = [
        ("1", "Начало", "принимающая"),
        ("2", "x := 5", "принимающая"),
        ("3", "icount := 0", "принимающая"),
        ("4", "x > 10", "выбор"),
        ("5", 'Println("gt10")', "принимающая"),
        ("6", "x > 0", "выбор"),
        ("7", "for i := 0", "принимающая"),
        ("8", "i < 12", "выбор"),
        ("9", "i == 1", "выбор"),
        ("10", 'Println("deep")', "принимающая"),
        ("11", "i == 2", "выбор"),
        ("12", "icount := 1", "принимающая"),
        ("13", "i == 5", "выбор"),
        ("14", "icount := 3", "принимающая"),
        ("15", "i == 11", "выбор"),
        ("16", "icount := 6", "принимающая"),
        ("17", "i++", "принимающая"),
        ("18", 'Println("other") (else x > 0)', "принимающая"),
        ("19", "n := 0", "принимающая"),
        ("20", "n < 2", "выбор"),
        ("21", "n++", "принимающая"),
        ("22", "for { }", "принимающая (одна исходящая дуга)"),
        ("23", "break", "принимающая"),
        ("24", "for range [1, 2]", "принимающая"),
        ("25", "range", "выбор"),
        ("26", 'Println("range")', "принимающая"),
        ("27", "x == 5", "выбор"),
        ("28", 'Println("five")', "принимающая"),
        ("29", "x == 3", "выбор"),
        ("30", 'Println("three")', "принимающая"),
        ("31", "x > icount", "выбор"),
        ("32", 'Println("Bigger")', "принимающая"),
        ("33", 'Println("other") (default)', "принимающая"),
        ("34", "Конец", "конечная (C = 0)"),
    ]
    add_table(doc, ["№", "Блок", "Тип"], vertices, col_widths=[1.5, 9, 5.5])
    add_para(doc, "", space_after=6)
    add_para(
        doc,
        "Вершины выбора: 4, 6, 8, 9, 11, 13, 15, 20, 25, 27, 29, 31 (12 шт.).",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=12,
    )

    # --- Таблица подграфов ---
    insert_page_break(doc)
    add_para(
        doc,
        "Результаты расчета метрики граничных значений",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        size=14,
        space_after=8,
    )
    add_para(
        doc,
        "Таблица 1 – Свойства подграфов программы",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=12,
        space_after=6,
    )

    # Compact subgraph table: property rows × choice columns would be wide.
    # Present as rows per choice vertex (clearer in Word).
    subgraph_rows = [
        ("4", "5, 6", "15", "5–18", "19"),
        ("6", "7, 18", "13", "7–18", "19"),
        ("8", "9, 19", "11", "8–17", "19"),
        ("9", "10, 11", "8", "10–16", "17"),
        ("11", "12, 13", "6", "12–16", "17"),
        ("13", "14, 15", "4", "14–16", "17"),
        ("15", "16, 17", "2", "16", "17"),
        ("20", "21, 22", "3", "20, 21", "22"),
        ("25", "26, 27", "3", "25, 26", "27"),
        ("27", "28, 29", "7", "28–33", "34"),
        ("29", "30, 33", "5", "30–33", "34"),
        ("31", "32, 34", "2", "32", "34"),
    ]
    add_table(
        doc,
        [
            "Вершина выбора",
            "Вершины перехода",
            "Скорр. сложность",
            "Вершины подграфа",
            "Нижняя граница",
        ],
        subgraph_rows,
        col_widths=[3, 3.5, 3, 3.5, 3],
    )
    add_para(doc, "", space_after=8)

    add_para(
        doc,
        "Таблица 2 – Скорректированные сложности вершин графа программы",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=12,
        space_after=6,
    )

    # Two tables for readability: 1-17 and 18-34
    c1 = [
        ("1", "1"), ("2", "1"), ("3", "1"), ("4", "15"), ("5", "1"),
        ("6", "13"), ("7", "1"), ("8", "11"), ("9", "8"), ("10", "1"),
        ("11", "6"), ("12", "1"), ("13", "4"), ("14", "1"), ("15", "2"),
        ("16", "1"), ("17", "1"),
    ]
    c2 = [
        ("18", "1"), ("19", "1"), ("20", "3"), ("21", "1"), ("22", "1"),
        ("23", "1"), ("24", "1"), ("25", "3"), ("26", "1"), ("27", "7"),
        ("28", "1"), ("29", "5"), ("30", "1"), ("31", "2"), ("32", "1"),
        ("33", "1"), ("34", "0"),
    ]
    add_table(doc, ["№ вершины", "Скорректированная сложность"], c1, col_widths=[4, 8])
    add_para(doc, "", space_after=4)
    add_table(doc, ["№ вершины", "Скорректированная сложность"], c2, col_widths=[4, 8])

    add_para(doc, "", space_after=10)
    add_para(
        doc,
        "Абсолютная граничная сложность программы:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=4,
    )
    add_para(
        doc,
        "Sa = 15+13+11+8+6+4+2+3+3+7+5+2 + 21·1 + 0 = 100",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        size=14,
        space_after=10,
    )
    add_para(
        doc,
        "Относительная граничная сложность программы:",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        size=14,
        space_after=4,
    )
    add_para(
        doc,
        "So = 1 − (ν − 1) / Sa = 1 − (34 − 1) / 100 = 1 − 0,33 = 0,67",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        bold=True,
        size=14,
        space_after=12,
    )

    add_para(doc, "Итоговые значения", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, space_after=6)
    add_table(
        doc,
        ["Метрика", "Значение"],
        [
            ("Число вершин ν", "34"),
            ("Число вершин выбора", "12"),
            ("Абсолютная граничная сложность Sa", "100"),
            ("Относительная граничная сложность So", "0,67"),
        ],
        col_widths=[10, 4],
    )

    doc.save(dst)
    print("Saved:", dst)


if __name__ == "__main__":
    main()
