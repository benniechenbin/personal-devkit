# services/ocr_engine/table_extractor.py
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class TableExtractor:
    def __init__(self):
        # ⚡ 状态机缓存：用于记忆上一页的“半截表格”
        self.buffered_table_data = None
        self.buffered_col_count = 0

    def process_document(self, doc: fitz.Document) -> str:
        """
        全文档级扫描：具备跨页缝合能力
        """
        markdown_tables = []
        table_counter = 1

        logger.info("启动全局表格扫描，共 %s 页。", len(doc))

        for page_num in range(len(doc)):
            page = doc[page_num]
            tables = page.find_tables()

            # --- 🛡️ 熔断机制 1：断层熔断 ---
            if not tables or not tables.tables:
                # 当前页没有表格，说明之前的跨页表格已经彻底结束
                if self.buffered_table_data:
                    markdown_tables.append(
                        self.render_markdown(self.buffered_table_data, table_counter)
                    )
                    table_counter += 1
                    self.buffered_table_data = None  # 清空缓存
                continue

            # 开始遍历当前页的表格
            for idx, table in enumerate(tables.tables):
                raw_data = table.extract()
                if not raw_data or len(raw_data) < 1:
                    continue

                current_col_count = len(raw_data[0])

                # --- ⚡ 核心逻辑：跨页缝合 ---
                # 条件：当前页的第1个表格 + 存在历史缓存 + 且两者的【列数完全一致】
                if (
                    idx == 0
                    and self.buffered_table_data
                    and current_col_count == self.buffered_col_count
                ):
                    logger.info(
                        "触发跨页合并：第 %s 页底部与第 %s 页顶部表格已无缝缝合。",
                        page_num,
                        page_num + 1,
                    )

                    # 重要妥协：如果下一页表格带有重复表头，先作为普通数据行拼入。
                    self.buffered_table_data.extend(raw_data)

                else:
                    # 遇到新表格（或者列数不匹配引发熔断），先把旧缓存吐出来
                    if self.buffered_table_data:
                        markdown_tables.append(
                            self.render_markdown(self.buffered_table_data, table_counter)
                        )
                        table_counter += 1

                    # 将当前新表格推入缓存
                    self.buffered_table_data = raw_data
                    self.buffered_col_count = current_col_count

        # --- 🛡️ 最终清理：文档结束，吐出最后残留的缓存 ---
        if self.buffered_table_data:
            markdown_tables.append(self.render_markdown(self.buffered_table_data, table_counter))

        return "".join(markdown_tables)

    def render_markdown(self, raw_data: list, table_idx: int) -> str:
        """
        将二维数组渲染为标准 Markdown 表格
        """
        try:
            table_lines = []

            # 1. 强制提取第一行作为表头
            header = raw_data[0]
            header_str = " | ".join(
                [str(cell).strip().replace("\n", "") if cell else "" for cell in header]
            )
            table_lines.append(f"| {header_str} |")

            # 2. 补充分割线
            separator_str = " | ".join(["---" for _ in header])
            table_lines.append(f"| {separator_str} |")

            # 3. 处理数据行
            for row in raw_data[1:]:
                # 过滤全空行
                if not any(row):
                    continue
                row_str = " | ".join(
                    [str(cell).strip().replace("\n", "") if cell else "" for cell in row]
                )
                table_lines.append(f"| {row_str} |")

            full_table_md = "\n".join(table_lines)
            return f"\n\n> 📊 [提取表格 {table_idx}]\n\n{full_table_md}\n\n"

        except Exception as e:
            # --- 🛡️ 熔断机制 2：渲染熔断 ---
            logger.warning("表格渲染熔断：数据结构异常 (%s)", e)
            return f"\n\n> ⚠️ [表格 {table_idx} 解析失败：超出了沙盒处理边界]\n\n"


# ==========================================
# 🧪 跨页表格测试
# ==========================================
if __name__ == "__main__":
    import os

    # 找一份包含跨页表格的 PDF（比如你截图里的那份规范）
    test_pdf_path = "tests/table_sample.pdf"

    if os.path.exists(test_pdf_path):
        doc = fitz.open(test_pdf_path)
        extractor = TableExtractor()

        # 注意：现在我们是直接传入整个 doc 跑全文档扫描
        table_md = extractor.process_document(doc)

        print("\n" + "=" * 50)
        print("🎯 跨页表格提取结果：")
        print("=" * 50)
        print(table_md if table_md else "[全文档未检测到矢量表格]")
        print("=" * 50)
        doc.close()
    else:
        logger.error("请在 tests 目录下放置跨页测试 PDF: %s", test_pdf_path)
