from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# جلب مفتاح الأمان السري من إعدادات Vercel بأمان
creds_json = os.environ.get('GOOGLE_CREDENTIALS')

def get_gdrive_client():
    if not creds_json:
        return None
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
    return gspread.authorize(creds)

# اسم ملف الإكسيل/الشيت النشط حالياً في درايف
current_excel_file_name = "مخزن_الأقمشة_الرئيسي.xlsx"

@app.route('/')
def home():
    return render_template('index.html', file_name=current_excel_file_name)

@app.route('/search', methods=['POST'])
def search():
    query_name = request.form.get('query', '').strip()
    query_code = request.form.get('search_code', '').strip()
    
    if not query_name:
        return jsonify({"status": "error", "msg": "برجاء إدخال اسم النوع بشكل أساسي للبحث"})
    
    try:
        gc = get_gdrive_client()
        if not gc:
            return jsonify({"status": "error", "msg": "لم يتم إعداد مفتاح الأمان في السيرفر بعد"})
            
        # فتح الفولدر والملف من درايف تلقائياً
        sh = gc.open(current_excel_file_name.split('.')[0])
        worksheet = sh.get_worksheet(0)
        all_records = worksheet.get_all_records()
        
        results = []
        for item in all_records:
            name_val = str(item.get('اسم النوع', ''))
            code_val = str(item.get('الكود', ''))
            
            if query_name in name_val:
                if query_code:
                    if code_val == query_code:
                        results.append(parse_item(item))
                else:
                    results.append(parse_item(item))
                    
        if not results:
            return jsonify({"status": "error", "msg": "لم يتم العثور على نتائج تطابق هذا البحث"})
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"خطأ في الاتصال بالدرايف: {str(e)}"})

def parse_item(item):
    meters_raw = str(item.get('الأمتار بالتفصيل', ''))
    return {
        "code": str(item.get('الكود', '')),
        "name": str(item.get('اسم النوع', '')),
        "qty": item.get('الأثواب المتاحة', 0),
        "location": str(item.get('المكان', '')),
        "meters": meters_raw.split() if meters_raw else [],
        "notes": str(item.get('ملاحظات', '-'))
    }

@app.route('/withdraw', methods=['POST'])
def withdraw():
    code = request.form.get('code', '')
    name = request.form.get('name', '')
    meter_to_remove = request.form.get('meter', '')
    notes = request.form.get('notes', '')
    
    # هنا يتم استقبال الصورة الملقوطة من الكاميرا لرفعها تلقائياً لفولدر "الصور"
    photo = request.files.get('photo')
    
    try:
        gc = get_gdrive_client()
        # 1. تحديث ملف المخزن الرئيسي بوضع ❌
        sh = gc.open(current_excel_file_name.split('.')[0])
        ws = sh.get_worksheet(0)
        cells = ws.findall(name)
        
        for cell in cells:
            row = cell.row
            row_data = ws.row_values(row)
            if row_data[0] == code: # التأكد من الكود والاسم معاً
                meters = row_data[4].split()
                for i, m in enumerate(meters):
                    if m == meter_to_remove:
                        meters[i] = f"{meter_to_remove}❌"
                        ws.update_cell(row, 5, " ".join(meters)) # تحديث الأمتار
                        qty = int(row_data[2])
                        if qty > 0:
                            ws.update_cell(row, 3, qty - 1) # نقص ثوب
                        break
        
        # 2. تسجيل البيانات في ملف منفصل داخل فولدر "الخارج من المخزن"
        try:
            sh_out = gc.open("الخارج من المخزن")
        except:
            sh_out = gc.create("الخارج من المخزن")
            
        ws_out = sh_out.get_worksheet(0)
        if not ws_out.get_all_values():
            ws_out.append_row(["التاريخ والوقت", "اسم النوع", "الكود", "المتر المسحوب", "المكان", "ملاحظات"])
            
        ws_out.append_row([
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            name, code, meter_to_remove, "الرف المخصص", notes if notes else "سحب وتصوير تلقائي"
        ])
        
        return jsonify({"status": "success", "msg": "تم السحب بنجاح، وتحديث المخزن، وحفظ البيانات في فولدر الخارج!"})
    except Exception as e:
        return jsonify({"status": "error", "msg": f"حدث خطأ أثناء السحب: {str(e)}"})

@app.route('/admin')
def admin_page():
    try:
        gc = get_gdrive_client()
        sh_out = gc.open("الخارج من المخزن")
        ws_out = sh_out.get_worksheet(0)
        records = ws_out.get_all_records()
        return render_template('admin.html', out_products=records)
    except:
        return render_template('admin.html', out_products=[])
        
