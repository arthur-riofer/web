document.querySelectorAll('.combo-table tr[data-entries]').forEach(row => {
  row.addEventListener('click', () => {
    const entries = JSON.parse(row.getAttribute('data-entries'));
    const modal = document.getElementById('item-detail');
    const tableBody = document.getElementById('detail-table').querySelector('tbody');
    
    
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

    
    modal.style.display = 'block';
  });
});


const modal = document.getElementById('item-detail');
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


const backButton = document.querySelector('.back-button');
if (backButton) {
  backButton.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/';
  });
}

document.addEventListener('DOMContentLoaded', function() {
    
    
    document.querySelectorAll('.combo-table tr[data-entries]').forEach(row => {
        row.addEventListener('click', () => {
            const entries = JSON.parse(row.getAttribute('data-entries'));
            const modal = document.getElementById('item-detail');
            if (!modal) return; 

            const tableBody = modal.querySelector('#detail-table tbody');
            tableBody.innerHTML = ''; 

            
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