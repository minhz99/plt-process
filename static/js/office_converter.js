/**
 * POLYTEE Tools - Office ⇄ ZIP Converter Module
 * Hỗ trợ chuyển đổi hai chiều giữa Word/Excel/PowerPoint (.docx, .xlsx, .pptx, .doc, .xls, .ppt) và file ZIP.
 * Tích hợp xử lý trực tiếp trên trình duyệt (client-side JSZip) và chuyển đổi nâng cao qua máy chủ (backend COM).
 */

let officeToZipFiles = [];
let zipToDocFiles = [];

const LEGACY_EXTS = ['.doc', '.dot', '.xls', '.xlt', '.ppt', '.pot', '.pps'];
const MODERN_EXTS = ['.docx', '.docm', '.dotx', '.dotm', '.xlsx', '.xlsm', '.xltx', '.xltm', '.xlsb', '.pptx', '.pptm', '.potx', '.ppsx'];
const ALL_EXTS = [...MODERN_EXTS, ...LEGACY_EXTS];

// ── KHỞI TẠO VÀ CHUYỂN TAB ──────────────────────────────────────────────────

function switchOfficeMode(mode) {
    const btnToZip = document.getElementById('btn-office-mode-to-zip');
    const btnToDoc = document.getElementById('btn-office-mode-to-office');
    const paneToZip = document.getElementById('office-pane-to-zip');
    const paneToDoc = document.getElementById('office-pane-to-office');

    if (!btnToZip || !btnToDoc || !paneToZip || !paneToDoc) return;

    if (mode === 'to-zip') {
        btnToZip.style.background = 'var(--accent)';
        btnToZip.style.color = 'white';
        btnToDoc.style.background = 'transparent';
        btnToDoc.style.color = 'var(--text-muted)';

        paneToZip.style.display = 'block';
        paneToDoc.style.display = 'none';
    } else {
        btnToDoc.style.background = 'var(--accent4)';
        btnToDoc.style.color = 'white';
        btnToZip.style.background = 'transparent';
        btnToZip.style.color = 'var(--text-muted)';

        paneToDoc.style.display = 'block';
        paneToZip.style.display = 'none';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function getOfficeTypeInfo(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    switch (ext) {
        case '.docx':
        case '.docm':
        case '.dotx':
        case '.dotm':
            return { type: 'word', label: 'Word', color: '#3b82f6', icon: 'bi-file-earmark-word', isLegacy: false };
        case '.doc':
        case '.dot':
            return { type: 'word', label: 'Word (cũ)', color: '#2563eb', icon: 'bi-file-earmark-word', isLegacy: true };
        case '.xlsx':
        case '.xlsm':
        case '.xltx':
        case '.xltm':
        case '.xlsb':
            return { type: 'excel', label: 'Excel', color: '#10b981', icon: 'bi-file-earmark-excel', isLegacy: false };
        case '.xls':
        case '.xlt':
            return { type: 'excel', label: 'Excel (cũ)', color: '#059669', icon: 'bi-file-earmark-excel', isLegacy: true };
        case '.pptx':
        case '.pptm':
        case '.potx':
        case '.ppsx':
            return { type: 'powerpoint', label: 'PowerPoint', color: '#f97316', icon: 'bi-file-earmark-ppt', isLegacy: false };
        case '.ppt':
        case '.pot':
        case '.pps':
            return { type: 'powerpoint', label: 'PowerPoint (cũ)', color: '#ea580c', icon: 'bi-file-earmark-ppt', isLegacy: true };
        case '.zip':
            return { type: 'zip', label: 'ZIP', color: '#eab308', icon: 'bi-file-earmark-zip', isLegacy: false };
        default:
            return { type: 'unknown', label: ext.toUpperCase(), color: '#64748b', icon: 'bi-file-earmark', isLegacy: false };
    }
}

function triggerDownloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
}


// ── TAB 1: OFFICE ➔ ZIP ─────────────────────────────────────────────────────

function initOfficeToZipListeners() {
    const input = document.getElementById('office-to-zip-input');
    const dropzone = document.getElementById('office-to-zip-dropzone');
    const btnConvert = document.getElementById('btn-office-convert-to-zip');

    if (!input || !dropzone || !btnConvert) return;

    input.addEventListener('change', (e) => {
        handleOfficeToZipFiles(e.target.files);
        input.value = '';
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent)';
    });

    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(109, 40, 217, 0.45)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(109, 40, 217, 0.45)';
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleOfficeToZipFiles(e.dataTransfer.files);
        }
    });

    btnConvert.addEventListener('click', runOfficeToZipConversion);
}

function handleOfficeToZipFiles(newFiles) {
    const validList = [];

    for (let i = 0; i < newFiles.length; i++) {
        const f = newFiles[i];
        const ext = '.' + f.name.split('.').pop().toLowerCase();
        if (ALL_EXTS.includes(ext)) {
            if (!officeToZipFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
                validList.push(f);
            }
        }
    }

    if (validList.length === 0 && newFiles.length > 0) {
        showOfficeError('to-zip', 'Vui lòng chọn tệp Word (.docx, .doc), Excel (.xlsx, .xls) hoặc PowerPoint (.pptx, .ppt) hợp lệ.');
        return;
    }

    hideOfficeError('to-zip');
    officeToZipFiles = officeToZipFiles.concat(validList);
    renderOfficeToZipFileList();
}

function renderOfficeToZipFileList() {
    const container = document.getElementById('office-to-zip-file-list');
    const btnConvert = document.getElementById('btn-office-convert-to-zip');
    const btnClear = document.getElementById('btn-office-clear-to-zip');
    const statusLabel = document.getElementById('office-status-to-zip');
    const statsDiv = document.getElementById('office-stats-to-zip');

    if (statsDiv) statsDiv.style.display = 'none';

    if (!container) return;
    container.innerHTML = '';

    if (officeToZipFiles.length === 0) {
        btnConvert.disabled = true;
        btnClear.style.display = 'none';
        statusLabel.innerText = 'Chưa chọn tệp';
        return;
    }

    btnConvert.disabled = false;
    btnClear.style.display = 'inline-block';
    statusLabel.innerText = `Đã chọn ${officeToZipFiles.length} tệp`;

    officeToZipFiles.forEach((file, index) => {
        const info = getOfficeTypeInfo(file.name);
        const item = document.createElement('div');
        item.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; font-size: 0.85rem;';

        const legacyBadge = info.isLegacy ? `<span style="background: rgba(234,88,12,0.18); color: #ea580c; border: 1px solid rgba(234,88,12,0.3); border-radius: 4px; padding: 1px 6px; font-size: 0.72rem; font-weight: 500;">97-2003</span>` : '';

        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                <span style="font-size: 1.1rem; color: ${info.color};"><i class="bi ${info.icon}"></i></span>
                <span style="font-weight: 500; color: var(--text); overflow: hidden; text-overflow: ellipsis;">${escapeHtml(file.name)}</span>
                <span style="background: ${info.color}22; color: ${info.color}; border: 1px solid ${info.color}44; border-radius: 4px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600;">${info.label}</span>
                ${legacyBadge}
                <span style="color: var(--text-muted); font-size: 0.78rem;">(${formatFileSize(file.size)})</span>
            </div>
            <button type="button" onclick="removeOfficeToZipFile(${index})" style="background: transparent; border: none; color: var(--danger); cursor: pointer; padding: 4px 8px; font-size: 0.9rem;" title="Xóa tệp">
                <i class="bi bi-x-circle"></i>
            </button>
        `;
        container.appendChild(item);
    });
}

function removeOfficeToZipFile(index) {
    officeToZipFiles.splice(index, 1);
    renderOfficeToZipFileList();
}

function clearOfficeToZipList() {
    officeToZipFiles = [];
    renderOfficeToZipFileList();
    hideOfficeError('to-zip');
}

async function runOfficeToZipConversion() {
    if (officeToZipFiles.length === 0) return;

    const btn = document.getElementById('btn-office-convert-to-zip');
    const spinner = document.getElementById('office-spinner-to-zip');
    const btnText = document.getElementById('office-btn-text-to-zip');
    const extractMedia = document.getElementById('office-opt-extract-media').checked;
    const statsDiv = document.getElementById('office-stats-to-zip');
    const statsText = document.getElementById('office-stats-to-zip-text');

    hideOfficeError('to-zip');
    if (statsDiv) statsDiv.style.display = 'none';

    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.innerText = 'Đang xử lý...';

    // Kiểm tra xem có file định dạng cũ (.doc, .xls, .ppt) hay không
    const hasLegacyFiles = officeToZipFiles.some(f => {
        const ext = '.' + f.name.split('.').pop().toLowerCase();
        return LEGACY_EXTS.includes(ext);
    });

    // Nếu không có file cũ và có thư viện JSZip trên client, xử lý trực tiếp trên trình duyệt
    if (!hasLegacyFiles && typeof JSZip !== 'undefined') {
        try {
            await convertOfficeToZipClientSide(officeToZipFiles, extractMedia, statsDiv, statsText);
            btn.disabled = false;
            spinner.style.display = 'none';
            btnText.innerText = '🚀 Bắt đầu chuyển sang ZIP';
            return;
        } catch (clientErr) {
            console.warn('Client-side conversion fallback to server API:', clientErr);
            // Tiếp tục gọi backend nếu xử lý client gặp ngoại lệ
        }
    }

    // Gửi lên backend (áp dụng cho file cũ .doc, .xls, .ppt hoặc khi client-side fallback)
    const formData = new FormData();
    officeToZipFiles.forEach(file => {
        formData.append('files', file);
    });
    formData.append('extract_media_only', extractMedia ? 'true' : 'false');

    try {
        const response = await fetch('/api/office/to-zip', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Có lỗi xảy ra khi chuyển đổi';
            try {
                const errJson = await response.json();
                if (errJson.error) errorMsg = errJson.error;
                if (errJson.stats && errJson.stats.errors && errJson.stats.errors.length > 0) {
                    errorMsg += ': ' + errJson.stats.errors.join('; ');
                }
            } catch (_) {}
            showOfficeError('to-zip', errorMsg);
            return;
        }

        const statsHeader = response.headers.get('X-Office-Stats');
        let stats = null;
        if (statsHeader) {
            try { stats = JSON.parse(statsHeader); } catch (_) {}
        }

        const blob = await response.blob();
        let downloadFilename = 'office_converted.zip';
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches != null && matches[1]) {
                downloadFilename = matches[1].replace(/['"]/g, '');
            }
        }

        triggerDownloadBlob(blob, downloadFilename);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            let summary = `Đã chuyển đổi thành công <strong>${stats ? stats.success : officeToZipFiles.length}</strong> tệp tin.`;
            if (extractMedia && stats && stats.media_count !== undefined) {
                summary += ` Đã trích xuất tổng cộng <strong>${stats.media_count}</strong> tệp hình ảnh/media.`;
            }
            summary += ` File tải về: <code>${downloadFilename}</code> (${formatFileSize(blob.size)})`;
            statsText.innerHTML = summary;
        }

    } catch (err) {
        let msg = err.message;
        if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
            msg = 'Không thể kết nối đến máy chủ PLT Process (server chưa khởi động hoặc bị ngắt kết nối). Vui lòng đảm bảo bạn đã mở và chạy file START.cmd trên máy tính!';
        }
        showOfficeError('to-zip', msg);
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.innerText = '🚀 Bắt đầu chuyển sang ZIP';
    }
}

/**
 * Xử lý chuyển đổi Office sang ZIP ngay trên Client bằng JSZip (cực nhanh, không cần upload mạng)
 */
async function convertOfficeToZipClientSide(files, extractMedia, statsDiv, statsText) {
    if (extractMedia) {
        // Trích xuất toàn bộ media từ các file
        let totalMediaCount = 0;
        const masterZip = new JSZip();

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const baseName = file.name.replace(/\.[^/.]+$/, "");
            const zip = new JSZip();
            const docData = await zip.loadAsync(file);

            let fileMediaCount = 0;
            const entries = Object.keys(docData.files);

            for (const entryName of entries) {
                const entry = docData.files[entryName];
                if (entry.dir) continue;
                const parts = entryName.replace(/\\/g, '/').split('/');
                if (parts.includes('media')) {
                    fileMediaCount++;
                    totalMediaCount++;
                    const mediaBlob = await entry.async('blob');
                    const imgName = parts[parts.length - 1];
                    const folderPrefix = files.length > 1 ? `${baseName}/` : '';
                    masterZip.file(`${folderPrefix}${imgName}`, mediaBlob);
                }
            }
        }

        if (totalMediaCount === 0) {
            throw new Error("Không tìm thấy hình ảnh/media nào trong các tài liệu đã chọn.");
        }

        const outBlob = await masterZip.generateAsync({ type: 'blob' });
        const downloadName = files.length === 1 ? `${files[0].name.replace(/\.[^/.]+$/, "")}_media.zip` : 'office_media_extracted.zip';
        triggerDownloadBlob(outBlob, downloadName);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            statsText.innerHTML = `Đã trích xuất thành công <strong>${totalMediaCount}</strong> hình ảnh từ <strong>${files.length}</strong> tệp tin. Tải về: <code>${downloadName}</code> (${formatFileSize(outBlob.size)})`;
        }
        return;
    }

    // Đổi sang file ZIP đầy đủ
    if (files.length === 1) {
        // 1 file duy nhất: Tải trực tiếp Blob với định dạng zip
        const file = files[0];
        const baseName = file.name.replace(/\.[^/.]+$/, "");
        const zipBlob = new Blob([file], { type: 'application/zip' });
        const downloadName = `${baseName}.zip`;
        triggerDownloadBlob(zipBlob, downloadName);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            statsText.innerHTML = `Đã chuyển đổi <strong>${file.name}</strong> sang file ZIP thành công! Tải về: <code>${downloadName}</code> (${formatFileSize(zipBlob.size)})`;
        }
    } else {
        // Nhiều file: Gộp vào một master ZIP
        const masterZip = new JSZip();
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const baseName = file.name.replace(/\.[^/.]+$/, "");
            masterZip.file(`${baseName}.zip`, file);
        }
        const outBlob = await masterZip.generateAsync({ type: 'blob' });
        const downloadName = 'office_to_zip_batch.zip';
        triggerDownloadBlob(outBlob, downloadName);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            statsText.innerHTML = `Đã chuyển đổi thành công <strong>${files.length}</strong> tệp Office sang ZIP. Tải về: <code>${downloadName}</code> (${formatFileSize(outBlob.size)})`;
        }
    }
}


// ── TAB 2: ZIP ➔ OFFICE ─────────────────────────────────────────────────────

function initZipToOfficeListeners() {
    const input = document.getElementById('office-to-doc-input');
    const dropzone = document.getElementById('office-to-doc-dropzone');
    const btnConvert = document.getElementById('btn-office-convert-to-doc');

    if (!input || !dropzone || !btnConvert) return;

    input.addEventListener('change', (e) => {
        handleZipToDocFiles(e.target.files);
        input.value = '';
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent4)';
    });

    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(245, 158, 11, 0.45)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'rgba(245, 158, 11, 0.45)';
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleZipToDocFiles(e.dataTransfer.files);
        }
    });

    btnConvert.addEventListener('click', runZipToOfficeConversion);
}

async function handleZipToDocFiles(newFiles) {
    const validList = [];

    for (let i = 0; i < newFiles.length; i++) {
        const f = newFiles[i];
        if (f.name.toLowerCase().endsWith('.zip')) {
            if (!zipToDocFiles.some(existing => existing.file.name === f.name && existing.file.size === f.size)) {
                validList.push({
                    file: f,
                    detectedType: 'Đang kiểm tra...',
                    suggestedExt: '.docx',
                    isNested: false
                });
            }
        }
    }

    if (validList.length === 0 && newFiles.length > 0) {
        showOfficeError('to-doc', 'Vui lòng chọn tệp tin định dạng .zip');
        return;
    }

    hideOfficeError('to-doc');
    zipToDocFiles = zipToDocFiles.concat(validList);
    renderZipToDocFileList();

    for (let i = 0; i < validList.length; i++) {
        const item = validList[i];
        await inspectZipOnClient(item);
        renderZipToDocFileList();
    }
}

async function inspectZipOnClient(item) {
    if (typeof JSZip === 'undefined') {
        item.detectedType = 'Tự động';
        return;
    }

    try {
        const zip = new JSZip();
        const zipData = await zip.loadAsync(item.file);
        const entries = Object.keys(zipData.files).map(name => name.replace(/\\/g, '/'));

        const partsList = entries.filter(e => !zipData.files[e].dir).map(e => e.split('/'));
        const firstParts = new Set(partsList.filter(p => p.length > 1).map(p => p[0]));
        let prefix = '';
        if (firstParts.size === 1 && partsList.every(p => p.length > 1)) {
            prefix = Array.from(firstParts)[0] + '/';
            item.isNested = true;
        }

        const unwrapped = entries.map(e => prefix ? (e.startsWith(prefix) ? e.slice(prefix.length) : e) : e);

        const hasWord = unwrapped.some(e => e.startsWith('word/') || e === 'word');
        const hasExcel = unwrapped.some(e => e.startsWith('xl/') || e === 'xl');
        const hasPPT = unwrapped.some(e => e.startsWith('ppt/') || e === 'ppt');
        const hasMacros = unwrapped.some(e => e.includes('vbaProject.bin'));

        if (hasWord) {
            item.detectedType = 'Word';
            item.suggestedExt = hasMacros ? '.docm' : '.docx';
        } else if (hasExcel) {
            item.detectedType = 'Excel';
            item.suggestedExt = hasMacros ? '.xlsm' : '.xlsx';
        } else if (hasPPT) {
            item.detectedType = 'PowerPoint';
            item.suggestedExt = hasMacros ? '.pptm' : '.pptx';
        } else {
            item.detectedType = 'Word';
            item.suggestedExt = '.docx';
        }
    } catch (e) {
        item.detectedType = 'Không xác định';
        item.suggestedExt = '.docx';
    }
}

function renderZipToDocFileList() {
    const container = document.getElementById('office-to-doc-file-list');
    const btnConvert = document.getElementById('btn-office-convert-to-doc');
    const btnClear = document.getElementById('btn-office-clear-to-doc');
    const statusLabel = document.getElementById('office-status-to-doc');
    const statsDiv = document.getElementById('office-stats-to-doc');

    if (statsDiv) statsDiv.style.display = 'none';

    if (!container) return;
    container.innerHTML = '';

    if (zipToDocFiles.length === 0) {
        btnConvert.disabled = true;
        btnClear.style.display = 'none';
        statusLabel.innerText = 'Chưa chọn tệp';
        return;
    }

    btnConvert.disabled = false;
    btnClear.style.display = 'inline-block';
    statusLabel.innerText = `Đã chọn ${zipToDocFiles.length} tệp ZIP`;

    zipToDocFiles.forEach((item, index) => {
        const file = item.file;
        const div = document.createElement('div');
        div.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; font-size: 0.85rem; flex-wrap: wrap; gap: 8px;';

        let badgeColor = '#3b82f6';
        let badgeIcon = 'bi-file-earmark-word';
        if (item.detectedType === 'Excel') {
            badgeColor = '#10b981';
            badgeIcon = 'bi-file-earmark-excel';
        } else if (item.detectedType === 'PowerPoint') {
            badgeColor = '#f97316';
            badgeIcon = 'bi-file-earmark-ppt';
        }

        const nestedBadge = item.isNested ? `<span style="background: rgba(245,158,11,0.18); color: var(--accent4); border: 1px solid rgba(245,158,11,0.3); border-radius: 4px; padding: 1px 6px; font-size: 0.72rem; font-weight: 500;" title="Phát hiện tệp bị bọc trong thư mục lồng (thường do nén bằng Windows)"><i class="bi bi-layers"></i> Tự sửa lồng thư mục</span>` : '';

        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 240px;">
                <span style="font-size: 1.1rem; color: var(--accent4);"><i class="bi bi-file-earmark-zip"></i></span>
                <span style="font-weight: 500; color: var(--text); overflow: hidden; text-overflow: ellipsis;">${escapeHtml(file.name)}</span>
                <span style="background: ${badgeColor}22; color: ${badgeColor}; border: 1px solid ${badgeColor}44; border-radius: 4px; padding: 1px 6px; font-size: 0.72rem; font-weight: 600;">
                    <i class="bi ${badgeIcon}"></i> ${item.detectedType} (${item.suggestedExt})
                </span>
                ${nestedBadge}
                <span style="color: var(--text-muted); font-size: 0.78rem;">(${formatFileSize(file.size)})</span>
            </div>
            <button type="button" onclick="removeZipToDocFile(${index})" style="background: transparent; border: none; color: var(--danger); cursor: pointer; padding: 4px 8px; font-size: 0.9rem;" title="Xóa tệp">
                <i class="bi bi-x-circle"></i>
            </button>
        `;
        container.appendChild(div);
    });
}

function removeZipToDocFile(index) {
    zipToDocFiles.splice(index, 1);
    renderZipToDocFileList();
}

function clearOfficeToDocList() {
    zipToDocFiles = [];
    renderZipToDocFileList();
    hideOfficeError('to-doc');
}

async function runZipToOfficeConversion() {
    if (zipToDocFiles.length === 0) return;

    const btn = document.getElementById('btn-office-convert-to-doc');
    const spinner = document.getElementById('office-spinner-to-doc');
    const btnText = document.getElementById('office-btn-text-to-doc');
    const targetFormat = document.getElementById('office-target-format').value;
    const autoFlatten = document.getElementById('office-opt-auto-flatten').checked;
    const statsDiv = document.getElementById('office-stats-to-doc');
    const statsText = document.getElementById('office-stats-to-doc-text');

    hideOfficeError('to-doc');
    if (statsDiv) statsDiv.style.display = 'none';

    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.innerText = 'Đang chuyển đổi...';

    // Nếu chọn định dạng cũ (.doc, .xls, .ppt): bắt buộc dùng server COM
    const isLegacyTarget = ['doc', 'xls', 'ppt'].includes(targetFormat);

    // Nếu chuyển sang định dạng mới (.docx, .xlsx, .pptx) và có JSZip trên client, xử lý trực tiếp
    if (!isLegacyTarget && typeof JSZip !== 'undefined') {
        try {
            await convertZipToOfficeClientSide(zipToDocFiles, targetFormat, autoFlatten, statsDiv, statsText);
            btn.disabled = false;
            spinner.style.display = 'none';
            btnText.innerText = '🚀 Chuyển sang tài liệu Office';
            return;
        } catch (clientErr) {
            console.warn('Client-side zip to office fallback to server API:', clientErr);
        }
    }

    const formData = new FormData();
    zipToDocFiles.forEach(item => {
        formData.append('files', item.file);
    });
    formData.append('target_format', targetFormat);
    formData.append('auto_flatten', autoFlatten ? 'true' : 'false');

    try {
        const response = await fetch('/api/office/to-office', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorMsg = 'Có lỗi xảy ra khi chuyển đổi sang Office';
            try {
                const errJson = await response.json();
                if (errJson.error) errorMsg = errJson.error;
                if (errJson.stats && errJson.stats.errors && errJson.stats.errors.length > 0) {
                    errorMsg += ': ' + errJson.stats.errors.join('; ');
                }
            } catch (_) {}
            showOfficeError('to-doc', errorMsg);
            return;
        }

        const statsHeader = response.headers.get('X-Office-Stats');
        let stats = null;
        if (statsHeader) {
            try { stats = JSON.parse(statsHeader); } catch (_) {}
        }

        const blob = await response.blob();
        let downloadFilename = 'converted_document.docx';
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.indexOf('filename=') !== -1) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
            if (matches != null && matches[1]) {
                downloadFilename = matches[1].replace(/['"]/g, '');
            }
        }

        triggerDownloadBlob(blob, downloadFilename);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            let summary = `Đã chuyển đổi thành công <strong>${stats ? stats.success : zipToDocFiles.length}</strong> tệp tin.`;
            if (stats && stats.items && stats.items.length > 0) {
                const names = stats.items.map(it => `<code>${it.converted}</code>`).join(', ');
                summary += ` Kết quả: ${names}`;
            }
            statsText.innerHTML = summary;
        }

    } catch (err) {
        let msg = err.message;
        if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
            msg = 'Không thể kết nối đến máy chủ PLT Process (server chưa khởi động hoặc bị ngắt kết nối). Vui lòng kiểm tra và chạy file START.cmd trên máy tính!';
        }
        showOfficeError('to-doc', msg);
    } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
        btnText.innerText = '🚀 Chuyển sang tài liệu Office';
    }
}

/**
 * Xử lý chuyển đổi ZIP sang Office ngay trên Client bằng JSZip
 */
async function convertZipToOfficeClientSide(items, targetFormat, autoFlatten, statsDiv, statsText) {
    const results = [];

    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const file = item.file;
        const baseName = file.name.replace(/\.zip$/i, "");
        const zip = new JSZip();
        const zipData = await zip.loadAsync(file);

        let finalExt = targetFormat !== 'auto' ? `.${targetFormat}` : item.suggestedExt;

        let outBlob = null;
        if (autoFlatten && item.isNested) {
            // Làm phẳng thư mục lồng
            const cleanZip = new JSZip();
            const entries = Object.keys(zipData.files);
            const prefix = entries[0].split('/')[0] + '/';

            for (const name of entries) {
                const entry = zipData.files[name];
                if (entry.dir) continue;
                if (name.startsWith(prefix)) {
                    const cleanName = name.slice(prefix.length);
                    if (cleanName) {
                        const content = await entry.async('blob');
                        cleanZip.file(cleanName, content);
                    }
                }
            }
            outBlob = await cleanZip.generateAsync({ type: 'blob' });
        } else {
            outBlob = file;
        }

        results.push({
            name: `${baseName}${finalExt}`,
            blob: outBlob
        });
    }

    if (results.length === 1) {
        triggerDownloadBlob(results[0].blob, results[0].name);
        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            statsText.innerHTML = `Đã chuyển đổi thành công tệp: <code>${results[0].name}</code> (${formatFileSize(results[0].blob.size)})`;
        }
    } else {
        const masterZip = new JSZip();
        for (const res of results) {
            masterZip.file(res.name, res.blob);
        }
        const masterBlob = await masterZip.generateAsync({ type: 'blob' });
        const batchName = 'converted_office_documents.zip';
        triggerDownloadBlob(masterBlob, batchName);

        if (statsDiv && statsText) {
            statsDiv.style.display = 'block';
            statsText.innerHTML = `Đã chuyển đổi thành công <strong>${results.length}</strong> tệp tin. Tải về: <code>${batchName}</code>`;
        }
    }
}


// ── TIỆN ÍCH HIỂN THỊ LỖI ───────────────────────────────────────────────────

function showOfficeError(pane, message) {
    const errBox = document.getElementById(pane === 'to-zip' ? 'office-error-to-zip' : 'office-error-to-doc');
    if (errBox) {
        errBox.innerHTML = `<strong>⚠️ Lỗi:</strong> ${escapeHtml(message)}`;
        errBox.style.display = 'block';
    }
}

function hideOfficeError(pane) {
    const errBox = document.getElementById(pane === 'to-zip' ? 'office-error-to-zip' : 'office-error-to-doc');
    if (errBox) {
        errBox.style.display = 'none';
    }
}

function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;')
                      .replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;')
                      .replace(/'/g, '&#039;');
}


// ── TỰ ĐỘNG KHỞI CHẠY KHI DOM SẴN SÀNG ─────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initOfficeToZipListeners();
    initZipToOfficeListeners();
});
