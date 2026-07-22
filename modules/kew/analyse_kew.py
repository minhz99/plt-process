import pandas as pd
import json
import os

CONFIG = {}
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')
if os.path.exists(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
    except Exception:
        pass

def parse_inps(filepath):
    """
    Đọc và phân tích cấu trúc file INPS (dữ liệu chất lượng điện từ thiết bị KEW).
    
    File INPS có cấu trúc nhị phân kết hợp văn bản, chứa các đại lượng trung bình, 
    cực đại và cực tiểu theo từng chu kỳ lưu trữ (thường là 1 giây hoặc 1 phút).
    
    Args:
        filepath: Đường dẫn tới file .KEW.
        
    Returns:
        tuple: (Chuỗi Magic định danh, pandas.DataFrame chứa dữ liệu đã xử lý).
    """
    try:
        with open(filepath, 'rb') as f:
            magic_bytes = f.readline().strip()
            magic = magic_bytes.decode('ascii', errors='ignore')
            
            header_bytes = f.readline()
            header_str = header_bytes.decode('ascii', errors='ignore').strip()
            
            # Tách header: cột dạng "AVG_V1[V],,," = 3 slots (avg, min, max)
            # Xây dựng danh sách tên cột đầy đủ
            raw_cols = header_str.split(',')
            expanded_cols = []
            i = 0
            while i < len(raw_cols):
                col = raw_cols[i].strip()
                if col == '':
                    # Cột trống sau tên đại lượng = min, max
                    if expanded_cols:
                        base = expanded_cols[-1].split('_avg')[0] if '_avg' in expanded_cols[-1] else expanded_cols[-1]
                        count_empty = 0
                        j = i
                        while j < len(raw_cols) and raw_cols[j].strip() == '':
                            count_empty += 1
                            j += 1
                        if count_empty >= 2:
                            expanded_cols.append(base + '_min')
                            expanded_cols.append(base + '_max')
                            i += 2
                            continue
                        else:
                            expanded_cols.append('')
                    else:
                        expanded_cols.append('')
                else:
                    expanded_cols.append(col)
                i += 1
            
            # Đọc dữ liệu
            data_rows = []
            for line in f:
                line_str = line.decode('ascii', errors='ignore').strip()
                if not line_str:
                    continue
                parts = line_str.split(',')
                data_rows.append(parts)
            
            # Đặt tên duy nhất cho cột rỗng để tránh lỗi DataFrame
            final_cols = []
            blank_count = 0
            for col in expanded_cols[:len(raw_cols)]:
                if col == '':
                    blank_count += 1
                    final_cols.append(f'_blank_{blank_count}')
                else:
                    final_cols.append(col)
            
            # Tạo DataFrame
            n_cols = len(raw_cols)
            padded_rows = []
            for row in data_rows:
                if len(row) < n_cols:
                    row = row + [''] * (n_cols - len(row))
                padded_rows.append(row[:n_cols])
            
            df = pd.DataFrame(padded_rows, columns=final_cols)
            
            # Parse datetime
            if 'DATE' in df.columns and 'TIME' in df.columns:
                datetime_str = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
                df['DATETIME'] = pd.to_datetime(
                    datetime_str, format='%Y/%m/%d %H:%M:%S', errors='coerce'
                )
                if df['DATETIME'].isna().all():
                    df['DATETIME'] = pd.to_datetime(datetime_str, errors='coerce')
            
            # Parse numeric (bỏ qua cột placeholder _blank_)
            skip = {'DATE', 'TIME', 'DATETIME', 'ELAPSED TIME'}
            for col in df.columns:
                if col in skip or col.startswith('_blank_'):
                    continue
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Tự động nhận diện và xử lý đấu ngược dây CT
            df, _, _ = detect_and_correct_ct_reversal(df, auto_correct=True)

            return magic, df
    
    except FileNotFoundError:
        print(f"[ERROR] INPS file not found: {filepath}")
        return None, None
    except Exception as e:
        print(f"[WARN] Could not parse INPS: {e}")
        return None, None

def detect_and_correct_ct_reversal(df: pd.DataFrame, auto_correct: bool = True) -> tuple[pd.DataFrame, bool, list[str]]:
    """
    Tự động nhận diện và xử lý trường hợp đấu ngược dây CT (Biến dòng).

    Dấu hiệu:
    - Giá trị trung bình của các đại lượng công suất tác dụng (P, P1, P2, P3) bị âm (P < 0).
    - Giá trị trung bình hệ số công suất (PF, PF1, PF2, PF3) bị âm.

    Xử lý:
    - Đảo chiều dấu cho công suất tác dụng P: P -> -P (hoặc |P| khi âm).
    - Đảo chiều dấu cho hệ số công suất PF: PF -> |PF|.
    - Đảo chiều dấu cho công suất phản kháng Q: Q -> -Q.
    - Cập nhật lại các cột _min và _max nếu có để đảm bảo min <= max.

    Args:
        df: DataFrame chứa dữ liệu đo KEW.
        auto_correct: Nếu True, tự động đảo chiều dữ liệu trong DataFrame khi phát hiện.

    Returns:
        tuple: (df_updated, was_reversed, list_of_details)
    """
    if df is None or df.empty:
        return df, False, []

    df = df.copy()

    # Tìm các kênh công suất tác dụng chính (AVG_P, AVG_P1, AVG_P2, AVG_P3)
    p_cols_to_check = []
    for c in df.columns:
        c_upper = c.upper()
        if c_upper.startswith("AVG_P") and not c_upper.startswith("AVG_PF") and not c_upper.startswith("AVG_PH"):
            if not c.endswith("_min") and not c.endswith("_max"):
                p_cols_to_check.append(c)

    reversed_channels = []

    for col in p_cols_to_check:
        vals = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(vals) > 0 and vals.mean() < -0.01:
            col_upper = col.upper()
            if "P1" in col_upper:
                label = "Pha 1 (P1 < 0)"
            elif "P2" in col_upper:
                label = "Pha 2 (P2 < 0)"
            elif "P3" in col_upper:
                label = "Pha 3 (P3 < 0)"
            else:
                label = "Tổng (P < 0)"
            reversed_channels.append((col, label))

    if not reversed_channels:
        df.attrs['ct_reversed'] = False
        df.attrs['ct_reversed_details'] = []
        df.attrs['ct_reversed_msg'] = ""
        return df, False, []

    was_reversed = True
    details_labels = [label for _, label in reversed_channels]

    if auto_correct:
        # 1. Đảo chiều và hoán đổi min/max cho các cột P
        for c in p_cols_to_check:
            vals = pd.to_numeric(df[c], errors='coerce')
            if vals.notna().any() and vals.dropna().mean() < 0:
                df[c] = vals.apply(lambda v: -v if pd.notna(v) else v)
                min_col = c + "_min"
                max_col = c + "_max"
                if min_col in df.columns and max_col in df.columns:
                    v_min = pd.to_numeric(df[min_col], errors='coerce')
                    v_max = pd.to_numeric(df[max_col], errors='coerce')
                    df[min_col] = v_max.apply(lambda v: -v if pd.notna(v) else v)
                    df[max_col] = v_min.apply(lambda v: -v if pd.notna(v) else v)

        # 2. Đảo chiều và hoán đổi min/max cho các cột PF
        for col in list(df.columns):
            cu = col.upper()
            if "AVG_PF" in cu and not col.endswith("_min") and not col.endswith("_max"):
                vals = pd.to_numeric(df[col], errors='coerce')
                if vals.notna().any() and (vals.dropna() < 0).mean() > 0.3:
                    df[col] = vals.apply(lambda v: abs(v) if pd.notna(v) else v)
                    min_col = col + "_min"
                    max_col = col + "_max"
                    if min_col in df.columns and max_col in df.columns:
                        v_min = pd.to_numeric(df[min_col], errors='coerce')
                        v_max = pd.to_numeric(df[max_col], errors='coerce')
                        df[min_col] = v_max.apply(lambda v: abs(v) if pd.notna(v) else v)
                        df[max_col] = v_min.apply(lambda v: abs(v) if pd.notna(v) else v)

        # 3. Đảo chiều và hoán đổi min/max cho các cột Q
        for col in list(df.columns):
            cu = col.upper()
            if cu.startswith("AVG_Q") and not col.endswith("_min") and not col.endswith("_max"):
                vals = pd.to_numeric(df[col], errors='coerce')
                if vals.notna().any():
                    df[col] = vals.apply(lambda v: -v if pd.notna(v) else v)
                    min_col = col + "_min"
                    max_col = col + "_max"
                    if min_col in df.columns and max_col in df.columns:
                        v_min = pd.to_numeric(df[min_col], errors='coerce')
                        v_max = pd.to_numeric(df[max_col], errors='coerce')
                        df[min_col] = v_max.apply(lambda v: -v if pd.notna(v) else v)
                        df[max_col] = v_min.apply(lambda v: -v if pd.notna(v) else v)

    msg = f"Phát hiện đấu ngược dây CT ({', '.join(details_labels)}). Hệ thống đã tự động đảo chiều dữ liệu P và PF."
    df.attrs['ct_reversed'] = was_reversed
    df.attrs['ct_reversed_details'] = details_labels
    df.attrs['ct_reversed_msg'] = msg

    return df, was_reversed, details_labels

def analyse_inps(df):
    """
    Tổng hợp các chỉ số thống kê từ DataFrame dữ liệu INPS.
    
    Args:
        df: DataFrame chứa dữ liệu đo lường.
        
    Returns:
        dict: Dictionary chứa các thống kê (avg, min, max, timestamps) theo từng cột.
    """
    if df is None or df.empty:
        return {}
    
    result = {}
    skip_cols = {'DATE', 'TIME', 'DATETIME', 'ELAPSED TIME', 'ELAPSED TIME_min', 'ELAPSED TIME_max'}

    # Giữ thông tin metadata về đấu ngược dây CT nếu có
    if getattr(df, 'attrs', None):
        if df.attrs.get('ct_reversed'):
            result['_ct_reversed'] = True
            result['_ct_reversed_details'] = df.attrs.get('ct_reversed_details', [])
            result['_ct_reversed_msg'] = df.attrs.get('ct_reversed_msg', '')
    
    # Lấy các cột avg (không phải _min/_max)
    avg_cols = [c for c in df.columns 
                if c not in skip_cols 
                and not c.endswith('_min') 
                and not c.endswith('_max')
                and c.strip() != '']
    
    timestamps = []
    if 'DATETIME' in df.columns:
        timestamps = df['DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    
    for col in avg_cols:
        try:
            vals = pd.to_numeric(df[col], errors='coerce')
            min_col = col + '_min'
            max_col = col + '_max'
            
            entry = {
                'timestamps': timestamps,
                'values': vals.tolist(),
                'avg': float(vals.mean()) if not vals.isna().all() else None,
                'min': float(vals.min()) if not vals.isna().all() else None,
                'max': float(vals.max()) if not vals.isna().all() else None,
            }
            
            if min_col in df.columns:
                min_vals = pd.to_numeric(df[min_col], errors='coerce')
                entry['recorded_min'] = float(min_vals.min()) if not min_vals.isna().all() else None
            if max_col in df.columns:
                max_vals = pd.to_numeric(df[max_col], errors='coerce')
                entry['recorded_max'] = float(max_vals.max()) if not max_vals.isna().all() else None
            
            result[col] = entry
        except Exception:
            continue
    
    return result

def find_file(folder, prefix):
    """
    Tìm file .KEW trong thư mục dựa trên tiền tố tên file.
    
    Args:
        folder: Thư mục cần tìm.
        prefix: Tiền tố tên file (không phân biệt hoa thường).
        
    Returns:
        str or None: Đường dẫn file nếu tìm thấy, ngược lại là None.
    """
    for f in os.listdir(folder):
        if f.upper().startswith(prefix.upper()) and f.upper().endswith('.KEW'):
            return os.path.join(folder, f)
    return None



