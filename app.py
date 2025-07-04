from flask import Flask, render_template, request, redirect, url_for, make_response
from functools import wraps
import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, auth as admin_auth
from flask import session as flask_session
from flask import abort

from otimcorte.sap import obter_dados_do_sap
from otimcorte.logic import adjust_planned, best_fit_grouped
from otimcorte.unitary_optimizer import find_optimal_combinations
from livereload import Server

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

cred = credentials.Certificate('riofer-537b0-firebase-adminsdk-buo66-13151ce8e2.json')
firebase_admin.initialize_app(cred)

data_cache = {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_cookie = request.cookies.get('session')
        print('Session cookie:', session_cookie)
        if not session_cookie:
            return redirect(url_for('login'))
        try:
            decoded_claims = admin_auth.verify_session_cookie(session_cookie, check_revoked=True)
            request.user = decoded_claims
        except Exception:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/sessionLogin', methods=['POST'])
def session_login():
    data = request.get_json()
    id_token = data.get('idToken')
    if not id_token:
        return 'Token ausente', 400
    try:
        expires_in = 60 * 60 * 24 * 5  # 5 dias
        session_cookie = admin_auth.create_session_cookie(id_token, expires_in=expires_in)
        response = make_response('Login OK')
        response.set_cookie('session', session_cookie, max_age=expires_in, httponly=True, secure=False)
        return response
    except Exception as e:
        return 'Erro ao criar sessão', 401

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response

def get_full_data():
    if 'full_df' not in data_cache:
        df = obter_dados_do_sap()
        numeric_cols = ['Estoque', 'EstoqueMax', 'EstoqueMin', 'DispPkl', 'Desenvolvimento', 'Comprimento', 'Espessura', 'Planejado']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        data_cache['full_df'] = df
    return data_cache['full_df']

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/', methods=['GET'])
@login_required
def index():
    df = get_full_data().copy()
    if 'Considerar no cálculo' not in df.columns:
        df['Considerar no cálculo'] = True
    if 'Variação de espessura' not in df.columns:
        df['Variação de espessura'] = 0
    return render_template('index.html', data=df.to_dict(orient='records'))

@app.route('/input-plates', methods=['POST'])
@login_required
def input_plates():
    data = request.form.get('data')
    df = pd.read_json(data)
    df_to_process = df[df['Considerar no cálculo']].copy()
    if df_to_process.empty:
        return redirect(url_for('index'))
    df_to_process['SheetLengthType'] = df_to_process['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')
    plate_types = df_to_process.groupby(['Espessura', 'SheetLengthType']).size().reset_index().to_dict(orient='records')
    return render_template('input_plates.html', plate_types=plate_types, original_data=data)

@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    original_data = request.form.get('original_data')
    df = pd.read_json(original_data)
    df_to_process = df[df['Considerar no cálculo']].copy()
    df_to_process['ToCut'] = df_to_process.apply(adjust_planned, axis=1)
    df_to_process['EstoqueFinal'] = df_to_process['Estoque'] + df_to_process['ToCut']
    df_to_process['SheetLengthType'] = df_to_process['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')

    plate_widths = {}
    for key, value in request.form.items():
        if key.startswith('width_'):
            parts = key.replace('width_', '').split('_')
            esp = float(parts[0])
            sheet_type = parts[1]
            plate_widths[(esp, sheet_type)] = int(value)

    groups = df_to_process.groupby(['Espessura', 'SheetLengthType'])
    report = []
    total_sheets = 0
    for (esp, sheet_type), group in groups:
        entries = []
        for _, row in group.iterrows():
            qty = min(row['ToCut'], row['DispPkl'])
            desenvolvimento = row['Desenvolvimento']
            variacao = row['Variação de espessura']
            desenvolvimentos = [desenvolvimento]
            if variacao > 0:
                desenvolvimentos = range(int(desenvolvimento - variacao), int(desenvolvimento + variacao + 1))
            for dev in desenvolvimentos:
                for _ in range(int(qty)):
                    entries.append({
                        'size': dev,
                        'item': {
                            'code': row['ItemCode'], 'name': row['ItemName'], 'Estoque': row['Estoque'],
                            'ToCut': row['ToCut'], 'EstoqueFinal': row['EstoqueFinal'],
                            'EstoqueMin': row['EstoqueMin'], 'EstoqueMax': row['EstoqueMax']
                        }
                    })
        if not entries: continue
        sheet_width = plate_widths.get((esp, sheet_type), 1200)
        summary, count = best_fit_grouped(entries, sheet_width=sheet_width)
        total_sheets += count
        report.append({'espessura': esp, 'tipo': sheet_type, 'summary': summary, 'sheet_count': count})

    resumo_final = df_to_process[['ItemCode', 'ItemName', 'Estoque', 'ToCut', 'EstoqueFinal', 'EstoqueMin', 'EstoqueMax']]
    items = resumo_final.drop_duplicates(subset=['ItemCode']).to_dict(orient='records')
    data_cache['summary_items'] = items
    return render_template('report.html', report=report, total_sheets=total_sheets, items=items)

@app.route('/optimize/<item_code>', methods=['GET', 'POST'])
@login_required
def optimize(item_code):
    if request.method == 'POST':
        sheet_width = int(request.form.get('sheet_width', 1200))
        expected_loss = int(request.form.get('expected_loss', 20))
        development_variation = int(request.form.get('development_variation', 0))
        max_items_option = request.form.get('max_items_option', '3')
    else:
        sheet_width = 1200
        expected_loss = 20
        development_variation = 0
        max_items_option = '3'

    max_items_per_sheet = int(max_items_option)
    full_df = get_full_data()
    main_item_series = full_df[full_df['ItemCode'] == item_code]
    if main_item_series.empty:
        return "Item não encontrado!", 404
    main_item = main_item_series.iloc[0].to_dict()

    solutions = find_optimal_combinations(
        main_item=main_item,
        all_items=full_df.to_dict(orient='records'),
        sheet_width=sheet_width,
        expected_loss=expected_loss,
        development_variation=development_variation,
        max_items_per_sheet=max_items_per_sheet
    )

    return render_template(
        'optimization.html',
        item=main_item,
        solutions=solutions,
        sheet_width=sheet_width,
        expected_loss=expected_loss,
        development_variation=development_variation,
        selected_option=max_items_option
    )

if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.watch('**/*.*')
    server.serve(port=5000, host='127.0.0.1', debug=True)
