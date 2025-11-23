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

# 預設假單資料
leaves = [
    {"id": 1, "student_id": "12156208", "date": "2023-12-01", "reason": "病假", "status": "Pending"},
    {"id": 2, "student_id": "12156231", "date": "2023-12-05", "reason": "事假", "status": "Approved"}
]
next_leave_id = 3

# --- HTML (最終修復版：防止頁面刷新 + 穩定日曆) ---
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
        /* 讓整個 Date 輸入框點擊時都能觸發日曆 */
        .date-wrapper {
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
            opacity: 0;
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
                        <input type="text" id="login-acc" placeholder="12156208 / admin" class="w-full p-2 border mb-4 rounded focus:ring-2 ring-blue-500 outline-none" required>
                        <label class="block mb-1 text-sm text-gray-600">密碼</label>
                        <input type="password" id="login-pwd" placeholder="123 / admin" class="w-full p-2 border mb-6 rounded focus:ring-2 ring-blue-500 outline-none" required>
                        <button type="submit" class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition font-bold">登入</button>
                    </form>
                </div>`;
        }

        async function handleLogin(e) {
            e.preventDefault(); // 防止登入表單刷新
            const acc = document.getElementById('login-acc').value;
            const pwd = document.getElementById('login-pwd').value;
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
                        
                        <div>
                            <label class="block mb-2 font-medium">日期</label>
                            <div class="date-wrapper relative">
                                <input type="date" id="apply-date" class="w-full p-2 border rounded mb-4 cursor-pointer hover:bg-gray-50 bg-white">
                            </div>
                            
                            <label class="block mb-2 font-medium">事由</label>
                            <textarea id="apply-reason" rows="3" class="w-full p-2 border rounded mb-4" placeholder="請填寫原因..."></textarea>
                            
                            <button type="button" onclick="handleApply()" class="w-full bg-orange-500 text-white p-2 rounded hover:bg-orange-600 font-bold">送出申請</button>
                        </div>

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

        async function handleApply() {
            // 直接抓取 ID，不依賴 form submit
            const dateVal = document.getElementById('apply-date').value;
            const reasonVal = document.getElementById('apply-reason').value;
            
            if (!dateVal || !reasonVal) {
                alert('請填寫完整資料！');
                return;
            }

            const res = await api('/apply', 'POST', { 
                student_id: user.account, 
                date: dateVal, 
                reason: reasonVal 
            });
            if (res) { 
                await loadLeaves(); 
                render(); 
                alert('申請成功！'); // 加入提示讓你知道成功了
            }
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
