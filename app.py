from flask import Flask, render_template, request
from otimcorte.sap import obter_dados_do_sap
from otimcorte.logic import (
    adjust_planned,
    best_fit_grouped,
)
import pandas as pd
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.get('data')
        df = pd.read_json(data)

        # Filtra apenas os itens marcados para o cálculo
        df_to_process = df[df['Considerar no cálculo']].copy()

        df_to_process['ToCut'] = df_to_process.apply(adjust_planned, axis=1)
        df_to_process['EstoqueFinal'] = df_to_process['Estoque'] + df_to_process['ToCut']
        df_to_process['SheetLengthType'] = df_to_process['Comprimento'].apply(lambda x: '6m' if x > 3 else '3m')

        groups = df_to_process.groupby(['Espessura', 'SheetLengthType'])
        report = []
        total_sheets = 0

        for (esp, sheet_type), group in groups:
            entries = []
            for _, row in group.iterrows():
                qty = min(row['ToCut'], row['DispPkl'])
                desenvolvimento = row['Desenvolvimento']
                variacao = row['Variação de espessura']

                # Gera as variações de desenvolvimento se a variação for maior que 0
                if variacao > 0:
                    desenvolvimentos = range(int(desenvolvimento - variacao), int(desenvolvimento + variacao + 1))
                else:
                    desenvolvimentos = [desenvolvimento]

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

            # **CORREÇÃO APLICADA AQUI**
            # A largura da chapa para o cálculo de otimização é sempre 1200.
            sheet_width = 1200
            summary, count = best_fit_grouped(entries, sheet_width=sheet_width)
            total_sheets += count
            report.append({
                'espessura': esp,
                'tipo': sheet_type, # O tipo '3m' ou '6m' é usado apenas para agrupar e no relatório
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

    # Se for GET, exibe a tabela de seleção
    df = obter_dados_do_sap()
    df['Considerar no cálculo'] = True
    df['Variação de espessura'] = 0
    return render_template('index.html', data=df.to_dict(orient='records'))


if __name__ == '__main__':
    app.run(debug=True)