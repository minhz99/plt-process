import os
import io
import re
import uuid
import shutil
import zipfile
import subprocess
import traceback
from flask import Blueprint, request, jsonify, send_file, current_app
from PIL import Image
import numpy as np

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

def check_pdf_pages_color_visually(filepath, work_dir, split_mode='normal'):
    """
    Renders PDF pages to PNG at 72 DPI and counts chromatic pixels.
    Returns a dictionary mapping page number (1-indexed) to boolean (True if page has color).
    """
    gs_executable = "gs"
    for path in ["gs", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            subprocess.run([path, "--version"], capture_output=True, check=True)
            gs_executable = path
            break
        except Exception:
            continue

    render_dir = os.path.join(work_dir, "render")
    os.makedirs(render_dir, exist_ok=True)
    
    cmd = [
        gs_executable,
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=png16m",
        "-r72",  # Use 72 DPI for better small text color retention
        f"-sOutputFile={render_dir}/page_%d.png",
        filepath
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        files = os.listdir(render_dir)
        
        pages_color = {}
        for f in files:
            if not f.startswith("page_") or not f.endswith(".png"):
                continue
            try:
                p_num = int(f.split('_')[1].split('.')[0])
                img_path = os.path.join(render_dir, f)
                with Image.open(img_path) as img:
                    arr = np.array(img)
                
                # Check pixel channel differences
                r = arr[:, :, 0].astype(int)
                g = arr[:, :, 1].astype(int)
                b = arr[:, :, 2].astype(int)
                
                diff_rg = np.abs(r - g)
                diff_gb = np.abs(g - b)
                diff_br = np.abs(b - r)
                
                # Count pixels where channel difference is > 10
                max_diff = np.max([diff_rg, diff_gb, diff_br], axis=0)
                colored_pixels = np.sum(max_diff > 10)
                total_pixels = r.size
                pct = (colored_pixels / total_pixels) * 100
                
                # Count printed pixels (brightness < 240)
                brightness = (r + g + b) // 3
                printed_pixels = np.sum(brightness < 240)
                colored_ratio_to_printed = (colored_pixels / max(1, printed_pixels)) * 100
                
                if split_mode == 'smart':
                    # Kiểu 2: Tách lọc dấu đỏ/vạch màu
                    # Trang có màu nếu:
                    # 1. Có màu rõ rệt (> 0.05% diện tích)
                    # 2. VÀ:
                    #    - Diện tích màu lớn (> 2.5% diện tích toàn trang)
                    #    - HOẶC tỷ lệ màu so với nội dung in cao (>= 20% - nghĩa là màu chữ/nội dung chính chứ không phải dấu đỏ/vạch chỉ dẫn đơn lẻ)
                    is_color = (pct > 0.05) and (pct > 2.5 or colored_ratio_to_printed >= 20.0)
                else:
                    # Kiểu 1: Tách thông thường
                    is_color = pct > 0.05
                    
                pages_color[p_num] = is_color
            except Exception as pe:
                current_app.logger.error("Failed parsing rendered page %s: %s", f, pe)
                
        return pages_color
    except Exception as e:
        current_app.logger.error("Failed visual PDF page color detection: %s", e)
        return None
    finally:
        shutil.rmtree(render_dir, ignore_errors=True)

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

def parse_page_exceptions(ex_str):
    """
    Parses a string of page numbers or page ranges (e.g. '5, 9, 10, 81-83')
    into a set of integer page numbers.
    """
    pages = set()
    if not ex_str:
        return pages
    # Replace common separators with comma
    ex_str = ex_str.replace(';', ',').replace(' ', ',')
    parts = ex_str.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                pages.update(range(start, end + 1))
            except ValueError:
                pass
        else:
            try:
                pages.add(int(part))
            except ValueError:
                pass
    return pages

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
            
        # Lấy ngoại lệ từ request
        gray_exceptions_str = request.form.get('gray_exceptions', '')
        color_exceptions_str = request.form.get('color_exceptions', '')
        
        gray_exceptions = parse_page_exceptions(gray_exceptions_str)
        color_exceptions = parse_page_exceptions(color_exceptions_str)
        
        # Kiểm tra màu sắc từng trang theo phương pháp dựng hình trực quan ('normal' mode)
        pages_color = check_pdf_pages_color_visually(original_path, work_dir, 'normal')
        
        # Fallback về phương pháp cũ (inkcov) nếu kiểm tra trực quan thất bại
        if not pages_color:
            current_app.logger.warning("Visual color check failed, falling back to inkcov.")
            pages_color = check_pdf_pages_color(original_path)
            
        if not pages_color:
            return jsonify({"error": "Không thể phân tích thông tin màu sắc của file PDF."}), 400
            
        # Phân loại trang từ trang thứ 2 trở đi
        color_page_indices = []
        gray_page_indices = []
        
        for p in range(2, num_pages + 1):
            is_color = pages_color.get(p, True) # mặc định là có màu nếu không phân tích được
            
            # Áp dụng ngoại lệ thủ công
            if p in gray_exceptions:
                is_color = False
            elif p in color_exceptions:
                is_color = True
                
            if is_color:
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
            gray_writer = PdfWriter()
            for p in gray_page_indices:
                gray_writer.add_page(reader.pages[p - 1]) # pypdf dùng 0-index
            with open(gray_path, 'wb') as f:
                gray_writer.write(f)
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
