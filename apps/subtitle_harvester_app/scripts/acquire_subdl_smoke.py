from __future__ import annotations

import asyncio

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.pipelines.subtitle_acquire_pipeline import (
    SubtitleAcquirePipeline,
)
from subtitle_harvester_app.pipelines.subtitle_search_pipeline import load_candidates
from subtitle_harvester_app.providers.subdl_provider import SubDLProvider


async def main() -> None:
    settings = init_workspace(get_settings())

    if not settings.subdl_api_key:
        raise RuntimeError("缺少 SUBDL_API_KEY，请在 .env 中配置。")

    candidates_path = settings.resolved_output_dir / "latest" / "latest_batch.json"
    if not candidates_path.exists():
        raise RuntimeError(f"找不到候选文件：{candidates_path}")

    candidates = load_candidates(candidates_path, limit=20)
    if not candidates:
        raise RuntimeError(f"候选文件为空：{candidates_path}")

    provider = SubDLProvider(
        api_key=settings.subdl_api_key.get_secret_value(),
        languages=settings.subdl_languages,
    )
    acquire_pipeline = SubtitleAcquirePipeline(min_score=0.0)

    try:
        for candidate in candidates:
            print(f"🔎 搜索字幕：{candidate.title} ({candidate.year})")

            results = provider.search(candidate)
            downloadable = [item for item in results if item.download_url]

            print(f"   搜索结果：{len(results)}，可下载：{len(downloadable)}")

            if not downloadable:
                continue

            relative_urls = [
                item.download_url
                for item in downloadable
                if item.download_url and not item.download_url.startswith(("http://", "https://"))
            ]
            if relative_urls:
                raise RuntimeError(
                    "发现相对 download_url，请先在 SubDLProvider 中转成完整 URL："
                    f"{relative_urls[:3]}"
                )

            result = await acquire_pipeline.acquire(
                candidate,
                downloadable,
                settings.resolved_output_dir,
                min_score=0.0,
            )

            if not result.success:
                print(f"   ❌ 下载失败：{result.error_message}")
                for index, attempt in enumerate(result.attempts, start=1):
                    file_name = attempt.selected_result.file_name
                    language = attempt.selected_result.language
                    score = attempt.selected_result.score
                    print(
                        f"   attempt {index}: file={file_name}, "
                        f"language={language}, score={score}, error={attempt.error_message}"
                    )
                continue

            print("✅ 字幕获取成功")
            print(f"   media_dir: {result.media_dir}")
            print(f"   raw_dir: {result.raw_dir}")
            print(f"   extracted_dir: {result.extracted_dir}")
            print("   subtitle_files:")
            for subtitle_file in result.subtitle_files:
                print(f"   - {subtitle_file}")

            return

        raise RuntimeError("前 20 个候选都没有成功下载到字幕。")

    finally:
        provider.close()
        await acquire_pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
