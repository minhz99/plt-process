# -*- coding: utf-8 -*-
"""
OCR Engine module for extracting text from images, PDFs, and ZIP archives.
Supports DeepDoc / DBNet text line detection + VietOCR Transformer recognition,
with RapidOCR as fast engine option.
"""
import io
import os
import zipfile
import numpy as np
from PIL import Image

_RAPID_OCR_INSTANCE = None
_VIETOCR_INSTANCE = None

def get_ocr_engine():
    """Lazy singleton loader for text detection / RapidOCR engine."""
    global _RAPID_OCR_INSTANCE
    if _RAPID_OCR_INSTANCE is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _RAPID_OCR_INSTANCE = RapidOCR()
        except Exception:
            _RAPID_OCR_INSTANCE = None
    return _RAPID_OCR_INSTANCE

def get_vietocr_engine():
    """Lazy singleton loader for VietOCR Transformer recognition engine."""
    global _VIETOCR_INSTANCE
    if _VIETOCR_INSTANCE is None:
        try:
            from vietocr.tool.config import Cfg
            from vietocr.tool.predictor import Predictor
            config = Cfg.load_config_from_name('vgg_transformer')
            config['device'] = 'cpu'
            config['predictor']['beamsearch'] = False
            _VIETOCR_INSTANCE = Predictor(config)
        except Exception:
            _VIETOCR_INSTANCE = None
    return _VIETOCR_INSTANCE

def is_blank_page(img: Image.Image, ink_threshold: float = 0.001) -> bool:
    """
    Kiểm tra trang có phải trang trắng / rỗng hay không.
    ink_threshold: Tỷ lệ pixel mực (tối) trên tổng số pixel.
    """
    try:
        gray = img.convert('L')
        arr = np.array(gray)
        ink_pixels = np.sum(arr < 200)
        total_pixels = arr.size
        ratio = ink_pixels / max(total_pixels, 1)
        return ratio < ink_threshold
    except Exception:
        return False

def ocr_image(image_input, engine_type: str = 'vietocr') -> str:
    """
    Nhận diện văn bản từ 1 ảnh (PIL Image, numpy array hoặc bytes).
    Sử dụng DeepDoc/DBNet detector + VietOCR Transformer hoặc RapidOCR.
    """
    detector = get_ocr_engine()
    if detector is None:
        return "[Lỗi: Chưa khởi tạo được bộ dò văn bản OCR]"

    if isinstance(image_input, (bytes, bytearray)):
        image_input = Image.open(io.BytesIO(image_input))

    if isinstance(image_input, Image.Image):
        if image_input.mode != 'RGB':
            pil_img = image_input.convert('RGB')
        else:
            pil_img = image_input
        np_img = np.array(pil_img)
    else:
        np_img = image_input
        pil_img = Image.fromarray(np_img)

    try:
        ocr_result, _ = detector(np_img)
        if not ocr_result:
            return ""

        # Nếu chọn engine VietOCR
        if engine_type == 'vietocr':
            viet_engine = get_vietocr_engine()
            if viet_engine is not None:
                lines = []
                for item in ocr_result:
                    if len(item) < 2 or not item[1]:
                        continue
                    box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    xs = [pt[0] for pt in box]
                    ys = [pt[1] for pt in box]
                    min_x, max_x = max(0, int(min(xs))), min(pil_img.width, int(max(xs)))
                    min_y, max_y = max(0, int(min(ys))), min(pil_img.height, int(max(ys)))
                    
                    # Nếu crop hợp lệ (chiều cao >= 6px, chiều rộng >= 6px)
                    if (max_x - min_x) >= 6 and (max_y - min_y) >= 6:
                        crop = pil_img.crop((min_x, min_y, max_x, max_y))
                        try:
                            pred_text = viet_engine.predict(crop).strip()
                            lines.append(pred_text if pred_text else item[1].strip())
                        except Exception:
                            lines.append(item[1].strip())
                    else:
                        lines.append(item[1].strip())
                return "\n".join(lines)

        # Fallback hoặc khi chọn RapidOCR
        lines = [item[1].strip() for item in ocr_result if len(item) >= 2 and item[1]]
        return "\n".join(lines)
    except Exception as e:
        return f"[Lỗi OCR ảnh: {e}]"

def ocr_pdf(pdf_bytes_or_path, resolution: int = 150, skip_blank: bool = True, engine_type: str = 'vietocr') -> list:
    """
    Nhận diện văn bản từ file PDF.
    Trả về danh sách dict: [{'page': 1, 'text': '...', 'is_blank': False}, ...]
    """
    import pdfplumber

    results = []
    stream = io.BytesIO(pdf_bytes_or_path) if isinstance(pdf_bytes_or_path, (bytes, bytearray)) else pdf_bytes_or_path

    with pdfplumber.open(stream) as doc:
        total_pages = len(doc.pages)
        for p_idx, page in enumerate(doc.pages, 1):
            try:
                native_text = page.extract_text() or ''
                if len(native_text.strip()) > 30:
                    results.append({
                        'page': p_idx,
                        'total_pages': total_pages,
                        'text': native_text.strip(),
                        'is_blank': False,
                        'source_type': 'digital_pdf'
                    })
                    continue

                img_obj = page.to_image(resolution=resolution)
                pil_img = img_obj.original

                if skip_blank and is_blank_page(pil_img):
                    results.append({
                        'page': p_idx,
                        'total_pages': total_pages,
                        'text': '--- [Trang trắng / Bỏ qua] ---',
                        'is_blank': True,
                        'source_type': 'blank'
                    })
                    continue

                page_text = ocr_image(pil_img, engine_type=engine_type)
                results.append({
                    'page': p_idx,
                    'total_pages': total_pages,
                    'text': page_text.strip(),
                    'is_blank': False,
                    'source_type': 'ocr_scan'
                })
            except Exception as e:
                results.append({
                    'page': p_idx,
                    'total_pages': total_pages,
                    'text': f'[Lỗi đọc trang {p_idx}: {e}]',
                    'is_blank': False,
                    'source_type': 'error'
                })

    return results

def ocr_archive_or_file(filename: str, file_bytes: bytes, resolution: int = 150, skip_blank: bool = True, engine_type: str = 'vietocr') -> list:
    """
    Xử lý file bất kỳ (ảnh, PDF, ZIP).
    Trả về danh sách kết quả cho từng file bên trong.
    """
    lower_name = filename.lower()
    items_out = []

    if lower_name.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            for member in z.namelist():
                if member.endswith('/') or '__MACOSX' in member or os.path.basename(member).startswith('.'):
                    continue
                m_lower = member.lower()
                m_bytes = z.read(member)

                if m_lower.endswith('.zip'):
                    sub_items = ocr_archive_or_file(member, m_bytes, resolution=resolution, skip_blank=skip_blank, engine_type=engine_type)
                    items_out.extend(sub_items)
                elif m_lower.endswith('.pdf'):
                    pages = ocr_pdf(m_bytes, resolution=resolution, skip_blank=skip_blank, engine_type=engine_type)
                    full_text = '\n\n'.join([f'=== [Trang {p["page"]}/{p["total_pages"]}] ===\n' + p['text'] for p in pages if not p.get('is_blank')])
                    items_out.append({'filename': member, 'pages': pages, 'full_text': full_text})
                elif any(m_lower.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                    txt = ocr_image(m_bytes, engine_type=engine_type)
                    items_out.append({
                        'filename': member,
                        'pages': [{'page': 1, 'total_pages': 1, 'text': txt, 'is_blank': False, 'source_type': 'ocr_image'}],
                        'full_text': txt
                    })

    elif lower_name.endswith('.pdf'):
        pages = ocr_pdf(file_bytes, resolution=resolution, skip_blank=skip_blank, engine_type=engine_type)
        full_text = '\n\n'.join([f'=== [Trang {p["page"]}/{p["total_pages"]}] ===\n' + p['text'] for p in pages if not p.get('is_blank')])
        items_out.append({'filename': filename, 'pages': pages, 'full_text': full_text})

    elif any(lower_name.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        txt = ocr_image(file_bytes, engine_type=engine_type)
        items_out.append({
            'filename': filename,
            'pages': [{'page': 1, 'total_pages': 1, 'text': txt, 'is_blank': False, 'source_type': 'ocr_image'}],
            'full_text': txt
        })

    return items_out
