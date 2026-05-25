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
    return `${String(dd || '00').padStart(2, '0')}/${String(mo || '00').padStart(2, '0')}/${String(yyyy || '0000').padStart(4, '0')} ${String(hh || '00').padStart(2, '0')}:${String(mi || '00').padStart(2, '0')}:${String(ss || '00').padStart(2, '0')}`;
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
        const pVal = parseFloat(document.getElementById('gen-P').value.replace(/,/g, '.'));
        const pfVal = parseFloat(document.getElementById('gen-PF').value.replace(/,/g, '.'));
        const a1 = parseFloat(document.getElementById('gen-A1').value.replace(/,/g, '.'));
        const a2 = parseFloat(document.getElementById('gen-A2').value.replace(/,/g, '.'));
        const a3 = parseFloat(document.getElementById('gen-A3').value.replace(/,/g, '.'));
        const aUnb = parseFloat(document.getElementById('gen-Aunb').value.replace(/,/g, '.'));
        const uUnb = parseFloat(document.getElementById('gen-Uunb').value.replace(/,/g, '.'));
        const thdMax = parseFloat(document.getElementById('gen-THDmax').value.replace(/,/g, '.'));
        const tddMax = parseFloat(document.getElementById('gen-TDDmax').value.replace(/,/g, '.'));

        if (isNaN(pVal) || isNaN(pfVal) || isNaN(a1) || isNaN(a2) || isNaN(a3) || isNaN(aUnb) || isNaN(uUnb) || isNaN(thdMax) || isNaN(tddMax)) {
            throw new Error("Vui lòng nhập đầy đủ và đúng định dạng số cho cả 9 thông số cốt lõi.");
        }

        if (pfVal <= 0 || pfVal > 1) {
            throw new Error("Hệ số công suất (PF) phải nằm trong khoảng (0, 1].");
        }

        // 1. Dòng điện trung bình
        const A_avg = (a1 + a2 + a3) / 3;

        // 2. Điện áp dây trung bình (Tự động phát hiện kW hay W)
        // P = sqrt(3) * U_dây * I * PF => U_dây_avg = P / (sqrt(3) * I * PF)
        let isKw = false;
        let U_avg = (Math.sqrt(3) * pVal) / (pfVal * (a1 + a2 + a3));
        if (U_avg < 10.0) {
            isKw = true;
            U_avg *= 1000;
        }

        // 3. Phân phối điện áp pha lệch theo U_unb
        const deltaU = U_avg * (uUnb / 100);
        const u1 = U_avg + deltaU;
        const u2 = U_avg - deltaU;
        const u3 = U_avg;

        // 4. Góc pha điện áp (Định mức lệch 120 độ)
        const vdeg1 = 0.0;
        const vdeg2 = -120.0;
        const vdeg3 = 120.0;

        // 5. Góc pha dòng điện (Chậm pha do tải cảm kháng)
        const thetaRad = Math.acos(pfVal);
        const thetaDeg = thetaRad * (180 / Math.PI);
        
        function normalizeAngle(angle) {
            while (angle > 180) angle -= 360;
            while (angle <= -180) angle += 360;
            return angle;
        }
        
        const adeg1 = normalizeAngle(vdeg1 - thetaDeg);
        const adeg2 = normalizeAngle(vdeg2 - thetaDeg);
        const adeg3 = normalizeAngle(vdeg3 - thetaDeg);

        // 6. Tính toán công suất biểu kiến S từng pha (Vì u1, u2, u3 là điện áp dây, S_pha = U_dây * I / sqrt(3))
        const factor = isKw ? 1000 : 1;
        const s1 = (u1 * a1) / (Math.sqrt(3) * factor);
        const s2 = (u2 * a2) / (Math.sqrt(3) * factor);
        const s3 = (u3 * a3) / (Math.sqrt(3) * factor);

        // 7. Tính công suất tác dụng và phản kháng (Hiệu chỉnh khớp số liệu tổng)
        const p1_tmp = s1 * pfVal;
        const p2_tmp = s2 * pfVal;
        const p3_tmp = s3 * pfVal;
        const p_sum_tmp = p1_tmp + p2_tmp + p3_tmp;
        const k_p = pVal / p_sum_tmp;

        const p1 = p1_tmp * k_p;
        const p2 = p2_tmp * k_p;
        const p3 = p3_tmp * k_p;

        const q1_tmp = Math.sqrt(Math.max(0, s1*s1 - p1*p1));
        const q2_tmp = Math.sqrt(Math.max(0, s2*s2 - p2*p2));
        const q3_tmp = Math.sqrt(Math.max(0, s3*s3 - p3*p3));
        
        const q_total = pVal * Math.tan(thetaRad);
        const q_sum_tmp = q1_tmp + q2_tmp + q3_tmp;
        const m_q = q_sum_tmp > 0 ? (q_total / q_sum_tmp) : 0;

        const q1 = q1_tmp * m_q;
        const q2 = q2_tmp * m_q;
        const q3 = q3_tmp * m_q;

        const S_total = Math.sqrt(pVal*pVal + q_total*q_total);
        const PF_total = pfVal;

        const pf1 = s1 > 0 ? (p1 / s1) : pfVal;
        const pf2 = s2 > 0 ? (p2 / s2) : pfVal;
        const pf3 = s3 > 0 ? (p3 / s3) : pfVal;

        // 8. Dòng điện trung tính An
        const r1 = a1 * Math.cos(adeg1 * Math.PI / 180);
        const i1 = a1 * Math.sin(adeg1 * Math.PI / 180);
        const r2 = a2 * Math.cos(adeg2 * Math.PI / 180);
        const i2 = a2 * Math.sin(adeg2 * Math.PI / 180);
        const r3 = a3 * Math.cos(adeg3 * Math.PI / 180);
        const i3 = a3 * Math.sin(adeg3 * Math.PI / 180);
        const r_n = r1 + r2 + r3;
        const i_n = i1 + i2 + i3;
        const an = Math.sqrt(r_n*r_n + i_n*i_n);

        // 9. THDV (Sóng hài áp)
        const thdv1 = thdMax;
        const thdv2 = Math.max(0, thdMax - (0.1 + Math.random() * 0.3));
        const thdv3 = Math.max(0, thdMax - (0.1 + Math.random() * 0.3));

        // 10. THDA (Sóng hài dòng - TDD)
        const currents = [
            { id: 1, val: a1 },
            { id: 2, val: a2 },
            { id: 3, val: a3 }
        ];
        currents.sort((x, y) => y.val - x.val);
        const maxIdx = currents[0].id;

        const thda = [];
        thda[maxIdx] = tddMax;
        for (let i = 1; i <= 3; i++) {
            if (i !== maxIdx) {
                thda[i] = Math.max(0, tddMax - (0.2 + Math.random() * 0.8));
            }
        }

        // Điền dữ liệu vào form
        document.getElementById('ei-V1').value = u1.toFixed(1);
        document.getElementById('ei-V2').value = u2.toFixed(1);
        document.getElementById('ei-V3').value = u3.toFixed(1);

        document.getElementById('ei-A1').value = a1.toFixed(2);
        document.getElementById('ei-A2').value = a2.toFixed(2);
        document.getElementById('ei-A3').value = a3.toFixed(2);

        document.getElementById('ei-P1').value = p1.toFixed(3);
        document.getElementById('ei-P2').value = p2.toFixed(3);
        document.getElementById('ei-P3').value = p3.toFixed(3);

        document.getElementById('ei-Q1').value = q1.toFixed(3);
        document.getElementById('ei-Q2').value = q2.toFixed(3);
        document.getElementById('ei-Q3').value = q3.toFixed(3);

        document.getElementById('ei-S1').value = s1.toFixed(3);
        document.getElementById('ei-S2').value = s2.toFixed(3);
        document.getElementById('ei-S3').value = s3.toFixed(3);

        document.getElementById('ei-PF1').value = pf1.toFixed(3);
        document.getElementById('ei-PF2').value = pf2.toFixed(3);
        document.getElementById('ei-PF3').value = pf3.toFixed(3);

        document.getElementById('ei-Vdeg1').value = vdeg1.toFixed(1);
        document.getElementById('ei-Vdeg2').value = vdeg2.toFixed(1);
        document.getElementById('ei-Vdeg3').value = vdeg3.toFixed(1);

        document.getElementById('ei-Adeg1').value = adeg1.toFixed(1);
        document.getElementById('ei-Adeg2').value = adeg2.toFixed(1);
        document.getElementById('ei-Adeg3').value = adeg3.toFixed(1);

        document.getElementById('ei-THDV1').value = thdv1.toFixed(2);
        document.getElementById('ei-THDV2').value = thdv2.toFixed(2);
        document.getElementById('ei-THDV3').value = thdv3.toFixed(2);

        document.getElementById('ei-THDA1').value = thda[1].toFixed(2);
        document.getElementById('ei-THDA2').value = thda[2].toFixed(2);
        document.getElementById('ei-THDA3').value = thda[3].toFixed(2);

        document.getElementById('ei-P').value = pVal.toFixed(3);
        document.getElementById('ei-Q').value = q_total.toFixed(3);
        document.getElementById('ei-S').value = S_total.toFixed(3);
        document.getElementById('ei-PF').value = PF_total.toFixed(3);

        document.getElementById('ei-freq').value = (50.0 + (Math.random() > 0.5 ? 0.02 : -0.02)).toFixed(2);
        document.getElementById('ei-An').value = an.toFixed(2);
        document.getElementById('ei-V_unb').value = uUnb.toFixed(2);
        document.getElementById('ei-A_unb').value = aUnb.toFixed(2);

        // Hiệu ứng nhấp nháy xanh nhẹ để người dùng nhận thấy dữ liệu đã đổi
        const fieldsToHighlight = ['V1', 'V2', 'V3', 'A1', 'A2', 'A3', 'P1', 'P2', 'P3', 'Q1', 'Q2', 'Q3',
                                   'S1', 'S2', 'S3', 'PF1', 'PF2', 'PF3', 'Vdeg1', 'Vdeg2', 'Vdeg3',
                                   'Adeg1', 'Adeg2', 'Adeg3', 'THDV1', 'THDV2', 'THDV3', 'THDA1', 'THDA2', 'THDA3',
                                   'P', 'Q', 'S', 'PF', 'freq', 'An', 'V_unb', 'A_unb'];
        fieldsToHighlight.forEach(f => {
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
