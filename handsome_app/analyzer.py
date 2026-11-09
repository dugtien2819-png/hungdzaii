import cv2
import math
import base64
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandsomeFaceAnalyzer:
    def __init__(self, model_path: str = "handsome_app/models/face_landmarker.task"):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            num_faces=1
        )
        self.detector = vision.FaceLandmarker.create_from_options(options)
        
        # Weights for the 7 World Aesthetic Criteria
        self.weights = {
            "symmetry": 0.15,
            "jawline": 0.20,
            "eyes": 0.15,
            "rule_of_thirds": 0.15,
            "rule_of_fifths": 0.15,
            "nose_lips": 0.10,
            "chin_lower_face": 0.10,
        }

    def _calc_angle(self, p1, p2, p3):
        """Angle at p2 formed by (p1-p2) and (p3-p2) in degrees"""
        v1 = p1 - p2
        v2 = p3 - p2
        dot = np.dot(v1, v2)
        m1 = np.linalg.norm(v1)
        m2 = np.linalg.norm(v2)
        if m1 * m2 == 0:
            return 180.0
        cos_val = np.clip(dot / (m1 * m2), -1.0, 1.0)
        return float(math.degrees(math.acos(cos_val)))

    def _get_tilt(self, inner, outer, ref_angle=0.0):
        """Calculate canthal tilt in degrees relative to facial horizontal"""
        dx = outer[0] - inner[0]
        dy = outer[1] - inner[1] # in image coords, y goes down
        # angle in degrees where positive means outer canthus is higher than inner canthus
        tilt = -math.degrees(math.atan2(dy, abs(dx)))
        return float(tilt - ref_angle)

    def extract_landmarks(self, image_bytes: bytes):
        """Decode image and detect facial landmarks"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None, None
        
        h, w = img.shape[:2]
        # Resize to max 1280 to maintain good performance & landmark fidelity
        max_dim = max(h, w)
        if max_dim > 1280:
            scale = 1280.0 / max_dim
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self.detector.detect(mp_img)
        
        if not results.face_landmarks:
            return None, img

        landmarks = results.face_landmarks[0]
        pts = np.array([[lm.x * w, lm.y * h] for lm in landmarks], dtype=np.float32)
        return pts, img

    def analyze_face(self, pts, img):
        """Compute all 7 world standard aesthetic criteria for a male face"""
        h, w = img.shape[:2]

        # Key landmark points
        top_forehead = pts[10]       # Trichion approx
        glabella = pts[168]          # Nasion/Glabella
        subnasale = pts[2]           # Base of nose
        menton = pts[152]            # Chin bottom
        nose_tip = pts[1]            # Pronasale
        
        # Eyes
        # Left eye (viewer's left / subject's right): 133 inner, 33 outer
        l_inner = pts[133]
        l_outer = pts[33]
        # Right eye (viewer's right / subject's left): 362 inner, 263 outer
        r_inner = pts[362]
        r_outer = pts[263]
        
        # Eye width & distance
        l_eye_w = np.linalg.norm(l_outer - l_inner)
        r_eye_w = np.linalg.norm(r_outer - r_inner)
        avg_eye_w = (l_eye_w + r_eye_w) / 2.0
        interocular_d = np.linalg.norm(r_inner - l_inner)
        
        # Facial tilt / roll correction based on eye centers
        l_pupil = (l_inner + l_outer) / 2.0
        r_pupil = (r_inner + r_outer) / 2.0
        eye_vec = r_pupil - l_pupil
        face_roll = math.degrees(math.atan2(eye_vec[1], eye_vec[0]))
        
        # 1. FACIAL SYMMETRY (Độ đối xứng khuôn mặt)
        # Vertical axis: glabella to menton
        axis_vec = menton - glabella
        axis_len = np.linalg.norm(axis_vec)
        if axis_len > 0:
            axis_unit = axis_vec / axis_len
            perp_unit = np.array([-axis_unit[1], axis_unit[0]])
        else:
            axis_unit = np.array([0, 1])
            perp_unit = np.array([1, 0])

        sym_pairs = [
            (33, 263),   # outer eye corners
            (133, 362),  # inner eye corners
            (234, 454),  # cheekbones
            (172, 397),  # jaw corners (gonions)
            (61, 291),   # mouth corners
            (107, 336),  # eyebrow peaks
            (48, 278),   # nose wings (alars)
        ]
        
        sym_diffs = []
        for left_idx, right_idx in sym_pairs:
            p_left = pts[left_idx]
            p_right = pts[right_idx]
            # distance of each point to the central axis
            dist_left = abs(np.dot(p_left - glabella, perp_unit))
            dist_right = abs(np.dot(p_right - glabella, perp_unit))
            avg_dist = (dist_left + dist_right) / 2.0
            if avg_dist > 1.0:
                diff_ratio = abs(dist_left - dist_right) / avg_dist
                sym_diffs.append(diff_ratio)
        
        mean_sym_diff = np.mean(sym_diffs) if sym_diffs else 0.05
        # Ideal symmetry diff is 0; 0.03 is exceptionally symmetric
        sym_score = float(np.clip(100.0 - (mean_sym_diff * 260.0), 55.0, 99.5))

        # 2. JAWLINE & GONIAL ANGLE (Góc hàm & Độ sắc nét viền hàm)
        # Left gonion: 172, Right gonion: 397
        l_gonion = pts[172]
        r_gonion = pts[397]
        # Ear top/temporal: 127 and 356
        l_temporal = pts[127]
        r_temporal = pts[356]
        
        l_gonial_angle = self._calc_angle(l_temporal, l_gonion, menton)
        r_gonial_angle = self._calc_angle(r_temporal, r_gonion, menton)
        avg_gonial_angle = (l_gonial_angle + r_gonial_angle) / 2.0
        
        # Ideal male gonial angle is 115° - 125° (sweet spot ~120°)
        angle_dev = abs(avg_gonial_angle - 120.0)
        jaw_angle_score = max(50.0, 100.0 - (angle_dev * 2.8))
        
        # Jaw width vs Cheekbone width (Bigonial / Bizygomatic ratio)
        jaw_w = np.linalg.norm(r_gonion - l_gonion)
        cheek_w = np.linalg.norm(pts[454] - pts[234])
        jaw_cheek_ratio = (jaw_w / cheek_w) if cheek_w > 0 else 0.8
        # Ideal male ratio is 0.84 - 0.90
        ratio_dev = abs(jaw_cheek_ratio - 0.87)
        jaw_ratio_score = max(50.0, 100.0 - (ratio_dev * 220.0))
        
        jawline_score = float(np.clip((jaw_angle_score * 0.6) + (jaw_ratio_score * 0.4), 52.0, 99.2))

        # 3. EYES & CANTHAL TILT (Đôi mắt & Ánh nhìn Hunter Eyes)
        l_tilt = self._get_tilt(l_inner, l_outer, face_roll)
        r_tilt = self._get_tilt(r_inner, r_outer, -face_roll)
        avg_tilt = (l_tilt + r_tilt) / 2.0
        
        # Aesthetic evaluation of canthal tilt:
        # Positive tilt (+2° to +6°) is hunter eyes / attractive
        if 2.0 <= avg_tilt <= 6.0:
            tilt_score = 96.0 + (avg_tilt - 2.0) * 0.8
        elif avg_tilt > 6.0:
            tilt_score = max(75.0, 99.0 - (avg_tilt - 6.0) * 3.0)
        elif 0.0 <= avg_tilt < 2.0:
            tilt_score = 88.0 + (avg_tilt * 4.0)
        else: # negative tilt
            tilt_score = max(50.0, 85.0 - abs(avg_tilt) * 5.0)

        # Eye spacing: interocular distance / eye width (Rule of Fifths)
        # Ideal is 1.0 (space between eyes equals width of one eye)
        eye_space_ratio = interocular_d / avg_eye_w if avg_eye_w > 0 else 1.0
        eye_space_score = max(50.0, 100.0 - abs(eye_space_ratio - 1.0) * 120.0)
        
        eyes_score = float(np.clip((tilt_score * 0.65) + (eye_space_score * 0.35), 52.0, 99.0))

        # 4. RULE OF THIRDS (Tỷ lệ vàng 3 tầng mặt theo chiều dọc)
        h_upper = np.linalg.norm(glabella - top_forehead)
        h_mid = np.linalg.norm(subnasale - glabella)
        h_lower = np.linalg.norm(menton - subnasale)
        h_total = h_upper + h_mid + h_lower
        
        t_upper = (h_upper / h_total) if h_total > 0 else 0.333
        t_mid = (h_mid / h_total) if h_total > 0 else 0.333
        t_lower = (h_lower / h_total) if h_total > 0 else 0.333
        
        # Ideal: 0.333 each (33.3%)
        thirds_dev = np.sqrt(((t_upper - 0.3333)**2 + (t_mid - 0.3333)**2 + (t_lower - 0.3333)**2) / 3.0)
        thirds_score = float(np.clip(100.0 - (thirds_dev * 340.0), 50.0, 99.5))

        # 5. RULE OF FIFTHS & FACE PROPORTIONS (Tỷ lệ chiều ngang 5 phần & Chiều dài/rộng)
        # Face Height (forehead to menton) vs Face Width (cheek to cheek)
        face_h = np.linalg.norm(menton - top_forehead)
        face_w = cheek_w
        hw_ratio = (face_h / face_w) if face_w > 0 else 1.4
        # Ideal male facial height-to-width ratio is ~1.38 - 1.45 (compact, masculine)
        hw_dev = abs(hw_ratio - 1.40)
        fifths_score = float(np.clip(100.0 - (hw_dev * 130.0), 52.0, 99.0))

        # 6. NOSE & LIPS HARMONY (Tỷ lệ Mũi & Môi)
        # Nose width (alars 48 to 278) vs Intercanthal distance (ideal ratio = 1.0)
        nose_w = np.linalg.norm(pts[278] - pts[48])
        nose_ratio = (nose_w / interocular_d) if interocular_d > 0 else 1.0
        nose_score = max(50.0, 100.0 - abs(nose_ratio - 1.0) * 120.0)
        
        # Lip thickness ratio: upper lip (12 to 13) vs lower lip (14 to 17)
        upper_lip_h = np.linalg.norm(pts[13] - pts[0])
        lower_lip_h = np.linalg.norm(pts[17] - pts[14])
        lip_ratio = (upper_lip_h / lower_lip_h) if lower_lip_h > 0 else 0.65
        # Ideal male ratio is ~ 1:1.5 (approx 0.65 to 0.75)
        lip_score = max(50.0, 100.0 - abs(lip_ratio - 0.68) * 90.0)
        
        nose_lips_score = float(np.clip((nose_score * 0.55) + (lip_score * 0.45), 52.0, 99.0))

        # 7. CHIN & LOWER FACE MASCULINITY (Tỷ lệ Cằm & Tầng mặt dưới)
        # Distance from lower lip (17) to menton (152) vs total lower third
        chin_h = np.linalg.norm(menton - pts[17])
        chin_ratio = (chin_h / h_lower) if h_lower > 0 else 0.65
        # In attractive males, chin makes up ~ 62% - 68% of the lower third
        chin_dev = abs(chin_ratio - 0.65)
        chin_score = float(np.clip(100.0 - (chin_dev * 220.0), 52.0, 99.0))

        # Overall weighted score
        overall_score = (
            sym_score * self.weights["symmetry"] +
            jawline_score * self.weights["jawline"] +
            eyes_score * self.weights["eyes"] +
            thirds_score * self.weights["rule_of_thirds"] +
            fifths_score * self.weights["rule_of_fifths"] +
            nose_lips_score * self.weights["nose_lips"] +
            chin_score * self.weights["chin_lower_face"]
        )

        return {
            "overall_score": round(overall_score, 1),
            "scale_10": round(overall_score / 10.0, 2),
            "tier": self._get_tier(overall_score),
            "metrics": {
                "symmetry": {
                    "score": round(sym_score, 1),
                    "mean_diff_percent": round(mean_sym_diff * 100.0, 1),
                },
                "jawline": {
                    "score": round(jawline_score, 1),
                    "gonial_angle": round(avg_gonial_angle, 1),
                    "jaw_cheek_ratio": round(jaw_cheek_ratio, 2),
                },
                "eyes": {
                    "score": round(eyes_score, 1),
                    "canthal_tilt": round(avg_tilt, 1),
                    "eye_space_ratio": round(eye_space_ratio, 2),
                },
                "rule_of_thirds": {
                    "score": round(thirds_score, 1),
                    "upper_percent": round(t_upper * 100.0, 1),
                    "mid_percent": round(t_mid * 100.0, 1),
                    "lower_percent": round(t_lower * 100.0, 1),
                },
                "rule_of_fifths": {
                    "score": round(fifths_score, 1),
                    "height_width_ratio": round(hw_ratio, 2),
                },
                "nose_lips": {
                    "score": round(nose_lips_score, 1),
                    "nose_eye_ratio": round(nose_ratio, 2),
                    "lip_ratio": round(lip_ratio, 2),
                },
                "chin_lower_face": {
                    "score": round(chin_score, 1),
                    "chin_ratio_percent": round(chin_ratio * 100.0, 1),
                }
            },
            "raw_pts": pts,
        }

    def _get_tier(self, score: float) -> dict:
        if score >= 91.0:
            return {"title": "God Tier / Đỉnh Cao Nhan Sắc", "class": "tier-god", "badge": "🔱 Đẳng Cấp Thần Tượng"}
        elif score >= 84.0:
            return {"title": "Supermodel / Nam Thần Chuẩn Mực", "class": "tier-model", "badge": "💎 Chuẩn Siêu Mẫu"}
        elif score >= 77.0:
            return {"title": "Handsome / Điển Trai Nổi Bật", "class": "tier-handsome", "badge": "✨ Điển Trai Nổi Bật"}
        elif score >= 70.0:
            return {"title": "Above Average / Ưa Nhìn Nam Tính", "class": "tier-above", "badge": "⭐ Ưa Nhìn & Cuốn Hút"}
        else:
            return {"title": "Harmonious / Hài Hòa Tự Nhiên", "class": "tier-average", "badge": "🌱 Nét Đẹp Tự Nhiên"}

    def draw_annotated_image(self, img, pts):
        """Draw aesthetic golden ratio wireframe, symmetry axis, thirds and canthal tilt"""
        vis = img.copy()
        h, w = vis.shape[:2]

        # 1. Subtle landmark points
        for i in [10, 168, 2, 152, 33, 133, 362, 263, 172, 397, 234, 454, 48, 278, 0, 17]:
            p = (int(pts[i][0]), int(pts[i][1]))
            cv2.circle(vis, p, 4, (0, 240, 255), -1)
            cv2.circle(vis, p, 7, (0, 180, 255), 1)

        # 2. Central vertical symmetry axis (Cyan-Gold)
        p_top = (int(pts[10][0]), int(pts[10][1]))
        p_menton = (int(pts[152][0]), int(pts[152][1]))
        cv2.line(vis, p_top, p_menton, (0, 225, 255), 2, cv2.LINE_AA)

        # 3. Rule of Thirds horizontal guide lines (Glowing Neon Teal)
        for idx, col in [(10, (255, 180, 50)), (168, (50, 255, 200)), (2, (50, 255, 200)), (152, (255, 180, 50))]:
            y_val = int(pts[idx][1])
            x_min = max(10, int(pts[idx][0] - w * 0.35))
            x_max = min(w - 10, int(pts[idx][0] + w * 0.35))
            cv2.line(vis, (x_min, y_val), (x_max, y_val), col, 2, cv2.LINE_AA)

        # 4. Jawline contour (Amber/Gold line)
        jaw_indices = [127, 234, 172, 136, 150, 152, 379, 365, 397, 454, 356]
        jaw_pts = np.array([[int(pts[i][0]), int(pts[i][1])] for i in jaw_indices], dtype=np.int32)
        cv2.polylines(vis, [jaw_pts], False, (0, 140, 255), 3, cv2.LINE_AA)

        # 5. Canthal tilt eye vectors (Electric Violet/Purple)
        # Left eye
        cv2.line(vis, (int(pts[133][0]), int(pts[133][1])), (int(pts[33][0]), int(pts[33][1])), (255, 100, 220), 2, cv2.LINE_AA)
        # Right eye
        cv2.line(vis, (int(pts[362][0]), int(pts[362][1])), (int(pts[263][0]), int(pts[263][1])), (255, 100, 220), 2, cv2.LINE_AA)

        # Encode to Base64 JPEG
        _, buffer = cv2.imencode(".jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64_str = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"

    def compare(self, data1: dict, data2: dict) -> dict:
        """Produce head-to-head comparison and detailed Vietnamese analysis"""
        m1 = data1["metrics"]
        m2 = data2["metrics"]
        
        criteria_list = [
            {
                "id": "jawline",
                "name": "Đường nét & Góc xương hàm (Jawline & Gonial Angle)",
                "weight": "20%",
                "score1": m1["jawline"]["score"],
                "score2": m2["jawline"]["score"],
                "detail1": f"Góc hàm {m1['jawline']['gonial_angle']}° | Tỷ lệ hàm/mặt {m1['jawline']['jaw_cheek_ratio']}",
                "detail2": f"Góc hàm {m2['jawline']['gonial_angle']}° | Tỷ lệ hàm/mặt {m2['jawline']['jaw_cheek_ratio']}",
                "ideal": "Góc hàm nam tính 115° - 125°, xương hàm rộng 0.85 - 0.90 so với gò má.",
            },
            {
                "id": "eyes",
                "name": "Đôi mắt & Ánh nhìn Hunter Eyes (Canthal Tilt & Spacing)",
                "weight": "15%",
                "score1": m1["eyes"]["score"],
                "score2": m2["eyes"]["score"],
                "detail1": f"Độ xếch Canthal: {m1['eyes']['canthal_tilt']:+0.1f}° | Tỷ lệ khoảng cách 2 mắt: {m1['eyes']['eye_space_ratio']}",
                "detail2": f"Độ xếch Canthal: {m2['eyes']['canthal_tilt']:+0.1f}° | Tỷ lệ khoảng cách 2 mắt: {m2['eyes']['eye_space_ratio']}",
                "ideal": "Độ xếch dương (+2° đến +6°) tạo ánh nhìn Hunter Eyes quyến rũ; khoảng cách 2 mắt bằng 1 độ rộng mắt.",
            },
            {
                "id": "symmetry",
                "name": "Độ đối xứng khuôn mặt (Facial Symmetry)",
                "weight": "15%",
                "score1": m1["symmetry"]["score"],
                "score2": m2["symmetry"]["score"],
                "detail1": f"Độ lệch đối xứng: {m1['symmetry']['mean_diff_percent']}%",
                "detail2": f"Độ lệch đối xứng: {m2['symmetry']['mean_diff_percent']}%",
                "ideal": "Độ cân xứng giữa hai nửa mặt trái - phải tiệm cận 100% (chỉ số sinh học hấp dẫn di truyền).",
            },
            {
                "id": "rule_of_thirds",
                "name": "Tỷ lệ vàng 3 tầng mặt (Rule of Thirds - Vertical)",
                "weight": "15%",
                "score1": m1["rule_of_thirds"]["score"],
                "score2": m2["rule_of_thirds"]["score"],
                "detail1": f"Trán: {m1['rule_of_thirds']['upper_percent']}% | Mũi: {m1['rule_of_thirds']['mid_percent']}% | Cằm: {m1['rule_of_thirds']['lower_percent']}%",
                "detail2": f"Trán: {m2['rule_of_thirds']['upper_percent']}% | Mũi: {m2['rule_of_thirds']['mid_percent']}% | Cằm: {m2['rule_of_thirds']['lower_percent']}%",
                "ideal": "3 tầng mặt (trán - mũi - cằm) chia đều tỷ lệ 1:1:1 (33.3% mỗi tầng).",
            },
            {
                "id": "rule_of_fifths",
                "name": "Tỷ lệ chiều ngang 5 phần & Gò má (Rule of Fifths & Bizygomatic)",
                "weight": "15%",
                "score1": m1["rule_of_fifths"]["score"],
                "score2": m2["rule_of_fifths"]["score"],
                "detail1": f"Tỷ lệ dài / rộng mặt: {m1['rule_of_fifths']['height_width_ratio']}",
                "detail2": f"Tỷ lệ dài / rộng mặt: {m2['rule_of_fifths']['height_width_ratio']}",
                "ideal": "Tỷ lệ chiều dài / rộng mặt chuẩn nam tính là 1.35 - 1.45 (gương mặt góc cạnh nam tính).",
            },
            {
                "id": "nose_lips",
                "name": "Tỷ lệ Mũi & Môi (Nose & Lips Harmony)",
                "weight": "10%",
                "score1": m1["nose_lips"]["score"],
                "score2": m2["nose_lips"]["score"],
                "detail1": f"Tỷ lệ mũi/mắt: {m1['nose_lips']['nose_eye_ratio']} | Tỷ lệ môi trên/dưới: {m1['nose_lips']['lip_ratio']}",
                "detail2": f"Tỷ lệ mũi/mắt: {m2['nose_lips']['nose_eye_ratio']} | Tỷ lệ môi trên/dưới: {m2['nose_lips']['lip_ratio']}",
                "ideal": "Chiều rộng cánh mũi bằng khoảng cách 2 mắt; môi dưới dày hơn môi trên tỷ lệ 1:1.5.",
            },
            {
                "id": "chin_lower_face",
                "name": "Độ nhô cằm & Tầng mặt dưới (Chin Prominence)",
                "weight": "10%",
                "score1": m1["chin_lower_face"]["score"],
                "score2": m2["chin_lower_face"]["score"],
                "detail1": f"Cằm chiếm {m1['chin_lower_face']['chin_ratio_percent']}% tầng dưới",
                "detail2": f"Cằm chiếm {m2['chin_lower_face']['chin_ratio_percent']}% tầng dưới",
                "ideal": "Cằm vuông vắn, chiếm 62% - 68% tầng mặt dưới tạo nét cương nghị, quyền lực.",
            },
        ]

        # Generate comparative verdict for each criterion
        comparisons = []
        person1_wins = 0
        person2_wins = 0
        
        for c in criteria_list:
            diff = round(abs(c["score1"] - c["score2"]), 1)
            if c["score1"] > c["score2"]:
                winner = 1
                person1_wins += 1
                reason = f"Ảnh 1 vượt trội hơn (+{diff} điểm) nhờ các chỉ số tiệm cận chuẩn thẩm mỹ quốc tế hơn ({c['detail1']} so với {c['detail2']})."
            elif c["score2"] > c["score1"]:
                winner = 2
                person2_wins += 1
                reason = f"Ảnh 2 vượt trội hơn (+{diff} điểm) nhờ các chỉ số tiệm cận chuẩn thẩm mỹ quốc tế hơn ({c['detail2']} so với {c['detail1']})."
            else:
                winner = 0
                reason = f"Cả hai ngang tài ngang sức ở tiêu chí này với cùng điểm số ({c['score1']})."
            
            comparisons.append({
                **c,
                "winner": winner,
                "diff": diff,
                "verdict": reason,
            })

        # Overall winner
        s1 = data1["overall_score"]
        s2 = data2["overall_score"]
        diff_overall = round(abs(s1 - s2), 1)
        
        if s1 > s2:
            overall_winner = 1
            winner_text = f"Ảnh 1 điển trai hơn tổng thể (+{diff_overall} điểm)"
            winner_sub = f"Ảnh 1 dẫn trước ở {person1_wins}/{len(criteria_list)} tiêu chí thẩm mỹ toàn cầu."
        elif s2 > s1:
            overall_winner = 2
            winner_text = f"Ảnh 2 điển trai hơn tổng thể (+{diff_overall} điểm)"
            winner_sub = f"Ảnh 2 dẫn trước ở {person2_wins}/{len(criteria_list)} tiêu chí thẩm mỹ toàn cầu."
        else:
            overall_winner = 0
            winner_text = "Hai gương mặt có độ điển trai tương đương nhau!"
            winner_sub = "Cả hai đều sở hữu những thế mạnh nhan sắc độc đáo và cân bằng."

        # Generate rich synthesis summary in Vietnamese
        top_strengths_1 = sorted([c for c in comparisons if c["winner"] == 1], key=lambda x: x["diff"], reverse=True)
        top_strengths_2 = sorted([c for c in comparisons if c["winner"] == 2], key=lambda x: x["diff"], reverse=True)

        summary_paragraphs = []
        if overall_winner == 1:
            summary_paragraphs.append(
                f"**Kết quả chung cuộc:** **Ảnh 1** giành chiến thắng với tổng điểm **{s1}/100** (Thang 10: **{data1['scale_10']}/10** - Phân hạng: *{data1['tier']['title']}*), vượt qua **Ảnh 2** đạt **{s2}/100** (Thang 10: **{data2['scale_10']}/10** - Phân hạng: *{data2['tier']['title']}*)."
            )
        elif overall_winner == 2:
            summary_paragraphs.append(
                f"**Kết quả chung cuộc:** **Ảnh 2** giành chiến thắng với tổng điểm **{s2}/100** (Thang 10: **{data2['scale_10']}/10** - Phân hạng: *{data2['tier']['title']}*), vượt qua **Ảnh 1** đạt **{s1}/100** (Thang 10: **{data1['scale_10']}/10** - Phân hạng: *{data1['tier']['title']}*)."
            )
        else:
            summary_paragraphs.append(
                f"**Kết quả chung cuộc:** Hai ứng viên hòa nhau với cùng tổng điểm **{s1}/100** (Thang 10: **{data1['scale_10']}/10**)."
            )

        if top_strengths_1:
            s_names = ", ".join([f"**{c['name'].split('(')[0].strip()}** (+{c['diff']}đ)" for c in top_strengths_1[:2]])
            summary_paragraphs.append(f"• **Điểm nổi bật của Ảnh 1:** Mạnh nhất ở các tiêu chí {s_names}.")
        if top_strengths_2:
            s_names = ", ".join([f"**{c['name'].split('(')[0].strip()}** (+{c['diff']}đ)" for c in top_strengths_2[:2]])
            summary_paragraphs.append(f"• **Điểm nổi bật của Ảnh 2:** Mạnh nhất ở các tiêu chí {s_names}.")

        return {
            "overall_winner": overall_winner,
            "winner_text": winner_text,
            "winner_sub": winner_sub,
            "diff_overall": diff_overall,
            "score1": s1,
            "score2": s2,
            "scale10_1": data1["scale_10"],
            "scale10_2": data2["scale_10"],
            "tier1": data1["tier"],
            "tier2": data2["tier"],
            "comparisons": comparisons,
            "summary": "\n\n".join(summary_paragraphs),
        }
