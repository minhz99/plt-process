/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  QR CODE GENERATOR — Frontend Handler (Enhanced)
 *  Preview realtime, download PNG/SVG, batch ZIP, logo nâng cao,
 *  gradient, label, clipboard, presets, transparent
 * ═══════════════════════════════════════════════════════════════════════════
 */

/* ── State ───────────────────────────────────────────────────────────────── */
let _qrCurrentType = 'url';
let _qrPreviewTimer = null;
let _qrLogoFile = null;
let _qrIsDownloading = false;
let _qrLogoFrame = 'rounded';

/* ── Initialisation ──────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    // Type tabs
    document.querySelectorAll('#qr-type-tabs .qr-type-btn').forEach(btn => {
        btn.addEventListener('click', () => _qrSwitchType(btn.dataset.type));
    });

    // Color pickers sync
    _qrSyncColors('qr-fg-color', 'qr-fg-color-text');
    _qrSyncColors('qr-bg-color', 'qr-bg-color-text');
    _qrSyncColors('qr-fg-color2', 'qr-fg-color2-text');
    _qrSyncColors('qr-logo-bg-color', 'qr-logo-bg-color-text');

    // Size slider
    const sizeSlider = document.getElementById('qr-size');
    if (sizeSlider) {
        sizeSlider.addEventListener('input', () => {
            document.getElementById('qr-size-value').textContent = sizeSlider.value + 'px';
            _qrSchedulePreview();
        });
    }

    // Error correction
    const ecSelect = document.getElementById('qr-error-correction');
    if (ecSelect) ecSelect.addEventListener('change', () => _qrSchedulePreview());

    // Logo input
    const logoInput = document.getElementById('qr-logo-input');
    if (logoInput) {
        logoInput.addEventListener('change', e => {
            const file = e.target.files[0];
            if (file) {
                _qrLogoFile = file;
                const reader = new FileReader();
                reader.onload = ev => {
                    document.getElementById('qr-logo-img').src = ev.target.result;
                    document.getElementById('qr-logo-img').style.display = 'block';
                    document.getElementById('qr-logo-placeholder').style.display = 'none';
                    document.getElementById('qr-logo-remove').style.display = 'inline-block';
                    _qrShowLogoOptions(true);
                };
                reader.readAsDataURL(file);
                _qrSchedulePreview();
            }
        });
    }

    // Batch toggle
    const batchToggle = document.getElementById('qr-batch-toggle');
    if (batchToggle) {
        batchToggle.addEventListener('change', () => {
            const batchArea = document.getElementById('qr-batch-area');
            const batchBtn = document.getElementById('btn-qr-batch-download');
            if (batchToggle.checked) {
                batchArea.style.display = 'block';
                batchBtn.style.display = 'flex';
            } else {
                batchArea.style.display = 'none';
                batchBtn.style.display = 'none';
            }
        });
    }

    // Gradient toggle
    const gradientToggle = document.getElementById('qr-gradient-toggle');
    if (gradientToggle) {
        gradientToggle.addEventListener('change', () => {
            document.getElementById('qr-gradient-area').style.display = gradientToggle.checked ? 'block' : 'none';
            _qrUpdateGradientBar();
            _qrSchedulePreview();
        });
    }

    // Gradient color2 change → update preview bar
    const fgColor2 = document.getElementById('qr-fg-color2');
    if (fgColor2) {
        fgColor2.addEventListener('input', _qrUpdateGradientBar);
    }
    const fgColor = document.getElementById('qr-fg-color');
    if (fgColor) {
        fgColor.addEventListener('input', _qrUpdateGradientBar);
    }

    // Logo opacity slider
    const opacitySlider = document.getElementById('qr-logo-opacity');
    if (opacitySlider) {
        opacitySlider.addEventListener('input', () => {
            document.getElementById('qr-logo-opacity-value').textContent = opacitySlider.value + '%';
            _qrSchedulePreview();
        });
    }

    // Logo scale slider
    const scaleSlider = document.getElementById('qr-logo-scale');
    if (scaleSlider) {
        scaleSlider.addEventListener('input', () => {
            document.getElementById('qr-logo-scale-value').textContent = scaleSlider.value + '%';
            _qrSchedulePreview();
        });
    }

    // Logo bg transparent checkbox
    const logoBgTransparent = document.getElementById('qr-logo-bg-transparent');
    if (logoBgTransparent) {
        logoBgTransparent.addEventListener('change', () => _qrSchedulePreview());
    }

    // Transparent bg checkbox
    const transparentBg = document.getElementById('qr-transparent-bg');
    if (transparentBg) {
        transparentBg.addEventListener('change', () => _qrSchedulePreview());
    }

    // Label text
    const labelText = document.getElementById('qr-label-text');
    if (labelText) {
        labelText.addEventListener('input', () => _qrSchedulePreview());
    }

    // Auto-preview on input: attach listeners to all qr-input elements
    _qrAttachInputListeners();
});


/* ── Type switching ──────────────────────────────────────────────────────── */
function _qrSwitchType(type) {
    _qrCurrentType = type;

    // Update tabs
    document.querySelectorAll('#qr-type-tabs .qr-type-btn').forEach(btn => {
        if (btn.dataset.type === type) {
            btn.style.background = 'linear-gradient(135deg, var(--accent), var(--accent2))';
            btn.style.color = 'white';
            btn.style.borderColor = 'transparent';
            btn.classList.add('active');
        } else {
            btn.style.background = 'var(--surface2)';
            btn.style.color = 'var(--text)';
            btn.style.borderColor = 'var(--border)';
            btn.classList.remove('active');
        }
    });

    // Show/hide field groups
    document.querySelectorAll('#qr-fields .qr-field-group').forEach(g => {
        g.style.display = 'none';
    });
    const group = document.getElementById('qr-fields-' + type);
    if (group) group.style.display = 'block';

    _qrSchedulePreview();
}


/* ── Get data from current form ──────────────────────────────────────────── */
function _qrGetFormData() {
    const type = _qrCurrentType;
    let data = '';
    let extra = {};

    switch (type) {
        case 'url':
            data = (document.getElementById('qr-data-url')?.value || '').trim();
            break;
        case 'text':
            data = (document.getElementById('qr-data-text')?.value || '').trim();
            break;
        case 'email':
            data = (document.getElementById('qr-data-email')?.value || '').trim();
            extra.subject = (document.getElementById('qr-data-email-subject')?.value || '').trim();
            extra.body = (document.getElementById('qr-data-email-body')?.value || '').trim();
            break;
        case 'phone':
            data = (document.getElementById('qr-data-phone')?.value || '').trim();
            break;
        case 'wifi':
            data = (document.getElementById('qr-data-wifi-ssid')?.value || '').trim();
            extra.password = document.getElementById('qr-data-wifi-password')?.value || '';
            extra.encryption = document.getElementById('qr-data-wifi-encryption')?.value || 'WPA';
            extra.hidden = document.getElementById('qr-data-wifi-hidden')?.checked || false;
            break;
        case 'vcard':
            data = (document.getElementById('qr-data-vcard-name')?.value || '').trim();
            extra.phone = (document.getElementById('qr-data-vcard-phone')?.value || '').trim();
            extra.email = (document.getElementById('qr-data-vcard-email')?.value || '').trim();
            extra.org = (document.getElementById('qr-data-vcard-org')?.value || '').trim();
            extra.title = (document.getElementById('qr-data-vcard-title')?.value || '').trim();
            extra.url = (document.getElementById('qr-data-vcard-url')?.value || '').trim();
            extra.address = (document.getElementById('qr-data-vcard-address')?.value || '').trim();
            break;
        case 'sms':
            data = (document.getElementById('qr-data-sms-phone')?.value || '').trim();
            extra.body = (document.getElementById('qr-data-sms-body')?.value || '').trim();
            break;
    }

    return { data, data_type: type, extra };
}


function _qrGetSettings() {
    return {
        size: document.getElementById('qr-size')?.value || '400',
        fg_color: document.getElementById('qr-fg-color')?.value || '#000000',
        bg_color: document.getElementById('qr-bg-color')?.value || '#ffffff',
        error_correction: document.getElementById('qr-error-correction')?.value || 'H',
    };
}


function _qrGetLogoOptions() {
    return {
        logo_frame: _qrLogoFrame,
        logo_opacity: (parseInt(document.getElementById('qr-logo-opacity')?.value || '100') / 100).toString(),
        logo_scale: (parseInt(document.getElementById('qr-logo-scale')?.value || '25') / 100).toString(),
        logo_bg_color: document.getElementById('qr-logo-bg-color')?.value || '#ffffff',
        logo_bg_transparent: document.getElementById('qr-logo-bg-transparent')?.checked ? 'true' : 'false',
    };
}


function _qrGetAdvancedOptions() {
    const gradientOn = document.getElementById('qr-gradient-toggle')?.checked || false;
    return {
        fg_color2: gradientOn ? (document.getElementById('qr-fg-color2')?.value || '') : '',
        label_text: document.getElementById('qr-label-text')?.value || '',
        transparent_bg: document.getElementById('qr-transparent-bg')?.checked ? 'true' : 'false',
    };
}


function _qrBuildFormData(includeFormat) {
    const { data, data_type, extra } = _qrGetFormData();
    const settings = _qrGetSettings();
    const logoOpts = _qrGetLogoOptions();
    const advOpts = _qrGetAdvancedOptions();

    const formData = new FormData();
    formData.append('data', data);
    formData.append('data_type', data_type);
    formData.append('extra', JSON.stringify(extra));
    formData.append('size', settings.size);
    formData.append('fg_color', settings.fg_color);
    formData.append('bg_color', settings.bg_color);
    formData.append('error_correction', settings.error_correction);

    // Logo options
    formData.append('logo_frame', logoOpts.logo_frame);
    formData.append('logo_opacity', logoOpts.logo_opacity);
    formData.append('logo_scale', logoOpts.logo_scale);
    formData.append('logo_bg_color', logoOpts.logo_bg_color);
    formData.append('logo_bg_transparent', logoOpts.logo_bg_transparent);

    // Advanced
    formData.append('fg_color2', advOpts.fg_color2);
    formData.append('label_text', advOpts.label_text);
    formData.append('transparent_bg', advOpts.transparent_bg);

    if (_qrLogoFile) {
        formData.append('logo', _qrLogoFile);
    }

    if (includeFormat) {
        formData.append('format', includeFormat);
    }

    return { formData, data };
}


/* ── Preview (debounced) ─────────────────────────────────────────────────── */
function _qrSchedulePreview() {
    if (_qrPreviewTimer) clearTimeout(_qrPreviewTimer);
    _qrPreviewTimer = setTimeout(_qrDoPreview, 500);
}


async function _qrDoPreview() {
    const { formData, data } = _qrBuildFormData(null);

    const previewImg = document.getElementById('qr-preview-img');
    const placeholder = document.getElementById('qr-preview-placeholder');
    const spinner = document.getElementById('qr-preview-spinner');
    const btnPng = document.getElementById('btn-qr-download-png');
    const btnSvg = document.getElementById('btn-qr-download-svg');
    const btnCopy = document.getElementById('btn-qr-copy');

    if (!data) {
        previewImg.style.display = 'none';
        placeholder.style.display = 'block';
        btnPng.disabled = true;
        btnSvg.disabled = true;
        btnCopy.disabled = true;
        return;
    }

    placeholder.style.display = 'none';
    spinner.style.display = 'block';

    try {
        const res = await fetch('/api/qr/preview', { method: 'POST', body: formData });
        const json = await res.json();

        spinner.style.display = 'none';

        if (res.ok && json.image) {
            previewImg.src = json.image;
            previewImg.style.display = 'block';
            btnPng.disabled = false;
            btnSvg.disabled = false;
            btnCopy.disabled = false;
            _qrHideError();
        } else {
            previewImg.style.display = 'none';
            placeholder.style.display = 'block';
            _qrShowError(json.error || 'Lỗi tạo mã QR');
        }
    } catch (err) {
        spinner.style.display = 'none';
        placeholder.style.display = 'block';
        _qrShowError('Không thể kết nối server: ' + err.message);
    }
}


/* ── Download single QR ──────────────────────────────────────────────────── */
async function qrDownload(format) {
    if (_qrIsDownloading) return;
    _qrIsDownloading = true;

    const { formData, data } = _qrBuildFormData(format);

    if (!data) {
        _qrShowError('Vui lòng nhập nội dung cho mã QR');
        _qrIsDownloading = false;
        return;
    }

    const downloadSpinner = document.getElementById('qr-download-spinner');
    if (downloadSpinner) downloadSpinner.style.display = 'inline-block';

    try {
        const res = await fetch('/api/qr/generate', { method: 'POST', body: formData });

        if (!res.ok) {
            const json = await res.json();
            _qrShowError(json.error || 'Lỗi tạo mã QR');
            return;
        }

        const blob = await res.blob();
        const ext = format === 'svg' ? 'svg' : 'png';
        _qrTriggerDownload(blob, `qrcode.${ext}`);
        _qrHideError();
    } catch (err) {
        _qrShowError('Không thể tải file: ' + err.message);
    } finally {
        if (downloadSpinner) downloadSpinner.style.display = 'none';
        _qrIsDownloading = false;
    }
}


/* ── Copy to clipboard ───────────────────────────────────────────────────── */
async function qrCopyToClipboard() {
    const previewImg = document.getElementById('qr-preview-img');
    if (!previewImg || !previewImg.src) return;

    const copyIcon = document.getElementById('qr-copy-icon');
    const copyText = document.getElementById('qr-copy-text');

    try {
        // Fetch image as blob from the preview base64 data
        const res = await fetch(previewImg.src);
        const blob = await res.blob();

        // Use Clipboard API
        await navigator.clipboard.write([
            new ClipboardItem({ 'image/png': blob })
        ]);

        // Visual feedback
        if (copyIcon) copyIcon.className = 'bi bi-check-lg';
        if (copyText) copyText.textContent = 'Đã sao chép!';
        setTimeout(() => {
            if (copyIcon) copyIcon.className = 'bi bi-clipboard';
            if (copyText) copyText.textContent = 'Sao chép vào clipboard';
        }, 2000);
    } catch (err) {
        // Fallback: try canvas approach
        try {
            const canvas = document.createElement('canvas');
            const img = new window.Image();
            img.crossOrigin = 'anonymous';
            await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
                img.src = previewImg.src;
            });
            canvas.width = img.width;
            canvas.height = img.height;
            canvas.getContext('2d').drawImage(img, 0, 0);
            canvas.toBlob(async (blob) => {
                try {
                    await navigator.clipboard.write([
                        new ClipboardItem({ 'image/png': blob })
                    ]);
                    if (copyIcon) copyIcon.className = 'bi bi-check-lg';
                    if (copyText) copyText.textContent = 'Đã sao chép!';
                    setTimeout(() => {
                        if (copyIcon) copyIcon.className = 'bi bi-clipboard';
                        if (copyText) copyText.textContent = 'Sao chép vào clipboard';
                    }, 2000);
                } catch (e2) {
                    _qrShowError('Trình duyệt không hỗ trợ sao chép ảnh vào clipboard');
                }
            }, 'image/png');
        } catch (e3) {
            _qrShowError('Không thể sao chép: ' + err.message);
        }
    }
}


/* ── Batch download ──────────────────────────────────────────────────────── */
async function qrBatchDownload() {
    if (_qrIsDownloading) return;

    const batchText = (document.getElementById('qr-batch-data')?.value || '').trim();
    if (!batchText) {
        _qrShowError('Vui lòng nhập nội dung cho các mã QR (mỗi dòng một nội dung)');
        return;
    }

    const lines = batchText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    if (lines.length === 0) {
        _qrShowError('Không tìm thấy nội dung hợp lệ');
        return;
    }

    _qrIsDownloading = true;
    const settings = _qrGetSettings();
    const advOpts = _qrGetAdvancedOptions();
    const dataType = _qrCurrentType;

    const items = lines.map(line => ({ data: line, data_type: dataType }));

    const progressEl = document.getElementById('qr-batch-progress');
    const stepEl = document.getElementById('qr-batch-step');
    const percentEl = document.getElementById('qr-batch-percent');
    const barEl = document.getElementById('qr-batch-bar');
    progressEl.style.display = 'block';
    stepEl.textContent = `Đang tạo ${items.length} mã QR...`;
    percentEl.textContent = '0%';
    barEl.style.width = '0%';

    const formData = new FormData();
    formData.append('items', JSON.stringify(items));
    formData.append('size', settings.size);
    formData.append('fg_color', settings.fg_color);
    formData.append('bg_color', settings.bg_color);
    formData.append('error_correction', settings.error_correction);
    formData.append('format', 'png');
    formData.append('fg_color2', advOpts.fg_color2);
    formData.append('label_text', advOpts.label_text);
    formData.append('transparent_bg', advOpts.transparent_bg);

    let faux = 0;
    const fauxTimer = setInterval(() => {
        faux = Math.min(faux + 2, 90);
        barEl.style.width = faux + '%';
        percentEl.textContent = faux + '%';
    }, 100);

    try {
        const res = await fetch('/api/qr/batch', { method: 'POST', body: formData });

        clearInterval(fauxTimer);

        if (!res.ok) {
            const json = await res.json();
            _qrShowError(json.error || 'Lỗi tạo hàng loạt');
            return;
        }

        barEl.style.width = '100%';
        percentEl.textContent = '100%';

        const statsHeader = res.headers.get('X-QR-Stats');
        if (statsHeader) {
            try {
                const stats = JSON.parse(statsHeader);
                stepEl.textContent = `Hoàn thành: ${stats.success}/${stats.total} mã QR`;
                if (stats.errors?.length > 0) {
                    _qrShowError('Một số mã QR bị lỗi:\n' + stats.errors.join('\n'));
                } else {
                    _qrHideError();
                }
            } catch (e) { /* ignore */ }
        } else {
            stepEl.textContent = 'Hoàn thành!';
        }

        const blob = await res.blob();
        _qrTriggerDownload(blob, 'qrcodes.zip');
    } catch (err) {
        clearInterval(fauxTimer);
        _qrShowError('Lỗi kết nối: ' + err.message);
    } finally {
        _qrIsDownloading = false;
        setTimeout(() => { progressEl.style.display = 'none'; }, 3000);
    }
}


/* ── Logo ────────────────────────────────────────────────────────────────── */
function qrRemoveLogo() {
    _qrLogoFile = null;
    const logoInput = document.getElementById('qr-logo-input');
    const logoImg = document.getElementById('qr-logo-img');
    const logoPlaceholder = document.getElementById('qr-logo-placeholder');
    const removeBtn = document.getElementById('qr-logo-remove');

    if (logoInput) logoInput.value = '';
    if (logoImg) { logoImg.src = ''; logoImg.style.display = 'none'; }
    if (logoPlaceholder) logoPlaceholder.style.display = 'block';
    if (removeBtn) removeBtn.style.display = 'none';

    _qrShowLogoOptions(false);
    _qrSchedulePreview();
}


function _qrShowLogoOptions(show) {
    const opts = document.getElementById('qr-logo-options');
    if (opts) opts.style.display = show ? 'flex' : 'none';
}


function qrSetLogoFrame(frame) {
    _qrLogoFrame = frame;

    // Update button styles
    document.querySelectorAll('#qr-logo-frame-tabs .qr-frame-btn').forEach(btn => {
        if (btn.dataset.frame === frame) {
            btn.style.border = '1px solid var(--accent)';
            btn.style.background = 'rgba(109,40,217,0.15)';
            btn.style.color = 'var(--accent)';
            btn.classList.add('active');
        } else {
            btn.style.border = '1px solid var(--border)';
            btn.style.background = 'var(--surface2)';
            btn.style.color = 'var(--text)';
            btn.classList.remove('active');
        }
    });

    _qrSchedulePreview();
}


function qrToggleWifiPassword() {
    const pw = document.getElementById('qr-data-wifi-password');
    const btn = document.getElementById('qr-wifi-toggle-pw');
    if (!pw || !btn) return;
    if (pw.type === 'password') {
        pw.type = 'text';
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
        pw.type = 'password';
        btn.innerHTML = '<i class="bi bi-eye"></i>';
    }
}


/* ── Presets ──────────────────────────────────────────────────────────────── */
function qrApplyPreset(fg, bg) {
    const fgPicker = document.getElementById('qr-fg-color');
    const fgText = document.getElementById('qr-fg-color-text');
    const bgPicker = document.getElementById('qr-bg-color');
    const bgText = document.getElementById('qr-bg-color-text');

    if (fgPicker) fgPicker.value = fg;
    if (fgText) fgText.value = fg;
    if (bgPicker) bgPicker.value = bg;
    if (bgText) bgText.value = bg;

    _qrUpdateGradientBar();
    _qrSchedulePreview();
}


/* ── Gradient preview bar ────────────────────────────────────────────────── */
function _qrUpdateGradientBar() {
    const bar = document.getElementById('qr-gradient-preview-bar');
    if (!bar) return;
    const c1 = document.getElementById('qr-fg-color')?.value || '#000000';
    const c2 = document.getElementById('qr-fg-color2')?.value || '#ec4899';
    bar.style.background = `linear-gradient(to right, ${c1}, ${c2})`;
}


/* ── Helpers ─────────────────────────────────────────────────────────────── */
function _qrSyncColors(pickerId, textId) {
    const picker = document.getElementById(pickerId);
    const textInput = document.getElementById(textId);
    if (!picker || !textInput) return;

    picker.addEventListener('input', () => {
        textInput.value = picker.value;
        _qrSchedulePreview();
    });
    textInput.addEventListener('input', () => {
        const val = textInput.value.trim();
        if (/^#[0-9a-fA-F]{6}$/.test(val)) {
            picker.value = val;
            _qrSchedulePreview();
        }
    });
}

function _qrAttachInputListeners() {
    document.querySelectorAll('#qr-fields .qr-input').forEach(el => {
        el.addEventListener('input', () => _qrSchedulePreview());
        el.addEventListener('change', () => _qrSchedulePreview());
    });
}

function _qrShowError(msg) {
    const el = document.getElementById('qr-error');
    if (el) {
        el.textContent = msg;
        el.style.display = 'block';
    }
}

function _qrHideError() {
    const el = document.getElementById('qr-error');
    if (el) el.style.display = 'none';
}

function _qrTriggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}
