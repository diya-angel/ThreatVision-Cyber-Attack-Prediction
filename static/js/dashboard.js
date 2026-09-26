async function loadSummary() {
    const response = await fetch('/api/summary');
    const data = await response.json();

    document.getElementById('totalAttacks').textContent = data.total_attacks.toLocaleString();
    document.getElementById('latestTotal').textContent = data.latest_total.toLocaleString();
    document.getElementById('topThreat').textContent = data.highest_attack;

    new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: data.months.map(m => `M${m}`),
            datasets: [{label: 'Total attacks', data: data.monthly_totals, borderWidth: 2, tension: 0.35, fill: true}]
        },
        options: chartOptions()
    });

    new Chart(document.getElementById('attackChart'), {
        type: 'doughnut',
        data: {labels: data.attack_types, datasets: [{data: data.attack_totals, borderWidth: 0}]},
        options: {responsive: true, plugins: {legend: {labels: {color: '#c9d5e6'}}}}
    });
}

function chartOptions() {
    return {
        responsive: true,
        scales: {
            x: {ticks: {color: '#8290a7'}, grid: {color: 'rgba(255,255,255,.05)'}},
            y: {ticks: {color: '#8290a7'}, grid: {color: 'rgba(255,255,255,.05)'}}
        },
        plugins: {legend: {labels: {color: '#c9d5e6'}}}
    };
}

async function predictTrend() {
    const attackType = document.getElementById('attackType').value;
    const monthsAhead = document.getElementById('monthsAhead').value;
    const button = document.querySelector('.prediction-panel button');
    button.textContent = 'Analyzing...';
    button.disabled = true;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({attack_type: attackType, months_ahead: monthsAhead})
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Prediction failed');

        document.getElementById('emptyState').classList.add('hidden');
        document.getElementById('resultBox').classList.remove('hidden');
        document.getElementById('resultType').textContent = data.attack_type;
        document.getElementById('predictedValue').textContent = data.predicted_attacks;
        document.getElementById('trendValue').textContent = data.trend;
        document.getElementById('riskValue').textContent = data.risk;
        document.getElementById('confidenceValue').textContent = `${data.confidence}%`;
        document.getElementById('recommendationValue').textContent = data.recommendation;
    } catch (err) {
        alert(err.message);
    } finally {
        button.textContent = 'Run Prediction';
        button.disabled = false;
    }
}

loadSummary();
