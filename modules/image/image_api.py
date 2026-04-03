import os
import base64
import io
from flask import Blueprint, jsonify, current_app
from PIL import Image

image_bp = Blueprint('image_bp', __name__)

@image_bp.route('/templates', methods=['GET'])
def get_templates():
    """Trả về danh sách các mẫu đồng hồ hỗ trợ (dùng cho mở rộng sau này)."""
    templates = [
        {"id": "kew6315", "name": "Kyoritsu KEW 6315"},
        {"id": "kew6305", "name": "Kyoritsu KEW 6305"},
        {"id": "hioki3198", "name": "Hioki PQ3198"},
        {"id": "chauvin", "name": "Chauvin Arnoux C.A 8336"}
    ]
    return jsonify(templates)


@image_bp.route('/digits', methods=['GET'])
def get_digits():
    """Trả về toàn bộ digit templates dạng base64 PNG để client-side dùng cho canvas."""
    digits_dir = os.path.join(current_app.static_folder, 'digits')
    result = {}

    symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'dot', 'minus']
    colors = ['w', 'g']

    for s in symbols:
        for c in colors:
            filename = f"{s}{c}.bmp"
            filepath = os.path.join(digits_dir, filename)
            if not os.path.exists(filepath):
                continue
            try:
                img = Image.open(filepath).convert('RGBA')
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                key = f"{s}_{c}"
                result[key] = f"data:image/png;base64,{b64}"
            except Exception as e:
                current_app.logger.warning(f"Không thể đọc digit {filename}: {e}")

    return jsonify(result)
