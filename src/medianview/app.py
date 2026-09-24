"""MedianView Flask web application."""

from __future__ import annotations

import base64
import io

from flask import Flask, Response, render_template, request
from PIL import Image, UnidentifiedImageError

from medianview.filter import filter_pil_image

ALLOWED_FORMATS = {"PNG", "JPEG"}


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates")

    @app.route("/", methods=["GET", "POST"])
    def index() -> str | tuple[str, int] | Response:
        if request.method in ("GET", "HEAD"):
            return render_template("index.html")

        if "image" not in request.files:
            return (
                render_template(
                    "index.html",
                    error="No file uploaded. Please select an image file.",
                ),
                400,
            )

        file = request.files["image"]
        if not file.filename:
            return (
                render_template(
                    "index.html",
                    error="No file selected. Please choose a PNG or JPEG file.",
                ),
                400,
            )

        data = file.read()
        if not data:
            return (
                render_template(
                    "index.html",
                    error="The uploaded file is empty.",
                ),
                400,
            )

        try:
            with Image.open(io.BytesIO(data)) as pil_img:
                if pil_img.format not in ALLOWED_FORMATS:
                    return (
                        render_template(
                            "index.html",
                            error=(
                                f"Unsupported image format: {pil_img.format or 'Unknown'}. "
                                "Only PNG and JPEG formats are supported."
                            ),
                        ),
                        400,
                    )

                # Ensure image data is loaded into memory
                pil_img.load()
                filtered = filter_pil_image(pil_img)

                # Original data URI
                orig_mime = "image/png" if pil_img.format == "PNG" else "image/jpeg"
                orig_b64 = base64.b64encode(data).decode("ascii")
                orig_data_uri = f"data:{orig_mime};base64,{orig_b64}"

                # Filtered data URI (rendered losslessly as PNG)
                buf = io.BytesIO()
                filtered.save(buf, format="PNG")
                filtered_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                filtered_data_uri = f"data:image/png;base64,{filtered_b64}"

                return render_template(
                    "index.html",
                    original_image=orig_data_uri,
                    filtered_image=filtered_data_uri,
                )

        except (UnidentifiedImageError, ValueError, OSError):
            return (
                render_template(
                    "index.html",
                    error="The uploaded file is corrupt or not a valid image.",
                ),
                400,
            )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
