// Dropdown toggle
document.addEventListener('click', function(e) {
    // Close all dropdowns
    document.querySelectorAll('.dropdown-content.show').forEach(function(el) {
        if (!el.parentElement.contains(e.target)) {
            el.classList.remove('show');
        }
    });
});

function toggleDropdown(btn) {
    var content = btn.nextElementSibling;
    document.querySelectorAll('.dropdown-content.show').forEach(function(el) {
        if (el !== content) el.classList.remove('show');
    });
    content.classList.toggle('show');
}

// Modal
function showModal(id) {
    document.getElementById(id).classList.add('show');
}

function hideModal(id) {
    document.getElementById(id).classList.remove('show');
}

// AJAX helper
function apiPost(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(function(r) { return r.json(); });
}

// Notify success
function notifySuccess(orderId) {
    if (!confirm('确认通知充值成功？')) return;
    apiPost('/order/notify-success/' + orderId, {}).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}

// Notify refund
function notifyRefund(orderId) {
    if (!confirm('确认通知退款？')) return;
    apiPost('/order/notify-refund/' + orderId, {}).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}

// Agiso deliver
function agisoDeliver(orderId) {
    if (!confirm('确认使用阿奇索发货？')) return;
    apiPost('/order/agiso-deliver/' + orderId, {}).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}

// Self debug
function selfDebug(orderId, status) {
    var msg = '⚠️ 自助联调修改订单状态，非联调场景下，不要使用此功能。\n' +
        '此页面是为了方便联调测试使用的，会直接修改订单状态而不回调\n' +
        '京东官方，用于京东反查订单状态的场景，请确认清楚操作再点击确认按钮。';
    if (!confirm(msg)) return;
    apiPost('/order/self-debug/' + orderId, { status: status }).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}

// Card delivery modal
function showCardModal(orderId, quantity) {
    var html = '<div class="modal-title">🚚 卡密发货</div>';
    html += '<p class="mb-4">请输入 ' + quantity + ' 组卡密信息：</p>';
    for (var i = 0; i < quantity; i++) {
        html += '<div class="form-row mb-2">';
        html += '<div class="form-group"><label>卡号 ' + (i + 1) + '</label>';
        html += '<input type="text" class="form-control card-no" placeholder="请输入卡号"></div>';
        html += '<div class="form-group"><label>密码 ' + (i + 1) + '</label>';
        html += '<input type="text" class="form-control card-pwd" placeholder="请输入密码"></div>';
        html += '</div>';
    }
    html += '<div class="modal-footer">';
    html += '<button class="btn" onclick="hideModal(\'cardModal\')">取消</button>';
    html += '<button class="btn btn-primary" onclick="submitCards(' + orderId + ', ' + quantity + ')">提交发货</button>';
    html += '</div>';

    var modal = document.getElementById('cardModal');
    modal.querySelector('.modal').innerHTML = html;
    showModal('cardModal');
}

function submitCards(orderId, quantity) {
    var cardNos = document.querySelectorAll('.card-no');
    var cardPwds = document.querySelectorAll('.card-pwd');
    var cards = [];
    for (var i = 0; i < quantity; i++) {
        var no = cardNos[i].value.trim();
        var pwd = cardPwds[i].value.trim();
        if (!no || !pwd) {
            alert('请填写完整的卡密信息');
            return;
        }
        cards.push({ cardNo: no, cardPwd: pwd });
    }
    apiPost('/order/deliver-card/' + orderId, { cards: cards }).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}

// Test notification
function testNotification(shopId, notifyType) {
    apiPost('/shop/test-notification', { shop_id: shopId, notify_type: notifyType }).then(function(res) {
        alert(res.message);
    });
}

// Resend notification
function resendNotification(logId) {
    if (!confirm('确认重新发送通知？')) return;
    apiPost('/notification/resend', { log_id: logId }).then(function(res) {
        alert(res.message);
        if (res.success) location.reload();
    });
}
