import os
import uuid
import json
import base64
import traceback
import numpy as np
from flask import Blueprint, request, jsonify, Response, current_app
from PIL import Image

# Để OpenCV hoạt động không cần hiển thị GUI (Headless)
import cv2
import pytesseract

# Thiết lập đường dẫn Tesseract cụ thể cho macOS Homebrew để tránh lỗi PATH
TESSERACT_PATH = '/opt/homebrew/bin/tesseract'
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

video_bp = Blueprint('video_bp', __name__)

# Thư mục lưu trữ tạm thời video tải lên
def get_temp_dir():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    temp_dir = os.path.join(project_root, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    Tải video lên thư mục tạm, lấy thông tin cơ bản và trích xuất frame đầu tiên
    dưới dạng Base64 JPEG để hiển thị trên Canvas cho người dùng vẽ ROI.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Không có tệp video nào được tải lên."}), 400
        
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "Tệp tải lên không hợp lệ."}), 400

    # Lấy đuôi file mở rộng
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mpeg']:
        return jsonify({"error": f"Định dạng video {ext} không hỗ trợ. Chỉ hỗ trợ MP4, AVI, MOV, MKV, WEBM."}), 400

    video_id = str(uuid.uuid4())
    temp_dir = get_temp_dir()
    video_filename = f"video_{video_id}{ext}"
    video_path = os.path.join(temp_dir, video_filename)

    try:
        # Lưu file video tạm
        file.save(video_path)

        # Mở video qua OpenCV để lấy metadata
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # Xóa file lỗi ngay lập tức
            if os.path.exists(video_path):
                os.remove(video_path)
            return jsonify({"error": "Không thể mở tệp video. Tệp có thể bị hỏng."}), 400

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # Tính thời lượng (giây)
        duration = 0
        if fps > 0:
            duration = total_frames / fps

        # Trích xuất frame đầu tiên (frame 0) để làm ảnh nền vẽ ROI
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            if os.path.exists(video_path):
                os.remove(video_path)
            return jsonify({"error": "Không thể đọc khung hình đầu tiên của video."}), 400

        # Encode frame đầu tiên thành Base64 JPEG để gửi trực tiếp về client
        ret_enc, buffer = cv2.imencode('.jpg', frame)
        if not ret_enc:
            if os.path.exists(video_path):
                os.remove(video_path)
            return jsonify({"error": "Không thể mã hóa khung hình xem trước."}), 400

        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        preview_data_url = f"data:image/jpeg;base64,{frame_base64}"

        return jsonify({
            "success": True,
            "video_id": video_id,
            "filename": file.filename,
            "video_filename": video_filename,
            "width": width,
            "height": height,
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "duration": round(duration, 2),
            "preview_url": preview_data_url
        })

    except Exception as e:
        current_app.logger.error("Error in upload_video: %s", traceback.format_exc())
        # Cleanup
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)
        return jsonify({"error": f"Lỗi hệ thống khi tải video: {str(e)}"}), 500


@video_bp.route('/process', methods=['GET'])
def process_video():
    """
    Tiến hành tách frame và chạy OCR.
    Sử dụng Server-Sent Events (SSE) để truyền dữ liệu cập nhật theo thời gian thực.
    Các tham số nhận được thông qua URL query parameters:
      - video_filename: tên file video đã lưu trong temp
      - rois: chuỗi JSON chứa danh sách các vùng chọn [{"id": "...", "x": 10, "y": 20, "w": 50, "h": 30}, ...]
      - interval: khoảng cách mẫu bằng giây (ví dụ: 1.0) hoặc bằng khung hình (mặc định lấy theo giây)
      - sampling_mode: 'seconds' hoặc 'frames'
      - skip_static: 'true' hoặc 'false' (bật tính năng bỏ qua frame tĩnh)
      - sensitivity: độ nhạy biến đổi từ 1 đến 50 (ngưỡng MSE giữa 2 frame để xem có biến động hay không)
      - numeric_only: 'true' hoặc 'false' (ép Tesseract chỉ nhận dạng chữ số và dấu chấm thập phân)
    """
    video_filename = request.args.get('video_filename')
    rois_str = request.args.get('rois', '[]')
    sampling_mode = request.args.get('sampling_mode', 'seconds')
    interval_str = request.args.get('interval', '1.0')
    skip_static_str = request.args.get('skip_static', 'true')
    sensitivity_str = request.args.get('sensitivity', '5.0')
    numeric_only_str = request.args.get('numeric_only', 'true')
    display_mode = request.args.get('display_mode', 'auto')
    clahe_enabled_str = request.args.get('clahe_enabled', 'true')
    denoise_enabled_str = request.args.get('denoise_enabled', 'false')

    temp_dir = get_temp_dir()
    video_path = os.path.join(temp_dir, video_filename)

    if not video_filename or not os.path.exists(video_path):
        return jsonify({"error": "Không tìm thấy file video tạm trên server."}), 404

    def generate_ocr_events():
        cap = None
        try:
            # Parse parameters
            rois = json.loads(rois_str)
            interval = float(interval_str)
            skip_static = skip_static_str.lower() == 'true'
            sensitivity = float(sensitivity_str)
            numeric_only = numeric_only_str.lower() == 'true'
            clahe_enabled = clahe_enabled_str.lower() == 'true'
            denoise_enabled = denoise_enabled_str.lower() == 'true'

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                yield f"data: {json.dumps({'error': 'Không thể mở file video để xử lý.'})}\n\n"
                return

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if fps <= 0:
                fps = 25.0

            # Xác định bước nhảy frame (step size)
            if sampling_mode == 'seconds':
                step_frames = int(round(interval * fps))
            else:
                step_frames = int(round(interval))
            
            if step_frames < 1:
                step_frames = 1

            # Khởi tạo cache các khung hình cũ để so sánh tĩnh/động
            # map: roi_id -> last_cropped_image_grayscale
            last_roi_crops = {}
            # map: roi_id -> last_ocr_value
            last_ocr_values = {}

            # Cấu hình whitelist của Tesseract
            tess_config = '--psm 7'
            if numeric_only:
                tess_config = '--psm 7 -c tessedit_char_whitelist=0123456789.-: '

            # Duyệt qua các khung hình theo bước nhảy
            frame_idx = 0
            while frame_idx < total_frames:
                # Seek đến khung hình tương ứng
                if step_frames > 5:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # Tính mốc thời gian thực của frame (giây)
                time_sec = frame_idx / fps
                time_str = f"{int(time_sec // 3600):02d}:{int((time_sec % 3600) // 60):02d}:{int(time_sec % 60):02d}"

                frame_results = {}
                frame_stats = {} # lưu thông tin chênh lệch pixel để gỡ lỗi

                # Xử lý từng vùng chọn (ROI)
                for roi in rois:
                    roi_id = roi['id']
                    rx, ry, rw, rh = roi['x'], roi['y'], roi['w'], roi['h']

                    # Đảm bảo toạ độ nằm trong phạm vi ảnh
                    x = max(0, min(int(rx), width - 1))
                    y = max(0, min(int(ry), height - 1))
                    w = max(1, min(int(rw), width - x))
                    h = max(1, min(int(rh), height - y))

                    # Cắt ảnh vùng ROI
                    crop_img = frame[y:y+h, x:x+w]
                    if crop_img.size == 0:
                        frame_results[roi_id] = ""
                        continue

                    # Chuyển grayscale
                    gray_crop = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

                    # Lọc nhiễu ảnh nếu bật
                    if denoise_enabled:
                        # Bilateral filter giảm nhiễu hạt, giữ cạnh chữ rõ nét
                        gray_crop = cv2.bilateralFilter(gray_crop, 9, 75, 75)

                    # Tăng tương phản CLAHE nếu bật
                    if clahe_enabled:
                        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                        gray_crop = clahe.apply(gray_crop)

                    # ── NHẬN BIẾT BIẾN ĐỔI (CHANGE DETECTION) ──
                    is_static = False
                    pixel_diff = 0.0

                    if skip_static and roi_id in last_roi_crops:
                        prev_crop = last_roi_crops[roi_id]
                        if prev_crop.shape != gray_crop.shape:
                            prev_crop = cv2.resize(prev_crop, (gray_crop.shape[1], gray_crop.shape[0]))

                        # MAE pixel difference
                        diff_img = cv2.absdiff(gray_crop, prev_crop)
                        pixel_diff = float(np.mean(diff_img))
                        frame_stats[roi_id] = round(pixel_diff, 2)

                        if pixel_diff < sensitivity:
                            is_static = True

                    # Cập nhật cache ảnh crop gốc (trước khi upscale/threshold)
                    last_roi_crops[roi_id] = gray_crop.copy()

                    if is_static and roi_id in last_ocr_values:
                        # Copy kết quả của khung hình trước, không chạy OCR
                        frame_results[roi_id] = last_ocr_values[roi_id]
                    else:
                        # Phóng to vùng ảnh lên 3.0 lần để chữ số rõ ràng hơn
                        resized = cv2.resize(gray_crop, (0, 0), fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

                        # Tạo danh sách các ứng viên tiền xử lý (Preprocessing Candidates)
                        candidates = []
                        
                        # 1. Ảnh xám thô (CLAHE + Bilateral)
                        candidates.append(("Grayscale", resized))

                        # 2. Ảnh nhị phân thường (Chữ tối, nền sáng)
                        if display_mode in ['auto', 'dark_on_light']:
                            otsu_norm = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                            candidates.append(("Otsu Normal", otsu_norm))
                            
                            adapt_norm = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
                            candidates.append(("Adaptive Gaussian Normal", adapt_norm))

                        # 3. Ảnh nhị phân đảo ngược (Chữ sáng, nền tối)
                        if display_mode in ['auto', 'light_on_dark']:
                            otsu_inv = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                            candidates.append(("Otsu Inverted", otsu_inv))
                            
                            adapt_inv = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 5)
                            candidates.append(("Adaptive Gaussian Inverted", adapt_inv))

                        # Chạy OCR song song trên từng phương thức để tìm ra kết quả tốt nhất dựa trên độ tin cậy (Confidence)
                        best_text = ""
                        best_score = -999.0
                        best_method = ""

                        import re
                        # Chữ số, dấu chấm, dấu trừ, dấu hai chấm, dấu phẩy, khoảng trắng, dấu cộng
                        numeric_pattern = re.compile(r"^[0-9\.\-\:\s\,\+]+$")

                        for name, img_cand in candidates:
                            try:
                                # Chạy image_to_data để lấy confidence cụ thể cho từng chữ/từ
                                ocr_data = pytesseract.image_to_data(img_cand, output_type=pytesseract.Output.DICT, config=tess_config)
                                confs = [int(c) for c in ocr_data['conf'] if int(c) != -1]
                                words = [w.strip() for i, w in enumerate(ocr_data['text']) if int(ocr_data['conf'][i]) != -1 and w.strip()]
                                text = " ".join(words).strip()
                                
                                if not text:
                                    continue
                                    
                                avg_conf = np.mean(confs) if confs else 0.0
                                score = avg_conf
                                
                                # Tối ưu hóa điểm số cho chế độ chỉ số
                                if numeric_only:
                                    if numeric_pattern.match(text) and any(char.isdigit() for char in text):
                                        score += 60.0
                                    else:
                                        score -= 40.0
                                        
                                if score > best_score:
                                    best_score = score
                                    best_text = text
                                    best_method = name
                            except Exception as cand_err:
                                current_app.logger.warning("Error in OCR candidate %s: %s", name, cand_err)

                        # Nếu toàn bộ candidates đều thất bại hoặc rỗng
                        if best_score < -100.0:
                            try:
                                best_text = pytesseract.image_to_string(resized, config=tess_config).strip().replace('\n', ' ')
                                best_method = "Fallback Raw"
                            except Exception:
                                best_text = ""
                                best_method = "Error"

                        # Làm sạch văn bản kết quả
                        best_text = best_text.strip()
                        
                        # Ghi nhận kết quả
                        frame_results[roi_id] = best_text
                        last_ocr_values[roi_id] = best_text

                # Tính phần trăm tiến độ
                pct = int(min(100, round((frame_idx / total_frames) * 100)))

                # Gửi sự kiện cập nhật về client
                yield f"data: {json.dumps({'progress': pct, 'frame_idx': frame_idx, 'time_sec': round(time_sec, 2), 'time_str': time_str, 'values': frame_results, 'stats': frame_stats})}\n\n"

                # Đi tới khung hình tiếp theo
                frame_idx += step_frames

            # Hoàn tất xử lý
            yield f"data: {json.dumps({'progress': 100, 'done': True})}\n\n"

        except Exception as e:
            current_app.logger.error("Error in generate_ocr_events: %s", traceback.format_exc())
            yield f"data: {json.dumps({'error': f'Lỗi trong quá trình xử lý: {str(e)}'})}\n\n"
        finally:
            if cap is not None:
                cap.release()

    return Response(generate_ocr_events(), mimetype='text/event-stream')


@video_bp.route('/cleanup', methods=['POST'])
def cleanup_video():
    """
    Xóa tệp video tạm thời sau khi xử lý hoàn tất để giải phóng bộ nhớ disk.
    """
    data = request.get_json() or {}
    video_filename = data.get('video_filename')
    
    if not video_filename:
        return jsonify({"error": "Thiếu tham số video_filename."}), 400

    temp_dir = get_temp_dir()
    video_path = os.path.join(temp_dir, video_filename)

    if os.path.exists(video_path):
        try:
            os.remove(video_path)
            return jsonify({"success": True, "message": "Đã xóa file tạm thành công."})
        except Exception as e:
            return jsonify({"error": f"Không thể xóa file tạm: {str(e)}"}), 500
    
    return jsonify({"success": True, "message": "File đã được dọn dẹp hoặc không tồn tại."})
