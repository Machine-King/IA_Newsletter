// scripts.js - Funcionalidades interactivas adicionales para el dashboard

class DashboardManager {
    constructor() {
        this.isLoading = false;
        this.init();
    }

    init() {
        // Inicializar tooltips y eventos
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // Agregar efecto de clic a los botones
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.addClickEffect(e.target);
            });
        });

        // Mejorar accesibilidad de la tabla
        document.querySelectorAll('.articles-table tr').forEach(row => {
            row.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const link = row.querySelector('.article-link');
                    if (link) link.click();
                }
            });
            row.setAttribute('tabindex', '0');
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R para actualizar todo
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.updateSource('all');
            }
        });
    }

    addClickEffect(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }

    showNotification(message, type = 'info') {
        const statusEl = document.getElementById('refresh-status');
        if (!statusEl) return;

        statusEl.innerHTML = `<div class="message message-${type}">${message}</div>`;
        statusEl.className = 'refresh-status show';
        
        setTimeout(() => {
            statusEl.className = 'refresh-status';
        }, 5000);
    }

    // Función para filtrar artículos
    filterArticles(searchTerm) {
        const rows = document.querySelectorAll('.articles-table tbody tr');
        let visibleCount = 0;

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(searchTerm.toLowerCase());
            row.style.display = isVisible ? '' : 'none';
            if (isVisible) visibleCount++;
        });

        // Mostrar mensaje si no hay resultados
        this.showFilterResults(visibleCount, rows.length);
    }

    showFilterResults(visible, total) {
        let resultMsg = document.getElementById('filter-results');
        if (!resultMsg) {
            resultMsg = document.createElement('div');
            resultMsg.id = 'filter-results';
            resultMsg.className = 'message message-info';
            document.querySelector('.articles-header').appendChild(resultMsg);
        }

        if (visible === total) {
            resultMsg.style.display = 'none';
        } else {
            resultMsg.style.display = 'block';
            resultMsg.textContent = `Mostrando ${visible} de ${total} artículos`;
        }
    }
}

// Inicializar el dashboard cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});

// Utilidades adicionales
const Utils = {
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    truncateText(text, maxLength = 100) {
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            if (window.dashboard) {
                window.dashboard.showNotification('📋 Copiado al portapapeles', 'success');
            }
        });
    }
};