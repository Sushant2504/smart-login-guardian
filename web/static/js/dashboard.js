/**
 * Dashboard Controller
 * Manages WebSocket connections, data updates, and UI interactions
 */

// WebSocket connection
let socket;
let riskChart;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initWebSocket();
    initCharts();
    loadInitialData();
    startStatsRefresh();
});

function initWebSocket() {
    socket = io.connect(window.location.origin);

    socket.on('connect', function() {
        console.log('Connected to Guardian');
        updateConnectionStatus(true);
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from Guardian');
        updateConnectionStatus(false);
    });

    socket.on('new_login', function(data) {
        handleNewLogin(data);
    });

    socket.on('connected', function(data) {
        console.log(data.message);
    });
}

function updateConnectionStatus(connected) {
    const indicator = document.getElementById('wsStatus');
    const text = document.getElementById('wsStatusText');

    if (connected) {
        indicator.classList.add('connected');
        text.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        text.textContent = 'Disconnected';
    }
}

function handleNewLogin(data) {
    // Add to threat feed
    addToThreatFeed(data);

    // Add marker to globe if location exists
    if (data.ip_address && data.risk_level) {
        // Use IP-based geolocation or provided location
        const location = extractLocation(data);
        if (location) {
            addLoginMarker(location.lat, location.lon, data.risk_level);
        }
    }

    // Update alerts if high risk
    if (data.risk_score >= 60) {
        addAlert(data);
    }

    // Refresh stats
    refreshStats();
}

function extractLocation(data) {
    // Try to get location from login data
    if (data.source && data.source.geo) {
        return {
            lat: data.source.geo.lat,
            lon: data.source.geo.lon
        };
    }

    // Fallback: generate random location for demo
    // In production, use real geolocation service
    return {
        lat: (Math.random() - 0.5) * 160,
        lon: (Math.random() - 0.5) * 360
    };
}

function addToThreatFeed(data) {
    const feed = document.getElementById('threatFeed');
    const item = document.createElement('div');
    item.className = `feed-item ${data.risk_level}`;

    const username = data.username || data.user?.username || 'Unknown';
    const ip = data.ip_address || data.source?.ip || 'Unknown';
    const timestamp = new Date(data.timestamp).toLocaleTimeString();

    let signalsHtml = '';
    if (data.threat && data.threat.signals && data.threat.signals.length > 0) {
        signalsHtml = '<div class="feed-signals">';
        data.threat.signals.forEach(signal => {
            signalsHtml += `<span class="signal-badge">${signal.description}</span>`;
        });
        signalsHtml += '</div>';
    } else if (data.signals && data.signals.length > 0) {
        signalsHtml = '<div class="feed-signals">';
        data.signals.forEach(signal => {
            signalsHtml += `<span class="signal-badge">${signal.description}</span>`;
        });
        signalsHtml += '</div>';
    }

    item.innerHTML = `
        <div class="feed-header">
            <span class="feed-username">${username}</span>
            <span class="feed-risk ${data.risk_level}">${data.risk_level.toUpperCase()} (${data.risk_score})</span>
        </div>
        <div class="feed-details">
            <span>🌐 ${ip}</span>
            <span>🕐 ${timestamp}</span>
        </div>
        ${signalsHtml}
    `;

    feed.insertBefore(item, feed.firstChild);

    // Keep only last 50 items
    while (feed.children.length > 50) {
        feed.removeChild(feed.lastChild);
    }

    // Auto-scroll to top for critical alerts
    if (data.risk_level === 'critical') {
        feed.scrollTop = 0;
    }
}

function addAlert(data) {
    const alertsList = document.getElementById('alertsList');
    const alert = document.createElement('div');
    alert.className = 'alert-item';

    const username = data.username || data.user?.username || 'Unknown';
    const timestamp = new Date(data.timestamp).toLocaleTimeString();

    alert.innerHTML = `
        <strong>${data.risk_level.toUpperCase()}</strong> - ${username}<br>
        <small>${timestamp} - Score: ${data.risk_score}</small>
    `;

    alertsList.insertBefore(alert, alertsList.firstChild);

    // Keep only last 20 alerts
    while (alertsList.children.length > 20) {
        alertsList.removeChild(alertsList.lastChild);
    }
}

function initCharts() {
    const ctx = document.getElementById('riskChart').getContext('2d');

    riskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Safe', 'Low', 'Medium', 'High', 'Critical'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(251, 146, 60, 0.8)',
                    'rgba(220, 38, 38, 0.8)'
                ],
                borderColor: [
                    '#10b981',
                    '#3b82f6',
                    '#f59e0b',
                    '#fb923c',
                    '#dc2626'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e0e7ff',
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

function loadInitialData() {
    // Load recent events
    fetch('/api/recent')
        .then(response => response.json())
        .then(data => {
            data.forEach(event => {
                addToThreatFeed(event);
                if (event.risk_score >= 60) {
                    addAlert(event);
                }
            });
        })
        .catch(error => console.error('Error loading recent events:', error));

    // Load threat intel
    refreshThreatIntel();
}

function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update stat cards
            document.getElementById('totalLogins').textContent = data.total_login_attempts || 0;
            document.getElementById('highRiskCount').textContent =
                (data.risk_distribution?.high || 0) + (data.risk_distribution?.critical || 0);
            document.getElementById('criticalCount').textContent = data.risk_distribution?.critical || 0;
            document.getElementById('successRate').textContent =
                data.success_rate ? data.success_rate.toFixed(1) + '%' : '0%';

            // Update chart
            if (data.risk_distribution) {
                riskChart.data.datasets[0].data = [
                    data.risk_distribution.safe || 0,
                    data.risk_distribution.low || 0,
                    data.risk_distribution.medium || 0,
                    data.risk_distribution.high || 0,
                    data.risk_distribution.critical || 0
                ];
                riskChart.update();
            }
        })
        .catch(error => console.error('Error refreshing stats:', error));
}

function refreshThreatIntel() {
    fetch('/api/threat-intel')
        .then(response => response.json())
        .then(data => {
            document.getElementById('maliciousIPs').textContent = data.malicious_ips_count || 0;
            document.getElementById('recentReports').textContent = data.recent_reports_count || 0;
            document.getElementById('reputationDB').textContent = data.reputation_db_size || 0;
        })
        .catch(error => console.error('Error loading threat intel:', error));
}

function startStatsRefresh() {
    // Refresh stats every 5 seconds
    setInterval(refreshStats, 5000);

    // Refresh threat intel every 30 seconds
    setInterval(refreshThreatIntel, 30000);
}

function simulateAttack(scenario) {
    fetch(`/api/simulate/${scenario}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Simulated ${scenario}:`, data);
            // Events will come through WebSocket
        })
        .catch(error => console.error('Error simulating attack:', error));
}

function clearFeed() {
    document.getElementById('threatFeed').innerHTML = '';
}

// Make functions globally available
window.simulateAttack = simulateAttack;
window.clearFeed = clearFeed;
window.toggleAutoRotate = toggleAutoRotate;
