async function runSynopexReport() {
  const zipInput = document.getElementById('synopex-zip');
  const statusEl = document.getElementById('synopex-status');
  const errorEl = document.getElementById('synopex-error');
  const downloadEl = document.getElementById('synopex-download');
  const btn = document.getElementById('btn-synopex-generate');
  const spinner = document.getElementById('synopex-spinner');
  const btnText = document.getElementById('synopex-btn-text');

  const zipFile = zipInput?.files?.[0];

  errorEl.style.display = 'none';
  errorEl.textContent = '';
  if (downloadEl) downloadEl.style.display = 'none';

  if (!zipFile) {
    errorEl.textContent = 'Vui lòng chọn file ZIP dữ liệu.';
    errorEl.style.display = 'block';
    return;
  }

  const formData = new FormData();
  formData.append('data_zip', zipFile);

  statusEl.textContent = `Đang xử lý ${zipFile.name}...`;
  btn.disabled = true;
  spinner.style.display = 'inline-block';
  btnText.textContent = 'Đang xử lý...';

  try {
    const response = await fetch('/api/synopex/generate', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let message = `Lỗi HTTP ${response.status}`;
      try {
        const data = await response.json();
        if (data?.error) message = data.error;
      } catch (_) { /* ignore */ }
      throw new Error(message);
    }

    const blob = await response.blob();
    const header = response.headers.get('Content-Disposition') || '';
    const match = header.match(/filename="?([^"]+)"?/i);
    const filename = match?.[1] || 'KEW_Synopex_Report.docx';

    if (downloadEl) {
      const oldUrl = downloadEl.getAttribute('href');
      if (oldUrl && oldUrl !== '#') URL.revokeObjectURL(oldUrl);

      const url = URL.createObjectURL(blob);
      downloadEl.href = url;
      downloadEl.download = filename;
      downloadEl.style.display = 'inline-block';
    }

    statusEl.textContent = `Đã tạo xong báo cáo: ${filename}`;
  } catch (error) {
    errorEl.textContent = error.message || 'Không thể tạo báo cáo.';
    errorEl.style.display = 'block';
    statusEl.textContent = '';
  } finally {
    btn.disabled = false;
    spinner.style.display = 'none';
    btnText.textContent = 'Tạo báo cáo Word';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const zipInput = document.getElementById('synopex-zip');
  if (!zipInput) return;

  zipInput.addEventListener('change', () => {
    const statusEl = document.getElementById('synopex-status');
    const downloadEl = document.getElementById('synopex-download');
    if (downloadEl) downloadEl.style.display = 'none';
    if (zipInput.files?.[0] && statusEl) {
      statusEl.textContent = `Đã chọn ZIP: ${zipInput.files[0].name}`;
    }
  });
});
