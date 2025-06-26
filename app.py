from flask import Flask, render_template, request, redirect, url_for
from otimcorte.sap import obter_dados_do_sap
from otimcorte.logic import (
    adjust_planned,
    best_fit_grouped,
)
import pandas as pd
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Exibe a tabela de seleção de itens."""
    df = obter_dados_do_sap()
    df['Considerar no cálculo'] = True
    df['Variação de espessura'] = 0
    return render_template('index.html', data=df.to_dict(orient='records'))

@app.route('/input-plates', methods=['POST'])
def input_plates():
    """Processa a seleção inicial e exibe a tela de entrada de dados das chapas."""
    data = request.form.get('data')
    df = pd.read_json(data)

    df_to_process = df[df['Considerar no cálculo']].copy()
    if df_to_process.empty:
        return redirect(url_for('index'))

    df_to_process['SheetLengthType'] = df_to_process['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')
    
    # Agrupa para identificar os tipos de chapa necessários
    plate_types = df_to_process.groupby(['Espessura', 'SheetLengthType']).size().reset_index().to_dict(orient='records')

    return render_template('input_plates.html', plate_types=plate_types, original_data=data)


@app.route('/calculate', methods=['POST'])
def calculate():
    """Recebe os dados das chapas e executa a otimização de corte."""
    original_data = request.form.get('original_data')
    df = pd.read_json(original_data)

    df_to_process = df[df['Considerar no cálculo']].copy()

    df_to_process['ToCut'] = df_to_process.apply(adjust_planned, axis=1)
    df_to_process['EstoqueFinal'] = df_to_process['Estoque'] + df_to_process['ToCut']
    df_to_process['SheetLengthType'] = df_to_process['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')

    # Extrai as larguras informadas pelo usuário
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
                            'code': row['ItemCode'],
                            'name': row['ItemName'],
                            'Estoque': row['Estoque'],
                            'ToCut': row['ToCut'],
                            'EstoqueFinal': row['EstoqueFinal'],
                            'EstoqueMin': row['EstoqueMin'],
                            'EstoqueMax': row['EstoqueMax']
                        }
                    })
        if not entries:
            continue

        # Usa a largura da chapa informada pelo usuário, com um padrão de 1200 se não for encontrada
        sheet_width = plate_widths.get((esp, sheet_type), 1200)
        summary, count = best_fit_grouped(entries, sheet_width=sheet_width)
        total_sheets += count
        report.append({
            'espessura': esp,
            'tipo': sheet_type,
            'summary': summary,
            'sheet_count': count
        })

    resumo_final = df_to_process[['ItemCode', 'ItemName', 'Estoque', 'ToCut', 'EstoqueFinal', 'EstoqueMin', 'EstoqueMax']]
    items = resumo_final.drop_duplicates(subset=['ItemCode']).to_dict(orient='records')

    return render_template(
        'report.html',
        report=report,
        total_sheets=total_sheets,
        items=items
    )

if __name__ == '__main__':
    app.run(debug=True)