import os
import io
import uuid
import json
import zipfile
import shutil
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file, current_app
from PIL import Image, ImageOps

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

compress_bp = Blueprint('compress_bp', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif', '.bmp', '.heic', '.heif'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | {'.zip'}

@compress_bp.route('/process', methods=['POST'])
def process():
    if 'files' not in request.files:
        return jsonify({"error": "Không tìm thấy tệp nào trong yêu cầu"}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Danh sách tệp trống"}), 400

    # Đọc các tham số
    try:
        quality = int(request.form.get('quality', 80))
        max_width = int(request.form.get('max_width', 0))
        max_height = int(request.form.get('max_height', 0))
    except ValueError:
        return jsonify({"error": "Các tham số quality, max_width, max_height phải là số nguyên"}), 400

    strip_metadata = request.form.get('strip_metadata', 'true').lower() == 'true'
    auto_orient = request.form.get('auto_orient', 'true').lower() == 'true'

    # Đảm bảo quality nằm trong khoảng 1-100
    quality = max(1, min(100, quality))

    session_id = str(uuid.uuid4())
    temp_dir = os.path.join(current_app.root_path, 'temp', f'compress_{session_id}')
    os.makedirs(temp_dir, exist_ok=True)

    stats = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'kept_original': 0,
        'original_size': 0,
        'compressed_size': 0,
        'saved_size': 0,
        'saved_percent': 0.0,
        'errors': []
    }

    try:
        # Thu thập danh sách tất cả các ảnh cần nén (từ file ảnh trực tiếp hoặc từ file zip)
        items_to_process = []
        
        for file in files:
            if not file.filename:
                continue
            
            filename = file.filename
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in ALLOWED_EXTENSIONS:
                stats['failed'] += 1
                stats['errors'].append(f"{filename}: Định dạng không được hỗ trợ")
                continue
            
            file_content = file.read()
            
            if ext == '.zip':
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content), 'r') as z_in:
                        zip_img_count = 0
                        for zip_info in z_in.infolist():
                            if zip_info.is_dir():
                                continue
                            
                            entry_name = zip_info.filename.replace('\\', '/')
                            # Bỏ qua các file ẩn/rác hệ thống MacOS & Windows
                            if (entry_name.startswith('__MACOSX/') or 
                                os.path.basename(entry_name).startswith('._') or 
                                os.path.basename(entry_name) in {'.DS_Store', 'Thumbs.db'}):
                                continue
                            
                            entry_ext = os.path.splitext(entry_name)[1].lower()
                            if entry_ext in ALLOWED_IMAGE_EXTENSIONS:
                                zip_img_count += 1
                                item_bytes = z_in.read(zip_info)
                                items_to_process.append({
                                    'arcname': entry_name,
                                    'display_name': f"{filename}/{entry_name}" if len(files) > 1 else entry_name,
                                    'file_content': item_bytes,
                                    'filename': entry_name
                                })
                        
                        if zip_img_count == 0:
                            stats['failed'] += 1
                            stats['errors'].append(f"{filename}: Không tìm thấy hình ảnh hợp lệ bên trong file ZIP")
                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"{filename}: Lỗi khi đọc file ZIP ({str(e)})")
            else:
                items_to_process.append({
                    'arcname': filename,
                    'display_name': filename,
                    'file_content': file_content,
                    'filename': filename
                })

        stats['total'] = len(items_to_process) + stats['failed']

        if not items_to_process and stats['failed'] > 0:
            return jsonify({
                "error": "Không có hình ảnh hợp lệ nào để xử lý",
                "stats": stats
            }), 400

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            used_arcnames = set()

            for item in items_to_process:
                filename = item['filename']
                arcname = item['arcname']
                display_name = item['display_name']
                file_content = item['file_content']
                ext = os.path.splitext(filename)[1].lower()

                if ext in {'.heic', '.heif'} and not HEIF_SUPPORT:
                    stats['failed'] += 1
                    stats['errors'].append(f"{display_name}: Không hỗ trợ định dạng HEIC/HEIF do thiếu thư viện pillow-heif")
                    continue

                original_size = len(file_content)
                stats['original_size'] += original_size

                try:
                    # Mở ảnh
                    img = Image.open(io.BytesIO(file_content))
                    
                    # Tự động xoay ảnh theo EXIF
                    if auto_orient:
                        try:
                            img = ImageOps.exif_transpose(img)
                        except Exception as e:
                            current_app.logger.warning(f"Lỗi khi xoay ảnh {display_name}: {str(e)}")

                    # Thay đổi kích thước
                    if max_width > 0 or max_height > 0:
                        w, h = img.size
                        target_w = max_width if max_width > 0 else w
                        target_h = max_height if max_height > 0 else h
                        
                        # Chỉ thu nhỏ, không phóng to
                        if w > target_w or h > target_h:
                            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
                    
                    # Chuyển đổi sang RGB (loại bỏ alpha channel)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Lưu dưới dạng JPEG
                    out_buffer = io.BytesIO()
                    save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True}
                    if quality >= 95:
                        save_kwargs['subsampling'] = 0
                    
                    # strip_metadata được xử lý mặc định khi không truyền tham số exif
                    img.save(out_buffer, **save_kwargs)
                    compressed_content = out_buffer.getvalue()
                    compressed_size = len(compressed_content)

                    # So sánh: nếu sau nén file to hơn hoặc bằng gốc → giữ file gốc
                    if compressed_size >= original_size:
                        target_arcname = arcname
                        # Đảm bảo tên không bị trùng trong ZIP đích
                        target_arcname = _resolve_unique_arcname(target_arcname, used_arcnames)
                        zip_file.writestr(target_arcname, file_content)
                        stats['compressed_size'] += original_size
                        stats['kept_original'] += 1
                    else:
                        base_path = os.path.splitext(arcname)[0]
                        target_arcname = f"{base_path}.jpg"
                        target_arcname = _resolve_unique_arcname(target_arcname, used_arcnames)
                        zip_file.writestr(target_arcname, compressed_content)
                        stats['compressed_size'] += compressed_size

                    stats['success'] += 1
                    
                except Exception as e:
                    current_app.logger.error(f"Lỗi khi xử lý ảnh {display_name}: {str(e)}")
                    stats['failed'] += 1
                    stats['errors'].append(f"{display_name}: {str(e)}")

        stats['saved_size'] = max(0, stats['original_size'] - stats['compressed_size'])
        if stats['original_size'] > 0:
            stats['saved_percent'] = round((stats['saved_size'] / stats['original_size']) * 100, 1)

        zip_buffer.seek(0)
        
        response = send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='compressed.zip'
        )
        response.headers['X-Compress-Stats'] = json.dumps(stats)
        response.headers['Access-Control-Expose-Headers'] = 'X-Compress-Stats'
        return response

    finally:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            current_app.logger.error(f"Lỗi khi xóa thư mục tạm {temp_dir}: {str(e)}")


def _resolve_unique_arcname(arcname, used_set):
    """Đảm bảo tên file trong ZIP không bị trùng lặp."""
    if arcname not in used_set:
        used_set.add(arcname)
        return arcname
    
    dir_name, base_name = os.path.split(arcname)
    name, ext = os.path.splitext(base_name)
    counter = 1
    while True:
        candidate = os.path.join(dir_name, f"{name}_{counter}{ext}").replace('\\', '/')
        if candidate not in used_set:
            used_set.add(candidate)
            return candidate
        counter += 1

