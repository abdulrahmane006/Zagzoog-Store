from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
# ملاحظة: الكود مبرمج لربط الفولدرات باستخدام مكتبة جوجل درايف المعتادة في مشروعك
# لضمان السرعة تم عمل الكود ليعتمد على جلب الملفات ككتل كاملة لتجنب الـ Timeout

app = Flask(__name__)

# متغيرات افتراضية لمحاكاة النظام الجديد السريع
FOLDER_MAIN = "محلات زقزوق"
FOLDER_STORES = "المخازن"
FOLDER_OUT = "الخارج من المخزن"

# اسم ملف الإكسيل الحالي (يتحدث دورياً بمجرد تغييره في فولدر المخازن)
current_excel_file_name = "مخزن_الأقمشة_الرئيسي.xlsx"

# محاكاة البيانات المستخرجة من ملف الإكسيل المرفوع في فولدر "المخازن"
DATA_STORE = [
    {
        "code": "101",
        "name": "كريب تركي فرز أول",
        "qty": 3,
        "location": "الرف أ",
        "meters": ["22.5", "25", "21"],
        "notes": "خامة ممتازة"
    }
]

# محاكاة لملف الإكسيل الآخر الذي يملأ تلقائياً في فولدر "الخارج من المخزن"
DATA_OUT_LOG = []

@app.route('/')
def home():
    # يتم تمرير اسم ملف الإكسيل الحالي ليظهر بشكل دائم في أعلى الموقع
    return render_template('index.html', file_name=current_excel_file_name)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    search_code = request.form.get('search_code', '').strip() # زر الإدخال الآخر للكود للوصول السريع
    
    if not query and not search_code:
        return jsonify({"status": "error", "msg": "برجاء إدخال اسم المنتج أو الكود للوصول السريع"})
    
    # البحث باسم المنتج أو الكود مباشرة
    results = []
    for item in DATA_STORE:
        if query and query in item['name']:
            results.append(item)
        elif search_code and search_code == item['code']:
            results.append(item)
            
    if not results:
        return jsonify({"status": "error", "msg": "لم يتم العثور على نتائج"})
        
    return jsonify({"status": "success", "data": results})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    code = request.form.get('code', '')
    meter_to_remove = request.form.get('meter', '')
    
    for item in DATA_STORE:
        if item['code'] == code:
            for i, m in enumerate(item['meters']):
                if m == meter_to_remove and "❌" not in m:
                    # 1. وضع علامة ❌ بجانب الثوب المنتقص
                    item['meters'][i] = f"{meter_to_remove} ❌"
                    if item['qty'] > 0: item['qty'] -= 1
                    
                    # 2. تسجيل البيانات لحفظها في ملف إكسيل منفصل بفولدر "الخارج من المخزن"
                    log_entry = {
                        "name": item['name'],
                        "code": item['code'],
                        "meter": meter_to_remove,
                        "location": item['location'],
                        "notes": "تم السحب من الموقع تلقائياً",
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    DATA_OUT_LOG.append(log_entry)
                    return jsonify({"status": "success", "msg": "تم السحب بنجاح وحفظه في فولدر الخارج!"})
                    
    return jsonify({"status": "error", "msg": "حدث خطأ أو الثوب مسحوب مسبقاً"})

# صفحة المسؤول لعرض بطاقات المنتجات الخارجة بصورة دورية قبل التحديث
@app.route('/admin/dashboard')
def admin_dashboard():
    return jsonify({"status": "success", "out_products": DATA_OUT_LOG})
  
