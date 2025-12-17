import pytest
import httpx
import os
import asyncio

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_upload_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Create dummy file
        files = {'file': ('test_file.txt', b'This is a test file for MinIO API', 'text/plain')}
        
        # 1. Upload
        print("Testing Upload...")
        response = await client.post("/files/upload", files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        file_id = data['id']
        assert data['filename'] == 'test_file.txt'
        print(f"Upload successful. ID: {file_id}")
        
        # 2. Get Metadata
        print("Testing Metadata Retrieval...")
        response = await client.get(f"/files/{file_id}/metadata")
        assert response.status_code == 200, "Metadata retrieval failed"
        meta = response.json()
        assert meta['id'] == file_id
        assert meta['size'] == len(b'This is a test file for MinIO API')
        print("Metadata verified.")
        
        # 3. Download
        print("Testing Download...")
        response = await client.get(f"/files/{file_id}")
        assert response.status_code == 200, "Download failed"
        assert response.content == b'This is a test file for MinIO API'
        print("Download verified.")
        
        # 4. Delete
        print("Testing Delete...")
        response = await client.delete(f"/files/{file_id}")
        assert response.status_code == 200, "Delete failed"
        
        # 5. Verify Deletion
        response = await client.get(f"/files/{file_id}")
        assert response.status_code == 404, "File should be not found after delete"
        print("Delete verified.")

if __name__ == "__main__":
    # Allow running directly with python
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_upload_flow())
