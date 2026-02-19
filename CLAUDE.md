# ComfyUI-MidJourney

ComfyUI custom node for Midjourney image generation.

## Dependencies

- Midjourney Python API Client: `/mnt/c/Users/Jooyo/source/MJ_API`
  - 패키지명: `midjourney-api`
  - 주요 클래스: `MidjourneyClient` (`midjourney_api/client.py`)
  - 기능: imagine, vary, upscale, pan, download
  - 인증: Firebase refresh token (`.env`)
  - HTTP: `curl_cffi` (Chrome TLS impersonation)
