# SilkBridge 音频转换服务

这是一个 HTTP 音频转换服务，支持：

- SILK 转 MP3/WAV/FLAC
- MP3 转 SILK

服务基于 FastAPI、ffmpeg、silk-v3-decoder/encoder，推荐用 Docker Compose + GHCR 镜像部署。

## 线上镜像

推送到 `main` 分支后，GitHub Actions 会自动构建并推送镜像：

```text
ghcr.io/zwscy/silkbridge:latest
```

推送 `v*` 标签时，也会生成对应版本标签的镜像。

首次部署前，需要先把代码推送到 GitHub，并等待 Actions 构建完成。

建议把 GHCR 镜像包设为 Public，这样服务器和宝塔 Docker 可以直接拉取，不需要登录：

1. 打开 GitHub 仓库的 `Packages`
2. 进入 `silkbridge` 包
3. 打开 `Package settings`
4. 在 `Danger Zone` 中把包可见性改成 `Public`

如果 GHCR 镜像包保持私有，服务器需要先登录：

```bash
docker login ghcr.io -u <github-user>
```

密码使用带 `read:packages` 权限的 GitHub token。

## 服务器部署

服务器需要先安装：

- Docker
- Docker Compose 插件，确认命令：`docker compose version`
- Git

首次部署：

```bash
git clone https://github.com/zwscy/SilkBridge.git
cd SilkBridge
cp .env.example .env
./scripts/deploy.sh
```

部署脚本默认会拉取线上镜像并启动容器。

默认监听宿主机 `8080` 端口。需要改端口时，编辑 `.env`：

```bash
PORT=8080
```

修改后重新部署：

```bash
./scripts/deploy.sh
```

## 更新服务

服务器进入项目目录后执行：

```bash
cd SilkBridge
git pull
./scripts/deploy.sh
```

脚本会拉取最新线上镜像并启动容器。

## 本地构建

如果需要在当前机器直接构建镜像：

```bash
DEPLOY_MODE=build ./scripts/deploy.sh
```

## 健康检查

```bash
curl http://localhost:8080/health
```

正常返回：

```json
{"status":"ok"}
```

## 接口用法

SILK 转 MP3：

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@voice.silk" \
  -F "format=mp3" \
  --output output.mp3
```

SILK 转 WAV：

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@voice.silk" \
  -F "format=wav" \
  --output output.wav
```

SILK 转 FLAC：

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@voice.silk" \
  -F "format=flac" \
  --output output.flac
```

MP3 转 SILK：

```bash
curl -X POST http://localhost:8080/convert-to-silk \
  -F "file=@voice.mp3" \
  --output output.silk
```

## 可选参数

`/convert` 支持这些表单参数：

- `format`：输出格式，支持 `mp3`、`wav`、`flac`，默认 `mp3`
- `bitrate`：MP3 码率，支持 `128k`、`192k`、`320k`，默认 `320k`
- `sample_rate`：输出采样率，支持 `8000`、`16000`、`44100`、`48000`，默认 `44100`

示例：

```bash
curl -X POST http://localhost:8080/convert \
  -F "file=@voice.silk" \
  -F "format=mp3" \
  -F "bitrate=192k" \
  -F "sample_rate=44100" \
  --output output.mp3
```

## 常用运维命令

查看容器状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f
```

重启服务：

```bash
docker compose restart
```

停止服务：

```bash
docker compose down
```

重新构建并启动：

```bash
DEPLOY_MODE=build ./scripts/deploy.sh
```
