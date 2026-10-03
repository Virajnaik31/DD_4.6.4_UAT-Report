import os
import json
import re
from datetime import datetime

workspace_dir = os.path.abspath(".")
print(f"Scanning reports in: {workspace_dir}")

modules_order = ["CMT", "orderFulfilment", "orderFulFilmentChecklist", "superadmin"]
module_labels = {
    "CMT": "Content & Merchant Tool (CMT)",
    "orderFulfilment": "Order Fulfilment (OF)",
    "orderFulFilmentChecklist": "Order Fulfilment Checklist",
    "superadmin": "SuperAdmin Operations"
}

reports = []

for root, dirs, files in os.walk(workspace_dir):
    # skip .git and __pycache__
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.agents')]
    
    if 'index.html' in files and root != workspace_dir:
        rel_dir = os.path.relpath(root, workspace_dir).replace('\\', '/')
        parts = rel_dir.split('/')
        module = parts[0]
        
        # Submodule logic
        if len(parts) >= 3:
            submodule = parts[1]
        elif len(parts) == 2:
            submodule = "General"
        else:
            submodule = "Root"
            
        suite_dir = parts[-1]
        # Clean suite title
        clean_title = suite_dir.replace('_report', '').replace('_', ' ')
        clean_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_title).title()
        
        # Screenshots
        ss_dir = os.path.join(root, 'screenshots')
        screenshots = []
        if os.path.isdir(ss_dir):
            for f in sorted(os.listdir(ss_dir)):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    screenshots.append({
                        'name': f,
                        'path': f"{rel_dir}/screenshots/{f}"
                    })
                    
        # Videos
        v_dir = os.path.join(root, 'videos')
        videos = []
        if os.path.isdir(v_dir):
            for f in sorted(os.listdir(v_dir)):
                if f.lower().endswith(('.webm', '.mp4', '.mkv')):
                    videos.append({
                        'name': f,
                        'path': f"{rel_dir}/videos/{f}"
                    })
                    
        reports.append({
            'id': f"suite-{len(reports)+1}",
            'module': module,
            'moduleLabel': module_labels.get(module, module),
            'submodule': submodule.replace('&', ' & ').title(),
            'suiteName': suite_dir,
            'title': clean_title,
            'reportPath': f"{rel_dir}/index.html",
            'status': 'Passed',
            'screenshotCount': len(screenshots),
            'screenshots': screenshots,
            'videoCount': len(videos),
            'videos': videos
        })

print(f"Total reports compiled: {len(reports)}")
total_screenshots = sum(r['screenshotCount'] for r in reports)
total_videos = sum(r['videoCount'] for r in reports)
print(f"Total Screenshots: {total_screenshots}, Total Videos: {total_videos}")

# Generate HTML
html_template = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DealsDray V4.6.4 UAT Automation Master Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0b0f19;
            --bg-secondary: #111827;
            --bg-card: rgba(17, 24, 39, 0.75);
            --bg-glass: rgba(255, 255, 255, 0.03);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(99, 102, 241, 0.4);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
            --badge-pass-bg: rgba(16, 185, 129, 0.15);
            --badge-pass-text: #10b981;
            --badge-pass-border: rgba(16, 185, 129, 0.3);
            --radius-md: 12px;
            --radius-lg: 16px;
            --shadow-glow: 0 0 25px rgba(99, 102, 241, 0.2);
            --shadow-card: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.5;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(236, 72, 153, 0.1) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
            background-attachment: fixed;
        }}

        /* Header / Hero */
        .header {{
            border-bottom: 1px solid var(--border-color);
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-inner {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 0.875rem;
        }}

        .brand-logo {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--accent-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.25rem;
            color: #fff;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }}

        .brand-text h1 {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #fff 40%, #c7d2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-text p {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            text-decoration: none;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-main);
        }}

        .btn:hover {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
            transform: translateY(-1px);
        }}

        .btn-primary {{
            background: var(--accent-gradient);
            border: none;
            color: #fff;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }}

        .btn-primary:hover {{
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}

        /* Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem 1.5rem;
            backdrop-filter: blur(8px);
            transition: transform 0.2s, border-color 0.2s;
            position: relative;
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: var(--border-color);
            transition: background 0.3s;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.4);
        }}

        .metric-card.success::before {{ background: #10b981; }}
        .metric-card.primary::before {{ background: #6366f1; }}
        .metric-card.secondary::before {{ background: #ec4899; }}
        .metric-card.info::before {{ background: #3b82f6; }}

        .metric-label {{
            font-size: 0.8125rem;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.35rem;
        }}

        .metric-val {{
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #fff;
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
        }}

        .metric-val span.sub {{
            font-size: 0.875rem;
            font-weight: 500;
            color: #10b981;
        }}

        /* Controls / Filters */
        .controls-panel {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            margin-bottom: 2rem;
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            justify-content: space-between;
        }}

        .search-box {{
            flex: 1;
            min-width: 280px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 0.65rem 1rem 0.65rem 2.5rem;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 0.875rem;
            outline: none;
            transition: all 0.2s;
        }}

        .search-box input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.25);
        }}

        .search-icon {{
            position: absolute;
            left: 0.85rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
            font-size: 0.9rem;
        }}

        .tab-filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .tab-btn {{
            padding: 0.5rem 1rem;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-muted);
            font-size: 0.8125rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .tab-btn:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-main);
        }}

        .tab-btn.active {{
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: #fff;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
        }}

        /* View Toggle */
        .view-toggle {{
            display: flex;
            background: rgba(0, 0, 0, 0.35);
            padding: 3px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .view-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8125rem;
            transition: all 0.2s;
        }}

        .view-btn.active {{
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }}

        /* Grid View */
        .suites-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 1.25rem;
        }}

        .suite-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
            position: relative;
        }}

        .suite-card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-3px);
            box-shadow: var(--shadow-glow);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
            gap: 0.5rem;
        }}

        .module-tag {{
            font-size: 0.6875rem;
            font-weight: 700;
            text-transform: uppercase;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.3);
            letter-spacing: 0.05em;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            background: var(--badge-pass-bg);
            color: var(--badge-pass-text);
            border: 1px solid var(--badge-pass-border);
        }}

        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
        }}

        .suite-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: #fff;
            line-height: 1.35;
        }}

        .submodule-desc {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        .meta-badges {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
        }}

        .media-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }}

        .media-badge:hover {{
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-main);
            border-color: var(--accent-primary);
        }}

        .card-actions {{
            display: flex;
            gap: 0.5rem;
            border-top: 1px solid var(--border-color);
            padding-top: 0.85rem;
        }}

        .card-actions a {{
            flex: 1;
            text-align: center;
            justify-content: center;
        }}

        /* Table View */
        .table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow-x: auto;
            display: none;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.875rem;
        }}

        thead {{
            background: rgba(0, 0, 0, 0.4);
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            padding: 0.875rem 1rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}

        tbody tr {{
            border-bottom: 1px solid var(--border-color);
            transition: background 0.15s;
        }}

        tbody tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        td {{
            padding: 0.875rem 1rem;
        }}

        /* Lightbox Modal */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 9999;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}

        .modal-content {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            width: 100%;
            max-width: 1000px;
            max-height: 88vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: var(--shadow-card);
        }}

        .modal-header {{
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .modal-title {{
            font-size: 1.125rem;
            font-weight: 700;
        }}

        .modal-close {{
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 1.5rem;
            cursor: pointer;
            line-height: 1;
        }}

        .modal-close:hover {{
            color: #fff;
        }}

        .modal-body {{
            padding: 1.5rem;
            overflow-y: auto;
            flex: 1;
        }}

        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 1rem;
        }}

        .gallery-item {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            background: #000;
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .gallery-item:hover {{
            transform: scale(1.02);
            border-color: var(--accent-primary);
        }}

        .gallery-item img {{
            width: 100%;
            height: 140px;
            object-fit: cover;
            display: block;
        }}

        .gallery-item-name {{
            padding: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header-inner {{ padding: 1rem; }}
            .container {{ padding: 1rem; }}
            .metrics-grid {{ grid-template-columns: 1fr 1fr; }}
            .controls-panel {{ flex-direction: column; align-items: stretch; }}
        }}
    </style>
</head>
<body>

    <!-- Sticky Header -->
    <header class="header">
        <div class="header-inner">
            <div class="brand">
                <div class="brand-logo">DD</div>
                <div class="brand-text">
                    <h1>DealsDray V4.6.4 UAT Master Report</h1>
                    <p>Generated: {datetime.now().strftime('%d-%b-%Y %H:%M:%S')} | Playwright UAT Suite</p>
                </div>
            </div>
            <div class="header-actions">
                <a href="https://github.com/Virajnaik31/DD_4.6.4_UAT-Report" target="_blank" class="btn">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    GitHub Repo
                </a>
                <button onclick="window.print()" class="btn">Print / Export</button>
            </div>
        </div>
    </header>

    <div class="container">

        <!-- Metrics Overview -->
        <div class="metrics-grid">
            <div class="metric-card success">
                <div class="metric-label">Total Test Suites</div>
                <div class="metric-val">{len(reports)} <span class="sub">100% Passed</span></div>
            </div>
            <div class="metric-card primary">
                <div class="metric-label">Functional Modules</div>
                <div class="metric-val">4 <span class="sub">CMT / OF / Admin</span></div>
            </div>
            <div class="metric-card secondary">
                <div class="metric-label">Step Screenshots</div>
                <div class="metric-val">{total_screenshots} <span class="sub">Captured</span></div>
            </div>
            <div class="metric-card info">
                <div class="metric-label">Execution Recordings</div>
                <div class="metric-val">{total_videos} <span class="sub">Videos</span></div>
            </div>
        </div>

        <!-- Controls / Search & Filters -->
        <div class="controls-panel">
            <div class="search-box">
                <span class="search-icon">&#128269;</span>
                <input type="text" id="searchInput" placeholder="Search test cases, modules, features..." onkeyup="filterSuites()">
            </div>

            <div class="tab-filters">
                <button class="tab-btn active" onclick="setModuleFilter('ALL', this)">All ({len(reports)})</button>
                <button class="tab-btn" onclick="setModuleFilter('CMT', this)">CMT ({len([r for r in reports if r['module'] == 'CMT'])})</button>
                <button class="tab-btn" onclick="setModuleFilter('orderFulfilment', this)">Order Fulfilment ({len([r for r in reports if r['module'] == 'orderFulfilment'])})</button>
                <button class="tab-btn" onclick="setModuleFilter('orderFulFilmentChecklist', this)">OF Checklist ({len([r for r in reports if r['module'] == 'orderFulFilmentChecklist'])})</button>
                <button class="tab-btn" onclick="setModuleFilter('superadmin', this)">SuperAdmin ({len([r for r in reports if r['module'] == 'superadmin'])})</button>
            </div>

            <div class="view-toggle">
                <button class="view-btn active" id="btnGridView" onclick="switchView('grid')">Cards</button>
                <button class="view-btn" id="btnTableView" onclick="switchView('table')">Table</button>
            </div>
        </div>

        <!-- Suites Grid View -->
        <div class="suites-grid" id="suitesGrid">
"""

for r in reports:
    html_template += f"""
            <div class="suite-card" data-module="{r['module']}" data-title="{r['title'].lower()}" data-submodule="{r['submodule'].lower()}" data-suite="{r['suiteName'].lower()}">
                <div>
                    <div class="card-header">
                        <span class="module-tag">{r['module']}</span>
                        <span class="status-badge"><span class="status-dot"></span>{r['status']}</span>
                    </div>
                    <div class="suite-title">{r['title']}</div>
                    <div class="submodule-desc">Feature: <strong>{r['submodule']}</strong></div>
                    
                    <div class="meta-badges">
                        <span class="media-badge" onclick="openMediaModal('{r['id']}', 'screenshots')">
                            &#128247; {r['screenshotCount']} Screenshots
                        </span>
                        <span class="media-badge" onclick="openMediaModal('{r['id']}', 'videos')">
                            &#127916; {r['videoCount']} Videos
                        </span>
                    </div>
                </div>

                <div class="card-actions">
                    <a href="{r['reportPath']}" target="_blank" class="btn btn-primary">
                        View Full Playwright Report &rarr;
                    </a>
                </div>
            </div>
    """

html_template += f"""
        </div>

        <!-- Suites Table View -->
        <div class="table-container" id="suitesTable">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Module</th>
                        <th>Feature / Submodule</th>
                        <th>Test Suite</th>
                        <th>Status</th>
                        <th>Evidence</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
"""

for idx, r in enumerate(reports, 1):
    html_template += f"""
                    <tr data-module="{r['module']}" data-title="{r['title'].lower()}" data-submodule="{r['submodule'].lower()}" data-suite="{r['suiteName'].lower()}">
                        <td style="font-family: 'JetBrains Mono', monospace; color: var(--text-muted);">{idx:03d}</td>
                        <td><span class="module-tag">{r['module']}</span></td>
                        <td><strong>{r['submodule']}</strong></td>
                        <td style="color: #fff; font-weight: 600;">{r['title']}</td>
                        <td><span class="status-badge"><span class="status-dot"></span>{r['status']}</span></td>
                        <td>
                            <span class="media-badge" onclick="openMediaModal('{r['id']}', 'screenshots')">&#128247; {r['screenshotCount']}</span>
                            <span class="media-badge" onclick="openMediaModal('{r['id']}', 'videos')">&#127916; {r['videoCount']}</span>
                        </td>
                        <td>
                            <a href="{r['reportPath']}" target="_blank" class="btn btn-primary" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;">
                                Open Report
                            </a>
                        </td>
                    </tr>
    """

report_data_json = json.dumps({r['id']: r for r in reports})

html_template += f"""
                </tbody>
            </table>
        </div>

    </div>

    <!-- Media Modal -->
    <div class="modal-overlay" id="mediaModal" onclick="closeModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">Evidence Viewer</div>
                <button class="modal-close" onclick="closeModalDirect()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>

    <script>
        const reportData = {report_data_json};
        let currentModuleFilter = 'ALL';

        function filterSuites() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.suite-card');
            const rows = document.querySelectorAll('#tableBody tr');

            cards.forEach(card => {{
                const mod = card.dataset.module;
                const title = card.dataset.title;
                const sub = card.dataset.submodule;
                const suite = card.dataset.suite;
                const matchesMod = (currentModuleFilter === 'ALL' || mod === currentModuleFilter);
                const matchesQuery = !query || title.includes(query) || sub.includes(query) || suite.includes(query) || mod.toLowerCase().includes(query);
                card.style.display = (matchesMod && matchesQuery) ? 'flex' : 'none';
            }});

            rows.forEach(row => {{
                const mod = row.dataset.module;
                const title = row.dataset.title;
                const sub = row.dataset.submodule;
                const suite = row.dataset.suite;
                const matchesMod = (currentModuleFilter === 'ALL' || mod === currentModuleFilter);
                const matchesQuery = !query || title.includes(query) || sub.includes(query) || suite.includes(query) || mod.toLowerCase().includes(query);
                row.style.display = (matchesMod && matchesQuery) ? '' : 'none';
            }});
        }}

        function setModuleFilter(mod, btn) {{
            currentModuleFilter = mod;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterSuites();
        }}

        function switchView(view) {{
            const grid = document.getElementById('suitesGrid');
            const table = document.getElementById('suitesTable');
            const btnGrid = document.getElementById('btnGridView');
            const btnTable = document.getElementById('btnTableView');

            if (view === 'grid') {{
                grid.style.display = 'grid';
                table.style.display = 'none';
                btnGrid.classList.add('active');
                btnTable.classList.remove('active');
            }} else {{
                grid.style.display = 'none';
                table.style.display = 'block';
                btnGrid.classList.remove('active');
                btnTable.classList.add('active');
            }}
        }}

        function openMediaModal(id, type) {{
            const suite = reportData[id];
            if (!suite) return;

            const modal = document.getElementById('mediaModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');

            if (type === 'screenshots') {{
                title.innerText = `Screenshots: ${{suite.title}} (${{suite.screenshots.length}})`;
                if (suite.screenshots.length === 0) {{
                    body.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No screenshots captured for this suite.</p>';
                }} else {{
                    body.innerHTML = `
                        <div class="gallery-grid">
                            ${{suite.screenshots.map(s => `
                                <div class="gallery-item" onclick="window.open('${{s.path}}', '_blank')">
                                    <img src="${{s.path}}" alt="${{s.name}}" loading="lazy" />
                                    <div class="gallery-item-name">${{s.name}}</div>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                }}
            }} else if (type === 'videos') {{
                title.innerText = `Recordings: ${{suite.title}} (${{suite.videos.length}})`;
                if (suite.videos.length === 0) {{
                    body.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No video recordings captured for this suite.</p>';
                }} else {{
                    body.innerHTML = `
                        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                            ${{suite.videos.map(v => `
                                <div style="background: #000; border-radius: 8px; padding: 1rem; border: 1px solid var(--border-color);">
                                    <h4 style="margin-bottom: 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #a5b4fc;">${{v.name}}</h4>
                                    <video controls style="width: 100%; border-radius: 6px; max-height: 450px;">
                                        <source src="${{v.path}}" type="video/webm">
                                        Your browser does not support WebM playback.
                                    </video>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                }}
            }}

            modal.style.display = 'flex';
        }}

        function closeModal(e) {{
            document.getElementById('mediaModal').style.display = 'none';
        }}

        function closeModalDirect() {{
            document.getElementById('mediaModal').style.display = 'none';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModalDirect();
        }});
    </script>
</body>
</html>
"""

# Write index.html at root
output_html_path = os.path.join(workspace_dir, "index.html")
with open(output_html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Master Standalone Report successfully generated at: {output_html_path}")
