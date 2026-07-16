let EDITED_FILES = [];
let PENDING_FILES = []; // Array of { id, file, url }
let SLOT_MAPPING = [null, null, null, null, null, null]; // slot index → PENDING_FILES entry

    function handleBulkDrop(e) {
      e.preventDefault();
      handleBulkFiles(e.dataTransfer.files);
    }

    document.getElementById('ei-bulk-upload-area').onclick = () => document.getElementById('ei-bulk-input').click();

    /**
     * Xử lý khi kéo thả nhiều file vào vùng tải lên.
     * @param {File[]} files - Danh sách các file.
     */
    function handleBulkFiles(files) {
      const container = document.getElementById('ei-preview-container');
      Array.from(files).forEach(file => {
        if (!file.name.toLowerCase().endsWith('.bmp')) return;
        const id = 'f_' + Math.random().toString(36).substr(2, 9);
        const url = URL.createObjectURL(file);
        const fileObj = { id, file, url };
        PENDING_FILES.push(fileObj);

        const el = document.createElement('div');
        el.className = 'ei-pending-preview';
        el.id = id;
        el.draggable = true;
        el.ondragstart = (e) => e.dataTransfer.setData('text/plain', id);
        el.style = 'border: 1px solid var(--border); border-radius: 6px; padding: 5px; background: var(--surface); text-align: center; cursor: grab;';
        el.innerHTML = `
        <img src="${url}" style="width: 100%; aspect-ratio: 4/3; object-fit: contain; border-radius: 4px; margin-bottom: 5px;">
        <div style="font-size: 0.65rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${file.name}</div>
    `;
        container.appendChild(el);
      });
    }

    /**
     * Xử lý khi kéo thả một file vào ô chức năng (slot).
     * @param {DragEvent} e - Sự kiện drag.
     * @param {number} slotIdx - Chỉ số ô (0-5).
     */
    function handleDropToSlot(e, slotIdx) {
      e.preventDefault();
      const fileId = e.dataTransfer.getData('text/plain');
      const fileObj = PENDING_FILES.find(f => f.id === fileId);
      if (!fileObj) return;

      SLOT_MAPPING[slotIdx] = fileObj;

      const slot = document.querySelectorAll('.ei-slot')[slotIdx];
      const content = slot.querySelector('.ei-slot-content');
      content.innerHTML = `
    <div style="position: relative; width: 100%;">
        <img src="${fileObj.url}" style="width: 100%; aspect-ratio: 4/3; object-fit: contain; border-radius: 4px;">
        <div style="font-size: 0.6rem; margin-top: 2px; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${fileObj.file.name}</div>
        <button onclick="clearSlot(${slotIdx}); event.stopPropagation();" style="position: absolute; top: -5px; right: -5px; background: var(--danger); color: white; border: none; border-radius: 50%; width: 15px; height: 15px; font-size: 10px; cursor: pointer;">×</button>
    </div>
  `;
    }

    function clearSlot(idx) {
      SLOT_MAPPING[idx] = null;
      const slot = document.querySelectorAll('.ei-slot')[idx];
      slot.querySelector('.ei-slot-content').innerHTML = '';
    }


    /**
     * Gửi các ảnh đã chọn và thông số lên server để xử lý.
     */
    async function submitEditImages() {
      const errorEl = document.getElementById('ei-error');
      const gallery = document.getElementById('ei-gallery');
      const resultsContainer = document.getElementById('ei-results-container');
      const btnSubmit = document.getElementById('btn-edit-img-submit');
      const btnZip = document.getElementById('btn-edit-img-zip');
      const spinner = document.getElementById('ei-spinner');
      const btnText = document.getElementById('ei-btn-text');

      const selectedFiles = [];
      for (let i = 0; i < 6; i++) {
        if (SLOT_MAPPING[i]) {
          selectedFiles.push({ idx: i, file: SLOT_MAPPING[i].file });
        }
      }

      if (selectedFiles.length === 0) {
        errorEl.textContent = 'Vui lòng kéo thả ít nhất một ảnh vào các ô chức năng bên trên.';
        errorEl.style.display = 'block';
        return;
      }

      errorEl.style.display = 'none';
      gallery.innerHTML = '';
      resultsContainer.style.display = 'block';
      btnSubmit.disabled = true;
      btnZip.style.display = 'none';
      spinner.style.display = 'inline-block';
      btnText.textContent = 'Đang xử lý...';
      EDITED_FILES = [];

      // Thu thập thông số đo
      const parameters = {};
      const fields = ['V1', 'V2', 'V3', 'A1', 'A2', 'A3', 'P1', 'P2', 'P3', 'Q1', 'Q2', 'Q3',
                      'S1', 'S2', 'S3', 'PF1', 'PF2', 'PF3', 'Vdeg1', 'Vdeg2', 'Vdeg3',
                      'Adeg1', 'Adeg2', 'Adeg3', 'THDV1', 'THDV2', 'THDV3',
                      'THDA1', 'THDA2', 'THDA3', 'P', 'Q', 'S', 'PF', 'freq', 'An', 'V_unb', 'A_unb'];
      fields.forEach(f => {
        const el = document.getElementById('ei-' + f);
        if (el && el.value && el.value.trim() !== "") {
          parameters[f] = el.value.trim().replace(/,/g, '.');
        }
      });

      // Thu thập thời gian (nếu có điền bất kỳ trường nào)
      const tsDD   = (document.getElementById('ei-ts-dd')  ?.value || '').trim();
      const tsMo   = (document.getElementById('ei-ts-mo')  ?.value || '').trim();
      const tsYYYY = (document.getElementById('ei-ts-yyyy')?.value || '').trim();
      const tsHH   = (document.getElementById('ei-ts-hh')  ?.value || '').trim();
      const tsMi   = (document.getElementById('ei-ts-mi')  ?.value || '').trim();
      const tsSS   = (document.getElementById('ei-ts-ss')  ?.value || '').trim();
      const hasTimestamp = Boolean(tsDD || tsMo || tsYYYY || tsHH || tsMi || tsSS);
      let timestampsForFiles = [];
      try {
        timestampsForFiles = buildTimestampPlan({
          hasTimestamp,
          tsDD,
          tsMo,
          tsYYYY,
          tsHH,
          tsMi,
          tsSS,
          fileCount: selectedFiles.length
        });
      } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = 'block';
        btnSubmit.disabled = false;
        spinner.style.display = 'none';
        btnText.textContent = '📸 Tiếp tục xử lý';
        return;
      }

      for (let order = 0; order < selectedFiles.length; order++) {
        const item = selectedFiles[order];
        const file = item.file;
        const i = item.idx;
        const imageTimestamp = timestampsForFiles[order];
        const card = document.createElement('div');
        card.className = 'chart-card';
        card.style.padding = '10px';
        card.innerHTML = `
      <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${file.name}</div>
      <div class="skeleton" style="width:100%; aspect-ratio:4/3; border-radius:6px; background:var(--surface2); animation: pulse 1.5s infinite;"></div>
    `;
        gallery.appendChild(card);
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        try {
          // Bước 1: xử lý thông số đo
          const templateSelect = document.getElementById('ei-template-select');
          const meterModel = templateSelect ? templateSelect.value : 'kew6315';
          let blob = await processImageServerSide(file, i, parameters, meterModel);

          // Bước 2: áp dụng timestamp (nếu có điền)
          if (imageTimestamp) {
            blob = await applyTimestampServerSide(blob, imageTimestamp);
          }

          const url = URL.createObjectURL(blob);
          const tsLabel = imageTimestamp
            ? `<div style="font-size:0.63rem; color:var(--text-muted); margin-top:3px; text-align:center;">⏱ ${imageTimestamp}</div>`
            : '';

          card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
          <div style="font-size:0.75rem; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:70%;">${file.name}</div>
          <a href="${url}" download="${file.name}" style="font-size:0.7rem; color:var(--accent); text-decoration:none;">Lưu ⬇️</a>
        </div>
        <img src="${url}" style="width:100%; border-radius:4px; cursor:pointer;" onclick="window.open('${url}')" />
        ${tsLabel}
      `;
          EDITED_FILES.push({ blob, name: file.name });
        } catch (err) {
          card.innerHTML = `<div style="color:var(--danger); font-size:0.75rem; padding:20px;">Lỗi: ${err.message}</div>`;
        }
      }

      btnSubmit.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = '📸 Tiếp tục xử lý';
      btnZip.style.display = EDITED_FILES.length > 0 ? 'block' : 'none';
    }

    async function downloadEditedZip() {
      if (EDITED_FILES.length === 0) return;
      const btn = document.getElementById('btn-edit-img-zip');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.textContent = '⏳ Đang nén...';

      const zip = new JSZip();
      EDITED_FILES.forEach(item => {
        zip.file(item.name, item.blob);
      });

      try {
        const content = await zip.generateAsync({ type: 'blob' });
        const url = URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Meter_Images.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        const errorEl = document.getElementById('ei-error');
        errorEl.textContent = `Không thể tạo ZIP: ${err.message}`;
        errorEl.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }


// ════════════════════════════════════════════════════════════════════
//  API HELPERS
// ════════════════════════════════════════════════════════════════════

/**
 * Gửi yêu cầu xử lý ảnh (chèn thông số đo) lên server.
 * @param {File} file - File ảnh gốc.
 * @param {number} screenIdx - Chỉ số màn hình (loại thông số).
 * @param {object} params - Các thông số đo lường.
 * @param {string} meterModel - Model thiết bị đo.
 * @returns {Promise<Blob>} - Blob ảnh đã xử lý.
 */
async function processImageServerSide(file, screenIdx, params, meterModel) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('screenIdx', screenIdx);
    formData.append('parameters', JSON.stringify(params));
    formData.append('meterModel', meterModel);

    const response = await fetch('/api/image/process', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        let errMsg = `Lỗi HTTP ${response.status}`;
        try {
            const errData = await response.json();
            if (errData && errData.error) errMsg = errData.error;
        } catch (e) { /* ignore */ }
        throw new Error(errMsg);
    }

    return await response.blob();
}

/** Gửi blob (đã xử lý thông số) lên server để dán chữ số thời gian */
async function applyTimestampServerSide(blobOrFile, timestamp) {
    const formData = new FormData();
    const fname = blobOrFile instanceof File ? blobOrFile.name : 'edited.bmp';
    formData.append('file', blobOrFile, fname);
    formData.append('timestamp', timestamp);

    const response = await fetch('/api/image/apply-timestamp', {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        let errMsg = `Lỗi HTTP ${response.status} (timestamp)`;
        try {
            const errData = await response.json();
            if (errData && errData.error) errMsg = errData.error;
        } catch (_) {}
        throw new Error(errMsg);
    }
    return await response.blob();
}


// ════════════════════════════════════════════════════════════════════
//  TIMESTAMP UI HELPERS
// ════════════════════════════════════════════════════════════════════

/** Điền thời gian hiện tại vào các ô nhập */
function fillTimestampNow() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('ei-ts-dd').value   = pad(now.getDate());
    document.getElementById('ei-ts-mo').value   = pad(now.getMonth() + 1);
    document.getElementById('ei-ts-yyyy').value = now.getFullYear();
    document.getElementById('ei-ts-hh').value   = pad(now.getHours());
    document.getElementById('ei-ts-mi').value   = pad(now.getMinutes());
    document.getElementById('ei-ts-ss').value   = pad(now.getSeconds());
    // Cập nhật picker
    const pv = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
    document.getElementById('ei-ts-picker').value = pv;
}

/** Đồng bộ từ datetime-local picker vào các ô riêng */
function fillTimestampFromPicker(val) {
    if (!val) return;
    const [datePart, timePart] = val.split('T');
    const [yyyy, mo, dd] = datePart.split('-');
    const [hh, mi]       = timePart.split(':');
    document.getElementById('ei-ts-dd').value   = dd;
    document.getElementById('ei-ts-mo').value   = mo;
    document.getElementById('ei-ts-yyyy').value = yyyy;
    document.getElementById('ei-ts-hh').value   = hh;
    document.getElementById('ei-ts-mi').value   = mi || '00';
}

function buildTimestampPlan(opts) {
    const { hasTimestamp, tsDD, tsMo, tsYYYY, tsHH, tsMi, tsSS, fileCount } = opts;
    if (!hasTimestamp) {
        return Array(fileCount).fill(null);
    }

    const baseTimestamp = formatTimestampString(tsDD, tsMo, tsYYYY, tsHH, tsMi, tsSS);
    if (fileCount <= 1) {
        return [baseTimestamp];
    }

    const minStep = parseNonNegativeInt(
        document.getElementById('ei-ts-step-min')?.value || '',
        'm (giây)',
        false
    );
    const maxStep = parseNonNegativeInt(
        document.getElementById('ei-ts-step-max')?.value || '',
        'n (giây)',
        false
    );
    if (maxStep < minStep) {
        throw new Error('Khoảng ngẫu nhiên không hợp lệ: n phải lớn hơn hoặc bằng m.');
    }

    if (minStep === 0 && maxStep === 0) {
        return Array(fileCount).fill(baseTimestamp);
    }

    const baseDate = parseStrictTimestampDate(tsDD, tsMo, tsYYYY, tsHH, tsMi, tsSS);
    if (!baseDate) {
        throw new Error('Để cộng thời gian giữa các ảnh, vui lòng nhập đầy đủ ngày/tháng/năm giờ:phút:giây hợp lệ.');
    }

    const planned = [baseTimestamp];
    let current = new Date(baseDate.getTime());
    for (let i = 1; i < fileCount; i++) {
        const delta = randomIntInclusive(minStep, maxStep);
        current = new Date(current.getTime() + (delta * 1000));
        planned.push(formatTimestampFromDate(current));
    }

    return planned;
}

function parseNonNegativeInt(rawValue, label, allowEmpty) {
    const raw = String(rawValue || '').trim();
    if (raw === '') {
        if (allowEmpty) return 0;
        throw new Error(`Vui lòng nhập ${label}.`);
    }
    if (!/^\d+$/.test(raw)) {
        throw new Error(`${label} phải là số nguyên không âm.`);
    }
    return parseInt(raw, 10);
}

function parseStrictTimestampDate(dd, mo, yyyy, hh, mi, ss) {
    const parts = [dd, mo, yyyy, hh, mi, ss].map(v => String(v || '').trim());
    if (!parts.every(v => /^\d+$/.test(v))) {
        return null;
    }

    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10);
    const year = parseInt(parts[2], 10);
    const hour = parseInt(parts[3], 10);
    const minute = parseInt(parts[4], 10);
    const second = parseInt(parts[5], 10);

    if (year < 1000 || month < 1 || month > 12 || day < 1 || day > 31) return null;
    if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) return null;

    const d = new Date(year, month - 1, day, hour, minute, second, 0);
    if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) return null;
    return d;
}

function formatTimestampString(dd, mo, yyyy, hh, mi, ss) {
    return `${String(dd || '__').padStart(2, '0')}/${String(mo || '__').padStart(2, '0')}/${String(yyyy || '____').padStart(4, '0')} ${String(hh || '__').padStart(2, '0')}:${String(mi || '__').padStart(2, '0')}:${String(ss || '__').padStart(2, '0')}`;
}

function formatTimestampFromDate(d) {
    return formatTimestampString(
        d.getDate(),
        d.getMonth() + 1,
        d.getFullYear(),
        d.getHours(),
        d.getMinutes(),
        d.getSeconds()
    );
}

function randomIntInclusive(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Tự động tính toán và điền 38 thông số đo đạc từ 9 thông số cốt lõi mà không bị xung đột logic kỹ thuật.
 */
function generateAndFillParameters() {
    const errorEl = document.getElementById('gen-error');
    if (errorEl) {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
    }

    try {
        const fields = [
            'V1', 'V2', 'V3', 'A1', 'A2', 'A3', 'P1', 'P2', 'P3', 'Q1', 'Q2', 'Q3',
            'S1', 'S2', 'S3', 'PF1', 'PF2', 'PF3', 'Vdeg1', 'Vdeg2', 'Vdeg3',
            'Adeg1', 'Adeg2', 'Adeg3', 'THDV1', 'THDV2', 'THDV3',
            'THDA1', 'THDA2', 'THDA3', 'P', 'Q', 'S', 'PF', 'freq', 'An', 'V_unb', 'A_unb'
        ];

        let vals = {};
        fields.forEach(f => {
            // Kiểm tra khung trên trước (gen-*)
            const genEl = document.getElementById('gen-' + f);
            if (genEl && genEl.value.trim() !== '') {
                const num = parseFloat(genEl.value.replace(/,/g, '.'));
                vals[f] = isNaN(num) ? null : num;
            } else {
                // Nếu khung trên trống, dùng khung dưới làm fallback (ei-*)
                const eiEl = document.getElementById('ei-' + f);
                if (eiEl && eiEl.value.trim() !== '') {
                    const num = parseFloat(eiEl.value.replace(/,/g, '.'));
                    vals[f] = isNaN(num) ? null : num;
                } else {
                    vals[f] = null;
                }
            }
        });

        // Đếm số thông số đã được cung cấp
        const numKnowns = Object.values(vals).filter(v => v !== null).length;
        if (numKnowns === 0) {
            throw new Error("Vui lòng nhập ít nhất một thông số ở khung trên hoặc khung dưới để hệ thống thực hiện dự đoán.");
        }

        // Tự động phát hiện đơn vị công suất (kW/kVar/kVA vs W/Var/VA)
        let isKw = true;
        const powerVals = [vals.P, vals.P1, vals.P2, vals.P3, vals.Q, vals.Q1, vals.Q2, vals.Q3, vals.S, vals.S1, vals.S2, vals.S3].filter(v => v !== null && v > 0);
        if (powerVals.length > 0) {
            const maxP = Math.max(...powerVals);
            if (maxP > 5000) {
                isKw = false;
            }
        }
        const factor = isKw ? 1000 : 1;

        // Vòng lặp giải quyết các ràng buộc toán học / kỹ thuật điện
        for (let pass = 0; pass < 5; pass++) {
            // 1. Điện áp (V1, V2, V3, V_unb)
            let vList = [vals.V1, vals.V2, vals.V3].filter(v => v !== null);
            let U_avg = vList.length > 0 ? (vList.reduce((a, b) => a + b, 0) / vList.length) : null;

            if (U_avg === null && vals.P !== null && vals.PF !== null && vals.PF > 0) {
                let aList = [vals.A1, vals.A2, vals.A3].filter(v => v !== null);
                if (aList.length > 0) {
                    let A_avg_temp = aList.reduce((a, b) => a + b, 0) / aList.length;
                    if (A_avg_temp > 0) {
                        U_avg = (vals.P * factor) / (Math.sqrt(3) * A_avg_temp * vals.PF);
                    }
                }
            }
            if (U_avg === null || U_avg <= 0) {
                U_avg = 380.0;
            }

            let vUnbVal = vals.V_unb !== null ? vals.V_unb : 1.2;
            if (vals.V1 === null) vals.V1 = U_avg + U_avg * (vUnbVal / 200);
            if (vals.V2 === null) vals.V2 = U_avg - U_avg * (vUnbVal / 200);
            if (vals.V3 === null) vals.V3 = U_avg;
            
            if (vals.V_unb === null) {
                let vAvg = (vals.V1 + vals.V2 + vals.V3) / 3;
                vals.V_unb = vAvg > 0 ? (Math.max(Math.abs(vals.V1 - vAvg), Math.abs(vals.V2 - vAvg), Math.abs(vals.V3 - vAvg)) / vAvg) * 100 : 0;
            }

            // 2. Dòng điện (A1, A2, A3, A_unb)
            let aList = [vals.A1, vals.A2, vals.A3].filter(v => v !== null);
            let A_avg = aList.length > 0 ? (aList.reduce((a, b) => a + b, 0) / aList.length) : null;

            if (A_avg === null && vals.P !== null && vals.PF !== null && vals.PF > 0) {
                let uAvg = (vals.V1 + vals.V2 + vals.V3) / 3;
                A_avg = (vals.P * factor) / (Math.sqrt(3) * uAvg * vals.PF);
            }
            if (A_avg === null || A_avg <= 0) {
                A_avg = 100.0;
            }

            let aUnbVal = vals.A_unb !== null ? vals.A_unb : 5.0;
            if (vals.A1 === null) vals.A1 = A_avg + A_avg * (aUnbVal / 200);
            if (vals.A2 === null) vals.A2 = A_avg - A_avg * (aUnbVal / 200);
            if (vals.A3 === null) vals.A3 = A_avg;

            if (vals.A_unb === null) {
                let aAvg = (vals.A1 + vals.A2 + vals.A3) / 3;
                vals.A_unb = aAvg > 0 ? (Math.max(Math.abs(vals.A1 - aAvg), Math.abs(vals.A2 - aAvg), Math.abs(vals.A3 - aAvg)) / aAvg) * 100 : 0;
            }

            // 3. Hệ số công suất (PF1, PF2, PF3, PF)
            let pfList = [vals.PF1, vals.PF2, vals.PF3].filter(v => v !== null);
            let PF_avg = pfList.length > 0 ? (pfList.reduce((a, b) => a + b, 0) / pfList.length) : (vals.PF !== null ? vals.PF : 0.85);
            if (PF_avg <= 0 || PF_avg > 1) PF_avg = 0.85;

            if (vals.PF1 === null) vals.PF1 = PF_avg;
            if (vals.PF2 === null) vals.PF2 = PF_avg;
            if (vals.PF3 === null) vals.PF3 = PF_avg;
            if (vals.PF === null) vals.PF = PF_avg;

            // 4. Công suất biểu kiến từng pha (S1, S2, S3)
            if (vals.S1 === null) vals.S1 = (vals.V1 * vals.A1) / (Math.sqrt(3) * factor);
            if (vals.S2 === null) vals.S2 = (vals.V2 * vals.A2) / (Math.sqrt(3) * factor);
            if (vals.S3 === null) vals.S3 = (vals.V3 * vals.A3) / (Math.sqrt(3) * factor);

            // 5. Công suất tác dụng từng pha (P1, P2, P3) và Tổng P
            if (vals.P1 === null) vals.P1 = vals.S1 * vals.PF1;
            if (vals.P2 === null) vals.P2 = vals.S2 * vals.PF2;
            if (vals.P3 === null) vals.P3 = vals.S3 * vals.PF3;

            let P_sum = vals.P1 + vals.P2 + vals.P3;
            if (vals.P === null) {
                vals.P = P_sum;
            } else {
                if (P_sum > 0) {
                    let kP = vals.P / P_sum;
                    vals.P1 *= kP;
                    vals.P2 *= kP;
                    vals.P3 *= kP;
                }
            }

            // 6. Công suất phản kháng (Q1, Q2, Q3) và Tổng Q
            if (vals.Q1 === null) vals.Q1 = Math.sqrt(Math.max(0, vals.S1 * vals.S1 - vals.P1 * vals.P1));
            if (vals.Q2 === null) vals.Q2 = Math.sqrt(Math.max(0, vals.S2 * vals.S2 - vals.P2 * vals.P2));
            if (vals.Q3 === null) vals.Q3 = Math.sqrt(Math.max(0, vals.S3 * vals.S3 - vals.P3 * vals.P3));

            let Q_sum = vals.Q1 + vals.Q2 + vals.Q3;
            if (vals.Q === null) {
                vals.Q = Q_sum;
            } else {
                if (Q_sum > 0) {
                    let kQ = vals.Q / Q_sum;
                    vals.Q1 *= kQ;
                    vals.Q2 *= kQ;
                    vals.Q3 *= kQ;
                }
            }

            // 7. Tính lại S và PF để đảm bảo logic
            vals.S = Math.sqrt(vals.P * vals.P + vals.Q * vals.Q);
            if (vals.S > 0) {
                vals.PF = vals.P / vals.S;
            }
            if (vals.S1 > 0) vals.PF1 = vals.P1 / vals.S1; else vals.PF1 = PF_avg;
            if (vals.S2 > 0) vals.PF2 = vals.P2 / vals.S2; else vals.PF2 = PF_avg;
            if (vals.S3 > 0) vals.PF3 = vals.P3 / vals.S3; else vals.PF3 = PF_avg;

            // 8. Góc lệch pha
            if (vals.Vdeg1 === null) vals.Vdeg1 = 0.0;
            if (vals.Vdeg2 === null) vals.Vdeg2 = -120.0;
            if (vals.Vdeg3 === null) vals.Vdeg3 = 120.0;

            const thetaRad1 = Math.acos(Math.min(1.0, Math.max(-1.0, vals.PF1)));
            const thetaRad2 = Math.acos(Math.min(1.0, Math.max(-1.0, vals.PF2)));
            const thetaRad3 = Math.acos(Math.min(1.0, Math.max(-1.0, vals.PF3)));

            function normalizeAngle(angle) {
                while (angle > 180) angle -= 360;
                while (angle <= -180) angle += 360;
                return angle;
            }

            if (vals.Adeg1 === null) vals.Adeg1 = normalizeAngle(vals.Vdeg1 - thetaRad1 * (180 / Math.PI));
            if (vals.Adeg2 === null) vals.Adeg2 = normalizeAngle(vals.Vdeg2 - thetaRad2 * (180 / Math.PI));
            if (vals.Adeg3 === null) vals.Adeg3 = normalizeAngle(vals.Vdeg3 - thetaRad3 * (180 / Math.PI));

            // 9. THDV và THDA
            let thdvList = [vals.THDV1, vals.THDV2, vals.THDV3].filter(v => v !== null);
            let THDV_avg = thdvList.length > 0 ? (thdvList.reduce((a, b) => a + b, 0) / thdvList.length) : 1.5;
            if (vals.THDV1 === null) vals.THDV1 = THDV_avg;
            if (vals.THDV2 === null) vals.THDV2 = Math.max(0, THDV_avg - (0.1 + Math.random() * 0.3));
            if (vals.THDV3 === null) vals.THDV3 = Math.max(0, THDV_avg - (0.1 + Math.random() * 0.3));

            let thdaList = [vals.THDA1, vals.THDA2, vals.THDA3].filter(v => v !== null);
            let THDA_avg = thdaList.length > 0 ? (thdaList.reduce((a, b) => a + b, 0) / thdaList.length) : 4.5;
            if (vals.THDA1 === null) vals.THDA1 = THDA_avg;
            if (vals.THDA2 === null) vals.THDA2 = Math.max(0, THDA_avg - (0.2 + Math.random() * 0.8));
            if (vals.THDA3 === null) vals.THDA3 = Math.max(0, THDA_avg - (0.2 + Math.random() * 0.8));

            // 10. Dòng trung tính An
            if (vals.An === null) {
                const r1 = vals.A1 * Math.cos(vals.Adeg1 * Math.PI / 180);
                const i1 = vals.A1 * Math.sin(vals.Adeg1 * Math.PI / 180);
                const r2 = vals.A2 * Math.cos(vals.Adeg2 * Math.PI / 180);
                const i2 = vals.A2 * Math.sin(vals.Adeg2 * Math.PI / 180);
                const r3 = vals.A3 * Math.cos(vals.Adeg3 * Math.PI / 180);
                const i3 = vals.A3 * Math.sin(vals.Adeg3 * Math.PI / 180);
                const r_n = r1 + r2 + r3;
                const i_n = i1 + i2 + i3;
                vals.An = Math.sqrt(r_n * r_n + i_n * i_n);
            }

            // 11. Tần số freq
            if (vals.freq === null) {
                vals.freq = 50.0 + (Math.random() > 0.5 ? 0.01 : -0.01);
            }
        }

        // Định dạng làm tròn các giá trị theo quy tắc của người dùng
        const formattingMap = {
            V1: 1, V2: 1, V3: 1,
            A1: 0, A2: 0, A3: 0, An: 0,
            P1: 0, P2: 0, P3: 0, P: 0,
            Q1: 0, Q2: 0, Q3: 0, Q: 0,
            S1: 0, S2: 0, S3: 0, S: 0,
            PF1: 3, PF2: 3, PF3: 3, PF: 3,
            Vdeg1: 1, Vdeg2: 1, Vdeg3: 1,
            Adeg1: 1, Adeg2: 1, Adeg3: 1,
            THDV1: 2, THDV2: 2, THDV3: 2,
            THDA1: 2, THDA2: 2, THDA3: 2,
            freq: 2, V_unb: 2, A_unb: 2
        };

        // Điền lại vào các trường của form
        fields.forEach(f => {
            const el = document.getElementById('ei-' + f);
            if (el) {
                const dec = formattingMap[f] !== undefined ? formattingMap[f] : 2;
                const val = (vals[f] !== null && !isNaN(vals[f])) ? vals[f] : 0;
                el.value = val.toFixed(dec);
            }
        });

        // Hiệu ứng nhấp nháy xanh nhẹ để người dùng nhận thấy dữ liệu đã đổi
        fields.forEach(f => {
            const el = document.getElementById('ei-' + f);
            if (el) {
                const oldTransition = el.style.transition;
                const oldBg = el.style.background;
                el.style.transition = 'background 0.3s ease';
                el.style.background = 'rgba(46, 204, 113, 0.2)'; // Xanh lục nhạt
                setTimeout(() => {
                    el.style.background = oldBg;
                    setTimeout(() => {
                        el.style.transition = oldTransition;
                    }, 300);
                }, 800);
            }
        });

    } catch (err) {
        if (errorEl) {
            errorEl.textContent = err.message;
            errorEl.style.display = 'block';
        }
    }
}
