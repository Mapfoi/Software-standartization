# -*- coding: utf-8 -*-
"""
Вернуть таблицы расчёта в прежней форме и убрать first-line indent
из docDefaults (w:ind w:firstLine=\"709\"), из‑за которого текст
в узких ячейках «уезжал» вправо и отступ нельзя было стереть вручную.
"""

import os
import shutil

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

BASE = r"D:\Projects\Software-standartization\Lab 2b Boundary value metric"
DOCX = next(
    f
    for f in os.listdir(BASE)
    if f.endswith(".docx")
    and "lab2b" in f.lower()
    and not f.startswith("~")
    and "backup" not in f.lower()
)


def set_run_font(run, name="Times New Roman", size=10, bold=None):
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:cs"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def clear_cell_paragraphs(cell):
    """Очистить ячейку, оставив один пустой абзац."""
    tc = cell._tc
    for child in list(tc):
        if child.tag == qn("w:p"):
            tc.remove(child)
    p = OxmlElement("w:p")
    tc.append(p)
    return p


def set_cell(cell, text, bold=False, size=10, center=True):
    """Записать текст в ячейку с явным сбросом first-line indent."""
    p = clear_cell_paragraphs(cell)

    pPr = OxmlElement("w:pPr")

    # Критично: перебить docDefaults firstLine=709
    ind = OxmlElement("w:ind")
    ind.set(qn("w:firstLine"), "0")
    ind.set(qn("w:left"), "0")
    ind.set(qn("w:right"), "0")
    pPr.append(ind)

    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    pPr.append(spacing)

    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center" if center else "left")
    pPr.append(jc)

    p.append(pPr)

    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")
    rPr.append(rFonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(szCs)
    if bold:
        rPr.append(OxmlElement("w:b"))
    r.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = str(text)
    r.append(t)
    p.append(r)


def shade_cell(cell, fill="D9E2F3"):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:shd")):
        tcPr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def set_table_full_width(table):
    tblPr = table._tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        table._tbl.insert(0, tblPr)
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:w"), "5000")
    tblW.set(qn("w:type"), "pct")
    tblPr.append(tblW)


def make_para(text="", center=False, bold=False, size=12, space_after=6, space_before=6):
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    # тоже без красной строки
    ind = OxmlElement("w:ind")
    ind.set(qn("w:firstLine"), "0")
    pPr.append(ind)
    if center:
        jc = OxmlElement("w:jc")
        jc.set(qn("w:val"), "center")
        pPr.append(jc)
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:after"), str(int(space_after * 20)))
    spacing.set(qn("w:before"), str(int(space_before * 20)))
    pPr.append(spacing)
    p.append(pPr)
    if text:
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(qn("w:ascii"), "Times New Roman")
        rFonts.set(qn("w:hAnsi"), "Times New Roman")
        rFonts.set(qn("w:cs"), "Times New Roman")
        rPr.append(rFonts)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(int(size * 2)))
        rPr.append(sz)
        if bold:
            rPr.append(OxmlElement("w:b"))
        r.append(rPr)
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        p.append(r)
    return p


def create_filled_table(doc, matrix, first_col_left=False):
    n_rows = len(matrix)
    n_cols = len(matrix[0])
    table = doc.add_table(rows=n_rows, cols=n_cols)
    table.style = "Table Grid"
    set_table_full_width(table)

    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            is_header = i == 0
            left = first_col_left and j == 0 and not is_header
            set_cell(
                table.rows[i].cells[j],
                val,
                bold=is_header or (first_col_left and j == 0),
                size=10,
                center=not left,
            )
            if is_header:
                shade_cell(table.rows[i].cells[j])
    return table


def fix_existing_table_indents(table):
    """Сбросить first-line indent во всех ячейках существующей таблицы."""
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                pPr = p._element.get_or_add_pPr()
                for old in pPr.findall(qn("w:ind")):
                    pPr.remove(old)
                ind = OxmlElement("w:ind")
                ind.set(qn("w:firstLine"), "0")
                ind.set(qn("w:left"), "0")
                ind.set(qn("w:right"), "0")
                pPr.insert(0, ind)


def main():
    src = os.path.join(BASE, DOCX)
    work = os.path.join(BASE, "_lab2b_fix_tmp.docx")
    shutil.copy2(src, work)
    doc = Document(work)
    body = doc.element.body

    # 1) В первой (нормальной по форме) таблице тоже сбросить отступ на всякий случай
    if doc.tables:
        fix_existing_table_indents(doc.tables[0])

    # 2) Найти якоря
    results_p = None
    abs_p = None
    itogo_p = None
    for child in list(body):
        if child.tag != qn("w:p"):
            continue
        text = "".join(t.text or "" for t in child.iter(qn("w:t")))
        if text.startswith("Результаты расчета"):
            results_p = child
        if text.strip().startswith("Абсолютная граничная"):
            abs_p = child
        if text.strip() == "Итоговые значения":
            itogo_p = child

    if results_p is None or abs_p is None:
        raise RuntimeError("Anchors not found")

    # 3) Удалить всё между «Результаты...» и «Абсолютная...»
    to_delete = []
    seen = False
    for child in list(body):
        if child is results_p:
            seen = True
            continue
        if child is abs_p:
            break
        if seen:
            to_delete.append(child)
    for el in to_delete:
        el.getparent().remove(el)

    # 4) Удалить старую итоговую таблицу после «Итоговые значения»
    if itogo_p is not None:
        removing = False
        for child in list(body):
            if child is itogo_p:
                removing = True
                continue
            if not removing:
                continue
            if child.tag == qn("w:sectPr"):
                break
            if child.tag == qn("w:tbl"):
                body.remove(child)
            elif child.tag == qn("w:p"):
                text = "".join(t.text or "" for t in child.iter(qn("w:t")))
                if text.strip():
                    break
                body.remove(child)

    # --- Данные в прежней удобной форме ---
    subgraph_rows = [
        ["Вершина выбора", "Вершины перехода", "Скорр. сложность", "Вершины подграфа", "Нижняя граница"],
        ["4", "5, 6", "15", "5–18", "19"],
        ["6", "7, 18", "13", "7–18", "19"],
        ["8", "9, 19", "11", "8–17", "19"],
        ["9", "10, 11", "8", "10–16", "17"],
        ["11", "12, 13", "6", "12–16", "17"],
        ["13", "14, 15", "4", "14–16", "17"],
        ["15", "16, 17", "2", "16", "17"],
        ["20", "21, 22", "3", "20, 21", "22"],
        ["25", "26, 27", "3", "25, 26", "27"],
        ["27", "28, 29", "7", "28–33", "34"],
        ["29", "30, 33", "5", "30–33", "34"],
        ["31", "32, 34", "2", "32", "34"],
    ]

    c1 = [["№ вершины", "Скорректированная сложность"]] + [
        [str(n), str(c)]
        for n, c in [
            (1, 1), (2, 1), (3, 1), (4, 15), (5, 1), (6, 13), (7, 1), (8, 11),
            (9, 8), (10, 1), (11, 6), (12, 1), (13, 4), (14, 1), (15, 2), (16, 1), (17, 1),
        ]
    ]
    c2 = [["№ вершины", "Скорректированная сложность"]] + [
        [str(n), str(c)]
        for n, c in [
            (18, 1), (19, 1), (20, 3), (21, 1), (22, 1), (23, 1), (24, 1), (25, 3),
            (26, 1), (27, 7), (28, 1), (29, 5), (30, 1), (31, 2), (32, 1), (33, 1), (34, 0),
        ]
    ]
    summary = [
        ["Метрика", "Значение"],
        ["Число вершин ν", "34"],
        ["Число вершин выбора", "12"],
        ["Абсолютная граничная сложность Sa", "100"],
        ["Относительная граничная сложность So", "0,67"],
    ]

    def detach(table):
        el = table._tbl
        el.getparent().remove(el)
        return el

    t_sub = detach(create_filled_table(doc, subgraph_rows))
    t_c1 = detach(create_filled_table(doc, c1))
    t_c2 = detach(create_filled_table(doc, c2))
    t_sum = detach(create_filled_table(doc, summary, first_col_left=True))

    new_elements = [
        make_para(
            "Таблица 1 – Свойства подграфов программы",
            center=True,
            size=12,
            space_before=8,
            space_after=4,
        ),
        t_sub,
        make_para("", space_before=2, space_after=4),
        make_para(
            "Таблица 2 – Скорректированные сложности вершин графа программы",
            center=True,
            size=12,
            space_before=4,
            space_after=4,
        ),
        t_c1,
        make_para("", space_before=2, space_after=2),
        t_c2,
        make_para("", space_before=2, space_after=4),
    ]

    anchor = results_p
    for el in new_elements:
        anchor.addnext(el)
        anchor = el

    if itogo_p is not None:
        itogo_p.addnext(t_sum)

    try:
        doc.save(work)
        shutil.copy2(work, src)
        print("Updated:", src)
    except PermissionError:
        alt = os.path.join(BASE, "Отчет_Вишневский_Ешманский_lab2b_fixed.docx")
        shutil.copy2(work, alt)
        print("Original locked. Saved:", alt)
    finally:
        if os.path.exists(work):
            os.remove(work)


if __name__ == "__main__":
    main()
