// scripts.js - Funcionalidades interactivas adicionales para el dashboard

class DashboardManager {
    constructor() {
        this.isLoading = false;
        this.init();
    }

    init() {
        // Inicializar tooltips y eventos
        this.setupEventListeners();
        this.setupAutoRefresh();
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

    setupAutoRefresh() {
        // Auto-refresh cada 5 minutos
        setInterval(() => {
            if (!this.isLoading) {
                this.showNotification('🔄 Actualizando datos automáticamente...', 'info');
                this.refreshStats();
            }
        }, 5 * 60 * 1000);
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R para actualizar todo
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.updateSource('all');
            }
            
            // Ctrl/Cmd + 1-4 para actualizar fuentes específicas
            if ((e.ctrlKey || e.metaKey) && ['1', '2', '3', '4'].includes(e.key)) {
                e.preventDefault();
                const sources = ['news', 'arxiv', 'youtube', 'all'];
                this.updateSource(sources[parseInt(e.key) - 1]);
            }
        });
    }

    addClickEffect(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }

    async updateSource(source) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState(true);
        
        try {
            const response = await fetch(`/update/${source}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(`✅ ${result.message}`, 'success');
                
                // Actualizar estadísticas inmediatamente
                await this.refreshStats();
                
                // Recargar la página después de un breve delay
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showNotification(`❌ Error: ${result.detail}`, 'error');
            }
        } catch (error) {
            this.showNotification(`❌ Error de conexión: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
            this.showLoadingState(false);
        }
    }

    async refreshStats() {
        try {
            const response = await fetch('/status');
            const stats = await response.json();
            
            if (response.ok) {
                this.displayStats(stats);
            }
        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
        }
    }

    displayStats(stats) {
        const statsSection = document.getElementById('stats-section');
        if (!statsSection) return;

        // Crear HTML para estadísticas
        let statsHTML = `
            <div class="stat-card fade-in">
                <div class="stat-number">${stats.total_articles}</div>
                <div class="stat-label">Total Artículos</div>
            </div>
        `;
        
        // Iconos para cada fuente
        const sourceIcons = {
            'arxiv': '📄',
            'techcrunch': '📰',
            'theverge': '📱',
            'youtube': '🎥'
        };
        
        Object.entries(stats.by_source || {}).forEach(([source, count]) => {
            const icon = sourceIcons[source.toLowerCase()] || '📊';
            statsHTML += `
                <div class="stat-card fade-in">
                    <div class="stat-number">${count}</div>
                    <div class="stat-label">${icon} ${source}</div>
                </div>
            `;
        });
        
        statsSection.innerHTML = statsHTML;
        statsSection.style.display = 'grid';
    }

    showLoadingState(isLoading) {
        const statusEl = document.getElementById('refresh-status');
        if (!statusEl) return;

        if (isLoading) {
            statusEl.innerHTML = `
                <div class="message message-info">
                    <span class="loading">
                        <span class="spinner"></span>
                        Actualizando contenido...
                    </span>
                </div>
            `;
            statusEl.className = 'refresh-status show';
        } else {
            statusEl.className = 'refresh-status';
        }
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

    // Función para exportar datos
    exportData() {
        const articles = [];
        document.querySelectorAll('.articles-table tbody tr').forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 4) {
                articles.push({
                    source: cells[0].textContent.trim(),
                    title: cells[1].textContent.trim(),
                    category: cells[2].textContent.trim(),
                    summary: cells[3].textContent.trim()
                });
            }
        });

        const dataStr = JSON.stringify(articles, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `ai-news-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
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
    
    // Hacer las funciones disponibles globalmente para compatibilidad
    window.updateSource = (source) => window.dashboard.updateSource(source);
    window.loadStats = () => window.dashboard.refreshStats();
    
    // Cargar estadísticas iniciales
    window.dashboard.refreshStats();
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
            dashboard.showNotification('📋 Copiado al portapapeles', 'success');
        });
    }
};