import os
from datetime import datetime


class ObsidianWrapper:
    @staticmethod
    def inject_yaml_frontmatter(
        body_text: str, source_filename: str, custom_tags: list | None = None
    ) -> str:
        """
        将纯净的 Markdown 文本包装为符合 Obsidian 契约的笔记格式
        """
        file_name = os.path.basename(source_filename).replace(".pdf", "")
        safe_title = file_name.replace('"', "'").replace(":", "：").replace("\n", "")
        tags = ["OCR-Extracted", "知识自动化"]
        if custom_tags:
            tags.extend(custom_tags)

        tags_str = ", ".join(tags)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        yaml_header = (
            "---\n"
            f'title: "{safe_title}"\n'
            f"date: {current_time}\n"
            f"tags: [{tags_str}]\n"
            "status: unreviewed\n"
            "---\n\n"
        )
        return yaml_header + body_text
