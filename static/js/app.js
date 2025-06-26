document.querySelectorAll('.combo-table tr[data-entries]').forEach(row => {
  row.addEventListener('click', () => {
    const entries = JSON.parse(row.getAttribute('data-entries'));
    const table = document.getElementById('detail-table');
    table.querySelectorAll('tr.item-row').forEach(r=>r.remove());
    entries.forEach(it => {
      const tr = document.createElement('tr'); tr.classList.add('item-row');
      tr.innerHTML = `
        <td>${it.code}</td>
        <td>${it.name}</td>
        <td>${it.Estoque}</td>
        <td>${it.ToCut}</td>
        <td>${it.EstoqueFinal}</td>
        <td>${it.EstoqueMin}</td>
        <td>${it.EstoqueMax}</td>
      `;
      table.appendChild(tr);
    });
    document.getElementById('item-detail').style.display = 'block';
  });
});

// fecha modal
document.getElementById('close-modal').onclick = () => {
  document.getElementById('item-detail').style.display = 'none';
};