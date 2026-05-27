import os
import io
import re
import uuid
import shutil
import zipfile
import subprocess
import traceback
from flask import Blueprint, request, jsonify, send_file, current_app

pdf_bp = Blueprint('pdf_bp', __name__)

def get_pdf_page_count(filepath):
    """
    Đọc số lượng trang của tệp PDF với giải pháp fallback đa tầng:
    1. Sử dụng thư viện pypdf (Python).
    2. Sử dụng công cụ pdfinfo (nếu được cài đặt).
    3. Sử dụng Ghostscript (gs).
    """
    # 1. Thử dùng pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return len(reader.pages)
    except Exception as e:
        current_app.logger.warning("pypdf page count failed: %s", e)

    # 2. Thử dùng pdfinfo
    for cmd_path in ["pdfinfo", "/opt/homebrew/bin/pdfinfo", "/usr/local/bin/pdfinfo"]:
        try:
            res = subprocess.run([cmd_path, filepath], capture_output=True, text=True, check=True)
            match = re.search(r"Pages:\s+(\d+)", res.stdout)
            if match:
                return int(match.group(1))
        except Exception:
            pass

    # 3. Thử dùng gs
    for gs_path in ["gs", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            cmd = [
                gs_path,
                "-q",
                "-dNODISPLAY",
                "-c",
                f"({filepath}) (r) file runpdfbegin pdfpagecount = quit"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = res.stdout.strip()
            if output.isdigit():
                return int(output)
        except Exception:
            pass

    return None

def check_pdf_pages_color(filepath):
    """
    Sử dụng Ghostscript với thiết bị inkcov để phân tích độ phủ mực CMYK của từng trang.
    Trả về danh sách boolean: True nếu trang đó có màu, False nếu là trắng đen (grayscale).
    Chỉ số của danh sách khớp với trang (1-indexed).
    """
    gs_executable = "gs"
    for path in ["gs", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            subprocess.run([path, "--version"], capture_output=True, check=True)
            gs_executable = path
            break
        except Exception:
            continue

    cmd = [
        gs_executable,
        "-q",
        "-o", "-",
        "-sDEVICE=inkcov",
        filepath
    ]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = res.stdout.strip().splitlines()
        
        pages_color = {}
        page_num = 1
        pattern = re.compile(r"^\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+CMYK\s+OK", re.IGNORECASE)
        
        for line in lines:
            match = pattern.match(line)
            if match:
                c, m, y, k = map(float, match.groups())
                # Dùng ngưỡng nhỏ 0.00001 để tránh các sai lệch nhiễu nhỏ khi chuyển đổi hệ màu
                is_color = (c > 0.00001) or (m > 0.00001) or (y > 0.00001)
                pages_color[page_num] = is_color
                page_num += 1
                
        return pages_color
    except Exception as e:
        current_app.logger.error("Failed to detect PDF page colors: %s", e)
        return None

def run_gs(input_path, output_path, first_page=None, last_page=None, to_gray=False):
    """
    Chạy lệnh Ghostscript để trích xuất trang và tùy chọn chuyển sang trắng đen (grayscale).
    """
    gs_executable = "gs"
    for path in ["gs", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            subprocess.run([path, "--version"], capture_output=True, check=True)
            gs_executable = path
            break
        except Exception:
            continue
            
    cmd = [
        gs_executable,
        "-sDEVICE=pdfwrite",
        "-dNOPAUSE",
        "-dBATCH",
    ]
    if to_gray:
        cmd.extend([
            "-sColorConversionStrategy=Gray",
            "-dProcessColorModel=/DeviceGray",
        ])
    if first_page is not None:
        cmd.append(f"-dFirstPage={first_page}")
    if last_page is not None:
        cmd.append(f"-dLastPage={last_page}")
        
    cmd.extend([
        f"-sOutputFile={output_path}",
        input_path
    ])
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res
    except subprocess.CalledProcessError as e:
        current_app.logger.error("Ghostscript failed. cmd=%s, stderr=%s, stdout=%s", cmd, e.stderr, e.stdout)
        raise RuntimeError(f"Lỗi xử lý PDF qua Ghostscript: {e.stderr or e.stdout or str(e)}")

@pdf_bp.route('/split', methods=['POST'])
def split_pdf():
    """
    Endpoint tải lên tệp PDF, thực hiện phân tách các trang dựa trên màu sắc:
    - Bìa riêng: trang đầu tiên (trang 1)
    - Tệp màu: chứa các trang còn lại có màu (C, M, Y > 0)
    - Tệp không màu: chứa các trang còn lại không có màu (chỉ có K), ép trắng đen.
    Tất cả các tệp sinh ra được đóng gói thành tệp ZIP tải về.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Không có tệp nào được tải lên."}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "Tệp tải lên không hợp lệ."}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Chỉ chấp nhận tệp định dạng .pdf."}), 400
        
    original_filename = file.filename
    base_name, _ = os.path.splitext(original_filename)
    
    # Xác định thư mục tạm bên trong thư mục temp của dự án
    project_temp_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        "temp"
    )
    os.makedirs(project_temp_dir, exist_ok=True)
    
    session_id = str(uuid.uuid4())
    work_dir = os.path.join(project_temp_dir, f"pdf_split_{session_id}")
    os.makedirs(work_dir, exist_ok=True)
    
    original_path = os.path.join(work_dir, "original.pdf")
    
    try:
        # Lưu tệp gốc
        file.save(original_path)
        
        # Đọc số trang
        num_pages = get_pdf_page_count(original_path)
        if num_pages is None:
            return jsonify({"error": "Không thể phân tích tệp PDF. Tệp có thể bị lỗi hoặc không đúng định dạng."}), 400
            
        if num_pages < 2:
            return jsonify({"error": "File PDF phải có ít nhất 2 trang để thực hiện tách file in."}), 400
            
        # Kiểm tra màu sắc từng trang
        pages_color = check_pdf_pages_color(original_path)
        if not pages_color:
            return jsonify({"error": "Không thể phân tích thông tin màu sắc của file PDF."}), 400
            
        # Phân loại trang từ trang thứ 2 trở đi
        color_page_indices = []
        gray_page_indices = []
        
        for p in range(2, num_pages + 1):
            if pages_color.get(p, True): # mặc định là có màu nếu không phân tích được
                color_page_indices.append(p)
            else:
                gray_page_indices.append(p)
                
        # Đường dẫn các tệp kết quả đầu ra
        cover_name = f"bìa-{base_name}.pdf"
        color_name = f"màu-{base_name}.pdf"
        gray_name = f"không màu-{base_name}.pdf"
        zip_name = f"in-{base_name}.zip"
        
        cover_path = os.path.join(work_dir, cover_name)
        color_path = os.path.join(work_dir, color_name)
        gray_path = os.path.join(work_dir, gray_name)
        zip_path = os.path.join(work_dir, zip_name)
        
        # Sử dụng pypdf để tách ghép trang
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(original_path)
        
        # 1. Trích xuất bìa (trang 1)
        cover_writer = PdfWriter()
        cover_writer.add_page(reader.pages[0])
        with open(cover_path, 'wb') as f:
            cover_writer.write(f)
            
        generated_files = [(cover_path, cover_name)]
        
        # 2. Trích xuất trang màu (nếu có)
        if color_page_indices:
            color_writer = PdfWriter()
            for p in color_page_indices:
                color_writer.add_page(reader.pages[p - 1]) # pypdf dùng 0-index
            with open(color_path, 'wb') as f:
                color_writer.write(f)
            generated_files.append((color_path, color_name))
            
        # 3. Trích xuất trang không màu (nếu có)
        if gray_page_indices:
            temp_gray_path = os.path.join(work_dir, "temp_gray.pdf")
            gray_writer = PdfWriter()
            for p in gray_page_indices:
                gray_writer.add_page(reader.pages[p - 1]) # pypdf dùng 0-index
            with open(temp_gray_path, 'wb') as f:
                gray_writer.write(f)
            # Ép chuyển đổi trắng đen triệt để bằng Ghostscript
            run_gs(temp_gray_path, gray_path, to_gray=True)
            generated_files.append((gray_path, gray_name))
            
        # Đóng gói ZIP các tệp được sinh ra
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for path, name in generated_files:
                zip_file.write(path, name)
            
        # Đọc file ZIP vào bộ nhớ đệm để giải phóng file trên đĩa
        with open(zip_path, 'rb') as fh:
            zip_data = io.BytesIO(fh.read())
        zip_data.seek(0)
        
        # Gửi file ZIP về cho client tải xuống
        return send_file(
            zip_data,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_name
        )
        
    except Exception as e:
        current_app.logger.error("Error in split_pdf: %s", traceback.format_exc())
        return jsonify({"error": f"Lỗi hệ thống khi xử lý PDF: {str(e)}"}), 500
        
    finally:
        # Xóa toàn bộ thư mục tạm và các tệp bên trong
        shutil.rmtree(work_dir, ignore_errors=True)
