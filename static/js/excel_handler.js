// ═══════════════════════════════════════════════════════
// Excel Handler – Data-first approach
// Lưu dữ liệu điện 3 giá dạng flat table vào file xlsx đơn giản.
// ═══════════════════════════════════════════════════════

let currentMode = 'string_mode';
let dataRows = [];           // [{nam, thang, ky, thue_vat, bt_don_gia, bt_san_luong, cd_don_gia, cd_san_luong, td_don_gia, td_san_luong, ghi_chu}]
let selectedRowIndices = new Set();
let currentDataFilename = "";

const DATA_SHEET_NAME = "DuLieu";
const DATA_HEADERS = ["nam", "thang", "ky", "thue_vat", "bt_don_gia", "bt_san_luong", "cd_don_gia", "cd_san_luong", "td_don_gia", "td_san_luong", "ghi_chu"];

// ───────────────────────────────────────────────────────
// Utility
// ───────────────────────────────────────────────────────

/**
 * Chuyển chuỗi số Việt Nam (dấu chấm phân cách hàng nghìn) sang number.
 */
function toNumber(val) {
    if (val === null || val === undefined) return 0;
    if (typeof val === 'number') return val;
    let s = String(val).trim();
    if (!s) return 0;
    s = s.replace(/\./g, '').replace(/,/g, '.');
    let n = parseFloat(s);
    return isNaN(n) ? 0 : n;
}

/**
 * Format số hiển thị trên bảng.
 */
function fmtNum(v) {
    if (v === null || v === undefined || v === 0) return '';
    return Number(v).toLocaleString('vi-VN');
}

function showMessage(msg, isError = false) {
    const msgDiv = document.getElementById('message');
    if (!msgDiv) return;
    msgDiv.textContent = msg;
    msgDiv.className = isError ? 'error' : 'success';
}

function showExportMessage(msg, isError = false) {
    const msgDiv = document.getElementById('export_message');
    if (!msgDiv) return;
    msgDiv.textContent = msg;
    msgDiv.style.color = isError ? 'var(--state-error-text)' : 'var(--state-success-text)';
    msgDiv.style.fontWeight = '600';
    msgDiv.style.fontSize = '0.85rem';
}

// ───────────────────────────────────────────────────────
// Tab switching
// ───────────────────────────────────────────────────────

function switchExcelTab(modeId) {
    const root = document.getElementById('workspace-excel');
    if (!root) return;
    root.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    root.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(modeId).classList.add('active');
    if (modeId === 'string_mode') {
        document.getElementById('tab_string').classList.add('active');
    } else {
        document.getElementById('tab_manual').classList.add('active');
    }
    currentMode = modeId;
}

// ───────────────────────────────────────────────────────
// Quản lý file
// ───────────────────────────────────────────────────────

/**
 * Tạo file dữ liệu mới.
 */
window.excelCreateNewFile = function () {
    dataRows = [];
    selectedRowIndices.clear();
    currentDataFilename = `DuLieu_Dien_${new Date().getFullYear()}.xlsx`;
    activateWorkspace();
    renderDataTable();
    showMessage("Đã tạo file dữ liệu mới.");
    // Set default year to current year
    document.getElementById('input_year').value = new Date().getFullYear();
    document.getElementById('input_tax').value = 0;
}

/**
 * Nạp file dữ liệu có sẵn (.xlsx) để nhập tiếp.
 */
window.excelLoadExistingFile = function (inputEl) {
    const file = inputEl.files && inputEl.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.xlsx')) {
        alert('Chỉ hỗ trợ file .xlsx');
        inputEl.value = '';
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });

            if (!workbook.SheetNames.includes(DATA_SHEET_NAME)) {
                alert(`File không chứa sheet "${DATA_SHEET_NAME}". Đây có thể không phải file dữ liệu đúng định dạng.`);
                inputEl.value = '';
                return;
            }

            const ws = workbook.Sheets[DATA_SHEET_NAME];
            const jsonData = XLSX.utils.sheet_to_json(ws, { header: 1 });

            // Validate header row
            if (jsonData.length === 0) {
                alert('File rỗng.');
                inputEl.value = '';
                return;
            }

            const headers = jsonData[0].map(h => String(h).trim().toLowerCase());
            const hasTaxCol = headers.includes("thue_vat") || headers.includes("thue") || headers.includes("vat");

            // Parse data rows
            dataRows = [];
            selectedRowIndices.clear();
            for (let i = 1; i < jsonData.length; i++) {
                const row = jsonData[i];
                if (!row || row.length === 0) continue;
                // Skip empty rows
                if (row.every(cell => cell === null || cell === undefined || String(cell).trim() === '')) continue;

                if (hasTaxCol || headers[3] === "thue_vat") {
                    dataRows.push({
                        nam: toNumber(row[0]),
                        thang: toNumber(row[1]),
                        ky: toNumber(row[2]),
                        thue_vat: toNumber(row[3]),
                        bt_don_gia: toNumber(row[4]),
                        bt_san_luong: toNumber(row[5]),
                        cd_don_gia: toNumber(row[6]),
                        cd_san_luong: toNumber(row[7]),
                        td_don_gia: toNumber(row[8]),
                        td_san_luong: toNumber(row[9]),
                        ghi_chu: row[10] != null ? String(row[10]) : ""
                    });
                } else {
                    // Legacy 10-column format without thue_vat
                    dataRows.push({
                        nam: toNumber(row[0]),
                        thang: toNumber(row[1]),
                        ky: toNumber(row[2]),
                        thue_vat: 0,
                        bt_don_gia: toNumber(row[3]),
                        bt_san_luong: toNumber(row[4]),
                        cd_don_gia: toNumber(row[5]),
                        cd_san_luong: toNumber(row[6]),
                        td_don_gia: toNumber(row[7]),
                        td_san_luong: toNumber(row[8]),
                        ghi_chu: row[9] != null ? String(row[9]) : ""
                    });
                }
            }

            currentDataFilename = file.name;
            activateWorkspace();
            renderDataTable();
            showMessage(`Đã nạp ${dataRows.length} dòng dữ liệu từ file "${file.name}".`);

            // Auto-detect year & tax from data
            if (dataRows.length > 0) {
                const latestYear = Math.max(...dataRows.map(r => r.nam));
                document.getElementById('input_year').value = latestYear;
                
                const latestTax = dataRows[dataRows.length - 1].thue_vat;
                if (latestTax !== undefined && latestTax !== null) {
                    document.getElementById('input_tax').value = latestTax;
                }

                // Auto-detect next month/period to input
                const latestRows = dataRows.filter(r => r.nam === latestYear);
                if (latestRows.length > 0) {
                    const maxMonth = Math.max(...latestRows.map(r => r.thang));
                    const monthRows = latestRows.filter(r => r.thang === maxMonth);
                    const maxPeriod = Math.max(...monthRows.map(r => r.ky));
                    // Advance to next period/month
                    let nextMonth = maxMonth, nextPeriod = maxPeriod;
                    if (nextPeriod < 3) {
                        nextPeriod++;
                    } else {
                        nextPeriod = 1;
                        nextMonth = maxMonth < 12 ? maxMonth + 1 : 1;
                    }
                    document.getElementById('input_month').value = nextMonth;
                    document.getElementById('input_period').value = nextPeriod;
                }
            }

        } catch (err) {
            alert('Lỗi đọc file: ' + err.message);
        }
        inputEl.value = '';
    };
    reader.readAsArrayBuffer(file);
}

/**
 * Tự động đọc và bóc tách dữ liệu từ file ZIP hoặc nhiều file PDF hóa đơn EVN (vector / digital PDF).
 */
window.excelParseInvoices = async function (inputEl) {
    const files = inputEl.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append("files", files[i]);
    }

    showMessage("⏳ Đang giải nén và phân tích hóa đơn điện...", false);

    try {
        const response = await fetch('/api/excel/parse-invoices', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Lỗi khi bóc tách hóa đơn.');
        }

        if (!result.data || result.data.length === 0) {
            showMessage("⚠️ Không bóc tách được số liệu nào từ các file đã tải lên.", true);
            inputEl.value = '';
            return;
        }

        if (!currentDataFilename) {
            const firstYear = result.data[0].nam || new Date().getFullYear();
            currentDataFilename = `DuLieu_Dien_${firstYear}.xlsx`;
        }

        activateWorkspace();

        result.data.forEach(entry => {
            dataRows.push(entry);
        });

        dataRows.sort((a, b) => {
            if (a.nam !== b.nam) return a.nam - b.nam;
            if (a.thang !== b.thang) return a.thang - b.thang;
            return a.ky - b.ky;
        });

        if (dataRows.length > 0) {
            const maxYear = Math.max(...dataRows.map(r => r.nam));
            document.getElementById('input_year').value = maxYear;
        }

        renderDataTable();
        updateExportSection();

        let msg = `✓ Đã tự động bóc tách thành công ${result.parsed_count}/${result.total_pdfs} hóa đơn!`;
        if (result.failed_count > 0) {
            msg += ` (Bỏ qua ${result.failed_count} file scan/ảnh hoặc không đúng định dạng)`;
        }
        showMessage(msg);

    } catch (err) {
        showMessage("Lỗi: " + err.message, true);
    } finally {
        inputEl.value = '';
    }
};

/**
 * Nạp file text (.txt) hoặc kết quả OCR từ máy cá nhân
 */
window.excelLoadTxtFile = function (inputEl) {
    const file = inputEl.files && inputEl.files[0];
    if (!file) return;


    const reader = new FileReader();
    reader.onload = function (e) {
        const content = e.target.result;
        excelParseFromText(content, file.name);
        inputEl.value = '';
    };
    reader.readAsText(file, 'utf-8');
};


/**
 * Phân tích chuỗi văn bản (plaintext từ OCR hoặc file .txt) và điền vào bảng dữ liệu.
 */
window.excelParseFromText = async function (textContent, sourceLabel = "Text OCR") {
    if (!textContent || !textContent.trim()) {
        showMessage("Văn bản rỗng, không có dữ liệu để phân tích.", true);
        return;
    }

    showMessage("⏳ Đang phân tích dữ liệu điện từ văn bản...", false);

    try {
        const response = await fetch('/api/excel/parse-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textContent })
        });

        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || "Không thể phân tích dữ liệu từ văn bản.");
        }

        if (!result.data || result.data.length === 0) {
            showMessage("⚠️ Không tìm thấy cấu trúc số điện hợp lệ trong văn bản.", true);
            return;
        }

        if (!currentDataFilename) {
            const firstYear = result.data[0].nam || new Date().getFullYear();
            currentDataFilename = `DuLieu_Dien_${firstYear}.xlsx`;
        }

        activateWorkspace();

        result.data.forEach(entry => {
            if (sourceLabel && (!entry.ghi_chu || entry.ghi_chu === 'OCR txt')) {
                entry.ghi_chu = sourceLabel;
            }
            dataRows.push(entry);
        });

        dataRows.sort((a, b) => {
            if (a.nam !== b.nam) return a.nam - b.nam;
            if (a.thang !== b.thang) return a.thang - b.thang;
            return a.ky - b.ky;
        });

        if (dataRows.length > 0) {
            const maxYear = Math.max(...dataRows.map(r => r.nam));
            document.getElementById('input_year').value = maxYear;
        }

        renderDataTable();
        updateExportSection();
        showMessage(`✓ Đã nạp thành công ${result.count} dòng dữ liệu từ văn bản (${sourceLabel})!`);

    } catch (err) {
        showMessage("Lỗi: " + err.message, true);
    }
};

function activateWorkspace() {
    document.getElementById('data_entry_section').style.opacity = '1';
    document.getElementById('data_entry_section').style.pointerEvents = 'auto';
    document.getElementById('active_file_display').style.display = 'flex';
    document.getElementById('active_filename_label').textContent = currentDataFilename;
    updateExportSection();
}

function updateExportSection() {
    const section = document.getElementById('export_section');
    if (dataRows.length > 0) {
        section.style.opacity = '1';
        section.style.pointerEvents = 'auto';
    } else {
        section.style.opacity = '0.5';
        section.style.pointerEvents = 'none';
    }
    // Update data count badge
    const badge = document.getElementById('data_count_badge');
    if (badge) {
        const uniqueMonths = new Set(dataRows.map(r => `${r.nam}-${r.thang}`));
        badge.textContent = `${dataRows.length} dòng · ${uniqueMonths.size} tháng`;
    }
}

// ───────────────────────────────────────────────────────
// Nhập dữ liệu
// ───────────────────────────────────────────────────────

window.excelSubmitData = function () {
    if (!currentDataFilename) {
        showMessage("Vui lòng tạo file mới hoặc nạp file có sẵn trước.", true);
        return;
    }

    const year = parseInt(document.getElementById('input_year').value);
    const month = parseInt(document.getElementById('input_month').value);
    const period = parseInt(document.getElementById('input_period').value);
    const taxRate = toNumber(document.getElementById('input_tax').value) || 0;

    if (!year || year < 2000 || year > 2100) {
        showMessage("Năm không hợp lệ.", true);
        return;
    }
    if (!month || month < 1 || month > 12) {
        showMessage("Tháng không hợp lệ (1-12).", true);
        return;
    }
    if (!period || period < 1 || period > 3) {
        showMessage("Kỳ không hợp lệ (1-3).", true);
        return;
    }

    let parsedGroups = [];

    if (currentMode === 'string_mode') {
        const rawText = document.getElementById('raw_data').value;
        const lines = rawText.split(/\n/).filter(l => l.trim().length > 0);

        for (let i = 0; i < lines.length; i += 3) {
            if (i + 2 >= lines.length) break;
            const items = [lines[i], lines[i + 1], lines[i + 2]].map(l => {
                const nums = l.match(/\d+[\d.,]*/g) || [];
                let p = "0", q = "0";
                if (nums.length >= 3) {
                    p = nums[nums.length - 3];
                    q = nums[nums.length - 2];
                } else if (nums.length === 2) {
                    p = nums[0];
                    q = nums[1];
                } else if (nums.length === 1) {
                    q = nums[0]; // If only 1 number, treat as san_luong
                }
                return [toNumber(p), toNumber(q)];
            });
            parsedGroups.push(items);
        }
    } else {
        // Manual mode
        const btPrice = toNumber(document.getElementById('bt_price').value);
        const btUsage = toNumber(document.getElementById('bt_usage').value);
        const cdPrice = toNumber(document.getElementById('cd_price').value);
        const cdUsage = toNumber(document.getElementById('cd_usage').value);
        const tdPrice = toNumber(document.getElementById('td_price').value);
        const tdUsage = toNumber(document.getElementById('td_usage').value);
        parsedGroups = [[[btPrice, btUsage], [cdPrice, cdUsage], [tdPrice, tdUsage]]];
    }

    if (parsedGroups.length === 0) {
        showMessage("Dữ liệu không hợp lệ. Cần 3 dòng: BT, CĐ, TĐ.", true);
        return;
    }

    // Add to dataRows (Luôn thêm mới chứ không ghi đè)
    let addedCount = 0;
    parsedGroups.forEach(group => {
        // group = [[bt_price, bt_usage], [cd_price, cd_usage], [td_price, td_usage]]
        const entry = {
            nam: year,
            thang: month,
            ky: period,
            thue_vat: taxRate,
            bt_don_gia: group[0][0],
            bt_san_luong: group[0][1],
            cd_don_gia: group[1][0],
            cd_san_luong: group[1][1],
            td_don_gia: group[2][0],
            td_san_luong: group[2][1],
            ghi_chu: "manual"
        };

        // Luôn thêm dòng vào dataRows (không ghi đè khi nạp nhiều lần cùng 1 kỳ)
        dataRows.push(entry);
        addedCount++;
    });

    // Sort by year/month/period
    dataRows.sort((a, b) => {
        if (a.nam !== b.nam) return a.nam - b.nam;
        if (a.thang !== b.thang) return a.thang - b.thang;
        return a.ky - b.ky;
    });

    // Auto-increment
    if (document.getElementById('auto_increment').checked) {
        let m = month, p = period;
        if (p === 3) { p = 1; m = m < 12 ? m + 1 : 1; } else { p++; }
        document.getElementById('input_month').value = m;
        document.getElementById('input_period').value = p;
    }

    // Clear input
    if (currentMode === 'string_mode') {
        document.getElementById('raw_data').value = '';
    } else {
        ['bt_price', 'bt_usage', 'cd_price', 'cd_usage', 'td_price', 'td_usage'].forEach(id => {
            document.getElementById(id).value = '';
        });
    }

    renderDataTable();
    updateExportSection();
    showMessage(`✓ Đã thêm ${addedCount} dòng dữ liệu (Tháng ${month}, Kỳ ${period}).`);
}

// ───────────────────────────────────────────────────────
// Render bảng dữ liệu & Xử lý chọn nhiều / Xóa hàng loạt
// ───────────────────────────────────────────────────────

function renderDataTable() {
    const tbody = document.getElementById('data_table_body');
    if (!tbody) return;
    tbody.innerHTML = '';

    const selectAllCb = document.getElementById('select_all_rows');
    const btnClearAll = document.getElementById('btn_clear_all');

    if (dataRows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="13" class="empty-state">Chưa có dữ liệu. Tạo file mới hoặc nạp file có sẵn để bắt đầu.</td></tr>`;
        if (selectAllCb) {
            selectAllCb.checked = false;
            selectAllCb.disabled = true;
        }
        if (btnClearAll) btnClearAll.disabled = true;
        selectedRowIndices.clear();
        updateBulkActionUI();
        return;
    }

    if (selectAllCb) {
        selectAllCb.disabled = false;
        selectAllCb.checked = selectedRowIndices.size === dataRows.length && dataRows.length > 0;
    }
    if (btnClearAll) btnClearAll.disabled = false;

    dataRows.forEach((row, index) => {
        const tr = document.createElement('tr');
        const isChecked = selectedRowIndices.has(index);
        if (isChecked) {
            tr.style.backgroundColor = 'rgba(59, 130, 246, 0.12)';
        }

        const taxDisp = row.thue_vat !== undefined && row.thue_vat !== null ? `${row.thue_vat}%` : '0%';
        tr.innerHTML = `
            <td style="text-align:center;">
                <input type="checkbox" class="row-checkbox" data-index="${index}" onchange="excelToggleRowSelect(${index}, this.checked)" ${isChecked ? 'checked' : ''}>
            </td>
            <td style="text-align:center;"><b>${row.nam}</b></td>
            <td style="text-align:center;"><b>${row.thang}</b></td>
            <td style="text-align:center;">${row.ky}</td>
            <td style="text-align:center; color: var(--accent4); font-weight: 500;">${taxDisp}</td>
            <td>${fmtNum(row.bt_don_gia)}</td>
            <td>${fmtNum(row.bt_san_luong)}</td>
            <td>${fmtNum(row.cd_don_gia)}</td>
            <td>${fmtNum(row.cd_san_luong)}</td>
            <td>${fmtNum(row.td_don_gia)}</td>
            <td>${fmtNum(row.td_san_luong)}</td>
            <td style="font-size:0.78rem; color:var(--text-muted);">${row.ghi_chu || ''}</td>
            <td style="text-align:center;">
                <button class="btn-small" style="background: var(--danger); padding: 3px 8px; font-size: 0.72rem;" onclick="excelDeleteRow(${index})" title="Xóa dòng này">✕</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    updateBulkActionUI();
}

function updateBulkActionUI() {
    const btnDeleteSelected = document.getElementById('btn_delete_selected');
    const selectedCountSpan = document.getElementById('selected_count');
    const selectAllCb = document.getElementById('select_all_rows');

    const count = selectedRowIndices.size;
    if (selectedCountSpan) selectedCountSpan.textContent = count;

    if (btnDeleteSelected) {
        btnDeleteSelected.style.display = count > 0 ? 'inline-flex' : 'none';
    }

    if (selectAllCb && dataRows.length > 0) {
        selectAllCb.checked = count === dataRows.length;
        selectAllCb.indeterminate = count > 0 && count < dataRows.length;
    }
}

window.excelToggleSelectAll = function (masterCb) {
    if (masterCb.checked) {
        dataRows.forEach((_, idx) => selectedRowIndices.add(idx));
    } else {
        selectedRowIndices.clear();
    }
    renderDataTable();
}

window.excelToggleRowSelect = function (index, isChecked) {
    if (isChecked) {
        selectedRowIndices.add(index);
    } else {
        selectedRowIndices.delete(index);
    }
    renderDataTable();
}

window.excelDeleteSelectedRows = function () {
    const count = selectedRowIndices.size;
    if (count === 0) return;

    if (!confirm(`Bạn có chắc chắn muốn xóa ${count} dòng dữ liệu đã chọn?`)) return;

    // Lọc các dòng không nằm trong selectedRowIndices
    dataRows = dataRows.filter((_, idx) => !selectedRowIndices.has(idx));
    selectedRowIndices.clear();

    renderDataTable();
    updateExportSection();
    showMessage(`✓ Đã xóa ${count} dòng dữ liệu.`);
}

window.excelClearAllRows = function () {
    if (dataRows.length === 0) return;

    if (!confirm("Bạn có chắc chắn muốn xóa toàn bộ dữ liệu trong bảng?")) return;

    dataRows = [];
    selectedRowIndices.clear();

    renderDataTable();
    updateExportSection();
    showMessage("Đã xóa toàn bộ dữ liệu.");
}

window.excelDeleteRow = function (index) {
    if (index < 0 || index >= dataRows.length) return;
    const row = dataRows[index];
    if (!confirm(`Xóa dòng: Năm ${row.nam}, Tháng ${row.thang}, Kỳ ${row.ky}?`)) return;
    
    dataRows.splice(index, 1);
    selectedRowIndices.delete(index);
    
    // Cập nhật lại các index trong selectedRowIndices lớn hơn index đã xóa
    const newSelected = new Set();
    selectedRowIndices.forEach(idx => {
        if (idx < index) newSelected.add(idx);
        else if (idx > index) newSelected.add(idx - 1);
    });
    selectedRowIndices = newSelected;

    renderDataTable();
    updateExportSection();
    showMessage("Đã xóa dòng dữ liệu.");
}

// ───────────────────────────────────────────────────────
// Lưu file dữ liệu (SheetJS - client-side)
// ───────────────────────────────────────────────────────

window.excelSaveDataFile = function () {
    if (dataRows.length === 0) {
        showExportMessage("Chưa có dữ liệu để lưu.", true);
        return;
    }

    // Build worksheet data
    const wsData = [DATA_HEADERS.slice()]; // header row
    dataRows.forEach(row => {
        wsData.push([
            row.nam, row.thang, row.ky,
            row.thue_vat !== undefined && row.thue_vat !== null ? row.thue_vat : 0,
            row.bt_don_gia, row.bt_san_luong,
            row.cd_don_gia, row.cd_san_luong,
            row.td_don_gia, row.td_san_luong,
            row.ghi_chu || ""
        ]);
    });

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(wsData);

    // Set column widths
    ws['!cols'] = [
        { wch: 6 },  // nam
        { wch: 7 },  // thang
        { wch: 5 },  // ky
        { wch: 10 }, // thue_vat
        { wch: 12 }, // bt_don_gia
        { wch: 14 }, // bt_san_luong
        { wch: 12 }, // cd_don_gia
        { wch: 14 }, // cd_san_luong
        { wch: 12 }, // td_don_gia
        { wch: 14 }, // td_san_luong
        { wch: 20 }, // ghi_chu
    ];

    XLSX.utils.book_append_sheet(wb, ws, DATA_SHEET_NAME);

    // Download
    XLSX.writeFile(wb, currentDataFilename || "DuLieu_Dien.xlsx");
    showExportMessage(`✓ Đã lưu file "${currentDataFilename}".`);
}

// ───────────────────────────────────────────────────────
// Xuất bảng tiêu thụ 12 tháng (gửi lên server)
// ───────────────────────────────────────────────────────

window.excelExportReport = async function () {
    if (dataRows.length === 0) {
        showExportMessage("Chưa có dữ liệu để xuất báo cáo.", true);
        return;
    }

    const reportName = currentDataFilename.replace(/\.xlsx$/i, '') + '_BaoCao.xlsx';

    try {
        showExportMessage("Đang tạo báo cáo...");

        const response = await fetch('/api/excel/export-electricity-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: dataRows,
                filename: reportName
            })
        });

        if (!response.ok) {
            let errMsg = 'Lỗi khi tạo báo cáo.';
            try {
                const errData = await response.json();
                if (errData.error) errMsg = errData.error;
            } catch (_) { }
            throw new Error(errMsg);
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = downloadUrl;
        anchor.download = reportName;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(downloadUrl);

        showExportMessage(`✓ Đã xuất báo cáo "${reportName}" thành công.`);
    } catch (error) {
        showExportMessage(error.message || "Xuất báo cáo thất bại.", true);
    }
}

// ───────────────────────────────────────────────────────
// Paste handler cho Manual Mode
// ───────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const btPriceField = document.getElementById('bt_price');
    if (btPriceField) {
        btPriceField.addEventListener('paste', function (event) {
            const pasteData = (event.clipboardData || window.clipboardData).getData('text');
            const lines = pasteData.trim().split(/\r?\n/).map(line => line.trim()).filter(line => line.length > 0);

            if (lines.length >= 3) {
                event.preventDefault();
                const parseLine = (line) => line.split(/\s+/);
                const bt = parseLine(lines[0]), cd = parseLine(lines[1]), td = parseLine(lines[2]);

                if (bt.length >= 2) { document.getElementById('bt_price').value = bt[0]; document.getElementById('bt_usage').value = bt[1]; }
                if (cd.length >= 2) { document.getElementById('cd_price').value = cd[0]; document.getElementById('cd_usage').value = cd[1]; }
                if (td.length >= 2) { document.getElementById('td_price').value = td[0]; document.getElementById('td_usage').value = td[1]; }
            }
        });
    }
});

// ───────────────────────────────────────────────────────
// Keyboard shortcuts
// ───────────────────────────────────────────────────────

document.addEventListener('keydown', function (event) {
    if (event.ctrlKey && event.key === 'Enter') {
        excelSubmitData();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const rawDataEl = document.getElementById('raw_data');
    if (rawDataEl) {
        rawDataEl.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                excelSubmitData();
            }
        });
    }
});


// ═══════════════════════════════════════════════════════
// CHART EXTRACTION (giữ nguyên cho workspace-chart)
// ═══════════════════════════════════════════════════════

function parseFilenameFromContentDisposition(contentDisposition) {
    if (!contentDisposition) return null;
    const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match && utf8Match[1]) {
        try {
            return decodeURIComponent(utf8Match[1]);
        } catch (_error) {
            return utf8Match[1];
        }
    }
    const asciiMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
    return asciiMatch ? asciiMatch[1] : null;
}

// Khởi tạo drag & drop cho chart workspace
document.addEventListener('DOMContentLoaded', () => {
    const dropArea = document.getElementById('chart-drop-area');
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
            dropArea.addEventListener(ev, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(ev => {
            dropArea.addEventListener(ev, () => {
                dropArea.style.borderColor = 'var(--accent)';
                dropArea.style.background = 'rgba(109, 40, 217, 0.08)';
            });
        });

        ['dragleave', 'drop'].forEach(ev => {
            dropArea.addEventListener(ev, () => {
                dropArea.style.borderColor = 'rgba(109, 40, 217, 0.45)';
                dropArea.style.background = 'var(--upload-bg)';
            });
        });

        dropArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer && e.dataTransfer.files;
            if (files && files.length > 0) {
                document.getElementById('chart_excel_file').files = files;
                window.updateChartFileLabel();
            }
        });
    }
});

window.updateChartFileLabel = function () {
    const input = document.getElementById('chart_excel_file');
    const label = document.getElementById('chart-file-label');
    const btn = document.getElementById('btn_extract_charts');
    if (input.files && input.files.length > 0) {
        label.textContent = "📁 " + input.files[0].name;
        label.style.color = "var(--accent2)";
        btn.disabled = false;
    } else {
        label.textContent = "Chưa chọn file Excel";
        label.style.color = "var(--text-muted)";
        btn.disabled = true;
    }
}

window.extractCharts = async function () {
    const fileInput = document.getElementById('chart_excel_file');
    const msgDiv = document.getElementById('chart_message');
    const btn = document.getElementById('btn_extract_charts');
    const spinner = document.getElementById('chart-spinner');
    const btnText = document.getElementById('chart-btn-text');

    if (!fileInput.files || fileInput.files.length === 0) {
        msgDiv.textContent = "Vui lòng chọn một file Excel (.xlsx, .xls)";
        msgDiv.className = "error";
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    if (btnText) btnText.textContent = "Đang trích xuất...";
    msgDiv.textContent = "Đang xử lý, vui lòng đợi (có thể mất chút thời gian)...";
    msgDiv.className = "";
    msgDiv.style.color = "var(--text-muted)";

    try {
        const response = await fetch('/api/excel/extract-charts', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let errorText = "Lỗi khi trích xuất biểu đồ.";
            try {
                const errData = await response.json();
                if (errData.error) errorText = errData.error;
            } catch (e) { }
            throw new Error(errorText);
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = downloadUrl;

        let contentDisp = response.headers.get("Content-Disposition");
        let filename = parseFilenameFromContentDisposition(contentDisp);
        if (!filename) {
            const originalName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
            filename = `Charts_${originalName}.zip`;
        }

        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(downloadUrl);

        msgDiv.textContent = "✓ Trích xuất biểu đồ thành công!";
        msgDiv.className = "success";
        msgDiv.style.color = "var(--state-success-text)";
    } catch (error) {
        msgDiv.textContent = error.message;
        msgDiv.className = "error";
        msgDiv.style.color = "var(--state-error-text)";
    } finally {
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.textContent = "🚀 Trích xuất SVG (ZIP)";
    }
}
