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
    1. Sử dụng pypdfium2 (nhanh và chuẩn xác nhất).
    2. Sử dụng thư viện pypdf.
    3. Sử dụng pdfplumber.
    4. Sử dụng công cụ pdfinfo / Ghostscript (nếu được cài đặt).
    """
    # 1. Thử dùng pypdfium2
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(filepath)
        return len(pdf)
    except Exception as e:
        current_app.logger.warning("pypdfium2 page count failed: %s", e)

    # 2. Thử dùng pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        return len(reader.pages)
    except Exception as e:
        current_app.logger.warning("pypdf page count failed: %s", e)

    # 3. Thử dùng pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            return len(pdf.pages)
    except Exception as e:
        current_app.logger.warning("pdfplumber page count failed: %s", e)

    # 4. Thử dùng pdfinfo
    for cmd_path in ["pdfinfo", "/opt/homebrew/bin/pdfinfo", "/usr/local/bin/pdfinfo"]:
        try:
            res = subprocess.run([cmd_path, filepath.replace('\\', '/')], capture_output=True, text=True, check=True)
            match = re.search(r"Pages:\s+(\d+)", res.stdout)
            if match:
                return int(match.group(1))
        except Exception:
            pass

    # 5. Thử dùng gs
    for gs_path in ["gs", "gswin64c", "gswin32c", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            filepath_gs = filepath.replace('\\', '/')
            cmd = [
                gs_path,
                "-q",
                "-dNODISPLAY",
                "-c",
                f"({filepath_gs}) (r) file runpdfbegin pdfpagecount = quit"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = res.stdout.strip()
            if output.isdigit():
                return int(output)
        except Exception:
            pass

    return None

def analyze_image_color(img):
    """
    Phân tích một ảnh PIL để xác định xem trang có chứa màu sắc hay không (dựa trên độ lệch kênh RGB).
    
    Args:
        img (PIL.Image): Ảnh trang PDF cần kiểm tra.
        
    Returns:
        bool: True nếu trang có màu sắc, False nếu là grayscale/trắng đen.
    """
    arr = np.array(img.convert('RGB'), dtype=np.int32)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    diff = max_c - min_c
    
    # Loại trừ nền giấy trắng tinh (min_c >= 250) và mực đen/rất tối (max_c <= 25)
    valid_mask = (max_c > 25) & (min_c < 250)
    chromatic_count = int(np.sum(valid_mask & (diff >= 18)))
    vivid_count = int(np.sum(valid_mask & (diff >= 28)))
    
    # Đếm số pixel có mực in (độ sáng < 240)
    brightness = (r + g + b) // 3
    printed_count = int(np.sum(brightness < 240))
    
    # Tiêu chí nhận diện màu sắc:
    # 1. Có ít nhất 15 pixel màu sắc nét (vivid - bắt được cả các chữ/con dấu/icon màu nhỏ).
    # 2. Hoặc có ít nhất 40 pixel có sắc độ lệch kênh màu.
    # 3. Hoặc tỷ lệ pixel màu so với nội dung in đạt >= 0.1% (kèm tối thiểu 10 pixel).
    is_color = (
        (vivid_count >= 15) or 
        (chromatic_count >= 40) or 
        (printed_count > 0 and chromatic_count >= 10 and (chromatic_count / printed_count) >= 0.001)
    )
    return is_color

def detect_pdf_page_colors_pdfium(filepath):
    """
    Sử dụng engine pypdfium2 (Google PDFium) để dựng hình và phân tích màu sắc trực tiếp trong bộ nhớ.
    Trả về dict {page_num (1-indexed): bool}.
    """
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(filepath)
    pages_color = {}
    
    for i, page in enumerate(pdf):
        p_num = i + 1
        # Render với tỉ lệ 1.2x (~86 DPI) vừa đảm bảo độ chi tiết cho text nhỏ vừa tối ưu tốc độ
        img = page.render(scale=1.2).to_pil()
        pages_color[p_num] = analyze_image_color(img)
        
    return pages_color

def detect_pdf_page_colors_pdfplumber(filepath):
    """
    Phương thức dự phòng 1: Sử dụng pdfplumber để dựng hình từng trang và phân tích màu.
    """
    import pdfplumber
    pages_color = {}
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            p_num = i + 1
            img = page.to_image(resolution=86).original
            pages_color[p_num] = analyze_image_color(img)
    return pages_color

def check_pdf_pages_color_gs(filepath):
    """
    Phương thức dự phòng 2: Sử dụng Ghostscript với thiết bị inkcov để phân tích CMYK.
    """
    gs_executable = None
    for path in ["gs", "gswin64c", "gswin32c", "/usr/local/bin/gs", "/opt/homebrew/bin/gs"]:
        try:
            subprocess.run([path, "--version"], capture_output=True, check=True)
            gs_executable = path
            break
        except Exception:
            continue

    if not gs_executable:
        return None

    cmd = [
        gs_executable,
        "-q",
        "-o", "-",
        "-sDEVICE=inkcov",
        filepath.replace('\\', '/')
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
                is_color = (c > 0.00001) or (m > 0.00001) or (y > 0.00001)
                pages_color[page_num] = is_color
                page_num += 1
                
        return pages_color
    except Exception as e:
        current_app.logger.warning("Ghostscript inkcov color check failed: %s", e)
        return None

def detect_pdf_page_colors(filepath):
    """
    Bộ nhận diện màu sắc thông minh đa tầng:
    1. Ưu tiên pypdfium2 (nhanh, chuẩn xác, độc lập không phụ thuộc phần mềm ngoài).
    2. Dự phòng 1: pdfplumber.
    3. Dự phòng 2: Ghostscript (nếu máy có cài).
    """
    # 1. pypdfium2
    try:
        colors = detect_pdf_page_colors_pdfium(filepath)
        if colors:
            return colors
    except Exception as e:
        current_app.logger.warning("pypdfium2 color detection failed: %s", e)

    # 2. pdfplumber
    try:
        colors = detect_pdf_page_colors_pdfplumber(filepath)
        if colors:
            return colors
    except Exception as e:
        current_app.logger.warning("pdfplumber color detection failed: %s", e)

    # 3. Ghostscript
    try:
        colors = check_pdf_pages_color_gs(filepath)
        if colors:
            return colors
    except Exception as e:
        current_app.logger.warning("Ghostscript color detection failed: %s", e)

    return None

def parse_page_exceptions(ex_str):
    """
    Phân tích chuỗi số trang hoặc dải trang (ví dụ: '5, 9, 10, 81-83')
    thành một set các số nguyên đại diện cho trang (1-indexed).
    """
    pages = set()
    if not ex_str:
        return pages
    # Thay thế các dấu phân cách phổ biến bằng dấu phẩy
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
    - Bìa riêng: trang đầu tiên (trang 1) nếu bật tách bìa
    - Tệp màu: chứa các trang nội dung có màu sắc
    - Tệp không màu: chứa các trang nội dung hoàn toàn trắng đen (grayscale)
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
    
    custom_filename = request.form.get('custom_filename', '').strip()
    if custom_filename:
        if custom_filename.lower().endswith('.zip'):
            custom_filename = custom_filename[:-4]
        base_name = custom_filename
    
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
        two_sided = request.form.get('two_sided', 'false').lower() in ('true', '1', 'yes')
        separate_cover = request.form.get('separate_cover', 'true').lower() in ('true', '1', 'yes')
        
        gray_exceptions = parse_page_exceptions(gray_exceptions_str)
        color_exceptions = parse_page_exceptions(color_exceptions_str)
        
        # Nhận diện màu sắc từng trang bằng engine đa tầng
        pages_color = detect_pdf_page_colors(original_path)
            
        if not pages_color:
            return jsonify({"error": "Không thể phân tích thông tin màu sắc của file PDF."}), 400
            
        # Phân loại trang
        color_page_indices = []
        gray_page_indices = []
        
        start_page = 2 if separate_cover else 1
        
        for p in range(start_page, num_pages + 1):
            if separate_cover and two_sided and p == 2:
                continue
                
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
        
        # Áp dụng quy tắc 2-sided: nếu 1 trong 2 mặt giấy có màu -> cả 2 mặt đều vào file màu
        # 1 tờ bao gồm trang lẻ (mặt trước) và trang chẵn (mặt sau).
        # Ví dụ: (1, 2), (3, 4), (5, 6)...
        if two_sided:
            new_color_indices = set(color_page_indices)
            for p in range(start_page, num_pages + 1):
                if separate_cover and p == 2:
                    continue
                    
                # Tìm trang cùng cặp với p (trang lẻ ghép trang chẵn, trang chẵn ghép trang lẻ)
                pair_p = p + 1 if p % 2 != 0 else p - 1
                
                # Nếu trang p có màu, ép trang cặp (nếu nằm trong khoảng hợp lệ) vào tệp màu
                if p in color_page_indices and start_page <= pair_p <= num_pages:
                    new_color_indices.add(pair_p)
            
            # Sắp xếp lại danh sách để đảm bảo thứ tự trang đúng
            color_page_indices = sorted(list(new_color_indices))
            gray_page_indices = [x for x in gray_page_indices if x not in color_page_indices]
            gray_page_indices.sort()
                
        # Đường dẫn các tệp kết quả đầu ra
        cover_name = f"00-bia-{base_name}.pdf"
        color_name = f"01-mau-{base_name}.pdf"
        gray_name = f"02-khong-mau-{base_name}.pdf"
        zip_name = f"{base_name}.zip" if custom_filename else f"in-{base_name}.zip"
        
        cover_path = os.path.join(work_dir, cover_name)
        color_path = os.path.join(work_dir, color_name)
        gray_path = os.path.join(work_dir, gray_name)
        zip_path = os.path.join(work_dir, zip_name)
        
        # Sử dụng pypdf để tách ghép trang
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(original_path)
        
        generated_files = []
        
        if separate_cover:
            # 1. Trích xuất bìa (trang 1)
            cover_writer = PdfWriter()
            cover_writer.add_page(reader.pages[0])
            with open(cover_path, 'wb') as f:
                cover_writer.write(f)
            generated_files.append((cover_path, cover_name))
            
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
