from fastapi import APIRouter, Request, Query, status
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional

from services.health_service import health_service

router = APIRouter(tags=["Health & Monitoring"])


def render_health_html(data: dict) -> str:
    """Renders a self-contained, responsive, real-time health monitoring dashboard."""
    overall_status = data.get("status", "unknown").lower()
    system = data.get("system", {})
    services = data.get("services", {})

    status_colors = {
        "healthy": {"bg": "#ecfdf5", "text": "#065f46", "border": "#10b981", "badge": "#059669"},
        "degraded": {"bg": "#fffbeb", "text": "#92400e", "border": "#f59e0b", "badge": "#d97706"},
        "unhealthy": {"bg": "#fef2f2", "text": "#991b1b", "border": "#ef4444", "badge": "#dc2626"},
    }
    current_theme = status_colors.get(overall_status, status_colors["degraded"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dukaan Server Health &amp; Diagnostics</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⚡</text></svg>">
  <style>
    :root {{
      --bg-base: #0f172a;
      --bg-card: #1e293b;
      --bg-card-hover: #24344d;
      --border-color: #334155;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --color-healthy: #10b981;
      --color-degraded: #f59e0b;
      --color-unhealthy: #ef4444;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-family);
      background-color: var(--bg-base);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding: 24px;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      width: 100%;
    }}
    header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 24px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .logo-badge {{
      background: linear-gradient(135deg, #f59e0b, #ef4444);
      color: white;
      font-weight: 800;
      font-size: 20px;
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }}
    .brand-title h1 {{
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}
    .brand-title p {{
      font-size: 13px;
      color: var(--text-muted);
    }}
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .btn {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
      transition: all 0.2s ease;
    }}
    .btn:hover {{
      background: var(--bg-card-hover);
      border-color: #475569;
    }}
    .btn-primary {{
      background: #2563eb;
      border-color: #3b82f6;
      color: white;
    }}
    .btn-primary:hover {{
      background: #1d4ed8;
    }}
    .auto-refresh-select {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 13px;
      outline: none;
      cursor: pointer;
    }}
    /* Status Banner */
    .status-banner {{
      background: var(--bg-card);
      border: 1px solid {current_theme['border']};
      border-radius: 14px;
      padding: 24px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      margin-bottom: 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }}
    .banner-main {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .status-beacon {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background-color: {current_theme['badge']};
      box-shadow: 0 0 14px {current_theme['badge']};
      animation: pulse 2s infinite ease-in-out;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 {current_theme['badge']}99; }}
      70% {{ transform: scale(1.05); box-shadow: 0 0 0 10px rgba(0,0,0,0); }}
      100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0,0,0,0); }}
    }}
    .banner-text h2 {{
      font-size: 20px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: {current_theme['badge']};
    }}
    .banner-text p {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .banner-metrics {{
      display: flex;
      gap: 24px;
    }}
    .metric-pill {{
      text-align: right;
    }}
    .metric-pill .label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
    }}
    .metric-pill .value {{
      font-size: 18px;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 2px;
    }}
    /* System Overview Grid */
    .overview-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .stat-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 16px;
    }}
    .stat-card .label {{
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}
    .stat-card .value {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text-main);
      word-break: break-all;
    }}
    /* Services Section */
    .section-title {{
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .services-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .service-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }}
    .service-card:hover {{
      border-color: #475569;
      transform: translateY(-2px);
    }}
    .service-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .service-name {{
      font-size: 16px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-healthy {{
      background: rgba(16, 185, 129, 0.15);
      color: var(--color-healthy);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    .badge-degraded {{
      background: rgba(245, 158, 11, 0.15);
      color: var(--color-degraded);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    .badge-unhealthy {{
      background: rgba(239, 68, 68, 0.15);
      color: var(--color-unhealthy);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .service-details {{
      font-size: 13px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 14px;
      min-height: 40px;
    }}
    .service-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      padding-top: 12px;
      font-size: 12px;
    }}
    .latency-pill {{
      font-family: monospace;
      font-size: 12px;
      background: rgba(255,255,255,0.05);
      padding: 2px 8px;
      border-radius: 6px;
    }}
    footer {{
      margin-top: auto;
      text-align: center;
      font-size: 12px;
      color: var(--text-muted);
      padding: 20px 0;
      border-top: 1px solid var(--border-color);
    }}
    .spin {{
      animation: rotation 1s infinite linear;
    }}
    @keyframes rotation {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(359deg); }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="logo-badge">D</div>
        <div class="brand-title">
          <h1>Dukaan Server Health</h1>
          <p>Real-time infrastructure &amp; service monitoring</p>
        </div>
      </div>
      <div class="header-actions">
        <select id="autoRefreshSelect" class="auto-refresh-select" onchange="updateAutoRefresh(this.value)">
          <option value="0">Auto-refresh: Off</option>
          <option value="5">Auto-refresh: 5s</option>
          <option value="10" selected>Auto-refresh: 10s</option>
          <option value="30">Auto-refresh: 30s</option>
        </select>
        <button id="refreshBtn" class="btn btn-primary" onclick="fetchLiveHealth()">
          <span id="refreshIcon">↻</span> Refresh
        </button>
        <a href="/health?format=json" target="_blank" class="btn">Raw JSON</a>
      </div>
    </header>

    <!-- Global Status Banner -->
    <div id="statusBanner" class="status-banner">
      <div class="banner-main">
        <div id="statusBeacon" class="status-beacon"></div>
        <div class="banner-text">
          <h2 id="statusTitle">{overall_status}</h2>
          <p id="statusSubtitle">All critical server dependencies are operational</p>
        </div>
      </div>
      <div class="banner-metrics">
        <div class="metric-pill">
          <div class="label">Server Uptime</div>
          <div id="uptimeDisplay" class="value">{system.get('uptime_human', 'N/A')}</div>
        </div>
        <div class="metric-pill">
          <div class="label">Memory (RSS)</div>
          <div id="memoryDisplay" class="value">{system.get('memory_rss_mb', 'N/A')} MB</div>
        </div>
        <div class="metric-pill">
          <div class="label">Active Threads</div>
          <div id="threadsDisplay" class="value">{system.get('threads_count', 'N/A')}</div>
        </div>
      </div>
    </div>

    <!-- System Details Grid -->
    <div class="overview-grid">
      <div class="stat-card">
        <div class="label">Host Platform</div>
        <div id="platformDisplay" class="value">{system.get('platform', 'N/A')}</div>
      </div>
      <div class="stat-card">
        <div class="label">Python Version</div>
        <div id="pythonDisplay" class="value">{system.get('python_version', 'N/A')}</div>
      </div>
      <div class="stat-card">
        <div class="label">Process ID (PID)</div>
        <div id="pidDisplay" class="value">{system.get('pid', 'N/A')}</div>
      </div>
      <div class="stat-card">
        <div class="label">Started At</div>
        <div id="startedDisplay" class="value">{system.get('started_at', 'N/A')[:19].replace('T', ' ')} UTC</div>
      </div>
    </div>

    <!-- Subsystems Grid -->
    <div class="section-title">📦 Subsystems &amp; Data Stores</div>
    <div id="servicesGrid" class="services-grid">
      <!-- PostgreSQL -->
      <div class="service-card" id="card-postgres">
        <div>
          <div class="service-header">
            <span class="service-name">🐘 PostgreSQL</span>
            <span class="badge badge-{services.get('postgresql', {}).get('status', 'degraded')}">
              {services.get('postgresql', {}).get('status', 'unknown')}
            </span>
          </div>
          <div class="service-details">
            {services.get('postgresql', {}).get('message') or services.get('postgresql', {}).get('error', 'Checking...')}
          </div>
        </div>
        <div class="service-footer">
          <span>Query Latency</span>
          <span class="latency-pill">{services.get('postgresql', {}).get('latency_ms', '0')} ms</span>
        </div>
      </div>

      <!-- Redis -->
      <div class="service-card" id="card-redis">
        <div>
          <div class="service-header">
            <span class="service-name">⚡ Redis Cache</span>
            <span class="badge badge-{services.get('redis', {}).get('status', 'degraded')}">
              {services.get('redis', {}).get('status', 'unknown')}
            </span>
          </div>
          <div class="service-details">
            {services.get('redis', {}).get('message') or services.get('redis', {}).get('error', 'Checking...')}
          </div>
        </div>
        <div class="service-footer">
          <span>Ping Latency</span>
          <span class="latency-pill">{services.get('redis', {}).get('latency_ms', '0')} ms</span>
        </div>
      </div>

      <!-- MongoDB -->
      <div class="service-card" id="card-mongodb">
        <div>
          <div class="service-header">
            <span class="service-name">🍃 MongoDB NoSQL</span>
            <span class="badge badge-{services.get('mongodb', {}).get('status', 'degraded')}">
              {services.get('mongodb', {}).get('status', 'unknown')}
            </span>
          </div>
          <div class="service-details">
            {services.get('mongodb', {}).get('message') or services.get('mongodb', {}).get('error', 'Checking...')}
          </div>
        </div>
        <div class="service-footer">
          <span>Admin Ping</span>
          <span class="latency-pill">{services.get('mongodb', {}).get('latency_ms', '0')} ms</span>
        </div>
      </div>

      <!-- RabbitMQ -->
      <div class="service-card" id="card-rabbitmq">
        <div>
          <div class="service-header">
            <span class="service-name">🐇 RabbitMQ Broker</span>
            <span class="badge badge-{services.get('rabbitmq', {}).get('status', 'degraded')}">
              {services.get('rabbitmq', {}).get('status', 'unknown')}
            </span>
          </div>
          <div class="service-details">
            {services.get('rabbitmq', {}).get('message') or services.get('rabbitmq', {}).get('error', 'Checking...')}
          </div>
        </div>
        <div class="service-footer">
          <span>Broker Latency</span>
          <span class="latency-pill">{services.get('rabbitmq', {}).get('latency_ms', '0')} ms</span>
        </div>
      </div>

      <!-- User Agent -->
      <div class="service-card" id="card-useragent">
        <div>
          <div class="service-header">
            <span class="service-name">🤖 User Agent Graph</span>
            <span class="badge badge-healthy">
              {services.get('agents', {}).get('user_agent', {}).get('status', 'ready')}
            </span>
          </div>
          <div class="service-details">
            LangGraph state machine for user chat, recommendations, and negotiation.
          </div>
        </div>
        <div class="service-footer">
          <span>Subsystem</span>
          <span class="latency-pill">Active</span>
        </div>
      </div>

      <!-- Merchant Agent -->
      <div class="service-card" id="card-merchantagent">
        <div>
          <div class="service-header">
            <span class="service-name">📊 Merchant Agent Graph</span>
            <span class="badge badge-healthy">
              {services.get('agents', {}).get('merchant_agent', {}).get('status', 'ready')}
            </span>
          </div>
          <div class="service-details">
            Store management, catalog publishing, and analytics AI tools.
          </div>
        </div>
        <div class="service-footer">
          <span>Subsystem</span>
          <span class="latency-pill">Active</span>
        </div>
      </div>
    </div>

    <footer>
      <p>Dukaan Backend Health &bull; Updated <span id="lastUpdated">just now</span></p>
    </footer>
  </div>

  <script>
    let refreshTimer = null;
    let secondsSinceUpdate = 0;

    function getBadgeClass(status) {{
      if (status === 'healthy') return 'badge-healthy';
      if (status === 'unhealthy') return 'badge-unhealthy';
      return 'badge-degraded';
    }}

    async function fetchLiveHealth() {{
      const btn = document.getElementById('refreshBtn');
      const icon = document.getElementById('refreshIcon');
      icon.classList.add('spin');
      btn.disabled = true;

      try {{
        const res = await fetch('/health?format=json');
        if (!res.ok && res.status !== 503) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        renderLiveMetrics(data);
        secondsSinceUpdate = 0;
        document.getElementById('lastUpdated').textContent = 'just now';
      }} catch (err) {{
        console.error('Failed to fetch live health metrics:', err);
      }} finally {{
        icon.classList.remove('spin');
        btn.disabled = false;
      }}
    }}

    function renderLiveMetrics(data) {{
      const status = (data.status || 'unknown').toLowerCase();
      const statusTitle = document.getElementById('statusTitle');
      const statusBeacon = document.getElementById('statusBeacon');
      const banner = document.getElementById('statusBanner');

      statusTitle.textContent = status;
      if (status === 'healthy') {{
        statusTitle.style.color = 'var(--color-healthy)';
        statusBeacon.style.backgroundColor = 'var(--color-healthy)';
        statusBeacon.style.boxShadow = '0 0 14px var(--color-healthy)';
        banner.style.borderColor = 'var(--color-healthy)';
      }} else if (status === 'unhealthy') {{
        statusTitle.style.color = 'var(--color-unhealthy)';
        statusBeacon.style.backgroundColor = 'var(--color-unhealthy)';
        statusBeacon.style.boxShadow = '0 0 14px var(--color-unhealthy)';
        banner.style.borderColor = 'var(--color-unhealthy)';
      }} else {{
        statusTitle.style.color = 'var(--color-degraded)';
        statusBeacon.style.backgroundColor = 'var(--color-degraded)';
        statusBeacon.style.boxShadow = '0 0 14px var(--color-degraded)';
        banner.style.borderColor = 'var(--color-degraded)';
      }}

      // Metrics
      const sys = data.system || {{}};
      document.getElementById('uptimeDisplay').textContent = sys.uptime_human || 'N/A';
      document.getElementById('memoryDisplay').textContent = (sys.memory_rss_mb || 'N/A') + ' MB';
      document.getElementById('threadsDisplay').textContent = sys.threads_count || 'N/A';

      // Update Service Cards
      const services = data.services || {{}};
      updateCard('card-postgres', services.postgresql);
      updateCard('card-redis', services.redis);
      updateCard('card-mongodb', services.mongodb);
      updateCard('card-rabbitmq', services.rabbitmq);
    }}

    function updateCard(cardId, sData) {{
      const card = document.getElementById(cardId);
      if (!card || !sData) return;
      const badge = card.querySelector('.badge');
      const details = card.querySelector('.service-details');
      const latencyPill = card.querySelector('.latency-pill');

      badge.className = 'badge ' + getBadgeClass(sData.status);
      badge.textContent = sData.status || 'unknown';
      details.textContent = sData.message || sData.error || '';
      if (latencyPill && sData.latency_ms !== undefined) {{
        latencyPill.textContent = sData.latency_ms + ' ms';
      }}
    }}

    function updateAutoRefresh(seconds) {{
      if (refreshTimer) clearInterval(refreshTimer);
      const sec = parseInt(seconds, 10);
      if (sec > 0) {{
        refreshTimer = setInterval(fetchLiveHealth, sec * 1000);
      }}
    }}

    // Local tick for last updated label
    setInterval(() => {{
      secondsSinceUpdate++;
      const el = document.getElementById('lastUpdated');
      if (el) {{
        if (secondsSinceUpdate < 5) el.textContent = 'just now';
        else el.textContent = secondsSinceUpdate + 's ago';
      }}
    }}, 1000);

    // Initial timer setup for 10s auto-refresh
    updateAutoRefresh(10);
  </script>
</body>
</html>"""


@router.get("/health", response_class=HTMLResponse)
async def health_check(
    request: Request,
    format: Optional[str] = Query(None, description="Output format: 'json' or 'html'"),
):
    """
    Main health monitoring website and API endpoint.
    - Browsers navigating to /health receive a rich, real-time interactive HTML dashboard.
    - API clients or requests with format=json receive structured JSON diagnostic metrics.
    """
    health_data = await health_service.get_full_health()
    accept_header = request.headers.get("accept", "").lower()

    # If client explicitly wants JSON, or format query param is 'json', or client is not a browser:
    if format == "json" or "application/json" in accept_header and "text/html" not in accept_header:
        http_status = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if health_data["status"] == "unhealthy"
            else status.HTTP_200_OK
        )
        return JSONResponse(content=health_data, status_code=http_status)

    # Return interactive HTML website
    html_content = render_health_html(health_data)
    http_status = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if health_data["status"] == "unhealthy"
        else status.HTTP_200_OK
    )
    return HTMLResponse(content=html_content, status_code=http_status)


@router.get("/api/health", response_class=JSONResponse)
@router.get("/health/json", response_class=JSONResponse)
async def health_check_json():
    """Explicit JSON health diagnostics endpoint for automated monitoring systems."""
    health_data = await health_service.get_full_health()
    http_status = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if health_data["status"] == "unhealthy"
        else status.HTTP_200_OK
    )
    return JSONResponse(content=health_data, status_code=http_status)


@router.get("/health/live", response_class=JSONResponse)
async def health_live():
    """Liveness probe: verifies process is alive and responsive."""
    return JSONResponse(content=health_service.get_liveness(), status_code=status.HTTP_200_OK)


@router.get("/health/ready", response_class=JSONResponse)
async def health_ready():
    """Readiness probe: verifies core PostgreSQL and Redis connections."""
    pg_res = await health_service.check_postgres()
    redis_res = await health_service.check_redis()

    is_ready = pg_res.get("status") == "healthy" and redis_res.get("status") == "healthy"
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "postgresql": pg_res,
            "redis": redis_res,
        },
    }
    http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=payload, status_code=http_status)
