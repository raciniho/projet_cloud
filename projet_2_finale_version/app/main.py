from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import init_db, get_session
from app.models import FileMetadata
from app.storage import minio_handler
import hashlib
from typing import List
from uuid import UUID

app = FastAPI(title="MinIO Microservice API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.post("/files/upload", response_model=FileMetadata)
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Calculate Hash and Size
        sha256_hash = hashlib.sha256()
        file_size = 0
        file_content = await file.read()
        
        sha256_hash.update(file_content)
        file_hash = sha256_hash.hexdigest()
        file_size = len(file_content)
        
        # Reset cursor for upload (MinIO client might need stream or bytes)
        # Using BytesIO for MinIO
        import io
        data = io.BytesIO(file_content)
        
        # Unique object name
        import uuid
        object_name = f"{uuid.uuid4()}-{file.filename}"
        
        # Upload to MinIO
        minio_handler.upload_file(
            object_name=object_name,
            data=data,
            length=file_size,
            content_type=file.content_type
        )
        
        # Save Metadata
        new_file = FileMetadata(
            filename=file.filename,
            size=file_size,
            content_type=file.content_type,
            hash=file_hash,
            minio_object_name=object_name
        )
        session.add(new_file)
        await session.commit()
        await session.refresh(new_file)
        
        return new_file

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_id}", response_class=StreamingResponse)
async def download_file(
    file_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    file_item = await session.get(FileMetadata, file_id)
    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")
        
    response = minio_handler.get_file(file_item.minio_object_name)
    if not response:
        raise HTTPException(status_code=500, detail="File missing in storage")
        
    return StreamingResponse(
        response,
        media_type=file_item.content_type,
        headers={"Content-Disposition": f"attachment; filename={file_item.filename}"}
    )

@app.get("/files/{file_id}/metadata", response_model=FileMetadata)
async def get_file_metadata(
    file_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    file_item = await session.get(FileMetadata, file_id)
    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")
    return file_item

@app.delete("/files/{file_id}")
async def delete_file(
    file_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    file_item = await session.get(FileMetadata, file_id)
    if not file_item:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Remove from MinIO
    minio_handler.delete_file(file_item.minio_object_name)
    
    # Remove from DB
    await session.delete(file_item)
    await session.commit()
    
    return {"message": "File deleted successfully"}

@app.get("/files", response_model=List[FileMetadata])
async def list_files(
    session: AsyncSession = Depends(get_session)
):
    statement = select(FileMetadata)
    results = await session.exec(statement)
    return results.all()
