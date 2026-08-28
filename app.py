import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from modules.excel.excel_api import excel_bp
from modules.kew.kew_api import kew_bp
from modules.image.image_api import image_bp
from modules.pdf.pdf_api import pdf_bp
from modules.video.video_api import video_bp
from modules.ocr.ocr_api import ocr_bp
from modules.compress.compress_api import compress_bp

def _env_int(name, default):
    """
    Chuyển đổi biến môi trường sang kiểu integer.
    
    Args:
        name (str): Tên biến môi trường.
        default (int): Giá trị mặc định nếu biến không tồn tại hoặc lỗi chuyển đổi.
        
    Returns:
        int: Giá trị integer của biến môi trường hoặc giá trị mặc định.
    """
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


app = Flask(__name__)
app.json.ensure_ascii = False
max_upload_mb = _env_int("MAX_UPLOAD_MB", 0)
app.config["MAX_CONTENT_LENGTH"] = (max_upload_mb * 1024 * 1024) if max_upload_mb > 0 else None
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Register Blueprints for specialized toolset
app.register_blueprint(excel_bp, url_prefix='/api/excel')
app.register_blueprint(kew_bp, url_prefix='/api/kew')
app.register_blueprint(image_bp, url_prefix='/api/image')
app.register_blueprint(pdf_bp, url_prefix='/api/pdf')
app.register_blueprint(video_bp, url_prefix='/api/video')
app.register_blueprint(ocr_bp, url_prefix='/api/ocr')
app.register_blueprint(compress_bp, url_prefix='/api/compress')



@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(_exc):
    """
    Xử lý lỗi khi file upload vượt quá kích thước cho phép.
    
    Args:
        _exc: Đối tượng exception.
        
    Returns:
        Response: Thông báo lỗi dạng JSON hoặc text với mã trạng thái 413.
    """
    max_len = app.config.get("MAX_CONTENT_LENGTH")
    if max_len:
        limit_mb = max_len // (1024 * 1024)
        msg = f"File upload vượt quá giới hạn {limit_mb} MB của server."
    else:
        msg = "File upload vượt quá dung lượng cho phép của server."

    if request.path.startswith("/api/"):
        return jsonify({"error": msg}), 413
    return msg, 413

@app.route('/')
@app.route('/kew')
@app.route('/img')
@app.route('/excel')
@app.route('/pdf')
@app.route('/video')
@app.route('/chart')
@app.route('/ocr')
@app.route('/compress')
def index():
    """Render the main dashboard UI application."""
    return render_template('dashboard.html')

if __name__ == '__main__':
    host = os.environ.get("HOST", "0.0.0.0")
    port = _env_int("PORT", 5525)
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    print(f"Khởi động PLT Process Server trên {host}:{port}...")
    app.run(host=host, port=port, debug=debug)
