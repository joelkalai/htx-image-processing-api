import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_and_list():
    # Create a tiny in-memory image
    from PIL import Image
    img = Image.new("RGB", (64, 64), (120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("sample.png", buf, "image/png")}
    r = client.post("/api/images", files=files)
    assert r.status_code in (200, 202)
    j = r.json()
    assert j["status"] in ("accepted", "success")
    image_id = j["data"]["image_id"]
    assert image_id

    # List images
    r2 = client.get("/api/images")
    assert r2.status_code == 200
    assert any(item["id"] == image_id for item in r2.json())
