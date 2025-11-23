from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json

# 初始化 Flask App
app = Flask(__name__)
CORS(app) 

# --- 模擬資料庫 (Mock Database) ---
# 實際專案中，這裡應該連接資料庫 (如 Firestore 或 PostgreSQL)
users = {
    "12156208": {"pwd": "123", "name": "王小明", "role": "student"},
    "admin": {"pwd": "admin", "name": "系統管理員", "role": "admin"}
}

leaves = [
    {"id": 1, "student_id": "12156208", "date": "2023-12-01", "reason": "病假", "status": "Pending"},
    {"id": 2, "student_id": "12156231", "date": "2023-12-05", "reason": "事假", "status": "Approved"}
]
next_leave_id = 3

# --- HTML/JavaScript 前端程式碼 (作為 Python 字串) ---
# 注意：前端 JS 中的 API_BASE_PATH 設置為 /api，指向下面的 Flask 路由
# --- 已修正 JS 語法錯誤的 HTML ---
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企業請假系統 - 前後端整合版</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
        .main-container { min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 20px; }
    </style>
    <script>
        tailwind.config = { theme: { extend: { colors: { 'primary': '#1e40af', 'secondary': '#f97316', 'success': '#10b981', 'danger': '#ef4444', } } } }
    </script>
</head>
<body>
    <div id="app" class="main-container w-full"></div>
    <div id="message-modal" class="hidden fixed inset-0 z-50 overflow-y-auto bg-gray-900 bg-opacity-50 flex items-center justify-center transition-opacity duration-300">
        <div class="bg-white rounded-xl shadow-2xl p-6 w-11/12 max-w-sm transform transition-transform duration-300 scale-95">
            <h3 id="modal-title" class="text-xl font-bold mb-3 text-primary">訊息</h3>
            <p id="modal-body" class="text-gray-700 mb-4"></p>
            <button onclick="closeModal()" class="w-full bg-primary hover:bg-blue-800 text-white font-semibold py-2 rounded-lg transition duration-150">確定</button>
        </div>
    </div>
    <script>
        const API_BASE_PATH = '/api'; 
        let currentUser = null; 
        let leavesData = [];
        let currentView = 'login';
        const app = document.getElementById('app');

        function showModal(title, body) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-body').textContent = body;
            document.getElementById('message-modal').classList.remove('hidden');
            document.querySelector('#message-modal > div').classList.add('scale-100');
        }
        function closeModal() {
            document.querySelector('#message-modal > div').classList.remove('scale-100');
            document.getElementById('message-modal').classList.add('hidden');
        }
        async function apiFetch(endpoint, method = 'GET', data = null) {
            const url = `${API_BASE_PATH}${endpoint}`;
            const options = { method: method, headers: { 'Content-Type': 'application/json', } };
            if (data) { options.body = JSON.stringify(data); }
            try {
                const response = await fetch(url, options);
                if (!response.ok) throw new Error('API 請求失敗');
                if (response.status === 204 || response.headers.get("Content-Length") === "0") return { status: "success" };
                return response.json();
            } catch (error) {
                console.error('API Error:', error);
                showModal('錯誤', '無法連線到伺服器');
                return null;
            }
        }
        async function fetchLeaves() {
            let endpoint = '/leaves';
            if (currentUser.role === 'student') endpoint += `?student_id=${currentUser.account}`;
            const data = await apiFetch(endpoint);
            if (data) { leavesData = data; render(); }
        }
        function render() {
            if (!currentUser && currentView !== 'login') currentView = 'login';
            app.innerHTML = '';
            let htmlContent = '';
            switch (currentView) {
                case 'login': htmlContent = renderLogin(); break;
                case 'student': htmlContent = renderStudentDashboard(); break;
                case 'admin': htmlContent = renderAdminDashboard(); break;
                default: htmlContent = renderLogin();
            }
            app.innerHTML = `
                <div class="w-full max-w-4xl pt-8">
                    <header class="mb-8 p-4 bg-white shadow-lg rounded-xl flex justify-between items-center flex-wrap">
                        <h1 class="text-2xl font-extrabold text-primary flex items-center"><i class="fa-solid fa-list-check mr-3 text-secondary"></i>企業請假系統</h1>
                        ${currentUser ? `
                            <div class="mt-2 sm:mt-0 text-sm font-medium text-gray-700">
                                歡迎, <span class="text-primary">${currentUser.name} (${currentUser.role === 'admin' ? '主管' : '學生'})</span>
                                <button onclick="logout()" class="ml-4 text-danger hover:text-red-700 transition duration-150"><i class="fa-solid fa-right-from-bracket"></i> 登出</button>
                            </div>
                        ` : ''}
                    </header>
                    <main id="dashboard-content">${htmlContent}</main>
                </div>
            `;
            if (currentUser && currentView !== 'login') fetchLeaves();
        }
        function renderLogin() {
            return `
                <div class="bg-white p-8 md:p-12 rounded-xl shadow-2xl w-full max-w-md mx-auto mt-10 border-t-4 border-primary">
                    <h2 class="text-3xl font-bold mb-6 text-center text-gray-800">系統登入</h2>
                    <form onsubmit="handleLogin(event)">
                        <div class="mb-6"><label class="block text-sm font-medium text-gray-700 mb-1">帳號</label><input type="text" name="account" placeholder="12156208 或 admin" required class="w-full px-4 py-2 border border-gray-300 rounded-lg"></div>
                        <div class="mb-8"><label class="block text-sm font-medium text-gray-700 mb-1">密碼</label><input type="password" name="password" placeholder="123 或 admin" required class="w-full px-4 py-2 border border-gray-300 rounded-lg"></div>
                        <button type="submit" class="w-full bg-primary hover:bg-blue-800 text-white font-bold py-3 rounded-lg transition duration-200 shadow-md">登入系統</button>
                    </form>
                </div>
            `;
        }
        function renderStudentDashboard() {
            const studentLeaves = leavesData.filter(l => l.student_id === currentUser.account);
            return `
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-1 bg-white p-6 rounded-xl shadow-lg border-l-4 border-secondary h-min">
                        <h3 class="text-xl font-bold text-secondary mb-4">申請請假</h3>
                        <form onsubmit="handleApply(event)">
                            <input type="hidden" id="student_id" value="${currentUser.account}">
                            <div class="mb-4"><label class="block text-sm font-medium text-gray-700 mb-1">日期</label><input type="date" id="date" required class="w-full px-3 py-2 border rounded-lg"></div>
                            <div class="mb-6"><label class="block text-sm font-medium text-gray-700 mb-1">事由</label><textarea id="reason" rows="3" required class="w-full px-3 py-2 border rounded-lg"></textarea></div>
                            <button type="submit" class="w-full bg-secondary hover:bg-orange-700 text-white font-bold py-2 rounded-lg">提交申請</button>
                        </form>
                    </div>
                    <div class="lg:col-span-2 bg-white p-6 rounded-xl shadow-lg border-l-4 border-primary">
                        <h3 class="text-xl font-bold text-primary mb-4">我的請假記錄</h3>
                        ${renderLeavesTable(studentLeaves, 'student')}
                    </div>
                </div>
            `;
        }
        function renderAdminDashboard() {
            return `
                <div class="bg-white p-6 rounded-xl shadow-2xl border-t-4 border-success">
                    <h3 class="text-2xl font-bold text-success mb-4">主管審核中心</h3>
                    ${renderLeavesTable(leavesData, 'admin')}
                </div>
            `;
        }
        function renderLeavesTable(data, role) {
            if (data.length === 0) return `<p class="text-gray-500 text-center py-10">目前沒有記錄。</p>`;
            return `
                <div class="overflow-x-auto"><table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50"><tr><th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th><th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th><th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">狀態</th>${role==='admin'?'<th class="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase">操作</th>':''}</tr></thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${data.map(leave => `
                            <tr>
                                <td class="px-3 py-4 text-sm font-medium text-gray-900">${leave.id}</td>
                                <td class="px-3 py-4 text-sm text-gray-900">${leave.date} (${leave.reason})</td>
                                <td class="px-3 py-4"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${leave.status==='Pending'?'bg-yellow-100 text-yellow-800':(leave.status==='Approved'?'bg-success text-white':'bg-danger text-white')}">${leave.status}</span></td>
                                ${role === 'admin' && leave.status === 'Pending' ? `
                                    <td class="px-3 py-4 text-center text-sm font-medium">
                                        <button onclick="handleAudit(${leave.id}, 'Approved')" class="text-success hover:text-green-700 mr-2">批准</button>
                                        <button onclick="handleAudit(${leave.id}, 'Rejected')" class="text-danger hover:text-red-700">拒絕</button>
                                    </td>
                                ` : (role === 'admin' ? '<td class="text-center">-</td>' : '')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table></div>
            `;
        }
        async function handleLogin(e) {
            e.preventDefault();
            const res = await apiFetch('/login', 'POST', { account: e.target.account.value, password: e.target.password.value });
            if (res && res.status === 'success') {
                currentUser = { account: e.target.account.value, name: res.name, role: res.role };
                currentView = res.role;
                render();
            } else { showModal('錯誤', '帳號或密碼錯誤'); }
        }
        async function handleApply(e) {
            e.preventDefault();
            const res = await apiFetch('/apply', 'POST', { student_id: currentUser.account, date: e.target.date.value, reason: e.target.reason.value });
            if (res && res.status === 'success') { showModal('成功', '假單已送出'); fetchLeaves(); }
        }
        async function handleAudit(id, status) {
            if (!confirm('確定嗎？')) return;
            const res = await apiFetch('/audit', 'PATCH', { id, status });
            if (res && res.status === 'success') fetchLeaves();
        }
        function logout() { currentUser = null; currentView = 'login'; render(); }
        window.onload = render;
    </script>
</body>
</html>
"""

# --- 核心 API 路由 ---

# 1. 前端渲染路由 (處理根路徑 /)
@app.route('/')
def home():
    # 返回包含整個前端 UI 的 HTML 字串
    # Vercel 接收到 / 請求時，會執行此函式並返回 HTML
    return Response(FRONTEND_HTML, mimetype='text/html')

# 2. 登入 API (/api/login)
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
            "token": f"mock-token-{account}"
        }), 200
    else:
        return jsonify({"status": "error", "message": "帳號或密碼錯誤"}), 401

# 3. 取得假單列表 API (/api/leaves)
@app.route('/api/leaves', methods=['GET'])
def get_leaves():
    student_id = request.args.get('student_id')
    
    # 這裡需要對 leaves 進行深拷貝以避免並發問題（在 Vercel Serverless 環境下不一定必要，但好習慣）
    current_leaves = json.loads(json.dumps(leaves))

    if student_id:
        student_leaves = [l for l in current_leaves if l['student_id'] == student_id]
        return jsonify(student_leaves), 200
    else:
        return jsonify(current_leaves), 200

# 4. 申請請假 API (/api/apply)
@app.route('/api/apply', methods=['POST'])
def apply_leave():
    global next_leave_id, leaves
    data = request.json
    
    if not all(k in data for k in ['student_id', 'date', 'reason']):
        return jsonify({"status": "error", "message": "缺少必要的欄位"}), 400
        
    new_leave = {
        "id": next_leave_id,
        "student_id": data['student_id'],
        "date": data['date'],
        "reason": data['reason'],
        "status": "Pending" 
    }
    leaves.append(new_leave)
    next_leave_id += 1
    return jsonify({"status": "success", "message": "假單已送出", "data": new_leave}), 201

# 5. 主管審核 API (/api/audit)
@app.route('/api/audit', methods=['PATCH'])
def audit_leave():
    data = request.json
    leave_id = data.get('id')
    new_status = data.get('status') 

    for leave in leaves:
        if leave['id'] == leave_id:
            leave['status'] = new_status
            return jsonify({"status": "success", "message": f"假單 ID:{leave_id} 已更新為 {new_status}"}), 200
            
    return jsonify({"status": "error", "message": "找不到該假單"}), 404
