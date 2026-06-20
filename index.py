import os
from flask import Flask, render_template, request, jsonify
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
app.secret_key = 'zagzoog_secret_key'

# إعدادات جوجل المدمجة مباشرة برابط الشيت ورابط مجلد الصور الخاص بك
SPREADSHEET_ID = '1wFyuzLaPt8Rno9PvAy0ouAQYCESVo44jTpLX6MCwllA'
IMAGES_FOLDER_ID = '1zO88nBb-2yrv7jPXMm6r1hrVerkESIbi'

# بيانات الاعتماد المسؤولة عن الربط الحديدي بدرايف بدون ملفات خارجية
GOOGLE_CREDS_INFO = {
  "type": "service_account",
  "project_id": "zagzoog-store",
  "private_key_id": "f30ff0742cf5e22f43b209c5487bcf11c1123747",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD00HY68904Pf13\nZ6cIP9q5URYHPGfK/NzjIKq+tzygeaAdaf+tfZLSJgI+X7SgqVHaUO31vjlDcMyC\nyNeTRc3MZjeoht8bvMhEHCdgcUIN9munLFC7hvAb89ljA1B7p7f88QzJbyPC6yhK\nt4PoTHUvbHDfFSZ/QHywLzwiXBYjavI7poJGaB8QssFHs8YpPNRJz6AVXxvdavAE\n0kLRyl0WPOlWYGcAkDUR+NfynwhEmgx6aezYrn6J7ReiC2EPWDHQGKpyPN4JtNlU\nw5/wZZ01bK+FN/ae9ghkg8EUjX8buyqkL/nQ7RKqa80uU8zAexPiiDQAv08wPi3k\nLgAj7MTzAgMBAAECggEATcQSanOgqAb5Bv8EDhjKj+d0CeRkTBS6zeNImcB3H7rC\n49USBLhI9TxhphKcvBRNDf57OH6ujf+81yaZZAzebLljoMMHCDaVnx0aXQZdJzZJ\nyBbJpmgcyaRSP6OD42PJjC2+FBab04UDjYhx/E6dQu09hX+gdPe1I/o9LeT2m1T0\nfGyseroTG55n3Yf6ZG/iuxMLfkON/1XdfShvwpQQJozeaQ+nKBH9UlEVJDHftZbZ\npoyq2I9fzHPN+uPDTMlVeSDIsMGGzOCMJe0dY+mkS8+H1O70WMQHZXOz/y/LWtib\n6jl/MKIKPUZft9m5L6zpsrPirOSs0h39wOgkZ5sQIQKBgQD/n+G5FfYkFGy7Hm3R\niFxuTsiQ6BNPKsazECs0zEzm+LJ1ml3A0SvZjuymgqH32VUwEmpBTV8UChNP22uU\n91/yNfsaExMgmOHjKPdJ0TWv061+0iN31+E6CIo1BgzGfFn+d5Zu7li90KxHesEK\nJFe0+KADlRLE7A8hXl4AgH/M+wKBgQD1LIPrjfhEKBsv/x7zRUjiY+yWzBymRVjY\n2Fh9a5UWXO6QF59ieyC04hMDKQWmDl7ElPo3tyimu4VX8B4cNua79/zuCB8x0KaU\nzBZGUdzra8iKVt36nMZZUoRjODFAQEyaP0YgZBn3Dp4vX5dfAt3Tiyz2PvhLH6CA\nyuYLGjJ2aQKBgQDKwfeaBqhxX94K4gz7iWy/djAyeFJwlh57g9SxkWdiQVvUWngI\n7CEa9PoS7UUpwbKHaePsHkHPNFqzGfkQdNMe3OBqgzzFu15Y/3J+k7A1+ci0+2c\nLpkQnht6CW1ytsnvRM4G+XlcPjuYiu65a7BB9H9/t+vmVNN/hUmMnmBApwKBgDnR\nMJ75EOYJyzeLY2IdIa35wI5jPhJb4jLo+h1BpJvseHnUiEqyHKlrcu5Y2zMoymJz\ne3puIBEJwc1WG9OtgsYrGiOMGMcnnFEUu+ADaCTAez9ccuap2ACye/PmCX9MaoQp\njcEPuivP76/eTBUk2OkNNiIwAV+96pzUvGE74VCZAoGBAIsCaT+Y6QODxUxvBJis\ngo9Hx1mIEy37q2ao3Iv8JAkAt5qb8VvL0Q2FhD5VNh3TLfdMV+2PDm2LpnAGyTiN\nl1MlOoVmDu6Fhqf4OMuod7vpQmSZfo3h+VdawrUpzEzMzB7wVCZZaFc6mf7dbWNR\nwIAB5RRSYZ3w2dMgMTpLY1nx\n-----END PRIVATE KEY-----\n",
  "client_email": "drive-bot@zagzoog-store.iam.gserviceaccount.com",
  "client_id": "109347724948706389584",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/drive-bot%40zagzoog-store.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

def get_drive_services():
    creds = Credentials.from_service_account_info(GOOGLE_CREDS_INFO, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds), build('sheets', 'v4', credentials=creds)

def get_egypt_time():
    egypt_now = datetime.utcnow() + timedelta(hours=3)
    date_str = egypt_now.strftime("%d/%m/%Y")
    time_str = egypt_now.strftime("%I:%M").lstrip("0")
    ampm = "م" if egypt_now.strftime("%p") == "PM" else "ص"
    return date_str, f"{time_str} {ampm}"

def load_store_data():
    _, sheets_service = get_drive_services()
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:G'
    ).execute()
    rows = result.get('values', [])
    if not rows:
        return pd.DataFrame(columns=["الكود", "اسم النوع", "الأثواب المتاحة", "المكان", "الأمتار بالتفصيل", "التاريخ", "الوقت"])
    return pd.DataFrame(rows[1:], columns=rows[0])

def save_store_data(df):
    _, sheets_service = get_drive_services()
    raw_data = [df.columns.tolist()] + df.values.tolist()
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range='Sheet1!A:G',
        valueInputOption='USER_ENTERED', body={'values': raw_data}
    ).execute()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    if not query:
        return jsonify({'status': 'empty', 'msg': 'يرجى كتابة نص للبحث'})
    
    df = load_store_data()
    if df.empty:
        return jsonify({'status': 'no_data', 'msg': 'المخزن فارغ حالياً'})

    # حظر ومطالبة العمال بكتابة الاسم أولاً قبل الأكواد المنفردة
    if query.isalnum() and not any(c.isalpha() for c in query):
        if query in df['الكود'].values and not any(query in name for name in df['اسم النوع'].values):
            return jsonify({'status': 'error', 'msg': 'يرجى كتابة اسم الخامة أولاً لإظهار البيانات'})

    res = df[
        df['اسم النوع'].str.contains(query, case=False, na=False) |
        df.apply(lambda r: query in f"{r['اسم النوع']} {r['الكود']}", axis=1)
    ]

    if res.empty:
        return jsonify({'status': 'not_found', 'msg': 'لا توجد نتائج تطابق هذا البحث'})

    cards = []
    for idx, row in res.iterrows():
        cards.append({
            'index': int(idx),
            'name': row['اسم النوع'],
            'code': row['الكود'],
            'qty': row['الأثواب المتاحة'],
            'location': row['المكان'],
            'meters': str(row.get('الأمتار بالتفصيل', '')).split(),
            'date': row.get('التاريخ', '-'),
            'time': row.get('الوقت', '-')
        })
    return jsonify({'status': 'success', 'data': cards})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    idx = int(request.form.get('idx'))
    selected_meter = request.form.get('meter')
    file = request.files.get('photo')

    df = load_store_data()
    row = df.loc[idx].copy()

    meters_list = str(row['الأمتار بالتفصيل']).split()
    updated_meters = []
    for m in meters_list:
        if m == selected_meter and not m.endswith('❌'):
            updated_meters.append(f"{m}❌")
        else:
            updated_meters.append(m)
    
    df.at[idx, 'الأمتار بالتفصيل'] = " ".join(updated_meters)
    
    current_qty = int(row['الأثواب المتاحة'])
    if current_qty > 0:
        df.at[idx, 'الأثواب المتاحة'] = str(current_qty - 1)

    current_date, current_time = get_egypt_time()
    df.at[idx, 'التاريخ'] = current_date
    df.at[idx, 'الوقت'] = current_time

    if file:
        filename = secure_filename(f"{row['الكود']}_{current_date.replace('/', '-')}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        drive_service, _ = get_drive_services()
        media = MediaFileUpload(filepath, mimetype='image/jpeg')
        drive_service.files().create(body={'name': filename, 'parents': [IMAGES_FOLDER_ID]}, media_body=media).execute()
        os.remove(filepath)

    save_store_data(df)
    return jsonify({'status': 'success', 'msg': 'تم تسجيل سحب الثوب وتحديث البيانات وصورته لحظياً في درايف'})

@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    if request.form.get('pass_code') != "404":
        return "كود الدخول غير صحيح", 403
    file = request.files.get('excel_file')
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filepath)
        new_df = pd.read_excel(filepath)
        current_date, current_time = get_egypt_time()
        new_df['التاريخ'] = current_date
        new_df['الوقت'] = current_time
        save_store_data(new_df)
        os.remove(filepath)
        return "✓ تم تطهير المخزن وتحديث البيانات بالكامل بنجاح"
    return "يرجى اختيار ملف", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
      
