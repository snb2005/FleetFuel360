// FleetFuel360 Dashboard JavaScript
class FleetFuelDashboard {
    constructor() {
        this.apiBase = '';
        this.charts = {};
        this.data = {
            vehicles: [],
            fuelLogs: [],
            stats: null
        };
        this.init();
    }

    init() {
        this.loadData();
        this.setupEventListeners();
        this.setupCharts();
        this.setupTooltips();
    }

    // Show loading spinner
    showLoading() {
        document.getElementById('loadingSpinner').style.display = 'block';
    }

    // Hide loading spinner
    hideLoading() {
        document.getElementById('loadingSpinner').style.display = 'none';
    }

    // API call wrapper
    async apiCall(endpoint, method = 'GET', data = null) {
        this.showLoading();
        try {
            const config = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data) {
                config.body = JSON.stringify(data);
            }

            const response = await fetch(this.apiBase + endpoint, config);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'API request failed');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            this.showAlert('Error: ' + error.message, 'danger');
            throw error;
        } finally {
            this.hideLoading();
        }
    }

    // Load all dashboard data
    async loadData() {
        try {
            const [vehicles, fuelLogs, stats] = await Promise.all([
                this.apiCall('/vehicles'),
                this.apiCall('/fuel-logs'),
                this.apiCall('/stats')
            ]);

            this.data.vehicles = vehicles.vehicles || [];
            this.data.fuelLogs = fuelLogs.fuel_logs || [];
            this.data.stats = stats;

            this.updateDashboard();
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    // Update entire dashboard
    updateDashboard() {
        this.updateStatsCards();
        this.updateVehiclesTable();
        this.updateFuelLogsTable();
        this.updateCharts();
        this.populateVehicleSelects();
    }

    // Update statistics cards
    updateStatsCards() {
        const stats = this.data.stats.overall_stats;
        
        this.animateNumber('totalVehicles', stats.total_vehicles);
        this.animateNumber('totalKilometers', Math.round(stats.total_km));
        this.animateNumber('totalFuel', Math.round(stats.total_fuel));
        this.animateNumber('avgEfficiency', parseFloat(stats.avg_efficiency).toFixed(1));
    }

    // Animate number counting
    animateNumber(elementId, targetValue) {
        const element = document.getElementById(elementId);
        const startValue = 0;
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = startValue + (targetValue - startValue) * progress;
            element.textContent = Math.floor(currentValue);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetValue;
            }
        };

        requestAnimationFrame(animate);
    }

    // Update vehicles table
    updateVehiclesTable() {
        const tbody = document.getElementById('vehiclesTableBody');
        tbody.innerHTML = '';

        this.data.vehicles.forEach(vehicle => {
            const stats = this.data.stats.vehicle_stats.find(s => s.name === vehicle.name);
            const efficiency = stats ? stats.avg_efficiency.toFixed(1) : 'N/A';
            const efficiencyClass = this.getEfficiencyClass(parseFloat(efficiency));

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <i class="fas fa-${this.getVehicleIcon(vehicle.type)} vehicle-icon vehicle-${vehicle.type.toLowerCase()}"></i>
                    ${vehicle.name}
                </td>
                <td><span class="badge badge-${this.getVehicleTypeColor(vehicle.type)}">${vehicle.type}</span></td>
                <td>${vehicle.make} ${vehicle.model}</td>
                <td>${vehicle.license_plate}</td>
                <td>${vehicle.year}</td>
                <td><span class="${efficiencyClass}">${efficiency} km/L</span></td>
                <td>
                    <button class="btn btn-sm btn-primary me-1" onclick="dashboard.editVehicle(${vehicle.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="dashboard.deleteVehicle(${vehicle.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // Update fuel logs table
    updateFuelLogsTable() {
        const tbody = document.getElementById('fuelLogsTableBody');
        tbody.innerHTML = '';

        this.data.fuelLogs.slice(0, 10).forEach(log => {
            const efficiency = log.efficiency ? log.efficiency.toFixed(1) : 'N/A';
            const efficiencyClass = this.getEfficiencyClass(parseFloat(efficiency));
            const cost = log.cost ? `$${parseFloat(log.cost).toFixed(2)}` : 'N/A';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDate(log.log_date)}</td>
                <td>
                    <i class="fas fa-${this.getVehicleIcon(log.vehicle_type)} vehicle-icon vehicle-${log.vehicle_type.toLowerCase()}"></i>
                    ${log.vehicle_name}
                </td>
                <td>${log.km_driven}</td>
                <td>${log.fuel_used}</td>
                <td><span class="${efficiencyClass}">${efficiency} km/L</span></td>
                <td>${cost}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="dashboard.deleteFuelLog(${log.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // Update all charts
    updateCharts() {
        this.updateFuelTrendChart();
        this.updateFleetDistributionChart();
        this.updateEfficiencyChart();
        this.updateAnomalyDisplay();
    }

    // Update fuel trend chart
    updateFuelTrendChart() {
        const ctx = document.getElementById('fuelTrendChart').getContext('2d');
        
        // Sort logs by date
        const sortedLogs = this.data.fuelLogs.sort((a, b) => new Date(a.log_date) - new Date(b.log_date));
        
        // Group by month
        const monthlyData = {};
        sortedLogs.forEach(log => {
            const month = new Date(log.log_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
            if (!monthlyData[month]) {
                monthlyData[month] = { fuel: 0, km: 0 };
            }
            monthlyData[month].fuel += log.fuel_used;
            monthlyData[month].km += log.km_driven;
        });

        const labels = Object.keys(monthlyData);
        const fuelData = Object.values(monthlyData).map(d => d.fuel);
        const kmData = Object.values(monthlyData).map(d => d.km);

        if (this.charts.fuelTrend) {
            this.charts.fuelTrend.destroy();
        }

        this.charts.fuelTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Fuel Used (L)',
                    data: fuelData,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Distance (km)',
                    data: kmData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Fuel (L)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Distance (km)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Monthly Fuel Consumption and Distance Trends'
                    }
                }
            }
        });
    }

    // Update fleet distribution chart
    updateFleetDistributionChart() {
        const ctx = document.getElementById('fleetDistributionChart').getContext('2d');
        
        const typeCount = {};
        this.data.vehicles.forEach(vehicle => {
            typeCount[vehicle.type] = (typeCount[vehicle.type] || 0) + 1;
        });

        const colors = {
            'Car': '#007bff',
            'Van': '#28a745',
            'Truck': '#ffc107',
            'Bus': '#17a2b8'
        };

        if (this.charts.fleetDistribution) {
            this.charts.fleetDistribution.destroy();
        }

        this.charts.fleetDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(typeCount),
                datasets: [{
                    data: Object.values(typeCount),
                    backgroundColor: Object.keys(typeCount).map(type => colors[type] || '#6c757d'),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    title: {
                        display: true,
                        text: 'Vehicle Type Distribution'
                    }
                }
            }
        });
    }

    // Update efficiency chart
    updateEfficiencyChart() {
        const ctx = document.getElementById('efficiencyChart').getContext('2d');
        
        const vehicleStats = this.data.stats.vehicle_stats;
        const labels = vehicleStats.map(v => v.name);
        const efficiencyData = vehicleStats.map(v => v.avg_efficiency);

        if (this.charts.efficiency) {
            this.charts.efficiency.destroy();
        }

        this.charts.efficiency = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Efficiency (km/L)',
                    data: efficiencyData,
                    backgroundColor: efficiencyData.map(eff => this.getEfficiencyColor(eff)),
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Efficiency (km/L)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Vehicle Efficiency Comparison'
                    }
                }
            }
        });
    }

    // Update anomaly display
    async updateAnomalyDisplay() {
        try {
            const anomalies = await this.apiCall('/detect-anomalies');
            const container = document.getElementById('anomalyResults');
            
            if (anomalies.anomalies.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        No anomalies detected in recent fuel consumption patterns.
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning mb-3">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${anomalies.anomalies.length} anomalies detected
                    </div>
                    ${anomalies.anomalies.map(anomaly => `
                        <div class="card anomaly-card">
                            <div class="card-body">
                                <h6 class="card-title text-danger">
                                    <i class="fas fa-exclamation-triangle me-1"></i>
                                    Vehicle ID: ${anomaly.vehicle_id}
                                </h6>
                                <p class="card-text">
                                    <strong>Date:</strong> ${this.formatDate(anomaly.log_date)}<br>
                                    <strong>Distance:</strong> ${anomaly.km_driven} km<br>
                                    <strong>Fuel:</strong> ${anomaly.fuel_used} L<br>
                                    <strong>Efficiency:</strong> ${anomaly.efficiency.toFixed(2)} km/L
                                </p>
                                <small class="text-muted">Anomaly Score: ${anomaly.anomaly_score.toFixed(3)}</small>
                            </div>
                        </div>
                    `).join('')}
                `;
            }
        } catch (error) {
            console.error('Failed to update anomaly display:', error);
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Set today's date as default for fuel log date
        document.getElementById('logDate').valueAsDate = new Date();
        
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Floating Action Button
        const fabButton = document.getElementById('fabButton');
        const fabMenu = document.getElementById('fabMenu');
        let fabMenuOpen = false;

        fabButton.addEventListener('click', () => {
            fabMenuOpen = !fabMenuOpen;
            if (fabMenuOpen) {
                fabMenu.classList.add('show');
                fabButton.innerHTML = '<i class="fas fa-times"></i>';
            } else {
                fabMenu.classList.remove('show');
                fabButton.innerHTML = '<i class="fas fa-plus"></i>';
            }
        });

        // Close FAB menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!fabButton.contains(e.target) && !fabMenu.contains(e.target)) {
                fabMenu.classList.remove('show');
                fabButton.innerHTML = '<i class="fas fa-plus"></i>';
                fabMenuOpen = false;
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch (e.key) {
                    case 'v':
                        e.preventDefault();
                        new bootstrap.Modal(document.getElementById('addVehicleModal')).show();
                        break;
                    case 'f':
                        e.preventDefault();
                        new bootstrap.Modal(document.getElementById('addFuelLogModal')).show();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.loadData();
                        break;
                }
            }
        });

        // Real-time updates
        setInterval(() => {
            this.loadData();
        }, 60000); // Update every minute
    }

    // Setup tooltips
    setupTooltips() {
        // Initialize Bootstrap tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Setup charts
    setupCharts() {
        // Chart defaults
        Chart.defaults.font.family = 'Inter';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
    }

    // Populate vehicle selects
    populateVehicleSelects() {
        const select = document.getElementById('logVehicle');
        select.innerHTML = '<option value="">Select Vehicle</option>';
        
        this.data.vehicles.forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = `${vehicle.name} (${vehicle.type})`;
            select.appendChild(option);
        });
    }

    // Add new vehicle
    async addVehicle() {
        const form = document.getElementById('addVehicleForm');
        const formData = new FormData(form);
        
        const vehicleData = {
            name: document.getElementById('vehicleName').value,
            type: document.getElementById('vehicleType').value,
            make: document.getElementById('vehicleMake').value,
            model: document.getElementById('vehicleModel').value,
            license_plate: document.getElementById('vehicleLicense').value,
            year: parseInt(document.getElementById('vehicleYear').value) || null
        };

        try {
            await this.apiCall('/vehicles', 'POST', vehicleData);
            this.showAlert('Vehicle added successfully!', 'success');
            form.reset();
            bootstrap.Modal.getInstance(document.getElementById('addVehicleModal')).hide();
            this.loadData();
        } catch (error) {
            console.error('Failed to add vehicle:', error);
        }
    }

    // Add new fuel log
    async addFuelLog() {
        const form = document.getElementById('addFuelLogForm');
        
        const logData = {
            vehicle_id: parseInt(document.getElementById('logVehicle').value),
            log_date: document.getElementById('logDate').value,
            km_driven: parseFloat(document.getElementById('logKmDriven').value),
            fuel_used: parseFloat(document.getElementById('logFuelUsed').value),
            cost: parseFloat(document.getElementById('logCost').value) || null,
            notes: document.getElementById('logNotes').value
        };

        try {
            await this.apiCall('/fuel-logs', 'POST', logData);
            this.showAlert('Fuel log added successfully!', 'success');
            form.reset();
            bootstrap.Modal.getInstance(document.getElementById('addFuelLogModal')).hide();
            this.loadData();
        } catch (error) {
            console.error('Failed to add fuel log:', error);
        }
    }

    // Delete vehicle
    async deleteVehicle(id) {
        if (confirm('Are you sure you want to delete this vehicle?')) {
            try {
                await this.apiCall(`/vehicles/${id}`, 'DELETE');
                this.showAlert('Vehicle deleted successfully!', 'success');
                this.loadData();
            } catch (error) {
                console.error('Failed to delete vehicle:', error);
            }
        }
    }

    // Delete fuel log
    async deleteFuelLog(id) {
        if (confirm('Are you sure you want to delete this fuel log?')) {
            try {
                await this.apiCall(`/fuel-logs/${id}`, 'DELETE');
                this.showAlert('Fuel log deleted successfully!', 'success');
                this.loadData();
            } catch (error) {
                console.error('Failed to delete fuel log:', error);
            }
        }
    }

    // Predict fuel consumption
    async predictFuel() {
        const km = document.getElementById('predictKm').value;
        if (!km) {
            this.showAlert('Please enter distance in kilometers', 'warning');
            return;
        }

        try {
            const result = await this.apiCall(`/predict?km=${km}`);
            document.getElementById('predictionResult').innerHTML = `
                <div class="alert alert-info">
                    <h6><i class="fas fa-calculator me-2"></i>Prediction Result</h6>
                    <p><strong>Distance:</strong> ${result.kilometers} km</p>
                    <p><strong>Predicted Fuel:</strong> ${result.predicted_fuel} L</p>
                    <p><strong>Model Accuracy:</strong> ${(result.model_score * 100).toFixed(1)}%</p>
                    <small class="text-muted">${result.note}</small>
                </div>
            `;
        } catch (error) {
            console.error('Failed to predict fuel:', error);
        }
    }

    // Detect anomalies
    async detectAnomalies() {
        try {
            const result = await this.apiCall('/detect-anomalies');
            const container = document.getElementById('anomalyDetectionResult');
            
            if (result.anomalies.length === 0) {
                container.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        No anomalies detected in ${result.total_records_analyzed} fuel records.
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Anomalies Detected</h6>
                        <p>Found ${result.anomalies_found} anomalies out of ${result.total_records_analyzed} records</p>
                        <small class="text-muted">${result.note}</small>
                    </div>
                    ${result.anomalies.map(anomaly => `
                        <div class="card anomaly-card mb-2">
                            <div class="card-body">
                                <small>
                                    <strong>Vehicle ID:</strong> ${anomaly.vehicle_id} |
                                    <strong>Date:</strong> ${this.formatDate(anomaly.log_date)} |
                                    <strong>Efficiency:</strong> ${anomaly.efficiency.toFixed(2)} km/L
                                </small>
                            </div>
                        </div>
                    `).join('')}
                `;
            }
        } catch (error) {
            console.error('Failed to detect anomalies:', error);
        }
    }

    // Utility functions
    getVehicleIcon(type) {
        const icons = {
            'Car': 'car',
            'Van': 'truck',
            'Truck': 'truck',
            'Bus': 'bus'
        };
        return icons[type] || 'car';
    }

    getVehicleTypeColor(type) {
        const colors = {
            'Car': 'primary',
            'Van': 'success',
            'Truck': 'warning',
            'Bus': 'info'
        };
        return colors[type] || 'secondary';
    }

    getEfficiencyClass(efficiency) {
        if (efficiency >= 12) return 'efficiency-excellent';
        if (efficiency >= 8) return 'efficiency-good';
        if (efficiency >= 5) return 'efficiency-average';
        return 'efficiency-poor';
    }

    getEfficiencyColor(efficiency) {
        if (efficiency >= 12) return '#28a745';
        if (efficiency >= 8) return '#17a2b8';
        if (efficiency >= 5) return '#ffc107';
        return '#dc3545';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '100px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        alertContainer.style.minWidth = '300px';
        
        document.body.appendChild(alertContainer);
        
        setTimeout(() => {
            alertContainer.remove();
        }, 5000);
    }
}

// Global functions for HTML onclick events
window.addVehicle = () => dashboard.addVehicle();
window.addFuelLog = () => dashboard.addFuelLog();
window.predictFuel = () => dashboard.predictFuel();
window.detectAnomalies = () => dashboard.detectAnomalies();

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new FleetFuelDashboard();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FleetFuelDashboard;
}
