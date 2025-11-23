from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
# 允許跨域請求，這很重要，因為您的前端在 Vercel 網域，後端也在 Vercel，但視為不同源
CORS(app) 

# --- 模擬資料庫 (Mock Database) ---
# 在實際專案中，這裡應該替換成連接 MySQL, PostgreSQL 或 Firebase
users = {
    "12156208": {"pwd": "123", "name": "王小明", "role": "student"},
    "admin": {"pwd": "admin", "name": "系統管理員", "role": "admin"}
}

leaves = [
    {"id": 1, "student_id": "12156208", "date": "2023-12-01", "reason": "病假", "status": "Pending"},
    {"id": 2, "student_id": "12156231", "date": "2023-12-05", "reason": "事假", "status": "Approved"}
]

# --- 路由與功能 ---

@app.route('/')
def home():
    return "Group 1 Leave System Backend is Running!"

# 1. 登入 API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    account = data.get('account')
    password = data.get('password')

    user = users.get(account)
    
    if user and user['pwd'] == password:
        return jsonify({
            "status": "success", 
            "message": "登入成功",
            "role": user['role'],
            "name": user['name'],
            "token": f"mock-token-{account}" # 實際專案請用 JWT
        }), 200
    else:
        return jsonify({"status": "error", "message": "帳號或密碼錯誤"}), 401

# 2. 取得假單列表 API (GET)
@app.route('/api/leaves', methods=['GET'])
def get_leaves():
    # 實際專案應檢查 Header 中的 Token
    student_id = request.args.get('student_id')
    
    if student_id:
        # 如果有傳學號，只回傳該學生的假單
        student_leaves = [l for l in leaves if l['student_id'] == student_id]
        return jsonify(student_leaves), 200
    else:
        # 如果沒傳學號 (通常是 Admin)，回傳全部
        return jsonify(leaves), 200

# 3. 申請請假 API (POST)
@app.route('/api/apply', methods=['POST'])
def apply_leave():
    data = request.json
    new_leave = {
        "id": len(leaves) + 1,
        "student_id": data.get('student_id'),
        "date": data.get('date'),
        "reason": data.get('reason'),
        "status": "Pending" # 預設為待審核
    }
    leaves.append(new_leave)
    return jsonify({"status": "success", "message": "假單已送出", "data": new_leave}), 201

# 4. 主管審核 API (PATCH)
@app.route('/api/audit', methods=['PATCH'])
def audit_leave():
    data = request.json
    leave_id = data.get('id')
    new_status = data.get('status') # 'Approved' or 'Rejected'

    for leave in leaves:
        if leave['id'] == leave_id:
            leave['status'] = new_status
            return jsonify({"status": "success", "message": f"假單已更新為 {new_status}"}), 200
            
    return jsonify({"status": "error", "message": "找不到該假單"}), 404

# 為了讓 Vercel 能夠執行
if __name__ == '__main__':
    app.run()