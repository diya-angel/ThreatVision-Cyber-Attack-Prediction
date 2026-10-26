// Show a warning when the predicted risk is High or Critical.
function showRiskAlert(risk, attackType, predictedAttacks, monthsAhead) {
    let banner = document.getElementById('threatAlertBanner');

    if (!banner) {
        banner = document.createElement('section');
        banner.id = 'threatAlertBanner';
        banner.setAttribute('role', 'alert');
        banner.setAttribute('aria-live', 'assertive');

        banner.style.cssText =
            'display:none;margin:0 0 22px;padding:16px 20px;' +
            'border-radius:12px;border:1px solid #ef4444;' +
            'background:rgba(127,29,29,.30);color:#fee2e2;';

        const header = document.getElementById('overview');

        if (header && header.parentNode) {
            header.parentNode.insertBefore(banner, header.nextSibling);
        }
    }

    if (risk === 'High' || risk === 'Critical') {
        const critical = risk === 'Critical';

        banner.style.display = 'block';
        banner.style.borderColor = critical ? '#ef4444' : '#f97316';
        banner.style.background = critical
            ? 'rgba(127,29,29,.35)'
            : 'rgba(124,45,18,.30)';
        banner.style.color = critical ? '#fee2e2' : '#ffedd5';

        banner.replaceChildren();

        const title = document.createElement('strong');
        title.textContent =
            (critical ? 'CRITICAL RISK ALERT' : 'HIGH RISK ALERT') +
            ' — ' + attackType;

        const message = document.createElement('p');
        message.style.cssText = 'margin:8px 0 12px;line-height:1.5';

        message.textContent =
            'Predicted attacks: ' +
            Number(predictedAttacks).toLocaleString() +
            ' | Forecast period: ' + monthsAhead +
            (Number(monthsAhead) === 1 ? ' month.' : ' months.') +
            ' Please review the recommended mitigation. ' +
            'This is a forecast warning, not live attack detection.';

        const dismiss = document.createElement('button');
        dismiss.type = 'button';
        dismiss.textContent = 'Dismiss warning';

        dismiss.style.cssText =
            'padding:7px 12px;border:1px solid currentColor;' +
            'border-radius:7px;background:transparent;' +
            'color:inherit;cursor:pointer';

        dismiss.addEventListener('click', function () {
            banner.style.display = 'none';
        });

        banner.appendChild(title);
        banner.appendChild(message);
        banner.appendChild(dismiss);

        banner.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest'
        });
    } else {
        banner.style.display = 'none';
        banner.replaceChildren();
    }
}

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

        // New alert feature: warn for High or Critical forecast risk.
        showRiskAlert(
            data.risk,
            data.attack_type,
            data.predicted_attacks,
            data.months_ahead
        );

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
