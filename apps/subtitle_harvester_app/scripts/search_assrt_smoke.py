from __future__ import annotations

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.outputs.subtitle_search_writer import write_subtitle_search_results
from subtitle_harvester_app.pipelines.subtitle_search_pipeline import load_candidates
from subtitle_harvester_app.providers.assrt import AssrtApiProvider, AssrtQuotaExceeded


def main() -> None:
    settings = init_workspace(get_settings())

    if not settings.assrt_token:
        raise RuntimeError("缺少 ASSRT_TOKEN，请在 .env 中配置。")

    candidates_path = settings.resolved_output_dir / "latest" / "latest_snapshot.json"
    if not candidates_path.exists():
        candidates_path = settings.resolved_output_dir / "latest" / "latest_batch.json"

    if not candidates_path.exists():
        raise RuntimeError(f"找不到候选文件：{candidates_path}")

    candidates = load_candidates(candidates_path, limit=5)
    if not candidates:
        raise RuntimeError(f"候选文件为空：{candidates_path}")

    provider = AssrtApiProvider(
        token=settings.assrt_token.get_secret_value(),
        max_detail_results=1,
    )

    all_results = []

    try:
        for candidate in candidates:
            print(f"🔎 搜索 Assrt 字幕：{candidate.title} ({candidate.year})")

            try:
                results = provider.search(candidate)
            except AssrtQuotaExceeded as exc:
                print(f"⚠️ Assrt API 配额或频率限制，停止本轮冒烟测试：{exc}")
                break

            downloadable = [item for item in results if item.download_url]

            print(f"   搜索结果：{len(results)}，可下载：{len(downloadable)}")

            for index, item in enumerate(downloadable[:5], start=1):
                print(
                    f"   {index}. lang={item.language}, "
                    f"score={item.score:.1f}, "
                    f"file={item.file_name}, "
                    f"url={item.download_url}"
                )

            all_results.extend(results)

            if downloadable:
                break

    finally:
        provider.close()

    output_path = settings.resolved_output_dir / "subtitle_search_results_assrt_smoke.json"
    write_subtitle_search_results(all_results, output_path)

    print(f"✅ 已生成 Assrt 搜索结果：{output_path}")
    print(f"📦 共 {len(all_results)} 条")


if __name__ == "__main__":
    main()
