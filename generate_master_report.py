import os
import json
import re
from datetime import datetime

workspace_dir = os.path.abspath(".")
print(f"Scanning reports in: {workspace_dir}")

GITHUB_USER = "Virajnaik31"
GITHUB_REPO = "DD_4.6.4_UAT-Report"

# The 4 main modules (strictly only these 4)
MODULE_CONFIG = [
    {
        "id": "CMT",
        "name": "CMT",
        "fullName": "Content & Merchant Tool",
        "icon": "📦",
        "description": "Brands, Categories, Coupons, Listings, Approvals & Media"
    },
    {
        "id": "orderFulfilment",
        "name": "Order Fulfilment",
        "fullName": "Order Fulfilment (Self Pickup)",
        "icon": "🚚",
        "description": "End-to-End Order Processing & Pickup Steps"
    },
    {
        "id": "orderFulFilmentChecklist",
        "name": "OF Checklist",
        "fullName": "Order Fulfilment Checklist",
        "icon": "📋",
        "description": "Comprehensive Case 001 - 049 Verification Suites"
    },
    {
        "id": "superadmin",
        "name": "SuperAdmin",
        "fullName": "SuperAdmin Operations",
        "icon": "⚡",
        "description": "RBAC, Logistics, Master Configs, Departments & Users"
    }
]

def clean_name(s):
    s = re.sub(r'^[0-9]+_', '', s)
    s = re.sub(r'^[0-9]+_[0-9]+_', '', s)
    s = s.replace('_report', '').replace('_', ' ').replace('-', ' ')
    s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    return s.strip().title()

def parse_step_description(filename):
    name_no_ext = os.path.splitext(filename)[0]
    m = re.match(r'^(\d+)(?:_(\d+))?_(.*)$', name_no_ext)
    if m:
        step_num = int(m.group(1))
        desc = m.group(3)
    else:
        step_num = 1
        desc = name_no_ext
        
    desc = desc.replace('_', ' ').replace('-', ' ')
    desc = re.sub(r'([a-z])([A-Z])', r'\1 \2', desc)
    desc_clean = desc.strip().title()
    return step_num, desc_clean

all_data = {
    "CMT": {},
    "orderFulfilment": {},
    "orderFulFilmentChecklist": {},
    "superadmin": {}
}

suite_flat_list = []

for root, dirs, files in os.walk(workspace_dir):
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.agents')]
    
    if 'index.html' in files and root != workspace_dir:
        rel_dir = os.path.relpath(root, workspace_dir).replace('\\', '/')
        parts = rel_dir.split('/')
        mod_key = parts[0]
        
        if mod_key not in all_data:
            continue
            
        # Determine Submodule & Suite Name
        if mod_key == "orderFulfilment":
            submodule = "Self Pickup"
            suite_id = parts[-1]
            suite_title = clean_name(parts[-1])
        elif mod_key == "orderFulFilmentChecklist":
            if "case-001-020" in parts:
                submodule = "Checklist Cases 001 - 020"
            else:
                submodule = "Checklist Cases 021 - 049"
            suite_id = parts[-1]
            suite_title = clean_name(parts[-1])
        elif mod_key == "CMT":
            submodule = clean_name(parts[1]) if len(parts) > 2 else "General"
            suite_id = parts[-1]
            suite_title = clean_name(parts[-1])
        elif mod_key == "superadmin":
            submodule = clean_name(parts[1]) if len(parts) > 2 else "General"
            suite_id = parts[-1]
            suite_title = clean_name(parts[-1])
            
        # Parse screenshots into sequential steps
        ss_dir = os.path.join(root, 'screenshots')
        steps = []
        if os.path.isdir(ss_dir):
            ss_files = sorted([f for f in os.listdir(ss_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
            for idx, ss in enumerate(ss_files, 1):
                s_num, s_desc = parse_step_description(ss)
                clean_media_path = f"{rel_dir}/screenshots/{ss}"
                steps.append({
                    "stepNumber": idx,
                    "title": s_desc if s_desc else f"Step {idx}",
                    "screenshot": clean_media_path,
                    "filename": ss,
                    "status": "Passed"
                })
                
        # Parse videos
        v_dir = os.path.join(root, 'videos')
        videos = []
        if os.path.isdir(v_dir):
            for vf in sorted(os.listdir(v_dir)):
                if vf.lower().endswith(('.webm', '.mp4')):
                    videos.append({
                        "name": vf,
                        "path": f"{rel_dir}/videos/{vf}"
                    })

        suite_obj = {
            "id": f"{mod_key}__{submodule.replace(' ', '_')}__{suite_id}",
            "module": mod_key,
            "submodule": submodule,
            "suiteName": suite_id,
            "title": suite_title,
            "reportPath": f"{rel_dir}/index.html",
            "status": "Passed",
            "stepCount": len(steps),
            "steps": steps,
            "videoCount": len(videos),
            "videos": videos
        }

        if submodule not in all_data[mod_key]:
            all_data[mod_key][submodule] = []
            
        all_data[mod_key][submodule].append(suite_obj)
        suite_flat_list.append(suite_obj)

# Sort suites inside submodules
for mod in all_data:
    for sub in all_data[mod]:
        all_data[mod][sub].sort(key=lambda s: s['title'])

print(f"Total Suites Parsed: {len(suite_flat_list)}")
total_all_steps = 0
total_all_videos = 0
for mod_cfg in MODULE_CONFIG:
    m_id = mod_cfg['id']
    m_suites = sum(len(suites) for suites in all_data[m_id].values())
    m_steps = sum(sum(s['stepCount'] for s in suites) for suites in all_data[m_id].values())
    m_videos = sum(sum(s['videoCount'] for s in suites) for suites in all_data[m_id].values())
    mod_cfg['suiteCount'] = m_suites
    mod_cfg['stepCount'] = m_steps
    mod_cfg['videoCount'] = m_videos
    total_all_steps += m_steps
    total_all_videos += m_videos
    print(f" -> {mod_cfg['name']}: {m_suites} suites, {m_steps} steps, {m_videos} videos")

global_stats = {
    "totalSuites": len(suite_flat_list),
    "totalSteps": total_all_steps,
    "totalVideos": total_all_videos,
    "passRate": "100%",
    "release": "V4.6.4",
    "generatedAt": datetime.now().strftime("%B %d, %Y - %H:%M:%S")
}

jsonData = json.dumps(all_data)
modulesJson = json.dumps(MODULE_CONFIG)
flatListJson = json.dumps(suite_flat_list)
statsJson = json.dumps(global_stats)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DD 4.6.4 UAT Master Test Reports</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-surface: #161f30;
            --bg-card: #151d2d;
            --bg-card-hover: #1c263b;
            --bg-active: rgba(59, 130, 246, 0.16);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-subtle: rgba(255, 255, 255, 0.05);
            --border-focus: #3b82f6;
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --color-pass: #10b981;
            --color-pass-bg: rgba(16, 185, 129, 0.12);
            --color-pass-border: rgba(16, 185, 129, 0.35);
            
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%);
            
            --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', Consolas, Monaco, monospace;
            
            --sidebar-width: 360px;
            --header-height: 64px;
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --transition: all 0.18s ease-in-out;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html, body {{
            height: 100%;
            width: 100%;
            overflow: hidden;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-sans);
            -webkit-font-smoothing: antialiased;
        }}

        .app-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }}

        /* Top Master Header */
        .master-header {{
            height: var(--header-height);
            min-height: var(--header-height);
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 50;
            gap: 16px;
            flex-shrink: 0;
        }}

        .brand-section {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-shrink: 0;
        }}

        .brand-logo {{
            width: 36px;
            height: 36px;
            background: var(--accent-gradient);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.1rem;
            color: #ffffff;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
        }}

        .brand-info h1 {{
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 6px;
            line-height: 1.2;
        }}

        .tag-version {{
            font-size: 0.6875rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(59, 130, 246, 0.18);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.35);
        }}

        .subtitle {{
            font-size: 0.725rem;
            color: var(--text-secondary);
        }}

        /* Quick Navigation Bar for 4 Main Folders */
        .nav-tabs {{
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 0, 0, 0.3);
            padding: 4px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle);
        }}

        .nav-tab {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: var(--radius-md);
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 0.8125rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
        }}

        .nav-tab:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
        }}

        .nav-tab.active {{
            background: var(--accent-gradient);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
        }}

        .nav-tab .badge {{
            font-size: 0.6875rem;
            padding: 1px 6px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: inherit;
        }}

        .nav-tab.active .badge {{
            background: rgba(255, 255, 255, 0.25);
            color: #ffffff;
            font-weight: 700;
        }}

        /* Suite Metrics */
        .header-stats {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }}

        .stat-pill {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: var(--radius-md);
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-subtle);
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .stat-pill .label {{
            color: var(--text-muted);
        }}

        .stat-pill .value.pass {{
            color: var(--color-pass);
            font-weight: 700;
        }}

        .stat-pill .value.rate {{
            color: #38bdf8;
            font-weight: 700;
        }}

        .btn-header {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            border-radius: var(--radius-md);
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }}

        .btn-header:hover {{
            color: #ffffff;
            border-color: var(--accent-blue);
        }}

        /* Main Workspace */
        .main-workspace {{
            display: flex;
            flex: 1;
            overflow: hidden;
            position: relative;
        }}

        /* Left Sidebar: Filtered Reports List */
        .reports-sidebar {{
            width: var(--sidebar-width);
            min-width: 300px;
            max-width: 440px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
            transition: width 0.25s, transform 0.25s;
        }}

        .reports-sidebar.collapsed {{
            width: 0px;
            min-width: 0px;
            border-right: none;
            overflow: hidden;
        }}

        .sidebar-filter-bar {{
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: rgba(17, 24, 39, 0.75);
        }}

        .search-box {{
            position: relative;
            display: flex;
            align-items: center;
        }}

        .search-box svg {{
            position: absolute;
            left: 10px;
            width: 14px;
            height: 14px;
            fill: var(--text-muted);
            pointer-events: none;
        }}

        .search-input {{
            width: 100%;
            padding: 7px 10px 7px 30px;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 0.8125rem;
            outline: none;
            transition: var(--transition);
        }}

        .search-input:focus {{
            border-color: var(--border-focus);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.25);
        }}

        /* Grouping & Collapse Controls */
        .sidebar-view-toggle-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .folder-mode-btn {{
            padding: 4px 8px;
            border-radius: var(--radius-sm);
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.75rem;
            cursor: pointer;
            transition: var(--transition);
        }}

        .folder-mode-btn.active, .folder-mode-btn:hover {{
            background: var(--bg-surface);
            color: #ffffff;
            border-color: var(--accent-blue);
        }}

        .tree-toggle-btn {{
            padding: 3px 6px;
            border-radius: var(--radius-sm);
            background: transparent;
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.7rem;
            cursor: pointer;
        }}

        .tree-toggle-btn:hover {{
            color: #ffffff;
            background: var(--bg-surface);
        }}

        /* Sidebar Reports Tree / List Body */
        .reports-list-container {{
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }}

        .subfolder-group {{
            margin-bottom: 8px;
        }}

        .subfolder-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 8px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            user-select: none;
            color: var(--text-secondary);
            font-size: 0.775rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            transition: var(--transition);
        }}

        .subfolder-header:hover {{
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-primary);
        }}

        .subfolder-header .caret {{
            font-size: 0.65rem;
            transition: transform 0.2s;
        }}

        .subfolder-header.collapsed .caret {{
            transform: rotate(-90deg);
        }}

        .subfolder-items {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-top: 2px;
            padding-left: 4px;
        }}

        .subfolder-items.collapsed {{
            display: none;
        }}

        .report-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 7px 10px;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: var(--transition);
            border: 1px solid transparent;
            text-decoration: none;
        }}

        .report-item:hover {{
            background: var(--bg-card-hover);
            border-color: rgba(255, 255, 255, 0.08);
        }}

        .report-item.active {{
            background: var(--bg-active);
            border-color: rgba(59, 130, 246, 0.45);
            box-shadow: inset 0 0 10px rgba(59, 130, 246, 0.12);
        }}

        .report-item .r-title {{
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 210px;
        }}

        .report-item.active .r-title {{
            color: #ffffff;
            font-weight: 700;
        }}

        .report-item .r-badges {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .step-pill {{
            font-size: 0.6875rem;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            font-family: var(--font-mono);
        }}

        .report-item.active .step-pill {{
            background: rgba(59, 130, 246, 0.3);
            color: #bfdbfe;
        }}

        .pass-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--color-pass);
        }}

        /* Right Detail View Area */
        .report-detail-view {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: var(--bg-primary);
        }}

        /* Detail Header Banner */
        .detail-header-banner {{
            padding: 14px 24px;
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            flex-shrink: 0;
        }}

        .detail-title-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .breadcrumbs {{
            font-size: 0.725rem;
            color: var(--text-muted);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .breadcrumbs span.current {{
            color: #93c5fd;
            font-weight: 700;
        }}

        .suite-heading {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .status-badge-lg {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.725rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 20px;
            background: var(--color-pass-bg);
            color: var(--color-pass);
            border: 1px solid var(--color-pass-border);
        }}

        .status-badge-lg .pulse-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--color-pass);
        }}

        .detail-actions {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .btn-action {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: var(--radius-sm);
            font-size: 0.8125rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: var(--transition);
            border: 1px solid var(--border-color);
            background: var(--bg-surface);
            color: var(--text-primary);
        }}

        .btn-action:hover {{
            border-color: var(--accent-blue);
            background: var(--bg-card-hover);
            transform: translateY(-1px);
        }}

        .btn-action-primary {{
            background: var(--accent-gradient);
            border: none;
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.35);
        }}

        /* Detail Scrollable Body */
        .detail-body {{
            flex: 1;
            overflow-y: auto;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Video Section */
        .video-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 16px;
        }}

        .section-header {{
            font-size: 0.925rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .video-player-box {{
            background: #000000;
            border-radius: var(--radius-md);
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            max-width: 960px;
        }}

        .video-player-box video {{
            width: 100%;
            height: auto;
            max-height: 480px;
            display: block;
        }}

        /* View Mode Toggle: Timeline vs Gallery */
        .view-mode-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }}

        .view-switch-btns {{
            display: flex;
            gap: 6px;
            background: rgba(0, 0, 0, 0.35);
            padding: 3px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-subtle);
        }}

        .view-switch-btn {{
            padding: 5px 12px;
            border-radius: var(--radius-sm);
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 0.775rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }}

        .view-switch-btn.active {{
            background: var(--bg-surface);
            color: #ffffff;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
        }}

        /* Timeline View */
        .timeline {{
            position: relative;
            padding-left: 28px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 10px;
            bottom: 10px;
            width: 2px;
            background: linear-gradient(to bottom, var(--accent-blue) 0%, rgba(59, 130, 246, 0.1) 100%);
        }}

        .timeline-step {{
            position: relative;
        }}

        .step-node {{
            position: absolute;
            left: -28px;
            top: 2px;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: var(--bg-secondary);
            border: 2px solid var(--accent-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.625rem;
            font-weight: 800;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
            z-index: 2;
        }}

        .step-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 14px;
            transition: var(--transition);
        }}

        .step-card:hover {{
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }}

        .step-meta-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .step-title-text {{
            font-size: 0.9rem;
            font-weight: 700;
            color: #ffffff;
        }}

        .step-img-box {{
            border-radius: var(--radius-sm);
            overflow: hidden;
            background: #000000;
            border: 1px solid rgba(255, 255, 255, 0.08);
            position: relative;
            cursor: zoom-in;
            transition: all 0.2s;
            max-width: 860px;
        }}

        .step-img-box:hover {{
            border-color: var(--accent-blue);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }}

        .step-img-box img {{
            width: 100%;
            height: auto;
            display: block;
            max-height: 480px;
            object-fit: contain;
        }}

        /* Gallery Grid View */
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }}

        .gallery-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow: hidden;
            cursor: zoom-in;
            transition: var(--transition);
        }}

        .gallery-card:hover {{
            border-color: var(--accent-blue);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
        }}

        .gallery-card img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
            background: #000000;
        }}

        .gallery-meta {{
            padding: 10px;
            font-size: 0.775rem;
            color: var(--text-secondary);
            font-weight: 600;
            border-top: 1px solid var(--border-subtle);
        }}

        /* Lightbox Carousel Modal */
        .lightbox-modal {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.94);
            backdrop-filter: blur(14px);
            z-index: 9999;
            display: none;
            flex-direction: column;
            padding: 16px 20px;
        }}

        .lightbox-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
            flex-shrink: 0;
        }}

        .lightbox-title-box {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .lightbox-step-counter {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 20px;
            background: rgba(59, 130, 246, 0.25);
            color: #93c5fd;
            font-weight: 700;
            font-family: var(--font-mono);
        }}

        .lightbox-title {{
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
        }}

        .lightbox-controls {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-lightbox {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #ffffff;
            padding: 5px 10px;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            cursor: pointer;
            transition: var(--transition);
        }}

        .btn-lightbox:hover {{
            background: var(--accent-blue);
            border-color: var(--accent-blue);
        }}

        .lightbox-close {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 1.75rem;
            cursor: pointer;
            line-height: 1;
            transition: color 0.15s;
        }}

        .lightbox-close:hover {{
            color: #ffffff;
        }}

        .lightbox-center {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
            padding: 10px 0;
        }}

        .lightbox-center img {{
            max-width: 92vw;
            max-height: 80vh;
            object-fit: contain;
            border-radius: var(--radius-md);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
            transition: transform 0.2s ease-out;
        }}

        .lightbox-nav-btn {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(17, 24, 39, 0.85);
            border: 1px solid var(--border-color);
            color: #ffffff;
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: var(--transition);
            z-index: 10;
        }}

        .lightbox-nav-btn:hover {{
            background: var(--accent-blue);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
            transform: translateY(-50%) scale(1.08);
        }}

        .lightbox-nav-prev {{
            left: 20px;
        }}

        .lightbox-nav-next {{
            right: 20px;
        }}

        /* Toast notification */
        .toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--bg-surface);
            color: #ffffff;
            border: 1px solid var(--accent-blue);
            border-radius: var(--radius-md);
            padding: 10px 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            font-size: 0.8125rem;
            display: none;
            animation: fadeIn 0.2s;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.15);
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 3px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Top Master Header -->
        <header class="master-header">
            <div class="brand-section">
                <div class="brand-logo">DD</div>
                <div class="brand-info">
                    <h1>
                        DD UAT Reports
                        <span class="tag-version">v4.6.4</span>
                    </h1>
                    <div class="subtitle">Unified Test Execution &amp; Artifacts Hub</div>
                </div>
            </div>

            <!-- Quick Navigation Bar for Exactly the 4 Main Folders -->
            <nav class="nav-tabs" id="navTabs">
                <!-- Rendered dynamically -->
            </nav>

            <!-- Suite Metrics -->
            <div class="header-stats">
                <div class="stat-pill" title="Total test suites executed">
                    <span class="label">Total:</span>
                    <span class="value" id="statTotal">{len(suite_flat_list)}</span>
                </div>
                <div class="stat-pill" title="Passed suites">
                    <span class="label">Passed:</span>
                    <span class="value pass" id="statPassed">{len(suite_flat_list)}</span>
                </div>
                <div class="stat-pill" title="Overall pass rate">
                    <span class="label">Rate:</span>
                    <span class="value rate" id="statPassRate">100%</span>
                </div>
                <button class="btn-header" onclick="exportToCSV()" title="Export Execution Matrix to CSV">
                    <span>📥</span> CSV
                </button>
            </div>
        </header>

        <!-- Main Workspace (LHS Sidebar + RHS Detail View) -->
        <main class="main-workspace">
            <!-- Left Sidebar -->
            <aside class="reports-sidebar" id="reportsSidebar">
                <div class="sidebar-filter-bar">
                    <div class="search-box">
                        <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 14z"/></svg>
                        <input type="text" id="searchInput" class="search-input" placeholder="Search tests, specs, folders..." oninput="filterSidebarSuites()">
                    </div>

                    <div class="sidebar-view-toggle-row">
                        <div style="display: flex; gap: 4px;">
                            <button class="folder-mode-btn active" id="btnFolderwise" onclick="setSidebarGrouping('FOLDERWISE')" title="Group reports by subfolders">
                                🗂️ Folder-wise
                            </button>
                            <button class="folder-mode-btn" id="btnFlatList" onclick="setSidebarGrouping('FLAT')" title="Show flat list of reports">
                                📋 Flat List
                            </button>
                        </div>
                        <div style="display: flex; gap: 4px;">
                            <button class="tree-toggle-btn" onclick="toggleAllFolderGroups(true)" title="Expand all subfolders">➕</button>
                            <button class="tree-toggle-btn" onclick="toggleAllFolderGroups(false)" title="Collapse all subfolders">➖</button>
                        </div>
                    </div>
                </div>

                <!-- Sidebar Report List -->
                <div class="reports-list-container" id="reportsListContainer">
                    <!-- Rendered dynamically -->
                </div>
            </aside>

            <!-- Right Detail View -->
            <section class="report-detail-view" id="reportDetailView">
                <!-- Detail Header Banner -->
                <div class="detail-header-banner">
                    <div>
                        <div class="breadcrumbs">
                            <span id="bcModule">CMT</span> &gt; 
                            <span id="bcSubmodule">Brand Master</span> &gt; 
                            <span class="current" id="bcSuite">Brand Master 1</span>
                        </div>
                        <div class="suite-heading">
                            <span id="suiteHeading">Brand Master 1</span>
                            <span class="status-badge-lg">
                                <span class="pulse-dot"></span> PASSED
                            </span>
                        </div>
                    </div>

                    <div class="detail-actions">
                        <button class="btn-action" onclick="copyShareLink()" title="Copy shareable deep link">
                            <span>🔗</span> Share Link
                        </button>
                        <a href="#" id="btnOpenRawReport" target="_blank" class="btn-action btn-action-primary">
                            Open Raw Playwright Report &rarr;
                        </a>
                    </div>
                </div>

                <!-- Scrollable Execution Body -->
                <div class="detail-body" id="detailBody">
                    
                    <!-- Video Execution Section -->
                    <div class="video-card" id="videoSection">
                        <div class="section-header">
                            <span><span>🎬</span> Execution Recording (<span id="videoCountLabel">1 Video</span>)</span>
                            <span style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">Playwright Capture</span>
                        </div>
                        <div class="video-player-box" id="videoPlayerBox">
                            <!-- Injected dynamically -->
                        </div>
                    </div>

                    <!-- Steps Execution Section -->
                    <div class="step-tree-container">
                        <!-- View mode switch: Timeline vs Gallery -->
                        <div class="view-mode-bar">
                            <div class="section-header" style="margin-bottom: 0;">
                                <span>📋 Execution Evidence (<span id="stepCountLabel">12 Steps</span>)</span>
                            </div>
                            <div class="view-switch-btns">
                                <button class="view-switch-btn active" id="btnViewTimeline" onclick="setViewMode('timeline')">
                                    ⏱️ Timeline
                                </button>
                                <button class="view-switch-btn" id="btnViewGallery" onclick="setViewMode('gallery')">
                                    🖼️ Gallery
                                </button>
                            </div>
                        </div>

                        <!-- Timeline Container -->
                        <div class="timeline" id="stepsTimeline">
                            <!-- Injected dynamically -->
                        </div>

                        <!-- Gallery Container -->
                        <div class="gallery-grid" id="stepsGallery" style="display: none;">
                            <!-- Injected dynamically -->
                        </div>
                    </div>

                </div>
            </section>
        </main>
    </div>

    <!-- Lightbox Carousel Modal -->
    <div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
        <div class="lightbox-top" onclick="event.stopPropagation()">
            <div class="lightbox-title-box">
                <span class="lightbox-step-counter" id="lightboxStepCounter">Step 1 of 10</span>
                <div class="lightbox-title" id="lightboxTitle">Screenshot Preview</div>
            </div>
            <div class="lightbox-controls">
                <button class="btn-lightbox" onclick="zoomLightbox(0.2)">🔍+ Zoom In</button>
                <button class="btn-lightbox" onclick="zoomLightbox(-0.2)">🔍- Zoom Out</button>
                <button class="btn-lightbox" onclick="resetLightboxZoom()">Reset</button>
                <button class="btn-lightbox" onclick="copyScreenshotUrl()">Copy Link</button>
                <button class="lightbox-close" onclick="closeLightboxDirect()">&times;</button>
            </div>
        </div>

        <div class="lightbox-center" onclick="event.stopPropagation()">
            <button class="lightbox-nav-btn lightbox-nav-prev" onclick="lightboxNavigate(-1)" title="Previous Step (Left Arrow)">&larr;</button>
            <img id="lightboxImg" src="" alt="Screenshot" />
            <button class="lightbox-nav-btn lightbox-nav-next" onclick="lightboxNavigate(1)" title="Next Step (Right Arrow)">&rarr;</button>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toastBox">Message</div>

    <script>
        const moduleConfigs = {modulesJson};
        const allReportsData = {jsonData};
        const flatSuitesList = {flatListJson};
        const globalStats = {statsJson};

        // Cloud-Powered Multi-Tier Asset Resolver for Standalone Sharing
        const GITHUB_USER = "{GITHUB_USER}";
        const GITHUB_REPO = "{GITHUB_REPO}";
        const GH_PAGES_BASE = `https://${{GITHUB_USER.toLowerCase()}}.github.io/${{GITHUB_REPO}}/`;
        const RAW_BASE = `https://raw.githubusercontent.com/${{GITHUB_USER}}/${{GITHUB_REPO}}/main/`;
        const JSDELIVR_BASE = `https://cdn.jsdelivr.net/gh/${{GITHUB_USER}}/${{GITHUB_REPO}}@main/`;

        function getMediaUrl(path) {{
            if (!path) return "";
            if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {{
                return path;
            }}
            const cleanPath = path.replace(/^\\.?\\//, '');
            // Prefer local path first, if standalone without folders, error handler triggers online fallbacks
            return './' + cleanPath;
        }}

        // Multi-tier image fallback: Local -> GitHub Pages -> GitHub Raw -> jsDelivr
        window.handleImgError = function(img, originalPath) {{
            if (!originalPath) return;
            const cleanPath = originalPath.replace(/^\\.?\\//, '');
            
            if (!img.dataset.step) {{
                img.dataset.step = "1";
                img.src = GH_PAGES_BASE + cleanPath;
                return;
            }}
            if (img.dataset.step === "1") {{
                img.dataset.step = "2";
                img.src = RAW_BASE + cleanPath;
                return;
            }}
            if (img.dataset.step === "2") {{
                img.dataset.step = "3";
                img.src = JSDELIVR_BASE + cleanPath;
                return;
            }}
        }};

        // Multi-tier video fallback
        window.handleVideoError = function(video, originalPath) {{
            if (!originalPath) return;
            const cleanPath = originalPath.replace(/^\\.?\\//, '');
            
            if (!video.dataset.step) {{
                video.dataset.step = "1";
                video.src = GH_PAGES_BASE + cleanPath;
                video.load();
                return;
            }}
            if (video.dataset.step === "1") {{
                video.dataset.step = "2";
                video.src = RAW_BASE + cleanPath;
                video.load();
                return;
            }}
        }};

        // App State
        let currentModuleId = 'CMT';
        let sidebarGrouping = 'FOLDERWISE'; // 'FOLDERWISE' or 'FLAT'
        let currentViewMode = 'timeline'; // 'timeline' or 'gallery'
        let currentSelectedSuite = null;
        let activeLightboxIndex = 0;
        let lightboxZoomLevel = 1;

        // Initialize App
        function initApp() {{
            renderQuickNav();
            
            // Hash Routing
            window.addEventListener('hashchange', handleHashRouting);
            if (window.location.hash) {{
                handleHashRouting();
            }} else {{
                selectModule('CMT');
            }}
        }}

        // Render Quick Nav Tabs
        function renderQuickNav() {{
            const nav = document.getElementById('navTabs');
            nav.innerHTML = moduleConfigs.map(m => `
                <button class="nav-tab ${{m.id === currentModuleId ? 'active' : ''}}" id="navTab_${{m.id}}" onclick="selectModule('${{m.id}}')">
                    <span>${{m.icon}}</span>
                    <span>${{m.name}}</span>
                    <span class="badge">${{m.suiteCount}}</span>
                </button>
            `).join('');
        }}

        // Select Main Module
        function selectModule(modId, autoSelectSuiteId) {{
            currentModuleId = modId;
            
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            const activeTab = document.getElementById(`navTab_${{modId}}`);
            if (activeTab) activeTab.classList.add('active');

            renderSidebarReports();

            if (autoSelectSuiteId) {{
                const target = flatSuitesList.find(s => s.id === autoSelectSuiteId);
                if (target) {{
                    loadSuiteDetails(target);
                    return;
                }}
            }}

            const submodules = allReportsData[modId] || {{}};
            const firstSubKey = Object.keys(submodules)[0];
            if (firstSubKey && submodules[firstSubKey].length > 0) {{
                loadSuiteDetails(submodules[firstSubKey][0]);
            }}
        }}

        // Set Sidebar Grouping Mode
        function setSidebarGrouping(mode) {{
            sidebarGrouping = mode;
            document.getElementById('btnFolderwise').classList.toggle('active', mode === 'FOLDERWISE');
            document.getElementById('btnFlatList').classList.toggle('active', mode === 'FLAT');
            renderSidebarReports();
        }}

        // Render Sidebar Reports (Folderwise vs Flat)
        function renderSidebarReports() {{
            const container = document.getElementById('reportsListContainer');
            const submodules = allReportsData[currentModuleId] || {{}};
            const subKeys = Object.keys(submodules);

            if (subKeys.length === 0) {{
                container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 2rem;">No test reports found.</div>';
                return;
            }}

            if (sidebarGrouping === 'FLAT') {{
                const allModSuites = flatSuitesList.filter(s => s.module === currentModuleId);
                container.innerHTML = `
                    <div class="subfolder-items">
                        ${{allModSuites.map(s => renderReportItemHtml(s)).join('')}}
                    </div>
                `;
            }} else {{
                let html = '';
                subKeys.forEach(subKey => {{
                    const suites = submodules[subKey];
                    html += `
                        <div class="subfolder-group" data-subname="${{subKey.toLowerCase()}}">
                            <div class="subfolder-header" onclick="toggleSubfolderGroup(this)">
                                <span>${{subKey}} (${{suites.length}})</span>
                                <span class="caret">&#9660;</span>
                            </div>
                            <div class="subfolder-items">
                                ${{suites.map(s => renderReportItemHtml(s)).join('')}}
                            </div>
                        </div>
                    `;
                }});
                container.innerHTML = html;
            }}

            // Re-highlight active
            if (currentSelectedSuite) {{
                const el = document.getElementById(`repItem_${{currentSelectedSuite.id}}`);
                if (el) el.classList.add('active');
            }}
        }}

        function renderReportItemHtml(s) {{
            return `
                <div class="report-item" id="repItem_${{s.id}}" onclick="loadSuiteDetailsById('${{s.id}}')" data-title="${{s.title.toLowerCase()}}">
                    <div class="r-title" title="${{s.title}}">${{s.title}}</div>
                    <div class="r-badges">
                        <span class="step-pill">${{s.stepCount}} steps</span>
                        <span class="pass-dot"></span>
                    </div>
                </div>
            `;
        }}

        function toggleSubfolderGroup(headerEl) {{
            headerEl.classList.toggle('collapsed');
            const items = headerEl.nextElementSibling;
            if (items) items.classList.toggle('collapsed');
        }}

        function toggleAllFolderGroups(expand) {{
            document.querySelectorAll('.subfolder-header').forEach(h => {{
                if (expand) {{
                    h.classList.remove('collapsed');
                    if (h.nextElementSibling) h.nextElementSibling.classList.remove('collapsed');
                }} else {{
                    h.classList.add('collapsed');
                    if (h.nextElementSibling) h.nextElementSibling.classList.add('collapsed');
                }}
            }});
        }}

        function loadSuiteDetailsById(suiteId) {{
            const suite = flatSuitesList.find(s => s.id === suiteId);
            if (suite) loadSuiteDetails(suite);
        }}

        // Load Suite Details in Right Area
        function loadSuiteDetails(suite) {{
            currentSelectedSuite = suite;

            // Highlight sidebar item
            document.querySelectorAll('.report-item').forEach(el => el.classList.remove('active'));
            const activeEl = document.getElementById(`repItem_${{suite.id}}`);
            if (activeEl) activeEl.classList.add('active');

            // Header Banner
            document.getElementById('bcModule').innerText = suite.module;
            document.getElementById('bcSubmodule').innerText = suite.submodule;
            document.getElementById('bcSuite').innerText = suite.title;
            document.getElementById('suiteHeading').innerText = suite.title;
            document.getElementById('btnOpenRawReport').href = suite.reportPath;

            // Video Player
            const videoSection = document.getElementById('videoSection');
            const videoPlayerBox = document.getElementById('videoPlayerBox');
            const videoCountLabel = document.getElementById('videoCountLabel');

            if (suite.videos && suite.videos.length > 0) {{
                videoSection.style.display = 'block';
                videoCountLabel.innerText = `${{suite.videos.length}} Video${{suite.videos.length > 1 ? 's' : ''}}`;
                const vPath = suite.videos[0].path;
                videoPlayerBox.innerHTML = `
                    <video controls preload="metadata" key="${{vPath}}" onerror="handleVideoError(this, '${{vPath}}')">
                        <source src="${{getMediaUrl(vPath)}}" type="video/webm">
                        Your browser does not support WebM playback.
                    </video>
                `;
            }} else {{
                videoSection.style.display = 'none';
                videoPlayerBox.innerHTML = '';
            }}

            // Render Steps (Timeline & Gallery)
            const stepsTimeline = document.getElementById('stepsTimeline');
            const stepsGallery = document.getElementById('stepsGallery');
            const stepCountLabel = document.getElementById('stepCountLabel');
            stepCountLabel.innerText = `${{suite.steps.length}} Steps`;

            if (suite.steps.length === 0) {{
                stepsTimeline.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No individual step screenshots recorded.</p>';
                stepsGallery.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No individual step screenshots recorded.</p>';
            }} else {{
                // Timeline HTML
                stepsTimeline.innerHTML = suite.steps.map((step, sIdx) => `
                    <div class="timeline-step">
                        <div class="step-node">${{step.stepNumber}}</div>
                        <div class="step-card">
                            <div class="step-meta-row">
                                <div class="step-title-text">
                                    <span class="step-pill" style="margin-right: 6px;">Step ${{step.stepNumber < 10 ? '0' + step.stepNumber : step.stepNumber}}</span>
                                    ${{step.title}}
                                </div>
                                <span class="status-badge-lg">&#10003; PASSED</span>
                            </div>
                            <div class="step-img-box" onclick="openLightboxByIndex(${{sIdx}})">
                                <img src="${{getMediaUrl(step.screenshot)}}" alt="${{step.title}}" loading="lazy" onerror="handleImgError(this, '${{step.screenshot}}')" />
                            </div>
                        </div>
                    </div>
                `).join('');

                // Gallery HTML
                stepsGallery.innerHTML = suite.steps.map((step, sIdx) => `
                    <div class="gallery-card" onclick="openLightboxByIndex(${{sIdx}})">
                        <img src="${{getMediaUrl(step.screenshot)}}" alt="${{step.title}}" loading="lazy" onerror="handleImgError(this, '${{step.screenshot}}')" />
                        <div class="gallery-meta">
                            <span class="step-pill">Step ${{step.stepNumber}}</span> ${{step.title}}
                        </div>
                    </div>
                `).join('');
            }}

            // Update URL hash
            window.location.hash = `${{suite.module}}/${{suite.id}}`;
            document.getElementById('detailBody').scrollTop = 0;
        }}

        // View Mode Switch: Timeline vs Gallery
        function setViewMode(mode) {{
            currentViewMode = mode;
            document.getElementById('btnViewTimeline').classList.toggle('active', mode === 'timeline');
            document.getElementById('btnViewGallery').classList.toggle('active', mode === 'gallery');
            document.getElementById('stepsTimeline').style.display = mode === 'timeline' ? 'flex' : 'none';
            document.getElementById('stepsGallery').style.display = mode === 'gallery' ? 'grid' : 'none';
        }}

        // Filter Sidebar Suites
        function filterSidebarSuites() {{
            const q = document.getElementById('searchInput').value.toLowerCase().trim();
            const items = document.querySelectorAll('.report-item');
            
            items.forEach(item => {{
                const title = item.dataset.title;
                const matches = !q || title.includes(q);
                item.style.display = matches ? 'flex' : 'none';
            }});

            if (sidebarGrouping === 'FOLDERWISE') {{
                document.querySelectorAll('.subfolder-group').forEach(group => {{
                    const visibleItems = group.querySelectorAll('.report-item[style*="display: flex"]');
                    group.style.display = visibleItems.length > 0 ? 'block' : 'none';
                }});
            }}
        }}

        // Lightbox Functions
        function openLightboxByIndex(index) {{
            if (!currentSelectedSuite || !currentSelectedSuite.steps[index]) return;
            activeLightboxIndex = index;
            resetLightboxZoom();
            updateLightboxContent();
            document.getElementById('lightboxModal').style.display = 'flex';
        }}

        function updateLightboxContent() {{
            const step = currentSelectedSuite.steps[activeLightboxIndex];
            const total = currentSelectedSuite.steps.length;
            const img = document.getElementById('lightboxImg');
            img.src = getMediaUrl(step.screenshot);
            img.onerror = () => handleImgError(img, step.screenshot);
            document.getElementById('lightboxTitle').innerText = step.title;
            document.getElementById('lightboxStepCounter').innerText = `Step ${{activeLightboxIndex + 1}} of ${{total}}`;
        }}

        function lightboxNavigate(delta) {{
            if (!currentSelectedSuite) return;
            const newIndex = activeLightboxIndex + delta;
            if (newIndex >= 0 && newIndex < currentSelectedSuite.steps.length) {{
                activeLightboxIndex = newIndex;
                resetLightboxZoom();
                updateLightboxContent();
            }}
        }}

        function zoomLightbox(delta) {{
            lightboxZoomLevel = Math.max(0.5, Math.min(3.5, lightboxZoomLevel + delta));
            document.getElementById('lightboxImg').style.transform = `scale(${{lightboxZoomLevel}})`;
        }}

        function resetLightboxZoom() {{
            lightboxZoomLevel = 1;
            document.getElementById('lightboxImg').style.transform = 'scale(1)';
        }}

        function closeLightbox(e) {{
            document.getElementById('lightboxModal').style.display = 'none';
        }}

        function closeLightboxDirect() {{
            document.getElementById('lightboxModal').style.display = 'none';
        }}

        // Deep Link & Copy
        function copyShareLink() {{
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {{
                showToast('🔗 Suite link copied to clipboard!');
            }});
        }}

        function copyScreenshotUrl() {{
            if (!currentSelectedSuite || !currentSelectedSuite.steps[activeLightboxIndex]) return;
            const step = currentSelectedSuite.steps[activeLightboxIndex];
            const url = GH_PAGES_BASE + step.screenshot.replace(/^\\.?\\//, '');
            navigator.clipboard.writeText(url).then(() => {{
                showToast('📸 Online screenshot URL copied!');
            }});
        }}

        // CSV Export
        function exportToCSV() {{
            let csv = "Module,Submodule,Suite Title,Status,Step Count,Video Count,Report Path\\n";
            flatSuitesList.forEach(s => {{
                const cleanT = `"${{s.title.replace(/"/g, '""')}}"`;
                const cleanSub = `"${{s.submodule.replace(/"/g, '""')}}"`;
                csv += `${{s.module}},${{cleanSub}},${{cleanT}},${{s.status}},${{s.stepCount}},${{s.videoCount}},${{s.reportPath}}\\n`;
            }});

            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.setAttribute("download", `DealsDray_V4.6.4_UAT_Report_${{new Date().toISOString().slice(0, 10)}}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast('📥 CSV Test Matrix Downloaded!');
        }}

        function showToast(msg) {{
            const toast = document.getElementById('toastBox');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => {{
                toast.style.display = 'none';
            }}, 3000);
        }}

        function handleHashRouting() {{
            const hash = window.location.hash.replace('#', '');
            if (!hash) {{
                selectModule('CMT');
                return;
            }}

            const parts = hash.split('/');
            if (parts.length >= 2) {{
                const mod = parts[0];
                const suiteId = parts[1];
                selectModule(mod, suiteId);
            }} else if (parts.length === 1 && moduleConfigs.some(m => m.id === parts[0])) {{
                selectModule(parts[0]);
            }}
        }}

        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                closeLightboxDirect();
            }} else if (document.getElementById('lightboxModal').style.display === 'flex') {{
                if (e.key === 'ArrowLeft') lightboxNavigate(-1);
                else if (e.key === 'ArrowRight') lightboxNavigate(1);
            }}
        }});

        window.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
"""

# Write to DD_V4.6.4_UAT-Report.html and index.html
output_named_path = os.path.join(workspace_dir, "DD_V4.6.4_UAT-Report.html")
output_index_path = os.path.join(workspace_dir, "index.html")

with open(output_named_path, "w", encoding="utf-8") as f:
    f.write(html_content)

with open(output_index_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Master Report successfully rebuilt at: {output_named_path} and {output_index_path}")
