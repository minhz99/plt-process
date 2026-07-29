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
        f"Độ lệch pha điện áp và dòng điện đáp ứng chuẩn cho phép ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp và dòng điện đều đáp ứng ngưỡng khuyến cáo ({unb_both_ok_vals}).",
        f"Độ lệch pha điện áp, dòng điện đều ở mức thấp ({unb_both_ok_vals}).",
        f"Mức độ mất cân bằng điện áp và dòng điện giữa các pha đều nằm trong phạm vi cho phép ({unb_both_ok_vals}).",
        f"Hệ thống duy trì sự cân bằng tốt giữa các pha, độ lệch điện áp và dòng điện đều thấp ({unb_both_ok_vals}).",
        f"Kết quả đo kiểm cho thấy độ lệch pha điện áp và dòng điện đều nằm trong giới hạn cho phép ({unb_both_ok_vals}).",
        f"Mức độ mất cân bằng pha của cả điện áp và dòng điện đều được kiểm soát tốt ({unb_both_ok_vals}).",
        f"Hệ thống duy trì độ đối xứng pha tốt, độ lệch pha điện áp và dòng điện đều ở mức thấp ({unb_both_ok_vals}).",
    ]


# ── 2. SÓNG HÀI (THD / TDD) ─────────────────────────────────────────────────
def get_harm_both_ok_templates(harm_ok_vals: str) -> list[str]:
    """Mẫu câu khi cả sóng hài điện áp THD và sóng hài dòng điện TDD đều đạt chuẩn."""
    return [
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều ở mức cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đáp ứng mức cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện nằm trong ngưỡng cho phép ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều đạt tiêu chuẩn quy định ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều đáp ứng ngưỡng quy định ({harm_ok_vals}).",
        f"Tổng biến dạng sóng hài điện áp và dòng điện đều ở mức thấp ({harm_ok_vals}).",
        f"Chất lượng sóng điện áp và dòng điện được đảm bảo tốt, các thành phần sóng hài nằm trong giới hạn ({harm_ok_vals}).",
        f"Mức độ biến dạng sóng hài của cả điện áp lẫn dòng điện đều kiểm soát tốt và đáp ứng tiêu chuẩn ({harm_ok_vals}).",
        f"Kết quả đo kiểm ghi nhận sóng hài điện áp và dòng điện đều ở mức an toàn ({harm_ok_vals}).",
        f"Mức độ biến dạng sóng hài điện áp và dòng điện được kiểm soát tốt ({harm_ok_vals}).",
    ]


# ── 3. NGUYÊN NHÂN THEO NHÓM PHỤ TẢI ĐẶC THÙ ────────────────────────────────

def get_cause_vfd_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Biến tần (VFD)."""
    return [
        "Sóng hài dòng điện ở mức cao là đặc tính kỹ thuật đặc trưng của bộ chỉnh lưu phi tuyến trong biến tần.",
        "Sóng hài dòng điện tăng cao do hệ thống sử dụng bộ biến tần điều khiển tốc độ động cơ.",
        "Sóng hài dòng điện vượt mức cho phép xuất phát từ nguyên lý hoạt động phi tuyến của bộ biến tần.",
        "Hiện tượng biến dạng sóng hài dòng điện xuất phát từ đặc tính đóng ngắt bằng bán dẫn công suất trong biến tần.",
        "Biến tần sử dụng mạch chỉnh lưu 6 xung tạo ra các thành phần sóng hài làm dòng điện biến dạng.",
        "Quá trình biến đổi tần số bằng linh kiện bán dẫn công suất tạo ra các sóng hài dòng điện đặc trưng.",
    ]


def get_cause_vsd_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Máy nén khí VSD."""
    return [
        "Nguyên nhân sóng hài dòng điện xuất phát từ bộ biến tần VSD tích hợp trong máy nén khí.",
        "Biến dạng sóng hài dòng điện do đặc tính đóng ngắt phi tuyến của bộ điều khiển VSD máy nén.",
        "Khối biến tần VSD của máy nén khí sinh ra sóng hài dòng điện trong quá trình điều chỉnh tốc độ motor.",
        "Sóng hài dòng điện tăng cao là đặc tính kỹ thuật phổ biến ở các hệ thống máy nén khí sử dụng biến tần VSD.",
        "Bộ biến tần VSD tích hợp trong máy nén khí, dù mang lại hiệu quả năng lượng cao, đồng thời tạo ra sóng hài dòng điện do bản chất chuyển mạch tần số.",
        "Đặc tính vận hành của máy nén khí biến tần, khi bộ điều khiển VSD điều chỉnh liên tục tốc độ động cơ là nguyên nhân chính phát sinh sóng hài dòng điện.",
    ]


def get_cause_servo_both_templates(di_s: str, td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân vừa lệch pha vừa sóng hài cao cho nhóm Máy may Servo."""
    return [
        "Độ lệch pha dòng điện và sóng hài tăng cao do phân bổ các tải 1 pha chưa đều, kết hợp với các bộ điều khiển servo phát sinh sóng hài.",
        "Mất cân bằng dòng giữa các pha và sóng hài dòng điện xuất phát từ đặc tính đóng ngắt không đồng bộ của các động cơ servo trong thiết bị.",
        "Sự kết hợp giữa phụ tải đơn pha phân bổ chưa cân đối và đặc tính bán dẫn phi tuyến của bộ điều khiển servo tạo ra hai vấn đề chất lượng điện.",
        "Nguyên nhân đồng thời gây lệch pha và sóng hài tăng cao là do số lượng lớn động cơ servo hoạt động độc lập, không đồng bộ về thời điểm khởi động và tải.",
    ]


def get_cause_servo_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho nhóm Máy may Servo."""
    return [
        "Độ lệch pha dòng điện do phân bổ số lượng thiết bị giữa các pha chưa thật sự cân bằng hoặc thao tác sử dụng thiết bị diễn ra không đồng bộ.",
        "Mất cân bằng dòng điện giữa các pha xuất phát từ việc bố trí phụ tải đơn pha trên các nhánh chưa đồng đều.",
        "Hiện tượng mất cân bằng pha dòng điện là hệ quả của việc các thiết bị 1 pha được phân bổ không đều giữa 3 pha.",
        "Nguyên nhân lệch pha dòng điện xuất phát từ việc các thiết bị đơn pha phân bổ chưa cân đối trên 3 pha lưới điện.",
        "Độ lệch pha dòng điện chủ yếu do số lượng thiết bị hoạt động không đều giữa các pha tại thời điểm khảo sát.",
    ]


def get_cause_servo_harm_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Máy may Servo."""
    return [
        "Các bộ điều khiển động cơ servo trong thiết bị phát sinh sóng hài dòng điện đặc trưng.",
        "Các khối nguồn và biến tần nhỏ trong thiết bị đóng ngắt liên tục là nguyên nhân tạo ra sóng hài dòng điện.",
        "Bộ điều khiển servo trong thiết bị là loại tải phi tuyến điển hình, có mạch chỉnh lưu tích hợp tạo ra các sóng hài dòng điện bậc lẻ.",
        "Hàng loạt động cơ servo vận hành đồng thời với tần suất đóng ngắt cao tích lũy sóng hài dòng điện lên lưới điện cấp cho thiết bị.",
        "Đặc tính phi tuyến của bộ nguồn xung và mạch điều khiển servo là nguồn phát sinh chính gây ra mức sóng hài dòng điện.",
    ]


def get_cause_lighting_both_templates(di_s: str, td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân vừa lệch pha vừa sóng hài cao cho nhóm Hệ thống chiếu sáng."""
    return [
        "Sóng hài dòng điện xuất phát từ bộ nguồn xung (LED driver) chiếu sáng, đồng thời độ lệch pha dòng điện do phân bổ phụ tải không đều giữa các tuyến.",
        "Hệ thống chiếu sáng LED tích tụ lượng sóng hài dòng điện, đặc biệt là sóng hài bậc 3, và gây mất cân bằng dòng giữa các pha.",
        "LED driver là tải phi tuyến phát sinh sóng hài dòng điện bậc 3, 5, 7, kết hợp với việc phân bổ phụ tải chiếu sáng đơn pha chưa cân đối.",
    ]


def get_cause_lighting_harm_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Hệ thống chiếu sáng."""
    return [
        "Tổng biến dạng sóng hài dòng điện xuất phát từ đặc tính của bộ nguồn xung như LED driver hoặc ballast điện tử trong hệ thống chiếu sáng.",
        "Hệ thống chiếu sáng LED là loại tải phi tuyến điển hình, tích tụ lượng sóng hài dòng điện bậc lẻ.",
        "LED driver sử dụng mạch chỉnh lưu tích hợp tụ lọc, tạo ra dòng điện có dạng xung nhọn với hàm lượng sóng hài dòng điện bậc 3, 5, 7 cao.",
        "Nguồn điện tử như LED driver hoặc ballast điện tử trong hệ thống chiếu sáng vốn là các bộ nguồn xung phi tuyến sinh ra sóng hài dòng điện.",
        "Đặc tính phi tuyến vốn có của mạch chỉnh lưu trong LED driver là nguồn gốc chính gây nên tổng biến dạng sóng hài dòng điện.",
    ]


def get_cause_lighting_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho nhóm Hệ thống chiếu sáng."""
    return [
        "Độ lệch pha dòng điện do phụ tải chiếu sáng phân bổ chưa đồng đều giữa các tầng hoặc các khu vực.",
        "Hiện tượng mất cân bằng dòng điện xuất phát từ việc đấu nối các nhánh đèn 1 pha chưa thật sự cân đối giữa 3 pha.",
        "Mất cân bằng dòng điện giữa các pha do các nhánh đèn chiếu sáng đơn pha được phân bổ không đều theo khu vực hoặc theo tầng.",
        "Nguyên nhân lệch pha dòng điện do các hồi dây chiếu sáng đơn pha phân bổ không đồng đều trên 3 pha.",
    ]


def get_cause_mba_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho Máy biến áp (MBA)."""
    return [
        "Độ lệch pha dòng điện tại máy biến áp ở mức cao, tạo ra dòng điện chạy trên dây trung tính MBA và giảm hiệu suất truyền tải.",
        "Mất cân bằng dòng điện giữa các pha phía hạ áp máy biến áp do phân bổ phụ tải hạ nguồn chưa đồng đều.",
        "Phụ tải phía hạ áp máy biến áp phân bổ chưa cân bằng giữa các pha, dẫn đến mất cân bằng dòng điện và gây phát nóng cuộn dây.",
        "Sự chênh lệch phụ tải giữa các pha hạ áp của máy biến áp là nguyên nhân chính gây ra mất cân bằng dòng điện.",
    ]


def get_cause_inv_templates() -> list[str]:
    """Mẫu câu nguyên nhân sóng hài chung cho thiết bị có từ khóa biến tần."""
    return [
        "Nguyên nhân hình thành sóng hài cao xuất phát từ việc sử dụng biến tần.",
        "Sóng hài dòng điện cao là đặc tính kỹ thuật của thiết bị điều khiển bằng biến tần.",
        "Quá trình chuyển mạch tần số cao của biến tần là nguồn gốc chính tạo ra các thành phần sóng hài trong dòng điện.",
        "Sóng hài dòng điện là hệ quả từ công nghệ điều khiển biến tần dựa trên linh kiện bán dẫn công suất.",
    ]


def get_cause_gen_harm_templates() -> list[str]:
    """Mẫu câu nguyên nhân sóng hài chung cho thiết bị phi tuyến."""
    return [
        "Nguyên nhân sóng hài cao xuất phát từ việc sử dụng các thiết bị phi tuyến trong hệ thống.",
        "Tổng biến dạng sóng hài dòng điện cao là đặc tính kỹ thuật của các bộ biến đổi công suất điện tử.",
        "Các thiết bị điện tử công suất như nguồn xung, bộ chỉnh lưu hay biến tần là tải phi tuyến điển hình, sinh ra sóng hài dòng điện trên lưới điện.",
    ]


def get_cause_chiller_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho hệ thống Chiller/HVAC."""
    return [
        "Sóng hài dòng điện xuất phát từ các bộ biến tần điều tốc tích hợp trong cụm máy nén Chiller và bơm nước lạnh.",
        "Mức độ sóng hài dòng điện do đặc tính biến đổi tần số liên tục của biến tần Chiller nhằm duy trì nhiệt độ nước lạnh ổn định.",
        "Khối chỉnh lưu bán dẫn trong biến tần điều khiển cụm Chiller/HVAC là nguồn phát sinh chính gây ra sóng hài dòng điện.",
    ]


def get_cause_ups_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho hệ thống UPS / Phòng Server / Data Center."""
    return [
        "Sóng hài dòng điện xuất phát từ bộ chỉnh lưu đầu vào của hệ thống UPS và mật độ cao các bộ nguồn chuyển mạch SMPS trong máy chủ.",
        "Sóng hài dòng điện là đặc tính kỹ thuật phổ biến ở các hạ tầng trung tâm dữ liệu, tạo ra bởi khối bộ đổi điện của hệ thống lưu điện UPS.",
        "Các bộ chỉnh lưu trong hệ thống UPS công suất lớn tích tụ lượng sóng hài dòng điện trên tuyến cấp nguồn.",
    ]


def get_cause_solar_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho hệ thống Điện mặt trời (Solar PV Inverter)."""
    return [
        "Sóng hài dòng điện do đặc tính đóng ngắt tần số cao của bộ Inverter hòa lưới, đặc biệt khi hệ thống vận hành ở dải công suất phát nhẹ.",
        "Sóng hài dòng điện xuất phát từ quá trình biến đổi điện một chiều (DC) từ pin mặt trời sang điện xoay chiều (AC) của Inverter hòa lưới.",
        "Đặc tính phi tuyến của mạch cầu biến tần hòa lưới Điện mặt trời là nguyên nhân chính gây ra sóng hài dòng điện.",
    ]


def get_cause_welding_both_templates(di_s: str, td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân vừa lệch pha vừa sóng hài cao cho nhóm Máy hàn / Lò công nghiệp."""
    return [
        "Độ lệch pha dòng điện do phân bổ phụ tải máy hàn/lò đơn pha không đều giữa các pha, kết hợp với mạch chỉnh lưu phi tuyến phát sinh sóng hài.",
        "Sự kết hợp giữa phụ tải xung kích đơn pha đấu nối lệch pha và đặc tính đóng ngắt bán dẫn của bộ nguồn hàn gây ra đồng thời hai vấn đề chất lượng điện.",
    ]


def get_cause_welding_unb_templates(di_s: str) -> list[str]:
    """Mẫu câu nguyên nhân lệch pha cho nhóm Máy hàn / Lò công nghiệp."""
    return [
        "Độ lệch pha dòng điện do phụ tải máy hàn/lò điện đơn pha phân bổ chưa thật sự cân bằng giữa các pha cấp nguồn.",
        "Hiện tượng mất cân bằng dòng điện xuất phát từ đặc tính vận hành ngắn hạn, đóng ngắt gián đoạn không đồng bộ của các máy hàn trên lưới 3 pha.",
    ]


def get_cause_welding_harm_templates(td_s: str, lim_s: str) -> list[str]:
    """Mẫu câu nguyên nhân sóng hài cho nhóm Máy hàn / Lò công nghiệp."""
    return [
        "Bộ nguồn chỉnh lưu inverter trong máy hàn/lò phát sinh sóng hài dòng điện ở mức cao.",
        "Đặc tính đóng ngắt dòng điện lớn với chu kỳ ngắn của máy hàn inverter là nguồn gốc chính tích tụ sóng hài dòng điện.",
    ]



# ── 4. MẪU CÂU CHO MÁY BIẾN ÁP (MBA) ────────────────────────────────────────

def get_load_mba_templates(load_pct_str: str) -> list[str]:
    """Mẫu câu tỷ lệ công suất tiêu thụ của MBA."""
    return [
        f"Công suất tiêu thụ của máy biến áp đạt {load_pct_str}% công suất thiết kế.",
        f"Công suất tiêu thụ tại máy biến áp ở mức {load_pct_str}% so với công suất định mức.",
        f"Tại thời điểm đo kiểm, máy biến áp vận hành ở mức {load_pct_str}% công suất thiết kế.",
        f"Hệ số mang tải của máy biến áp đạt {load_pct_str}% so với công suất danh định.",
        f"Mức độ phụ tải tại thời điểm khảo sát cho thấy máy biến áp vận hành ở {load_pct_str}% công suất định mức.",
        f"Mức mang tải của máy biến áp đạt {load_pct_str}% so với công suất định mức.",
        f"Kết quả khảo sát cho thấy máy biến áp đang vận hành với {load_pct_str}% công suất thiết kế.",
    ]


def get_wave_mba_map(wave: str) -> dict[str, list[str]]:
    """Bản đồ các mẫu câu đặc tính đồ thị dòng điện cho MBA."""
    mba_map = {
        "ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm ổn định.",
            "Biểu đồ dòng điện tiêu thụ tại máy biến áp tương đối ổn định trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại máy biến áp tương đối ổn định.",
            "Dòng điện tải phía hạ áp máy biến áp duy trì ổn định trong suốt thời gian khảo sát.",
            "Đồ thị dòng điện tại máy biến áp cho thấy hệ thống vận hành ổn định, không có đột biến bất thường.",
            "Biểu đồ dòng điện tại máy biến áp không có biến động đáng kể trong suốt quá trình khảo sát.",
        ],
        "tương đối ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm tương đối ổn định.",
            "Đồ thị dòng điện đo được tại máy biến áp có sự điều chỉnh nhẹ.",
            "Biểu đồ dòng điện tiêu thụ tại máy biến áp tương đối ổn định và có sự điều chỉnh nhẹ.",
            "Dòng điện tải tại máy biến áp tương đối đồng đều với biên độ dao động không đáng kể.",
            "Đồ thị dòng điện vận hành tương đối ổn định, phản ánh chu kỳ sản xuất đều đặn của nhà máy.",
            "Đồ thị dòng điện tại máy biến áp dao động nhẹ theo nhu cầu phụ tải.",
        ],
        "ổn định nhưng có sự biến đổi trong quá trình đo": [
            "Biểu đồ dòng điện tiêu thụ tại máy biến áp duy trì mức ổn định, tuy nhiên ghi nhận sự biến đổi nhẹ tại một số thời điểm trong quá trình đo kiểm.",
            "Đồ thị dòng điện phía hạ áp máy biến áp thể hiện xu hướng ổn định, kèm theo các đợt điều chỉnh tải ngắn theo tiến trình sản xuất.",
            "Dòng điện tải máy biến áp vận hành ổn định, nhưng có sự biến đổi theo nhu cầu phụ tải tại một số giai đoạn khảo sát.",
            "Biểu đồ dòng điện của máy biến áp tương đối ổn định với các khoảng tăng/giảm nhẹ tùy theo chu kỳ vận hành của nhà máy.",
        ],
        "dao động liên tục quanh ngưỡng nhất định": [
            "Biểu đồ dòng điện tiêu thụ phía hạ áp máy biến áp dao động liên tục quanh ngưỡng định vị trong suốt thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại máy biến áp dao động đều đặn xung quanh mức tải trung bình cố định.",
            "Dòng điện tải máy biến áp biến thiên liên tục quanh một ngưỡng xác định, phản ánh phản hồi tự động của hệ thống phụ tải.",
        ],
        "biến đổi theo chu kỳ load/unload": [
            "Biểu đồ dòng điện tiêu thụ tại thời điểm đo kiểm biến đổi theo chu kỳ Load/Unload.",
            "Đồ thị dòng điện đo được tại máy biến áp vận hành theo chế độ Load/Unload.",
            "Biểu đồ dòng điện tại máy biến áp thể hiện đặc tính chu kỳ Load/Unload của tải máy nén khí.",
            "Dòng điện tiêu thụ tại máy biến áp dao động theo chu kỳ nạp/xả khí nén (Load/Unload) của nhóm phụ tải máy nén.",
            "Biểu đồ dòng điện thể hiện rõ chu kỳ đóng/ngắt tải phía hạ áp máy biến áp.",
        ],
    }
    mba_map["ổn định nhưng có biến đổi"] = mba_map["ổn định nhưng có sự biến đổi trong quá trình đo"]
    mba_map["dao động quanh ngưỡng"] = mba_map["dao động liên tục quanh ngưỡng nhất định"]
    w_key = wave.lower().strip()
    if w_key in mba_map:
        return mba_map
    return mba_map


def get_mba_openings(name_mid: str, quality: str) -> list[str]:
    """Mẫu câu mở đầu chất lượng điện cho MBA."""
    return [
        f"Chất lượng điện đo tại {name_mid} ở mức {quality}",
        f"Dữ liệu đo kiểm cho thấy {name_mid} có chất lượng điện ở mức {quality}",
        f"Nhìn chung, nguồn điện cấp cho {name_mid} có chất lượng {quality}",
        f"Chất lượng dòng điện đo được tại {name_mid} ở mức {quality}",
        f"Kết quả đo kiểm cho thấy nguồn điện cấp cho {name_mid} ở mức {quality}",
        f"Tổng hợp kết quả đo kiểm tại {name_mid} cho thấy chất lượng điện đạt mức {quality}",
    ]


def get_pf_mba_templates(pf_txt: str, abs_pf: float) -> list[str]:
    """Mẫu câu hệ số công suất cosφ cho MBA."""
    if abs_pf >= 0.9:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất đo được ở mức {pf_txt}",
            f"hệ số cosφ đo được ở mức {pf_txt}",
            f"hệ số công suất cosφ ghi nhận ở mức {pf_txt}",
            f"hệ số công suất đáp ứng yêu cầu ở mức {pf_txt}",
            f"giá trị hệ số công suất tại thời điểm khảo sát ở mức {pf_txt}",
        ]
    elif abs_pf >= 0.8:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất của thiết bị ở mức {pf_txt}",
            f"hệ số cosφ hiện ở mức {pf_txt}",
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất đo được ở mức {pf_txt}",
        ]
    else:
        return [
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất ở mức {pf_txt}",
            f"hệ số công suất cosφ ở mức {pf_txt}",
            f"hệ số công suất cosφ duy trì ở mức {pf_txt}",
            f"hệ số công suất đo được ở mức {pf_txt}",
        ]


def get_mba_closing_templates() -> list[str]:
    """Mẫu câu chốt dẫn bảng thông số cho MBA."""
    return [
        "Dưới đây là bảng tổng hợp thông số hoạt động của máy biến áp:",
        "Chi tiết các thông số đo đạc máy biến áp được tổng hợp trong bảng bên dưới:",
        "Bảng tổng hợp dưới đây thể hiện các giá trị điện áp, dòng điện và công suất đo kiểm được của MBA:",
    ]


# ── 5. MẪU CÂU CHO THIẾT BỊ ĐO KIỂM THÔNG THƯỜNG (DEVICE / DEVICE4) ─────────

def get_volt_verdict_ok_templates() -> list[str]:
    """Cụm từ kết luận điện áp đạt tiêu chuẩn cho thiết bị."""
    return [
        "đạt tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
        "thuộc ngưỡng tiêu chuẩn điện áp (-5% ≤ δ ≤ 5%)",
        "nằm trong ngưỡng tiêu chuẩn dao động điện áp (-5% ≤ δ ≤ 5%)",
        "hiện nằm trong ngưỡng tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
        "đáp ứng yêu cầu chất lượng điện áp theo tiêu chuẩn (-5% ≤ δ ≤ 5%)",
        "kiểm soát tốt trong phạm vi biến động cho phép (-5,0% ≤ δ ≤ 5,0%)",
        "phù hợp với quy định về dao động điện áp (-5% ≤ δ ≤ 5%)",
        "đáp ứng đầy đủ ngưỡng tiêu chuẩn cho phép (-5,0% ≤ δ ≤ 5,0%)",
    ]


def get_volt_verdict_bad_templates() -> list[str]:
    """Cụm từ kết luận điện áp vượt tiêu chuẩn cho thiết bị."""
    return [
        "chưa đáp ứng tiêu chuẩn điện áp (-5% ≤ δ ≤ 5%)",
        "nằm ngoài ngưỡng tiêu chuẩn (-5,0% ≤ δ ≤ 5,0%)",
        "chưa đáp ứng yêu cầu chất lượng điện áp (vượt giới hạn ±5,0%)",
        "dao động vượt ngưỡng tiêu chuẩn điện áp (-5% ≤ δ ≤ 5%)",
        "vượt ra ngoài dải khuyến cáo về dao động điện áp (-5% ≤ δ ≤ 5%)",
        "chưa phù hợp với ngưỡng tiêu chuẩn quy định (-5,0% ≤ δ ≤ 5,0%)",
    ]


def get_volt_templates(umin_s: str, umax_s: str, dlo_s: str, dhi_s: str, verdict: str) -> list[str]:
    """Mẫu câu điện áp và độ lệch chuẩn δU cho thiết bị."""
    return [
        f"Điện áp dao động từ {umin_s} ÷ {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%), {verdict}.",
        f"Điện áp đo được nằm trong khoảng {umin_s} - {umax_s} V với độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
        f"Điện áp nguồn cấp dao động từ {umin_s} ÷ {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%), {verdict}.",
        f"Thông số điện áp dao động từ {umin_s} - {umax_s} V, độ lệch chuẩn của điện áp δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
        f"Điện áp cấp nguồn ghi nhận trong khoảng {umin_s} ÷ {umax_s} V, δU = {dlo_s}% ÷ {dhi_s}%, {verdict}.",
        f"Kết quả đo cho thấy điện áp biến động trong khoảng {umin_s} – {umax_s} V (δU = {dlo_s}% ÷ {dhi_s}%), {verdict}.",
        f"Kết quả đo kiểm ghi nhận điện áp trong khoảng {umin_s} ÷ {umax_s} V, với độ lệch chuẩn δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
        f"Điện áp cấp cho thiết bị dao động trong khoảng {umin_s} - {umax_s} V, độ lệch chuẩn δU (= {dlo_s}% ÷ {dhi_s}%) {verdict}.",
    ]


def get_inst_power_val_templates(p_str: str) -> list[str]:
    """Mẫu câu thông báo công suất tức thời khi ghi nhận giá trị P (kW)."""
    return [
        f"Công suất tức thời đạt mức {p_str} kW.",
        f"Công suất tiêu thụ của thiết bị đạt {p_str} kW tại thời điểm khảo sát.",
        f"Tại thời điểm khảo sát, công suất tiêu thụ tức thời của thiết bị ở mức {p_str} kW.",
        f"Kết quả đo kiểm ghi nhận công suất tức thời đạt mức {p_str} kW.",
    ]


def get_load_dev_templates(load_pct_dev: float, pct_s: str, p_str: str, pdm_str: str) -> list[str]:
    """Mẫu câu công suất tiêu thụ & % mang tải cho thiết bị ngoài MBA."""
    if load_pct_dev < 50.0:
        return [
            f"Công suất tức thời đạt mức {p_str} kW, đạt {pct_s}% công suất định mức Pđm = {pdm_str} kW, phụ tải vận hành ở mức tải nhẹ.",
            f"Công suất tiêu thụ của thiết bị đạt {p_str} kW, tương đương {pct_s}% công suất thiết kế (Pđm = {pdm_str} kW).",
            f"Tại thời điểm khảo sát, công suất tức thời ghi nhận ở mức {p_str} kW, đạt khoảng {pct_s}% công suất định mức.",
            f"Phụ tải mang tải khoảng {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW).",
            f"Thiết bị vận hành với mức tải nhẹ, công suất tiêu thụ thực tế đạt {p_str} kW (bằng {pct_s}% Pđm = {pdm_str} kW).",
            f"Công suất tiêu thụ đo được ở mức {pct_s}% so với công suất định mức (P = {p_str} kW / Pđm = {pdm_str} kW).",
        ]
    elif load_pct_dev <= 90.0:
        return [
            f"Công suất tức thời đạt mức {p_str} kW (tương đương {pct_s}% công suất định mức Pđm = {pdm_str} kW).",
            f"Công suất tiêu thụ của thiết bị đạt {p_str} kW, đạt {pct_s}% công suất thiết kế.",
            f"Tại thời điểm khảo sát, công suất tiêu thụ thực tế đạt {p_str} kW (bằng {pct_s}% Pđm = {pdm_str} kW).",
            f"Phụ tải vận hành ở mức tải hợp lý, công suất tức thời đạt {p_str} kW ({pct_s}% Pđm).",
            f"Công suất tiêu thụ đạt {p_str} kW (tương đương {pct_s}% Pđm = {pdm_str} kW), thiết bị vận hành ổn định.",
        ]
    elif load_pct_dev <= 100.0:
        return [
            f"Công suất tức thời đạt mức {p_str} kW, tương đương {pct_s}% công suất định mức (Pđm = {pdm_str} kW), phụ tải vận hành gần đầy tải.",
            f"Công suất tiêu thụ của thiết bị đạt {p_str} kW, đạt {pct_s}% công suất thiết kế (Pđm = {pdm_str} kW).",
            f"Tại thời điểm khảo sát, công suất tiêu thụ thực tế đạt {p_str} kW, bằng {pct_s}% công suất danh định.",
            f"Mức tải cao ghi nhận công suất tức thời đạt {p_str} kW, tương đương {pct_s}% Pđm.",
        ]
    else:
        return [
            f"Công suất tức thời đạt mức {p_str} kW",
            f"Mức tải thực tế đạt {p_str} kW ({pct_s}% Pđm).",
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
        f"Tổng hợp các thông số đo kiểm tại {name_mid} cho thấy chất lượng điện đạt mức {quality}.",
        f"Theo số liệu đo kiểm, chất lượng điện áp và dòng điện cấp cho {name_mid} ở mức {quality}.",
        f"Kết quả khảo sát ghi nhận {name_mid} vận hành với chất lượng điện ở mức {quality}.",
    ]


def get_device_closings_eval(name: str, quality: str) -> list[str]:
    """Mẫu câu chốt tổng kết đánh giá chất lượng điện ở cuối đoạn cho thiết bị (viết lại tên thiết bị)."""
    name_mid = name[0].lower() + name[1:] if name and len(name) > 1 and not name.isupper() else name
    return [
        f"Tổng hợp các kết quả phân tích cho thấy chất lượng điện năng cấp cho {name_mid} vận hành ở mức {quality}.",
        f"Nhìn chung, hệ thống điện cấp cho {name_mid} đảm bảo chất lượng ở mức {quality}.",
        f"Kết quả đo kiểm tổng hợp đánh giá nguồn điện cấp cho {name_mid} đạt chất lượng ở mức {quality}.",
        f"Đánh giá chung, nguồn điện cấp cho {name_mid} có chất lượng ở mức {quality}.",
    ]


def get_pf_dev_templates(pf_txt: str, abs_pf: float) -> list[str]:
    """Mẫu câu hệ số công suất cosφ cho thiết bị."""
    if abs_pf >= 0.9:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất của thiết bị ở mức {pf_txt}.",
            f"Hệ số công suất đo được ở mức {pf_txt}.",
            f"Giá trị hệ số công suất đo được tại thời điểm khảo sát ở mức {pf_txt}.",
            f"Hệ số công suất cosφ ở mức {pf_txt}, đáp ứng tốt yêu cầu vận hành.",
            f"Hệ số cosφ ghi nhận ở mức {pf_txt}, thiết bị sử dụng hiệu quả công suất điện năng.",
            f"Hệ số công suất đo được ở mức {pf_txt}, đảm bảo hiệu quả vận hành.",
        ]
    elif abs_pf >= 0.8:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất của thiết bị ở mức {pf_txt}.",
            f"Hệ số cosφ đo được có giá trị {pf_txt}.",
            f"Giá trị hệ số công suất đo được tại thời điểm khảo sát ở mức {pf_txt}.",
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất đo được ở mức {pf_txt}.",
        ]
    else:
        return [
            f"Hệ số công suất cosφ ở mức {pf_txt}.",
            f"Hệ số công suất ở mức {pf_txt}.",
            f"Hệ số cosφ đo được ở mức {pf_txt}.",
            f"Hệ số cosφ đo được có giá trị {pf_txt}.",
            f"Hệ số công suất đo được ở mức {pf_txt}.",
        ]


def get_wave_dev_by_category(cat: str, wave: str) -> list[str]:
    """Mẫu câu đặc tính đồ thị dòng điện và công suất tức thời theo nhóm thiết bị (VSD, Servo, Lighting, VFD, Thường)."""
    if cat == "vsd_compressor":
        return [
            "Biểu đồ dòng điện tiêu thụ biến đổi mượt mà theo áp suất khí nén nhờ bộ biến tần VSD điều chỉnh tốc độ động cơ.",
            "Máy nén khí VSD vận hành tự động điều chỉnh tốc độ motor theo nhu cầu sử dụng khí nén thực tế.",
            "Đồ thị dòng điện thể hiện đặc tính điều khiển biến tần VSD, giúp tối ưu điện năng tiêu thụ và tránh sụt áp khi khởi động.",
            "Biểu đồ dòng điện biến đổi theo phụ tải điều khiển qua bộ biến tần VSD của máy nén khí.",
            "Dòng điện tiêu thụ biến đổi linh hoạt theo nhu cầu khí nén thực tế, nhờ bộ VSD tự động tăng/giảm tốc độ motor, không gây sụt áp đột ngột.",
            "Biểu đồ dòng điện phản ánh đặc tính điều tốc tuyến tính của VSD, dòng điện tăng/giảm mượt mà theo áp suất yêu cầu.",
            "Dòng điện tiêu thụ dao động linh hoạt theo nhu cầu khí nén thực tế nhờ khả năng điều tốc của biến tần VSD.",
            "Công suất tiêu thụ tức thời tự động điều chỉnh linh hoạt bám sát nhu cầu sử dụng khí nén thực tế nhờ bộ biến tần VSD.",
            "Biến động công suất tức thời phản ánh đúng chế độ điều tốc tuyến tính của VSD, giúp tối ưu điện năng khi phụ tải thay đổi.",
        ]
    elif cat == "servo_sewing":
        return [
            "Biểu đồ dòng điện tiêu thụ dao động liên tục với tần suất cao, phản ánh đúng đặc tính vận hành nhấp nhô theo từng nhịp may của công nhân.",
            "Đồ thị dòng điện biến động liên tục theo nhịp thao tác trên chuyền may, thể hiện đặc tính tải nhấp nhô của động cơ servo.",
            "Dòng điện tiêu thụ biến đổi liên tục với biên độ dao động nhanh theo từng công đoạn may sản phẩm.",
            "Biểu đồ dòng điện cấp cho chuyền may thể hiện đặc tính tải servo biến đổi liên tục theo nhịp sản xuất.",
            "Đồ thị dòng điện đặc trưng của chuyền may: biến thiên liên tục với biên độ cao, phản ánh tần suất đóng/ngắt nhanh của hàng loạt động cơ servo vận hành đồng thời.",
            "Sự dao động liên tục của dòng điện là đặc tính tải điển hình của xưởng may servo, phụ thuộc trực tiếp vào tốc độ và cường độ thao tác của công nhân.",
            "Dòng điện dao động với tần suất cao và biên độ ngắn, đặc trưng cho hoạt động của nhiều động cơ servo trên chuyền may.",
            "Công suất tiêu thụ tức thời dao động nhấp nhô với tần suất cao, thay đổi theo từng nhịp thao tác may trên chuyền.",
            "Biểu đồ công suất tức thời phản ánh đúng đặc tính vận hành theo thời gian thực của hàng loạt động cơ servo.",
        ]
    elif cat == "lighting":
        return [
            "Biểu đồ dòng điện tiêu thụ của hệ thống chiếu sáng duy trì rất ổn định trong suốt thời gian khảo sát.",
            "Đồ thị dòng điện tủ chiếu sáng có tính ổn định cao, phản ánh thời gian bật/tắt đèn cố định của tòa nhà/bệnh viện.",
            "Dòng điện cấp cho hệ thống đèn chiếu sáng vận hành ổn định theo thời gian hoạt động của khu vực.",
            "Biểu đồ dòng điện của hệ thống chiếu sáng duy trì mức ổn định cao trong giờ vận hành.",
            "Đặc tính ổn định của đồ thị dòng điện hệ thống chiếu sáng phản ánh chế độ vận hành liên tục, đèn bật/tắt theo giờ hành chính cố định.",
            "Dòng điện hệ thống chiếu sáng gần như không thay đổi trong giờ vận hành, chỉ có bước nhảy nhỏ khi bật/tắt từng khu vực theo ca.",
            "Dòng điện tiêu thụ gần như không đổi trong suốt khung giờ chiếu sáng, phản ánh đặc tính tải tuyến tính, ổn định.",
            "Công suất tiêu thụ tức thời của hệ thống duy trì mức rất ổn định, chỉ thay đổi nhỏ khi chuyển đổi ca chiếu sáng.",
        ]
    elif cat == "vfd_inverter":
        return [
            "Biểu đồ dòng điện tiêu thụ biến đổi mượt mà theo tần số điều khiển của biến tần.",
            "Đồ thị dòng điện đo được điều chỉnh linh hoạt theo tốc độ động cơ qua bộ biến tần.",
            "Biểu đồ dòng điện phản ánh quá trình điều khiển tần số dòng điện cấp cho động cơ.",
            f"Biểu đồ dòng điện tiêu thụ {wave} theo tần số biến tần điều khiển.",
            "Dòng điện tiêu thụ phản ánh rõ nét quá trình điều tốc của biến tần: tăng/giảm mượt mà theo nhu cầu vận hành thực tế.",
            "Biểu đồ dòng điện thể hiện khả năng điều tiết linh hoạt của biến tần, tránh được các sụt áp đột ngột khi khởi động và dừng động cơ.",
            "Dòng điện thay đổi linh hoạt tương ứng với tốc độ vận hành của động cơ do biến tần điều khiển.",
            "Công suất tiêu thụ tức thời biến đổi linh hoạt tương ứng với tần số điều khiển động cơ qua bộ biến tần.",
            "Đồ thị công suất tức thời phản ánh quá trình tăng/giảm tải mượt mà của biến tần theo nhu cầu vận hành thực tế.",
        ]
    elif cat == "building_commercial":
        return [
            "Hệ thống gồm nhiều thiết bị điện một pha khiến cho độ lệch giữa các pha trên đồ thị thể hiện rõ.",
            "Phụ tải tòa nhà/văn phòng chủ yếu gồm các thiết bị điện một pha (chiếu sáng, điều hòa cục bộ, máy tính) phân bổ trên các pha, khiến độ lệch dòng điện giữa các pha hiển thị rõ nét trên đồ thị.",
            "Biểu đồ dòng điện thể hiện rõ đặc tính phụ tải tòa nhà với nhiều thiết bị điện 1 pha tiêu thụ rải rác và không đồng đều giữa các pha.",
            "Do đặc thù phụ tải tòa nhà sử dụng nhiều thiết bị điện một pha, đồ thị dòng điện giữa các pha có sự lệch pha thể hiện rõ.",
            "Dòng điện giữa các pha có sự chênh lệch rõ nét trên đồ thị, phản ánh đúng thực tế vận hành rải rác của các nhóm phụ tải điện một pha trong tòa nhà.",
            "Công suất tiêu thụ tức thời của các tầng/phân khu biến đổi linh hoạt tương ứng với mật độ thiết bị điện một pha vận hành trong ca.",
            "Hệ thống gồm nhiều thiết bị điện một pha phân bổ trên các pha khiến cho độ lệch pha thể hiện rõ nét.",
        ]
    elif cat == "chiller_hvac":
        return [
            "Công suất tiêu thụ tức thời của hệ thống Chiller/HVAC biến đổi theo nhu cầu làm lạnh và nhiệt độ môi trường thực tế.",
            "Biểu đồ dòng điện thể hiện đặc tính vận hành của hệ thống HVAC trung tâm: dòng điện biến đổi nhịp nhàng theo chu kỳ điều chỉnh công suất làm lạnh.",
            "Đồ thị dòng điện phản ánh chế độ tải biến đổi theo ca của hệ thống Chiller, tăng cao vào các giờ cao điểm nhiệt độ và giảm về đêm.",
            "Công suất tiêu thụ tức thời điều chỉnh linh hoạt theo số lượng máy nén Chiller và quạt AHU/bơm nước lạnh tham gia vận hành.",
            "Đặc tính tải Chiller/HVAC biến đổi theo bước công suất làm lạnh, vận hành ổn định trong dải tải thiết kế.",
            "Dòng điện tiêu thụ của hệ thống Chiller duy trì ở mức cao và biến đổi theo nhu cầu phụ tải làm mát của tòa nhà/nhà xưởng.",
        ]
    elif cat == "ups_datacenter":
        return [
            "Công suất tiêu thụ tức thời duy trì mức rất ổn định, phản ánh đặc tính tải vận hành liên tục 24/7 của hệ thống trung tâm dữ liệu/UPS.",
            "Biểu đồ dòng điện cấp cho hệ thống UPS/Data Center thể hiện đặc tính tải ổn định phẳng, với hệ số công suất cosφ cao do bộ chỉnh lưu hiện đại.",
            "Dòng điện tiêu thụ duy trì ổn định cao, biến động không đáng kể trong suốt khung giờ khảo sát của phòng máy chủ.",
        ]
    elif cat == "solar_inverter":
        return [
            "Đồ thị công suất phát của hệ thống Inverter Điện mặt trời biến thiên mượt mà theo cường độ bức xạ ánh sáng mặt trời thực tế.",
            "Biểu đồ dòng điện phản ánh chế độ phát công suất hòa lưới của Inverter: tăng cao vào thời điểm giữa trưa và giảm dần về chiều tối.",
            "Công suất tức thời biến đổi linh hoạt bám sát cường độ bức xạ mặt trời, thể hiện khả năng dò điểm công suất cực đại (MPPT) của bộ hòa lưới.",
        ]
    elif cat == "welding_furnace":
        return [
            "Biểu đồ dòng điện ghi nhận các xung dòng nhọn tăng cao đột biến với tần suất liên tục, thể hiện rõ đặc tính vận hành đóng/ngắt tải xung của máy hàn/lò điện.",
            "Đồ thị dòng điện biến động rất mạnh với biên độ rộng, phản ánh các chu kỳ hàn ngắn hạn và thời gian chờ không tải ngắt quãng.",
            "Công suất tiêu thụ tức thời thay đổi đột ngột giữa mức tải đỉnh khi đóng cọc hàn/nạp lò và mức tải chờ ngắn hạn.",
        ]


    _wave_dev_map: dict[str, list[str]] = {
        "ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị ổn định trong thời gian đo kiểm.",
            "Biểu đồ dòng điện cấp cho thiết bị duy trì ổn định trong suốt quá trình khảo sát.",
            "Biểu đồ dòng điện của thiết bị thể hiện tính ổn định trong vận hành.",
            "Dòng điện tiêu thụ duy trì ổn định, không ghi nhận sự kiện quá tải hay sụt áp bất thường trong thời gian khảo sát.",
            "Dòng điện tiêu thụ không có biến động đáng kể trong suốt thời gian khảo sát.",
            "Công suất tiêu thụ tức thời tại thiết bị duy trì ở mức ổn định, không xuất hiện biến động đột biến trong thời gian khảo sát.",
        ],
        "tương đối ổn định": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị tương đối ổn định trong thời gian đo kiểm.",
            "Đồ thị dòng điện cấp cho thiết bị tương đối ổn định.",
            "Dòng điện tiêu thụ tương đối ổn định với dao động biên độ nhỏ, phản ánh điều kiện vận hành bình thường của thiết bị.",
            "Dòng điện tiêu thụ dao động không đáng kể, phản ánh chế độ vận hành tương đối đều đặn.",
            "Công suất tiêu thụ tức thời tương đối ổn định, chỉ dao động nhẹ theo sự điều chỉnh tải của hệ thống.",
        ],
        "biến đổi liên tục theo tải": [
            "Biểu đồ dòng điện tiêu thụ biến đổi liên tục theo tải trong thời gian đo kiểm.",
            "Đồ thị dòng điện có sự điều chỉnh theo hoạt động sản xuất.",
            "Biểu đồ dòng điện cấp cho thiết bị có sự biến động theo tình hình vận hành.",
            "Dòng điện tiêu thụ biến đổi linh hoạt theo cường độ vận hành sản xuất thực tế.",
            "Dòng điện tiêu thụ thay đổi tương ứng với cường độ hoạt động thực tế của thiết bị.",
            "Công suất tiêu thụ tức thời biến đổi linh hoạt, bám sát theo cường độ vận hành sản xuất thực tế.",
        ],
        "biến đổi liên tục": [
            "Biểu đồ dòng điện tiêu thụ tại thiết bị biến đổi liên tục trong thời gian đo kiểm.",
            "Đồ thị dòng điện đo được tại thiết bị có sự biến đổi liên tục.",
            "Biểu đồ dòng điện tiêu thụ biến đổi liên tục trong thời gian đo kiểm.",
            "Dòng điện tiêu thụ biến đổi liên tục"
            "Đồ thị dòng điện cho thấy thiết bị hoạt động với đặc tính tải biến đổi liên tục trong thời gian đo kiểm.",
            "Dòng điện tiêu thụ dao động thường xuyên trong suốt quá trình khảo sát.",
            "Công suất tiêu thụ tức thời biến đổi liên tục theo thời gian thực, đặc trưng cho nhóm phụ tải động.",
        ],
        "biến đổi liên tục với biên độ nhỏ": [
            "Biểu đồ dòng điện tiêu thụ của thiết bị biến đổi liên tục với biên độ nhỏ.",
            "Đồ thị dòng điện đo được tại thiết bị biến đổi liên tục với biên độ không lớn.",
            "Biểu đồ dòng điện tiêu thụ biến đổi liên tục với biên độ nhỏ trong thời gian đo kiểm.",
            "Dòng điện tiêu thụ có sự dao động nhẹ liên tục với biên độ nhỏ.",
            "Công suất tiêu thụ tức thời dao động với biên độ nhỏ xung quanh giá trị trung bình.",
        ],
        "ổn định nhưng có sự biến đổi trong quá trình đo": [
            "Biểu đồ dòng điện tiêu thụ nhìn chung duy trì mức ổn định, tuy nhiên có sự biến đổi nhẹ tại một số thời điểm trong quá trình đo kiểm.",
            "Đồ thị dòng điện thể hiện xu hướng tương đối ổn định, kèm theo các đợt thay đổi nhỏ.",
            "Biểu đồ dòng điện của thiết bị duy trì ổn định làm chủ đạo, nhưng ghi nhận những khoảng biến đổi nhỏ trong suốt thời gian khảo sát.",
            "Dòng điện tiêu thụ tổng thể ổn định, chỉ xuất hiện sự biến đổi nhỏ tại một số thời điểm.",
            "Công suất tiêu thụ tức thời duy trì mức ổn định ở từng khoảng thời gian, có sự điều chỉnh khi thay đổi chế độ làm việc.",
        ],
        "dao động liên tục quanh ngưỡng nhất định": [
            "Biểu đồ dòng điện tiêu thụ dao động liên tục quanh một ngưỡng nhất định trong suốt thời gian đo kiểm.",
            "Đồ thị dòng điện ghi nhận sự dao động đều đặn quanh dải giá trị cố định.",
            "Biểu đồ dòng điện của thiết bị biến thiên liên tục xung quanh mức tải trung bình cố định.",
            "Dòng điện tiêu thụ duy trì trạng thái dao động liên tục quanh điểm cài đặt vận hành của hệ thống.",
            "Đồ thị dòng điện đo được dao động ổn định quanh một ngưỡng dòng điện xác định.",
            "Công suất tiêu thụ tức thời dao động đều đặn xung quanh một ngưỡng giá trị định vị cố định.",
        ],
        "dao động liên tục với biên độ lớn": [
            "Biểu đồ dòng điện tiêu thụ dao động liên tục với biên độ lớn trong suốt thời gian đo kiểm.",
            "Đồ thị dòng điện biến động mạnh với biên độ dao động rộng, phản ánh đặc tính tải không ổn định của thiết bị.",
            "Biểu đồ dòng điện ghi nhận các bước nhảy công suất lớn và liên tục theo từng chu kỳ vận hành sản xuất.",
            "Dòng điện tiêu thụ dao động với biên độ lớn quanh mức trung bình, thể hiện sự thay đổi tải đột ngột thường xuyên.",
            "Công suất tiêu thụ tức thời dao động mạnh với biên độ lớn, thể hiện sự thay đổi tải đột ngột thường xuyên.",
        ],
        "biến đổi nhấp nhô theo ca sản xuất": [
            "Biểu đồ dòng điện tiêu thụ thể hiện đặc tính tải nhấp nhô liên tục theo nhịp vận hành sản xuất.",
            "Đồ thị dòng điện biến động nhấp nhô theo từng công đoạn thao tác thực tế trên chuyền.",
            "Dòng điện tiêu thụ duy trì trạng thái tải nhấp nhô với tần suất thay đổi cao trong ca làm việc.",
            "Công suất tiêu thụ tức thời biến đổi nhấp nhô liên tục theo nhịp vận hành sản xuất trên chuyền.",
        ],
        "biến đổi theo chu kỳ load/unload": [
            "Biểu đồ dòng điện tiêu thụ cho thấy thiết bị vận hành theo chế độ Load/Unload.",
            "Đồ thị dòng điện đo được biến đổi theo chu kỳ Load/Unload.",
            "Thiết bị hoạt động theo chế độ Load/Unload, đồ thị dòng điện thể hiện rõ chu kỳ đóng/ngắt tải.",
            "Dòng điện tiêu thụ dao động tuần hoàn theo chu kỳ Load/Unload của máy nén, với biên độ bước nhảy lớn và thời gian lặp đều đặn.",
            "Dòng điện biến thiên theo từng chu kỳ tải/không tải đặc trưng của chế độ vận hành Load/Unload.",
        ],
        "cao đột biến và có tính chu kỳ": [
            "Tại thời điểm khảo sát, đồ thị dòng điện đo được có những thời điểm cao đột biến và có tính chu kỳ.",
            "Biểu đồ dòng điện ghi nhận các đỉnh nhọn tăng cao đột biến với tần suất lặp lại có tính chu kỳ trong suốt thời gian khảo sát.",
            "Đồ thị dòng điện xuất hiện các bước nhảy công suất cao đột biến theo chu kỳ vận hành của phụ tải.",
            "Dòng điện tiêu thụ duy trì ở mức trung bình và xuất hiện các xung dòng cao đột biến lặp lại định kỳ theo thời gian.",
            "Biểu đồ dòng điện đo được ghi nhận các đỉnh tải tăng cao đột biến có tính chu kỳ, thể hiện sự khởi động/vận hành tuần hoàn của thiết bị công suất lớn.",
            "Đặc tính dòng điện tiêu thụ biến động với các đỉnh nhọn xuất hiện có tính chu kỳ, tương ứng với chu kỳ thao tác/khởi động máy.",
        ],
        "xuất hiện các đỉnh nhọn cao đột biến": [
            "Biểu đồ dòng điện ghi nhận sự xuất hiện của các đỉnh nhọn công suất cao đột biến tại một số thời điểm đo kiểm.",
            "Đồ thị dòng điện tiêu thụ xuất hiện các bước nhảy tăng cao đột biến so với mức trung bình.",
            "Dòng điện tiêu thụ tổng thể duy trì ổn định, tuy nhiên ghi nhận các đỉnh nhọn dòng điện tăng đột biến rải rác.",
        ],
        "biến đổi theo bậc tải": [
            "Biểu đồ dòng điện tiêu thụ biến đổi theo từng bậc tải, phản ánh quá trình tự động bật/tắt các cụm thiết bị phụ thuộc theo nhu cầu vận hành thực tế.",
            "Đồ thị dòng điện thể hiện đặc tính biến đổi theo bậc tải, chuyển nấc rõ rệt giữa các cấp công suất vận hành.",
            "Dòng điện tiêu thụ biến đổi theo từng nấc tải công suất, phản ánh chế độ đóng/ngắt các khối phụ tải trong hệ thống.",
        ],
        "dòng đỉnh nhọn khi khởi động": [
            "Biểu đồ dòng điện ghi nhận các đỉnh nhọn vọt cao ngắn hạn tại thời điểm khởi động thiết bị, sau đó duy trì ổn định ở mức tải vận hành bình thường.",
            "Đồ thị dòng điện tiêu thụ xuất hiện xung dòng đỉnh nhọn ngắn hạn lúc khởi động, sau đó giảm nhanh về dải tải vận hành ổn định.",
            "Dòng điện tiêu thụ tổng thể duy trì ổn định, ngoại trừ sự xuất hiện của dòng đỉnh nhọn tại thời điểm khởi động phụ tải nặng.",
        ],
        "biến đổi mượt mà theo tần số": [
            "Dòng điện tiêu thụ biến đổi mượt mà và tỷ lệ thuận với tần số điều khiển biến tần, bám sát nhu cầu phụ tải thực tế mà không gây bước nhảy đột ngột.",
            "Biểu đồ dòng điện phản ánh đặc tính điều tốc mượt mà theo tần số, dòng điện tăng/giảm tuyến tính theo nhu cầu vận hành.",
            "Đồ thị dòng điện biến đổi mượt mà bám sát phụ tải, thể hiện hiệu quả của hệ thống điều khiển biến tần linh hoạt.",
        ],
        "biến đổi theo ca sản xuất": [
            "Biểu đồ dòng điện thể hiện rõ nhịp độ ca làm việc: duy trì mức tải cao trong giờ sản xuất và giảm về mức tải chờ vào các khoảng nghỉ chuyển ca.",
            "Đồ thị dòng điện phản ánh chế độ tải biến đổi theo ca sản xuất, tăng cao trong giờ hành chính và hạ thấp ngoài ca làm việc.",
            "Dòng điện tiêu thụ biến đổi tương ứng với tiến trình các ca làm việc trong ngày của nhà máy.",
        ],
        "biến đổi tuần hoàn theo chu kỳ công nghệ": [
            "Đồ thị dòng điện biến đổi tuần hoàn theo đúng chu kỳ công nghệ của thiết bị (kẹp khuôn, nén ép và xả tải), với khoảng thời gian lặp lại đều đặn.",
            "Biểu đồ dòng điện lặp lại đều đặn theo các chu kỳ công nghệ thao tác thực tế của máy.",
            "Dòng điện tiêu thụ biến động tuần hoàn có tính chu kỳ, thể hiện các giai đoạn vận hành nối tiếp trong một chu kỳ sản xuất.",
        ],
    }

    # Bổ sung các alias mapping linh hoạt
    _wave_dev_map["ổn định nhưng có biến đổi"] = _wave_dev_map["ổn định nhưng có sự biến đổi trong quá trình đo"]
    _wave_dev_map["ổn định có biến đổi"] = _wave_dev_map["ổn định nhưng có sự biến đổi trong quá trình đo"]
    _wave_dev_map["ổn định có điều chỉnh"] = _wave_dev_map["ổn định nhưng có sự biến đổi trong quá trình đo"]
    _wave_dev_map["ổn định nhưng có sự điều chỉnh trong quá trình đo"] = _wave_dev_map["ổn định nhưng có sự biến đổi trong quá trình đo"]
    _wave_dev_map["dao động quanh ngưỡng"] = _wave_dev_map["dao động liên tục quanh ngưỡng nhất định"]
    _wave_dev_map["dao động liên tục quanh ngưỡng"] = _wave_dev_map["dao động liên tục quanh ngưỡng nhất định"]
    _wave_dev_map["dao động quanh mức"] = _wave_dev_map["dao động liên tục quanh ngưỡng nhất định"]
    _wave_dev_map["biến đổi quanh ngưỡng"] = _wave_dev_map["dao động liên tục quanh ngưỡng nhất định"]
    _wave_dev_map["dao động biên độ lớn"] = _wave_dev_map["dao động liên tục với biên độ lớn"]
    _wave_dev_map["tải nhấp nhô"] = _wave_dev_map["biến đổi nhấp nhô theo ca sản xuất"]
    _wave_dev_map["đột biến có tính chu kỳ"] = _wave_dev_map["cao đột biến và có tính chu kỳ"]
    _wave_dev_map["đột biến theo chu kỳ"] = _wave_dev_map["cao đột biến và có tính chu kỳ"]
    _wave_dev_map["đỉnh nhọn chu kỳ"] = _wave_dev_map["cao đột biến và có tính chu kỳ"]
    _wave_dev_map["tải xung chu kỳ"] = _wave_dev_map["cao đột biến và có tính chu kỳ"]

    _wave_key_dev = wave.lower().strip()
    if _wave_key_dev in _wave_dev_map:
        return _wave_dev_map[_wave_key_dev]
    return [f"Biểu đồ dòng điện tiêu thụ {wave} trong thời gian đo kiểm."]

