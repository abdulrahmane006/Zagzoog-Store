from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# اسم ملف الإكسيل النشط حالياً في درايف
current_excel_file_name = "مخزن_الأقمشة_الرئيسي.xlsx"

# بيانات تجريبية ثابتة ومحاكاة لما يتم قراءته من فولدر "المخازن"
DATA_STORE = [
    {
        "code": "101",
        "name": "كريب تركي فرز أول",
        "qty": 3,
        "location": "الرف أ",
        "meters": ["22.5", "25", "21"],
        "notes": "خامة ممتازة وارد دبي"
    },
    {
        "code": "101",
        "name": "كريب تركي فرز ثاني",
        "qty": 5,
        "location": "الرف ب",
        "meters": ["18", "19.5"],
        "notes": "كود مكرر للتجربة"
    }
]

# السجل المخصص لملف إكسيل "الخارج من المخزن" (يملأ تلقائياً)
DATA_OUT_LOG = [
    {
        "name": "حرير إيطالي سوبر",
        "code": "105",
        "meter": "24.5",
        "location": "الرف ج",
        "notes": "خروج كعينة للعميل",
        "date": "2026-06-20 15:30"
    }
]

@app.route('/')
def home():
    return render_template('index.html', file_name=current_excel_file_name)

# صفحة المسؤول المنفصلة
@app.route('/admin')
def admin_page():
    return render_template('admin.html', out_products=DATA_OUT_LOG)

@app.route('/search', methods=['POST'])
def search():
    query_name = request.form.get('query', '').strip()
    query_code = request.form.get('search_code', '').strip()
    
    if not query_name:
        return jsonify({"status": "error", "msg": "برجاء إدخال اسم النوع بشكل أساسي للبحث"})
    
    results = []
    for item in DATA_STORE:
        # البحث بالنوع (أو النوع والكود معاً إذا تم إدخال الكود)
        if query_name in item['name']:
            if query_code:
                if item['code'] == query_code:
                    results.append(item)
            else:
                results.append(item)
                
    if not results:
        return jsonify({"status": "error", "msg": "لم يتم العثور على نتائج تطابق هذا البحث"})
        
    return jsonify({"status": "success", "data": results})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    code = request.form.get('code', '')
    name = request.form.get('name', '')
    meter_to_remove = request.form.get('meter', '')
    notes = request.form.get('notes', '')
    
    # هنا الكود يستقبل الصورة لرفعها في فولدر "الصور" داخل "الخارج من المخزن"
    photo = request.files.get('photo')
    
    for item in DATA_STORE:
        if item['code'] == code and item['name'] == name:
            for i, m in enumerate(item['meters']):
                if m == meter_to_remove and "❌" not in m:
                    # 1. وضع علامة ❌ بجانب الثوب المنتقص
                    item['meters'][i] = f"{meter_to_remove} ❌"
                    if item['qty'] > 0: 
                        item['qty'] -= 1
                    
                    # 2. حفظ البيانات تلقائياً في سجل "الخارج من المخزن"
                    log_entry = {
                        "name": item['name'],
                        "code": item['code'],
                        "meter": meter_to_remove,
                        "location": item['location'],
                        "notes": notes if notes else "تم السحب والتصوير تلقائياً",
                        "date": datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    DATA_OUT_LOG.append(log_entry)
                    return jsonify({"status": "success", "msg": "تم تسجيل السحب بنجاح، وجاري حفظ الصورة في فولدر (الصور)!"})
                    
    return jsonify({"status": "error", "msg": "حدث خطأ أثناء تسجيل السحب"})
    
