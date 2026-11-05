# StudyMate AI

Trợ lý học tập thông minh sử dụng React, FastAPI, SQLite/PostgreSQL và Google Gemini.

## Tính năng

- Đăng ký, đăng nhập và đăng xuất bằng JWT.
- Mật khẩu được băm trước khi lưu vào cơ sở dữ liệu.
- Chat với AI qua Gemini API.
- Lưu và xem lại lịch sử trò chuyện theo từng tài khoản.
- Xóa lịch sử trò chuyện.
- Giao diện responsive, hỗ trợ máy tính và điện thoại.

## Cấu trúc

```
studymate-ai/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── style.css
├── .env.example
└── README.md
```

## 1. Chạy backend

Yêu cầu Python 3.10+.

```bash
cd backend
python -m venv .venv
```

Windows:
```bat
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Cài thư viện và chạy:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend chạy tại http://localhost:8000. Tài liệu API: http://localhost:8000/docs.

## 2. Chạy frontend

Mở terminal khác:

```bash
cd frontend
npm install
npm run dev
```

Mở URL Vite hiển thị trong terminal (thường là http://localhost:5173).

Nếu backend không chạy ở localhost:8000, tạo file `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Sau khi sửa biến môi trường Vite, khởi động lại frontend.

## 3. Bật Gemini AI

Tạo API key trong Google AI Studio: https://aistudio.google.com/app/apikey

Đặt biến môi trường `GEMINI_API_KEY` trong môi trường chạy backend. Không đưa API key vào React, không commit key lên GitHub. Khi chưa cấu hình key, ứng dụng vẫn chạy được luồng tài khoản và giao diện chat nhưng backend trả về thông báo hướng dẫn cấu hình.

Có thể đổi model bằng biến `GEMINI_MODEL`.

## 4. Triển khai công khai

### Backend (Render hoặc dịch vụ tương đương)

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment: `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `DATABASE_URL`, `FRONTEND_ORIGIN`.
- Dùng PostgreSQL được cấp bởi nhà cung cấp và đặt `DATABASE_URL` theo định dạng PostgreSQL. Không dùng SQLite tạm thời cho dữ liệu production trên filesystem không bền vững.

### Frontend (Vercel hoặc Netlify)

- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variable: `VITE_API_URL=https://<backend-domain>`

Sau khi có domain frontend, cập nhật `FRONTEND_ORIGIN` ở backend đúng domain đó (không có dấu / cuối), rồi redeploy backend.

## Lưu ý bảo mật

- Thay `SECRET_KEY` bằng chuỗi ngẫu nhiên dài khi triển khai.
- Không commit file .env hoặc API key.
- Chỉ dùng HTTPS trên môi trường công khai.
- Đây là phiên bản đồ án/MVP; trước khi dùng thực tế cần bổ sung giới hạn tần suất, xác minh email, chính sách quyền riêng tư, quản lý refresh token và kiểm thử bảo mật.
