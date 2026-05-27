import streamlit.components.v1 as _components


def inject_theme_js(T: dict) -> None:
    """Inject JS via components.html (iframe → window.parent) to force-apply theme colors."""
    bg  = T['bg_card']
    bge = T['bg_elevated']
    fg  = T['text_primary']
    brd = T['border']
    acc = T['accent']
    suc = T['success']
    _components.html(f"""
<script>
(function() {{
    var BG  = '{bg}';
    var BGE = '{bge}';
    var FG  = '{fg}';
    var BRD = '1px solid {brd}';
    var ACC = '{acc}';
    var SUC = '{suc}';
    // Cross-origin embed safety — Streamlit Cloud iframe có thể sandbox parent
    var doc;
    try {{ doc = window.parent.document; }} catch(e) {{ return; }}
    if (!doc) return;

    function styleEl(el, bg, fg, brd, radius) {{
        el.style.setProperty('background-color', bg,  'important');
        el.style.setProperty('color',            fg,  'important');
        el.style.setProperty('border',           brd, 'important');
        el.style.setProperty('border-radius',    radius, 'important');
        el.style.setProperty('font-weight',      '600', 'important');
        el.querySelectorAll('p, span').forEach(function(c) {{
            c.style.setProperty('color',      fg,          'important');
            c.style.setProperty('background', 'transparent','important');
        }});
    }}

    function fixSidebarWidgets() {{
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (!sb) return;

        /* Selectbox — set tinted background on the visible select container */
        sb.querySelectorAll('[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child').forEach(function(el) {{
            el.style.setProperty('background',       'rgba(255,255,255,0.08)', 'important');
            el.style.setProperty('background-color', 'rgba(255,255,255,0.08)', 'important');
            el.style.setProperty('border',           '1px solid rgba(255,255,255,0.15)', 'important');
            el.style.setProperty('border-radius',    '8px', 'important');
        }});
        /* Selectbox inner elements — transparent + white text */
        sb.querySelectorAll('[data-testid="stSelectbox"] [data-baseweb="select"] > div:first-child *').forEach(function(el) {{
            if (el.tagName !== 'SVG' && el.tagName !== 'svg' && el.tagName !== 'PATH' && el.tagName !== 'path')
                el.style.setProperty('color', '#FFFFFF', 'important');
            el.style.setProperty('background',       'transparent', 'important');
            el.style.setProperty('background-color', 'transparent', 'important');
        }});
        /* SVG arrow in selectbox */
        sb.querySelectorAll('[data-testid="stSelectbox"] svg').forEach(function(el) {{
            el.style.setProperty('fill', 'rgba(191,219,254,0.8)', 'important');
        }});

        /* NumberInput container */
        sb.querySelectorAll('[data-testid="stNumberInput"] > div').forEach(function(el) {{
            el.style.setProperty('background',       'rgba(255,255,255,0.04)', 'important');
            el.style.setProperty('background-color', 'rgba(255,255,255,0.04)', 'important');
            el.style.setProperty('border',           '1px solid rgba(255,255,255,0.10)', 'important');
            el.style.setProperty('border-radius',    '10px', 'important');
            el.style.setProperty('overflow',         'hidden', 'important');
        }});
        /* NumberInput input text */
        sb.querySelectorAll('[data-testid="stNumberInput"] input').forEach(function(el) {{
            el.style.setProperty('background',       'transparent', 'important');
            el.style.setProperty('background-color', 'transparent', 'important');
            el.style.setProperty('color',            '#FFFFFF', 'important');
        }});
        /* NumberInput +/- buttons */
        sb.querySelectorAll('[data-testid="stNumberInput"] button').forEach(function(el) {{
            el.style.setProperty('background',       'rgba(255,255,255,0.04)', 'important');
            el.style.setProperty('background-color', 'rgba(255,255,255,0.04)', 'important');
            el.style.setProperty('color',            'rgba(191,219,254,0.8)', 'important');
            el.style.setProperty('border-left',      '1px solid rgba(255,255,255,0.08)', 'important');
        }});

        /* DateInput container */
        sb.querySelectorAll('[data-testid="stDateInput"] [data-baseweb="input"]').forEach(function(el) {{
            el.style.setProperty('background',       'rgba(255,255,255,0.08)', 'important');
            el.style.setProperty('background-color', 'rgba(255,255,255,0.08)', 'important');
            el.style.setProperty('border',           '1px solid rgba(255,255,255,0.15)', 'important');
            el.style.setProperty('border-radius',    '8px', 'important');
        }});
        sb.querySelectorAll('[data-testid="stDateInput"] input').forEach(function(el) {{
            el.style.setProperty('background',       'transparent', 'important');
            el.style.setProperty('background-color', 'transparent', 'important');
            el.style.setProperty('color',            '#FFFFFF', 'important');
        }});
    }}

    function applyAll() {{
        var root = doc.querySelector('[data-testid="stMain"]') ||
                   doc.querySelector('.main') || doc.body;
        if (!root) return;

        var RBG = 'linear-gradient(135deg,#0D1F4A 0%,#1B3D8C 60%,#2756C0 100%)';
        function styleRefreshBtn(btn) {{
            btn.style.setProperty('background',       RBG,   'important');
            btn.style.setProperty('background-image', RBG,   'important');
            btn.style.setProperty('color',            '#FFF','important');
            btn.style.setProperty('border',           'none','important');
            btn.style.setProperty('border-radius',    '10px','important');
            btn.style.setProperty('font-size',        '22px','important');
            btn.style.setProperty('min-height',       '60px','important');
            btn.style.setProperty('box-shadow',       '0 2px 10px rgba(27,61,140,0.4)','important');
            btn.querySelectorAll('p,span,div').forEach(function(c) {{
                c.style.setProperty('color',            '#FFF',        'important');
                c.style.setProperty('background',       'transparent', 'important');
                c.style.setProperty('background-image', 'none',        'important');
            }});
            if (!btn._hoverRefresh) {{
                btn._hoverRefresh = true;
                btn.addEventListener('mouseenter', function() {{
                    btn.style.setProperty('filter','brightness(1.2)','important');
                    btn.style.setProperty('transform','rotate(180deg)','important');
                }});
                btn.addEventListener('mouseleave', function() {{
                    btn.style.setProperty('filter','none','important');
                    btn.style.setProperty('transform','rotate(0deg)','important');
                }});
            }}
        }}
        doc.querySelectorAll('.refresh-header-btn button').forEach(styleRefreshBtn);
        root.querySelectorAll('.stButton > button').forEach(function(btn) {{
            var txt = btn.textContent.trim();
            if (txt === '↺' || txt === '⟳' || txt === '🔄') {{
                styleRefreshBtn(btn); return;
            }}

            if (btn.closest('[data-testid="stSidebar"]')) return;
            if (btn.closest('.stDownloadButton')) return;
            if (btn.closest('[data-baseweb="tab-list"]')) return;
            styleEl(btn, BG, FG, BRD, '20px');
            if (!btn._evt) {{
                btn._evt = true;
                btn.addEventListener('mouseenter', function() {{
                    btn.style.setProperty('background-color', ACC, 'important');
                    btn.style.setProperty('color', '#fff', 'important');
                    btn.style.setProperty('border-color', ACC, 'important');
                    btn.querySelectorAll('p,span').forEach(function(c) {{
                        c.style.setProperty('color', '#fff', 'important');
                    }});
                }});
                btn.addEventListener('mouseleave', function() {{
                    btn.style.setProperty('background-color', BG, 'important');
                    btn.style.setProperty('color', FG, 'important');
                    btn.style.setProperty('border-color', '{brd}', 'important');
                    btn.querySelectorAll('p,span').forEach(function(c) {{
                        c.style.setProperty('color', FG, 'important');
                    }});
                }});
            }}
        }});

        root.querySelectorAll('[data-baseweb="input"]').forEach(function(el) {{
            if (el.closest('[data-testid="stSidebar"]')) return;
            el.style.setProperty('background-color', BG, 'important');
            el.style.setProperty('border', BRD, 'important');
            el.style.setProperty('border-radius', '20px', 'important');
            el.style.setProperty('min-height', '40px', 'important');
            el.querySelectorAll('input').forEach(function(inp) {{
                inp.style.setProperty('color',       FG,            'important');
                inp.style.setProperty('background',  'transparent', 'important');
                inp.style.setProperty('font-weight', '600',         'important');
                inp.style.setProperty('font-size',   '13px',        'important');
            }});
        }});

        root.querySelectorAll('[data-baseweb="select"] > div').forEach(function(el) {{
            if (el.closest('[data-testid="stSidebar"]')) return;
            el.style.setProperty('background-color', BG, 'important');
            el.style.setProperty('border-color', brd, 'important');
            el.querySelectorAll('*').forEach(function(c) {{
                if (c.tagName !== 'INPUT')
                    c.style.setProperty('background', 'transparent', 'important');
                c.style.setProperty('color', FG, 'important');
            }});
        }});

        fixSidebarWidgets();

        doc.querySelectorAll('[data-testid="stSidebar"] iframe').forEach(function(iframe) {{
            try {{
                var idoc = iframe.contentDocument || iframe.contentWindow.document;
                if (idoc && idoc.body) {{
                    idoc.body.style.setProperty('background', 'transparent', 'important');
                    idoc.body.style.setProperty('background-color', 'transparent', 'important');
                    idoc.documentElement.style.setProperty('background', 'transparent', 'important');
                    idoc.documentElement.style.setProperty('background-color', 'transparent', 'important');
                }}
            }} catch(e) {{}}
        }});
        doc.querySelectorAll('[data-testid="stSidebar"] [data-testid="stCustomComponentV1"],' +
                             '[data-testid="stSidebar"] .stComponentContainer').forEach(function(el) {{
            el.style.setProperty('background', 'transparent', 'important');
            el.style.setProperty('border', 'none', 'important');
            el.style.setProperty('box-shadow', 'none', 'important');
        }});

        root.querySelectorAll('.stDownloadButton > button').forEach(function(btn) {{
            styleEl(btn, BG, FG, BRD, '10px');
            if (!btn._dlEvt) {{
                btn._dlEvt = true;
                btn.addEventListener('mouseenter', function() {{
                    btn.style.setProperty('background-color', SUC, 'important');
                    btn.style.setProperty('color', '#fff', 'important');
                    btn.querySelectorAll('p,span').forEach(function(c) {{
                        c.style.setProperty('color', '#fff', 'important');
                    }});
                }});
                btn.addEventListener('mouseleave', function() {{
                    btn.style.setProperty('background-color', BG, 'important');
                    btn.style.setProperty('color', FG, 'important');
                    btn.querySelectorAll('p,span').forEach(function(c) {{
                        c.style.setProperty('color', FG, 'important');
                    }});
                }});
            }}
        }});

        doc.querySelectorAll('[data-testid="stDataFrame"]').forEach(function(el) {{
            el.style.setProperty('background',       BG, 'important');
            el.style.setProperty('background-color', BG, 'important');
        }});
    }}

    // PERF v32: Bootstrap guard — chỉ chạy initial burst 1 LẦN trên parent.
    // Mỗi Streamlit rerun spawn iframe mới, IIFE chạy lại; flag này tránh
    // 19 timers × N reruns = 100+ timers thừa.
    if (!window.parent.__themeBootstrapped) {{
        window.parent.__themeBootstrapped = true;
        // Giảm cascade: 3 timers thay vì 5
        [100, 500, 2000].forEach(function(ms) {{ setTimeout(applyAll, ms); }});
        [200, 800].forEach(function(ms) {{ setTimeout(fixSidebarWidgets, ms); }});
    }} else {{
        // Reruns sau: chỉ 1 lần để re-apply nếu Streamlit GC styles
        setTimeout(applyAll, 200);
    }}

    // PERF v32: Observer NARROWED to stMain (not body) + EXCLUDE Plotly subtree.
    // Plotly emits 100+ DOM mutations per pan/zoom → trước đây fire applyAll
    // mỗi 500ms suốt thời gian user tương tác chart. Giờ filter out plotly.
    if (!window.parent.__themeObserverAttached) {{
        window.parent.__themeObserverAttached = true;
        var _debounce;
        var _lastApply = 0;
        var _scrollerFor = function(target) {{
            // Trả về true nếu mutation nằm trong plotly chart → skip
            var n = target;
            while (n && n !== doc.body) {{
                if (n.classList && (
                    n.classList.contains('js-plotly-plot') ||
                    n.classList.contains('plotly') ||
                    n.classList.contains('plot-container'))) return true;
                n = n.parentNode;
            }}
            return false;
        }};
        new MutationObserver(function(mutations) {{
            // Filter: skip mutations từ Plotly subtree
            var relevant = false;
            for (var i = 0; i < mutations.length; i++) {{
                if (!_scrollerFor(mutations[i].target)) {{
                    relevant = true;
                    break;
                }}
            }}
            if (!relevant) return;
            // Throttle: tối thiểu 1000ms giữa các applyAll calls
            var now = Date.now();
            if (now - _lastApply < 1000) {{
                clearTimeout(_debounce);
                _debounce = setTimeout(function() {{
                    _lastApply = Date.now();
                    applyAll();
                }}, 1000 - (now - _lastApply));
                return;
            }}
            clearTimeout(_debounce);
            _debounce = setTimeout(function() {{
                _lastApply = Date.now();
                applyAll();
            }}, 500);
        }}).observe(
            doc.querySelector('[data-testid="stMain"]') || doc.body,
            {{ childList: true, subtree: true }}
        );
    }}
}})();
</script>
""", height=0, scrolling=False)


def hide_streamlit_badges_js() -> None:
    """Ẩn Streamlit Cloud badges — LIGHTWEIGHT version (không làm quá tải app).
    Chỉ chạy initial burst + MutationObserver (event-driven, không polling)."""
    _components.html("""
<script>
(function() {
    var doc;
    try { doc = window.parent.document; } catch(e) { return; }

    // Inject CSS 1 lần vào parent <head>
    if (!doc._badgeCssInjected) {
        try {
            var style = doc.createElement('style');
            style.id = '__hide_streamlit_badges__';
            style.textContent = `
                [class*="viewerBadge"], [class*="ViewerBadge"],
                [class*="profileContainer"], [class*="_profileContainer"],
                [data-testid="stToolbar"], [data-testid="stDecoration"],
                [data-testid="stAppDeployButton"], [data-testid="stStatusWidget"],
                [data-testid*="manage-app"], [data-testid*="viewer"],
                .stDeployButton, .stAppDeployButton,
                button[kind="header"], button[data-testid="baseButton-header"],
                #MainMenu {
                    display: none !important;
                    visibility: hidden !important;
                }
                a[href*="streamlit.io"]:not([href*="docs.streamlit.io"]) {
                    display: none !important;
                }
            `;
            (doc.head || doc.documentElement).appendChild(style);
            doc._badgeCssInjected = true;
        } catch(e) {}
    }

    function hideBadges() {
        if (!doc.querySelectorAll) return;
        // Chỉ target selector cụ thể (không scan toàn bộ div/span — quá tốn CPU)
        var sels = [
            '[class*="viewerBadge"]','[class*="ViewerBadge"]',
            '[class*="profileContainer"]','[data-testid*="viewer"]',
            '[data-testid*="manage-app"]','[data-testid="stToolbar"]',
            '[data-testid="stDecoration"]','[data-testid="stAppDeployButton"]',
            '[data-testid="stStatusWidget"]','.stDeployButton'
        ];
        sels.forEach(function(sel) {
            doc.querySelectorAll(sel).forEach(function(el) {
                if (!el._hidden) {
                    el.style.setProperty('display', 'none', 'important');
                    el._hidden = true;
                }
            });
        });
        // Hide streamlit.io links (không phải docs)
        doc.querySelectorAll('a[href*="streamlit.io"]').forEach(function(el) {
            if (el._hidden) return;
            if (!el.href.includes('docs.streamlit.io')) {
                el.style.setProperty('display', 'none', 'important');
                el._hidden = true;
            }
        });
    }

    // Initial burst — chỉ vài lần đầu. CSS đã inject vào parent <head> ở
    // line trên rồi nên badge sẽ luôn ẩn (DOM mới cũng không tạo lại được
    // vì CSS rule `display:none` global). Bỏ MutationObserver — tránh fire
    // mỗi Plotly DOM mutation gây jank chart.
    // v40 PERF: 4 timers → 2 timers (badge CSS đã inject vào parent <head>
    // → bất kỳ DOM mới cũng tự ẩn, không cần aggressive polling)
    if (!window.parent.__hideBadgesBurst) {
        window.parent.__hideBadgesBurst = true;
        [100, 1500].forEach(function(ms) { setTimeout(hideBadges, ms); });
    }
})();
</script>
""", height=0, scrolling=False)


def force_sidebar_open_js() -> None:
    """Sidebar behavior (v21, 2026-05-20):
    Toggle button enabled trên CẢ desktop và mobile.

    JS làm 4 việc:
      1. INJECT CSS vào parent <head> — bypass Streamlit's CSS GC + cover
         ::before/::after pseudo-elements mà JS inline không reach được.
         Đây là layer DEFENSE chính.
      2. Clear stale inline lock styles từ legacy force-open era.
      3. Ensure toggle buttons không bị inline display:none.
      4. NUKE-STYLE nút X collapse button — set inline `!important` cho mọi
         property. Đây là layer DEFENSE phụ phòng khi CSS thua specificity.

    MutationObserver scoped vào sidebar để re-style nếu Streamlit re-render
    button khi user collapse/expand.

    Console log "[SidebarToggle]" cho phép verify trong DevTools.
    """
    _components.html("""
<script>
(function() {
    var doc, win;
    try {
        doc = window.parent.document;
        win = window.parent;
    } catch(e) { return; }
    if (!doc || !win) return;

    // ── LAYER 1: INJECT CSS VÀO PARENT <HEAD> — SPECIFICITY BOOST ────
    // Dùng :not(#__never_X__) chain để boost specificity. Mỗi :not(#id)
    // thêm 1 ID-level (100 pts). 5x :not = 500 pts specificity → vượt
    // mọi class-based selector của Streamlit Emotion CSS-in-JS.
    function injectToggleCSS() {
        if (doc.getElementById('__sidebar_toggle_force__')) return;
        var style = doc.createElement('style');
        style.id = '__sidebar_toggle_force__';
        // Boost = :not(#a):not(#b):not(#c):not(#d):not(#e) — 5 IDs phantom
        var BOOST = ':not(#__a__):not(#__b__):not(#__c__):not(#__d__):not(#__e__)';
        var BTN = '[data-testid="stSidebarCollapseButton"]' + BOOST;
        var BTN_ALT = 'button[data-testid="stSidebarCollapseButton"]' + BOOST;
        var HDR = '[data-testid="stSidebarHeader"]' + BOOST;

        style.textContent = (
            /* HEADER container — transparent */
            HDR + ', html body ' + HDR + ' {' +
                'background: transparent !important;' +
                'background-color: transparent !important;' +
                'background-image: none !important;' +
                'padding: 8px 14px 4px !important;' +
                'display: flex !important;' +
                'justify-content: flex-end !important;' +
                'align-items: center !important;' +
                'border: none !important;' +
                'box-shadow: none !important;' +
            '}' +
            /* BUTTON — navy translucent với viền xanh nhạt */
            BTN + ', ' + BTN_ALT + ', html body ' + BTN + ' {' +
                'background: rgba(255,255,255,0.10) !important;' +
                'background-color: rgba(255,255,255,0.10) !important;' +
                'background-image: none !important;' +
                'border: 1px solid rgba(122,164,212,0.45) !important;' +
                'border-radius: 8px !important;' +
                'box-shadow: none !important;' +
                'color: #D0E0F5 !important;' +
                'width: 30px !important;' +
                'height: 30px !important;' +
                'min-width: 30px !important;' +
                'min-height: 30px !important;' +
                'padding: 4px !important;' +
                'margin: 0 !important;' +
                'display: inline-flex !important;' +
                'align-items: center !important;' +
                'justify-content: center !important;' +
                'cursor: pointer !important;' +
                'outline: none !important;' +
            '}' +
            /* HOVER */
            BTN + ':hover, ' + BTN_ALT + ':hover {' +
                'background: rgba(122,164,212,0.30) !important;' +
                'background-color: rgba(122,164,212,0.30) !important;' +
                'border-color: rgba(208,224,245,0.70) !important;' +
            '}' +
            /* ALL DESCENDANTS — kill white backgrounds from nested elements */
            BTN + ' *, ' + BTN + '::before, ' + BTN + '::after {' +
                'background: transparent !important;' +
                'background-color: transparent !important;' +
                'background-image: none !important;' +
                'color: #D0E0F5 !important;' +
                'border: none !important;' +
                'box-shadow: none !important;' +
            '}' +
            /* SVG icon — force light blue fill/stroke */
            BTN + ' svg, ' + BTN + ' svg *, ' + BTN + ' svg path, ' +
            BTN + ' svg rect, ' + BTN + ' svg line, ' + BTN + ' svg circle {' +
                'color: #D0E0F5 !important;' +
                'fill: #D0E0F5 !important;' +
                'stroke: #D0E0F5 !important;' +
                'background: transparent !important;' +
                'background-color: transparent !important;' +
            '}' +
            BTN + ' svg {' +
                'width: 16px !important;' +
                'height: 16px !important;' +
            '}' +
            /* v30: HAMBURGER (collapsedControl) khi sidebar collapsed
             * Force navy + sliders icon — nằm NGOÀI sidebar nên observer
             * scoped sidebar không catch. CSS injection vào parent head
             * là cách duy nhất ổn định. */
            'html body [data-testid="stSidebarCollapsedControl"]' + BOOST + ',' +
            'html body [data-testid="collapsedControl"]' + BOOST + ' {' +
                'background: #1A3A6A !important;' +
                'background-color: #1A3A6A !important;' +
                'background-image: none !important;' +
                'border: 1px solid rgba(122,164,212,0.45) !important;' +
                'border-left: 3px solid #7AA4D4 !important;' +
                'border-radius: 0 12px 12px 0 !important;' +
                'box-shadow: 4px 0 16px rgba(0,0,0,0.45) !important;' +
                'min-width: 36px !important;' +
                'min-height: 44px !important;' +
                'padding: 4px 8px !important;' +
                'cursor: pointer !important;' +
            '}' +
            'html body [data-testid="stSidebarCollapsedControl"]:hover,' +
            'html body [data-testid="collapsedControl"]:hover {' +
                'background: #2557A7 !important;' +
                'background-color: #2557A7 !important;' +
                'border-color: #D0E0F5 !important;' +
            '}' +
            /* Hamburger descendants — transparent + light blue */
            'html body [data-testid="stSidebarCollapsedControl"] *,' +
            'html body [data-testid="collapsedControl"] * {' +
                'background: transparent !important;' +
                'background-color: transparent !important;' +
                'color: #D0E0F5 !important;' +
            '}' +
            /* SVG icon inside hamburger — light blue */
            'html body [data-testid="stSidebarCollapsedControl"] svg,' +
            'html body [data-testid="stSidebarCollapsedControl"] svg *,' +
            'html body [data-testid="collapsedControl"] svg,' +
            'html body [data-testid="collapsedControl"] svg * {' +
                'color: #D0E0F5 !important;' +
                'fill: #D0E0F5 !important;' +
                'stroke: #D0E0F5 !important;' +
                'background: transparent !important;' +
            '}'
        );
        (doc.head || doc.documentElement).appendChild(style);
        try { console.log('[SidebarToggle v30] CSS injected — includes hamburger rules in parent <head>'); } catch(e) {}
    }

    // ── LAYER 2: INLINE STYLE FALLBACK ──────────────────────────────
    // Inline style + !important beats ALL external CSS. Phòng khi CSS layer
    // thua specificity battle với Streamlit's internal style.
    function styleToggleButton() {
        var sels = [
            '[data-testid="stSidebarCollapseButton"]',
            '[data-testid="stSidebarHeader"] > button',
            '[data-testid="stSidebarHeader"] [data-testid="baseButton-headerNoPadding"]',
            'button[data-testid="baseButton-headerNoPadding"]',
            'button[kind="headerNoPadding"]'
        ];
        var buttons = [];
        sels.forEach(function(sel) {
            doc.querySelectorAll(sel).forEach(function(el) {
                if (buttons.indexOf(el) === -1) buttons.push(el);
            });
        });
        if (!buttons.length) return;

        var btnStyles = {
            'background':       'rgba(255,255,255,0.10)',
            'background-color': 'rgba(255,255,255,0.10)',
            'background-image': 'none',
            'border':           '1px solid rgba(122,164,212,0.45)',
            'border-radius':    '8px',
            'box-shadow':       'none',
            'color':            '#D0E0F5',
            'width':            '30px',
            'height':           '30px',
            'min-width':        '30px',
            'min-height':       '30px',
            'padding':          '4px',
            'margin':           '0',
            'display':          'inline-flex',
            'align-items':      'center',
            'justify-content':  'center',
            'cursor':           'pointer',
            'outline':          'none'
        };

        buttons.forEach(function(btn) {
            for (var k in btnStyles) {
                btn.style.setProperty(k, btnStyles[k], 'important');
            }
            // SVG icon — light blue fill/stroke
            btn.querySelectorAll('svg, svg *').forEach(function(el) {
                el.style.setProperty('color',  '#D0E0F5', 'important');
                el.style.setProperty('fill',   '#D0E0F5', 'important');
                el.style.setProperty('stroke', '#D0E0F5', 'important');
                if (el.tagName.toLowerCase() === 'svg') {
                    el.style.setProperty('width',  '16px', 'important');
                    el.style.setProperty('height', '16px', 'important');
                }
            });
            // All other descendants — transparent background, light blue text
            btn.querySelectorAll('*:not(svg):not(path):not(circle):not(line):not(polyline):not(rect)').forEach(function(el) {
                el.style.setProperty('background',       'transparent', 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
                el.style.setProperty('color',            '#D0E0F5',     'important');
            });

            // Hover handler — inline event listener (idempotent via _hovered flag)
            if (!btn._hoverBound) {
                btn._hoverBound = true;
                btn.addEventListener('mouseenter', function() {
                    btn.style.setProperty('background',       'rgba(122,164,212,0.30)', 'important');
                    btn.style.setProperty('background-color', 'rgba(122,164,212,0.30)', 'important');
                    btn.style.setProperty('border-color',     'rgba(208,224,245,0.70)', 'important');
                });
                btn.addEventListener('mouseleave', function() {
                    btn.style.setProperty('background',       'rgba(255,255,255,0.10)', 'important');
                    btn.style.setProperty('background-color', 'rgba(255,255,255,0.10)', 'important');
                    btn.style.setProperty('border-color',     'rgba(122,164,212,0.45)', 'important');
                });
            }
        });

        // Also style the sidebar header container itself — transparent
        doc.querySelectorAll('[data-testid="stSidebarHeader"]').forEach(function(hdr) {
            hdr.style.setProperty('background',       'transparent', 'important');
            hdr.style.setProperty('background-color', 'transparent', 'important');
            hdr.style.setProperty('padding',          '8px 14px 4px', 'important');
            hdr.style.setProperty('display',          'flex',         'important');
            hdr.style.setProperty('justify-content',  'flex-end',     'important');
            hdr.style.setProperty('align-items',      'center',       'important');
            hdr.style.setProperty('border',           'none',         'important');
            hdr.style.setProperty('box-shadow',       'none',         'important');
        });

        // v29: NUKE-STYLE HAMBURGER (collapsedControl) khi sidebar collapsed.
        // Streamlit's default hamburger có thể hiện white → force navy +
        // sliders icon (consistent với expanded toggle button).
        var hamburgers = [];
        ['[data-testid="stSidebarCollapsedControl"]', '[data-testid="collapsedControl"]'].forEach(function(sel) {
            doc.querySelectorAll(sel).forEach(function(el) {
                if (hamburgers.indexOf(el) === -1) hamburgers.push(el);
            });
        });
        hamburgers.forEach(function(hb) {
            // Force navy styling (override default Streamlit)
            hb.style.setProperty('background',       '#1A3A6A', 'important');
            hb.style.setProperty('background-color', '#1A3A6A', 'important');
            hb.style.setProperty('background-image', 'none',    'important');
            hb.style.setProperty('border',           '1px solid rgba(122,164,212,0.45)', 'important');
            hb.style.setProperty('border-left',      '3px solid #7AA4D4', 'important');
            hb.style.setProperty('border-radius',    '0 12px 12px 0', 'important');
            hb.style.setProperty('box-shadow',       '4px 0 16px rgba(0,0,0,0.45)', 'important');
            hb.style.setProperty('min-width',        '36px',    'important');
            hb.style.setProperty('min-height',       '44px',    'important');
            hb.style.setProperty('padding',          '4px 8px', 'important');
            // SVG icon inside — light blue
            hb.querySelectorAll('svg, svg *').forEach(function(el) {
                el.style.setProperty('color',  '#D0E0F5', 'important');
                el.style.setProperty('fill',   '#D0E0F5', 'important');
                el.style.setProperty('stroke', '#D0E0F5', 'important');
            });
            // All descendants — transparent + light blue text
            hb.querySelectorAll('*:not(svg):not(path):not(line):not(circle):not(rect)').forEach(function(el) {
                el.style.setProperty('background',       'transparent', 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
                el.style.setProperty('color',            '#D0E0F5',     'important');
            });
        });
    }

    function applySidebarMode() {
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (!sb) return;

        // FIX B1: Nếu đang fake-collapsed (L6 đã fire) → KHÔNG strip transform/
        // min-width/max-width vì sẽ wipe collapse. Chỉ clear các property legacy.
        var isFakeCollapsed = sb.getAttribute('data-fake-collapsed') === '1';
        if (!isFakeCollapsed) {
            ['display','visibility','transform','margin-left',
             'left','opacity','position']
                .forEach(function(p) { sb.style.removeProperty(p); });
        } else {
            // Chỉ clear các property KHÔNG liên quan đến collapse visual
            ['margin-left','left','opacity','position']
                .forEach(function(p) { sb.style.removeProperty(p); });
        }

        // Unhide toggle buttons (in case any code set inline display:none)
        // EXCEPT khi fake-collapsed: muốn hamburger HIỆN để user re-open
        var shows = [
            '[data-testid="stSidebarHeader"]',
            '[data-testid="stSidebarCollapseButton"]',
            'button[data-testid="baseButton-headerNoPadding"]',
            '[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"]'
        ];
        shows.forEach(function(sel) {
            doc.querySelectorAll(sel).forEach(function(el) {
                el.style.removeProperty('display');
                el.style.removeProperty('visibility');
            });
        });

        // NUKE-STYLE the X toggle button (layer 2)
        styleToggleButton();

        // LAYER 3 — REPLACE with custom button (most reliable approach)
        injectCustomToggleButton();

        // FIX B2: ATTACH RECONCILER ở đây — chạy mỗi applySidebarMode, đảm bảo
        // observer attach lại khi Streamlit re-render entire sidebar element.
        if (!sb.__reconcilerAttached) {
            sb.__reconcilerAttached = true;
            new MutationObserver(function() {
                if (sb.getAttribute('data-fake-collapsed') !== '1') return;
                var expanded = sb.getAttribute('aria-expanded');
                var nativeInline = sb.style.transform || '';
                // Streamlit thinks expanded → heal fake-collapse
                if (expanded === 'true' || nativeInline === '' || nativeInline === 'none') {
                    sb.style.removeProperty('transform');
                    sb.style.removeProperty('min-width');
                    sb.style.removeProperty('max-width');
                    sb.style.removeProperty('transition');
                    sb.removeAttribute('data-fake-collapsed');
                    var hb = doc.querySelector('[data-testid="stSidebarCollapsedControl"]') ||
                             doc.querySelector('[data-testid="collapsedControl"]');
                    if (hb) hb.style.removeProperty('display');
                    try { console.log('[SidebarToggle v25] Reconciler healed fake-collapse'); } catch(e) {}
                }
            }).observe(sb, {
                attributes: true,
                attributeFilter: ['aria-expanded', 'class']
            });
        }

        // v28 FIX: Re-inject observer — khi Streamlit collapse + expand sidebar,
        // React re-render header → custom button bị xoá → user thấy white default
        // Streamlit button. Observer watches sidebar DOM, debounced 100ms, kiểm
        // tra custom button có còn không, nếu mất thì re-inject.
        if (!sb.__reinjectObserverAttached) {
            sb.__reinjectObserverAttached = true;
            var _reinjectT;
            new MutationObserver(function() {
                clearTimeout(_reinjectT);
                _reinjectT = setTimeout(function() {
                    var header2 = sb.querySelector('[data-testid="stSidebarHeader"]');
                    if (header2 && !header2.querySelector('.__custom_sidebar_toggle__')) {
                        // Custom button bị xoá → re-inject
                        try { console.log('[SidebarToggle v28] Re-injecting custom button after re-render'); } catch(e) {}
                        injectCustomToggleButton();
                        // Also re-style toggle button (in case Streamlit reverted it)
                        styleToggleButton();
                    }
                }, 100);
            }).observe(sb, {
                childList: true, subtree: true
            });
        }
    }

    // ── LAYER 3: CUSTOM BUTTON REPLACEMENT (v25) ────────────────────
    // 3 agents điều tra v24 confirm 6 nguyên nhân khiến click forwarding fail:
    //   1. new MouseEvent từ IFRAME context không hợp lệ với React parent
    //   2. pointer-events:none block React event handling
    //   3. z-index:-1 đẩy element ra khỏi stacking context
    //   4. Cached nativeBtn stale qua Streamlit reruns
    //   5. Streamlit's BaseWeb button có thể listen mousedown/pointerdown
    //   6. React class component setState — phải qua React's fiber
    //
    // Fix v25: 6-layer defense:
    //   L1: Fresh lookup nativeBtn mỗi click (no closure cache)
    //   L2: win.MouseEvent constructor (parent's realm)
    //   L3: visibility:hidden + left:-9999px (KHÔNG pointer-events:none)
    //   L4: Full event sequence: pointerdown→mousedown→mouseup→click
    //   L5: React fiber __reactProps.onClick direct invocation
    //   L6: Last-resort fake-collapse: manually slide sidebar via inline style
    function injectCustomToggleButton() {
        var nativeBtn = doc.querySelector('[data-testid="stSidebarCollapseButton"]');
        if (!nativeBtn) return;

        var header = nativeBtn.closest('[data-testid="stSidebarHeader"]') ||
                     nativeBtn.parentElement;
        if (!header) return;

        // Idempotency check
        if (header.querySelector('.__custom_sidebar_toggle__')) return;

        // L3: Hide native button — visibility:hidden + position:absolute
        // + left:-9999px. KHÔNG dùng pointer-events:none vì React check
        // computed style. KHÔNG dùng z-index:-1 vì đẩy ra khỏi stacking
        // context. KHÔNG dùng display:none vì block click() event.
        nativeBtn.style.setProperty('visibility', 'hidden', 'important');
        nativeBtn.style.setProperty('position', 'absolute', 'important');
        nativeBtn.style.setProperty('left', '-9999px', 'important');
        nativeBtn.style.setProperty('top', '0', 'important');
        nativeBtn.style.setProperty('width', '30px', 'important');
        nativeBtn.style.setProperty('height', '30px', 'important');
        nativeBtn.style.setProperty('opacity', '0', 'important');

        // Tạo custom button — full control HTML + inline style
        var customBtn = doc.createElement('button');
        customBtn.className = '__custom_sidebar_toggle__';
        customBtn.setAttribute('type', 'button');
        customBtn.setAttribute('aria-label', 'Toggle sidebar');
        customBtn.title = 'Đóng/mở thanh điều hướng';

        // v26: SOLID NAVY background — không dùng rgba transparent vì nếu
        // element parent bị white (Streamlit có thể có element nền sáng), sẽ
        // hiện ra white thay vì navy. Dùng #1A3A6A giống hamburger button ở
        // ui/css.py line 1096 cho consistency.
        var baseStyle = (
            'background: #1A3A6A !important;' +
            'background-color: #1A3A6A !important;' +
            'background-image: none !important;' +
            'border: 1px solid rgba(122,164,212,0.45) !important;' +
            'border-radius: 8px !important;' +
            'box-shadow: 0 1px 4px rgba(0,0,0,0.25) !important;' +
            'color: #D0E0F5 !important;' +
            'width: 32px !important;' +
            'height: 32px !important;' +
            'min-width: 32px !important;' +
            'min-height: 32px !important;' +
            'padding: 4px !important;' +
            'margin: 0 !important;' +
            'display: inline-flex !important;' +
            'align-items: center !important;' +
            'justify-content: center !important;' +
            'cursor: pointer !important;' +
            'outline: none !important;' +
            'transition: background-color 0.15s, border-color 0.15s !important;' +
            'font-family: inherit !important;' +
            'position: relative !important;' +
            'z-index: 10 !important;'
        );
        customBtn.setAttribute('style', baseStyle);

        // v26: SLIDERS/EQUALIZER icon — matches Streamlit native UX. User
        // request: dùng icon giống "Thanh điều khiển Sidebar" tooltip.
        // 3 horizontal sliders với dots — phong cách settings.
        customBtn.innerHTML = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" ' +
            'viewBox="0 0 24 24" fill="none" stroke="#D0E0F5" stroke-width="2" ' +
            'stroke-linecap="round" stroke-linejoin="round" ' +
            'style="pointer-events:none;display:block">' +
            '<line x1="4" y1="6" x2="20" y2="6"/>' +
            '<line x1="4" y1="12" x2="20" y2="12"/>' +
            '<line x1="4" y1="18" x2="20" y2="18"/>' +
            '<circle cx="8" cy="6" r="2" fill="#1A3A6A"/>' +
            '<circle cx="16" cy="12" r="2" fill="#1A3A6A"/>' +
            '<circle cx="10" cy="18" r="2" fill="#1A3A6A"/>' +
            '</svg>'
        );

        // Hover handlers — solid navy sáng hơn
        customBtn.addEventListener('mouseenter', function() {
            customBtn.style.setProperty('background', '#2557A7', 'important');
            customBtn.style.setProperty('background-color', '#2557A7', 'important');
            customBtn.style.setProperty('border-color', 'rgba(208,224,245,0.70)', 'important');
        });
        customBtn.addEventListener('mouseleave', function() {
            customBtn.style.setProperty('background', '#1A3A6A', 'important');
            customBtn.style.setProperty('background-color', '#1A3A6A', 'important');
            customBtn.style.setProperty('border-color', 'rgba(122,164,212,0.45)', 'important');
        });

        // ── L5: REACT FIBER PROPS ACCESS ────────────────────────────
        // Direct invocation của React's onClick prop, bypass DOM event hệ
        // hoàn toàn. Streamlit dùng React class component với:
        //   onClick={this.toggleCollapse}
        // React DOM gắn props vào element qua key __reactProps$<random>.
        function getReactProps(el) {
            if (!el) return null;
            var keys = Object.keys(el);
            for (var i = 0; i < keys.length; i++) {
                if (keys[i].indexOf('__reactProps') === 0) return el[keys[i]];
            }
            return null;
        }

        // ── L6: LAST-RESORT FAKE-COLLAPSE ───────────────────────────
        // Nếu mọi cách forward click đều fail, manually toggle sidebar visual
        // bằng cách set inline style giống Streamlit's collapsed state.
        function fakeToggleSidebar() {
            var sb = doc.querySelector('[data-testid="stSidebar"]');
            var hamburger = doc.querySelector('[data-testid="stSidebarCollapsedControl"]') ||
                            doc.querySelector('[data-testid="collapsedControl"]');
            if (!sb) return false;

            var isFakeCollapsed = sb.getAttribute('data-fake-collapsed') === '1';
            if (!isFakeCollapsed) {
                var w = sb.getBoundingClientRect().width || 280;
                sb.style.setProperty('transform', 'translateX(-' + w + 'px)', 'important');
                sb.style.setProperty('min-width', '0', 'important');
                sb.style.setProperty('max-width', '0', 'important');
                sb.style.setProperty('transition',
                    'transform 300ms, min-width 300ms, max-width 300ms', 'important');
                sb.setAttribute('data-fake-collapsed', '1');
                if (hamburger) hamburger.style.setProperty('display', 'flex', 'important');
            } else {
                sb.style.removeProperty('transform');
                sb.style.removeProperty('min-width');
                sb.style.removeProperty('max-width');
                sb.removeAttribute('data-fake-collapsed');
                if (hamburger) hamburger.style.removeProperty('display');
            }
            try { console.log('[SidebarToggle v25] Fake-collapse used (L6 fallback)'); } catch(e) {}
            return true;
        }

        // ── DEBOUNCE for forwardClick (avoid double-toggle on rapid click) ─
        var _fwdInProgress = false;

        // ── MAIN FORWARDER: 6 layers in priority order ──────────────
        function forwardClick(e) {
            try { console.log('[SidebarToggle v27] forwardClick fired — attempting collapse/expand'); } catch(e2) {}
            if (e) { e.preventDefault(); e.stopPropagation(); }
            if (_fwdInProgress) return;  // debounce 350ms
            _fwdInProgress = true;
            setTimeout(function() { _fwdInProgress = false; }, 350);

            // L1: FRESH LOOKUP — không dùng closure cache vì stale qua reruns
            var native = doc.querySelector('[data-testid="stSidebarCollapseButton"]');
            if (!native) {
                // Native button không còn → dùng L6 fake-collapse
                fakeToggleSidebar();
                return;
            }

            // FIX B1: Snapshot via getBoundingClientRect — Streamlit collapse
            // dùng Emotion CSS classes (computed style), KHÔNG phải inline
            // style.transform. Phải đo width trực tiếp.
            var sb = doc.querySelector('[data-testid="stSidebar"]');
            var preWidth = sb ? sb.getBoundingClientRect().width : 0;

            // Tạm thời unblock native button để React's handler nhận click.
            // Native vẫn visibility:hidden + left:-9999px → user không thấy.
            native.style.setProperty('pointer-events', 'auto', 'important');

            // L4 + L2: Dispatch full event sequence với win.MouseEvent
            // (parent realm constructor) → BaseWeb có thể listen mousedown
            try {
                var MEC = win.MouseEvent || MouseEvent;
                var opts = { bubbles: true, cancelable: true, view: win, button: 0 };
                ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(function(type) {
                    try {
                        if (type.indexOf('pointer') === 0 && win.PointerEvent) {
                            native.dispatchEvent(new win.PointerEvent(type, opts));
                        } else {
                            native.dispatchEvent(new MEC(type, opts));
                        }
                    } catch(err) {}
                });
            } catch(err) {}

            // L5: Direct React onClick invocation via fiber props.
            // FIX B3: nativeEvent là object đầy đủ method để Streamlit's
            // BaseWeb handler có thể call e.nativeEvent.stopImmediatePropagation()
            // mà không crash.
            try {
                var props = getReactProps(native);
                if (props && typeof props.onClick === 'function') {
                    var noop = function() {};
                    var nativeEventStub = {
                        stopImmediatePropagation: noop,
                        stopPropagation: noop,
                        preventDefault: noop,
                        target: native,
                        currentTarget: native,
                        type: 'click',
                        defaultPrevented: false,
                        cancelable: true,
                        bubbles: true
                    };
                    var fakeEvent = {
                        preventDefault: noop,
                        stopPropagation: noop,
                        stopImmediatePropagation: noop,
                        currentTarget: native,
                        target: native,
                        nativeEvent: nativeEventStub,
                        type: 'click',
                        bubbles: true,
                        cancelable: true,
                        defaultPrevented: false,
                        isTrusted: false
                    };
                    props.onClick(fakeEvent);
                    try { console.log('[SidebarToggle v25] React onClick invoked via fiber'); } catch(e) {}
                }
            } catch(err) {}

            // FIX B2: KHÔNG cần setTimeout restore visibility:hidden — native
            // luôn left:-9999px nên user không thấy dù visibility:visible.

            // L6: Verify sau 350ms — đo width thật, nếu KHÔNG đổi → React
            // không trigger collapse → fallback fake-collapse
            setTimeout(function() {
                var sb2 = doc.querySelector('[data-testid="stSidebar"]');
                if (!sb2) return;
                var postWidth = sb2.getBoundingClientRect().width;
                // Streamlit collapse → width đi từ 280 → 0 (hoặc ngược lại)
                // Chênh lệch <5px → coi như KHÔNG đổi → React không nhận click
                if (Math.abs(postWidth - preWidth) < 5 &&
                    sb2.getAttribute('data-fake-collapsed') !== '1') {
                    try { console.warn('[SidebarToggle v25] React click failed (width unchanged), using L6 fake-collapse'); } catch(e) {}
                    fakeToggleSidebar();
                }
            }, 350);
        }

        customBtn.addEventListener('click', forwardClick);
        // Reconciliation observer moved to applySidebarMode để re-attach
        // khi Streamlit re-render sidebar element (FIX B2).

        // Append vào header
        header.appendChild(customBtn);

        // Style header — flex justify-end
        header.style.setProperty('display', 'flex', 'important');
        header.style.setProperty('justify-content', 'flex-end', 'important');
        header.style.setProperty('align-items', 'center', 'important');
        header.style.setProperty('padding', '8px 14px 4px', 'important');
        header.style.setProperty('background', 'transparent', 'important');

        try { console.log('[SidebarToggle v27] Custom button injected — width lock removed, click should work now'); } catch(e) {}
    }

    // ── INJECT CSS NGAY khi script chạy (không cần đợi sidebar render) ──
    // CSS sống trong parent <head>, không bị Streamlit GC qua reruns.
    injectToggleCSS();

    // v40 PERF: bootstrap guard — chỉ chạy initial burst 1 LẦN/parent window.
    // Mỗi Streamlit rerun spawn iframe mới, IIFE chạy lại. Flag tránh 6 timers
    // × N reruns = lãng phí. MutationObserver đã catch button re-render.
    if (!win.__sbInitBurst) {
        win.__sbInitBurst = true;
        // Reduced: 6 timers → 3 timers (early + medium + late)
        [100, 800, 3000].forEach(function(ms) {
            setTimeout(applySidebarMode, ms);
        });
    } else {
        // Reruns sau: 1 lần để re-apply
        setTimeout(applySidebarMode, 100);
    }

    try { console.log('[SidebarToggle v40] Performance: lazy imports + CSS cache + reduced timer cascade'); } catch(e) {}

    // Resize/orientationchange listeners — guarded
    if (!win.__sbResizeAttached) {
        win.__sbResizeAttached = true;
        var _resizeT;
        win.addEventListener('resize', function() {
            clearTimeout(_resizeT);
            _resizeT = setTimeout(applySidebarMode, 150);
        });
        win.addEventListener('orientationchange', function() {
            setTimeout(applySidebarMode, 300);
        });
    }

    // MutationObserver — SCOPED vào sidebar (NOT body) để tránh fire mỗi
    // Plotly mutation gây jank chart. Guarded to avoid duplicate observers.
    if (!win.__sbToggleObserverAttached) {
        var _styleT;
        var _scheduleStyle = function() {
            clearTimeout(_styleT);
            _styleT = setTimeout(styleToggleButton, 100);
        };

        function tryAttachToSidebar() {
            var sb = doc.querySelector('[data-testid="stSidebar"]');
            if (!sb) {
                // Sidebar chưa render → retry sau 200ms
                setTimeout(tryAttachToSidebar, 200);
                return;
            }
            if (win.__sbToggleObserverAttached) return;
            win.__sbToggleObserverAttached = true;
            new MutationObserver(_scheduleStyle).observe(sb, {
                childList: true, subtree: true
            });
        }
        tryAttachToSidebar();
    }
})();
</script>
""", height=0, scrolling=False)
