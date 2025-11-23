from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# --- Mock Data ---
users = {
    "12156208": {"pwd": "123", "name": "王小明", "role": "student"},
    "admin": {"pwd": "admin", "name": "系統管理員", "role": "admin"}
}

leaves = [
    {"id": 1, "student_id": "12156208", "date": "2023-12-01", "reason": "病假", "status": "Pending"},
    {"id": 2, "student_id": "12156231", "date": "2023-12-05", "reason": "事假", "status": "Approved"}
]
next_leave_id = 3

# --- HTML (修正版: 移除可能導致 SyntaxError 的字元) ---
# 注意：為了避免 Python f-string 衝突，這裡不使用 f-string，改用純字串
FRONTEND_HTML = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企業請假系統</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
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
                        <h1 class="text-xl font-bold">請假系統</h1>
                        <div>
                            <span class="mr-4 text-gray-600">${user.name} (${user.role})</span>
                            <button onclick="logout()" class="text-red-500 hover:text-red-700">登出</button>
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
                <div class="bg-white p-8 rounded shadow-md w-96 mt-20">
                    <h2 class="text-2xl font-bold mb-6 text-center">登入</h2>
                    <form onsubmit="handleLogin(event)">
                        <input type="text" name="acc" placeholder="帳號 (12156208/admin)" class="w-full p-2 border mb-4 rounded" required>
                        <input type="password" name="pwd" placeholder="密碼 (123/admin)" class="w-full p-2 border mb-6 rounded" required>
                        <button class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700">登入</button>
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
                    <div class="bg-white p-6 rounded shadow h-fit">
                        <h3 class="text-lg font-bold mb-4">申請假單</h3>
                        <form onsubmit="apply(event)">
                            <label class="block mb-2">日期</label>
                            <input type="date" name="date" required class="w-full p-2 border rounded mb-4">
                            <label class="block mb-2">事由</label>
                            <textarea name="reason" required class="w-full p-2 border rounded mb-4"></textarea>
                            <button class="w-full bg-orange-500 text-white p-2 rounded">送出</button>
                        </form>
                    </div>
                    <div class="md:col-span-2 bg-white p-6 rounded shadow">
                        <h3 class="text-lg font-bold mb-4">我的紀錄</h3>
                        ${tableHtml(myLeaves, false)}
                    </div>
                </div>`;
        }

        function renderAdmin() {
            document.getElementById('content').innerHTML = `
                <div class="bg-white p-6 rounded shadow">
                    <h3 class="text-lg font-bold mb-4">假單審核</h3>
                    ${tableHtml(leaves, true)}
                </div>`;
        }

        function tableHtml(data, isAdmin) {
            if (!data.length) return '<p class="text-gray-500">無資料</p>';
            return `
                <table class="w-full text-left border-collapse">
                    <thead><tr class="bg-gray-50 border-b">
                        <th class="p-3">ID</th><th class="p-3">日期</th><th class="p-3">事由</th><th class="p-3">狀態</th>${isAdmin?'<th class="p-3">操作</th>':''}
                    </tr></thead>
                    <tbody>${data.map(l => `
                        <tr class="border-b hover:bg-gray-50">
                            <td class="p-3">${l.id}</td>
                            <td class="p-3">${l.date}</td>
                            <td class="p-3">${l.reason}</td>
                            <td class="p-3"><span class="px-2 py-1 rounded text-sm ${l.status==='Pending'?'bg-yellow-100':(l.status==='Approved'?'bg-green-100':'bg-red-100')}">${l.status}</span></td>
                            ${isAdmin && l.status === 'Pending' ? `
                            <td class="p-3">
                                <button onclick="audit(${l.id}, 'Approved')" class="text-green-600 mr-2">批准</button>
                                <button onclick="audit(${l.id}, 'Rejected')" class="text-red-600">拒絕</button>
                            </td>` : (isAdmin ? '<td class="p-3 text-gray-400">-</td>' : '')}
                        </tr>`).join('')}
                    </tbody>
                </table>`;
        }

        async function apply(e) {
            e.preventDefault();
            const res = await api('/apply', 'POST', { 
                student_id: user.account, 
                date: e.target.date.value, 
                reason: e.target.reason.value 
            });
            if (res) { await loadLeaves(); render(); }
        }

        async function audit(id, status) {
            if(!confirm('確定?')) return;
            const res = await api('/audit', 'PATCH', { id, status });
            if (res) { await loadAllLeaves(); render(); }
        }
        function logout() { user = null; render(); }
        
        window.onload = init;
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return Response(FRONTEND_HTML, mimetype='text/html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    u = users.get(data.get('account'))
    if u and u['pwd'] == data.get('password'):
        return jsonify({"status": "success", "role": u['role'], "name": u['name']})
    return jsonify({"status": "error"}), 401

@app.route('/api/leaves', methods=['GET'])
def get_leaves():
    sid = request.args.get('student_id')
    return jsonify([l for l in leaves if l['student_id'] == sid] if sid else leaves)

@app.route('/api/apply', methods=['POST'])
def apply():
    global next_leave_id
    d = request.json
    leaves.append({"id": next_leave_id, "student_id": d['student_id'], "date": d['date'], "reason": d['reason'], "status": "Pending"})
    next_leave_id += 1
    return jsonify({"status": "success"}), 201

@app.route('/api/audit', methods=['PATCH'])
def audit():
    d = request.json
    for l in leaves:
        if l['id'] == d['id']:
            l['status'] = d['status']
            return jsonify({"status": "success"})
    return jsonify({"error": "not found"}), 404
