
async function loadSummary() {
    try {
        const response = await fetch('/api/summary');
        if (!response.ok) {
            throw new Error('Could not load dashboard summary.');
        }

        const data = await response.json();

        document.getElementById('totalAttacks').textContent =
            Number(data.total_attacks).toLocaleString();

        document.getElementById('latestTotal').textContent =
            Number(data.latest_total).toLocaleString();

        document.getElementById('topThreat').textContent =
            data.highest_attack;

        // Prevent duplicate charts if the summary is loaded again.
        const trendCanvas = document.getElementById('trendChart');
        const attackCanvas = document.getElementById('attackChart');

        const oldTrend = Chart.getChart(trendCanvas);
        if (oldTrend) oldTrend.destroy();

        const oldAttack = Chart.getChart(attackCanvas);
        if (oldAttack) oldAttack.destroy();

        new Chart(trendCanvas, {
            type: 'line',
            data: {
                labels: data.months.map(m => `M${m}`),
                datasets: [{
                    label: 'Total attacks',
                    data: data.monthly_totals,
                    borderWidth: 2,
                    tension: 0.35,
                    fill: true
                }]
            },
            options: chartOptions()
        });

        new Chart(attackCanvas, {
            type: 'doughnut',
            data: {
                labels: data.attack_types,
                datasets: [{
                    data: data.attack_totals,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#c9d5e6' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Dashboard summary error:', error);
    }
}

function chartOptions() {
    return {
        responsive: true,
        scales: {
            x: {
                ticks: { color: '#8290a7' },
                grid: { color: 'rgba(255,255,255,.05)' }
            },
            y: {
                ticks: { color: '#8290a7' },
                grid: { color: 'rgba(255,255,255,.05)' }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#c9d5e6' }
            }
        }
    };
}

async function predictTrend() {
    const attackType = document.getElementById('attackType').value;
    const monthsAhead = Number(
        document.getElementById('monthsAhead').value
    );

    const button = document.querySelector('.prediction-panel button');
    button.textContent = 'Analyzing...';
    button.disabled = true;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                attack_type: attackType,
                months_ahead: monthsAhead
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Prediction failed.');
        }

        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('resultBox').classList.remove('hidden');

        document.getElementById('resultType').textContent =
            data.attack_type;

        document.getElementById('predictedValue').textContent =
            Number(data.predicted_attacks).toLocaleString();

        document.getElementById('trendValue').textContent = data.trend;
        document.getElementById('riskValue').textContent = data.risk;

        document.getElementById('confidenceValue').textContent =
            `${data.confidence}% indicator`;

        document.getElementById('recommendationValue').textContent =
            data.recommendation;

    } catch (error) {
        alert(error.message);
    } finally {
        button.textContent = 'Run Prediction';
        button.disabled = false;
    }
}

loadSummary();
