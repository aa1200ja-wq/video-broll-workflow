import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from app.config import settings
from app.main import app
from app.models import MaterialAsset
from app.services import library


client = TestClient(app)


def test_material_library_can_move_to_custom_folder():
    source = settings.assets_path / "move-test.mp4"
    source.write_bytes(b"material")
    asset = MaterialAsset(
        id="move-test",
        media_type="video",
        local_path=str(source.resolve()),
        source="manual",
        title="move test",
        width=1920,
        height=1080,
    )
    library.upsert_asset(asset)

    target = Path(tempfile.mkdtemp(prefix="broll-library-target-"))
    response = client.put(
        "/api/settings",
        json={"material_library_dir": str(target)},
    )
    assert response.status_code == 200
    body = response.json()
    assert Path(body["material_library_dir"]) == target.resolve()
    assert Path(body["assets_dir"]).parent == target.resolve()

    moved = target / "assets" / "move-test.mp4"
    assert moved.exists()
    index = json.loads((target / "library.json").read_text(encoding="utf-8"))
    entry = next(item for item in index if item["id"] == "move-test")
    assert Path(entry["local_path"]) == moved.resolve()
    assert library.find_asset("move-test") is not None
