import logging
import sys
from pathlib import Path

from document_engine import DocumentAssembler, DocumentRouter

# 简单配置日志以便查看输出
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    # 1. 准备工作目录
    example_dir = Path(__file__).parent
    data_dir = example_dir / "data"
    output_dir = example_dir / "output"

    # 确保输出目录存在
    output_dir.mkdir(exist_ok=True)

    # 提示用户放入测试文件
    print(f"工作目录: {example_dir}")
    print(f"数据目录: {data_dir}")
    print("-" * 40)

    # 寻找 data 目录下的第一个支持的文件
    test_files = list(data_dir.glob("*.*"))
    supported_files = [
        f for f in test_files if f.suffix.lower() in [".pdf", ".xlsx", ".xlsm", ".csv", ".docx"]
    ]

    if not supported_files:
        msg = (
            f"⚠️  未找到测试文件。\n"
            f"请先在 {data_dir} 下放置一个测试文档 (支持 .pdf, .xlsx, .xlsm, .csv, .docx)。"
        )
        print(msg)
        sys.exit(0)

    target_file = supported_files[0]
    print(f"🚀 发现测试文件，正在解析: {target_file.name}...")

    # 2. 调用路由解析
    try:
        router = DocumentRouter(output_dir=str(output_dir))
        fragments = router.parse(target_file)
        print(f"✅ 解析完成，获得 {len(fragments)} 个 Fragment。")

        # 3. 装配为 Markdown
        print("🔨 正在装配为 Markdown...")
        assembler = DocumentAssembler()
        markdown_content = assembler.assemble(fragments)

        # 4. 查看效果预览
        print("\n" + "=" * 50)
        print("--- 预览 (前500字符) ---")
        preview = markdown_content[:500]
        print(preview if preview.strip() else "[内容为空]")
        if len(markdown_content) > 500:
            print("\n... (更多内容省略) ...")
        print("=" * 50 + "\n")

        # 5. 保存完整结果
        output_path = output_dir / f"{target_file.stem}.md"
        output_path.write_text(markdown_content, encoding="utf-8")
        print(f"💾 完整结果已保存至:\n  {output_path.absolute()}")

    except Exception as e:
        print(f"❌ 解析过程中发生错误: {e}")
        logging.exception(e)


if __name__ == "__main__":
    main()
