#!/usr/bin/env python3
"""
Verification script for Phase 2 UI Global improvements.
Checks that all HTML and CSS changes are in place.
"""

import os
from pathlib import Path

def check_file_exists(path):
    """Check if a file exists and return status."""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    return status, exists

def check_file_contains(path, text, description):
    """Check if file contains specific text."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            found = text in content
            status = "✓" if found else "✗"
            return status, found, description
    except Exception as e:
        return "✗", False, f"{description} (Error: {e})"

def main():
    base_path = Path(__file__).parent
    
    print("=" * 60)
    print("VERIFICATION: Phase 2 - UI Global Improvements")
    print("=" * 60)
    
    # Check files exist
    print("\n1. Files Existence Check:")
    files_to_check = [
        ("app/templates/base.html", "Base template"),
        ("app/static/css/styles.css", "Main stylesheet"),
        ("app/static/js/app.js", "App JavaScript"),
    ]
    
    for file_path, desc in files_to_check:
        full_path = base_path / file_path
        status, exists = check_file_exists(full_path)
        print(f"   {status} {file_path}: {desc}")
    
    # Check base.html improvements
    print("\n2. Base.html Enhancements:")
    base_html = base_path / "app/templates/base.html"
    checks = [
        ('<footer class="footer">', "Footer section"),
        ('id="mobile-menu-toggle"', "Mobile menu toggle"),
        ('class="nav-link"', "Nav link styling"),
        ('footer__brand', "Footer branding"),
        ('footer__nav', "Footer navigation"),
        ('role="navigation"', "Semantic HTML role"),
    ]
    
    for text, desc in checks:
        status, found, _ = check_file_contains(base_html, text, desc)
        print(f"   {status} {desc}")
    
    # Check CSS improvements
    print("\n3. CSS Enhancements:")
    styles_css = base_path / "app/static/css/styles.css"
    css_checks = [
        ('--primary:', "CSS color variables"),
        ('.nav-link', "Nav link styles"),
        ('.menu-toggle', "Mobile menu toggle styles"),
        ('.footer', "Footer styles"),
        ('.footer__inner', "Footer grid layout"),
        ('@media (max-width: 768px)', "Mobile responsive design"),
        ('body.dark .footer', "Dark mode footer styles"),
        ('body.dark .nav-link', "Dark mode nav styles"),
    ]
    
    for text, desc in css_checks:
        status, found, _ = check_file_contains(styles_css, text, desc)
        print(f"   {status} {desc}")
    
    # Check JavaScript functionality
    print("\n4. JavaScript Features:")
    app_js = base_path / "app/static/js/app.js"
    js_checks = [
        ('initMobileMenu', "Mobile menu initialization"),
        ('menuToggle.addEventListener', "Menu toggle event listener"),
        ('navMenu.classList.toggle', "Menu toggle class"),
        ('aria-expanded', "Accessibility attribute handling"),
    ]
    
    for text, desc in js_checks:
        status, found, _ = check_file_contains(app_js, text, desc)
        print(f"   {status} {desc}")
    
    # Check templates extend base.html
    print("\n5. Template Inheritance Check:")
    templates_dir = base_path / "app/templates"
    template_files = [
        "formatter.html",
        "csv_sql.html",
        "generator.html",
        "table_size.html",
        "normalization.html",
        "optimizer.html",
        "index.html",
    ]
    
    for template in template_files:
        template_path = templates_dir / template
        status, found, _ = check_file_contains(template_path, "{% extends 'base.html' %}", template)
        print(f"   {status} {template} extends base.html")
    
    # Check responsive design
    print("\n6. Responsive Design Check:")
    responsive_checks = [
        (".footer__inner", "Footer responsive grid"),
        ("@media", "Media queries present"),
        ("768px", "Mobile breakpoint"),
        ("960px", "Tablet breakpoint"),
        ("1024px", "Desktop breakpoint"),
    ]
    
    for text, desc in responsive_checks:
        status, found, _ = check_file_contains(styles_css, text, desc)
        print(f"   {status} {desc}")
    
    # Check dark mode implementation
    print("\n7. Dark Mode Check:")
    dark_mode_checks = [
        ("body.dark", "Dark mode selector"),
        ("body.dark .topbar", "Dark navbar"),
        ("body.dark .footer", "Dark footer"),
        ("body.dark .nav-link", "Dark nav links"),
        ("color-scheme: dark", "Color scheme property"),
    ]
    
    for text, desc in dark_mode_checks:
        status, found, _ = check_file_contains(styles_css, text, desc)
        print(f"   {status} {desc}")
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
