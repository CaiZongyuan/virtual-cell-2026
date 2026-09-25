# 生成式图片与交付

仅在采用生成式插画时读取，路径均相对于仓库根目录。先确认当前会话是否已有 CLI/API 回退授权；已有授权无需重复询问。共用的可读性与体积要求见 [配图规范](figures.md)。

1. `$imagegen` 优先使用内置 `image_gen`。内置工具不可用且用户已授权 CLI/API 回退时，使用该 skill 自带的 `scripts/image_gen.py`，默认模型为 `gpt-image-2`；通过 `uv run --with openai` 提供依赖，不编写临时 SDK runner，也不修改 skill 脚本。
2. CLI 回退须同时读取 Codex 配置的凭证与 Provider：从 `~/.codex/auth.json` 取得 `OPENAI_API_KEY`，从 `~/.codex/config.toml` 取得当前 provider 的 `base_url`；当前 custom provider 供 OpenAI SDK 使用时在该 URL 后补 `/v1` 并设置 `OPENAI_BASE_URL`。只在子进程环境中注入，不打印、复制、持久化或写入仓库。若只带 Key 直连官方端点，custom-provider Key 会返回 401。
3. 参考图只作风格、构图或情绪指导时，在 prompt 中明确写 `Image 1: style/layout reference`，不得把它描述成待保留内容的 edit target。CLI 需要传图时使用 `edit --image <reference>` 调用图像输入接口，并要求替换原内容、只继承指定视觉特征；`gpt-image-2` 不设置 `input_fidelity`。
4. 信息图 prompt 明确受众、教学目标、分区顺序、逐字标签和科学边界。中文标签保持短小；小字、密集图表或最终资产使用 `quality=medium|high`。生成后逐张检查文字、箭头关系、事实、尺寸、空白、裁切和水印；标签不可靠时改用 HTML/CSS 覆盖准确文字。
5. GPT / `$imagegen` 生成的原始大图、候选图和测试输出先保存到已由 Git 忽略的 `output/imagegen/`，作为本地母版保留，不直接移入或提交到教程目录。
6. 教程采用的生成式图片默认从本地母版转换为 WebP `quality=90`（如 `cwebp -q 90 -m 6 -mt`），将压缩后的 `.webp` 保存到对应的 `docs/**/assets/` 并就近插入 Markdown。转换后核对尺寸、视觉伪影和压缩前后体积；不要覆盖已有资产，除非用户明确要求。完成时报告模式、模型、最终 prompt、参考图角色、最终路径和压缩结果。
