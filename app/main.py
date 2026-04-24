import shutil
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.converter import ConversionError, convert_mp3_to_silk, convert_silk

_VALID_RATES = {8000, 16000, 44100, 48000}

app = FastAPI(title="Silk Audio Converter", version="1.1.0")

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
    sample_rate: int = Form(44100),
):
    if sample_rate not in _VALID_RATES:
        raise HTTPException(status_code=422, detail=f"sample_rate must be one of {sorted(_VALID_RATES)}")
    work_dir = Path(tempfile.mkdtemp())
    try:
        input_path = work_dir / "input.silk"
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:  # 10 MB max
            shutil.rmtree(work_dir, ignore_errors=True)
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
        input_path.write_bytes(data)

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
        raise HTTPException(status_code=500, detail="Internal server error")

    # Cleanup AFTER the response body has been fully sent
    background_tasks.add_task(shutil.rmtree, work_dir, ignore_errors=True)

    return FileResponse(
        path=output_path,
        media_type=_MIME[format],
        filename=f"output.{format}",
    )


@app.post("/convert-to-silk")
async def convert_to_silk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    work_dir = Path(tempfile.mkdtemp())
    try:
        input_path = work_dir / "input.mp3"
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:  # 10 MB max
            shutil.rmtree(work_dir, ignore_errors=True)
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
        input_path.write_bytes(data)

        output_path = convert_mp3_to_silk(input_path, work_dir=work_dir)
    except ConversionError as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    background_tasks.add_task(shutil.rmtree, work_dir, ignore_errors=True)

    return FileResponse(
        path=output_path,
        media_type="audio/silk",
        filename="output.silk",
    )
