// ═══════════════════════════════════════════════════════
// OCR Handler – Client logic for Image/PDF OCR Workspace
// ═══════════════════════════════════════════════════════

let ocrSelectedFiles = [];
let ocrResultData = null;

// ───────────────────────────────────────────────────────
// File Selection & Drag-and-Drop
// ───────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('ocr_drop_zone');
    if (dropZone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.borderColor = 'var(--accent2)';
                dropZone.style.background = 'rgba(16, 185, 129, 0.08)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.borderColor = 'var(--border)';
                dropZone.style.background = 'var(--surface2)';
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                ocrAddFiles(Array.from(dt.files));
            }
        });
    }
});

window.ocrHandleFileSelect = function (inputEl) {
    if (inputEl.files && inputEl.files.length > 0) {
        ocrAddFiles(Array.from(inputEl.files));
        inputEl.value = '';
    }
};

function ocrAddFiles(files) {
    const validExtensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.pdf', '.zip'];
    files.forEach(f => {
        const ext = '.' + f.name.split('.').pop().toLowerCase();
        if (validExtensions.includes(ext)) {
            // Avoid duplicate filenames
            if (!ocrSelectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
                ocrSelectedFiles.push(f);
            }
        }
    });
    renderOcrFileList();
}

window.ocrRemoveFile = function (index) {
    if (index >= 0 && index < ocrSelectedFiles.length) {
        ocrSelectedFiles.splice(index, 1);
        renderOcrFileList();
    }
};

window.ocrClearSelectedFiles = function () {
    ocrSelectedFiles = [];
    renderOcrFileList();
};

function renderOcrFileList() {
    const container = document.getElementById('ocr_selected_files_container');
    const listEl = document.getElementById('ocr_file_list');
    if (!container || !listEl) return;

    if (ocrSelectedFiles.length === 0) {
        container.style.display = 'none';
        listEl.innerHTML = '';
        return;
    }

    container.style.display = 'block';
    listEl.innerHTML = '';

    ocrSelectedFiles.forEach((f, idx) => {
        const sizeMb = (f.size / (1024 * 1024)).toFixed(2);
        const item = document.createElement('div');
        item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; padding: 4px 8px; background: var(--surface2); border-radius: 4px;';
        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                <span>📄</span>
                <span style="font-weight: 500; color: var(--text);">${f.name}</span>
                <span style="color: var(--text-muted); font-size: 0.72rem;">(${sizeMb} MB)</span>
            </div>
            <button onclick="ocrRemoveFile(${idx})" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 2px 6px; font-size: 0.8rem;" title="Xóa tệp">✕</button>
        `;
        listEl.appendChild(item);
    });
}

// ───────────────────────────────────────────────────────
// Processing OCR
// ───────────────────────────────────────────────────────

window.ocrStartProcessing = async function () {
    if (ocrSelectedFiles.length === 0) {
        showOcrError("Vui lòng chọn ít nhất một file ảnh, PDF hoặc ZIP để OCR.");
        return;
    }

    const btn = document.getElementById('btn_run_ocr');
    const progressCont = document.getElementById('ocr_progress_container');
    const progressText = document.getElementById('ocr_progress_text');
    const statusBadge = document.getElementById('ocr_status_badge');
    const resultsSection = document.getElementById('ocr_results_section');
    clearOcrError();

    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Đang xử lý OCR...</span>';
    progressCont.style.display = 'block';
    progressText.textContent = `Đang phân tích và nhận diện ${ocrSelectedFiles.length} tệp...`;
    statusBadge.style.display = 'none';

    const formData = new FormData();
    ocrSelectedFiles.forEach(f => {
        formData.append('files', f);
    });

    const resVal = document.getElementById('ocr_resolution').value || '150';
    const skipBlank = document.getElementById('ocr_skip_blank').checked;
    const engineType = (document.getElementById('ocr_engine_type') && document.getElementById('ocr_engine_type').value) || 'vietocr';

    formData.append('resolution', resVal);
    formData.append('skip_blank', skipBlank ? 'true' : 'false');
    formData.append('engine_type', engineType);

    try {
        const response = await fetch('/api/ocr/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || "Không thể hoàn thành OCR.");
        }

        ocrResultData = data;
        renderOcrResults(data);

        statusBadge.textContent = `✓ OCR hoàn tất (${data.total_files} tài liệu, ${data.total_pages} trang)`;
        statusBadge.style.display = 'inline-block';
        resultsSection.style.display = 'block';

        // Scroll smoothly to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
        showOcrError(err.message || "Đã xảy ra lỗi khi kết nối server OCR.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🚀 Bắt đầu OCR</span>';
        progressCont.style.display = 'none';
    }
};

function renderOcrResults(data) {
    const textarea = document.getElementById('ocr_result_textarea');
    const statsBadge = document.getElementById('ocr_stats_badge');
    const filesAccordion = document.getElementById('ocr_files_accordion');

    if (textarea) {
        textarea.value = data.combined_text || '';
    }

    const charCount = (data.combined_text || '').length;
    const wordCount = (data.combined_text || '').trim().split(/\s+/).filter(Boolean).length;
    if (statsBadge) {
        statsBadge.textContent = `${data.total_files} file • ${data.total_pages} trang • ${charCount.toLocaleString()} ký tự • ~${wordCount.toLocaleString()} từ`;
    }

    if (filesAccordion && data.items) {
        filesAccordion.innerHTML = '';
        data.items.forEach((item, idx) => {
            const card = document.createElement('div');
            card.style.cssText = 'background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow: hidden;';
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: var(--surface2); cursor: pointer;" onclick="ocrToggleFileCard(${idx})">
                    <div style="font-weight: 600; font-size: 0.85rem; color: var(--accent2); display: flex; align-items: center; gap: 6px;">
                        <span>📄 ${item.filename}</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal;">(${item.pages ? item.pages.length : 1} trang)</span>
                    </div>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <button class="btn-small btn-outline" style="font-size: 0.72rem; padding: 2px 8px;" onclick="event.stopPropagation(); ocrCopySingleFile(${idx})">Sao chép</button>
                        <span id="ocr_arrow_${idx}" style="font-size: 0.8rem; color: var(--text-muted); transition: transform 0.2s;">▼</span>
                    </div>
                </div>
                <div id="ocr_content_${idx}" style="display: block; padding: 12px;">
                    <textarea style="width: 100%; height: 220px; font-family: monospace; font-size: 0.82rem; padding: 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--surface2); color: var(--text); resize: vertical;" readonly>${item.full_text}</textarea>
                </div>
            `;
            filesAccordion.appendChild(card);
        });
    }
}

window.ocrToggleFileCard = function (idx) {
    const content = document.getElementById(`ocr_content_${idx}`);
    const arrow = document.getElementById(`ocr_arrow_${idx}`);
    if (content) {
        const isHidden = content.style.display === 'none';
        content.style.display = isHidden ? 'block' : 'none';
        if (arrow) arrow.style.transform = isHidden ? 'rotate(0deg)' : 'rotate(-90deg)';
    }
};

window.ocrSwitchViewTab = function (tabName) {
    const tabAll = document.getElementById('ocr_view_all');
    const tabFiles = document.getElementById('ocr_view_by_file');
    const btnAll = document.getElementById('ocr_tab_all_btn');
    const btnFiles = document.getElementById('ocr_tab_files_btn');

    if (tabName === 'all') {
        if (tabAll) tabAll.style.display = 'block';
        if (tabFiles) tabFiles.style.display = 'none';
        if (btnAll) btnAll.classList.add('active');
        if (btnFiles) btnFiles.classList.remove('active');
    } else {
        if (tabAll) tabAll.style.display = 'none';
        if (tabFiles) tabFiles.style.display = 'block';
        if (btnAll) btnAll.classList.remove('active');
        if (btnFiles) btnFiles.classList.add('active');
    }
};

// ───────────────────────────────────────────────────────
// Actions (Copy, Download, Send to Excel)
// ───────────────────────────────────────────────────────

window.ocrCopyText = function () {
    const textarea = document.getElementById('ocr_result_textarea');
    if (!textarea || !textarea.value) {
        showOcrError("Chưa có văn bản để sao chép.");
        return;
    }
    navigator.clipboard.writeText(textarea.value).then(() => {
        alert("✓ Đã sao chép toàn bộ văn bản OCR vào bộ nhớ tạm!");
    }).catch(err => {
        textarea.select();
        document.execCommand('copy');
        alert("✓ Đã sao chép văn bản!");
    });
};

window.ocrCopySingleFile = function (idx) {
    if (!ocrResultData || !ocrResultData.items || !ocrResultData.items[idx]) return;
    const text = ocrResultData.items[idx].full_text;
    navigator.clipboard.writeText(text).then(() => {
        alert(`✓ Đã sao chép nội dung file: ${ocrResultData.items[idx].filename}`);
    });
};

window.ocrDownloadSingleTxt = function () {
    const textarea = document.getElementById('ocr_result_textarea');
    const text = textarea ? textarea.value : '';
    if (!text) {
        showOcrError("Chưa có văn bản để tải về.");
        return;
    }

    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `KetQua_OCR_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

window.ocrDownloadZip = async function () {
    if (!ocrResultData || !ocrResultData.items || ocrResultData.items.length === 0) {
        showOcrError("Chưa có dữ liệu danh sách file để tải ZIP.");
        return;
    }

    try {
        const response = await fetch('/api/ocr/download-zip', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: ocrResultData.items })
        });

        if (!response.ok) throw new Error("Lỗi khi tải file ZIP.");
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `KetQua_OCR_TungFile_${new Date().toISOString().slice(0, 10)}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) {
        showOcrError(err.message || "Lỗi khi tạo file ZIP.");
    }
};

function showOcrError(msg) {

    const el = document.getElementById('ocr_error_message');
    if (el) {
        el.innerHTML = `<div class="alert alert-danger" style="margin-top: 10px; font-size: 0.85rem; padding: 8px 12px; border-radius: 6px;">⚠️ ${msg}</div>`;
    }
}

function clearOcrError() {
    const el = document.getElementById('ocr_error_message');
    if (el) el.innerHTML = '';
}
