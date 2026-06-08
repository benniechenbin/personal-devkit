# services/documents_intelligence/assembler.py

from .schema import Fragment


class DocumentAssembler:
    """文档重组与装配器"""

    def assemble(self, fragments: list[Fragment]) -> str:
        """
        目前阶段：仅仅做排序与物理拼接
        未来阶段：在这里插入 Stitcher 逻辑 (跨页表合并、重叠处理)
        """
        # 1. 全局排序 (按页码 -> 按纵坐标)
        fragments.sort(key=lambda f: (f.page_num, f.y0))

        # 2. 物理拼接 (目前先简单粗暴合并)
        markdown_output = ""
        for frag in fragments:
            markdown_output += f"\n\n{frag.content}"

        return markdown_output
