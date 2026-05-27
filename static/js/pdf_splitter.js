(function () {
  let _selectedPdfFile = null;
  let _progressInterval = null;

  function setBtnState() {
    const btn = document.getElementById('btn-pdf-process');
    if (btn) btn.disabled = !_selectedPdfFile;
  }

  function setFileLabel(name) {
    const el = document.getElementById('pdf-file-label');
    if (el) {
      el.textContent = name ? `Đã chọn: ${name}` : 'Chưa chọn file PDF';
    }
  }

  function showStatus(text, type = 'muted') {
    const el = document.getElementById('pdf-status');
    if (el) {
      el.textContent = text;
      if (type === 'success') {
        el.style.color = 'var(--state-success-text)';
      } else if (type === 'danger') {
        el.style.color = 'var(--state-error-text)';
      } else {
        el.style.color = 'var(--text-muted)';
      }
    }
  }

  function showError(msg) {
    const errorEl = document.getElementById('pdf-error');
    if (errorEl) {
      if (msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
      } else {
        errorEl.style.display = 'none';
      }
    }
  }

  // Khởi tạo các sự kiện drag & drop và click chọn file
  document.addEventListener('DOMContentLoaded', () => {
    const inp = document.getElementById('pdf-file-input');
    const drop = document.getElementById('pdf-drop-area');
    const btnProcess = document.getElementById('btn-pdf-process');

    if (inp) {
      inp.addEventListener('change', () => {
        const f = inp.files && inp.files[0];
        if (f) {
          if (!f.name.toLowerCase().endsWith('.pdf')) {
            showError('Vui lòng chọn tệp định dạng PDF (.pdf)');
            _selectedPdfFile = null;
            setFileLabel('');
            setBtnState();
            return;
          }
          showError('');
          _selectedPdfFile = f;
          setFileLabel(f.name);
          setBtnState();
        }
        inp.value = '';
      });
    }

    if (drop) {
      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
        drop.addEventListener(ev, (e) => {
          e.preventDefault();
          e.stopPropagation();
        }, false);
      });

      ['dragenter', 'dragover'].forEach(ev => {
        drop.addEventListener(ev, () => {
          drop.style.borderColor = 'var(--accent)';
          drop.style.background = 'rgba(109, 40, 217, 0.08)';
        });
      });

      ['dragleave', 'drop'].forEach(ev => {
        drop.addEventListener(ev, () => {
          drop.style.borderColor = 'rgba(109, 40, 217, 0.45)';
          drop.style.background = 'var(--upload-bg)';
        });
      });

      drop.addEventListener('drop', (e) => {
        const files = e.dataTransfer && e.dataTransfer.files;
        if (!files || !files.length) return;
        const f = files[0];
        if (!f.name.toLowerCase().endsWith('.pdf')) {
          showError('Vui lòng kéo thả file có định dạng .pdf');
          return;
        }
        showError('');
        _selectedPdfFile = f;
        setFileLabel(f.name);
        setBtnState();
      });
    }

    if (btnProcess) {
      btnProcess.addEventListener('click', submitPdfSplit);
    }
  });

  async function submitPdfSplit() {
    if (!_selectedPdfFile) return;

    const btn = document.getElementById('btn-pdf-process');
    const spin = document.getElementById('pdf-spinner');
    const btnText = document.getElementById('pdf-btn-text');
    const progressContainer = document.getElementById('pdf-progress-container');
    const progressBar = document.getElementById('pdf-progress-bar');
    const progressPercent = document.getElementById('pdf-progress-percent');
    const progressStep = document.getElementById('pdf-progress-step');

    // Reset UI & Khóa tương tác
    btn.disabled = true;
    if (spin) spin.style.display = 'inline-block';
    if (btnText) btnText.textContent = 'Đang xử lý...';
    showError('');
    showStatus('Đang gửi dữ liệu...');

    // Hiển thị thanh tiến trình
    if (progressContainer) progressContainer.style.display = 'block';
    if (progressBar) progressBar.style.width = '0%';
    if (progressPercent) progressPercent.textContent = '0%';
    if (progressStep) progressStep.textContent = 'Đang tải file PDF lên máy chủ...';

    // Giả lập thanh tiến trình chạy từ 0% đến 92% trong quá trình server xử lý (vì PDF split + grayscale của Ghostscript chạy đồng bộ)
    let percent = 0;
    _progressInterval = setInterval(() => {
      if (percent < 90) {
        percent += Math.floor(Math.random() * 8) + 2;
        if (percent > 90) percent = 90;
        
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressPercent) progressPercent.textContent = `${percent}%`;
        
        if (percent < 30) {
          if (progressStep) progressStep.textContent = 'Đang lưu file tạm thời...';
        } else if (percent < 60) {
          if (progressStep) progressStep.textContent = 'Đang phân tách bìa và trang nội dung...';
        } else {
          if (progressStep) progressStep.textContent = 'Đang chuyển đổi màu sắc (Grayscale) bằng Ghostscript...';
        }
      }
    }, 400);

    const fd = new FormData();
    fd.append('file', _selectedPdfFile, _selectedPdfFile.name);

    try {
      const response = await fetch('/api/pdf/split', {
        method: 'POST',
        body: fd
      });

      // Dừng giả lập progress
      clearInterval(_progressInterval);

      if (!response.ok) {
        let errMsg = `Lỗi HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData && errData.error) errMsg = errData.error;
        } catch (_) {}
        throw new Error(errMsg);
      }

      // Xử lý khi thành công
      if (progressBar) progressBar.style.width = '100%';
      if (progressPercent) progressPercent.textContent = '100%';
      if (progressStep) progressStep.textContent = 'Hoàn tất! Đang đóng gói tệp ZIP...';
      showStatus('Thành công!', 'success');

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      // Tạo tên file download
      let origName = _selectedPdfFile.name;
      if (origName.toLowerCase().endsWith('.pdf')) {
        origName = origName.slice(0, -4);
      }
      const downloadName = `in-${origName}.zip`;

      // Kích hoạt download
      const a = document.createElement('a');
      a.href = url;
      a.download = downloadName;
      document.body.appendChild(a);
      a.click();
      
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 400);

      // Reset UI sau 3 giây thành công
      setTimeout(() => {
        if (progressContainer) progressContainer.style.display = 'none';
        showStatus('');
      }, 3000);

    } catch (err) {
      clearInterval(_progressInterval);
      if (progressContainer) progressContainer.style.display = 'none';
      showError(err.message || 'Có lỗi xảy ra trong quá trình xử lý PDF.');
      showStatus('Thất bại', 'danger');
    } finally {
      btn.disabled = false;
      if (spin) spin.style.display = 'none';
      if (btnText) btnText.textContent = '🚀 Bắt đầu tách file';
    }
  }
})();
