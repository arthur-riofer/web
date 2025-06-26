
from collections import defaultdict, Counter

class Sheet:
    def __init__(self, sheet_id, max_width=1200):
        self.id = sheet_id
        self.max_width = max_width
        self.remaining = max_width
        self.cuts = []

    def can_fit(self, entry):
        size = entry['size']
        unique_sizes = set(e['size'] for e in self.cuts)
        if self.remaining < size:
            return False
        if size not in unique_sizes and len(unique_sizes) >= 3:
            return False
        return True

    def add_cut(self, entry):
        self.remaining -= entry['size']
        self.cuts.append(entry)

    def combo_key(self):
        cnt = Counter(e['size'] for e in self.cuts)
        return tuple(sorted(cnt.items()))


def best_fit_grouped(entries, sheet_width=1200):
    sheets = []
    sid = 1
    for entry in sorted(entries, key=lambda x: x['size'], reverse=True):
        best = None
        min_waste = None
        for sh in sheets:
            if sh.can_fit(entry):
                waste = sh.remaining - entry['size']
                if min_waste is None or waste < min_waste:
                    best = sh
                    min_waste = waste
        if best:
            best.add_cut(entry)
        else:
            sh = Sheet(sid, max_width=sheet_width)
            sid += 1
            sh.add_cut(entry)
            sheets.append(sh)

    combo_map = defaultdict(lambda: {'count': 0, 'unique_items': {}})
    for sh in sheets:
        key = sh.combo_key()
        combo_map[key]['count'] += 1
        for e in sh.cuts:
            item = e['item']
            combo_map[key]['unique_items'][item['code']] = item

    summary = []
    for key, val in combo_map.items():
        cuts_str = ", ".join(f"{size}mm x {qty}" for size, qty in key)
        items = list(val['unique_items'].values())
        summary.append({
            'cuts': cuts_str,
            'count': val['count'],
            'entries': items
        })

    total = len(sheets)
    return summary, total


def adjust_planned(row):
    est, plan, emin, emax = row['Estoque'], row['Planejado'], row['EstoqueMin'], row['EstoqueMax']
    desired = max(emin - est, 0)
    capped = min(plan, emax - est)
    return max(desired, capped)