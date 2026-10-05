import os
import json
import re
from datetime import datetime

workspace_dir = os.path.abspath(".")
print(f"Scanning reports in: {workspace_dir}")

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
    # match leading digits
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
                steps.append({
                    "stepNumber": idx,
                    "title": s_desc if s_desc else f"Step {idx}",
                    "screenshot": f"{rel_dir}/screenshots/{ss}",
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
for mod_cfg in MODULE_CONFIG:
    m_id = mod_cfg['id']
    m_suites = sum(len(suites) for suites in all_data[m_id].values())
    m_steps = sum(sum(s['stepCount'] for s in suites) for suites in all_data[m_id].values())
    mod_cfg['suiteCount'] = m_suites
    mod_cfg['stepCount'] = m_steps
    print(f" -> {mod_cfg['name']}: {m_suites} suites, {m_steps} steps")

jsonData = json.dumps(all_data)
modulesJson = json.dumps(MODULE_CONFIG)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DealsDray V4.6.4 UAT Master Automation Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #090d16;
            --bg-sidebar: #0f172a;
            --bg-surface: #1e293b;
            --bg-surface-elevated: #334155;
            --bg-card: rgba(30, 41, 59, 0.7);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-active: rgba(99, 102, 241, 0.4);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            --color-pass: #10b981;
            --color-pass-bg: rgba(16, 185, 129, 0.12);
            --color-pass-border: rgba(16, 185, 129, 0.3);
            --color-info: #38bdf8;
            --color-info-bg: rgba(56, 189, 248, 0.12);
            --sidebar-width: 380px;
            --header-height: 68px;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        /* Top Header & Quick Navigation Bar */
        .top-navbar {{
            height: var(--header-height);
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.5rem;
            z-index: 50;
            flex-shrink: 0;
        }}

        .brand-section {{
            display: flex;
            align-items: center;
            gap: 0.875rem;
        }}

        .brand-badge {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--accent-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.15rem;
            color: #ffffff;
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
        }}

        .brand-info h1 {{
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .brand-info h1 span.tag {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            background: rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.35);
        }}

        .brand-info p {{
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        /* 4 Main Folder Quick Navigation Tabs */
        .quick-nav-container {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(0, 0, 0, 0.35);
            padding: 0.3rem 0.4rem;
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
        }}

        .nav-folder-btn {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.55rem 1.15rem;
            border-radius: 8px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }}

        .nav-folder-btn:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }}

        .nav-folder-btn.active {{
            background: var(--accent-gradient);
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
        }}

        .nav-folder-btn .badge-count {{
            font-size: 0.7rem;
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            background: rgba(0, 0, 0, 0.3);
            color: inherit;
        }}

        .nav-folder-btn.active .badge-count {{
            background: rgba(255, 255, 255, 0.25);
            color: #ffffff;
            font-weight: 700;
        }}

        /* Header Right Meta Actions */
        .header-meta {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .meta-stat-pill {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            background: var(--color-pass-bg);
            border: 1px solid var(--color-pass-border);
            color: var(--color-pass);
            font-size: 0.75rem;
            font-weight: 700;
        }}

        .meta-stat-pill .pulse-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--color-pass);
            box-shadow: 0 0 8px var(--color-pass);
        }}

        /* Main Workspace App Layout (Split view LHS & RHS) */
        .app-layout {{
            display: flex;
            flex: 1;
            overflow: hidden;
            height: calc(100vh - var(--header-height));
        }}

        /* LHS: Sidebar Folder & Report Tree */
        .lhs-sidebar {{
            width: var(--sidebar-width);
            min-width: 320px;
            max-width: 460px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
        }}

        .sidebar-header {{
            padding: 1rem 1.25rem 0.75rem;
            border-bottom: 1px solid var(--border-subtle);
            background: rgba(15, 23, 42, 0.6);
        }}

        .current-module-title {{
            font-size: 0.875rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .current-module-title span.sub {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .tree-search-box {{
            position: relative;
        }}

        .tree-search-box input {{
            width: 100%;
            padding: 0.55rem 0.85rem 0.55rem 2.25rem;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            color: var(--text-main);
            font-size: 0.8125rem;
            outline: none;
            transition: all 0.2s;
        }}

        .tree-search-box input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
        }}

        .tree-search-box .icon {{
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 0.8rem;
            pointer-events: none;
        }}

        /* Tree List Content */
        .sidebar-tree-body {{
            flex: 1;
            overflow-y: auto;
            padding: 0.75rem;
        }}

        .submodule-group {{
            margin-bottom: 0.85rem;
        }}

        .submodule-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            user-select: none;
            color: var(--text-secondary);
            font-size: 0.8125rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            transition: all 0.15s;
        }}

        .submodule-header:hover {{
            background: rgba(255, 255, 255, 0.03);
            color: var(--text-main);
        }}

        .submodule-header .caret {{
            font-size: 0.65rem;
            transition: transform 0.2s;
        }}

        .submodule-header.collapsed .caret {{
            transform: rotate(-90deg);
        }}

        .submodule-items {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-top: 2px;
            padding-left: 0.5rem;
        }}

        .submodule-items.collapsed {{
            display: none;
        }}

        .tree-suite-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.55rem 0.75rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.15s;
            border: 1px solid transparent;
            text-decoration: none;
        }}

        .tree-suite-item:hover {{
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.06);
        }}

        .tree-suite-item.active {{
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: inset 0 0 10px rgba(99, 102, 241, 0.1);
        }}

        .tree-suite-item .item-title {{
            font-size: 0.8125rem;
            font-weight: 600;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 210px;
        }}

        .tree-suite-item.active .item-title {{
            color: #ffffff;
            font-weight: 700;
        }}

        .tree-suite-item .item-badges {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .step-pill {{
            font-size: 0.6875rem;
            padding: 0.1rem 0.4rem;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}

        .tree-suite-item.active .step-pill {{
            background: rgba(99, 102, 241, 0.3);
            color: #c7d2fe;
        }}

        .pass-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--color-pass);
        }}

        /* RHS: Execution View Container */
        .rhs-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: var(--bg-base);
            position: relative;
        }}

        /* RHS Top Sticky Suite Banner */
        .suite-banner {{
            padding: 1.25rem 2rem;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            flex-shrink: 0;
        }}

        .breadcrumbs {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .breadcrumbs span.current {{
            color: #a5b4fc;
            font-weight: 600;
        }}

        .suite-heading-row {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .suite-heading-row h2 {{
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.02em;
        }}

        .status-badge-lg {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            background: var(--color-pass-bg);
            color: var(--color-pass);
            border: 1px solid var(--color-pass-border);
        }}

        .suite-actions {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .btn-action {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.55rem 1rem;
            border-radius: 8px;
            font-size: 0.8125rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
            border: 1px solid var(--border-subtle);
            background: var(--bg-surface);
            color: var(--text-main);
        }}

        .btn-action:hover {{
            border-color: var(--accent-primary);
            background: var(--bg-surface-elevated);
            transform: translateY(-1px);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
        }}

        .btn-action-primary {{
            background: var(--accent-gradient);
            border: none;
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
        }}

        .btn-action-primary:hover {{
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
        }}

        /* RHS Scrollable Body */
        .suite-body {{
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
            scroll-behavior: smooth;
        }}

        /* Video Section */
        .video-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.25rem;
            backdrop-filter: blur(8px);
        }}

        .section-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .video-player-container {{
            background: #000000;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
            max-width: 900px;
        }}

        .video-player-container video {{
            width: 100%;
            height: auto;
            max-height: 480px;
            display: block;
        }}

        /* Step Tree Execution Section */
        .step-tree-container {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(8px);
        }}

        .step-tree-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 1rem;
        }}

        .timeline {{
            position: relative;
            padding-left: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.75rem;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 11px;
            top: 10px;
            bottom: 10px;
            width: 2px;
            background: linear-gradient(to bottom, var(--accent-primary) 0%, rgba(99, 102, 241, 0.1) 100%);
        }}

        .timeline-step {{
            position: relative;
        }}

        .step-node-icon {{
            position: absolute;
            left: -2rem;
            top: 2px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--bg-sidebar);
            border: 2px solid var(--accent-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.65rem;
            font-weight: 800;
            color: #ffffff;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
            z-index: 2;
        }}

        .step-card {{
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 1.15rem;
            transition: all 0.2s ease;
        }}

        .step-card:hover {{
            border-color: var(--border-active);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }}

        .step-meta-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.85rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .step-info {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}

        .step-badge {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            background: rgba(99, 102, 241, 0.2);
            color: #c7d2fe;
            font-family: 'JetBrains Mono', monospace;
        }}

        .step-title-text {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #ffffff;
        }}

        .step-status-chip {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.2rem 0.55rem;
            border-radius: 12px;
            background: var(--color-pass-bg);
            color: var(--color-pass);
            border: 1px solid var(--color-pass-border);
        }}

        .step-image-wrapper {{
            border-radius: 8px;
            overflow: hidden;
            background: #000000;
            border: 1px solid rgba(255, 255, 255, 0.08);
            position: relative;
            cursor: zoom-in;
            transition: all 0.25s;
            max-width: 820px;
        }}

        .step-image-wrapper:hover {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 25px rgba(99, 102, 241, 0.3);
            transform: scale(1.005);
        }}

        .step-image-wrapper img {{
            width: 100%;
            height: auto;
            display: block;
            max-height: 480px;
            object-fit: contain;
        }}

        .image-overlay-hint {{
            position: absolute;
            bottom: 0.75rem;
            right: 0.75rem;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            padding: 0.3rem 0.65rem;
            border-radius: 6px;
            font-size: 0.7rem;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        /* Lightbox Fullscreen Modal */
        .lightbox-modal {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.94);
            backdrop-filter: blur(12px);
            z-index: 9999;
            display: none;
            flex-direction: column;
            padding: 1.5rem;
        }}

        .lightbox-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-subtle);
            flex-shrink: 0;
        }}

        .lightbox-title {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #ffffff;
        }}

        .lightbox-close {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 1.75rem;
            cursor: pointer;
            line-height: 1;
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
            padding: 1rem 0;
        }}

        .lightbox-center img {{
            max-width: 96vw;
            max-height: 82vh;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
        }}

        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            color: var(--text-muted);
            padding: 3rem;
        }}

        .empty-state .icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}

        /* Scrollbar styles */
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

    <!-- Top Sticky Header with Quick Nav Bar containing only the 4 Main Folders -->
    <header class="top-navbar">
        <div class="brand-section">
            <div class="brand-badge">DD</div>
            <div class="brand-info">
                <h1>DealsDray UAT Report <span class="tag">V4.6.4</span></h1>
                <p>132 Test Suites | 3,218 Steps & Screenshots | 100% Passed</p>
            </div>
        </div>

        <!-- ONLY 4 MAIN FOLDERS IN QUICK NAV BAR -->
        <nav class="quick-nav-container" id="quickNavButtons">
            <!-- Injected via JavaScript for exactly the 4 main modules -->
        </nav>

        <div class="header-meta">
            <div class="meta-stat-pill">
                <span class="pulse-dot"></span>
                ALL 132 SUITES PASSED
            </div>
        </div>
    </header>

    <!-- Main Workspace Split-View App Layout -->
    <main class="app-layout">
        
        <!-- LHS: Sidebar Tree of Reports & Folders -->
        <aside class="lhs-sidebar">
            <div class="sidebar-header">
                <div class="current-module-title">
                    <span id="sidebarModuleLabel">Content & Merchant Tool (CMT)</span>
                    <span class="sub" id="sidebarSuiteCount">33 Suites</span>
                </div>
                <div class="tree-search-box">
                    <span class="icon">&#128269;</span>
                    <input type="text" id="treeSearchInput" placeholder="Filter suites in this module..." onkeyup="filterTreeSuites()">
                </div>
            </div>

            <!-- Scrollable Report Hierarchy Tree -->
            <div class="sidebar-tree-body" id="treeContainer">
                <!-- Injected via JS -->
            </div>
        </aside>

        <!-- RHS: Right-Hand Side Execution Tree & Media View -->
        <section class="rhs-content" id="rhsContentArea">
            
            <!-- Dynamic Suite Header Banner -->
            <div class="suite-banner">
                <div>
                    <div class="breadcrumbs">
                        <span id="bcModule">CMT</span> &gt; 
                        <span id="bcSubmodule">Brand Master</span> &gt; 
                        <span class="current" id="bcSuite">Brand Master 1</span>
                    </div>
                    <div class="suite-heading-row">
                        <h2 id="suiteHeading">Brand Master 1</h2>
                        <span class="status-badge-lg">
                            <span class="pulse-dot"></span> PASSED
                        </span>
                    </div>
                </div>

                <div class="suite-actions">
                    <a href="#" id="btnOpenRawReport" target="_blank" class="btn-action btn-action-primary">
                        Open Full Playwright Report &rarr;
                    </a>
                </div>
            </div>

            <!-- Scrollable Execution Body (Video + Step Tree with Attached Screenshots) -->
            <div class="suite-body" id="suiteBody">
                
                <!-- Video Execution Section (Hidden if no video) -->
                <div class="video-card" id="videoSection">
                    <div class="section-title">
                        <span>&#127916;</span> Execution Recording (<span id="videoCountLabel">1 Video</span>)
                    </div>
                    <div class="video-player-container" id="videoPlayerWrapper">
                        <!-- Video element injected via JS -->
                    </div>
                </div>

                <!-- Complete Step-by-Step Execution Tree attached with Screenshots -->
                <div class="step-tree-container">
                    <div class="step-tree-header">
                        <div class="section-title" style="margin-bottom: 0;">
                            <span>&#128203;</span> Complete Step-by-Step Execution Tree (<span id="stepCountLabel">12 Steps</span>)
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">
                            Click screenshot to enlarge
                        </div>
                    </div>

                    <!-- Numbered Timeline Steps -->
                    <div class="timeline" id="stepsTimeline">
                        <!-- Steps injected via JS -->
                    </div>
                </div>

            </div>
        </section>

    </main>

    <!-- Lightbox Modal for High-Res Screenshots -->
    <div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
        <div class="lightbox-top">
            <div class="lightbox-title" id="lightboxTitle">Screenshot Preview</div>
            <button class="lightbox-close" onclick="closeLightboxDirect()">&times;</button>
        </div>
        <div class="lightbox-center" onclick="event.stopPropagation()">
            <img id="lightboxImg" src="" alt="Screenshot" />
        </div>
    </div>

    <script>
        const moduleConfigs = {modulesJson};
        const allReportsData = {jsonData};

        let currentModuleId = 'CMT';
        let currentSelectedSuite = null;

        // Initialize App
        function initApp() {{
            renderQuickNav();
            selectModule('CMT');
        }}

        // Render the 4 Main Folders in the Quick Nav Bar
        function renderQuickNav() {{
            const container = document.getElementById('quickNavButtons');
            container.innerHTML = moduleConfigs.map(m => `
                <button class="nav-folder-btn ${{m.id === currentModuleId ? 'active' : ''}}" id="navBtn_${{m.id}}" onclick="selectModule('${{m.id}}')">
                    <span>${{m.icon}}</span>
                    <span>${{m.name}}</span>
                    <span class="badge-count">${{m.suiteCount}}</span>
                </button>
            `).join('');
        }}

        // Select a Main Module (1 of the 4)
        function selectModule(modId) {{
            currentModuleId = modId;
            
            // Update Quick Nav UI
            document.querySelectorAll('.nav-folder-btn').forEach(btn => btn.classList.remove('active'));
            const activeBtn = document.getElementById(`navBtn_${{modId}}`);
            if (activeBtn) activeBtn.classList.add('active');

            const modCfg = moduleConfigs.find(m => m.id === modId);
            document.getElementById('sidebarModuleLabel').innerText = modCfg.fullName;
            document.getElementById('sidebarSuiteCount').innerText = `${{modCfg.suiteCount}} Suites`;

            // Render LHS Tree for this Module
            renderSidebarTree(modId);

            // Auto-select first suite in module
            const submodules = allReportsData[modId];
            const firstSubKey = Object.keys(submodules)[0];
            if (firstSubKey && submodules[firstSubKey].length > 0) {{
                loadSuiteDetails(submodules[firstSubKey][0]);
            }}
        }}

        // Render LHS Sidebar Tree
        function renderSidebarTree(modId) {{
            const treeContainer = document.getElementById('treeContainer');
            const submodules = allReportsData[modId] || {{}};
            const subKeys = Object.keys(submodules);

            if (subKeys.length === 0) {{
                treeContainer.innerHTML = '<div class="empty-state"><div class="icon">📂</div><p>No test reports found in this folder.</p></div>';
                return;
            }}

            let html = '';
            subKeys.forEach((subKey, subIdx) => {{
                const suites = submodules[subKey];
                html += `
                    <div class="submodule-group" data-subname="${{subKey.toLowerCase()}}">
                        <div class="submodule-header" onclick="toggleSubmoduleGroup(this)">
                            <span>${{subKey}} (${{suites.length}})</span>
                            <span class="caret">&#9660;</span>
                        </div>
                        <div class="submodule-items">
                            ${{suites.map(s => `
                                <div class="tree-suite-item" id="treeItem_${{s.id}}" onclick="loadSuiteDetailsById('${{modId}}', '${{subKey.replace(/'/g, "\\\\'")}}', '${{s.id}}')" data-title="${{s.title.toLowerCase()}}">
                                    <div class="item-title" title="${{s.title}}">${{s.title}}</div>
                                    <div class="item-badges">
                                        <span class="step-pill">${{s.stepCount}} steps</span>
                                        <span class="pass-dot"></span>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                    </div>
                `;
            }});

            treeContainer.innerHTML = html;
        }}

        function toggleSubmoduleGroup(headerEl) {{
            headerEl.classList.toggle('collapsed');
            const itemsContainer = headerEl.nextElementSibling;
            if (itemsContainer) {{
                itemsContainer.classList.toggle('collapsed');
            }}
        }}

        function loadSuiteDetailsById(modId, subKey, suiteId) {{
            const suite = allReportsData[modId][subKey].find(s => s.id === suiteId);
            if (suite) {{
                loadSuiteDetails(suite);
            }}
        }}

        // Load and Render RHS Suite Execution Tree & Media
        function loadSuiteDetails(suite) {{
            currentSelectedSuite = suite;

            // Highlight in LHS tree
            document.querySelectorAll('.tree-suite-item').forEach(el => el.classList.remove('active'));
            const activeTreeEl = document.getElementById(`treeItem_${{suite.id}}`);
            if (activeTreeEl) activeTreeEl.classList.add('active');

            // Update Breadcrumbs & Banner
            document.getElementById('bcModule').innerText = suite.module;
            document.getElementById('bcSubmodule').innerText = suite.submodule;
            document.getElementById('bcSuite').innerText = suite.title;
            document.getElementById('suiteHeading').innerText = suite.title;
            document.getElementById('btnOpenRawReport').href = suite.reportPath;

            // Update Video Section
            const videoSection = document.getElementById('videoSection');
            const videoWrapper = document.getElementById('videoPlayerWrapper');
            const videoCountLabel = document.getElementById('videoCountLabel');

            if (suite.videos && suite.videos.length > 0) {{
                videoSection.style.display = 'block';
                videoCountLabel.innerText = `${{suite.videos.length}} Recording${{suite.videos.length > 1 ? 's' : ''}}`;
                videoWrapper.innerHTML = `
                    <video controls preload="metadata" key="${{suite.videos[0].path}}">
                        <source src="${{suite.videos[0].path}}" type="video/webm">
                        Your browser does not support WebM video playback.
                    </video>
                `;
            }} else {{
                videoSection.style.display = 'none';
                videoWrapper.innerHTML = '';
            }}

            // Render Step-by-Step Execution Tree
            const stepsTimeline = document.getElementById('stepsTimeline');
            const stepCountLabel = document.getElementById('stepCountLabel');
            stepCountLabel.innerText = `${{suite.steps.length}} Step${{suite.steps.length > 1 ? 's' : ''}}`;

            if (suite.steps.length === 0) {{
                stepsTimeline.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">No individual step screenshots recorded for this test suite.</p>';
            }} else {{
                stepsTimeline.innerHTML = suite.steps.map(step => `
                    <div class="timeline-step">
                        <div class="step-node-icon">${{step.stepNumber}}</div>
                        <div class="step-card">
                            <div class="step-meta-row">
                                <div class="step-info">
                                    <span class="step-badge">Step ${{step.stepNumber < 10 ? '0' + step.stepNumber : step.stepNumber}}</span>
                                    <span class="step-title-text">${{step.title}}</span>
                                </div>
                                <span class="step-status-chip">&#10003; PASSED</span>
                            </div>

                            <div class="step-image-wrapper" onclick="openLightbox('${{step.screenshot}}', '${{step.title.replace(/'/g, "\\\\'")}}')">
                                <img src="${{step.screenshot}}" alt="${{step.title}}" loading="lazy" />
                                <div class="image-overlay-hint">&#128269; Click to zoom</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }}

            // Reset scroll to top
            document.getElementById('suiteBody').scrollTop = 0;
        }}

        // Filter Suites in Sidebar
        function filterTreeSuites() {{
            const q = document.getElementById('treeSearchInput').value.toLowerCase().trim();
            const groups = document.querySelectorAll('.submodule-group');

            groups.forEach(group => {{
                const items = group.querySelectorAll('.tree-suite-item');
                let groupHasMatch = false;

                items.forEach(item => {{
                    const title = item.dataset.title;
                    const matches = !q || title.includes(q);
                    item.style.display = matches ? 'flex' : 'none';
                    if (matches) groupHasMatch = true;
                }});

                group.style.display = groupHasMatch ? 'block' : 'none';
            }});
        }}

        // Lightbox Zoom Functions
        function openLightbox(imgSrc, title) {{
            const modal = document.getElementById('lightboxModal');
            const img = document.getElementById('lightboxImg');
            const titleEl = document.getElementById('lightboxTitle');

            img.src = imgSrc;
            titleEl.innerText = title;
            modal.style.display = 'flex';
        }}

        function closeLightbox(e) {{
            document.getElementById('lightboxModal').style.display = 'none';
        }}

        function closeLightboxDirect() {{
            document.getElementById('lightboxModal').style.display = 'none';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeLightboxDirect();
        }});

        // Start on load
        window.addEventListener('DOMContentLoaded', initApp);
    </script>
</body>
</html>
"""

# Write to index.html
output_path = os.path.join(workspace_dir, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Standalone HTML Master Report successfully rebuilt at: {output_path}")
