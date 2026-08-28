(function () {
  let compressSelectedFiles = [];

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function setCompressProcessing(processing) {
    const btn = document.getElementById('btn-compress-process');
    const spin = document.getElementById('compress-spinner');
    const btnText = document.getElementById('compress-btn-text');
    const progressContainer = document.getElementById('compress-progress-container');

    if (btn) btn.disabled = processing || compressSelectedFiles.length === 0;
    if (spin) spin.style.display = processing ? 'inline-block' : 'none';
    if (btnText) btnText.textContent = processing ? 'Đang xử lý...' : '🚀 Bắt đầu nén ảnh';
    if (progressContainer) progressContainer.style.display = processing ? 'block' : 'none';
  }

  function updateCompressFileLabel() {
    const label = document.getElementById('compress-file-label');
    const btn = document.getElementById('btn-compress-process');
    if (label) {
      if (compressSelectedFiles.length === 0) {
        label.textContent = 'Chưa chọn ảnh';
      } else {
        const totalSize = compressSelectedFiles.reduce((sum, f) => sum + f.size, 0);
        label.textContent = `Đã chọn: ${compressSelectedFiles.length} ảnh (${formatFileSize(totalSize)})`;
      }
    }
    if (btn && !document.getElementById('compress-spinner').style.display.includes('inline-block')) {
      btn.disabled = compressSelectedFiles.length === 0;
    }
  }

  function updateCompressFileList() {
    const listEl = document.getElementById('compress-file-list');
    if (!listEl) return;

    listEl.innerHTML = '';
    
    compressSelectedFiles.forEach((file, index) => {
      const item = document.createElement('div');
      item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8rem;';
      
      const info = document.createElement('div');
      info.style.cssText = 'display: flex; gap: 8px; align-items: center; overflow: hidden;';
      
      const icon = document.createElement('i');
      icon.className = 'bi bi-image';
      icon.style.color = 'var(--text-muted)';
      
      const name = document.createElement('span');
      name.textContent = file.name;
      name.style.cssText = 'color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;';
      
      const size = document.createElement('span');
      size.textContent = formatFileSize(file.size);
      size.style.cssText = 'color: var(--text-muted); font-size: 0.75rem;';
      
      info.appendChild(icon);
      info.appendChild(name);
      info.appendChild(size);
      
      const removeBtn = document.createElement('button');
      removeBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
      removeBtn.style.cssText = 'background: none; border: none; color: var(--state-error-text); cursor: pointer; padding: 4px;';
      removeBtn.onclick = (e) => {
        e.stopPropagation();
        compressSelectedFiles.splice(index, 1);
        updateCompressFileList();
        updateCompressFileLabel();
      };
      
      item.appendChild(info);
      item.appendChild(removeBtn);
      listEl.appendChild(item);
    });

    updateCompressFileLabel();
  }

  function showCompressStatus(text, type = 'muted') {
    const el = document.getElementById('compress-status');
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

  function showCompressError(msg) {
    const errorEl = document.getElementById('compress-error');
    if (errorEl) {
      if (msg) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
      } else {
        errorEl.style.display = 'none';
      }
    }
  }

  function hideCompressError() {
    showCompressError('');
  }

  function displayCompressStats(stats) {
    const container = document.getElementById('compress-stats-container');
    const content = document.getElementById('compress-stats-content');
    const errContainer = document.getElementById('compress-stats-errors');
    
    if (!container || !content || !stats) return;

    container.style.display = 'block';
    
    const saved = stats.original_size - stats.compressed_size;
    const ratio = stats.original_size > 0 ? ((saved / stats.original_size) * 100).toFixed(1) : 0;

    content.innerHTML = `
      <div><strong>Tổng số ảnh:</strong> ${stats.total || 0}</div>
      <div><strong>Đã nén:</strong> <span style="color: var(--state-success-text)">${(stats.success || 0) - (stats.kept_original || 0)}</span> | <strong>Giữ gốc:</strong> <span style="color: var(--accent2)">${stats.kept_original || 0}</span> | <strong>Thất bại:</strong> <span style="color: var(--state-error-text)">${stats.failed || 0}</span></div>
      <div><strong>Dung lượng gốc:</strong> ${formatFileSize(stats.original_size || 0)}</div>
      <div><strong>Dung lượng sau nén:</strong> ${formatFileSize(stats.compressed_size || 0)}</div>
      <div style="grid-column: 1 / -1; color: var(--accent2);"><strong>Tiết kiệm:</strong> ${formatFileSize(Math.max(0, saved))} (${ratio}%)</div>
      ${stats.kept_original > 0 ? `<div style="grid-column: 1 / -1; font-size: 0.78rem; color: var(--text-muted); font-style: italic;">ℹ️ ${stats.kept_original} ảnh đã được nén tốt sẵn nên giữ nguyên file gốc.</div>` : ''}
    `;

    if (stats.errors && stats.errors.length > 0 && errContainer) {
      errContainer.style.display = 'block';
      errContainer.innerHTML = '<strong>Lỗi chi tiết:</strong><br>' + stats.errors.map(e => `• ${e}`).join('<br>');
    } else if (errContainer) {
      errContainer.style.display = 'none';
      errContainer.innerHTML = '';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const inp = document.getElementById('compress-file-input');
    const drop = document.getElementById('compress-drop-area');
    const btnProcess = document.getElementById('btn-compress-process');
    const qualitySlider = document.getElementById('compress-quality');
    const qualityValue = document.getElementById('compress-quality-value');

    // Quality slider change
    if (qualitySlider && qualityValue) {
      qualitySlider.addEventListener('input', () => {
        qualityValue.textContent = `${qualitySlider.value}%`;
      });
    }

    // File input change
    if (inp) {
      inp.addEventListener('change', () => {
        if (inp.files && inp.files.length > 0) {
          for (let i = 0; i < inp.files.length; i++) {
            compressSelectedFiles.push(inp.files[i]);
          }
          hideCompressError();
          updateCompressFileList();
        }
        inp.value = '';
      });
    }

    // Drag and Drop
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
        
        let added = false;
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith('image/') || files[i].name.match(/\.(heic|heif)$/i)) {
            compressSelectedFiles.push(files[i]);
            added = true;
          }
        }

        if (added) {
          hideCompressError();
          updateCompressFileList();
        } else {
          showCompressError('Vui lòng kéo thả các file hình ảnh hợp lệ.');
        }
      });
    }

    if (btnProcess) {
      btnProcess.addEventListener('click', processCompressImages);
    }
  });

  function processCompressImages() {
    if (compressSelectedFiles.length === 0) return;

    hideCompressError();
    document.getElementById('compress-stats-container').style.display = 'none';
    setCompressProcessing(true);
    showCompressStatus('Đang chuẩn bị...', 'muted');

    const progressBar = document.getElementById('compress-progress-bar');
    const progressPercent = document.getElementById('compress-progress-percent');
    const progressStep = document.getElementById('compress-progress-step');

    if (progressBar) progressBar.style.width = '0%';
    if (progressPercent) progressPercent.textContent = '0%';
    if (progressStep) progressStep.textContent = 'Đang tải lên...';

    const quality = document.getElementById('compress-quality') ? document.getElementById('compress-quality').value : '80';
    const maxWidth = document.getElementById('compress-max-width') ? document.getElementById('compress-max-width').value : '1920';
    const maxHeight = document.getElementById('compress-max-height') ? document.getElementById('compress-max-height').value : '1080';
    const stripMeta = document.getElementById('compress-strip-meta') ? document.getElementById('compress-strip-meta').checked : true;
    const autoOrient = document.getElementById('compress-auto-orient') ? document.getElementById('compress-auto-orient').checked : true;

    const fd = new FormData();
    compressSelectedFiles.forEach(f => {
      fd.append('files', f);
    });
    fd.append('quality', quality);
    fd.append('max_width', maxWidth);
    fd.append('max_height', maxHeight);
    fd.append('strip_metadata', stripMeta);
    fd.append('auto_orient', autoOrient);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/compress/process', true);
    xhr.responseType = 'blob';

    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        const percentComplete = Math.round((e.loaded / e.total) * 100);
        if (progressBar) progressBar.style.width = percentComplete + '%';
        if (progressPercent) progressPercent.textContent = percentComplete + '%';
        if (percentComplete === 100 && progressStep) {
          progressStep.textContent = 'Đang xử lý (có thể mất một lúc)...';
        }
      }
    };

    xhr.onload = function () {
      setCompressProcessing(false);
      
      if (xhr.status === 200) {
        if (progressBar) progressBar.style.width = '100%';
        if (progressPercent) progressPercent.textContent = '100%';
        if (progressStep) progressStep.textContent = 'Hoàn tất!';
        showCompressStatus('Thành công!', 'success');

        // Handle statistics
        const statsHeader = xhr.getResponseHeader('X-Compress-Stats');
        if (statsHeader) {
          try {
            const stats = JSON.parse(statsHeader);
            displayCompressStats(stats);
          } catch (e) {
            console.error("Lỗi parse X-Compress-Stats", e);
          }
        }

        // Handle download
        const blob = xhr.response;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'images-compressed.zip';
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 400);

      } else {
        // Read blob as text to extract error
        const reader = new FileReader();
        reader.onload = function() {
          let errMsg = `Lỗi server (${xhr.status})`;
          try {
            const errData = JSON.parse(reader.result);
            if (errData && errData.error) errMsg = errData.error;
          } catch (e) {}
          showCompressError(errMsg);
          showCompressStatus('Thất bại', 'danger');
        };
        reader.readAsText(xhr.response);
      }
    };

    xhr.onerror = function () {
      setCompressProcessing(false);
      showCompressError('Lỗi kết nối mạng hoặc server không phản hồi.');
      showCompressStatus('Thất bại', 'danger');
    };

    xhr.send(fd);
  }
})();
