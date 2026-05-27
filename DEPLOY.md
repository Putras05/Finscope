# Hướng dẫn đưa app lên GitHub + Streamlit Cloud

> Code đã được commit sẵn trong git ở thư mục `D:\App_DuBao_AI`.
> Bạn chỉ cần làm 2 phần: (A) đẩy lên GitHub, (B) bấm deploy trên Streamlit Cloud.

## A. Đẩy lên GitHub

### 1. Tạo repo rỗng trên GitHub
- Vào https://github.com/new
- Đặt tên, ví dụ: **`app-dubao-ai`** (Public hoặc Private đều được).
- **KHÔNG** tích "Add a README / .gitignore / license" (để repo rỗng, tránh xung đột).
- Bấm **Create repository** → copy URL repo, ví dụ:
  `https://github.com/<tên-bạn>/app-dubao-ai.git`

### 2. Mở PowerShell tại thư mục app và push
```powershell
cd D:\App_DuBao_AI
git remote add origin https://github.com/<tên-bạn>/app-dubao-ai.git
git branch -M main
git push -u origin main
```
- Lần đầu push, GitHub sẽ yêu cầu đăng nhập (trình duyệt hoặc Personal Access Token).
- Nếu báo "remote origin already exists": chạy `git remote set-url origin <URL>` rồi push lại.

## B. Deploy lên Streamlit Community Cloud (miễn phí)

1. Vào **https://share.streamlit.io** → đăng nhập bằng tài khoản GitHub.
2. Bấm **Create app** → **Deploy a public app from GitHub**.
3. Điền:
   - **Repository:** `<tên-bạn>/app-dubao-ai`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Bấm **Deploy**. Lần đầu mất ~3–5 phút để cài thư viện (statsmodels, arch, vnstock...).
5. Xong → bạn nhận link dạng:
   `https://<tên-bạn>-app-dubao-ai-xxxx.streamlit.app`

> **Không cần khai báo Secrets** — app không còn dùng chatbot/API key.

## Cập nhật về sau
Mỗi lần sửa code:
```powershell
cd D:\App_DuBao_AI
git add -A
git commit -m "cập nhật ..."
git push
```
Streamlit Cloud tự động deploy lại khi repo `main` có commit mới.

## Lưu ý
- Nguồn dữ liệu **vnstock** miễn phí giới hạn ~20 request/phút. Trên cloud nếu
  nhiều người dùng cùng lúc có thể gặp giới hạn — app sẽ hiện thông báo chờ.
- File `requirements.txt` đã ghim phiên bản; nếu cloud lỗi cài `arch`, đổi dòng
  `arch==8.0.0` thành `arch` (bản mới nhất).
