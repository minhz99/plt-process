import io
import os
import json
import uuid
import base64
import zipfile
import math

from flask import Blueprint, request, jsonify, send_file, current_app
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import qrcode
import qrcode.image.svg
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
)

qr_bp = Blueprint('qr_bp', __name__)

# ── Ánh xạ mức sửa lỗi ─────────────────────────────────────────────────────
ERROR_LEVELS = {
    'L': ERROR_CORRECT_L,
    'M': ERROR_CORRECT_M,
    'Q': ERROR_CORRECT_Q,
    'H': ERROR_CORRECT_H,
}


# ── Tiện ích định dạng dữ liệu theo loại ────────────────────────────────────

def _format_data(data: str, data_type: str, extra: dict | None = None) -> str:
    """
    Định dạng dữ liệu thô theo chuẩn mã QR cho từng loại nội dung.

    Args:
        data: Nội dung chính (URL, text, email, phone…).
        data_type: Loại dữ liệu (url, text, email, phone, wifi, vcard, sms).
        extra: Thông tin bổ sung cho các loại đặc biệt (wifi, vcard, sms).

    Returns:
        str: Chuỗi đã được định dạng đúng chuẩn QR.
    """
    extra = extra or {}

    if data_type == 'url':
        if data and not data.startswith(('http://', 'https://', 'ftp://')):
            return 'https://' + data
        return data

    if data_type == 'email':
        subject = extra.get('subject', '')
        body = extra.get('body', '')
        mailto = f'mailto:{data}'
        params = []
        if subject:
            params.append(f'subject={subject}')
        if body:
            params.append(f'body={body}')
        if params:
            mailto += '?' + '&'.join(params)
        return mailto

    if data_type == 'phone':
        return f'tel:{data}'

    if data_type == 'sms':
        body = extra.get('body', '')
        sms = f'sms:{data}'
        if body:
            sms += f'?body={body}'
        return sms

    if data_type == 'wifi':
        ssid = data
        password = extra.get('password', '')
        encryption = extra.get('encryption', 'WPA')
        hidden = extra.get('hidden', False)
        hidden_str = 'true' if hidden else 'false'
        return f'WIFI:T:{encryption};S:{ssid};P:{password};H:{hidden_str};;'

    if data_type == 'vcard':
        name = data
        phone = extra.get('phone', '')
        email = extra.get('email', '')
        org = extra.get('org', '')
        title = extra.get('title', '')
        url = extra.get('url', '')
        address = extra.get('address', '')

        lines = ['BEGIN:VCARD', 'VERSION:3.0']
        lines.append(f'FN:{name}')
        if phone:
            lines.append(f'TEL:{phone}')
        if email:
            lines.append(f'EMAIL:{email}')
        if org:
            lines.append(f'ORG:{org}')
        if title:
            lines.append(f'TITLE:{title}')
        if url:
            lines.append(f'URL:{url}')
        if address:
            lines.append(f'ADR:{address}')
        lines.append('END:VCARD')
        return '\n'.join(lines)

    # text hoặc bất kỳ loại nào khác → trả về nguyên bản
    return data


def _hex_to_rgb(hex_color: str, default: tuple = (0, 0, 0)) -> tuple:
    """Chuyển đổi mã màu HEX sang tuple RGB."""
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return default


def _hex_to_rgba(hex_color: str, alpha: int = 255, default: tuple = (0, 0, 0, 255)) -> tuple:
    """Chuyển đổi mã màu HEX sang tuple RGBA."""
    rgb = _hex_to_rgb(hex_color, default[:3])
    return (*rgb, alpha)


# ── Gradient ─────────────────────────────────────────────────────────────────

def _apply_gradient(img: Image.Image, color1: tuple, color2: tuple) -> Image.Image:
    """
    Áp dụng gradient 2 màu lên các pixel foreground của mã QR.
    Gradient chạy từ trên xuống dưới.

    Args:
        img: Ảnh QR dạng RGBA.
        color1: Tuple RGB màu đầu (trên).
        color2: Tuple RGB màu cuối (dưới).

    Returns:
        PIL.Image.Image: Ảnh QR với gradient đã áp dụng.
    """
    w, h = img.size
    pixels = img.load()

    # Xác định ngưỡng — pixel foreground là pixel tối (luminance < 128)
    # so với background (pixel sáng)
    for y in range(h):
        t = y / max(h - 1, 1)  # 0.0 → 1.0
        gr = int(color1[0] + (color2[0] - color1[0]) * t)
        gg = int(color1[1] + (color2[1] - color1[1]) * t)
        gb = int(color1[2] + (color2[2] - color1[2]) * t)
        for x in range(w):
            r, g, b, a = pixels[x, y]
            # Pixel foreground: luminance thấp (tối)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 128 and a > 0:
                pixels[x, y] = (gr, gg, gb, a)

    return img


# ── Logo embedding với options nâng cao ──────────────────────────────────────

def _embed_logo(
    img: Image.Image,
    logo_file,
    size: int,
    logo_frame: str = 'rounded',
    logo_opacity: float = 1.0,
    logo_scale: float = 0.25,
    logo_bg_color: str = '#ffffff',
    logo_bg_transparent: bool = False,
) -> Image.Image:
    """
    Chèn logo vào giữa mã QR với các tuỳ chọn khung, opacity, kích thước.

    Args:
        img: Ảnh QR dạng RGBA.
        logo_file: File logo (file-like object).
        size: Kích thước ảnh QR (px).
        logo_frame: Kiểu khung: 'none', 'rounded', 'circle', 'square', 'shadow'.
        logo_opacity: Độ mờ 0.1–1.0 (< 1.0 = hiệu ứng dấu chìm).
        logo_scale: Tỉ lệ logo so với QR (0.1–0.35).
        logo_bg_color: Màu nền khung logo (HEX).
        logo_bg_transparent: Nếu True, khung logo có nền trong suốt.

    Returns:
        PIL.Image.Image: Ảnh QR với logo đã chèn.
    """
    try:
        logo = Image.open(logo_file).convert('RGBA')
    except Exception:
        return img

    # Scale logo
    max_logo_size = int(size * max(0.1, min(0.35, logo_scale)))
    logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)

    # Áp dụng opacity
    opacity = max(0.1, min(1.0, logo_opacity))
    if opacity < 1.0:
        alpha_int = int(255 * opacity)
        # Nhân alpha channel hiện tại với opacity
        r, g, b, a = logo.split()
        a = a.point(lambda p: int(p * opacity))
        logo = Image.merge('RGBA', (r, g, b, a))

    padding = 8
    bg_w = logo.width + padding * 2
    bg_h = logo.height + padding * 2

    if logo_frame == 'none':
        # Không khung — dán logo trực tiếp
        composite = logo
        pos_x = (size - logo.width) // 2
        pos_y = (size - logo.height) // 2
        img.paste(composite, (pos_x, pos_y), composite)
        return img

    # Tạo nền khung
    if logo_bg_transparent:
        bg_color = (255, 255, 255, 0)
    else:
        bg_color = _hex_to_rgba(logo_bg_color, 255, (255, 255, 255, 255))

    logo_bg = Image.new('RGBA', (bg_w, bg_h), bg_color)

    # Tạo mask theo kiểu khung
    mask = Image.new('L', (bg_w, bg_h), 0)
    draw = ImageDraw.Draw(mask)

    if logo_frame == 'circle':
        draw.ellipse([(0, 0), (bg_w - 1, bg_h - 1)], fill=255)
    elif logo_frame == 'square':
        draw.rectangle([(0, 0), (bg_w - 1, bg_h - 1)], fill=255)
    elif logo_frame in ('rounded', 'shadow'):
        radius = min(bg_w, bg_h) // 6
        draw.rounded_rectangle(
            [(0, 0), (bg_w - 1, bg_h - 1)],
            radius=radius,
            fill=255,
        )
    else:
        # Fallback: rounded
        radius = min(bg_w, bg_h) // 6
        draw.rounded_rectangle(
            [(0, 0), (bg_w - 1, bg_h - 1)],
            radius=radius,
            fill=255,
        )

    logo_bg.putalpha(mask)

    # Dán logo lên nền khung
    # Nếu khung tròn, cần crop logo theo mask tròn
    if logo_frame == 'circle':
        logo_mask = Image.new('L', logo.size, 0)
        logo_draw = ImageDraw.Draw(logo_mask)
        logo_draw.ellipse([(0, 0), (logo.width - 1, logo.height - 1)], fill=255)
        # Kết hợp alpha channel gốc với mask tròn
        if logo.mode == 'RGBA':
            orig_alpha = logo.split()[3]
            combined = Image.new('L', logo.size, 0)
            combined_pixels = combined.load()
            orig_pixels = orig_alpha.load()
            mask_pixels = logo_mask.load()
            for y in range(logo.height):
                for x in range(logo.width):
                    combined_pixels[x, y] = min(orig_pixels[x, y], mask_pixels[x, y])
            logo.putalpha(combined)
        logo_bg.paste(logo, (padding, padding), logo)
    else:
        logo_bg.paste(logo, (padding, padding), logo)

    # Hiệu ứng bóng đổ
    if logo_frame == 'shadow':
        shadow_offset = 4
        shadow_blur = 8
        shadow = Image.new('RGBA', (bg_w + shadow_offset * 2 + shadow_blur * 2,
                                     bg_h + shadow_offset * 2 + shadow_blur * 2), (0, 0, 0, 0))
        shadow_mask = Image.new('L', shadow.size, 0)
        sd = ImageDraw.Draw(shadow_mask)
        radius = min(bg_w, bg_h) // 6
        sd.rounded_rectangle(
            [(shadow_blur, shadow_blur + shadow_offset),
             (shadow_blur + bg_w - 1, shadow_blur + shadow_offset + bg_h - 1)],
            radius=radius,
            fill=80,
        )
        shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
        shadow.putalpha(shadow_mask)

        # Dán logo_bg lên shadow
        shadow.paste(logo_bg, (shadow_blur, shadow_blur), logo_bg)

        pos_x = (size - shadow.width) // 2
        pos_y = (size - shadow.height) // 2
        img.paste(shadow, (pos_x, pos_y), shadow)
        return img

    # Dán vào giữa QR
    pos_x = (size - bg_w) // 2
    pos_y = (size - bg_h) // 2
    img.paste(logo_bg, (pos_x, pos_y), logo_bg)

    return img


# ── Label text ───────────────────────────────────────────────────────────────

def _add_label(img: Image.Image, text: str, fg_color: tuple, bg_color: tuple) -> Image.Image:
    """
    Thêm dòng chữ nhãn phía dưới mã QR.

    Args:
        img: Ảnh QR dạng RGBA.
        text: Nội dung nhãn.
        fg_color: Màu chữ RGB.
        bg_color: Màu nền RGB/RGBA.

    Returns:
        PIL.Image.Image: Ảnh mới với nhãn phía dưới.
    """
    if not text.strip():
        return img

    w = img.width
    label_height = 40
    font_size = max(14, w // 25)

    # Tìm font — thử nhiều hệ thống
    font = None
    font_paths = [
        # Windows
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/tahoma.ttf',
        # Linux
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf',
        # macOS
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
        label_height = 24

    # Đo chiều cao text thực tế
    temp_draw = ImageDraw.Draw(img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_h = bbox[3] - bbox[1]
    label_height = text_h + 16

    # Tạo canvas mới mở rộng xuống dưới
    bg_rgba = (*bg_color[:3], bg_color[3] if len(bg_color) > 3 else 255)
    new_img = Image.new('RGBA', (w, img.height + label_height), bg_rgba)
    new_img.paste(img, (0, 0), img)

    # Vẽ chữ
    draw = ImageDraw.Draw(new_img)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    tx = (w - text_w) // 2
    ty = img.height + (label_height - text_h) // 2
    draw.text((tx, ty), text, fill=(*fg_color[:3], 255), font=font)

    return new_img


# ── Main QR generation ───────────────────────────────────────────────────────

def _generate_qr_image(
    data: str,
    size: int = 400,
    fg_color: str = '#000000',
    bg_color: str = '#ffffff',
    error_correction: str = 'H',
    logo_file=None,
    # Logo options
    logo_frame: str = 'rounded',
    logo_opacity: float = 1.0,
    logo_scale: float = 0.25,
    logo_bg_color: str = '#ffffff',
    logo_bg_transparent: bool = False,
    # Advanced
    fg_color2: str = '',
    label_text: str = '',
    transparent_bg: bool = False,
) -> Image.Image:
    """
    Tạo ảnh mã QR dưới dạng PIL Image với đầy đủ tuỳ chỉnh.

    Args:
        data: Nội dung cần mã hoá.
        size: Kích thước ảnh đầu ra (px).
        fg_color: Màu foreground (HEX).
        bg_color: Màu background (HEX).
        error_correction: Mức sửa lỗi (L/M/Q/H).
        logo_file: File logo (file-like object hoặc None).
        logo_frame: Kiểu khung logo.
        logo_opacity: Độ mờ logo (0.1–1.0).
        logo_scale: Tỉ lệ logo so với QR.
        logo_bg_color: Màu nền khung logo.
        logo_bg_transparent: Nền khung logo trong suốt.
        fg_color2: Màu gradient thứ 2 (HEX, rỗng = không gradient).
        label_text: Nhãn chữ dưới QR.
        transparent_bg: Nền QR trong suốt.

    Returns:
        PIL.Image.Image: Ảnh mã QR.
    """
    ec = ERROR_LEVELS.get(error_correction.upper(), ERROR_CORRECT_H)
    fg = _hex_to_rgb(fg_color, (0, 0, 0))

    if transparent_bg:
        bg = (255, 255, 255, 0)
        bg_for_label = (255, 255, 255, 0)
    else:
        bg = _hex_to_rgb(bg_color, (255, 255, 255))
        bg_for_label = bg

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg, back_color=bg).convert('RGBA')

    # Nền trong suốt: thay thế pixel nền bằng transparent
    if transparent_bg:
        bg_rgb = _hex_to_rgb(bg_color, (255, 255, 255))
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                # Pixel nền: gần trắng hoặc gần màu bg
                if (abs(r - bg_rgb[0]) < 30 and abs(g - bg_rgb[1]) < 30 and abs(b - bg_rgb[2]) < 30):
                    pixels[x, y] = (r, g, b, 0)

    # Resize đến kích thước mong muốn
    if img.width != size or img.height != size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)

    # Áp dụng gradient nếu có màu thứ 2
    if fg_color2 and fg_color2.strip() and fg_color2 != fg_color:
        color2 = _hex_to_rgb(fg_color2, fg)
        img = _apply_gradient(img, fg, color2)

    # Chèn logo nếu có
    if logo_file is not None:
        img = _embed_logo(
            img, logo_file, size,
            logo_frame=logo_frame,
            logo_opacity=logo_opacity,
            logo_scale=logo_scale,
            logo_bg_color=logo_bg_color,
            logo_bg_transparent=logo_bg_transparent,
        )

    # Thêm nhãn chữ
    if label_text and label_text.strip():
        img = _add_label(img, label_text.strip(), fg, bg_for_label)

    return img


def _generate_qr_svg(
    data: str,
    fg_color: str = '#000000',
    bg_color: str = '#ffffff',
    error_correction: str = 'H',
) -> bytes:
    """
    Tạo mã QR dưới dạng SVG.

    Args:
        data: Nội dung cần mã hoá.
        fg_color: Màu foreground (HEX).
        bg_color: Màu background (HEX).
        error_correction: Mức sửa lỗi (L/M/Q/H).

    Returns:
        bytes: Nội dung SVG.
    """
    ec = ERROR_LEVELS.get(error_correction.upper(), ERROR_CORRECT_H)

    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=10,
        border=4,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fg_color, back_color=bg_color)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()


# ── Parse logo + advanced options từ request ─────────────────────────────────

def _parse_logo_options(form):
    """Trích xuất các tuỳ chọn logo từ form request."""
    return {
        'logo_frame': form.get('logo_frame', 'rounded').strip().lower(),
        'logo_opacity': _safe_float(form.get('logo_opacity'), 1.0, 0.1, 1.0),
        'logo_scale': _safe_float(form.get('logo_scale'), 0.25, 0.1, 0.35),
        'logo_bg_color': form.get('logo_bg_color', '#ffffff').strip(),
        'logo_bg_transparent': form.get('logo_bg_transparent', 'false').strip().lower() == 'true',
    }


def _parse_advanced_options(form):
    """Trích xuất các tuỳ chọn nâng cao từ form request."""
    return {
        'fg_color2': form.get('fg_color2', '').strip(),
        'label_text': form.get('label_text', '').strip(),
        'transparent_bg': form.get('transparent_bg', 'false').strip().lower() == 'true',
    }


# ══════════════════════════════════════════════════════════════════════════════
#  API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@qr_bp.route('/generate', methods=['POST'])
def generate():
    """
    Tạo mã QR đơn lẻ và trả về file ảnh.

    Form fields:
        data              – Nội dung chính
        data_type         – Loại: url | text | email | phone | wifi | vcard | sms
        extra             – JSON chứa thông tin bổ sung
        size              – Kích thước pixel (mặc định 400)
        fg_color          – Màu foreground HEX
        bg_color          – Màu background HEX
        error_correction  – L | M | Q | H
        format            – png | svg
        logo              – File ảnh logo (tùy chọn)
        logo_frame        – none | rounded | circle | square | shadow
        logo_opacity      – 0.1–1.0
        logo_scale        – 0.1–0.35
        logo_bg_color     – Màu nền khung logo HEX
        logo_bg_transparent – true | false
        fg_color2         – Màu gradient thứ 2 HEX
        label_text        – Nhãn chữ dưới QR
        transparent_bg    – true | false
    """
    data = request.form.get('data', '').strip()
    if not data:
        return jsonify({'error': 'Vui lòng nhập nội dung cho mã QR'}), 400

    data_type = request.form.get('data_type', 'text').strip().lower()
    extra_str = request.form.get('extra', '{}')
    try:
        extra = json.loads(extra_str) if extra_str else {}
    except json.JSONDecodeError:
        extra = {}

    size = _safe_int(request.form.get('size'), 400, 50, 2000)
    fg_color = request.form.get('fg_color', '#000000').strip()
    bg_color = request.form.get('bg_color', '#ffffff').strip()
    error_correction = request.form.get('error_correction', 'H').strip().upper()
    output_format = request.form.get('format', 'png').strip().lower()

    formatted = _format_data(data, data_type, extra)

    if output_format == 'svg':
        svg_bytes = _generate_qr_svg(formatted, fg_color, bg_color, error_correction)
        buf = io.BytesIO(svg_bytes)
        return send_file(
            buf,
            mimetype='image/svg+xml',
            as_attachment=True,
            download_name='qrcode.svg',
        )

    # PNG — parse logo + advanced options
    logo_opts = _parse_logo_options(request.form)
    adv_opts = _parse_advanced_options(request.form)
    logo_file = request.files.get('logo')

    img = _generate_qr_image(
        formatted,
        size=size,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=error_correction,
        logo_file=logo_file,
        **logo_opts,
        **adv_opts,
    )

    buf = io.BytesIO()
    if adv_opts.get('transparent_bg'):
        img.save(buf, format='PNG', optimize=True)
    else:
        img.convert('RGB').save(buf, format='PNG', optimize=True)
    buf.seek(0)

    return send_file(
        buf,
        mimetype='image/png',
        as_attachment=True,
        download_name='qrcode.png',
    )


@qr_bp.route('/preview', methods=['POST'])
def preview():
    """
    Xem trước mã QR — trả về base64 data URI.

    Nhận cùng tham số như /generate, trả về JSON:
        { "image": "data:image/png;base64,..." }
    """
    data = request.form.get('data', '').strip()
    if not data:
        return jsonify({'error': 'Nội dung trống'}), 400

    data_type = request.form.get('data_type', 'text').strip().lower()
    extra_str = request.form.get('extra', '{}')
    try:
        extra = json.loads(extra_str) if extra_str else {}
    except json.JSONDecodeError:
        extra = {}

    size = _safe_int(request.form.get('size'), 400, 50, 2000)
    fg_color = request.form.get('fg_color', '#000000').strip()
    bg_color = request.form.get('bg_color', '#ffffff').strip()
    error_correction = request.form.get('error_correction', 'H').strip().upper()

    formatted = _format_data(data, data_type, extra)

    logo_opts = _parse_logo_options(request.form)
    adv_opts = _parse_advanced_options(request.form)
    logo_file = request.files.get('logo')

    img = _generate_qr_image(
        formatted,
        size=size,
        fg_color=fg_color,
        bg_color=bg_color,
        error_correction=error_correction,
        logo_file=logo_file,
        **logo_opts,
        **adv_opts,
    )

    buf = io.BytesIO()
    if adv_opts.get('transparent_bg'):
        img.save(buf, format='PNG', optimize=True)
    else:
        img.convert('RGB').save(buf, format='PNG', optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')

    return jsonify({'image': f'data:image/png;base64,{b64}'})


@qr_bp.route('/batch', methods=['POST'])
def batch():
    """
    Tạo hàng loạt mã QR và trả về file ZIP.

    Form fields:
        items            – JSON array: [{"data": "...", "data_type": "url"}, ...]
        size             – Kích thước pixel chung
        fg_color         – Màu foreground HEX chung
        bg_color         – Màu background HEX chung
        error_correction – L | M | Q | H chung
        format           – png | svg chung
        fg_color2        – Màu gradient thứ 2 HEX
        label_text       – Nhãn chữ (dùng chung hoặc mỗi item có riêng)
        transparent_bg   – true | false
    """
    items_str = request.form.get('items', '[]')
    try:
        items = json.loads(items_str)
    except json.JSONDecodeError:
        return jsonify({'error': 'Dữ liệu items không hợp lệ'}), 400

    if not items or not isinstance(items, list):
        return jsonify({'error': 'Danh sách items trống'}), 400

    size = _safe_int(request.form.get('size'), 400, 50, 2000)
    fg_color = request.form.get('fg_color', '#000000').strip()
    bg_color = request.form.get('bg_color', '#ffffff').strip()
    error_correction = request.form.get('error_correction', 'H').strip().upper()
    output_format = request.form.get('format', 'png').strip().lower()
    adv_opts = _parse_advanced_options(request.form)

    zip_buffer = io.BytesIO()
    stats = {'total': len(items), 'success': 0, 'failed': 0, 'errors': []}

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, item in enumerate(items):
            data = str(item.get('data', '')).strip()
            if not data:
                stats['failed'] += 1
                stats['errors'].append(f'Item {idx + 1}: Nội dung trống')
                continue

            data_type = item.get('data_type', 'text')
            extra = item.get('extra', {})
            formatted = _format_data(data, data_type, extra)

            try:
                if output_format == 'svg':
                    content = _generate_qr_svg(
                        formatted, fg_color, bg_color, error_correction
                    )
                    filename = f'qr_{idx + 1:04d}.svg'
                else:
                    img = _generate_qr_image(
                        formatted,
                        size=size,
                        fg_color=fg_color,
                        bg_color=bg_color,
                        error_correction=error_correction,
                        **adv_opts,
                    )
                    buf = io.BytesIO()
                    if adv_opts.get('transparent_bg'):
                        img.save(buf, format='PNG', optimize=True)
                    else:
                        img.convert('RGB').save(buf, format='PNG', optimize=True)
                    content = buf.getvalue()
                    filename = f'qr_{idx + 1:04d}.png'

                zf.writestr(filename, content)
                stats['success'] += 1
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f'Item {idx + 1}: {str(e)}')

    zip_buffer.seek(0)

    response = send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='qrcodes.zip',
    )
    response.headers['X-QR-Stats'] = json.dumps(stats, ensure_ascii=False)
    response.headers['Access-Control-Expose-Headers'] = 'X-QR-Stats'
    return response


# ── Helpers ──────────────────────────────────────────────────────────────────

def _safe_int(value, default: int, min_val: int = 0, max_val: int = 10000) -> int:
    """Chuyển đổi an toàn sang int với giới hạn min/max."""
    try:
        v = int(value)
        return max(min_val, min(max_val, v))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Chuyển đổi an toàn sang float với giới hạn min/max."""
    try:
        v = float(value)
        return max(min_val, min(max_val, v))
    except (TypeError, ValueError):
        return default
