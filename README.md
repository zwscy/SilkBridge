# SilkBridge 音频转换服务

这是一个 HTTP 音频转换服务，支持：

- SILK 转 MP3/WAV/FLAC
- MP3 转 SILK

服务基于 FastAPI、ffmpeg、silk-v3-decoder/encoder，推荐用 Docker Compose 部署。

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

脚本会重新构建镜像并启动容器。

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
./scripts/deploy.sh
```
