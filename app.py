
from flask import Flask, render_template
from otimcorte.sap import obter_dados_do_sap
from otimcorte.logic import (
    adjust_planned,
    best_fit_grouped,
)
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    df = obter_dados_do_sap()
    df['ToCut'] = df.apply(adjust_planned, axis=1)
    df['EstoqueFinal'] = df['Estoque'] + df['ToCut']

    df['SheetLengthType'] = df['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')
    groups = df.groupby(['Espessura','SheetLengthType'])

    report = []
    total_sheets = 0

    for (esp, sheet_type), group in groups:
        entries = []
        for _, row in group.iterrows():
            qty = min(row['ToCut'], row['DispPkl'])
            for _ in range(int(qty)):
                entries.append({
                    'size': row['Desenvolvimento'],
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
        summary, count = best_fit_grouped(entries)
        total_sheets += count
        report.append({
            'espessura': esp,
            'tipo': sheet_type,
            'summary': summary,
            'sheet_count': count
        })

    # Preparar resumo final por item
    resumo_final = df[['ItemCode','ItemName','Estoque','ToCut','EstoqueFinal','EstoqueMin','EstoqueMax']]
    items = resumo_final.drop_duplicates(subset=['ItemCode']).to_dict(orient='records')

    return render_template(
        'report.html',
        report=report,
        total_sheets=total_sheets,
        items=items
    )

if __name__=='__main__':
    app.run(debug=True)