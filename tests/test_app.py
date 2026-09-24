"""Integration tests for MedianView Flask application."""

import io
from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from PIL import Image

from medianview.app import create_app


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Test client fixture for the Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def create_test_image_bytes(format_name: str, mode: str = "RGB", size: tuple[int, int] = (20, 20)) -> bytes:
    """Helper to generate encoded image bytes for tests."""
    img = Image.new(mode, size, color=(100, 150, 200) if mode == "RGB" else 128)
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_get_index(client: FlaskClient) -> None:
    """GET / should render the upload form."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "MedianView" in html
    assert '<input id="image_file" type="file"' in html
    assert "Apply 3x3 Median Filter" in html


def test_post_valid_png(client: FlaskClient) -> None:
    """POST / with a valid PNG image renders side-by-side comparison."""
    png_bytes = create_test_image_bytes("PNG")
    data = {
        "image": (io.BytesIO(png_bytes), "sample.png", "image/png"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Original" in html
    assert "Filtered (3x3 Median)" in html
    assert "data:image/png;base64," in html
    assert "Upload Another Image" in html


def test_post_valid_jpeg(client: FlaskClient) -> None:
    """POST / with a valid JPEG image renders side-by-side comparison."""
    jpeg_bytes = create_test_image_bytes("JPEG")
    data = {
        "image": (io.BytesIO(jpeg_bytes), "sample.jpg", "image/jpeg"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Original" in html
    assert "Filtered (3x3 Median)" in html
    assert "data:image/jpeg;base64," in html
    assert "data:image/png;base64," in html


def test_post_no_file(client: FlaskClient) -> None:
    """POST / without an image part should return 400 Bad Request."""
    response = client.post("/", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "No file uploaded" in html


def test_post_empty_filename(client: FlaskClient) -> None:
    """POST / with an empty filename should return 400 Bad Request."""
    data = {
        "image": (io.BytesIO(b""), "", "application/octet-stream"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "No file selected" in html


def test_post_empty_file_content(client: FlaskClient) -> None:
    """POST / with empty content should return 400 Bad Request."""
    data = {
        "image": (io.BytesIO(b""), "empty.png", "image/png"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "The uploaded file is empty" in html


def test_post_corrupt_file(client: FlaskClient) -> None:
    """POST / with non-image bytes should return 400 Bad Request."""
    data = {
        "image": (io.BytesIO(b"not an image at all"), "fake.png", "image/png"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "corrupt or not a valid image" in html


def test_post_unsupported_format(client: FlaskClient) -> None:
    """POST / with an unsupported image format (e.g. GIF) should return 400 Bad Request."""
    gif_bytes = create_test_image_bytes("GIF")
    data = {
        "image": (io.BytesIO(gif_bytes), "sample.gif", "image/gif"),
    }
    response = client.post("/", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    html = response.get_data(as_text=True)
    assert "Unsupported image format" in html
