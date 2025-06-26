document.querySelectorAll('.combo-table tr[data-entries]').forEach(row => {
  row.addEventListener('click', () => {
    const entries = JSON.parse(row.getAttribute('data-entries'));
    const modal = document.getElementById('item-detail');
    const tableBody = document.getElementById('detail-table').querySelector('tbody');
    
    // Limpa a tabela de detalhes antes de adicionar novas linhas
    tableBody.innerHTML = ''; 

    entries.forEach(it => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${it.code}</td>
        <td>${it.name}</td>
        <td>${it.Estoque}</td>
        <td>${it.ToCut}</td>
        <td>${it.EstoqueFinal}</td>
        <td>${it.EstoqueMin}</td>
        <td>${it.EstoqueMax}</td>
      `;
      tableBody.appendChild(tr);
    });

    // Exibe o modal
    modal.style.display = 'block';
  });
});

// Lógica para fechar o modal
const modal = document.getElementById('item-detail');
const closeButton = document.getElementById('close-modal');

// Fecha ao clicar no botão (X)
if(closeButton) {
    closeButton.onclick = () => {
        modal.style.display = 'none';
    };
}


// Fecha ao clicar fora do conteúdo do modal
window.onclick = (event) => {
  if (event.target == modal) {
    modal.style.display = 'none';
  }
};

// Mantém a lógica do botão de voltar da página
const backButton = document.querySelector('.back-button');
if (backButton) {
  backButton.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/';
  });
}

document.addEventListener('DOMContentLoaded', function() {
    
    // Lógica para o modal de detalhes do item na página de relatório
    document.querySelectorAll('.combo-table tr[data-entries]').forEach(row => {
        row.addEventListener('click', () => {
            const entries = JSON.parse(row.getAttribute('data-entries'));
            const modal = document.getElementById('item-detail');
            if (!modal) return; // Só executa se o modal existir na página

            const tableBody = modal.querySelector('#detail-table tbody');
            tableBody.innerHTML = ''; 

            // Agrupa itens para evitar duplicatas no modal
            const uniqueItems = {};
            entries.forEach(item => {
                uniqueItems[item.code] = item;
            });

            Object.values(uniqueItems).forEach(it => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${it.code}</td>
                    <td>${it.name}</td>
                    <td>${it.Estoque}</td>
                    <td>${it.ToCut}</td>
                    <td>${it.EstoqueFinal}</td>
                    <td>${it.EstoqueMin}</td>
                    <td>${it.EstoqueMax}</td>
                `;
                tableBody.appendChild(tr);
            });
            
            modal.style.display = 'block';
        });
    });

    // Lógica para fechar o modal
    const modal = document.getElementById('item-detail');
    if (modal) {
        const closeButton = document.getElementById('close-modal');
        if(closeButton) {
            closeButton.onclick = () => {
                modal.style.display = 'none';
            };
        }
        window.onclick = (event) => {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    }
});