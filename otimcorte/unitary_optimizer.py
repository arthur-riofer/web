import itertools

def find_optimal_combinations(main_item, all_items, sheet_width, expected_loss):
    """
    Encontra as 10 melhores combinações de corte para um item principal,
    com base em regras de prioridade e necessidade de estoque.
    """
    solutions = []
    usable_width = sheet_width - expected_loss
    main_item_size = main_item['Desenvolvimento']

    # --- 1. A melhor solução: Apenas o item principal repetido ---
    if main_item_size > 0:
        qty = int(usable_width // main_item_size)
        if qty > 0:
            total_width = qty * main_item_size
            solutions.append({
                'combination': {main_item['ItemName']: qty},
                'total_width': total_width,
                'waste': usable_width - total_width,
                'priority': 999999  # Prioridade máxima para a solução solo
            })

    # --- 2. Soluções combinadas com 2 ou 3 itens diferentes ---
    
    # Filtra parceiros potenciais do mesmo grupo e com necessidade de estoque
    potential_partners = [
        item for item in all_items
        if (item['Espessura'] == main_item['Espessura'] and
            item['Comprimento'] == main_item['Comprimento'] and
            item['ItemCode'] != main_item['ItemCode'] and
            item['EstoqueMax'] > item['DispPkl'] and
            item['Desenvolvimento'] > 0)
    ]
    
    # Ordena os parceiros pelo fator determinante: (EstoqueMax - DispPkl)
    potential_partners.sort(key=lambda x: (x['EstoqueMax'] - x['DispPkl']), reverse=True)

    # Gera combinações de 1 ou 2 parceiros para juntar com o item principal
    for i in range(1, 3):
        if len(potential_partners) < i:
            continue
        
        for combo in itertools.combinations(potential_partners, i):
            items_to_combine = [main_item] + list(combo)
            
            # Tenta encontrar a melhor combinação de quantidades para os itens selecionados
            # Esta é uma abordagem simplificada de "knapsack problem"
            best_combo_for_this_set = None
            min_waste = float('inf')

            # Itera sobre quantidades possíveis para cada item na combinação
            # (limitado a um número razoável para evitar processamento infinito)
            item_sizes = [it['Desenvolvimento'] for it in items_to_combine]
            max_qtys = [int(usable_width // size) if size > 0 else 0 for size in item_sizes]
            
            # Gera todas as permutações de quantidades
            qty_ranges = [range(max_qty + 1) for max_qty in max_qtys]
            for qtys in itertools.product(*qty_ranges):
                # O item principal deve sempre estar presente
                if qtys[0] == 0:
                    continue
                
                total_width = sum(size * qty for size, qty in zip(item_sizes, qtys))
                
                if total_width <= usable_width:
                    waste = usable_width - total_width
                    if waste < min_waste:
                        min_waste = waste
                        current_priority = sum(p['EstoqueMax'] - p['DispPkl'] for p in combo)
                        best_combo_for_this_set = {
                            'combination': {item['ItemName']: qty for item, qty in zip(items_to_combine, qtys) if qty > 0},
                            'total_width': total_width,
                            'waste': waste,
                            'priority': current_priority
                        }
            
            if best_combo_for_this_set:
                solutions.append(best_combo_for_this_set)

    # --- Ordena e filtra as 10 melhores soluções ---
    # Remove duplicados baseados na combinação e na sobra
    unique_solutions = {}
    for sol in solutions:
        # Cria uma chave única para cada combinação de itens e quantidades
        combo_key = tuple(sorted(sol['combination'].items()))
        if combo_key not in unique_solutions or sol['waste'] < unique_solutions[combo_key]['waste']:
             unique_solutions[combo_key] = sol

    # Ordena pela menor sobra (waste) e depois pela maior prioridade
    sorted_solutions = sorted(unique_solutions.values(), key=lambda x: (x['waste'], -x['priority']))
    
    # Formata a string de combinação para exibição
    for sol in sorted_solutions:
        sol['combination_str'] = ", ".join([f"{name} ({qty}x)" for name, qty in sol['combination'].items()])

    return sorted_solutions[:10]