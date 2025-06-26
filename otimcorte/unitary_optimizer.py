import itertools

def find_optimal_combinations(main_item, all_items, sheet_width, expected_loss, development_variation, max_items_per_sheet):
    """
    Encontra as 10 melhores combinações de corte, considerando variações de desenvolvimento
    e um número máximo de itens por chapa. Impede a repetição de planos de corte.
    """
    solutions = []
    usable_width = sheet_width - expected_loss

    # Filtra parceiros potenciais
    potential_partners = [
        item for item in all_items
        if (item['Espessura'] == main_item['Espessura'] and
            item['Comprimento'] == main_item['Comprimento'] and
            item['ItemCode'] != main_item['ItemCode'] and
            item['EstoqueMax'] > item['DispPkl'] and
            item['Desenvolvimento'] > 0)
    ]
    potential_partners.sort(key=lambda x: (x['EstoqueMax'] - x['DispPkl']), reverse=True)

    items_to_process = [main_item] + potential_partners

    # --- Gera combinações de itens respeitando o limite selecionado pelo usuário ---
    for i in range(1, max_items_per_sheet + 1):
        if len(items_to_process) < i:
            continue

        for combo_items in itertools.combinations(items_to_process, i):
            if main_item['ItemCode'] not in [c['ItemCode'] for c in combo_items]:
                continue
            
            size_variations_per_item = []
            for item in combo_items:
                original_size = item['Desenvolvimento']
                variations = [original_size]
                if development_variation > 0:
                    variations.extend([original_size + development_variation, original_size - development_variation])
                size_variations_per_item.append(list(set(v for v in variations if v > 0)))

            for size_set in itertools.product(*size_variations_per_item):
                best_qtys = [0] * len(combo_items)
                min_waste = float('inf')

                max_qtys = [int(usable_width // size) if size > 0 else 0 for size in size_set]
                qty_ranges = [range(max_qty + 1) for max_qty in max_qtys]

                for qtys in itertools.product(*qty_ranges):
                    main_item_index = [idx for idx, item in enumerate(combo_items) if item['ItemCode'] == main_item['ItemCode']][0]
                    if qtys[main_item_index] == 0:
                        continue

                    total_width = sum(size * qty for size, qty in zip(size_set, qtys))
                    
                    if total_width <= usable_width:
                        waste = usable_width - total_width
                        if waste < min_waste:
                            min_waste = waste
                            best_qtys = qtys
                
                if sum(best_qtys) > 0:
                    combination_details = []
                    for idx, item in enumerate(combo_items):
                        if best_qtys[idx] > 0:
                            combination_details.append({
                                'name': item['ItemName'],
                                'qty': best_qtys[idx],
                                'original_size': item['Desenvolvimento'],
                                'used_size': size_set[idx]
                            })
                    
                    priority = sum(p['EstoqueMax'] - p['DispPkl'] for p in combo_items if p['ItemCode'] != main_item['ItemCode'])
                    solutions.append({
                        'details': combination_details,
                        'total_width': usable_width - min_waste,
                        'waste': min_waste,
                        'priority': 999999 if len(combo_items) == 1 else priority
                    })

    # --- LÓGICA ATUALIZADA: Impede repetição de planos de corte ---
    # Agrupa soluções por plano de corte (mesmos itens e quantidades), mantendo apenas a de menor 'waste'.
    best_solutions_for_plan = {}
    for sol in solutions:
        # A chave agora ignora a variação de medida, focando no plano de corte.
        plan_key = tuple(sorted([(d['name'], d['qty']) for d in sol['details']]))
        
        # Se o plano é novo ou se a solução atual tem um desperdício menor, armazena/substitui.
        if plan_key not in best_solutions_for_plan or sol['waste'] < best_solutions_for_plan[plan_key]['waste']:
            best_solutions_for_plan[plan_key] = sol

    # Ordena as soluções únicas pelo menor desperdício e depois pela maior prioridade.
    sorted_solutions = sorted(best_solutions_for_plan.values(), key=lambda x: (x['waste'], -x['priority']))

    return sorted_solutions[:10]