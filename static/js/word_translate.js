/**
 * POLYTEE Tools - Word Document Translator Module
 * Hỗ trợ dịch thuật tài liệu Word (.docx, .doc) giữ nguyên 100% định dạng, bảng biểu, hình ảnh.
 */

let selectedWordFile = null;
let extractedSegments = [];

// ── KHỞI TẠO & CHUYỂN TAB ──────────────────────────────────────────────────

function switchTranslateTab(tab) {
    const btnAuto = document.getElementById('btn-trans-mode-auto');
    const btnManual = document.getElementById('btn-trans-mode-manual');
    const paneAuto = document.getElementById('trans-pane-auto');
    const paneManual = document.getElementById('trans-pane-manual');

    if (!btnAuto || !btnManual || !paneAuto || !paneManual) return;

    if (tab === 'auto') {
        btnAuto.style.background = 'var(--accent)';
        btnAuto.style.color = 'white';
        btnManual.style.background = 'transparent';
        btnManual.style.color = 'var(--text-muted)';

        paneAuto.style.display = 'block';
        paneManual.style.display = 'none';
    } else {
        btnManual.style.background = 'var(--accent)';
        btnManual.style.color = 'white';
        btnAuto.style.background = 'transparent';
        btnAuto.style.color = 'var(--text-muted)';

        paneManual.style.display = 'block';
        paneAuto.style.display = 'none';
    }
}

function swapTranslateLanguages() {
    const srcSel = document.getElementById('trans-src-lang');
    const tgtSel = document.getElementById('trans-tgt-lang');
    if (!srcSel || !tgtSel) return;

    const srcVal = srcSel.value;
    const tgtVal = tgtSel.value;

    if (srcVal !== 'auto') {
        srcSel.value = tgtVal;
        tgtSel.value = srcVal;
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function triggerDownload(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}


// ── CHỌN TỆP WORD ──────────────────────────────────────────────────────────

function initWordTranslateListeners() {
    const input = document.getElementById('trans-file-input');
    const dropzone = document.getElementById('trans-dropzone');

    if (!input || !dropzone) return;

    input.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedWordFile(e.target.files[0]);
        }
        input.value = '';
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent)';
    });

    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(59, 130, 246, 0.45)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(59, 130, 246, 0.45)';
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleSelectedWordFile(e.dataTransfer.files[0]);
        }
    });
}

function handleSelectedWordFile(file) {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!['.docx', '.doc', '.docm'].includes(ext)) {
        showTranslateError('Vui lòng chọn tệp Word hợp lệ (.docx, .doc, .docm)');
        return;
    }

    hideTranslateError();
    selectedWordFile = file;

    // Cập nhật giao diện thông tin file
    document.getElementById('trans-dropzone').style.display = 'none';
    const fileCard = document.getElementById('trans-selected-file');
    fileCard.style.display = 'flex';
    document.getElementById('trans-filename').innerText = file.name;
    document.getElementById('trans-filesize').innerText = formatBytes(file.size);

    document.getElementById('btn-trans-run-auto').disabled = false;
    document.getElementById('btn-trans-extract').disabled = false;
    document.getElementById('trans-status-auto').innerText = 'Sẵn sàng dịch';
}

function clearSelectedWordFile() {
    selectedWordFile = null;
    extractedSegments = [];

    document.getElementById('trans-dropzone').style.display = 'block';
    document.getElementById('trans-selected-file').style.display = 'none';

    document.getElementById('btn-trans-run-auto').disabled = true;
    document.getElementById('btn-trans-extract').disabled = true;
    document.getElementById('trans-status-auto').innerText = 'Chưa chọn tệp';

    document.getElementById('trans-table-container').style.display = 'none';
    document.getElementById('trans-success-auto').style.display = 'none';
    document.getElementById('trans-progress-container').style.display = 'none';
    hideTranslateError();
}


// ── CHẾ ĐỘ 1: DỊCH TỰ ĐỘNG BẰNG GOOGLE DỊCH ────────────────────────────────

async function runAutoWordTranslation() {
    if (!selectedWordFile) return;

    const btn = document.getElementById('btn-trans-run-auto');
    const spinner = document.getElementById('trans-spinner-auto');
    const btnText = document.getElementById('trans-btn-text-auto');
    const progressDiv = document.getElementById('trans-progress-container');
    const successDiv = document.getElementById('trans-success-auto');
    const successDetail = document.getElementById('trans-success-auto-detail');
    const srcLang = document.getElementById('trans-src-lang').value;
    const tgtLang = document.getElementById('trans-tgt-lang').value;

    hideTranslateError();
    if (successDiv) successDiv.style.display = 'none';

    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.innerText = 'Đang dịch...';
    if (progressDiv) progressDiv.style.display = 'block';

    const formData = new FormData();
    formData.append('file', selectedWordFile);
    formData.append('src_lang', srcLang);
    formData.append('tgt_lang', tgtLang);

    try {
        const response = await fetch('/api/translate/auto', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Có lỗi xảy ra khi dịch file Word';
            try {
                const errJson = await response.json();
                if (errJson.error) errorMsg = errJson.error;
            } catch (_) {}
            showTranslateError(errorMsg);
            return;
        }

        const blob = await response.blob();
        let downloadName = `${selectedWordFile.name.replace(/\.[^/.]+$/, "")}_translated.docx`;
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches != null && matches[1]) {
                downloadName = matches[1].replace(/['"]/g, '');
            }
        }

        triggerDownload(blob, downloadName);

        if (successDiv && successDetail) {
            successDiv.style.display = 'block';
            successDetail.innerHTML = `File Word đã được dịch và tải về: <code>${downloadName}</code> (${formatBytes(blob.size)}). Toàn bộ bảng biểu, hình ảnh và định dạng đã được bảo toàn nguyên vẹn.`;
        }

    } catch (err) {
        let msg = err.message;
        if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
            msg = 'Không thể kết nối đến máy chủ PLT Process. Vui lòng đảm bảo file START.cmd đang chạy!';
        }
        showTranslateError(msg);
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.innerText = '🚀 Dịch toàn bộ & Tải file Word';
        if (progressDiv) progressDiv.style.display = 'none';
    }
}


// ── CHẾ ĐỘ 2: TỰ DỊCH & BIÊN TẬP SONG NGỮ ───────────────────────────────────

async function extractSegmentsFromWord() {
    if (!selectedWordFile) return;

    const btn = document.getElementById('btn-trans-extract');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang trích xuất...';
    hideTranslateError();

    const formData = new FormData();
    formData.append('file', selectedWordFile);

    try {
        const response = await fetch('/api/translate/extract', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Lỗi khi trích xuất văn bản từ Word';
            try {
                const errJson = await response.json();
                if (errJson.error) errorMsg = errJson.error;
            } catch (_) {}
            showTranslateError(errorMsg);
            return;
        }

        const data = await response.json();
        extractedSegments = data.segments || [];

        renderBilingualTable(extractedSegments);

    } catch (err) {
        let msg = err.message;
        if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
            msg = 'Không thể kết nối đến máy chủ PLT Process. Vui lòng đảm bảo file START.cmd đang chạy!';
        }
        showTranslateError(msg);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-list-columns-reverse"></i> Trích xuất văn bản sang bảng';
    }
}

function renderBilingualTable(segments) {
    const container = document.getElementById('trans-table-container');
    const tbody = document.getElementById('trans-tbody');
    const countSpan = document.getElementById('trans-segment-count');

    if (!container || !tbody) return;

    countSpan.innerText = segments.length;
    tbody.innerHTML = '';

    if (segments.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted py-4">Tài liệu không chứa văn bản nào để trích xuất.</td></tr>`;
        container.style.display = 'block';
        return;
    }

    segments.forEach((seg, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="text-align: center; vertical-align: top; color: var(--text-muted); font-weight: 600;">${idx + 1}</td>
            <td style="vertical-align: top; line-height: 1.5; color: var(--text); background: var(--surface2);">${escapeHtml(seg.text)}</td>
            <td style="vertical-align: top;">
                <textarea class="form-control trans-input-row" id="trans-input-${seg.id}" data-id="${seg.id}"
                    rows="2" style="font-size: 0.82rem; background: var(--surface); color: var(--text); border: 1px solid var(--border);"
                    placeholder="Nhập bản dịch tại đây...">${escapeHtml(seg.translated || '')}</textarea>
            </td>
        `;
        tbody.appendChild(tr);
    });

    container.style.display = 'block';
}

async function autoFillSuggestions() {
    if (!extractedSegments || extractedSegments.length === 0) return;

    const srcLang = document.getElementById('trans-src-lang').value;
    const tgtLang = document.getElementById('trans-tgt-lang').value;

    const textsToTranslate = extractedSegments.map(s => s.text);

    try {
        const response = await fetch('/api/translate/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                texts: textsToTranslate,
                src_lang: srcLang,
                tgt_lang: tgtLang
            })
        });

        if (!response.ok) {
            showTranslateError('Không thể lấy gợi ý bản dịch từ Google Dịch.');
            return;
        }

        const data = await response.json();
        const translations = data.translations || [];

        translations.forEach((transText, idx) => {
            if (idx < extractedSegments.length) {
                extractedSegments[idx].translated = transText;
                const inputEl = document.getElementById(`trans-input-${extractedSegments[idx].id}`);
                if (inputEl) {
                    inputEl.value = transText;
                }
            }
        });

    } catch (err) {
        showTranslateError('Lỗi kết nối khi lấy gợi ý dịch: ' + err.message);
    }
}

function exportBilingualCSV() {
    if (!extractedSegments || extractedSegments.length === 0) return;

    // Tạo CSV có UTF-8 BOM để Excel hiển thị đúng tiếng Việt
    let csvContent = '\uFEFF"STT","Van_Ban_Goc","Ban_Dich"\n';

    extractedSegments.forEach((seg, idx) => {
        const inputEl = document.getElementById(`trans-input-${seg.id}`);
        const currentTrans = inputEl ? inputEl.value : (seg.translated || '');

        const safeOrig = seg.text.replace(/"/g, '""');
        const safeTrans = currentTrans.replace(/"/g, '""');

        csvContent += `"${idx + 1}","${safeOrig}","${safeTrans}"\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const filename = `${selectedWordFile ? selectedWordFile.name.replace(/\.[^/.]+$/, "") : 'document'}_song_ngu.csv`;
    triggerDownload(blob, filename);
}

function importBilingualCSV(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split('\n');

        let filledCount = 0;
        // Bỏ qua dòng tiêu đề đầu tiên
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            // Phân tích dòng CSV cơ bản
            const matches = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g);
            if (matches && matches.length >= 3) {
                const transVal = matches[2].replace(/^"|"$/g, '').replace(/""/g, '"');
                const segIdx = i - 1;
                if (segIdx < extractedSegments.length) {
                    extractedSegments[segIdx].translated = transVal;
                    const inputEl = document.getElementById(`trans-input-${extractedSegments[segIdx].id}`);
                    if (inputEl) {
                        inputEl.value = transVal;
                        filledCount++;
                    }
                }
            }
        }
        event.target.value = '';
    };
    reader.readAsText(file, 'UTF-8');
}

async function applyManualTranslations() {
    if (!selectedWordFile || !extractedSegments || extractedSegments.length === 0) return;

    const btn = document.getElementById('btn-trans-apply');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang tạo file Word...';
    hideTranslateError();

    // Thu thập toàn bộ bản dịch từ các ô textarea
    const translations = [];
    extractedSegments.forEach(seg => {
        const inputEl = document.getElementById(`trans-input-${seg.id}`);
        const userText = inputEl ? inputEl.value : (seg.translated || '');
        translations.push({
            id: seg.id,
            text: userText
        });
    });

    const formData = new FormData();
    formData.append('file', selectedWordFile);
    formData.append('translations', JSON.stringify(translations));

    try {
        const response = await fetch('/api/translate/apply', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Lỗi khi tạo file Word từ bản dịch';
            try {
                const errJson = await response.json();
                if (errJson.error) errorMsg = errJson.error;
            } catch (_) {}
            showTranslateError(errorMsg);
            return;
        }

        const blob = await response.blob();
        let downloadName = `${selectedWordFile.name.replace(/\.[^/.]+$/, "")}_translated.docx`;
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches != null && matches[1]) {
                downloadName = matches[1].replace(/['"]/g, '');
            }
        }

        triggerDownload(blob, downloadName);

    } catch (err) {
        showTranslateError('Lỗi kết nối: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-file-earmark-check"></i> 🚀 Tạo & Tải file Word đã dịch';
    }
}


// ── TIỆN ÍCH HIỂN THỊ LỖI ───────────────────────────────────────────────────

function showTranslateError(message) {
    const errBox = document.getElementById('trans-error');
    if (errBox) {
        errBox.innerHTML = `<strong>⚠️ Thông báo:</strong> ${escapeHtml(message)}`;
        errBox.style.display = 'block';
    }
}

function hideTranslateError() {
    const errBox = document.getElementById('trans-error');
    if (errBox) {
        errBox.style.display = 'none';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;')
                      .replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;')
                      .replace(/'/g, '&#039;');
}

document.addEventListener('DOMContentLoaded', () => {
    initWordTranslateListeners();
});
