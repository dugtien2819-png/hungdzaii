# Ứng Dụng So Sánh Độ Điển Trai Nam Giới (AI Handsome Face Comparator)

Ứng dụng web xây dựng bằng **FastAPI**, **MediaPipe Face Mesh (478 3D Facial Landmarks)** và **OpenCV**, cho phép so sánh độ đẹp trai giữa **2 bức ảnh khuôn mặt nam giới** dựa trên **Bảng Tiêu Chí Thẩm Mỹ Toàn Cầu**.

---

## 🌟 Bảng Tiêu Chí Thẩm Mỹ Thế Giới Được Áp Dụng

Hệ thống tính toán dựa trên các nghiên cứu nhân trắc học khuôn mặt (Facial Anthropometry) và các chuẩn mực nhan sắc quốc tế:

1. **Đường nét & Góc xương hàm (Jawline & Gonial Angle - Trọng số 20%):**
   * Góc hàm (Gonial angle) lý tưởng của nam giới: **115° – 125°** (chuẩn mực góc cạnh, nam tính).
   * Tỷ lệ độ rộng xương hàm so với gò má (Bigonial / Bizygomatic ratio): lý tưởng **0.84 – 0.90**.
2. **Đôi mắt & Ánh nhìn Hunter Eyes (Canthal Tilt & Eye Spacing - Trọng số 15%):**
   * Độ nghiêng góc mắt Canthal Tilt dương (**+2° đến +6°**) tạo ánh nhìn sắc bén, cuốn hút đặc trưng của người mẫu nam ("Hunter Eyes").
   * Khoảng cách giữa 2 mắt xấp xỉ 1 độ rộng mắt (chuẩn tỷ lệ 1/5).
3. **Độ đối xứng khuôn mặt (Facial Symmetry - Trọng số 15%):**
   * Đo khoảng cách sai lệch của các cặp điểm ngũ quan (mắt, mày, mũi, môi, gò má, viền hàm) so với trục đối xứng dọc khuôn mặt.
4. **Tỷ lệ 3 tầng khuôn mặt (Rule of Thirds - Trọng số 15%):**
   * Tầng trên (trán), Tầng giữa (mũi), Tầng dưới (cằm) chia đều tỷ lệ **1 : 1 : 1** (mỗi phần 33.3%).
5. **Tỷ lệ chiều ngang 5 phần & Gò má (Rule of Fifths & Face Proportion - Trọng số 15%):**
   * Tỷ lệ chiều dài khuôn mặt / chiều rộng mặt chuẩn nam tính lý tưởng: **1.35 – 1.45**.
6. **Tỷ lệ Mũi & Môi (Nose & Lips Harmony - Trọng số 10%):**
   * Chiều rộng cánh mũi tương ứng với khoảng cách 2 khóe mắt trong (tỷ lệ 1:1).
   * Độ dày môi dưới so với môi trên tỷ lệ chuẩn **1:1.5**.
7. **Độ nhô cằm & Tầng mặt dưới (Chin Prominence - Trọng số 10%):**
   * Cằm chiếm **62% – 68%** chiều cao tầng mặt dưới, thể hiện sự vững chãi, uy quyền.

---

## 🚀 Cách Khởi Chạy Ứng Dụng

### Cách 1: Chạy file Batch (Nhanh nhất trên Windows)
Chỉ cần nhấp đúp chuột vào file:
```
run_app.bat
```

### Cách 2: Chạy bằng dòng lệnh Terminal
```powershell
py -m uvicorn handsome_app.main:app --host 127.0.0.1 --port 8000 --reload
```

Sau đó mở trình duyệt web và truy cập:
👉 **http://127.0.0.1:8000**

---

## 💡 Tính Năng Nổi Bật Trên Giao Diện Web

* **Kéo thả / Tải lên 2 ảnh:** Xem trước ảnh trực tiếp, hỗ trợ định dạng JPG, PNG, WEBP.
* **Nút "Thử nhanh với 2 ảnh mẫu":** Trải nghiệm ngay kết quả so sánh với 1 cú click.
* **Bảng điểm đối đầu (Head-to-head Scoreboard):**
  - Điểm tổng thể trên thang **100** và thang **10**.
  - Phân hạng đẳng cấp nhan sắc quốc tế: *God Tier, Supermodel, Handsome, Above Average...*
* **Trực quan hóa Lưới Landmark AI & Tỷ Lệ Vàng:**
  - Hiển thị trực tiếp trục đối xứng, đường chia 3 tầng mặt, viền xương hàm và vector góc mắt Canthal Tilt.
  - Công tắc bật/tắt giữa ảnh lưới AI và ảnh gốc.
* **Biểu đồ mạng nhện (Radar Chart):** Trực quan hóa độ phủ cả 7 tiêu chí thẩm mỹ.
* **Chi Tiết "Đẹp hơn ở chỗ nào?":** Từng thẻ tiêu chí chỉ rõ ai thắng, cách biệt bao nhiêu điểm kèm lý giải khoa học chi tiết bằng tiếng Việt.
* **Tổng kết thẩm mỹ:** Đánh giá điểm mạnh vượt trội của từng gương mặt.
