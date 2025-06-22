// FleetFuel360 Dashboard JavaScript
// Chart.js configuration and API interactions

class FleetFuelDashboard {
    constructor() {
        console.log('🏗️ Constructing FleetFuelDashboard...');
        this.charts = {};
        this.currentData = {};
        this.loadingModal = null;
        this.refreshInterval = null;
        
        // Initialize Bootstrap modal
        try {
            const modalElement = document.getElementById('loadingModal');
            if (modalElement) {
                this.loadingModal = new bootstrap.Modal(modalElement);
                console.log('✅ Bootstrap modal initialized successfully');
            } else {
                console.error('❌ Loading modal element not found');
            }
        } catch (error) {
            console.error('❌ Error initializing Bootstrap modal:', error);
        }
    }

    // Initialize the dashboard
    async initializeDashboard() {
        console.log('🚀 Initializing dashboard...');
        this.showLoading('Loading dashboard data...');
        
        // Set a timeout to force hide loading modal after 10 seconds
        const forceHideTimeout = setTimeout(() => {
            console.log('⏰ Force hiding loading modal after timeout');
            this.hideLoading();
        }, 10000);
        
        try {
            console.log('📊 Loading vehicles...');
            // Load vehicles for dropdown
            await this.loadVehicles();
            
            console.log('📈 Loading dashboard data...');
            // Load initial data
            await this.loadDashboardData();
            
            console.log('🤖 Checking model status...');
            // Check model status
            await this.checkModelStatus();
            
            console.log('⏰ Setting up auto-refresh...');
            // Set up auto-refresh
            this.setupAutoRefresh();
            
            console.log('✅ Dashboard initialization complete!');
            
        } catch (error) {
            console.error('❌ Dashboard initialization error:', error);
            this.showError('Failed to initialize dashboard');
        } finally {
            console.log('🔄 Hiding loading modal...');
            clearTimeout(forceHideTimeout);
            this.hideLoading();
            
            // Add class to body to indicate dashboard is ready
            document.body.classList.add('dashboard-ready');
        }
    }

    // Show loading modal
    showLoading(message = 'Loading...') {
        console.log(`📋 Showing loading modal: ${message}`);
        const loadingText = document.getElementById('loadingText');
        if (loadingText) {
            loadingText.textContent = message;
        }
        
        if (this.loadingModal) {
            try {
                this.loadingModal.show();
            } catch (error) {
                console.error('❌ Error showing modal:', error);
            }
        }
    }

    // Hide loading modal
    hideLoading() {
        console.log('🔄 Attempting to hide loading modal...');
        try {
            if (this.loadingModal) {
                this.loadingModal.hide();
            }
            console.log('✅ Loading modal hidden successfully');
        } catch (error) {
            console.error('❌ Error hiding loading modal:', error);
        }
        
        // Force hide using DOM manipulation as backup
        setTimeout(() => {
            const modal = document.getElementById('loadingModal');
            const backdrop = document.querySelector('.modal-backdrop');
            
            if (modal) {
                modal.style.display = 'none';
                modal.classList.remove('show');
                modal.setAttribute('aria-hidden', 'true');
            }
            
            if (backdrop) {
                backdrop.remove();
            }
            
            // Remove modal-open class from body
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }, 500);
    }

    // Load vehicles for dropdown
    async loadVehicles() {
        try {
            const response = await fetch(`${API_BASE_URL}/vehicles`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const select = document.getElementById('vehicleSelect');
                
                // Clear existing options except "All Vehicles"
                select.innerHTML = '<option value="all">All Vehicles</option>';
                
                // Add vehicle options
                data.vehicles.forEach(vehicle => {
                    const option = document.createElement('option');
                    option.value = vehicle.vehicle_id;
                    option.textContent = `${vehicle.vehicle_id} (${vehicle.make} ${vehicle.model})`;
                    if (vehicle.vehicle_id === SELECTED_VEHICLE) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading vehicles:', error);
        }
    }

    // Load main dashboard data
    async loadDashboardData() {
        const vehicleId = document.getElementById('vehicleSelect').value;
        const daysBack = document.getElementById('daysSelect').value;
        
        const params = new URLSearchParams({
            days_back: daysBack
        });
        
        if (vehicleId !== 'all') {
            params.append('vehicle_id', vehicleId);
        }

        try {
            // Load multiple data sources in parallel
            const [statsResponse, fuelLogsResponse, anomaliesResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/statistics?${params}`),
                fetch(`${API_BASE_URL}/fuel-logs?${params}`),
                fetch(`${API_BASE_URL}/anomalies?${params}`)
            ]);

            const statsData = await statsResponse.json();
            const fuelLogsData = await fuelLogsResponse.json();
            const anomaliesData = await anomaliesResponse.json();

            // Update dashboard components
            this.updateStatisticsCards(statsData);
            this.updateCharts(vehicleId, daysBack);
            this.updateAnomaliesTable(anomaliesData);
            this.updateRecentLogsTable(fuelLogsData);
            
            // Load analysis and recommendations
            await this.loadAnalysis(vehicleId, daysBack);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    // Update statistics cards
    updateStatisticsCards(data) {
        const container = document.getElementById('statsCards');
        
        if (data.status !== 'success') {
            container.innerHTML = '<div class="col-12"><div class="alert alert-warning">No statistics available</div></div>';
            return;
        }

        const stats = data.fleet_summary;
        
        const cardsHtml = `
            <div class="col-md-3">
                <div class="card stats-card border-start-primary">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col">
                                <div class="stats-number text-primary">${stats.total_vehicles}</div>
                                <div class="stats-label">Total Vehicles</div>
                            </div>
                            <div class="col-auto">
                                <i class="bi bi-truck fs-2 text-primary"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card stats-card border-start-success">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col">
                                <div class="stats-number text-success">${stats.total_km_driven.toLocaleString()}</div>
                                <div class="stats-label">Total KM Driven</div>
                            </div>
                            <div class="col-auto">
                                <i class="bi bi-speedometer2 fs-2 text-success"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card stats-card border-start-info">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col">
                                <div class="stats-number text-info">${stats.avg_efficiency.toFixed(2)}</div>
                                <div class="stats-label">Avg Efficiency (km/L)</div>
                            </div>
                            <div class="col-auto">
                                <i class="bi bi-fuel-pump fs-2 text-info"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card stats-card border-start-warning">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col">
                                <div class="stats-number text-warning">${stats.total_anomalies}</div>
                                <div class="stats-label">Anomalies Detected</div>
                                <div class="stats-change ${stats.anomaly_rate > 0.1 ? 'negative' : 'positive'}">
                                    ${(stats.anomaly_rate * 100).toFixed(1)}% anomaly rate
                                </div>
                            </div>
                            <div class="col-auto">
                                <i class="bi bi-exclamation-triangle fs-2 text-warning"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = cardsHtml;
    }

    // Update charts
    async updateCharts(vehicleId, daysBack) {
        try {
            // Load chart data
            const params = new URLSearchParams({
                days_back: daysBack,
                type: 'efficiency_timeline'
            });
            
            if (vehicleId !== 'all') {
                params.append('vehicle_id', vehicleId);
            }
            
            const [timelineResponse, comparisonResponse] = await Promise.all([
                fetch(`${API_BASE_URL}/chart-data?${params}`),
                fetch(`${API_BASE_URL}/chart-data?${params.toString().replace('efficiency_timeline', 'vehicle_comparison')}`)
            ]);

            const timelineData = await timelineResponse.json();
            const comparisonData = await comparisonResponse.json();

            // Update efficiency timeline chart
            this.updateEfficiencyChart(timelineData);
            
            // Update vehicle comparison chart
            this.updateComparisonChart(comparisonData);

        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    // Update efficiency timeline chart
    updateEfficiencyChart(data) {
        const ctx = document.getElementById('efficiencyChart').getContext('2d');
        
        if (this.charts.efficiency) {
            this.charts.efficiency.destroy();
        }

        if (data.status !== 'success') {
            return;
        }

        const chartData = data.data;
        
        // Prepare anomaly points
        const anomalyPoints = chartData.anomalies || [];
        
        this.charts.efficiency = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    ...chartData.datasets,
                    {
                        label: 'Anomalies',
                        data: anomalyPoints.map(point => ({
                            x: point.x,
                            y: point.y
                        })),
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        borderColor: 'rgb(255, 99, 132)',
                        pointRadius: 6,
                        pointHoverRadius: 8,
                        showLine: false,
                        type: 'scatter'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Fuel Efficiency Over Time'
                    },
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Efficiency (km/L)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 6
                    }
                }
            }
        });
    }

    // Update vehicle comparison chart
    updateComparisonChart(data) {
        const ctx = document.getElementById('comparisonChart').getContext('2d');
        
        if (this.charts.comparison) {
            this.charts.comparison.destroy();
        }

        if (data.status !== 'success') {
            return;
        }

        this.charts.comparison = new Chart(ctx, {
            type: 'bar',
            data: data.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Vehicle Efficiency Comparison'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Efficiency (km/L)'
                        }
                    }
                }
            }
        });
    }

    // Update anomalies table
    updateAnomaliesTable(data) {
        const container = document.getElementById('anomaliesTable');
        const countBadge = document.getElementById('anomalyCount');
        
        if (data.status !== 'success' || data.anomalies.length === 0) {
            container.innerHTML = '<p class="text-muted">No anomalies detected</p>';
            countBadge.textContent = '0';
            return;
        }

        countBadge.textContent = data.count;

        const tableHtml = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Vehicle</th>
                        <th>Date</th>
                        <th>Efficiency</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.anomalies.slice(0, 5).map(anomaly => `
                        <tr>
                            <td><strong>${anomaly.vehicle_id}</strong></td>
                            <td>${new Date(anomaly.timestamp).toLocaleDateString()}</td>
                            <td class="efficiency-${this.getEfficiencyClass(anomaly.fuel_efficiency)}">
                                ${anomaly.fuel_efficiency?.toFixed(2) || 'N/A'} km/L
                            </td>
                            <td>
                                <span class="badge ${this.getAnomalyScoreBadgeClass(anomaly.anomaly_score)}">
                                    ${anomaly.anomaly_score?.toFixed(3) || 'N/A'}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHtml;
    }

    // Update recent logs table
    updateRecentLogsTable(data) {
        const container = document.getElementById('recentLogsTable');
        
        if (data.status !== 'success' || data.fuel_logs.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent fuel logs</p>';
            return;
        }

        const tableHtml = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Vehicle</th>
                        <th>Date</th>
                        <th>KM Driven</th>
                        <th>Fuel Used</th>
                        <th>Efficiency</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.fuel_logs.slice(0, 5).map(log => `
                        <tr>
                            <td><strong>${log.vehicle_id}</strong></td>
                            <td>${new Date(log.timestamp).toLocaleDateString()}</td>
                            <td>${log.km_driven?.toFixed(1) || 'N/A'} km</td>
                            <td>${log.fuel_used?.toFixed(1) || 'N/A'} L</td>
                            <td class="efficiency-${this.getEfficiencyClass(log.fuel_efficiency)}">
                                ${log.fuel_efficiency?.toFixed(2) || 'N/A'} km/L
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHtml;
    }

    // Load analysis and recommendations
    async loadAnalysis(vehicleId, daysBack) {
        try {
            const params = new URLSearchParams({
                days_back: daysBack
            });
            
            if (vehicleId !== 'all') {
                params.append('vehicle_id', vehicleId);
            }

            const response = await fetch(`${API_BASE_URL}/analysis?${params}`);
            const data = await response.json();

            this.updateRecommendations(data.recommendations || []);

        } catch (error) {
            console.error('Error loading analysis:', error);
        }
    }

    // Update recommendations
    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendationsContainer');
        
        if (recommendations.length === 0) {
            container.innerHTML = '<p class="text-muted">No specific recommendations at this time. Fleet performance looks good!</p>';
            return;
        }

        const recommendationsHtml = recommendations.map(rec => `
            <div class="recommendation ${rec.priority}-priority">
                <div class="recommendation-title">
                    <i class="bi bi-${this.getRecommendationIcon(rec.type)} me-2"></i>
                    ${rec.type.replace('_', ' ').toUpperCase()}
                    ${rec.vehicle_id ? ` - ${rec.vehicle_id}` : ''}
                </div>
                <div class="recommendation-message">${rec.message}</div>
                <div class="recommendation-action">
                    <i class="bi bi-arrow-right me-1"></i>
                    Action: ${rec.action}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = recommendationsHtml;
    }

    // Check model status
    async checkModelStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/model-status`);
            const data = await response.json();
            
            const statusBadge = document.getElementById('modelStatus');
            
            if (data.status === 'success' && data.model_status.status === 'trained') {
                statusBadge.textContent = 'Model Ready';
                statusBadge.className = 'badge bg-success';
            } else {
                statusBadge.textContent = 'Model Not Ready';
                statusBadge.className = 'badge bg-warning';
            }
            
        } catch (error) {
            console.error('Error checking model status:', error);
            const statusBadge = document.getElementById('modelStatus');
            statusBadge.textContent = 'Model Error';
            statusBadge.className = 'badge bg-danger';
        }
    }

    // Detect anomalies
    async detectAnomalies() {
        this.showLoading('Detecting anomalies...');
        
        try {
            const vehicleId = document.getElementById('vehicleSelect').value;
            const requestData = {
                update_db: true,
                retrain: false
            };
            
            if (vehicleId !== 'all') {
                requestData.vehicle_id = vehicleId;
            }

            const response = await fetch(`${API_BASE_URL}/detect-anomalies`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.showSuccess(`Anomaly detection completed. Found ${data.anomalies_detected} anomalies out of ${data.total_records} records.`);
                
                // Refresh the dashboard
                await this.loadDashboardData();
            } else {
                this.showError(`Anomaly detection failed: ${data.message}`);
            }
            
        } catch (error) {
            console.error('Error detecting anomalies:', error);
            this.showError('Failed to detect anomalies');
        } finally {
            this.hideLoading();
        }
    }

    // Utility functions
    getEfficiencyClass(efficiency) {
        if (!efficiency) return 'poor';
        if (efficiency >= 10) return 'good';
        if (efficiency >= 7) return 'average';
        return 'poor';
    }

    getAnomalyScoreBadgeClass(score) {
        if (!score) return 'bg-secondary';
        if (score < -0.5) return 'bg-danger';
        if (score < -0.2) return 'bg-warning';
        return 'bg-info';
    }

    getRecommendationIcon(type) {
        const icons = {
            'efficiency_concern': 'fuel-pump',
            'anomaly_concern': 'exclamation-triangle',
            'fleet_efficiency': 'speedometer2',
            'declining_trend': 'arrow-down',
            'error': 'exclamation-circle'
        };
        return icons[type] || 'info-circle';
    }

    showSuccess(message) {
        // You can implement a toast notification here
        alert(message);
    }

    showError(message) {
        // You can implement a toast notification here
        alert('Error: ' + message);
    }

    // Setup auto-refresh
    setupAutoRefresh() {
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    // Cleanup
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Global dashboard instance
let dashboard;

// Global functions called by HTML
function initializeDashboard() {
    dashboard = new FleetFuelDashboard();
    dashboard.initializeDashboard();
}

function updateDashboard() {
    if (dashboard) {
        dashboard.loadDashboardData();
    }
}

function refreshData() {
    if (dashboard) {
        dashboard.loadDashboardData();
    }
}

function detectAnomalies() {
    if (dashboard) {
        dashboard.detectAnomalies();
    }
}
