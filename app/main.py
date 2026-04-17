import shutil
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.converter import ConversionError, convert_silk

app = FastAPI(title="Silk-to-Audio Converter", version="1.0.0")

_MIME = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/convert")
async def convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    format: Literal["mp3", "wav", "flac"] = Form("mp3"),
    bitrate: Literal["128k", "192k", "320k"] = Form("320k"),
    sample_rate: Literal[8000, 16000, 44100, 48000] = Form(44100),
):
    work_dir = Path(tempfile.mkdtemp())
    try:
        input_path = work_dir / "input.silk"
        input_path.write_bytes(await file.read())

        output_path = convert_silk(
            input_path,
            work_dir=work_dir,
            format=format,
            bitrate=bitrate,
            sample_rate=sample_rate,
        )
    except ConversionError as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    # Cleanup AFTER the response body has been fully sent
    background_tasks.add_task(shutil.rmtree, str(work_dir), True)

    return FileResponse(
        path=str(output_path),
        media_type=_MIME[format],
        filename=f"output.{format}",
    )
