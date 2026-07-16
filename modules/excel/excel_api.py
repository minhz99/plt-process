import io
import json
import re
import os
import tempfile
import zipfile
import shutil
from copy import copy

from flask import Blueprint, jsonify, request, send_file

try:
    from openpyxl import load_workbook
except Exception:  # pragma: no cover - dependency guard
    load_workbook = None

try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None

excel_bp = Blueprint('excel_bp', __name__)
CELL_ADDR_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")


@excel_bp.route('/apply-updates', methods=['POST'])
def apply_updates():
    """
    Cập nhật giá trị vào file Excel được upload trong khi vẫn giữ nguyên định dạng (styles).
    
    Hỗ trợ hai loại thao tác:
    1. Cập nhật giá trị ô: Dựa trên địa chỉ ô (vd: 'A1').
    2. Chèn dòng mới: Chèn dòng tại vị trí chỉ định và sao chép định dạng từ dòng phía trên.
    
    Returns:
        Response: File Excel đã được cập nhật hoặc lỗi JSON.
    """
    if load_workbook is None:
        return jsonify({"error": "Thiếu thư viện openpyxl trên server."}), 500

    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"error": "Cần upload file Excel (.xlsx)."}), 400

    filename = uploaded_file.filename or "KetQua_Excel.xlsx"
    if not filename.lower().endswith(".xlsx"):
        return jsonify({"error": "Chỉ hỗ trợ file định dạng .xlsx."}), 400

    updates_raw = request.form.get("updates", "[]")
    try:
        updates = json.loads(updates_raw)
    except json.JSONDecodeError:
        return jsonify({"error": "Dữ liệu updates không phải JSON hợp lệ."}), 400

    if not isinstance(updates, list):
        return jsonify({"error": "Dữ liệu updates phải là mảng JSON."}), 400

    try:
        workbook = load_workbook(filename=io.BytesIO(uploaded_file.read()))
    except Exception:
        return jsonify({"error": "Không đọc được file Excel đầu vào."}), 400

    for idx, item in enumerate(updates):
        if not isinstance(item, dict):
            return jsonify({"error": f"Update tại vị trí {idx} không hợp lệ."}), 400

        sheet_name = str(item.get("sheet", "")).strip()
        if not sheet_name:
            return jsonify({"error": f"Thiếu tên sheet tại vị trí {idx}."}), 400
        if sheet_name not in workbook.sheetnames:
            return jsonify({"error": f"Không tìm thấy sheet '{sheet_name}' trong file Excel."}), 400

        worksheet = workbook[sheet_name]

        if item.get("type") == "insert_row":
            try:
                row_idx = int(item.get("row"))
            except (ValueError, TypeError):
                return jsonify({"error": f"Dòng chèn tại vị trí {idx} không hợp lệ."}), 400
            
            worksheet.insert_rows(row_idx)
            
            # Copy styles and formulas from the row above
            src_row = row_idx - 1
            if src_row > 0:
                # Need to import Translator here or at the top
                from openpyxl.formula.translate import Translator
                for col_idx in range(1, worksheet.max_column + 1):
                    src_cell = worksheet.cell(row=src_row, column=col_idx)
                    tgt_cell = worksheet.cell(row=row_idx, column=col_idx)
                    
                    if src_cell.has_style:
                        tgt_cell.font = copy(src_cell.font)
                        tgt_cell.border = copy(src_cell.border)
                        tgt_cell.fill = copy(src_cell.fill)
                        tgt_cell.number_format = copy(src_cell.number_format)
                        tgt_cell.protection = copy(src_cell.protection)
                        tgt_cell.alignment = copy(src_cell.alignment)
                    
                    if src_cell.data_type == 'f':
                        try:
                            tgt_cell.value = Translator(src_cell.value, origin=src_cell.coordinate).translate_formula(tgt_cell.coordinate)
                        except Exception:
                            # Fallback if formula translation fails
                            tgt_cell.value = src_cell.value
                            
            # Fix all formulas below the inserted row because openpyxl insert_rows doesn't update references
            def shift_formula(formula, insert_row_idx, num_rows=1):
                def repl(m):
                    if m.group(5):  # Range reference
                        col1_abs, col1, row1_abs, row1_str = m.group(1), m.group(2), m.group(3), m.group(4)
                        col2_abs, col2, row2_abs, row2_str = m.group(6), m.group(7), m.group(8), m.group(9)
                        row1 = int(row1_str)
                        row2 = int(row2_str)
                        
                        if row1_abs != '$' and row1 >= insert_row_idx:
                            row1 += num_rows
                            
                        # Expand the range if inserted exactly at boundary (row2 + 1)
                        if row2_abs != '$':
                            if row2 >= insert_row_idx or row2 == insert_row_idx - 1:
                                row2 += num_rows
                                
                        return f"{col1_abs}{col1}{row1_abs}{row1}:{col2_abs}{col2}{row2_abs}{row2}"
                    else:  # Single cell reference
                        col_abs, col, row_abs, row_str = m.group(1), m.group(2), m.group(3), m.group(4)
                        row = int(row_str)
                        if row_abs != '$' and row >= insert_row_idx:
                            row += num_rows
                        return f"{col_abs}{col}{row_abs}{row}"

                pattern = r'(?<![a-zA-Z])(\$?)([A-Z]{1,3})(\$?)(\d+)(?:(:)(\$?)([A-Z]{1,3})(\$?)(\d+))?(?!\()'
                return re.sub(pattern, repl, formula)

            for row in worksheet.iter_rows():
                for cell in row:
                    if cell.row != row_idx and cell.data_type == 'f' and cell.value and isinstance(cell.value, str):
                        new_formula = shift_formula(cell.value, row_idx)
                        if new_formula != cell.value:
                            cell.value = new_formula
                            
            continue

        cell_address = str(item.get("address", "")).strip().upper()
        if not CELL_ADDR_RE.fullmatch(cell_address):
            return jsonify({"error": f"Địa chỉ ô '{cell_address}' không hợp lệ."}), 400

        worksheet[cell_address].value = item.get("value")

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    output_name = (request.form.get("filename", "") or filename).strip() or "KetQua_Excel.xlsx"
    if not output_name.lower().endswith(".xlsx"):
        output_name = f"{output_name}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=output_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

@excel_bp.route('/extract-charts', methods=['POST'])
def extract_charts():
    """
    Trích xuất toàn bộ biểu đồ từ file Excel và gom vào thư mục có tên của sheet.
    Trả về file ZIP chứa tất cả các ảnh dưới dạng SVG.
    """
    if win32com is None:
        return jsonify({"error": "Thiếu thư viện pywin32 hoặc không chạy trên môi trường Windows."}), 500

    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"error": "Cần upload file Excel."}), 400

    filename = uploaded_file.filename
    if not (filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls")):
        return jsonify({"error": "Chỉ hỗ trợ file Excel (.xls, .xlsx)."}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        ext = os.path.splitext(filename)[1]
        input_filepath = os.path.join(temp_dir, f"input_file{ext}")
        uploaded_file.save(input_filepath)
        
        # Khởi tạo COM để dùng pywin32 trong thread của Flask
        pythoncom.CoInitialize()
        
        excel = None
        try:
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            
            wb = excel.Workbooks.Open(os.path.abspath(input_filepath))
            
            valid_charts_count = 0
            charts_dir = os.path.join(temp_dir, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            for sheet in wb.Worksheets:
                chart_objects = sheet.ChartObjects()
                if chart_objects.Count > 0:
                    sheet_name = sheet.Name
                    sheet_dir = os.path.join(charts_dir, sheet_name)
                    os.makedirs(sheet_dir, exist_ok=True)
                    
                    for idx, chart_obj in enumerate(chart_objects):
                        # Bỏ qua các object quá nhỏ (thường là icon, nút bấm, hình rác)
                        if chart_obj.Width < 50 or chart_obj.Height < 50:
                            continue
                            
                        chart = chart_obj.Chart
                        image_path = os.path.join(sheet_dir, f"chart_{idx + 1}.svg")
                        try:
                            chart.Export(os.path.abspath(image_path), "SVG")
                            # Lọc các file SVG lỗi hoặc rỗng (thường < 100 bytes)
                            if os.path.exists(image_path):
                                if os.path.getsize(image_path) < 100:
                                    os.remove(image_path)
                                else:
                                    valid_charts_count += 1
                        except Exception:
                            pass
            
            wb.Close(SaveChanges=False)
            excel.Quit()
        except Exception as e:
            if excel:
                excel.Quit()
            raise e
        finally:
            pythoncom.CoUninitialize()

        if valid_charts_count == 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({"error": "Không tìm thấy biểu đồ hợp lệ nào (có thể toàn bộ là biểu đồ trống hoặc hình rác)."}), 404

        # Nén thành zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(charts_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, charts_dir)
                    zipf.write(file_path, arcname)

        zip_buffer.seek(0)
        zip_filename = f"Charts_{os.path.splitext(filename)[0]}.zip"
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=zip_filename,
            mimetype="application/zip"
        )
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({"error": f"Lỗi khi trích xuất biểu đồ: {str(e)}"}), 500

