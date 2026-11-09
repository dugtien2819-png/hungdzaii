import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from handsome_app.analyzer import HandsomeFaceAnalyzer

app = FastAPI(title="Male Handsome & Aesthetic Comparator API", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_landmarker.task")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Face Analyzer
analyzer = HandsomeFaceAnalyzer(model_path=MODEL_PATH)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Trang web đang được khởi tạo...</h1>")


@app.post("/api/compare")
async def compare_photos(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    try:
        content1 = await file1.read()
        content2 = await file2.read()

        if len(content1) == 0 or len(content2) == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Một trong hai tệp ảnh tải lên bị rỗng. Vui lòng thử lại."}
            )

        pts1, img1 = analyzer.extract_landmarks(content1)
        if pts1 is None:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "Không tìm thấy khuôn mặt rõ nét trong Ảnh 1. Vui lòng chọn ảnh chụp góc chính diện, rõ nét và đủ sáng."
                }
            )

        pts2, img2 = analyzer.extract_landmarks(content2)
        if pts2 is None:
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "Không tìm thấy khuôn mặt rõ nét trong Ảnh 2. Vui lòng chọn ảnh chụp góc chính diện, rõ nét và đủ sáng."
                }
            )

        d1 = analyzer.analyze_face(pts1, img1)
        d2 = analyzer.analyze_face(pts2, img2)
        comparison = analyzer.compare(d1, d2)

        annotated1 = analyzer.draw_annotated_image(img1, pts1)
        annotated2 = analyzer.draw_annotated_image(img2, pts2)

        return {
            "success": True,
            "data": comparison,
            "annotated1": annotated1,
            "annotated2": annotated2
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Lỗi hệ thống khi phân tích hình ảnh: {str(e)}"}
        )


@app.post("/api/compare-samples")
async def compare_samples():
    try:
        sample1_path = os.path.join(STATIC_DIR, "images", "sample1.jpg")
        sample2_path = os.path.join(STATIC_DIR, "images", "sample2.jpg")

        if not os.path.exists(sample1_path) or not os.path.exists(sample2_path):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Ảnh mẫu chưa sẵn sàng."}
            )

        with open(sample1_path, "rb") as f1, open(sample2_path, "rb") as f2:
            content1 = f1.read()
            content2 = f2.read()

        pts1, img1 = analyzer.extract_landmarks(content1)
        pts2, img2 = analyzer.extract_landmarks(content2)

        d1 = analyzer.analyze_face(pts1, img1)
        d2 = analyzer.analyze_face(pts2, img2)
        comparison = analyzer.compare(d1, d2)

        annotated1 = analyzer.draw_annotated_image(img1, pts1)
        annotated2 = analyzer.draw_annotated_image(img2, pts2)

        return {
            "success": True,
            "data": comparison,
            "annotated1": annotated1,
            "annotated2": annotated2
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Lỗi khi so sánh ảnh mẫu: {str(e)}"}
        )


if __name__ == "__main__":
    uvicorn.run("handsome_app.main:app", host="127.0.0.1", port=8000, reload=True)
