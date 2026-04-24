# SilkBridge 音频转换服务

这是一个 HTTP 音频转换服务，支持：

- SILK 转 MP3/WAV/FLAC
- MP3 转 SILK

服务基于 FastAPI、ffmpeg、silk-v3-decoder/encoder，推荐直接拉取 GHCR 镜像部署。

## 线上镜像

GitHub Actions 会自动构建并推送镜像：

```text
ghcr.io/zwscy/silkbridge:latest
```

推送 `v*` 标签时，也会生成对应版本标签的镜像。

## Docker 部署

服务器需要先安装 Docker。默认容器监听 `8080` 端口，宿主机也映射到 `8080`。

```bash
docker pull ghcr.io/zwscy/silkbridge:latest

docker run -d \
  --name silk-converter \
  --restart unless-stopped \
  -p 8080:8080 \
  ghcr.io/zwscy/silkbridge:latest
```

启动后检查：

```bash
docker ps
curl http://localhost:8080/health
```

正常返回：

```json
{"status":"ok"}
```

如果需要外网访问，需要在服务器防火墙和云厂商安全组中放行 `8080` 端口。

### 更新服务

镜像更新后，服务器执行：

```bash
docker pull ghcr.io/zwscy/silkbridge:latest
docker rm -f silk-converter

docker run -d \
  --name silk-converter \
  --restart unless-stopped \
  -p 8080:8080 \
  ghcr.io/zwscy/silkbridge:latest
```

## 本地部署

本地部署需要安装 Git、Docker 和 Docker Compose 插件。

```bash
git clone https://github.com/zwscy/SilkBridge.git
cd SilkBridge
cp .env.example .env
./scripts/deploy.sh
```

`scripts/deploy.sh` 默认会拉取线上镜像并启动容器。如果需要在当前机器直接构建镜像：

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
docker ps
```

查看日志：

```bash
docker logs -f silk-converter
```

重启服务：

```bash
docker restart silk-converter
```

停止服务：

```bash
docker rm -f silk-converter
```

拉取最新镜像并重启：

```bash
docker pull ghcr.io/zwscy/silkbridge:latest
docker rm -f silk-converter
docker run -d --name silk-converter --restart unless-stopped -p 8080:8080 ghcr.io/zwscy/silkbridge:latest
```
