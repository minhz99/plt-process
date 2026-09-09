import os
import io
import json
import uuid
import zipfile
import shutil
import platform
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app

office_bp = Blueprint('office_bp', __name__)

# Định dạng hiện đại (OpenXML zip-based)
MODERN_WORD_EXTENSIONS = {'.docx', '.docm', '.dotx', '.dotm'}
MODERN_EXCEL_EXTENSIONS = {'.xlsx', '.xlsm', '.xltx', '.xltm', '.xlsb'}
MODERN_PPT_EXTENSIONS = {'.pptx', '.pptm', '.potx', '.potm', '.ppsx', '.ppsm'}
MODERN_OFFICE_EXTENSIONS = MODERN_WORD_EXTENSIONS | MODERN_EXCEL_EXTENSIONS | MODERN_PPT_EXTENSIONS

# Định dạng nhị phân cũ (OLE2 Compound Document)
LEGACY_WORD_EXTENSIONS = {'.doc', '.dot'}
LEGACY_EXCEL_EXTENSIONS = {'.xls', '.xlt'}
LEGACY_PPT_EXTENSIONS = {'.ppt', '.pot', '.pps'}
LEGACY_EXTENSIONS = LEGACY_WORD_EXTENSIONS | LEGACY_EXCEL_EXTENSIONS | LEGACY_PPT_EXTENSIONS

ALL_OFFICE_EXTENSIONS = MODERN_OFFICE_EXTENSIONS | LEGACY_EXTENSIONS

MIME_TYPES = {
    # Modern
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.docm': 'application/vnd.ms-word.document.macroEnabled.12',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.pptm': 'application/vnd.ms-powerpoint.presentation.macroEnabled.12',
    # Legacy
    '.doc': 'application/msword',
    '.dot': 'application/msword',
    '.xls': 'application/vnd.ms-excel',
    '.xlt': 'application/vnd.ms-excel',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pot': 'application/vnd.ms-powerpoint',
    '.pps': 'application/vnd.ms-powerpoint',
    '.zip': 'application/zip'
}

SYSTEM_JUNK_FILES = {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
OLE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def _get_temp_dir() -> str:
    temp_dir = os.path.join(current_app.root_path if current_app else os.path.abspath('.'), 'temp', 'office_conv')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def _normalize_entry_name(entry_name: str) -> str:
    """Chuẩn hóa đường dẫn tập tin bên trong file ZIP (dùng dấu /)."""
    return entry_name.replace('\\', '/').strip('/')


def _is_system_junk(entry_name: str) -> bool:
    """Kiểm tra tệp tin rác của hệ điều hành."""
    norm = _normalize_entry_name(entry_name)
    if norm.startswith('__MACOSX/') or os.path.basename(norm).startswith('._'):
        return True
    if os.path.basename(norm) in SYSTEM_JUNK_FILES:
        return True
    return False


# ── XỬ LÝ ĐỊNH DẠNG CŨ QUA COM AUTOMATION (WINDOWS) ──────────────────────────

def convert_legacy_to_modern_bytes(data: bytes, ext: str) -> tuple[bytes, str]:
    """
    Chuyển đổi file định dạng Office cũ (.doc, .xls, .ppt) sang OpenXML (.docx, .xlsx, .pptx).
    Sử dụng Microsoft Office COM Automation trên Windows.
    """
    if platform.system() != 'Windows':
        raise RuntimeError("Chuyển đổi định dạng Office cũ (.doc, .xls, .ppt) hiện chỉ hỗ trợ trên Windows với Microsoft Office.")

    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise RuntimeError("Thư viện pywin32 chưa được cài đặt trong môi trường Python.")

    pythoncom.CoInitialize()
    temp_dir = _get_temp_dir()
    file_id = str(uuid.uuid4())
    in_path = os.path.join(temp_dir, f"in_{file_id}{ext}")
    
    with open(in_path, 'wb') as f:
        f.write(data)

    out_path = None
    modern_ext = ''
    app = None

    try:
        if ext in LEGACY_WORD_EXTENSIONS:
            modern_ext = '.docx'
            out_path = os.path.join(temp_dir, f"out_{file_id}.docx")
            app = win32com.client.Dispatch('Word.Application')
            app.Visible = False
            app.DisplayAlerts = 0
            doc = app.Documents.Open(in_path, ReadOnly=True, ConfirmConversions=False)
            doc.SaveAs(out_path, FileFormat=16)  # 16 = wdFormatXMLDocument (.docx)
            doc.Close()

        elif ext in LEGACY_EXCEL_EXTENSIONS:
            modern_ext = '.xlsx'
            out_path = os.path.join(temp_dir, f"out_{file_id}.xlsx")
            app = win32com.client.Dispatch('Excel.Application')
            app.Visible = False
            app.DisplayAlerts = False
            wb = app.Workbooks.Open(in_path, ReadOnly=True)
            wb.SaveAs(out_path, FileFormat=51)  # 51 = xlOpenXMLWorkbook (.xlsx)
            wb.Close()

        elif ext in LEGACY_PPT_EXTENSIONS:
            modern_ext = '.pptx'
            out_path = os.path.join(temp_dir, f"out_{file_id}.pptx")
            app = win32com.client.Dispatch('PowerPoint.Application')
            pres = app.Presentations.Open(in_path, WithWindow=False)
            pres.SaveAs(out_path, 24)  # 24 = ppSaveAsOpenXMLPresentation (.pptx)
            pres.Close()

        else:
            raise ValueError(f"Định dạng không được hỗ trợ để chuyển đổi: {ext}")

        if not os.path.exists(out_path):
            raise RuntimeError(f"Chuyển đổi thất bại, không tạo được file đầu ra cho {ext}")

        with open(out_path, 'rb') as f:
            converted_data = f.read()

        return converted_data, modern_ext

    finally:
        if app:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
        for p in [in_path, out_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def convert_modern_to_legacy_bytes(data: bytes, target_ext: str) -> bytes:
    """
    Chuyển đổi OpenXML (.docx, .xlsx, .pptx) sang định dạng nhị phân cũ (.doc, .xls, .ppt).
    """
    if platform.system() != 'Windows':
        raise RuntimeError("Chuyển đổi sang định dạng Office cũ (.doc, .xls, .ppt) hiện chỉ hỗ trợ trên Windows với Microsoft Office.")

    try:
        import pythoncom
        import win32com.client
    except ImportError:
        raise RuntimeError("Thư viện pywin32 chưa được cài đặt trong môi trường Python.")

    pythoncom.CoInitialize()
    temp_dir = _get_temp_dir()
    file_id = str(uuid.uuid4())
    in_path = None
    out_path = os.path.join(temp_dir, f"out_{file_id}{target_ext}")
    app = None

    try:
        if target_ext in LEGACY_WORD_EXTENSIONS:
            in_path = os.path.join(temp_dir, f"in_{file_id}.docx")
            with open(in_path, 'wb') as f:
                f.write(data)
            app = win32com.client.Dispatch('Word.Application')
            app.Visible = False
            app.DisplayAlerts = 0
            doc = app.Documents.Open(in_path, ReadOnly=True)
            doc.SaveAs(out_path, FileFormat=0)  # 0 = wdFormatDocument (.doc)
            doc.Close()

        elif target_ext in LEGACY_EXCEL_EXTENSIONS:
            in_path = os.path.join(temp_dir, f"in_{file_id}.xlsx")
            with open(in_path, 'wb') as f:
                f.write(data)
            app = win32com.client.Dispatch('Excel.Application')
            app.Visible = False
            app.DisplayAlerts = False
            wb = app.Workbooks.Open(in_path, ReadOnly=True)
            wb.SaveAs(out_path, FileFormat=56)  # 56 = xlExcel8 (.xls)
            wb.Close()

        elif target_ext in LEGACY_PPT_EXTENSIONS:
            in_path = os.path.join(temp_dir, f"in_{file_id}.pptx")
            with open(in_path, 'wb') as f:
                f.write(data)
            app = win32com.client.Dispatch('PowerPoint.Application')
            pres = app.Presentations.Open(in_path, WithWindow=False)
            pres.SaveAs(out_path, 1)  # 1 = ppSaveAsPresentation (.ppt)
            pres.Close()

        else:
            raise ValueError(f"Định dạng đích cũ không hợp lệ: {target_ext}")

        if not os.path.exists(out_path):
            raise RuntimeError(f"Không tạo được file đích {target_ext}")

        with open(out_path, 'rb') as f:
            result_bytes = f.read()

        return result_bytes

    finally:
        if app:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
        for p in [in_path, out_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


# ── PHÂN TÍCH VÀ ĐÓNG GÓI TỆP TIN OPENXML / ZIP ──────────────────────────────

def inspect_zip_entries(zip_bytes: bytes) -> dict:
    """
    Phân tích cấu trúc các tập tin bên trong gói ZIP / OpenXML.
    Phát hiện loại tài liệu, kiểm tra lỗi lồng thư mục và đếm số lượng media.
    """
    result = {
        'is_valid_zip': False,
        'is_openxml': False,
        'is_legacy': False,
        'detected_type': 'unknown',
        'suggested_ext': '.zip',
        'has_macros': False,
        'is_nested': False,
        'nested_prefix': '',
        'total_files': 0,
        'media_files': [],
        'media_count': 0,
        'entries': []
    }

    # Kiểm tra OLE Compound binary (.doc, .xls, .ppt)
    if zip_bytes.startswith(OLE_MAGIC):
        result['is_legacy'] = True
        return result

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as z:
            result['is_valid_zip'] = True
            all_entries = []
            file_entries = []

            for info in z.infolist():
                norm_name = _normalize_entry_name(info.filename)
                if not norm_name or _is_system_junk(norm_name):
                    continue
                all_entries.append(norm_name)
                if not info.is_dir():
                    file_entries.append(norm_name)

            result['total_files'] = len(file_entries)
            result['entries'] = file_entries

            if not file_entries:
                return result

            # Kiểm tra xem toàn bộ file có nằm trong 1 thư mục cha hay không (Lỗi nén Windows)
            parts_list = [f.split('/') for f in file_entries]
            first_parts = {p[0] for p in parts_list if len(p) > 1}

            if len(first_parts) == 1 and all(len(p) > 1 for p in parts_list):
                candidate_prefix = list(first_parts)[0] + '/'
                has_content_types = any(f == candidate_prefix + '[Content_Types].xml' for f in file_entries)
                has_subdirs = any(f.startswith(candidate_prefix + 'word/') or 
                                  f.startswith(candidate_prefix + 'xl/') or 
                                  f.startswith(candidate_prefix + 'ppt/') for f in file_entries)
                if has_content_types or has_subdirs:
                    result['is_nested'] = True
                    result['nested_prefix'] = candidate_prefix

            prefix_len = len(result['nested_prefix'])
            unwrapped_entries = [f[prefix_len:] for f in file_entries]

            has_macros = any('vbaProject.bin' in f for f in unwrapped_entries)
            result['has_macros'] = has_macros

            media_files = []
            for f in unwrapped_entries:
                parts = f.split('/')
                if 'media' in parts:
                    media_files.append(f)
            result['media_files'] = media_files
            result['media_count'] = len(media_files)

            is_word = any(f.startswith('word/') or f == 'word' for f in unwrapped_entries)
            is_excel = any(f.startswith('xl/') or f == 'xl' for f in unwrapped_entries)
            is_ppt = any(f.startswith('ppt/') or f == 'ppt' for f in unwrapped_entries)
            has_content_types = '[Content_Types].xml' in unwrapped_entries

            if is_word:
                result['is_openxml'] = True
                result['detected_type'] = 'word'
                result['suggested_ext'] = '.docm' if has_macros else '.docx'
            elif is_excel:
                result['is_openxml'] = True
                result['detected_type'] = 'excel'
                result['suggested_ext'] = '.xlsm' if has_macros else '.xlsx'
            elif is_ppt:
                result['is_openxml'] = True
                result['detected_type'] = 'powerpoint'
                result['suggested_ext'] = '.pptm' if has_macros else '.pptx'
            elif has_content_types:
                try:
                    raw_ct_path = (result['nested_prefix'] + '[Content_Types].xml') if result['is_nested'] else '[Content_Types].xml'
                    ct_content = z.read(raw_ct_path).decode('utf-8', errors='ignore')
                    if 'wordprocessingml' in ct_content:
                        result['is_openxml'] = True
                        result['detected_type'] = 'word'
                        result['suggested_ext'] = '.docm' if has_macros else '.docx'
                    elif 'spreadsheetml' in ct_content:
                        result['is_openxml'] = True
                        result['detected_type'] = 'excel'
                        result['suggested_ext'] = '.xlsm' if has_macros else '.xlsx'
                    elif 'presentationml' in ct_content:
                        result['is_openxml'] = True
                        result['detected_type'] = 'powerpoint'
                        result['suggested_ext'] = '.pptm' if has_macros else '.pptx'
                except Exception:
                    pass

    except (zipfile.BadZipFile, Exception):
        result['is_valid_zip'] = False

    return result


def repack_to_clean_office_zip(zip_bytes: bytes, auto_flatten: bool = True) -> tuple[bytes, dict]:
    """
    Chuẩn hóa và đóng gói lại ZIP thành cấu trúc chuẩn Office OpenXML:
    - Loại bỏ thư mục rác hệ thống (__MACOSX, .DS_Store, Thumbs.db).
    - Làm phẳng thư mục gốc bị lồng nếu được nén từ Windows Explorer.
    """
    info = inspect_zip_entries(zip_bytes)
    if not info['is_valid_zip']:
        raise ValueError("Tệp tin không phải định dạng ZIP hợp lệ hoặc đã bị lỗi.")

    prefix_len = len(info['nested_prefix']) if (auto_flatten and info['is_nested']) else 0

    out_buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as z_in:
        with zipfile.ZipFile(out_buffer, 'w', zipfile.ZIP_DEFLATED) as z_out:
            written_names = set()
            for item in z_in.infolist():
                norm_name = _normalize_entry_name(item.filename)
                if not norm_name or _is_system_junk(norm_name) or item.is_dir():
                    continue

                if prefix_len > 0:
                    if not norm_name.startswith(info['nested_prefix']):
                        continue
                    arcname = norm_name[prefix_len:]
                else:
                    arcname = norm_name

                if arcname and arcname not in written_names:
                    written_names.add(arcname)
                    data = z_in.read(item)
                    z_out.writestr(arcname, data)

    out_buffer.seek(0)
    return out_buffer.getvalue(), info


def extract_media_from_zip(zip_bytes: bytes) -> tuple[bytes, int]:
    """
    Trích xuất toàn bộ tệp hình ảnh/media từ tài liệu Office OpenXML thành file ZIP độc lập.
    """
    out_buffer = io.BytesIO()
    media_count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as z_in:
        with zipfile.ZipFile(out_buffer, 'w', zipfile.ZIP_DEFLATED) as z_out:
            used_names = set()
            for item in z_in.infolist():
                norm_name = _normalize_entry_name(item.filename)
                if not norm_name or _is_system_junk(norm_name) or item.is_dir():
                    continue

                parts = norm_name.split('/')
                if 'media' in parts:
                    media_count += 1
                    base_name = os.path.basename(norm_name)
                    target_name = base_name
                    counter = 1
                    name_root, ext = os.path.splitext(base_name)
                    while target_name in used_names:
                        target_name = f"{name_root}_{counter}{ext}"
                        counter += 1
                    used_names.add(target_name)
                    z_out.writestr(target_name, z_in.read(item))

    out_buffer.seek(0)
    return out_buffer.getvalue(), media_count


# ── API ENDPOINTS ────────────────────────────────────────────────────────────

@office_bp.route('/inspect', methods=['POST'])
def inspect_file():
    """Kiểm tra nhanh tập tin và trả về siêu dữ liệu cấu trúc."""
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy tệp tin trong yêu cầu'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Tên tệp không hợp lệ'}), 400

    data = file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    info = inspect_zip_entries(data)

    if info['is_legacy']:
        if ext in LEGACY_WORD_EXTENSIONS:
            info['detected_type'] = 'word'
            info['suggested_ext'] = '.docx'
        elif ext in LEGACY_EXCEL_EXTENSIONS:
            info['detected_type'] = 'excel'
            info['suggested_ext'] = '.xlsx'
        elif ext in LEGACY_PPT_EXTENSIONS:
            info['detected_type'] = 'powerpoint'
            info['suggested_ext'] = '.pptx'

    return jsonify({
        'filename': file.filename,
        'filesize': len(data),
        'extension': ext,
        'info': info
    })


@office_bp.route('/to-zip', methods=['POST'])
def convert_to_zip():
    """
    Chuyển đổi các tệp tin Word/Excel/PowerPoint (.docx, .xlsx, .pptx, .doc, .xls, .ppt) sang file ZIP.
    Hỗ trợ cả định dạng mới và định dạng nhị phân cũ.
    """
    if 'files' not in request.files:
        return jsonify({'error': 'Không tìm thấy tệp tin nào được tải lên'}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Danh sách tệp tin trống'}), 400

    extract_media_only = request.form.get('extract_media_only', 'false').lower() == 'true'

    results = []
    stats = {
        'total': len(files),
        'success': 0,
        'failed': 0,
        'media_count': 0,
        'errors': []
    }

    for file in files:
        if not file.filename:
            continue

        orig_name = file.filename
        base_name, ext = os.path.splitext(orig_name)
        ext = ext.lower()

        if ext not in ALL_OFFICE_EXTENSIONS and ext != '.zip':
            stats['failed'] += 1
            stats['errors'].append(f"{orig_name}: Không phải định dạng Office hợp lệ ({ext})")
            continue

        try:
            content = file.read()

            # Nếu là định dạng cũ (.doc, .xls, .ppt), chuyển sang định dạng mới OpenXML trước
            if ext in LEGACY_EXTENSIONS or content.startswith(OLE_MAGIC):
                try:
                    content, modern_ext = convert_legacy_to_modern_bytes(content, ext)
                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"{orig_name}: Lỗi chuyển đổi file cũ sang OpenXML ({str(e)})")
                    continue

            if not content.startswith(b'PK\x03\x04'):
                stats['failed'] += 1
                stats['errors'].append(f"{orig_name}: Tệp không phải là định dạng nén OpenXML hợp lệ")
                continue

            if extract_media_only:
                media_zip, count = extract_media_from_zip(content)
                if count == 0:
                    stats['failed'] += 1
                    stats['errors'].append(f"{orig_name}: Không tìm thấy hình ảnh/media nào trong tài liệu")
                    continue
                stats['media_count'] += count
                results.append({
                    'filename': f"{base_name}_media.zip",
                    'data': media_zip
                })
            else:
                clean_zip, _ = repack_to_clean_office_zip(content, auto_flatten=False)
                results.append({
                    'filename': f"{base_name}.zip",
                    'data': clean_zip
                })

            stats['success'] += 1

        except Exception as e:
            stats['failed'] += 1
            stats['errors'].append(f"{orig_name}: {str(e)}")

    if not results:
        return jsonify({'error': 'Không có tệp nào được xử lý thành công', 'stats': stats}), 400

    # Nếu chỉ có 1 file: trả về trực tiếp file đó
    if len(results) == 1 and stats['total'] == 1:
        res_file = results[0]
        resp = send_file(
            io.BytesIO(res_file['data']),
            mimetype='application/zip',
            as_attachment=True,
            download_name=res_file['filename']
        )
        resp.headers['X-Office-Stats'] = json.dumps(stats)
        resp.headers['Access-Control-Expose-Headers'] = 'X-Office-Stats'
        return resp

    # Nếu nhiều file: đóng gói vào 1 master ZIP
    master_buffer = io.BytesIO()
    with zipfile.ZipFile(master_buffer, 'w', zipfile.ZIP_DEFLATED) as z_master:
        used_names = set()
        for res in results:
            target_name = res['filename']
            name_root, ext = os.path.splitext(target_name)
            counter = 1
            while target_name in used_names:
                target_name = f"{name_root}_{counter}{ext}"
                counter += 1
            used_names.add(target_name)
            z_master.writestr(target_name, res['data'])

    master_buffer.seek(0)
    download_name = 'office_media_extracted.zip' if extract_media_only else 'office_to_zip_batch.zip'
    resp = send_file(
        master_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )
    resp.headers['X-Office-Stats'] = json.dumps(stats)
    resp.headers['Access-Control-Expose-Headers'] = 'X-Office-Stats'
    return resp


@office_bp.route('/to-office', methods=['POST'])
def convert_to_office():
    """
    Chuyển đổi file ZIP trở lại định dạng tài liệu Office (.docx, .xlsx, .pptx, .doc, .xls, .ppt).
    Tự động nhận diện loại tài liệu và hỗ trợ chuyển đổi sang cả định dạng cũ 97-2003.
    """
    if 'files' not in request.files:
        return jsonify({'error': 'Không tìm thấy tệp tin nào được tải lên'}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Danh sách tệp tin trống'}), 400

    target_format = request.form.get('target_format', 'auto').strip().lower()
    auto_flatten = request.form.get('auto_flatten', 'true').lower() == 'true'

    results = []
    stats = {
        'total': len(files),
        'success': 0,
        'failed': 0,
        'items': [],
        'errors': []
    }

    for file in files:
        if not file.filename:
            continue

        orig_name = file.filename
        base_name, ext = os.path.splitext(orig_name)
        ext = ext.lower()

        if ext != '.zip':
            stats['failed'] += 1
            stats['errors'].append(f"{orig_name}: Chỉ hỗ trợ chuyển đổi từ định dạng .zip sang Office")
            continue

        try:
            content = file.read()
            clean_bytes, info = repack_to_clean_office_zip(content, auto_flatten=auto_flatten)

            # Xác định định dạng đích
            final_ext = ''
            if target_format != 'auto':
                final_ext = '.' + target_format.lstrip('.')
            else:
                if info['detected_type'] != 'unknown':
                    final_ext = info['suggested_ext']
                else:
                    final_ext = '.docx'

            # Nếu định dạng đích là định dạng cũ (.doc, .xls, .ppt)
            output_bytes = clean_bytes
            if final_ext in LEGACY_EXTENSIONS:
                output_bytes = convert_modern_to_legacy_bytes(clean_bytes, final_ext)

            out_filename = f"{base_name}{final_ext}"
            mimetype = MIME_TYPES.get(final_ext, 'application/octet-stream')

            results.append({
                'filename': out_filename,
                'data': output_bytes,
                'mimetype': mimetype,
                'detected_type': info['detected_type'],
                'is_nested': info['is_nested']
            })

            stats['items'].append({
                'original': orig_name,
                'converted': out_filename,
                'type': info['detected_type'],
                'flattened': info['is_nested']
            })
            stats['success'] += 1

        except Exception as e:
            stats['failed'] += 1
            stats['errors'].append(f"{orig_name}: {str(e)}")

    if not results:
        return jsonify({'error': 'Không có tệp nào được xử lý thành công', 'stats': stats}), 400

    # Nếu chỉ có 1 file: trả về trực tiếp file đó
    if len(results) == 1 and stats['total'] == 1:
        res_file = results[0]
        resp = send_file(
            io.BytesIO(res_file['data']),
            mimetype=res_file['mimetype'],
            as_attachment=True,
            download_name=res_file['filename']
        )
        resp.headers['X-Office-Stats'] = json.dumps(stats)
        resp.headers['Access-Control-Expose-Headers'] = 'X-Office-Stats'
        return resp

    # Nếu nhiều file: đóng gói vào 1 master ZIP
    master_buffer = io.BytesIO()
    with zipfile.ZipFile(master_buffer, 'w', zipfile.ZIP_DEFLATED) as z_master:
        used_names = set()
        for res in results:
            target_name = res['filename']
            name_root, ext = os.path.splitext(target_name)
            counter = 1
            while target_name in used_names:
                target_name = f"{name_root}_{counter}{ext}"
                counter += 1
            used_names.add(target_name)
            z_master.writestr(target_name, res['data'])

    master_buffer.seek(0)
    resp = send_file(
        master_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_office_documents.zip'
    )
    resp.headers['X-Office-Stats'] = json.dumps(stats)
    resp.headers['Access-Control-Expose-Headers'] = 'X-Office-Stats'
    return resp
