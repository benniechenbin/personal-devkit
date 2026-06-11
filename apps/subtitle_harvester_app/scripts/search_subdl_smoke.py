from __future__ import annotations

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.outputs.subtitle_search_writer import write_subtitle_search_results
from subtitle_harvester_app.pipelines.subtitle_search_pipeline import SubtitleSearchPipeline
from subtitle_harvester_app.providers.subdl_provider import SubDLProvider
from subtitle_harvester_app.routing.subtitle_router import SubtitleRouter


def main() -> None:
    settings = init_workspace(get_settings())

    if not settings.subdl_api_key:
        raise RuntimeError("缺少 SUBDL_API_KEY，请在 .env 中配置。")

    input_path = settings.resolved_output_dir / "test_subdl_known_candidates.json"
    output_path = settings.resolved_output_dir / "subtitle_search_results_subdl_smoke.json"

    provider = SubDLProvider(
        api_key=settings.subdl_api_key.get_secret_value(),
        languages=settings.subdl_languages,
    )

    try:
        router = SubtitleRouter([provider])
        pipeline = SubtitleSearchPipeline(router)
        results = pipeline.run(input_path, limit=10)
    finally:
        provider.close()

    write_subtitle_search_results(results, output_path)

    print(f"✅ 已生成字幕搜索结果：{output_path}")
    print(f"📦 共 {len(results)} 条")


if __name__ == "__main__":
    main()
