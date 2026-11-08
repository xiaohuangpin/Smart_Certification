"""Excel 解析工具：拆分合并单元格，并将每个工作表转为带行号的 Markdown 表格。"""

from datetime import date, datetime, time
from pathlib import Path
from typing import BinaryIO

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.common.errors import AppError

ExcelSource = str | Path | BinaryIO


class ExcelParser:
    """将 Excel 解析为 {工作表名: Markdown 内容}，Markdown 首列为行号便于定位。"""

    @classmethod
    def parse(
        cls,
        source: ExcelSource,
        *,
        data_only: bool = True,
    ) -> dict[str, str]:
        """解析 Excel。source 支持路径或文件对象，隐藏工作表会被跳过。"""
        try:
            workbook = load_workbook(source, data_only=data_only)
        except Exception as exc:
            raise AppError("EXCEL_PARSE_ERROR", "Excel 文件解析失败，请确认文件格式", 400) from exc

        try:
            return {
                sheet.title: cls._sheet_to_markdown(sheet)
                for sheet in workbook.worksheets
                if sheet.sheet_state == "visible"
            }
        finally:
            workbook.close()

    @staticmethod
    def _unmerge(sheet: Worksheet) -> None:
        """拆分合并单元格，并将原合并区域的值填充到区域内每个单元格。"""
        for merged in list(sheet.merged_cells.ranges):
            value = sheet.cell(merged.min_row, merged.min_col).value
            sheet.unmerge_cells(str(merged))
            if value is None:
                continue
            for row in sheet.iter_rows(
                min_row=merged.min_row,
                max_row=merged.max_row,
                min_col=merged.min_col,
                max_col=merged.max_col,
            ):
                for cell in row:
                    cell.value = value

    @classmethod
    def _sheet_to_markdown(cls, sheet: Worksheet) -> str:
        cls._unmerge(sheet)
        rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        width = max((len(row) for row in rows), default=0)
        rows = [row + [None] * (width - len(row)) for row in rows]
        while rows and all(cls._is_blank(value) for value in rows[-1]):
            rows.pop()
        while width and all(cls._is_blank(row[width - 1]) for row in rows):
            width -= 1
        rows = [row[:width] for row in rows]
        if not rows or not width:
            return ""

        header = "| 行号 | " + " | ".join(get_column_letter(i) for i in range(1, width + 1)) + " |"
        divider = "| --- |" + " --- |" * width
        body = [
            f"| {index} | " + " | ".join(cls._format(value) for value in row) + " |"
            for index, row in enumerate(rows, start=1)
        ]
        return "\n".join([header, divider, *body])

    @staticmethod
    def _is_blank(value: object) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def _format(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            has_time = value.hour or value.minute or value.second
            text = value.strftime("%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d")
        elif isinstance(value, date | time):
            text = value.isoformat()
        elif isinstance(value, float) and value.is_integer():
            text = str(int(value))
        else:
            text = str(value)
        return text.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


if __name__ == "__main__":
    excel_path = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "NS260930001205"
        / "NS260930001205附件（税金计提明细表西彭09）.xlsx"
    )
    for key, markdown in ExcelParser.parse(excel_path).items():
        print(f"== {key} ==")
        print(markdown)

