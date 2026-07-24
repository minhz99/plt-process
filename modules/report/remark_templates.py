"""Module chứa kho các mẫu câu động (remark sentence templates) cho báo cáo Word.

Chứa toàn bộ các danh sách mẫu câu đa dạng (mở đầu, đánh giá tải %, điện áp,
hệ số công suất cosφ, độ lệch pha, sóng hài, nguyên nhân theo nhóm phụ tải VFD/VSD/Servo/Lighting/MBA...)
giúp dễ dàng tinh chỉnh văn phong, sửa đổi hoặc mở rộng mẫu câu độc lập với logic xử lý báo cáo.
"""

from __future__ import annotations


# ── 1. ĐỘ LỆCH PHA (ΔU / ΔI) ────────────────────────────────────────────────
def get_unb_both_ok_templates(unb_both_ok_vals: str) -> list[str]:
    """Mẫu câu khi cả lệch pha điện áp ΔU và dòng điện ΔI đều đạt chuẩn."""
    return [
        f"Độ lệch pha điện áp và dòng điện đều ở mức thấp ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp và dòng điện đều ở mức cho phép ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp và dòng điện đo được đều thấp hơn mức chuẩn khuyến cáo ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp và dòng điện đáp ứng chuẩn cho phép ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp và dòng điện đều đáp ứng ngưỡng khuyến cáo ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp, dòng điện đều ở mức thấp ({unb_both_ok_vals}).",
    ]


# ── 2. SÓNG HÀI (THD / TDD) ─────────────────────────────────────────────────
def get_harm_both_ok_templates(harm_ok_vals: str) -> list[str]:
    """Mẫu câu khi cả sóng hài điện áp THD và sóng hài dòng điện TDD đều đạt chuẩn."""
    return [
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều ở mức cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đáp ứng mức cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện nằm trong ngưỡng cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều đạt tiêu chuẩn quy định ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện hiện đáp ứng ngưỡng quy định ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều thấp hơn ngưỡng cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều ở mức thấp ({harm_ok_vals}).",
    ]


# ── 3. NGUYÊN NHÂN THEO NHÓM PHỤ TẢI ĐẶC THÙ ────────────────────────────────

def get_cause_vfd_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Biến tần (VFD)."""
    return [
        f"Sóng hài dòng điện ở mức cao (TDDmax = {td_s}% > {lim_s}%) là đặc tính kỹ thuật đặc trưng của bộ chỉnh lưu phi tuyến trong biến tần.",
        f"Việc xuất hiện sóng hài dòng điện cao (TDDmax = {td_s}%) do hệ thống sử dụng bộ biến tần điều khiển tốc độ động cơ (sinh ra sóng hài bậc 5, 7).",
        f"Sóng hài dòng điện vượt mức cho phép (TDDmax = {td_s}% > {lim_s}%) xuất phát từ nguyên lý hoạt động phi tuyến của bộ biến tần.",
        f"Hiện tượng tổng biến dạng sóng hài dòng điện cao (TDDmax = {td_s}%) xuất phát từ đặc tính biến đổi tần số bằng bán dẫn công suất trong biến tần.",
    ]


def get_cause_vsd_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Máy nén khí VSD."""
    return [
        f"Nguyên nhân sóng hài dòng điện ở mức cao (TDDmax = {td_s}% > {lim_s}%) xuất phát từ bộ biến tần VSD tích hợp trong máy nén khí.",
        f"Tổng biến dạng sóng hài dòng điện vượt ngưỡng (TDDmax = {td_s}%) do đặc tính đóng ngắt phi tuyến của bộ điều khiển VSD máy nén.",
        f"Mặc dù tối ưu lượng khí nén và tiết kiệm điện năng, khối biến tần VSD của máy nén khí sinh ra sóng hài dòng điện lớn (TDDmax = {td_s}% > {lim_s}%).",
        f"Sóng hài dòng điện tăng cao (TDDmax = {td_s}%) là đặc tính kỹ thuật phổ biến ở các hệ thống máy nén khí sử dụng biến tần VSD.",
        f"Việc xuất hiện thành phần sóng hài dòng điện cao (TDDmax = {td_s}% > {lim_s}%) xuất phát từ các linh kiện bán dẫn công suất trong mạch VSD.",
    ]


def get_cause_servo_both_templates(di_s: str, td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân vừa lệch pha vừa sóng hài cao cho nhóm Máy may Servo."""
    return [
        f"Độ lệch pha dòng điện ở mức cao (ΔI = {di_s}% > 10,0%) do phân bổ các tuyến máy may 1 pha giữa các pha chưa đồng đều, kết hợp với các bộ điều khiển servo phát sinh sóng hài dòng lớn (TDDmax = {td_s}% > {lim_s}%).",
        f"Mất cân bằng dòng giữa các pha (ΔI = {di_s}%) và sóng hài dòng điện cao (TDDmax = {td_s}%) xuất phát từ đặc tính đóng ngắt không đồng bộ của các động cơ servo trên chuyền.",
    ]


def get_cause_servo_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho nhóm Máy may Servo."""
    return [
        f"Độ lệch pha dòng điện ở mức cao (ΔI = {di_s}% > 10,0%), nguyên nhân do phân bổ số lượng máy may giữa các pha chưa thật sự cân bằng hoặc thao tác may diễn ra không đồng bộ.",
        f"Mất cân bằng dòng điện giữa các pha (ΔI = {di_s}%) xuất phát từ việc bố trí phụ tải máy may đơn pha trên các nhánh chưa đồng đều.",
    ]


def get_cause_servo_harm_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Máy may Servo."""
    return [
        f"Các bộ điều khiển động cơ servo (tải phi tuyến) phát sinh sóng hài dòng điện cao (TDDmax = {td_s}% > {lim_s}%).",
        "Các khối nguồn và biến tần nhỏ trong máy may servo đóng ngắt liên tục là nguyên nhân tạo ra sóng hài dòng điện lớn.",
    ]


def get_cause_lighting_both_templates(di_s: str, td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân vừa lệch pha vừa sóng hài cao cho nhóm Hệ thống chiếu sáng."""
    return [
        f"Tổng biến dạng sóng hài dòng điện ở mức cao (TDDmax = {td_s}% > {lim_s}%) do đặc tính của bộ nguồn xung (LED driver) trong hệ thống chiếu sáng, đồng thời độ lệch pha dòng điện ở mức cao (ΔI = {di_s}% > 10,0%) do phân bổ phụ tải giữa các tuyến không đều.",
        f"Hệ thống chiếu sáng LED/nguồn điện tử tích tụ lượng sóng hài dòng điện lớn (TDDmax = {td_s}%, đặc biệt sóng hài bậc 3) và gây mất cân bằng dòng giữa các pha (ΔI = {di_s}%).",
    ]


def get_cause_lighting_harm_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Hệ thống chiếu sáng."""
    return [
        f"Tổng biến dạng sóng hài dòng điện ở mức cao (TDDmax = {td_s}% > {lim_s}%), xuất phát từ đặc tính của bộ nguồn xung (LED driver/ballast điện tử) sử dụng trong hệ thống chiếu sáng.",
        f"Hệ thống chiếu sáng LED là loại tải phi tuyến điển hình, tích tụ lượng sóng hài dòng điện lớn (TDDmax = {td_s}%, đặc biệt các thành phần sóng hài bậc lẻ).",
    ]


def get_cause_lighting_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho nhóm Hệ thống chiếu sáng."""
    return [
        f"Độ lệch pha dòng điện ở mức cao (ΔI = {di_s}% > 10,0%) do phụ tải chiếu sáng phân bổ chưa đồng đều giữa các tầng hoặc các khu vực.",
        "Hiện tượng mất cân bằng dòng điện xuất phát từ việc đấu nối các nhánh đèn 1 pha chưa thật sự cân đối giữa 3 pha.",
    ]


def get_cause_mba_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho Máy biến áp (MBA)."""
    return [
        f"Độ lệch pha dòng điện tại máy biến áp ở mức cao (ΔI = {di_s}% > 10,0%), tạo ra dòng điện chạy trên dây trung tính MBA và giảm hiệu suất truyền tải.",
        f"Mất cân bằng dòng điện giữa các pha phía hạ áp máy biến áp (ΔI = {di_s}%) do phân bổ phụ tải hạ nguồn chưa đồng đều.",
    ]


def get_cause_inv_templates() -> list[str]:
    """Mẫu câu nguyên nhân sóng hài chung cho thiết bị có từ khóa biến tần."""
    return [
        "Nguyên nhân hình thành nên giá trị sóng hài cao xuất phát từ việc sử dụng biến tần.",
        "Sóng hài dòng điện cao là đặc tính kỹ thuật của thiết bị điều khiển bằng biến tần.",
        "Việc xuất hiện sóng hài cao xuất phát từ các hệ thống được điều khiển bằng biến tần.",
    ]


def get_cause_gen_harm_templates() -> list[str]:
    """Mẫu câu nguyên nhân sóng hài chung cho thiết bị phi tuyến."""
    return [
        "Nguyên nhân hình thành nên giá trị sóng hài cao xuất phát từ việc sử dụng các thiết bị phi tuyến trong hệ thống.",
        "Tổng biến dạng sóng hài dòng điện cao là đặc tính kỹ thuật của các bộ biến đổi công suất điện tử.",
    ]


# ── 4. MẪU CÂU CHO MÁY BIẾN ÁP (MBA) ────────────────────────────────────────

def get_load_mba_templates(load_pct_str: str) -> list[str]:
    """Mẫu câu tỷ lệ công suất tiêu thụ của MBA."""
    return [
        f"Công suất tiêu thụ của máy biến áp đạt {load_pct_str}% công suất thiết kế.",
        f"Công suất tiêu thụ tại máy biến áp ở mức {load_pct_str}% so với công suất định mức.",
        f"Tại thời điểm đo kiểm, máy biến áp vận hành ở mức {load_pct_str}% công suất thiết kế.",
    ]


def get_wave_mba_map(wave: str) -> dict[str, list[str]]:
    """Bản đồ các mẫu câu đặc tính đồ thị dòng điện cho MBA."""
    return {
        "ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm ổn định.",
            "Biểu đồ dòng điện tiêu thụ tại máy biến áp tương đối ổn định trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại máy biến áp tương đối ổn định.",
        ],
        "tương đối ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm tương đối ổn định.",
            "Đồ thị dòng điện đo được tại máy biến áp có sự điều chỉnh nhẹ.",
            "Biểu đồ dòng điện tiêu thụ tại máy biến áp tương đối ổn định và có sự điều chỉnh nhẹ.",
        ],
        "biến đổi theo chu kỳ load/unload": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm biến đổi theo chu kỳ Load/Unload.",
            "Đồ thị dòng điện đo được tại máy biến áp vận hành theo chế độ Load/Unload.",
        ],
    }


def get_mba_openings(name_mid: str, quality: str) -> list[str]:
    """Mẫu câu mở đầu chất lượng điện cho MBA."""
    return [
        f"Chất lượng điện đo tại {name_mid} ở mức {quality}",
        f"Dữ liệu đo kiểm cho thấy {name_mid} có chất lượng điện ở mức {quality}",
        f"Nhìn chung, nguồn điện cấp cho {name_mid} có chất lượng {quality}",
        f"Chất lượng dòng điện đo được tại {name_mid} ở mức {quality}",
        f"Kết quả đo kiểm cho thấy nguồn điện cấp cho {name_mid} ở mức {quality}",
        f"Qua đo kiểm, chất lượng điện tại {name_mid} ở mức {quality}",
    ]


def get_pf_mba_templates(pf_txt: str, abs_pf: float) -> list[str]:
    """Mẫu câu hệ số công suất cosφ cho MBA."""
    if abs_pf >= 0.9:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất đo được ở mức {pf_txt}",
            f"hệ số cosφ đo được ở mức {pf_txt}",
        ]
    elif abs_pf >= 0.8:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất của thiết bị ở mức {pf_txt}",
            f"hệ số cosφ hiện ở mức {pf_txt}",
        ]
    else:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất ở mức {pf_txt}",
        ]


def get_mba_closing_templates() -> list[str]:
    """Mẫu câu chốt dẫn bảng thông số cho MBA."""
    return [
        "Dưới đây là bảng tổng hợp thông số hoạt động của máy biến áp:",
        "Chất lượng dòng điện đo được tại máy biến áp được thể hiện chi tiết tại bảng sau:",
    ]


# ── 5. MẪU CÂU CHO THIẾT BỊ ĐO KIỂM THÔNG THƯỜNG (DEVICE / DEVICE4) ─────────

def get_volt_verdict_ok_templates() -> list[str]:
    """Cụm từ kết luận điện áp đạt tiêu chuẩn cho thiết bị."""
    return [
        "đạt tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
        "thuộc ngưỡng tiêu chuẩn điện áp (-5% ≤ δ ≤ 5%)",
        "nằm trong ngưỡng tiêu chuẩn dao động điện áp (-5% ≤ δ ≤ 5%)",
        "hiện nằm trong ngưỡng tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
    ]


def get_volt_verdict_bad_templates() -> list[str]:
    """Cụm từ kết luận điện áp vượt tiêu chuẩn cho thiết bị."""
    return [
        "vượt giới hạn cho phép (-5,0% ≤ δ ≤ 5,0%)",
        "chưa đáp ứng tiêu chuẩn điện áp (-5% ≤ δ ≤ 5%)",
        "nằm ngoài ngưỡng tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
    ]


def get_volt_templates(umin_s: str, umax_s: str, dlo_s: str, dhi_s: str, verdict: str) -> list[str]:
    """Mẫu câu điện áp và độ lệch chuẩn δU cho thiết bị."""
    return [
        f"Điện áp dao động từ {umin_s} ÷ {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%), {verdict}.",
        f"Điện áp đo được nằm trong khoảng {umin_s} - {umax_s} V với độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
        f"Điện áp nguồn cấp dao động từ {umin_s} ÷ {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%), {verdict}.",
        f"Thông số điện áp dao động từ {umin_s} - {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
    ]


def get_load_dev_templates(load_pct_dev: float, pct_s: str, p_str: str, pdm_str: str) -> list[str]:
    """Mẫu câu công suất tiêu thụ & % mang tải cho thiết bị ngoài MBA."""
    if load_pct_dev < 50.0:
        return [
            f"Công suất tiêu thụ đo được ở mức {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW), phụ tải vận hành ở mức tải nhẹ.",
            f"Tại thời điểm khảo sát, phụ tải vận hành với công suất bằng {pct_s}% công suất thiết kế (P = {p_str} kW so với Pđm = {pdm_str} kW).",
            f"Công suất tiêu thụ thực tế đạt khoảng {pct_s}% công suất định mức, tải vận hành tương đối nhẹ.",
            f"Phụ tải mang tải khoảng {pct_s}% so với công suất định mức.",
        ]
    elif load_pct_dev <= 90.0:
        return [
            f"Công suất tiêu thụ đo được ở mức {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW).",
            f"Tại thời điểm khảo sát, hệ thống vận hành với công suất bằng {pct_s}% công suất thiết kế, đáp ứng phù hợp nhu cầu phụ tải.",
            f"Công suất tiêu thụ thực tế đạt {pct_s}% công suất định mức (P = {p_str} kW so với Pđm = {pdm_str} kW).",
            f"Phụ tải vận hành ở mức tải hợp lý, đạt {pct_s}% công suất thiết kế.",
        ]
    elif load_pct_dev <= 100.0:
        return [
            f"Công suất tiêu thụ đạt {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW), phụ tải vận hành gần như đầy tải.",
            f"Tại thời điểm khảo sát, phụ tải mang tải ở mức cao, đạt {pct_s}% công suất thiết kế.",
            f"Công suất tiêu thụ thực tế đạt {pct_s}% công suất danh định, cần chú ý chế độ phát nóng khi vận hành liên tục.",
        ]
    else:
        return [
            f"Công suất tiêu thụ đạt {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW), phụ tải đang ở tình trạng quá tải.",
            f"Tại thời điểm khảo sát, hệ thống vận hành vượt công suất thiết kế ({pct_s}% Pđm), cần có giải pháp tiết giảm tải hoặc nâng công suất cấp nguồn.",
        ]


def get_device_openings(name_mid: str, quality: str) -> list[str]:
    """Mẫu câu mở đầu nhận xét chất lượng điện cho thiết bị."""
    return [
        f"Chất lượng điện cấp cho {name_mid} ở mức {quality}.",
        f"Dữ liệu đo kiểm cho thấy {name_mid} hoạt động với chất lượng điện ở mức {quality}.",
        f"Nhìn chung, nguồn điện cấp cho {name_mid} có chất lượng {quality}.",
        f"Chất lượng dòng điện đo được tại nguồn cấp cho {name_mid} ở mức {quality}.",
        f"Kết quả đo kiểm cho thấy chất lượng điện cấp cho {name_mid} ở mức {quality}.",
        f"Qua đo kiểm, chất lượng điện cấp cho {name_mid} ở mức {quality}.",
        f"Tại thời điểm khảo sát, {name_mid} vận hành với chất lượng điện ở mức {quality}.",
        f"Chất lượng điện đo tại {name_mid} ở mức {quality}.",
    ]


def get_pf_dev_templates(pf_txt: str, abs_pf: float) -> list[str]:
    """Mẫu câu hệ số công suất cosφ cho thiết bị."""
    if abs_pf >= 0.9:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất của thiết bị ở mức {pf_txt}.",
            f"Hệ số công suất đo được ở mức {pf_txt}.",
            f"Giá trị hệ số công suất đo được tại thời điểm khảo sát ở mức {pf_txt}.",
        ]
    elif abs_pf >= 0.8:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất của thiết bị ở mức {pf_txt}.",
            f"Hệ số cosφ đo được có giá trị {pf_txt}.",
            f"Giá trị hệ số công suất đo được tại thời điểm khảo sát ở mức {pf_txt}.",
        ]
    else:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất ở mức {pf_txt}.",
        ]


def get_wave_dev_by_category(cat: str, wave: str) -> list[str]:
    """Mẫu câu đặc tính đồ thị dòng điện theo nhóm thiết bị (VSD, Servo, Lighting, VFD, Thường)."""
    if cat == "vsd_compressor":
        return [
            "Biểu đồ dòng điện tiêu thụ biến đổi mượt mà theo áp suất khí nén nhờ bộ biến tần VSD điều chỉnh tốc độ động cơ.",
            "Máy nén khí VSD vận hành tự động điều chỉnh tốc độ motor theo nhu cầu sử dụng khí nén thực tế.",
            "Đồ thị dòng điện thể hiện đặc tính điều khiển biến tần VSD, giúp tối ưu điện năng tiêu thụ và tránh sụt áp khi khởi động.",
            "Biểu đồ dòng điện biến đổi theo phụ tải điều khiển qua bộ biến tần VSD của máy nén khí.",
        ]
    elif cat == "servo_sewing":
        return [
            "Biểu đồ dòng điện tiêu thụ dao động liên tục với tần suất cao, phản ánh đúng đặc tính vận hành nhấp nhô theo từng nhịp may của công nhân.",
            "Đồ thị dòng điện biến động liên tục theo nhịp thao tác trên chuyền may, thể hiện đặc tính tải nhấp nhô của động cơ servo.",
            "Dòng điện tiêu thụ biến đổi liên tục với biên độ dao động nhanh theo từng công đoạn may sản phẩm.",
            "Biểu đồ dòng điện cấp cho chuyền may thể hiện đặc tính tải servo biến đổi liên tục theo nhịp sản xuất.",
        ]
    elif cat == "lighting":
        return [
            "Biểu đồ dòng điện tiêu thụ của hệ thống chiếu sáng duy trì rất ổn định trong suốt thời gian khảo sát.",
            "Đồ thị dòng điện tủ chiếu sáng có tính ổn định cao, phản ánh thời gian bật/tắt đèn cố định của tòa nhà/bệnh viện.",
            "Dòng điện cấp cho hệ thống đèn chiếu sáng vận hành ổn định theo thời gian hoạt động của khu vực.",
            "Biểu đồ dòng điện của hệ thống chiếu sáng duy trì mức ổn định cao trong giờ vận hành.",
        ]
    elif cat == "vfd_inverter":
        return [
            "Biểu đồ dòng điện tiêu thụ biến đổi mượt mà theo tần số điều khiển của biến tần.",
            "Đồ thị dòng điện đo được điều chỉnh linh hoạt theo tốc độ động cơ qua bộ biến tần.",
            "Biểu đồ dòng điện phản ánh quá trình điều khiển tần số dòng điện cấp cho động cơ.",
            f"Biểu đồ dòng điện tiêu thụ {wave} theo tần số biến tần điều khiển.",
        ]

    _wave_dev_map: dict[str, list[str]] = {
        "ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị ổn định trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại nguồn cấp tương đối ổn định.",
            "Biểu đồ dòng điện cấp cho thiết bị duy trì ổn định trong suốt quá trình khảo sát.",
            "Biểu đồ dòng điện của thiết bị thể hiện tính ổn định trong vận hành.",
        ],
        "tương đối ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị tương đối ổn định trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại thiết bị ít có sự biến động.",
            "Biểu đồ dòng điện cấp cho thiết bị tương đối ổn định với sự điều chỉnh nhẹ.",
        ],
        "biến đổi liên tục theo tải": [
            f"Biểu đồ dòng điện tiêu thụ {wave} trong thời gian đo kiểm.",
            "Đồ thị dòng điện có sự điều chỉnh theo hoạt động sản xuất.",
            "Biểu đồ dòng điện cấp cho thiết bị có sự biến động theo tình hình vận hành.",
        ],
        "biến đổi liên tục": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị biến đổi liên tục trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại thiết bị có sự biến đổi liên tục.",
            f"Biểu đồ dòng điện tiêu thụ {wave} trong thời gian đo kiểm.",
        ],
        "biến đổi liên tục với biên độ nhỏ": [
            "Biểu đồ dòng điện tiêu thụ của thiết bị biến đổi liên tục với biên độ nhỏ.",
            "Đồ thị dòng điện đo được tại thiết bị biến đổi liên tục với biên độ không lớn.",
            f"Biểu đồ dòng điện tiêu thụ {wave} trong thời gian đo kiểm.",
        ],
        "biến đổi theo chu kỳ load/unload": [
            "Biểu đồ dòng điện tiêu thụ cho thấy thiết bị vận hành theo chế độ Load/Unload.",
            "Đồ thị dòng điện đo được biến đổi theo chu kỳ Load/Unload.",
            "Thiết bị hoạt động theo chế độ Load/Unload, đồ thị dòng điện thể hiện rõ chu kỳ đóng/ngắt tải.",
        ],
    }

    _wave_key_dev = wave.lower().strip()
    if _wave_key_dev in _wave_dev_map:
        return _wave_dev_map[_wave_key_dev]
    return [f"Biểu đồ dòng điện tiêu thụ {wave} trong thời gian đo kiểm."]


def get_closing_dev_templates() -> list[str]:
    """Mẫu câu chốt đánh giá tốt cho thiết bị."""
    return [
        "Tổng quan, chất lượng điện cấp cho thiết bị ở mức tốt.",
        "Tổng quan, chất lượng dòng điện cấp cho thiết bị ở mức tốt.",
        "Nhìn chung, thiết bị vận hành ổn định với chất lượng điện cấp ở mức tốt.",
        "Tổng quan, hệ thống hoạt động ổn định và chất lượng điện ở mức tốt.",
        "Kết quả đo kiểm cho thấy chất lượng điện cấp cho thiết bị ở mức tốt.",
    ]
