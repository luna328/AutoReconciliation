// 全局状态
let vendorData = null;
let internalData = null;
let reconcileResult = null;

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initThemeSwitcher();
    initFileUploads();
    initTabs();
    initReconcileButton();
    initExportButton();
});

function initThemeSwitcher() {
    const select = document.getElementById('theme-select');
    if (!select) return;

    const saved = localStorage.getItem('reconcile_theme') || 'sage';
    applyTheme(saved);
    select.value = saved;

    select.addEventListener('change', function(e) {
        const theme = e.target.value;
        applyTheme(theme);
        localStorage.setItem('reconcile_theme', theme);
    });
}

function applyTheme(theme) {
    if (theme === 'sage') {
        document.body.removeAttribute('data-theme');
    } else {
        document.body.setAttribute('data-theme', theme);
    }
}

// 初始化文件上传
function initFileUploads() {
    // 供应商对账单上传
    const vendorFile = document.getElementById('vendor-file');
    vendorFile.addEventListener('change', function(e) {
        handleFileUpload(e.target.files[0], 'vendor');
    });

    // 入库单上传
    const internalFile = document.getElementById('internal-file');
    internalFile.addEventListener('change', function(e) {
        handleFileUpload(e.target.files[0], 'internal');
    });
}

// 处理文件上传
async function handleFileUpload(file, type) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadCardLoading(type, true);

    try {
        const response = await fetch(`/api/upload/${type}`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            if (type === 'vendor') {
                vendorData = result;
                displayFileInfo('vendor', result);
                displayPreview('vendor-preview', result.preview, result.columns);
                applySuggestedVendorMapping(result.suggested_mapping || {});
            } else {
                internalData = result;
                displayFileInfo('internal', result);
                displayPreview('internal-preview', result.preview, result.columns);
            }
            updateReconcileButton();
        } else {
            alert('上传失败：' + result.error);
        }
    } catch (error) {
        alert('上传出错：' + error.message);
    } finally {
        setUploadCardLoading(type, false);
    }
}

function setUploadCardLoading(type, isLoading) {
    const card = document.getElementById(type === 'vendor' ? 'vendor-upload' : 'internal-upload');
    if (!card) return;

    const uploadArea = card.querySelector('.upload-area');
    const infoDiv = document.getElementById(`${type}-info`);

    if (uploadArea) {
        uploadArea.style.pointerEvents = isLoading ? 'none' : 'auto';
        uploadArea.style.opacity = isLoading ? '0.6' : '1';
    }

    if (isLoading) {
        if (infoDiv) infoDiv.innerHTML = '上传中...';
    }
}

function applySuggestedVendorMapping(suggested) {
    const mappingToInput = {
        po_no: 'vendor-po',
        item_code: 'vendor-item-code',
        qty: 'vendor-qty',
        unit_price: 'vendor-price',
        amount: 'vendor-amount'
    };

    Object.keys(mappingToInput).forEach((key) => {
        const inputId = mappingToInput[key];
        const input = document.getElementById(inputId);
        if (input && suggested[key]) {
            input.value = suggested[key];
        }
    });
}

// 显示文件信息
function displayFileInfo(type, data) {
    const infoDiv = document.getElementById(`${type}-info`);
    infoDiv.innerHTML = `
        <strong>文件名：</strong>${data.filename}<br>
        <strong>行数：</strong>${data.row_count} 行
    `;
}

// 显示预览表格
function displayPreview(elementId, previewData, columns) {
    const container = document.getElementById(elementId);
    if (!previewData || previewData.length === 0) {
        container.innerHTML = '<p class="text-muted">无数据预览</p>';
        return;
    }

    // 过滤掉Unnamed列
    const displayColumns = columns.filter(col => !col.startsWith('Unnamed'));
    
    let html = '<table class="data-table"><thead><tr>';
    displayColumns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';

    previewData.forEach(row => {
        html += '<tr>';
        displayColumns.forEach(col => {
            let value = row[col];
            if (value === null || value === undefined || value === '') {
                value = '-';
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// 更新对账按钮状态
function updateReconcileButton() {
    const btn = document.getElementById('reconcile-btn');
    btn.disabled = !(vendorData && internalData);
}

// 初始化标签页
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            // 更新按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 更新内容显示
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tab}-content`).classList.add('active');
        });
    });
}

// 初始化对账按钮
function initReconcileButton() {
    const btn = document.getElementById('reconcile-btn');
    btn.addEventListener('click', performReconcile);
}

// 执行对账
async function performReconcile() {
    const config = {
        vendor_mapping: {
            po_no: document.getElementById('vendor-po').value,
            item_code: document.getElementById('vendor-item-code').value,
            qty: document.getElementById('vendor-qty').value,
            unit_price: document.getElementById('vendor-price').value,
            amount: document.getElementById('vendor-amount').value
        },
        internal_mapping: {
            po_no: document.getElementById('internal-po').value,
            item_code: document.getElementById('internal-item-code').value,
            qty: document.getElementById('internal-qty').value,
            unit_price: document.getElementById('internal-price').value,
            amount: document.getElementById('internal-amount').value
        },
        price_tolerance: parseFloat(document.getElementById('price-tolerance').value),
        qty_tolerance: parseFloat(document.getElementById('qty-tolerance').value),
        amount_tolerance: parseFloat(document.getElementById('amount-tolerance').value)
    };

    setReconcileLoading(true);

    try {
        const response = await fetch('/api/reconcile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();

        if (result.success) {
            reconcileResult = result.result;
            displayResults(reconcileResult);
        } else {
            alert('对账失败：' + result.error);
        }
    } catch (error) {
        alert('对账出错：' + error.message);
    } finally {
        setReconcileLoading(false);
    }
}

function setReconcileLoading(isLoading) {
    const btn = document.getElementById('reconcile-btn');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.dataset.originalText = btn.dataset.originalText || btn.textContent;
    btn.textContent = isLoading ? '对账中...' : btn.dataset.originalText;
    btn.style.opacity = isLoading ? '0.8' : '1';
}

// 显示对账结果
function displayResults(result) {
    const resultSection = document.getElementById('result-section');
    resultSection.style.display = 'block';

    // 显示汇总卡片
    displaySummaryCards(result.summary);

    // 显示匹配明细
    displayMatchedResults(result);

    // 显示差异明细
    displayIssues(result);

    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 显示汇总卡片
function displaySummaryCards(summary) {
    const container = document.getElementById('summary-cards');
    
    const cards = [
        { title: '供应商总行数', value: summary.vendor_total_rows, type: 'info' },
        { title: '系统总行数', value: summary.internal_total_rows, type: 'info' },
        { title: '完全匹配(分组)', value: summary.matched_count, type: 'success' },
        { title: '完全匹配(展示行)', value: summary.matched_display_count ?? summary.matched_count, type: 'success' },
        { title: '差异项(展示行)', value: summary.diff_items_display_count ?? summary.diff_items_count, type: 'warning' },
        { title: '数量差异(展示行)', value: summary.diff_qty_display_count ?? summary.diff_qty_count, type: 'warning' },
        { title: '单价差异(展示行)', value: summary.diff_price_display_count ?? summary.diff_price_count, type: 'warning' },
        { title: '金额差异(展示行)', value: summary.diff_amount_display_count ?? summary.diff_amount_count, type: 'warning' }
    ];

    container.innerHTML = cards.map(card => `
        <div class="summary-card ${card.type}">
            <h4>${card.title}</h4>
            <div class="number">${card.value}</div>
        </div>
    `).join('');

}

// 显示匹配结果
function displayMatchedResults(result) {
    // 完全匹配（行级真实配对）
    const oneToOneDiv = document.getElementById('matched-one-to-one');
    const matchedPairs = result.matched_pairs || [];
    if (matchedPairs.length > 0) {
        const displayCount = matchedPairs.length;
        const sectionId = 'matched-table-section';
        let html = '<h3 class="section-title">✅ 完全匹配（展示维度）(' + displayCount + ' 条) '
            + '<button class="expand-btn" style="margin-left: 10px;" onclick="toggleSection(\'' + sectionId + '\', this)">展开明细</button>'
            + '</h3>';
        html += '<div id="' + sectionId + '" style="display:none; overflow-x: auto;"><table class="data-table">';
        html += '<thead><tr>';
        html += '<th>PO号</th>';
        html += '<th>物料编码</th>';
        html += '<th>行引用</th>';
        html += '<th>供应商数量</th>';
        html += '<th>系统数量</th>';
        html += '<th>供应商单价</th>';
        html += '<th>系统单价</th>';
        html += '<th>供应商金额</th>';
        html += '<th>系统金额</th>';
        html += '</tr></thead><tbody>';

        matchedPairs.forEach(match => {
            const vRefs = match.vendor_refs || [];
            const iRefs = match.internal_refs || [];
            const maxLen = Math.max(vRefs.length, iRefs.length, 1);

            for (let idx = 0; idx < maxLen; idx++) {
                const vr = vRefs[idx] || null;
                const ir = iRefs[idx] || null;
                html += '<tr>';
                html += `<td>${match.po_no || '-'}</td>`;
                html += `<td>${match.item_code}</td>`;
                html += `<td>V${vr ? vr.row_no : '-'} / I${ir ? ir.row_no : '-'}</td>`;
                html += `<td>${vr ? vr.qty : '-'}</td>`;
                html += `<td>${ir ? ir.qty : '-'}</td>`;
                html += `<td>${vr && vr.unit_price != null ? Number(vr.unit_price).toFixed(4) : '-'}</td>`;
                html += `<td>${ir && ir.unit_price != null ? Number(ir.unit_price).toFixed(4) : '-'}</td>`;
                html += `<td>${vr && vr.amount != null ? Number(vr.amount).toFixed(2) : '-'}</td>`;
                html += `<td>${ir && ir.amount != null ? Number(ir.amount).toFixed(2) : '-'}</td>`;
                html += '</tr>';
            }
        });

        html += '</tbody></table></div>';
        oneToOneDiv.innerHTML = html;
    } else {
        oneToOneDiv.innerHTML = '<div class="alert alert-warning">无完全匹配数据</div>';
    }

    // 分组视图：展示聚合后的完全匹配组
    const aggregateDiv = document.getElementById('matched-aggregate');
    const matchedGroups = result.matched_groups || result.matched_list || [];
    if (matchedGroups.length > 0) {
        const aggregateSectionId = 'matched-group-table-section';
        let html = '<h3 class="section-title">📦 完全匹配（分组维度）(' + matchedGroups.length + ' 组) '
            + '<button class="expand-btn" style="margin-left: 10px;" onclick="toggleSection(\'' + aggregateSectionId + '\', this)">展开明细</button>'
            + '</h3>';
        html += '<div id="' + aggregateSectionId + '" style="display:none; overflow-x: auto;"><table class="data-table">';
        html += '<thead><tr>';
        html += '<th>PO号</th>';
        html += '<th>物料编码</th>';
        html += '<th>供应商汇总数量</th>';
        html += '<th>系统汇总数量</th>';
        html += '<th>供应商汇总金额</th>';
        html += '<th>系统汇总金额</th>';
        html += '<th>供应商行数</th>';
        html += '<th>系统行数</th>';
        html += '</tr></thead><tbody>';

        matchedGroups.forEach(group => {
            const vCount = (group.vendor_refs || []).length;
            const iCount = (group.internal_refs || []).length;
            html += '<tr>';
            html += `<td>${group.po_no || '-'}</td>`;
            html += `<td>${group.item_code}</td>`;
            html += `<td>${group.vendor_qty ?? '-'}</td>`;
            html += `<td>${group.internal_qty ?? '-'}</td>`;
            html += `<td>${group.vendor_amount != null ? Number(group.vendor_amount).toFixed(2) : '-'}</td>`;
            html += `<td>${group.internal_amount != null ? Number(group.internal_amount).toFixed(2) : '-'}</td>`;
            html += `<td>${vCount}</td>`;
            html += `<td>${iCount}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        aggregateDiv.innerHTML = html;
    } else {
        aggregateDiv.innerHTML = '';
    }
}

function toggleSection(sectionId, btn) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    const hidden = section.style.display === 'none';
    section.style.display = hidden ? 'block' : 'none';
    btn.textContent = hidden ? '收起明细' : '展开明细';
}

// 显示差异
function displayIssues(result) {
    const issuesDiv = document.getElementById('issues-table');
    
    let issuesHtml = '';

    const renderIssueRows = (rows, badgeClass, badgeText) => {
        let html = '';
        rows.forEach((row) => {
            const vRefs = row.vendor_refs || [];
            const iRefs = row.internal_refs || [];
            const maxLen = Math.max(vRefs.length, iRefs.length, 1);
            for (let idx = 0; idx < maxLen; idx++) {
                const vr = vRefs[idx] || null;
                const ir = iRefs[idx] || null;
                html += '<tr>';
                html += `<td>${row.po_no || '-'}</td>`;
                html += `<td>${row.item_code}</td>`;
                html += `<td>V${vr ? vr.row_no : '-'} / I${ir ? ir.row_no : '-'}</td>`;
                html += `<td>${vr ? vr.qty : '-'}</td>`;
                html += `<td>${ir ? ir.qty : '-'}</td>`;
                html += `<td>${vr && vr.unit_price != null ? Number(vr.unit_price).toFixed(4) : '-'}</td>`;
                html += `<td>${ir && ir.unit_price != null ? Number(ir.unit_price).toFixed(4) : '-'}</td>`;
                html += `<td>${vr && vr.amount != null ? Number(vr.amount).toFixed(2) : '-'}</td>`;
                html += `<td>${ir && ir.amount != null ? Number(ir.amount).toFixed(2) : '-'}</td>`;
                html += `<td><span class="badge ${badgeClass}">${badgeText}</span></td>`;
                html += '</tr>';
            }
        });
        return html;
    };

    const renderIssueSection = (sectionId, title, count, rows, badgeClass, badgeText) => {
        if (!rows || rows.length === 0) return '';
        let html = `<h3 class="section-title">⚠️ ${title} (${count} 条) `
            + `<button class="expand-btn" style="margin-left: 10px;" onclick="toggleSection('${sectionId}', this)">收起明细</button>`
            + '</h3>';
        html += `<div id="${sectionId}" style="display:block; overflow-x: auto;"><table class="data-table">`;
        html += '<thead><tr>';
        html += '<th>PO号</th>';
        html += '<th>物料编码</th>';
        html += '<th>行引用</th>';
        html += '<th>供应商数量</th>';
        html += '<th>系统数量</th>';
        html += '<th>供应商单价</th>';
        html += '<th>系统单价</th>';
        html += '<th>供应商金额</th>';
        html += '<th>系统金额</th>';
        html += '<th>差异类型</th>';
        html += '</tr></thead><tbody>';
        html += renderIssueRows(rows, badgeClass, badgeText);
        html += '</tbody></table></div>';
        return html;
    };

    issuesHtml += renderIssueSection(
        'issue-diff-items',
        '差异项 - 一方完全不存在',
        result.summary?.diff_items_display_count ?? result.diff_items?.length ?? 0,
        result.diff_items,
        'badge-danger',
        '差异项'
    );
    issuesHtml += renderIssueSection(
        'issue-diff-qty',
        '数量差异 - PO+物料编码匹配，数量不一致',
        result.summary?.diff_qty_display_count ?? result.diff_qty?.length ?? 0,
        result.diff_qty,
        'badge-warning',
        '数量差异'
    );
    issuesHtml += renderIssueSection(
        'issue-diff-price',
        '单价差异 - PO+物料编码匹配，单价不一致',
        result.summary?.diff_price_display_count ?? result.diff_price?.length ?? 0,
        result.diff_price,
        'badge-warning',
        '单价差异'
    );
    issuesHtml += renderIssueSection(
        'issue-diff-amount',
        '金额差异 - PO+物料编码+数量+单价匹配，金额不一致',
        result.summary?.diff_amount_display_count ?? result.diff_amount?.length ?? 0,
        result.diff_amount,
        'badge-warning',
        '金额差异'
    );

    if (!issuesHtml) {
        issuesHtml = '<div class="alert alert-success">🎉 恭喜！没有发现差异，所有数据均已匹配。</div>';
    }

    issuesDiv.innerHTML = issuesHtml;
}

// 初始化导出按钮
function initExportButton() {
    const btn = document.getElementById('export-btn');
    btn.addEventListener('click', exportResults);
}

// 导出结果
async function exportResults() {
    if (!reconcileResult) {
        alert('没有可导出的结果');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'all' })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `对账结果_${new Date().toISOString().slice(0,10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const result = await response.json();
            alert('导出失败：' + result.error);
        }
    } catch (error) {
        alert('导出出错：' + error.message);
    } finally {
        showLoading(false);
    }
}

// 显示/隐藏加载遮罩
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

// 拖拽上传支持
function initDragAndDrop() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.style.background = '#e3f2fd';
            area.style.borderColor = '#667eea';
        });

        area.addEventListener('dragleave', (e) => {
            e.preventDefault();
            area.style.background = '#f8f9fa';
            area.style.borderColor = 'transparent';
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.style.background = '#f8f9fa';
            area.style.borderColor = 'transparent';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const card = area.closest('.upload-card');
                const type = card.id === 'vendor-upload' ? 'vendor' : 'internal';
                handleFileUpload(files[0], type);
            }
        });
    });
}

// 页面加载完成后初始化拖拽
document.addEventListener('DOMContentLoaded', initDragAndDrop);
