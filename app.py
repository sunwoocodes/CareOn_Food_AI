import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import json
import cv2
import numpy as np
from ultralytics import YOLO

# 다크 모드 및 기본 테마 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class FoodAnalyzerGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("AI 음식 분석기")
        self.root.geometry("1400x950")
        self.root.minsize(900, 600)

        self.image_path = None
        
        # 💡 [핵심] 현재 이 파이썬 파일(app.py)이 실행되는 폴더의 절대 경로를 자동으로 가져옵니다.
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 미리 넣어둘 샘플 이미지 경로도 실행 위치 기준으로 변경 (필요 시 수정하여 사용)
        self.sample_images = {
            "샘플 1: 감자튀김": os.path.join(self.base_dir, "test_images", "side_기타튀김_배달종이박스_감자튀김(스틱형)_Q3_00008.jpg"),
            "샘플 2: 콩국수": os.path.join(self.base_dir, "test_images", "side_국물면류_원형배달_콩국수_Q5_00002.jpg"),
            "샘플 3: 순대볶음": os.path.join(self.base_dir, "test_images", "top_육류부피_사각배달_순대볶음_Q4_00001.jpg"),
            "샘플 4: 어묵볶음": os.path.join(self.base_dir, "test_images", "side_반찬부피_접시_어묵볶음_Q1_00007.jpg"),
            "샘플 5: 파전": os.path.join(self.base_dir, "test_images", "side_기타튀김_접시_새우튀김_Q2_00001.jpg")
        }
        
        # ==========================================
        # 모델 경로 설정 (os.path.join을 사용하여 상대 경로 적용)
        # ==========================================
        self.food_model_path = os.path.join(self.base_dir, "models", "food_detection_model.pt")
        self.ref_model_path = os.path.join(self.base_dir, "models", "Reference_detection_model.pt")
        
        # 파일 존재 여부를 체크하여 친절한 에러 메시지 띄우기
        if not os.path.exists(self.food_model_path) or not os.path.exists(self.ref_model_path):
            messagebox.showerror("모델 로드 실패", "models 폴더 내에 AI 모델(.pt) 파일이 존재하지 않습니다.\n폴더 구조를 확인해주세요.")
        
        self.food_model = YOLO(self.food_model_path)
        self.ref_model = YOLO(self.ref_model_path)

        # ==========================================
        # JSON 로드 설정 (상대 경로 적용)
        # ==========================================
        try:
            with open(os.path.join(self.base_dir, "json", "food_q4_reference.json"), encoding="utf-8") as f:
                self.food_q4 = json.load(f)

            with open(os.path.join(self.base_dir, "json", "category_q4_reference.json"), encoding="utf-8") as f:
                self.category_q4 = json.load(f)

            with open(os.path.join(self.base_dir, "json", "food_nutrition_db.json"), encoding="utf-8") as f:
                self.nutrition_db = json.load(f)
        except FileNotFoundError as e:
            messagebox.showerror("데이터베이스 로드 실패", f"json 폴더의 설정 파일을 찾을 수 없습니다.\n오류 내용: {e}")
            
        self.create_ui()

    def create_ui(self):
        self.root.grid_columnconfigure(0, weight=6)
        self.root.grid_columnconfigure(1, weight=4)
        self.root.grid_rowconfigure(1, weight=1)

        # 상단 타이틀
        title = ctk.CTkLabel(
            self.root,
            text="AI 음식 분석기",
            font=("맑은 고딕", 28, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(20, 10), sticky="n")

        # ==========================================
        # 1. 왼쪽 영역 (이미지 뷰어 및 제어부)
        # ==========================================
        left_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        left_frame.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nsew")

        # 이미지 표시 프레임
        self.image_frame = ctk.CTkFrame(left_frame, corner_radius=15, height=420)
        self.image_frame.pack(fill="both", expand=True, pady=(0, 15))
        self.image_frame.pack_propagate(False)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="📷\n이미지를 선택하거나\n리스트에서 골라주세요",
            font=("맑은 고딕", 18),
            text_color="gray50"
        )
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        # --- 하단 컨트롤 프레임 ---
        control_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        control_frame.pack(fill="x")

        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))

        self.select_btn = ctk.CTkButton(
            btn_frame,
            text="PC에서 이미지 직접 선택",
            font=("맑은 고딕", 15, "bold"),
            height=45,
            command=self.select_image_from_pc
        )
        self.select_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.analyze_btn = ctk.CTkButton(
            btn_frame,
            text="AI 분석 시작",
            font=("맑은 고딕", 15, "bold"),
            height=45,
            fg_color="#2FA572",
            hover_color="#1D7850",
            command=self.analyze
        )
        self.analyze_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        list_label = ctk.CTkLabel(control_frame, text="▼ 샘플 이미지 리스트", font=("맑은 고딕", 14, "bold"))
        list_label.pack(anchor="w", pady=(5, 5))

        self.sample_list_frame = ctk.CTkScrollableFrame(control_frame, height=120, corner_radius=10)
        self.sample_list_frame.pack(fill="x")

        self.sample_var = ctk.StringVar(value="")

        for name in self.sample_images.keys():
            rb = ctk.CTkRadioButton(
                self.sample_list_frame,
                text=name,
                variable=self.sample_var,
                value=name,
                font=("맑은 고딕", 14),
                command=self.select_image_from_list
            )
            rb.pack(anchor="w", pady=6, padx=10)

        # ==========================================
        # 2. 오른쪽 영역 (분석 결과 및 영양 정보)
        # ==========================================
        right_frame = ctk.CTkFrame(self.root)
        right_frame.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="nsew")

        info_title = ctk.CTkLabel(right_frame, text="📋 분석 요약", font=("맑은 고딕", 18, "bold"))
        info_title.pack(anchor="w", padx=20, pady=(20, 10))

        info_bg = ctk.CTkFrame(right_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        info_bg.pack(fill="x", padx=20, pady=(0, 20))

        self.food_label = ctk.CTkLabel(info_bg, text="음식명 : -", font=("맑은 고딕", 15))
        self.food_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.reference_label = ctk.CTkLabel(info_bg, text="기준물 : -", font=("맑은 고딕", 15))
        self.reference_label.pack(anchor="w", padx=15, pady=5)

        self.portion_label = ctk.CTkLabel(info_bg, text="인분수 : -", font=("맑은 고딕", 15))
        self.portion_label.pack(anchor="w", padx=15, pady=5)

        self.weight_label = ctk.CTkLabel(info_bg, text="예상 중량 : -", font=("맑은 고딕", 15))
        self.weight_label.pack(anchor="w", padx=15, pady=(5, 15))

        nutri_title = ctk.CTkLabel(right_frame, text="📊 상세 영양 성분", font=("맑은 고딕", 18, "bold"))
        nutri_title.pack(anchor="w", padx=20, pady=(0, 10))

        self.nutrition_text = ctk.CTkTextbox(
            right_frame,
            font=("맑은 고딕", 15),
            corner_radius=10,
            fg_color=("gray85", "gray20"),
            border_width=1,
            border_color="gray30"
        )
        self.nutrition_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def select_image_from_pc(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.JPG *.JPEG")]
        )
        if path:
            self.image_path = path
            self.display_image(path)
            self.sample_var.set("")

    def select_image_from_list(self):
        choice = self.sample_var.get()
        path = self.sample_images.get(choice)
        
        if path:
            if os.path.exists(path):
                self.image_path = path
                self.display_image(path)
            else:
                self.sample_var.set("")
                messagebox.showerror("파일 오류", f"'{os.path.basename(path)}' 파일을 찾을 수 없습니다.\n지정된 폴더 구조를 확인해주세요.")

    def display_image(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((600, 420), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image
        except Exception as e:
            messagebox.showerror("오류", f"이미지를 불러오는 중 오류가 발생했습니다: {e}")

    def analyze(self):
        if self.image_path is None:
            messagebox.showwarning("경고", "먼저 이미지를 선택해주세요!")
            return

        try:
            food_result = self.food_model(self.image_path, verbose=False)[0]

            if len(food_result.boxes) == 0:
                messagebox.showerror("오류", "음식을 찾지 못했습니다.")
                return

            food_box = max(food_result.boxes, key=lambda x: float(x.conf[0]))
            food_code = food_result.names[int(food_box.cls[0])]
            food_conf = float(food_box.conf[0])
            fx1, fy1, fx2, fy2 = food_box.xyxy[0].cpu().numpy()
            food_area_px = (fx2 - fx1) * (fy2 - fy1)

            ref_result = self.ref_model(self.image_path, verbose=False)[0]

            if len(ref_result.boxes) == 0:
                messagebox.showerror("오류", "기준물을 찾지 못했습니다.")
                return

            ref_box = max(ref_result.boxes, key=lambda x: float(x.conf[0]))
            ref_cls = int(ref_box.cls[0])
            ref_name = ref_result.names[ref_cls]
            ref_conf = float(ref_box.conf[0])
            ux1, uy1, ux2, uy2 = ref_box.xyxy[0].cpu().numpy()
            utensil_area_px = (ux2 - ux1) * (uy2 - uy1)

            ratio = food_area_px / utensil_area_px
            food_info = self.nutrition_db.get(food_code, None)

            if food_info is None:
                messagebox.showerror("오류", f"{food_code} 영양정보 없음")
                return

            food_name = food_info.get("name", food_code)
            q4_ratio = self.food_q4.get(food_name, None)

            if q4_ratio is None:
                amount_scale = 1.0
            else:
                amount_scale = ratio / q4_ratio

            # ==========================
            # 중량 및 영양성분 비례 계산 (None값 안전 처리 적용)
            # ==========================
            # JSON에서 값이 null(None)로 올 경우 0으로 안전하게 변환하는 헬퍼 함수
            def get_nutri(key, default_val=0):
                val = food_info.get(key)
                return val if val is not None else default_val

            base_weight = get_nutri("base_weight_g", 100)
            weight_g = base_weight * amount_scale

            kcal = get_nutri("kcal") * amount_scale
            carb = get_nutri("carb_g") * amount_scale
            protein = get_nutri("protein_g") * amount_scale
            fat = get_nutri("fat_g") * amount_scale
            sodium = get_nutri("natrium_mg") * amount_scale
            sugar = get_nutri("sugar_g") * amount_scale
            calcium = get_nutri("calcium_mg") * amount_scale
            potassium = get_nutri("potassium_mg") * amount_scale
            magnesium = get_nutri("magnesium_mg") * amount_scale
            phosphorus = get_nutri("phosphorus_mg") * amount_scale
            iron = get_nutri("iron_mg") * amount_scale
            zinc = get_nutri("zinc_mg") * amount_scale
            cholesterol = get_nutri("cholesterol_mg") * amount_scale
            transfat = get_nutri("transfat_g") * amount_scale

            img_array = np.fromfile(self.image_path, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            cv2.rectangle(img, (int(fx1), int(fy1)), (int(fx2), int(fy2)), (0, 255, 0), 3)
            cv2.putText(img, food_name, (int(fx1), int(fy1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.rectangle(img, (int(ux1), int(uy1)), (int(ux2), int(uy2)), (255, 0, 0), 3)
            cv2.putText(img, ref_name, (int(ux1), int(uy1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # 결과 임시 이미지도 상대 경로(실행 폴더 내)로 안전하게 생성
            temp_path = os.path.join(self.base_dir, "temp_result.jpg")
            result, encoded_img = cv2.imencode('.jpg', img)
            if result:
                with open(temp_path, mode='wb') as f:
                    encoded_img.tofile(f)
                self.display_image(temp_path)

            self.food_label.configure(text=f"음식명 : {food_name}")
            self.reference_label.configure(text=f"기준물 : {ref_name}")
            self.portion_label.configure(text=f"인분수 : {amount_scale:.2f}")
            self.weight_label.configure(text=f"예상 중량 : {weight_g:.1f} g")

            self.nutrition_text.delete("1.0", "end")
            self.nutrition_text.insert(
                "end",
                f"""[ AI 분석 완료 ]

음식명 : {food_name}

음식 신뢰도 : {food_conf:.2%}
기준물 신뢰도 : {ref_conf:.2%}

ratio : {ratio:.2f}
Q4 기준 : {q4_ratio}
인분수 : {amount_scale:.2f}
예상 중량 : {weight_g:.1f} g

🔥 열량 : {kcal:.1f} kcal
🍚 탄수화물 : {carb:.1f} g
🍗 단백질 : {protein:.1f} g
🥑 지방 : {fat:.1f} g
🧂 나트륨 : {sodium:.1f} mg
🍬 당류 : {sugar:.1f} g
🦴 칼슘 : {calcium:.1f} mg
🍌 칼륨 : {potassium:.1f} mg
🌱 마그네슘 : {magnesium:.1f} mg
🐟 인 : {phosphorus:.1f} mg
🩸 철 : {iron:.1f} mg
💪 아연 : {zinc:.1f} mg
🍳 콜레스테롤 : {cholesterol:.1f} mg
🍟 트랜스지방 : {transfat:.1f} g

"""
            )

        except Exception as e:
            messagebox.showerror("오류", str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FoodAnalyzerGUI()
    app.run()