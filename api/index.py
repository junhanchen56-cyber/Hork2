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
# --- HTML (修正版: 點擊輸入框直接彈出日曆 + 修復無法選取問題) ---
FRONTEND_HTML = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企業請假系統</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <style>
        /* 強制讓日曆圖示更明顯，且讓整個輸入框都可以點擊 */
        input[type="date"] {
            position: relative;
        }
        input[type="date"]::-webkit-calendar-picker-indicator {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
            color: transparent;
            background: transparent;
            cursor: pointer;
        }
    </style>
</head>
<body class="bg-gray-100 font-sans">
    <div id="app" class="min-h-screen flex justify-center p-5"></div>

    <script>
        const API_BASE = '/api';
        let user = null;
        let leaves = [];
        let view = 'login';
        const app = document.getElementById('app');

        async function api(url, method='GET', body=null) {
            try {
                const opts = { method, headers: { 'Content-Type': 'application/json' } };
                if (body) opts.body = JSON.stringify(body);
                const res = await fetch(API_BASE + url, opts);
                if (!res.ok) throw new Error('API Error');
                return res.status === 204 ? {} : await res.json();
            } catch (e) { alert('操作失敗: ' + e.message); return null; }
        }

        async function init() { render(); }

        function render() {
            app.innerHTML = '';
            if (!user) { renderLogin(); return; }
            
            const header = `
                <div class="w-full max-w-4xl">
                    <div class="flex justify-between items-center mb-6 bg-white p-4 rounded shadow">
                        <h1 class="text-xl font-bold flex items-center"><i class="fa-solid fa-calendar-check mr-2 text-blue-600"></i>請假系統</h1>
                        <div>
                            <span class="mr-4 text-gray-600">${user.name} (${user.role})</span>
                            <button onclick="logout()" class="text-red-500 hover:text-red-700 font-bold">登出</button>
                        </div>
                    </div>
                    <div id="content"></div>
                </div>`;
            app.innerHTML = header;
            
            if (user.role === 'student') renderStudent();
            else renderAdmin();
        }

        function renderLogin() {
            app.innerHTML = `
                <div class="bg-white p-8 rounded shadow-md w-96 mt-20 border-t-4 border-blue-600">
                    <h2 class="text-2xl font-bold mb-6 text-center">系統登入</h2>
                    <form onsubmit="handleLogin(event)">
                        <label class="block mb-1 text-sm text-gray-600">帳號</label>
                        <input type="text" name="acc" placeholder="12156208 / admin" class="w-full p-2 border mb-4 rounded focus:ring-2 ring-blue-500 outline-none" required>
                        <label class="block mb-1 text-sm text-gray-600">密碼</label>
                        <input type="password" name="pwd" placeholder="123 / admin" class="w-full p-2 border mb-6 rounded focus:ring-2 ring-blue-500 outline-none" required>
                        <button class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition font-bold">登入</button>
                    </form>
                </div>`;
        }

        async function handleLogin(e) {
            e.preventDefault();
            const acc = e.target.acc.value;
            const pwd = e.target.pwd.value;
            const res = await api('/login', 'POST', { account: acc, password: pwd });
            if (res && res.status === 'success') {
                user = { account: acc, name: res.name, role: res.role };
                if (user.role === 'student') await loadLeaves();
                if (user.role === 'admin') await loadAllLeaves();
                render();
            } else { alert('帳號密碼錯誤'); }
        }

        async function loadLeaves() { leaves = await api(`/leaves?student_id=${user.account}`); }
        async function loadAllLeaves() { leaves = await api('/leaves'); }

        function renderStudent() {
            const myLeaves = leaves.filter(l => l.student_id === user.account);
            document.getElementById('content').innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-6 rounded shadow h-fit border-l-4 border-orange-500">
                        <h3 class="text-lg font-bold mb-4 text-orange-600">申請假單</h3>
                        <form onsubmit="apply(event)">
                            <label class="block mb-2 font-medium">日期</label>
                            <input type="date" name="date" required onclick="this.showPicker()" class="w-full p-2 border rounded mb-4 cursor-pointer hover:bg-gray-50">
                            
                            <label class="block mb-2 font-medium">事由</label>
                            <textarea name="reason" required rows="3" class="w-full p-2 border rounded mb-4" placeholder="請填寫原因..."></textarea>
                            
                            <button class="w-full bg-orange-500 text-white p-2 rounded hover:bg-orange-600 font-bold">送出申請</button>
                        </form>
                    </div>
                    <div class="md:col-span-2 bg-white p-6 rounded shadow border-l-4 border-blue-500">
                        <h3 class="text-lg font-bold mb-4 text-blue-600">我的紀錄</h3>
                        ${tableHtml(myLeaves, false)}
                    </div>
                </div>`;
        }

        function renderAdmin() {
            document.getElementById('content').innerHTML = `
                <div class="bg-white p-6 rounded shadow border-t-4 border-green-500">
                    <h3 class="text-lg font-bold mb-4 text-green-600">假單審核</h3>
                    ${tableHtml(leaves, true)}
                </div>`;
        }

        function tableHtml(data, isAdmin) {
            if (!data.length) return '<p class="text-gray-500 py-4 text-center">目前無資料</p>';
            return `
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead><tr class="bg-gray-50 border-b">
                            <th class="p-3 whitespace-nowrap">ID</th>
                            ${isAdmin ? '<th class="p-3 whitespace-nowrap">學號</th>' : ''}
                            <th class="p-3 whitespace-nowrap">日期</th>
                            <th class="p-3 w-1/3">事由</th>
                            <th class="p-3 whitespace-nowrap">狀態</th>
                            ${isAdmin?'<th class="p-3 text-center whitespace-nowrap">操作</th>':''}
                        </tr></thead>
                        <tbody>${data.map(l => `
                            <tr class="border-b hover:bg-gray-50">
                                <td class="p-3 font-mono text-sm">${l.id}</td>
                                ${isAdmin ? `<td class="p-3 font-mono text-sm text-gray-600">${l.student_id}</td>` : ''}
                                <td class="p-3 whitespace-nowrap">${l.date}</td>
                                <td class="p-3 text-gray-700">${l.reason}</td>
                                <td class="p-3"><span class="px-2 py-1 rounded-full text-xs font-bold ${l.status==='Pending'?'bg-yellow-100 text-yellow-800':(l.status==='Approved'?'bg-green-100 text-green-800':'bg-red-100 text-red-800')}">${l.status}</span></td>
                                ${isAdmin && l.status === 'Pending' ? `
                                <td class="p-3 text-center">
                                    <button onclick="audit(${l.id}, 'Approved')" class="text-green-600 hover:text-green-800 mr-3 font-bold">批准</button>
                                    <button onclick="audit(${l.id}, 'Rejected')" class="text-red-600 hover:text-red-800 font-bold">拒絕</button>
                                </td>` : (isAdmin ? '<td class="p-3 text-center text-gray-400 text-sm">-</td>' : '')}
                            </tr>`).join('')}
                        </tbody>
                    </table>
                </div>`;
        }

        async function apply(e) {
            e.preventDefault();
            // 修正：使用 e.target.elements.date.value 確保抓取正確
            const dateVal = e.target.elements.date.value;
            const reasonVal = e.target.elements.reason.value;
            
            const res = await api('/apply', 'POST', { 
                student_id: user.account, 
                date: dateVal, 
                reason: reasonVal 
            });
            if (res) { await loadLeaves(); render(); }
        }

        async function audit(id, status) {
            if(!confirm('確定要執行此操作嗎?')) return;
            const res = await api('/audit', 'PATCH', { id, status });
            if (res) { await loadAllLeaves(); render(); }
        }
        function logout() { user = null; render(); }
        
        window.onload = init;
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
