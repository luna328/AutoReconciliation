from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import os
import json
import math
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import io


def clean_nan(value):
    """清理NaN值，用于JSON序列化"""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def clean_dict(data):
    """递归清理字典中的NaN值"""
    if isinstance(data, dict):
        return {k: clean_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict(item) for item in data]
    else:
        return clean_nan(data)


app = Flask(__name__)
app.json.sort_keys = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# 全局变量存储当前任务数据
current_task = {
    "vendor_file": None,
    "internal_file": None,
    "vendor_data": None,
    "internal_data": None,
    "result": None,
}

PO_PATTERN = re.compile(r"^LY20\d{6,}$", re.IGNORECASE)
ITEM_PATTERN = re.compile(r"^(BC\d{5,}|ASE[0-9A-Z-]{3,})$", re.IGNORECASE)
FOOTER_KEYWORDS = [
    "合计",
    "总计",
    "小计",
    "本月合计",
    "金额合计",
    "累计",
    "TOTAL",
    "Total",
]


def _to_text(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def _to_float(v):
    if pd.isna(v):
        return None
    if isinstance(v, (int, float, np.number)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _is_po(v):
    return bool(PO_PATTERN.match(_to_text(v)))


def _is_item(v):
    return bool(ITEM_PATTERN.match(_to_text(v)))


def detect_vendor_table_and_mapping(raw_df):
    scan_limit = min(len(raw_df), 200)
    data_start = None

    for i in range(scan_limit):
        row = raw_df.iloc[i]
        po_hits = sum(1 for v in row if _is_po(v))
        item_hits = sum(1 for v in row if _is_item(v))
        num_hits = sum(1 for v in row if _to_float(v) is not None)
        if po_hits >= 1 and item_hits >= 1 and num_hits >= 2:
            data_start = i
            break

    if data_start is None:
        return None, {}

    header_row = max(data_start - 1, 0)
    header_vals = raw_df.iloc[header_row].tolist()

    table_df = raw_df.iloc[data_start:].reset_index(drop=True).copy()
    col_names = []
    used = set()
    for idx, hv in enumerate(header_vals[: table_df.shape[1]]):
        name = _to_text(hv) or f"列{idx + 1}"
        base = name
        n = 2
        while name in used:
            name = f"{base}_{n}"
            n += 1
        used.add(name)
        col_names.append(name)

    if len(col_names) < table_df.shape[1]:
        for idx in range(len(col_names), table_df.shape[1]):
            col_names.append(f"列{idx + 1}")

    table_df.columns = [str(c) for c in col_names]
    table_df = table_df.dropna(how="all", axis=1)

    sample = table_df.head(120)
    col_stats = {}
    for col in sample.columns:
        vals = sample[col].tolist()
        po_count = sum(1 for v in vals if _is_po(v))
        item_count = sum(1 for v in vals if _is_item(v))
        nums = [_to_float(v) for v in vals]
        nums = [v for v in nums if v is not None]
        int_ratio = 0
        mean_val = 0
        if nums:
            int_ratio = sum(1 for x in nums if abs(x - round(x)) < 1e-9) / len(nums)
            mean_val = sum(nums) / len(nums)
        col_stats[col] = {
            "po": po_count,
            "item": item_count,
            "num_count": len(nums),
            "int_ratio": int_ratio,
            "mean": mean_val,
        }

    suggested = {}

    po_col = max(sample.columns, key=lambda c: col_stats[c]["po"], default=None)
    if po_col and col_stats[po_col]["po"] > 0:
        suggested["po_no"] = po_col

    item_col = max(sample.columns, key=lambda c: col_stats[c]["item"], default=None)
    if item_col and col_stats[item_col]["item"] > 0:
        suggested["item_code"] = item_col

    qty_kw = [c for c in sample.columns if any(k in c for k in ["数量", "數量", "qty"])]
    price_kw = [
        c
        for c in sample.columns
        if any(k in c for k in ["单价", "單價", "price", "含税单价"])
    ]
    amount_kw = [
        c
        for c in sample.columns
        if any(k in c for k in ["金额", "金額", "amount", "价税合计"])
    ]

    numeric_cols = [c for c in sample.columns if col_stats[c]["num_count"] >= 3]

    if qty_kw:
        suggested["qty"] = qty_kw[0]
    if price_kw:
        suggested["unit_price"] = price_kw[0]
    if amount_kw:
        suggested["amount"] = amount_kw[0]

    if "qty" not in suggested:
        qty_candidates = sorted(
            numeric_cols,
            key=lambda c: (col_stats[c]["int_ratio"], col_stats[c]["mean"]),
            reverse=True,
        )
        if qty_candidates:
            suggested["qty"] = qty_candidates[0]

    if "unit_price" not in suggested:
        rem = [c for c in numeric_cols if c != suggested.get("qty")]
        if rem:
            rem.sort(
                key=lambda c: col_stats[c]["mean"] if col_stats[c]["mean"] > 0 else 1e18
            )
            suggested["unit_price"] = rem[0]

    if "amount" not in suggested and "qty" in suggested and "unit_price" in suggested:
        rem = [
            c
            for c in numeric_cols
            if c not in {suggested.get("qty"), suggested.get("unit_price")}
        ]
        if rem:
            q = suggested["qty"]
            p = suggested["unit_price"]
            best_col = None
            best_err = None
            for c in rem:
                errs = []
                for _, r in sample[[q, p, c]].dropna().head(60).iterrows():
                    qv = _to_float(r[q])
                    pv = _to_float(r[p])
                    av = _to_float(r[c])
                    if qv is None or pv is None or av is None:
                        continue
                    pred = qv * pv
                    errs.append(abs(av - pred))
                if errs:
                    err = sum(errs) / len(errs)
                    if best_err is None or err < best_err:
                        best_err = err
                        best_col = c
            if best_col:
                suggested["amount"] = best_col

    # 依据明细模式识别表尾并裁剪，防止把合计/签字等行纳入对账
    po_col = suggested.get("po_no")
    item_col = suggested.get("item_code")
    qty_col = suggested.get("qty")
    price_col = suggested.get("unit_price")
    amount_col = suggested.get("amount")

    if not po_col or not item_col:
        return table_df, suggested

    detail_indices = []
    seen_detail = False
    non_detail_streak = 0

    for idx, row in table_df.iterrows():
        row_vals = [_to_text(v) for v in row.tolist() if _to_text(v)]
        has_footer_keyword = any(
            any(k in cell for k in FOOTER_KEYWORDS) for cell in row_vals
        )

        if has_footer_keyword and seen_detail:
            break

        po_ok = _is_po(row.get(po_col))
        item_ok = _is_item(row.get(item_col))

        numeric_hits = 0
        for c in [qty_col, price_col, amount_col]:
            if c and c in table_df.columns and _to_float(row.get(c)) is not None:
                numeric_hits += 1

        is_detail = po_ok and item_ok and numeric_hits >= 2

        if is_detail:
            detail_indices.append(idx)
            seen_detail = True
            non_detail_streak = 0
        else:
            if seen_detail:
                non_detail_streak += 1
                if non_detail_streak >= 3:
                    break

    if detail_indices:
        table_df = table_df.loc[detail_indices].reset_index(drop=True)

    return table_df, suggested


def build_row_refs(rows):
    return [
        {
            "row_no": r.get("row_no"),
            "qty": r.get("qty"),
            "unit_price": r.get("unit_price"),
            "amount": r.get("amount"),
        }
        for r in rows
    ]


def split_qty_residual_rows(v_rows, i_rows, price_tolerance=0.0001):
    """在数量差异组内做行级配对，只返回未配对残差行用于展示。"""
    v_used = [False] * len(v_rows)
    i_used = [False] * len(i_rows)

    # 第一轮：数量+单价同时相同优先配对
    for vi, vr in enumerate(v_rows):
        if v_used[vi]:
            continue
        vq = vr.get("qty")
        vp = vr.get("unit_price")
        for ii, ir in enumerate(i_rows):
            if i_used[ii]:
                continue
            iq = ir.get("qty")
            ip = ir.get("unit_price")
            if vq == iq and abs(float(vp) - float(ip)) <= price_tolerance:
                v_used[vi] = True
                i_used[ii] = True
                break

    # 第二轮：仅数量相同也视为配对（数量差异场景下用于剔除无关行）
    for vi, vr in enumerate(v_rows):
        if v_used[vi]:
            continue
        vq = vr.get("qty")
        for ii, ir in enumerate(i_rows):
            if i_used[ii]:
                continue
            if vq == ir.get("qty"):
                v_used[vi] = True
                i_used[ii] = True
                break

    v_remain = [r for idx, r in enumerate(v_rows) if not v_used[idx]]
    i_remain = [r for idx, r in enumerate(i_rows) if not i_used[idx]]
    return v_remain, i_remain


# 默认列映射配置
DEFAULT_VENDOR_MAPPING = {
    "po_no": "订单号码",
    "item_code": "物料编码",
    "item_name": "品名",
    "qty": "数量",
    "unit_price": "单价",
    "amount": "金额",
}

DEFAULT_INTERNAL_MAPPING = {
    "item_code": "物料编码",
    "item_name": "物料名称",
    "spec": "规格型号",
    "qty": "实收数量",
    "unit_price": "含税单价",
    "amount": "价税合计",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload/vendor", methods=["POST"])
def upload_vendor_file():
    """上传供应商对账单"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "没有选择文件"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "文件名为空"})

        if not file.filename.endswith((".xlsx", ".xls")):
            return jsonify({"success": False, "error": "请上传Excel文件(.xlsx或.xls)"})

        filename = secure_filename(
            f"vendor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # 读取文件并自动识别表头/字段（基于内容模式）
        raw_df = pd.read_excel(filepath, header=None)
        df, suggested = detect_vendor_table_and_mapping(raw_df)
        if df is None or len(df) == 0:
            # 兜底：沿用固定表头行
            df = pd.read_excel(filepath, header=4)
            df = df.dropna(how="all", axis=1)
            df.columns = [str(col) for col in df.columns]
            suggested = {}

        # 保存数据
        current_task["vendor_file"] = filepath
        current_task["vendor_data"] = df

        # 返回预览数据 - 处理日期和NaN值
        preview_df = df.head(10).copy()
        preview = []
        for record in preview_df.to_dict("records"):
            cleaned_record = {}
            for k, v in record.items():
                key = str(k)
                if pd.isna(v):
                    cleaned_record[key] = ""
                elif isinstance(v, (pd.Timestamp, datetime)):
                    cleaned_record[key] = str(v)
                else:
                    cleaned_record[key] = v
            preview.append(cleaned_record)
        columns = df.columns.tolist()

        return jsonify(
            {
                "success": True,
                "filename": file.filename,
                "row_count": len(df),
                "columns": columns,
                "preview": preview,
                "suggested_mapping": suggested,
            }
        )

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "trace": traceback.format_exc()}
        )


@app.route("/api/upload/internal", methods=["POST"])
def upload_internal_file():
    """上传系统入库单"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "没有选择文件"})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "文件名为空"})

        if not file.filename.endswith((".xlsx", ".xls")):
            return jsonify({"success": False, "error": "请上传Excel文件(.xlsx或.xls)"})

        filename = secure_filename(
            f"internal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # 读取文件（系统导出固定格式）
        df = pd.read_excel(filepath)
        df.columns = [str(col) for col in df.columns]

        # 固定规则：第一列出现“合计”的行剔除，避免纳入对账
        if len(df.columns) > 0:
            first_col = df.columns[0]
            mask_total = df[first_col].astype(str).str.contains("合计", na=False)
            if mask_total.any():
                df = df.loc[~mask_total].reset_index(drop=True)

        # 保存数据
        current_task["internal_file"] = filepath
        current_task["internal_data"] = df

        # 返回预览数据 - 处理日期和NaN值
        preview_df = df.head(10).copy()
        preview = []
        for record in preview_df.to_dict("records"):
            cleaned_record = {}
            for k, v in record.items():
                key = str(k)
                if pd.isna(v):
                    cleaned_record[key] = ""
                elif isinstance(v, (pd.Timestamp, datetime)):
                    cleaned_record[key] = str(v)
                else:
                    cleaned_record[key] = v
            preview.append(cleaned_record)
        columns = df.columns.tolist()

        return jsonify(
            {
                "success": True,
                "filename": file.filename,
                "row_count": len(df),
                "columns": columns,
                "preview": preview,
            }
        )

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "trace": traceback.format_exc()}
        )


@app.route("/api/reconcile", methods=["POST"])
def reconcile():
    """执行对账"""
    try:
        if current_task["vendor_data"] is None or current_task["internal_data"] is None:
            return jsonify({"success": False, "error": "请先上传两个文件"})

        data = request.json or {}

        # 获取列映射配置
        vendor_mapping = data.get("vendor_mapping", DEFAULT_VENDOR_MAPPING)
        internal_mapping = data.get("internal_mapping", DEFAULT_INTERNAL_MAPPING)

        # 容差设置
        price_tolerance = float(data.get("price_tolerance", 0.0001))
        qty_tolerance = float(data.get("qty_tolerance", 0))
        amount_tolerance = float(data.get("amount_tolerance", 0.01))

        # 执行对账
        result = perform_reconciliation(
            current_task["vendor_data"],
            current_task["internal_data"],
            vendor_mapping,
            internal_mapping,
            price_tolerance,
            qty_tolerance,
            amount_tolerance,
        )

        current_task["result"] = result

        return jsonify({"success": True, "result": result})

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


def perform_reconciliation(
    vendor_df,
    internal_df,
    vendor_mapping,
    internal_mapping,
    price_tolerance=0.0001,
    qty_tolerance=0,
    amount_tolerance=0.01,
):
    """
    执行对账核心逻辑
    差异分类：差异项 > 数量差异 > 单价差异 > 金额差异
    """
    # 标准化供应商数据
    vendor_std = standardize_vendor_data(vendor_df, vendor_mapping)

    # 标准化内部数据
    internal_std = standardize_internal_data(internal_df, internal_mapping)

    # 按PO号+物料编码分组
    vendor_std["po_item_key"] = (
        vendor_std["po_no"].astype(str)
        + "|"
        + vendor_std["item_code_clean"].astype(str)
    ).str.strip()
    internal_std["po_item_key"] = (
        internal_std["po_no"].astype(str) + "|" + internal_std["item_code"].astype(str)
    ).str.strip()

    # 构建PO+物料编码的映射
    vendor_grouped = (
        vendor_std.groupby("po_item_key")
        .agg(
            {
                "qty": "sum",
                "unit_price": "first",
                "amount": "sum",
                "po_no": "first",
                "item_code_clean": "first",
            }
        )
        .reset_index()
    )

    internal_grouped = (
        internal_std.groupby("po_item_key")
        .agg(
            {
                "qty": "sum",
                "unit_price": "first",
                "amount": "sum",
                "po_no": "first",
                "item_code": "first",
            }
        )
        .reset_index()
    )

    # 获取所有唯一的PO+物料编码
    all_keys = set(vendor_grouped["po_item_key"]) | set(internal_grouped["po_item_key"])

    # 分类结果
    matched_list = []
    diff_items = []  # 差异项：一方完全不存在
    diff_qty = []  # 数量差异
    diff_price = []  # 单价差异
    diff_amount = []  # 金额差异

    # 创建内部数据的索引映射
    internal_key_to_rows = {}
    for i_idx, i_row in internal_std.iterrows():
        key = i_row["po_item_key"]
        if key not in internal_key_to_rows:
            internal_key_to_rows[key] = []
        internal_key_to_rows[key].append(i_row.to_dict())

    # 创建供应商数据的索引映射
    vendor_key_to_rows = {}
    for v_idx, v_row in vendor_std.iterrows():
        key = v_row["po_item_key"]
        if key not in vendor_key_to_rows:
            vendor_key_to_rows[key] = []
        vendor_key_to_rows[key].append(v_row.to_dict())

    for key in all_keys:
        v_rows = vendor_key_to_rows.get(key, [])
        i_rows = internal_key_to_rows.get(key, [])
        vendor_refs = build_row_refs(v_rows)
        internal_refs = build_row_refs(i_rows)

        v_sum_qty = sum(r["qty"] for r in v_rows) if v_rows else 0
        i_sum_qty = sum(r["qty"] for r in i_rows) if i_rows else 0

        v_unit_price = v_rows[0]["unit_price"] if v_rows else 0
        i_unit_price = i_rows[0]["unit_price"] if i_rows else 0

        v_sum_amount = sum(r["amount"] for r in v_rows) if v_rows else 0
        i_sum_amount = sum(r["amount"] for r in i_rows) if i_rows else 0

        # 1. 差异项：一方完全没有这个PO+物料编码
        if not v_rows or not i_rows:
            diff_items.append(
                {
                    "po_no": v_rows[0]["po_no"]
                    if v_rows
                    else (i_rows[0]["po_no"] if i_rows else ""),
                    "item_code": v_rows[0]["item_code_clean"]
                    if v_rows
                    else (i_rows[0]["item_code"] if i_rows else ""),
                    "vendor_qty": v_sum_qty,
                    "internal_qty": i_sum_qty,
                    "vendor_price": v_unit_price,
                    "internal_price": i_unit_price,
                    "vendor_amount": v_sum_amount,
                    "internal_amount": i_sum_amount,
                    "vendor_rows": v_rows,
                    "internal_rows": i_rows,
                    "vendor_refs": vendor_refs,
                    "internal_refs": internal_refs,
                    "diff_type": "差异项",
                }
            )
            continue

        # 2. 数量差异：PO+物料编码匹配上了，但数量不一致
        if abs(v_sum_qty - i_sum_qty) > qty_tolerance:
            v_remain, i_remain = split_qty_residual_rows(
                v_rows, i_rows, price_tolerance
            )
            diff_qty.append(
                {
                    "po_no": v_rows[0]["po_no"],
                    "item_code": v_rows[0]["item_code_clean"],
                    "vendor_qty": v_sum_qty,
                    "internal_qty": i_sum_qty,
                    "vendor_price": v_unit_price,
                    "internal_price": i_unit_price,
                    "vendor_amount": v_sum_amount,
                    "internal_amount": i_sum_amount,
                    "vendor_rows": v_rows,
                    "internal_rows": i_rows,
                    "vendor_refs": build_row_refs(v_remain),
                    "internal_refs": build_row_refs(i_remain),
                    "diff_type": "数量差异",
                }
            )
            continue

        # 3. 单价差异：PO+物料编码匹配上了，但单价不一致
        if abs(v_unit_price - i_unit_price) > price_tolerance:
            diff_price.append(
                {
                    "po_no": v_rows[0]["po_no"],
                    "item_code": v_rows[0]["item_code_clean"],
                    "vendor_qty": v_sum_qty,
                    "internal_qty": i_sum_qty,
                    "vendor_price": v_unit_price,
                    "internal_price": i_unit_price,
                    "vendor_amount": v_sum_amount,
                    "internal_amount": i_sum_amount,
                    "vendor_rows": v_rows,
                    "internal_rows": i_rows,
                    "vendor_refs": vendor_refs,
                    "internal_refs": internal_refs,
                    "diff_type": "单价差异",
                }
            )
            continue

        # 4. 金额差异：PO+物料编码+数量+单价都匹配上了，但金额不一致
        if abs(v_sum_amount - i_sum_amount) > amount_tolerance:
            diff_amount.append(
                {
                    "po_no": v_rows[0]["po_no"],
                    "item_code": v_rows[0]["item_code_clean"],
                    "vendor_qty": v_sum_qty,
                    "internal_qty": i_sum_qty,
                    "vendor_price": v_unit_price,
                    "internal_price": i_unit_price,
                    "vendor_amount": v_sum_amount,
                    "internal_amount": i_sum_amount,
                    "vendor_rows": v_rows,
                    "internal_rows": i_rows,
                    "vendor_refs": vendor_refs,
                    "internal_refs": internal_refs,
                    "diff_type": "金额差异",
                }
            )
            continue

        # 完全匹配
        matched_list.append(
            {
                "po_no": v_rows[0]["po_no"],
                "item_code": v_rows[0]["item_code_clean"],
                "vendor_qty": v_sum_qty,
                "internal_qty": i_sum_qty,
                "vendor_price": v_unit_price,
                "internal_price": i_unit_price,
                "vendor_amount": v_sum_amount,
                "internal_amount": i_sum_amount,
                "vendor_rows": v_rows,
                "internal_rows": i_rows,
                "vendor_refs": vendor_refs,
                "internal_refs": internal_refs,
                "diff_type": "完全匹配",
            }
        )

    # 计算统计信息
    total_vendor_amount = vendor_std["amount"].sum() if len(vendor_std) > 0 else 0
    total_internal_amount = internal_std["amount"].sum() if len(internal_std) > 0 else 0
    matched_amount = sum(m["vendor_amount"] for m in matched_list)
    matched_display_count = sum(
        max(len(m.get("vendor_refs", [])), len(m.get("internal_refs", [])), 1)
        for m in matched_list
    )
    diff_items_display_count = sum(
        max(len(m.get("vendor_refs", [])), len(m.get("internal_refs", [])), 1)
        for m in diff_items
    )
    diff_qty_display_count = sum(
        max(len(m.get("vendor_refs", [])), len(m.get("internal_refs", [])), 1)
        for m in diff_qty
    )
    diff_price_display_count = sum(
        max(len(m.get("vendor_refs", [])), len(m.get("internal_refs", [])), 1)
        for m in diff_price
    )
    diff_amount_display_count = sum(
        max(len(m.get("vendor_refs", [])), len(m.get("internal_refs", [])), 1)
        for m in diff_amount
    )

    matched_vendor_lines = sum(len(m.get("vendor_rows", [])) for m in matched_list)
    matched_internal_lines = sum(len(m.get("internal_rows", [])) for m in matched_list)
    diff_items_vendor_lines = sum(len(m.get("vendor_rows", [])) for m in diff_items)
    diff_items_internal_lines = sum(len(m.get("internal_rows", [])) for m in diff_items)
    diff_qty_vendor_lines = sum(len(m.get("vendor_rows", [])) for m in diff_qty)
    diff_qty_internal_lines = sum(len(m.get("internal_rows", [])) for m in diff_qty)
    diff_price_vendor_lines = sum(len(m.get("vendor_rows", [])) for m in diff_price)
    diff_price_internal_lines = sum(len(m.get("internal_rows", [])) for m in diff_price)
    diff_amount_vendor_lines = sum(len(m.get("vendor_rows", [])) for m in diff_amount)
    diff_amount_internal_lines = sum(
        len(m.get("internal_rows", [])) for m in diff_amount
    )

    result = {
        "summary": {
            "vendor_total_rows": len(vendor_std),
            "internal_total_rows": len(internal_std),
            "vendor_total_amount": round(total_vendor_amount, 2),
            "internal_total_amount": round(total_internal_amount, 2),
            "matched_vendor_lines": matched_vendor_lines,
            "matched_internal_lines": matched_internal_lines,
            "diff_items_vendor_lines": diff_items_vendor_lines,
            "diff_items_internal_lines": diff_items_internal_lines,
            "diff_qty_vendor_lines": diff_qty_vendor_lines,
            "diff_qty_internal_lines": diff_qty_internal_lines,
            "diff_price_vendor_lines": diff_price_vendor_lines,
            "diff_price_internal_lines": diff_price_internal_lines,
            "diff_amount_vendor_lines": diff_amount_vendor_lines,
            "diff_amount_internal_lines": diff_amount_internal_lines,
            "matched_count": len(matched_list),
            "matched_display_count": matched_display_count,
            "diff_items_count": len(diff_items),
            "diff_qty_count": len(diff_qty),
            "diff_price_count": len(diff_price),
            "diff_amount_count": len(diff_amount),
            "diff_items_display_count": diff_items_display_count,
            "diff_qty_display_count": diff_qty_display_count,
            "diff_price_display_count": diff_price_display_count,
            "diff_amount_display_count": diff_amount_display_count,
            "matched_amount": round(matched_amount, 2),
            "diff_amount": round(total_vendor_amount - total_internal_amount, 2),
        },
        "matched_list": matched_list,
        "diff_items": diff_items,
        "diff_qty": diff_qty,
        "diff_price": diff_price,
        "diff_amount": diff_amount,
    }

    return clean_dict(result)


def standardize_vendor_data(df, mapping):
    """标准化供应商数据"""
    std_data = pd.DataFrame()
    std_data["row_no"] = df.index + 1

    # 列名映射
    column_map = {
        "po_no": mapping.get("po_no", "订单号码"),
        "item_code_raw": mapping.get("item_code", "物料编码"),
        "item_name": mapping.get("item_name", "品名"),
        "qty": mapping.get("qty", "数量"),
        "unit_price": mapping.get("unit_price", "单价"),
        "amount": mapping.get("amount", "金额"),
    }

    # 提取数据
    for std_col, orig_col in column_map.items():
        if orig_col in df.columns:
            std_data[std_col] = df[orig_col]
        else:
            std_data[std_col] = None

    # 数据清洗
    # 数量转换为整数
    std_data["qty"] = (
        pd.to_numeric(std_data["qty"], errors="coerce").fillna(0).astype(int)
    )

    # 单价标准化为4位小数
    std_data["unit_price"] = pd.to_numeric(
        std_data["unit_price"], errors="coerce"
    ).fillna(0)
    std_data["unit_price"] = std_data["unit_price"].round(4)

    # 金额计算
    std_data["amount"] = pd.to_numeric(std_data["amount"], errors="coerce").fillna(0)

    # 物料编码清洗
    std_data["item_code_clean"] = std_data["item_code_raw"].astype(str).str.strip()

    return std_data


def standardize_internal_data(df, mapping):
    """标准化内部数据"""
    std_data = pd.DataFrame()
    std_data["row_no"] = df.index + 1

    # 列名映射
    column_map = {
        "po_no": mapping.get("po_no", "订单单号"),
        "item_code": mapping.get("item_code", "物料编码"),
        "item_name": mapping.get("item_name", "物料名称"),
        "spec": mapping.get("spec", "规格型号"),
        "qty": mapping.get("qty", "实收数量"),
        "unit_price": mapping.get("unit_price", "含税单价"),
        "amount": mapping.get("amount", "价税合计"),
    }

    # 提取数据
    for std_col, orig_col in column_map.items():
        if orig_col in df.columns:
            std_data[std_col] = df[orig_col]
        else:
            std_data[std_col] = None

    # 数据清洗
    std_data["qty"] = (
        pd.to_numeric(std_data["qty"], errors="coerce").fillna(0).astype(int)
    )
    std_data["unit_price"] = (
        pd.to_numeric(std_data["unit_price"], errors="coerce").fillna(0).round(4)
    )
    std_data["amount"] = pd.to_numeric(std_data["amount"], errors="coerce").fillna(0)
    std_data["item_code"] = std_data["item_code"].astype(str).str.strip()

    return std_data


def perform_aggregate_matching(
    vendor_unmatched,
    internal_unmatched,
    price_tolerance,
    qty_tolerance,
    amount_tolerance,
):
    """执行聚合匹配"""
    if len(vendor_unmatched) == 0 or len(internal_unmatched) == 0:
        return []

    matched_groups = []

    # 按物料编码和单价分组
    vendor_groups = vendor_unmatched.groupby(["item_code_clean", "unit_price"])
    internal_groups = internal_unmatched.groupby(["item_code", "unit_price"])

    for (v_code, v_price), v_group in vendor_groups:
        v_qty_sum = v_group["qty"].sum()
        v_amount_sum = v_group["amount"].sum()

        # 查找匹配的内部组
        for (i_code, i_price), i_group in internal_groups:
            if v_code == i_code:
                price_diff = abs(v_price - i_price)

                if price_diff <= price_tolerance:
                    i_qty_sum = i_group["qty"].sum()
                    i_amount_sum = i_group["amount"].sum()

                    qty_diff = abs(v_qty_sum - i_qty_sum)
                    amount_diff = abs(v_amount_sum - i_amount_sum)

                    if qty_diff <= qty_tolerance and amount_diff <= amount_tolerance:
                        # 聚合匹配成功
                        matched_groups.append(
                            {
                                "match_type": "AGGREGATE",
                                "item_code": v_code,
                                "unit_price": v_price,
                                "vendor_sum_qty": v_qty_sum,
                                "internal_sum_qty": i_qty_sum,
                                "vendor_sum_amount": v_amount_sum,
                                "internal_sum_amount": i_amount_sum,
                                "diff_qty": qty_diff,
                                "diff_amount": amount_diff,
                                "vendor_rows": v_group.to_dict("records"),
                                "internal_rows": i_group.to_dict("records"),
                            }
                        )
                        break

    return matched_groups


def classify_issues(unmatched_vendor, unmatched_internal, vendor_std, internal_std):
    """分类差异类型"""
    issues = []

    # 检查供应商侧的差异
    for v_row in unmatched_vendor:
        # 检查物料是否存在
        item_exists = any(
            str(v_row["item_code_clean"]) == str(i_row["item_code"])
            for i_row in internal_std.to_dict("records")
        )

        if not item_exists:
            issue_type = "material_unmapped"
        else:
            # 物料存在但无法匹配，可能是数量或价格差异
            issue_type = "qty_price_diff"

        issues.append(
            {
                "side": "vendor",
                "issue_type": issue_type,
                "item_code": v_row["item_code_clean"],
                "qty": v_row["qty"],
                "unit_price": v_row["unit_price"],
                "amount": v_row["amount"],
            }
        )

    # 检查内部侧的差异
    for i_row in unmatched_internal:
        item_exists = any(
            str(v_row["item_code_clean"]) == str(i_row["item_code"])
            for v_row in vendor_std.to_dict("records")
        )

        if not item_exists:
            issue_type = "only_internal"
        else:
            issue_type = "qty_price_diff"

        issues.append(
            {
                "side": "internal",
                "issue_type": issue_type,
                "item_code": i_row["item_code"],
                "qty": i_row["qty"],
                "unit_price": i_row["unit_price"],
                "amount": i_row["amount"],
            }
        )

    return issues


@app.route("/api/export", methods=["POST"])
def export_results():
    """导出对账结果"""
    try:
        if current_task["result"] is None:
            return jsonify({"success": False, "error": "没有可导出的结果"})

        result = current_task["result"]
        export_type = request.json.get("type", "all")

        # 创建Excel文件
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 汇总表
            summary_df = pd.DataFrame([result["summary"]])
            summary_df.to_excel(writer, sheet_name="汇总", index=False)

            # 完全匹配明细
            if result.get("matched_list"):
                matched_df = pd.DataFrame(
                    [
                        {
                            "PO号": m["po_no"],
                            "物料编码": m["item_code"],
                            "供应商数量": m["vendor_qty"],
                            "系统数量": m["internal_qty"],
                            "供应商单价": m["vendor_price"],
                            "系统单价": m["internal_price"],
                            "供应商金额": m["vendor_amount"],
                            "系统金额": m["internal_amount"],
                        }
                        for m in result["matched_list"]
                    ]
                )
                matched_df.to_excel(writer, sheet_name="完全匹配", index=False)

            # 差异项
            if result.get("diff_items"):
                diff_items_df = pd.DataFrame(
                    [
                        {
                            "差异类型": "差异项",
                            "PO号": m["po_no"],
                            "物料编码": m["item_code"],
                            "供应商数量": m["vendor_qty"],
                            "系统数量": m["internal_qty"],
                            "供应商单价": m["vendor_price"],
                            "系统单价": m["internal_price"],
                            "供应商金额": m["vendor_amount"],
                            "系统金额": m["internal_amount"],
                        }
                        for m in result["diff_items"]
                    ]
                )
                diff_items_df.to_excel(writer, sheet_name="差异项", index=False)

            # 数量差异
            if result.get("diff_qty"):
                diff_qty_df = pd.DataFrame(
                    [
                        {
                            "差异类型": "数量差异",
                            "PO号": m["po_no"],
                            "物料编码": m["item_code"],
                            "供应商数量": m["vendor_qty"],
                            "系统数量": m["internal_qty"],
                            "供应商单价": m["vendor_price"],
                            "系统单价": m["internal_price"],
                            "供应商金额": m["vendor_amount"],
                            "系统金额": m["internal_amount"],
                        }
                        for m in result["diff_qty"]
                    ]
                )
                diff_qty_df.to_excel(writer, sheet_name="数量差异", index=False)

            # 单价差异
            if result.get("diff_price"):
                diff_price_df = pd.DataFrame(
                    [
                        {
                            "差异类型": "单价差异",
                            "PO号": m["po_no"],
                            "物料编码": m["item_code"],
                            "供应商数量": m["vendor_qty"],
                            "系统数量": m["internal_qty"],
                            "供应商单价": m["vendor_price"],
                            "系统单价": m["internal_price"],
                            "供应商金额": m["vendor_amount"],
                            "系统金额": m["internal_amount"],
                        }
                        for m in result["diff_price"]
                    ]
                )
                diff_price_df.to_excel(writer, sheet_name="单价差异", index=False)

            # 金额差异
            if result.get("diff_amount"):
                diff_amount_df = pd.DataFrame(
                    [
                        {
                            "差异类型": "金额差异",
                            "PO号": m["po_no"],
                            "物料编码": m["item_code"],
                            "供应商数量": m["vendor_qty"],
                            "系统数量": m["internal_qty"],
                            "供应商单价": m["vendor_price"],
                            "系统单价": m["internal_price"],
                            "供应商金额": m["vendor_amount"],
                            "系统金额": m["internal_amount"],
                        }
                        for m in result["diff_amount"]
                    ]
                )
                diff_amount_df.to_excel(writer, sheet_name="金额差异", index=False)

        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"对账结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        )

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
