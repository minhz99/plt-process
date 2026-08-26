# -*- coding: utf-8 -*-
"""
OCR API Blueprint: Handlers for OCR processing of images, PDFs, and ZIP files.
"""
import io
import os
import zipfile
from flask import Blueprint, jsonify, request, send_file
from modules.ocr.ocr_engine import ocr_archive_or_file

ocr_bp = Blueprint('ocr_bp', __name__)

@ocr_bp.route('/process', methods=['POST'])
def process_ocr():
    """
    Nhận 1 hoặc nhiều file (Ảnh, PDF, ZIP) và thực hiện OCR trích xuất plaintext.
    """
    uploaded_files = request.files.getlist('files') or request.files.getlist('file')
    if not uploaded_files or len(uploaded_files) == 0 or not uploaded_files[0].filename:
        return jsonify({"error": "Vui lòng chọn ít nhất một file ảnh, PDF hoặc ZIP để OCR."}), 400

    resolution = 150
    try:
        if 'resolution' in request.form:
            resolution = int(request.form.get('resolution', 150))
    except (ValueError, TypeError):
        resolution = 150

    skip_blank = request.form.get('skip_blank', 'true').strip().lower() in {'true', '1', 'yes'}
    engine_type = request.form.get('engine_type', 'vietocr').strip().lower()

    all_items = []
    total_pages = 0

    try:
        for f in uploaded_files:
            if not f.filename:
                continue
            f_bytes = f.read()
            if not f_bytes:
                continue
            
            items = ocr_archive_or_file(f.filename, f_bytes, resolution=resolution, skip_blank=skip_blank, engine_type=engine_type)
            for it in items:
                total_pages += len(it.get('pages', []))
            all_items.extend(items)

        if not all_items:
            return jsonify({"error": "Không tìm thấy nội dung hợp lệ để OCR."}), 400

        # Ghép văn bản tổng hợp
        combined_parts = []
        for it in all_items:
            combined_parts.append(f"########################################\n# FILE: {it['filename']}\n########################################\n\n{it['full_text']}")
        
        combined_text = "\n\n\n".join(combined_parts)

        return jsonify({
            "success": True,
            "total_files": len(all_items),
            "total_pages": total_pages,
            "items": all_items,
            "combined_text": combined_text
        })

    except Exception as e:
        return jsonify({"error": f"Lỗi trong quá trình OCR: {str(e)}"}), 500


@ocr_bp.route('/download-txt', methods=['POST'])
def download_txt():
    """
    Tải về văn bản OCR dạng file .txt
    """
    payload = request.get_json(silent=True) or {}
    text_content = payload.get('text', '')
    filename = payload.get('filename', 'KetQua_OCR.txt').strip()
    if not filename.lower().endswith('.txt'):
        filename += '.txt'

    output = io.BytesIO()
    output.write(text_content.encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain; charset=utf-8'
    )


@ocr_bp.route('/download-zip', methods=['POST'])
def download_zip():
    """
    Tải về file ZIP chứa các file .txt của từng tài liệu đã OCR.
    """
    payload = request.get_json(silent=True) or {}
    items = payload.get('items', [])
    if not items or not isinstance(items, list):
        return jsonify({"error": "Dữ liệu items không hợp lệ."}), 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for it in items:
            raw_fn = it.get('filename', 'document')
            base_fn = os.path.splitext(os.path.basename(raw_fn))[0] + '.txt'
            text = it.get('full_text', '')
            zf.writestr(base_fn, text.encode('utf-8'))

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='KetQua_OCR_TungFile.zip',
        mimetype='application/zip'
    )
