// ══════════════════ GLOBAL VARIABLES ══════════════════
let videoFilename = "";
let videoMetadata = null;
let rois = []; // Vùng chọn: [{"id": "label", "x": 10, "y": 20, "w": 50, "h": 30, "color": "#ff00ff"}]
let isDrawing = false;
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let previewImg = new Image();
let sseSource = null;
let videoChart = null;
let tableData = []; // Dữ liệu kết quả: [{"stt": 1, "time_sec": 0, "time_str": "00:00:00", "values": {"roi_id": "val"}}]

// Danh sách màu sắc neon nổi bật cho các ROI khác nhau
const ROI_COLORS = ["#38bdf8", "#f472b6", "#34d399", "#fbbf24", "#a78bfa", "#f87171", "#2dd4bf", "#fb7185"];

// Khởi tạo Canvas và các biến tương tác
const canvas = document.getElementById("roi-canvas");
const ctx = canvas ? canvas.getContext("2d") : null;

// Chờ DOM load hoàn tất
document.addEventListener("DOMContentLoaded", () => {
  // Lắng nghe sự kiện kéo vẽ trên Canvas
  if (canvas) {
    canvas.addEventListener("mousedown", handleMouseDown);
    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseup", handleMouseUp);
  }
  
  // Khởi tạo nút lưu ROI trong modal đặt tên
  const btnRoiSave = document.getElementById("btn-roi-save");
  if (btnRoiSave) {
    btnRoiSave.addEventListener("click", saveRoiFromModal);
  }

  // Cho phép nhấn Enter trong ô tên ROI modal để lưu
  const roiNameInput = document.getElementById("roi-name-input");
  if (roiNameInput) {
    roiNameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveRoiFromModal();
      }
    });
  }
});

// ── BƯỚC 1: XỬ LÝ UPLOAD VIDEO ──

function handleVideoDrop(e) {
  e.preventDefault();
  document.getElementById("video-upload-area").style.borderColor = "var(--border)";
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleVideoFile(e.dataTransfer.files[0]);
  }
}

function handleVideoFile(file) {
  if (!file) return;
  
  const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
  const allowed = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.mpeg'];
  if (!allowed.includes(ext)) {
    showUploadError(`Định dạng file ${ext} không được hỗ trợ. Vui lòng chọn MP4, AVI, MOV, MKV hoặc WEBM.`);
    return;
  }

  // Hiển thị thanh tiến trình upload
  document.getElementById("video-upload-error").style.display = "none";
  document.getElementById("video-upload-progress-container").style.display = "block";
  document.getElementById("video-upload-filename").innerText = `Đang tải: ${file.name} (${formatBytes(file.size)})`;
  
  const formData = new FormData();
  formData.append("file", file);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/video/upload", true);

  // Cập nhật tiến độ tải lên
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const percentComplete = Math.round((e.loaded / e.total) * 100);
      document.getElementById("video-upload-pct").innerText = percentComplete + "%";
      document.getElementById("video-upload-progress-bar").style.width = percentComplete + "%";
    }
  };

  xhr.onload = () => {
    if (xhr.status === 200) {
      try {
        const res = JSON.parse(xhr.responseText);
        if (res.success) {
          videoFilename = res.video_filename;
          videoMetadata = res;
          
          // Cập nhật thông tin UI
          document.getElementById("video-resolution-badge").innerText = `${res.width}x${res.height} @ ${res.fps}fps | ${res.duration}s`;
          document.getElementById("video-upload-card").style.display = "none";
          document.getElementById("video-editor-row").style.display = "flex";
          
          // Load ảnh preview lên canvas
          loadPreviewImage(res.preview_url);
        } else {
          showUploadError(res.error || "Có lỗi xảy ra khi tải video.");
        }
      } catch (err) {
        showUploadError("Lỗi phân tích phản hồi từ máy chủ.");
      }
    } else {
      try {
        const res = JSON.parse(xhr.responseText);
        showUploadError(res.error || "Tải tệp thất bại.");
      } catch (err) {
        showUploadError(`Lỗi máy chủ: Mã trạng thái ${xhr.status}`);
      }
    }
  };

  xhr.onerror = () => {
    showUploadError("Kết nối mạng bị lỗi. Không thể tải tệp lên.");
  };

  xhr.send(formData);
}

function showUploadError(msg) {
  document.getElementById("video-upload-progress-container").style.display = "none";
  const errDiv = document.getElementById("video-upload-error");
  errDiv.innerText = msg;
  errDiv.style.display = "block";
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// ── BƯỚC 2: canvas vẽ ROI ──

function loadPreviewImage(dataUrl) {
  document.getElementById("canvas-loading").style.display = "flex";
  previewImg = new Image();
  previewImg.onload = () => {
    document.getElementById("canvas-loading").style.display = "none";
    canvas.width = previewImg.width;
    canvas.height = previewImg.height;
    
    // Reset và mặc định thêm vùng nhận dạng toàn bộ khung hình (Full Frame)
    rois = [
      {
        id: "Full_Frame",
        x: 0,
        y: 0,
        w: previewImg.width,
        h: previewImg.height,
        color: ROI_COLORS[0]
      }
    ];
    updateRoiList();
    drawCanvas();
  };
  previewImg.onerror = () => {
    document.getElementById("canvas-loading").style.display = "none";
    alert("Không thể load hình ảnh xem trước của video.");
  };
  previewImg.src = dataUrl;
}

// Chuyển tọa độ click chuột trên trình duyệt thành tọa độ gốc trên Canvas ảnh
function getMousePos(e) {
  const rect = canvas.getBoundingClientRect();
  // scale giữa kích thước thực tế hiển thị trên màn hình CSS và kích thước pixel thực của ảnh
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  };
}

function handleMouseDown(e) {
  if (isDrawing || !previewImg.src) return;
  const pos = getMousePos(e);
  startX = pos.x;
  startY = pos.y;
  currentX = pos.x;
  currentY = pos.y;
  isDrawing = true;
}

function handleMouseMove(e) {
  if (!isDrawing) return;
  const pos = getMousePos(e);
  currentX = pos.x;
  currentY = pos.y;
  drawCanvas();
}

function handleMouseUp(e) {
  if (!isDrawing) return;
  isDrawing = false;
  
  const pos = getMousePos(e);
  currentX = pos.x;
  currentY = pos.y;
  
  // Tính kích thước hộp chữ nhật vẽ được
  const x = Math.min(startX, currentX);
  const y = Math.min(startY, currentY);
  const w = Math.abs(startX - currentX);
  const h = Math.abs(startY - currentY);
  
  // Chỉ chấp nhận hình vẽ có kích thước tối thiểu (ví dụ 10x10 px) để tránh click nhầm
  if (w > 10 && h > 10) {
    // Lưu tọa độ nháp để chờ modal nhập tên đặt nhãn
    window.tempRoiCoords = { x, y, w, h };
    
    // Mở modal đặt tên
    const roiModal = new bootstrap.Modal(document.getElementById('roiNameModal'));
    document.getElementById("roi-name-input").value = `Param_${rois.length + 1}`;
    document.getElementById("roi-modal-error").style.display = "none";
    roiModal.show();
    
    // Focus vào input
    setTimeout(() => {
      document.getElementById("roi-name-input").focus();
      document.getElementById("roi-name-input").select();
    }, 450);
  } else {
    drawCanvas();
  }
}

function saveRoiFromModal() {
  const nameInput = document.getElementById("roi-name-input");
  const name = nameInput.value.trim().replace(/[^a-zA-Z0-9_\-\s]/g, ""); // Dọn dẹp ký tự lạ
  
  if (!name) {
    const err = document.getElementById("roi-modal-error");
    err.innerText = "Tên vùng chọn không được để trống.";
    err.style.display = "block";
    return;
  }
  
  // Tránh trùng tên
  if (rois.some(r => r.id.toLowerCase() === name.toLowerCase())) {
    const err = document.getElementById("roi-modal-error");
    err.innerText = "Tên vùng chọn này đã tồn tại.";
    err.style.display = "block";
    return;
  }
  
  const coords = window.tempRoiCoords;
  if (coords) {
    const color = ROI_COLORS[rois.length % ROI_COLORS.length];
    rois.push({
      id: name,
      x: Math.round(coords.x),
      y: Math.round(coords.y),
      w: Math.round(coords.w),
      h: Math.round(coords.h),
      color: color
    });
    
    // Reset và ẩn modal
    window.tempRoiCoords = null;
    const modalEl = document.getElementById('roiNameModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
    
    // Vẽ lại canvas và update list bên phải
    updateRoiList();
    drawCanvas();
  }
}

// Xóa vùng chọn
function deleteRoi(idx) {
  rois.splice(idx, 1);
  updateRoiList();
  drawCanvas();
}

// Vẽ toàn bộ các thành phần lên canvas
function drawCanvas() {
  if (!ctx || !previewImg.src) return;
  
  // 1. Vẽ ảnh nền
  ctx.drawImage(previewImg, 0, 0);
  
  // 2. Vẽ các hộp ROI đã vẽ
  rois.forEach((roi) => {
    ctx.strokeStyle = roi.color;
    ctx.lineWidth = Math.max(2, Math.round(canvas.width / 500)); // Độ dày đường viền tỉ lệ với ảnh
    ctx.strokeRect(roi.x, roi.y, roi.w, roi.h);
    
    // Vẽ nhãn văn bản của vùng chọn
    ctx.fillStyle = roi.color;
    const fontSize = Math.max(12, Math.round(canvas.width / 60));
    ctx.font = `bold ${fontSize}px sans-serif`;
    
    const text = ` ${roi.id} `;
    const textWidth = ctx.measureText(text).width;
    const textHeight = fontSize + 6;
    
    // Hộp chứa nền chữ
    ctx.fillRect(roi.x, Math.max(0, roi.y - textHeight), textWidth, textHeight);
    
    // Vẽ chữ nhãn màu đen hoặc trắng để dễ nhìn
    ctx.fillStyle = "#000000";
    ctx.fillText(text, roi.x, Math.max(textHeight - 4, roi.y - 4));
  });
  
  // 3. Vẽ hộp nháp khi đang di chuột kéo vẽ
  if (isDrawing) {
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]); // Nét đứt
    
    const x = Math.min(startX, currentX);
    const y = Math.min(startY, currentY);
    const w = Math.abs(startX - currentX);
    const h = Math.abs(startY - currentY);
    
    ctx.strokeRect(x, y, w, h);
    ctx.setLineDash([]); // Reset nét đứt
  }
}

// Cập nhật danh sách hiển thị vùng chọn bên phải
function updateRoiList() {
  const emptyMsg = document.getElementById("roi-empty-msg");
  const listContainer = document.getElementById("roi-items-container");
  
  if (rois.length === 0) {
    emptyMsg.style.display = "block";
    listContainer.style.display = "none";
    return;
  }
  
  emptyMsg.style.display = "none";
  listContainer.innerHTML = "";
  listContainer.style.display = "flex";
  
  rois.forEach((roi, idx) => {
    const item = document.createElement("div");
    item.className = "d-flex align-items-center justify-content-between p-2 rounded";
    item.style.background = "var(--surface2)";
    item.style.borderLeft = `4px solid ${roi.color}`;
    item.style.fontSize = "0.78rem";
    
    item.innerHTML = `
      <div class="d-flex flex-column">
        <span class="fw-bold" style="color: var(--text);">${roi.id}</span>
        <span class="text-muted" style="font-size:0.68rem;">ROI: [x:${roi.x}, y:${roi.y}, w:${roi.w}, h:${roi.h}]</span>
      </div>
      <button onclick="deleteRoi(${idx})" class="btn btn-sm btn-link text-danger p-0 border-0" title="Xóa vùng">
        <i class="bi bi-trash-fill" style="font-size: 0.85rem;"></i>
      </button>
    `;
    listContainer.appendChild(item);
  });
}

function toggleSamplingInputLabel() {
  const mode = document.querySelector('input[name="sampling_mode"]:checked').value;
  const label = document.getElementById("sampling-interval-label");
  const input = document.getElementById("sampling-interval");
  
  if (mode === "seconds") {
    label.innerText = "Chu kỳ lấy mẫu (giây):";
    input.value = "1.0";
    input.min = "0.1";
    input.step = "0.1";
  } else {
    label.innerText = "Số lượng khung hình bỏ qua (frames):";
    input.value = "25";
    input.min = "1";
    input.step = "1";
  }
}

function toggleSensitivityControl(checked) {
  const container = document.getElementById("sensitivity-container");
  if (checked) {
    container.style.opacity = "1";
    container.style.pointerEvents = "auto";
  } else {
    container.style.opacity = "0.4";
    container.style.pointerEvents = "none";
  }
}


// ── BƯỚC 3: XỬ LÝ TRÍCH XUẤT OCR QUA SSE ──

function startVideoOCR() {
  if (rois.length === 0) {
    alert("Vui lòng vẽ ít nhất một vùng nhận dạng (ROI) trước khi bắt đầu.");
    return;
  }
  
  // Ẩn bảng kết quả cũ
  document.getElementById("video-results-panel").style.display = "none";
  
  // Hiển thị progress panel
  const progressCard = document.getElementById("video-progress-card");
  progressCard.style.display = "block";
  
  // Reset các thanh tiến trình
  document.getElementById("video-processing-pct").innerText = "0%";
  document.getElementById("video-processing-bar").style.width = "0%";
  document.getElementById("progress-status-title").innerText = "Đang bắt đầu xử lý...";
  document.getElementById("video-stop-container").style.display = "flex";
  
  // Khởi tạo terminal log
  const consoleLog = document.getElementById("video-console-log");
  consoleLog.innerHTML = "";
  logToConsole("[Hệ thống] Đang gửi yêu cầu khởi tạo phân tích video...");
  logToConsole(`[Hệ thống] Danh sách tham số cấu hình:
  - Video file: ${videoFilename}
  - Tổng số vùng nhận dạng: ${rois.length} (${rois.map(r => r.id).join(", ")})
  - Chế độ: ${document.querySelector('input[name="sampling_mode"]:checked').value === "seconds" ? "Lấy mẫu theo giây" : "Lấy mẫu theo số frame"}
  - Khoảng cách: ${document.getElementById("sampling-interval").value}
  - Lọc nhiễu tĩnh: ${document.getElementById("skip-static").checked ? "Bật" : "Tắt"}
  - Nhận diện số: ${document.getElementById("ocr-numeric-only").value === "true" ? "Có" : "Không"}
  - Kiểu màn hình: ${document.getElementById("ocr-display-mode").value}
  - CLAHE cục bộ: ${document.getElementById("ocr-clahe").checked ? "Bật" : "Tắt"}
  - Lọc Bilateral: ${document.getElementById("ocr-denoise").checked ? "Bật" : "Tắt"}`);

  // Chuẩn bị dữ liệu bảng
  tableData = [];
  
  // Dựng Header cho bảng kết quả
  const headerTr = document.getElementById("video-table-header");
  headerTr.innerHTML = `
    <th style="color: var(--text-muted); font-weight: 600;">STT</th>
    <th style="color: var(--text-muted); font-weight: 600;">Mốc thời gian (s)</th>
    <th style="color: var(--text-muted); font-weight: 600;">Mã thời gian</th>
  `;
  rois.forEach((roi) => {
    const th = document.createElement("th");
    th.style.color = "var(--text)";
    th.style.fontWeight = "600";
    th.innerHTML = `<span class="badge" style="background: ${roi.color}; color: #000; font-weight: bold; margin-right: 5px;">⬤</span> ${roi.id}`;
    headerTr.appendChild(th);
  });
  
  // Xóa nội dung body cũ
  document.getElementById("video-table-body").innerHTML = "";

  // Tạo URL SSE
  const params = new URLSearchParams({
    video_filename: videoFilename,
    rois: JSON.stringify(rois),
    sampling_mode: document.querySelector('input[name="sampling_mode"]:checked').value,
    interval: document.getElementById("sampling-interval").value,
    skip_static: document.getElementById("skip-static").checked,
    sensitivity: document.getElementById("sensitivity").value,
    numeric_only: document.getElementById("ocr-numeric-only").value,
    display_mode: document.getElementById("ocr-display-mode").value,
    clahe_enabled: document.getElementById("ocr-clahe").checked,
    denoise_enabled: document.getElementById("ocr-denoise").checked
  });
  
  logToConsole("[Hệ thống] Đang thiết lập kết nối thời gian thực (SSE)...");
  
  // Kết nối SSE
  sseSource = new EventSource(`/api/video/process?${params.toString()}`);
  
  sseSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.error) {
        logToConsole(`[LỖI] ${data.error}`, "danger");
        stopSseConnection();
        return;
      }

      if (data.done) {
        logToConsole("[Hệ thống] Xử lý hoàn tất! Đang dọn dẹp bộ nhớ...");
        document.getElementById("progress-status-title").innerText = "Hoàn tất xử lý dữ liệu!";
        document.getElementById("video-stop-container").style.display = "none";
        
        stopSseConnection();
        cleanupTempVideo();
        
        // Render đồ thị và hiển thị bảng kết quả
        renderChart();
        document.getElementById("video-results-panel").style.display = "block";
        return;
      }
      
      // Nhận dữ liệu frame
      if (data.progress !== undefined) {
        // Cập nhật thanh tiến trình
        document.getElementById("video-processing-pct").innerText = data.progress + "%";
        document.getElementById("video-processing-bar").style.width = data.progress + "%";
        document.getElementById("progress-status-title").innerText = `Đang trích xuất frame: ${data.frame_idx} (${data.time_str})`;
        
        // Thêm bản ghi dữ liệu mới
        const stt = tableData.length + 1;
        const record = {
          stt: stt,
          time_sec: data.time_sec,
          time_str: data.time_str,
          values: data.values
        };
        tableData.push(record);
        
        // Thêm hàng vào bảng
        appendTableRow(record, data.stats);
        
        // In log ra console
        let valuesLog = Object.entries(data.values)
          .map(([k, v]) => {
            const isStatic = data.stats && data.stats[k] !== undefined && data.stats[k] < parseFloat(document.getElementById("sensitivity").value);
            return `${k}=${v || "N/A"}${isStatic ? " (static)" : ""}`;
          })
          .join(", ");
        logToConsole(`[${data.time_str}] Khung hình #${data.frame_idx}: ${valuesLog}`);
      }
    } catch (err) {
      logToConsole(`[LỖI] Lỗi phân tích cú pháp dữ liệu: ${err.message}`, "danger");
    }
  };

  sseSource.onerror = (err) => {
    logToConsole("[LỖI] Mất kết nối EventSource với server. Có thể tiến trình đã bị gián đoạn.", "danger");
    stopSseConnection();
  };
}

function stopSseConnection() {
  if (sseSource) {
    sseSource.close();
    sseSource = null;
  }
}

function abortVideoOCR() {
  if (confirm("Bạn có chắc chắn muốn dừng việc trích xuất giữa chừng? Dữ liệu đã chạy được vẫn sẽ được giữ lại.")) {
    logToConsole("[Hệ thống] Người dùng yêu cầu dừng xử lý.");
    stopSseConnection();
    document.getElementById("progress-status-title").innerText = "Đã dừng xử lý bởi người dùng.";
    document.getElementById("video-stop-container").style.display = "none";
    cleanupTempVideo();
    
    if (tableData.length > 0) {
      renderChart();
      document.getElementById("video-results-panel").style.display = "block";
    }
  }
}

function cleanupTempVideo() {
  if (!videoFilename) return;
  fetch("/api/video/cleanup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_filename: videoFilename })
  })
  .then(res => res.json())
  .then(data => {
    logToConsole("[Hệ thống] Đã dọn dẹp file tạm thành công trên server.");
  })
  .catch(err => {
    console.error("Cleanup failed:", err);
  });
}

function logToConsole(text, type = "info") {
  const consoleLog = document.getElementById("video-console-log");
  if (!consoleLog) return;
  
  let color = "#a78bfa"; // purple default
  if (type === "danger") color = "var(--danger)";
  else if (type === "success") color = "var(--accent3)";
  
  const span = document.createElement("span");
  span.style.color = color;
  span.innerText = text + "\n";
  consoleLog.appendChild(span);
  
  // Tự động cuộn xuống cuối cùng
  consoleLog.scrollTop = consoleLog.scrollHeight;
}

function clearConsoleLog() {
  const consoleLog = document.getElementById("video-console-log");
  if (consoleLog) consoleLog.innerHTML = "";
}

// ── BƯỚC 4: RENDER BẢNG KẾT QUẢ & CHỈNH SỬA Ô DỮ LIỆU ──

function appendTableRow(record, stats) {
  const tbody = document.getElementById("video-table-body");
  const tr = document.createElement("tr");
  tr.id = `video-row-${record.stt}`;
  
  let html = `
    <td class="text-muted fw-semibold">${record.stt}</td>
    <td class="fw-bold">${record.time_sec}s</td>
    <td class="text-muted">${record.time_str}</td>
  `;
  
  rois.forEach((roi) => {
    const val = record.values[roi.id] !== undefined ? record.values[roi.id] : "";
    const isStatic = stats && stats[roi.id] !== undefined && stats[roi.id] < parseFloat(document.getElementById("sensitivity").value);
    
    // Cell màu nhạt nếu bị static (không thay đổi) để người dùng dễ quan sát
    const bgStyle = isStatic ? `background: rgba(255, 255, 255, 0.02); color: var(--text-muted);` : "";
    
    html += `
      <td style="${bgStyle}" class="editable-cell" data-stt="${record.stt}" data-roi-id="${roi.id}" ondoubleclick="startEditCell(this)">
        ${val}
      </td>
    `;
  });
  
  tr.innerHTML = html;
  tbody.appendChild(tr);
}

// Bắt đầu sửa ô dữ liệu trực tiếp bằng double click
function startEditCell(cell) {
  if (cell.querySelector("input")) return; // Đang edit rồi thì bỏ qua
  
  const val = cell.innerText.trim();
  const input = document.createElement("input");
  input.type = "text";
  input.value = val;
  input.className = "form-control form-control-sm";
  input.style.width = "100%";
  input.style.minWidth = "60px";
  input.style.fontSize = "0.82rem";
  input.style.padding = "2px 5px";
  input.style.background = "var(--surface2)";
  input.style.color = "var(--text)";
  input.style.border = "1px solid var(--accent)";
  
  cell.innerHTML = "";
  cell.appendChild(input);
  input.focus();
  input.select();
  
  // Sự kiện kết thúc chỉnh sửa khi nhấn enter hoặc blur ra ngoài
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveEditCell(cell, input.value);
    } else if (e.key === "Escape") {
      cell.innerHTML = val;
    }
  });
  
  input.addEventListener("blur", () => {
    saveEditCell(cell, input.value);
  });
}

function saveEditCell(cell, newVal) {
  const stt = parseInt(cell.getAttribute("data-stt"));
  const roiId = cell.getAttribute("data-roi-id");
  
  // Cập nhật mảng dữ liệu gốc
  const recordIndex = tableData.findIndex(r => r.stt === stt);
  if (recordIndex !== -1) {
    tableData[recordIndex].values[roiId] = newVal;
  }
  
  cell.innerHTML = newVal;
  
  // Cập nhật lại đồ thị
  renderChart();
}


// ── BƯỚC 5: RENDER ĐỒ THỊ BẰNG CHART.JS ──

function renderChart() {
  const chartCanvas = document.getElementById("video-chart");
  if (!chartCanvas) return;
  
  // Hủy đồ thị cũ nếu có
  if (videoChart) {
    videoChart.destroy();
    videoChart = null;
  }
  
  // Dựng nhãn X-axis: thời gian của các mốc lấy mẫu
  const labels = tableData.map(r => r.time_str);
  
  // Dựng datasets cho từng ROI
  const datasets = rois.map((roi) => {
    // Trích xuất các giá trị số để vẽ đồ thị (chuyển sang float, bỏ qua các chữ cái lỗi OCR)
    const dataPoints = tableData.map((record) => {
      const val = record.values[roi.id];
      if (val === undefined || val === null || val === "") return null;
      const num = parseFloat(val);
      return isNaN(num) ? null : num;
    });
    
    return {
      label: roi.id,
      data: dataPoints,
      borderColor: roi.color,
      backgroundColor: roi.color + "1A", // Thêm alpha độ mờ 10%
      borderWidth: 2,
      pointRadius: labels.length > 50 ? 0 : 3, // Ẩn điểm tròn nếu quá nhiều bản ghi để đồ thị thoáng hơn
      pointHoverRadius: 5,
      tension: 0.15, // Smooth line
      spanGaps: true // Kết nối đường thẳng vượt qua điểm bị null lỗi
    };
  });

  const isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
  const gridColor = isDark ? "#2d2845" : "#e2e8f0";
  const textColor = isDark ? "#94a3b8" : "#475569";
  
  videoChart = new Chart(chartCanvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: isDark ? "#f8fafc" : "#0f172a",
            font: { family: 'Inter', size: 11, weight: 'semibold' }
          }
        },
        tooltip: {
          padding: 10,
          backgroundColor: isDark ? "#14131d" : "#ffffff",
          titleColor: isDark ? "#f8fafc" : "#0f172a",
          bodyColor: isDark ? "#94a3b8" : "#475569",
          borderColor: "rgba(109, 40, 217, 0.3)",
          borderWidth: 1,
          textDirection: 'ltr',
          usePointStyle: true
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
        },
        y: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
        }
      }
    }
  });
}


// ── BƯỚC 6: XUẤT FILE EXCEL & CSV ──

function downloadVideoExcel() {
  if (tableData.length === 0) {
    alert("Không có dữ liệu để xuất Excel.");
    return;
  }
  
  try {
    // 1. Tạo workbook mới
    const wb = XLSX.utils.book_new();
    
    // 2. Chuyển mảng dữ liệu thành dạng mảng 2 chiều để xuất
    const excelHeaders = ["STT", "Thời gian (s)", "Mã thời gian", ...rois.map(r => r.id)];
    const excelRows = [excelHeaders];
    
    tableData.forEach((record) => {
      const row = [
        record.stt,
        record.time_sec,
        record.time_str
      ];
      rois.forEach((roi) => {
        const val = record.values[roi.id];
        // Thử parse sang số, nếu thành công thì lưu dạng số, thất bại giữ nguyên text
        const num = parseFloat(val);
        row.push(isNaN(num) ? val : num);
      });
      excelRows.push(row);
    });
    
    // 3. Tạo worksheet từ dữ liệu mảng
    const ws = XLSX.utils.aoa_to_sheet(excelRows);
    
    // Cài đặt độ rộng cột tự động
    const colWidths = excelHeaders.map(h => ({ wch: Math.max(h.length + 3, 12) }));
    ws['!cols'] = colWidths;
    
    // 4. Nhét worksheet vào workbook
    XLSX.utils.book_append_sheet(wb, ws, "Dữ liệu OCR");
    
    // 5. Xuất và tải file
    const dateStr = new Date().toISOString().slice(0, 10);
    const excelFilename = `video_ocr_results_${dateStr}.xlsx`;
    XLSX.writeFile(wb, excelFilename);
    
    logToConsole(`[Hệ thống] Xuất file Excel thành công: ${excelFilename}`, "success");
  } catch (err) {
    alert(`Lỗi xuất Excel: ${err.message}`);
  }
}

function downloadVideoCSV() {
  if (tableData.length === 0) {
    alert("Không có dữ liệu để xuất CSV.");
    return;
  }
  
  try {
    const headers = ["STT", "Thoi gian (s)", "Ma thoi gian", ...rois.map(r => r.id)];
    let csvContent = headers.join(",") + "\n";
    
    tableData.forEach((record) => {
      const row = [
        record.stt,
        record.time_sec,
        `"${record.time_str}"`
      ];
      rois.forEach((roi) => {
        let val = record.values[roi.id] || "";
        // Thoát dấu ngoặc kép nếu có trong text
        if (typeof val === "string") {
          val = `"${val.replace(/"/g, '""')}"`;
        }
        row.push(val);
      });
      csvContent += row.join(",") + "\n";
    });
    
    // Tạo blob tải file
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const dateStr = new Date().toISOString().slice(0, 10);
    
    link.setAttribute("href", url);
    link.setAttribute("download", `video_ocr_results_${dateStr}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    logToConsole(`[Hệ thống] Đã xuất file CSV thành công.`, "success");
  } catch (err) {
    alert(`Lỗi xuất CSV: ${err.message}`);
  }
}

function downloadVideoTXT() {
  if (tableData.length === 0) {
    alert("Không có dữ liệu để xuất file TXT.");
    return;
  }
  
  try {
    const dateStr = new Date().toLocaleString();
    let txtContent = `=========================================\n`;
    txtContent += `KẾT QUẢ TRÍCH XUẤT DỮ LIỆU VIDEO OCR\n`;
    txtContent += `Thời gian xuất file: ${dateStr}\n`;
    txtContent += `Tổng số bản ghi: ${tableData.length}\n`;
    txtContent += `=========================================\n\n`;
    
    tableData.forEach((record) => {
      txtContent += `Mốc thời gian: ${record.time_str} (${record.time_sec}s)\n`;
      rois.forEach((roi) => {
        const val = record.values[roi.id] || "";
        txtContent += `  - ${roi.id}: ${val}\n`;
      });
      txtContent += `-----------------------------------------\n`;
    });
    
    // Tạo blob tải file
    const blob = new Blob([txtContent], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const fileDateStr = new Date().toISOString().slice(0, 10);
    
    link.setAttribute("href", url);
    link.setAttribute("download", `video_ocr_results_${fileDateStr}.txt`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    logToConsole(`[Hệ thống] Đã xuất file TXT thành công.`, "success");
  } catch (err) {
    alert(`Lỗi xuất TXT: ${err.message}`);
  }
}
