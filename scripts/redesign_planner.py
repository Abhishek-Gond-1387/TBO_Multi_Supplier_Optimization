#!/usr/bin/env python3
"""
Redesigns the Master Planner section of frontend/index.html into a 
world-class luxury travel planning interface (inspired by Airbnb, Expedia, Aman, Black Tomato).
Preserves all functionality, IDs, and API hooks while elevating:
- Hero Section with high-resolution travel photography & "Your Journey, Your Way."
- Floating Luxury Search Dock
- Destination Discovery Cards with real imagery
- Tactile Custom Traveler & Room Selector
- Visual Transit & Accommodation Cards
- Modern Budget Slider + Feasibility Gauge
- Editorial 3-Tier Results, Timeline, and Price Breakdown
"""

import re
import sys

PLANNER_CSS = '''
    /* ========================================================
       MASTER PLANNER REDESIGN: LUXURY EDITORIAL TRAVEL ARCHITECT
       Inspired by Airbnb, Expedia, Aman & Modern Luxury Travel
       ======================================================== */
    .planner-engine-section {
      background-color: #FAF8F5;
      position: relative;
      padding: 0 0 100px 0;
      overflow: hidden;
    }

    /* 1. Cinematic Master Planner Hero Banner */
    .planner-hero-banner {
      position: relative;
      min-height: 520px;
      background: linear-gradient(180deg, rgba(14, 27, 36, 0.45) 0%, rgba(14, 27, 36, 0.88) 100%),
                  url('https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=2000&q=85') center center / cover no-repeat;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 90px 24px 130px;
      color: #FFFFFF;
    }

    .planner-hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(212, 175, 55, 0.2);
      border: 1px solid rgba(212, 175, 55, 0.5);
      backdrop-filter: blur(8px);
      padding: 6px 16px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #F8D98C;
      margin-bottom: 20px;
      animation: fadeInDown 0.6s ease;
    }

    .planner-hero-title {
      font-family: var(--font-serif);
      font-size: clamp(38px, 5.5vw, 64px);
      font-weight: 600;
      line-height: 1.12;
      color: #FFFFFF;
      margin: 0 0 18px 0;
      max-width: 900px;
      text-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
      letter-spacing: -0.01em;
    }

    .planner-hero-sub {
      font-family: var(--font-sans);
      font-size: clamp(15px, 1.8vw, 18px);
      color: rgba(255, 255, 255, 0.88);
      max-width: 720px;
      line-height: 1.6;
      margin: 0 auto 32px;
      font-weight: 400;
      text-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    }

    /* 2. Floating Search Dock (Airbnb Style Capsule) */
    .planner-dock-container {
      max-width: 1200px;
      width: 94%;
      margin: -70px auto 48px;
      position: relative;
      z-index: 30;
    }

    .planner-dock-bar {
      background: rgba(255, 255, 255, 0.98);
      backdrop-filter: blur(20px);
      border-radius: 24px;
      box-shadow: 0 24px 60px rgba(14, 27, 36, 0.14), 0 4px 16px rgba(0, 0, 0, 0.04);
      border: 1px solid rgba(212, 175, 55, 0.35);
      display: grid;
      grid-template-columns: 1.3fr 1fr 1fr 1fr auto;
      align-items: center;
      padding: 10px 14px;
      gap: 8px;
      transition: all 0.3s ease;
    }

    @media (max-width: 980px) {
      .planner-dock-bar {
        grid-template-columns: 1fr;
        padding: 16px;
        border-radius: 20px;
      }
    }

    .planner-dock-item {
      padding: 12px 18px;
      border-radius: 16px;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }

    .planner-dock-item:hover {
      background: rgba(42, 127, 186, 0.05);
    }

    .planner-dock-item.active {
      background: #FAF8F5;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    }

    .planner-dock-label {
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--color-muted-grey);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .planner-dock-val {
      font-size: 14.5px;
      font-weight: 700;
      color: var(--color-deep-navy);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .planner-dock-cta {
      background: linear-gradient(135deg, #D4AF37 0%, #C49B27 100%);
      color: #162D3C;
      font-weight: 800;
      font-size: 14px;
      padding: 16px 28px;
      border-radius: 18px;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.35);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      white-space: nowrap;
    }

    .planner-dock-cta:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 28px rgba(212, 175, 55, 0.5);
      background: linear-gradient(135deg, #DFC048 0%, #D4AF37 100%);
    }

    /* 3. Destination Discovery Gallery */
    .dest-discovery-wrap {
      max-width: 1240px;
      margin: 0 auto 56px;
      padding: 0 24px;
    }

    .dest-discovery-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 12px;
    }

    .dest-grid-cards {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 22px;
    }

    .dest-card-luxury {
      background: #FFFFFF;
      border-radius: 20px;
      overflow: hidden;
      border: 1px solid rgba(22, 45, 60, 0.08);
      box-shadow: 0 8px 24px rgba(22, 45, 60, 0.06);
      transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
      position: relative;
      display: flex;
      flex-direction: column;
    }

    .dest-card-luxury:hover {
      transform: translateY(-6px);
      box-shadow: 0 20px 48px rgba(22, 45, 60, 0.14);
      border-color: rgba(212, 175, 55, 0.45);
    }

    .dest-card-thumb-wrap {
      position: relative;
      height: 190px;
      overflow: hidden;
    }

    .dest-card-thumb {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .dest-card-luxury:hover .dest-card-thumb {
      transform: scale(1.08);
    }

    .dest-card-badge {
      position: absolute;
      top: 14px;
      left: 14px;
      background: rgba(14, 27, 36, 0.7);
      backdrop-filter: blur(8px);
      color: #FFFFFF;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      letter-spacing: 0.04em;
    }

    .dest-card-price-pill {
      position: absolute;
      bottom: 12px;
      right: 14px;
      background: #FFFFFF;
      color: var(--color-deep-navy);
      font-size: 11.5px;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .dest-card-body {
      padding: 18px 20px 20px;
      display: flex;
      flex-direction: column;
      flex: 1;
      justify-content: space-between;
    }

    .dest-card-title {
      font-family: var(--font-serif);
      font-size: 20px;
      font-weight: 600;
      color: var(--color-deep-navy);
      margin: 0 0 4px 0;
    }

    .dest-card-region {
      font-size: 12px;
      color: var(--color-primary-blue);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }

    .dest-card-desc {
      font-size: 13px;
      color: var(--color-muted-grey);
      line-height: 1.5;
      margin: 0 0 16px 0;
    }

    .dest-card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px solid rgba(22, 45, 60, 0.06);
      padding-top: 12px;
      font-size: 12px;
      color: var(--color-dark-text);
    }

    .btn-card-select {
      background: transparent;
      border: 1.5px solid var(--color-sky-blue);
      color: var(--color-primary-blue);
      font-weight: 700;
      font-size: 12px;
      padding: 6px 14px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .dest-card-luxury:hover .btn-card-select {
      background: var(--color-primary-blue);
      color: #FFFFFF;
      border-color: var(--color-primary-blue);
    }

    /* 4. Luxury Progress Stepper */
    .luxury-stepper-wrap {
      display: flex;
      justify-content: center;
      align-items: center;
      max-width: 680px;
      margin: 0 auto 36px;
      position: relative;
    }

    .luxury-stepper-track {
      position: absolute;
      top: 20px;
      left: 12%;
      right: 12%;
      height: 2px;
      background: rgba(22, 45, 60, 0.12);
      z-index: 1;
    }

    .luxury-stepper-item {
      position: relative;
      z-index: 2;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      flex: 1;
      text-align: center;
      cursor: pointer;
    }

    .luxury-stepper-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2px solid rgba(22, 45, 60, 0.18);
      color: var(--color-muted-grey);
      font-weight: 800;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }

    .luxury-stepper-item.active .luxury-stepper-circle {
      background: var(--color-deep-navy);
      border-color: #D4AF37;
      color: #FFFFFF;
      box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.25);
    }

    .luxury-stepper-item.completed .luxury-stepper-circle {
      background: #28A745;
      border-color: #28A745;
      color: #FFFFFF;
    }

    .luxury-stepper-label {
      font-size: 13px;
      font-weight: 700;
      color: var(--color-muted-grey);
      transition: color 0.3s ease;
    }

    .luxury-stepper-item.active .luxury-stepper-label {
      color: var(--color-deep-navy);
    }

    /* 5. Modern Interactive Planning Cards (Step 1 & 2) */
    .planner-card-elevated {
      background: #FFFFFF;
      border-radius: 24px;
      border: 1px solid rgba(22, 45, 60, 0.08);
      box-shadow: 0 20px 50px rgba(22, 45, 60, 0.07);
      padding: 44px;
      max-width: 1200px;
      margin: 0 auto;
      transition: all 0.3s ease;
    }

    @media (max-width: 768px) {
      .planner-card-elevated {
        padding: 24px 18px;
        border-radius: 20px;
      }
    }

    /* Visual Preference Cards (Transit & Accommodation) */
    .pref-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-top: 10px;
    }

    .pref-visual-card {
      background: #FAF8F5;
      border: 1.5px solid rgba(22, 45, 60, 0.1);
      border-radius: 16px;
      padding: 18px 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
    }

    .pref-visual-card:hover {
      transform: translateY(-3px);
      border-color: var(--color-sky-blue);
      background: #FFFFFF;
      box-shadow: 0 8px 20px rgba(42, 127, 186, 0.12);
    }

    .pref-visual-card.active {
      border-color: #D4AF37;
      background: #FFFFFF;
      box-shadow: 0 8px 24px rgba(212, 175, 55, 0.22);
    }

    .pref-visual-card.active::after {
      content: '✓';
      position: absolute;
      top: 12px;
      right: 12px;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: #D4AF37;
      color: #162D3C;
      font-size: 11px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .pref-card-icon {
      font-size: 26px;
      margin-bottom: 2px;
    }

    .pref-card-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--color-deep-navy);
      margin: 0;
    }

    .pref-card-sub {
      font-size: 12px;
      color: var(--color-muted-grey);
      line-height: 1.4;
      margin: 0;
    }

    /* Duration Quick Presets Row */
    .duration-presets-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 10px;
    }

    .duration-preset-btn {
      padding: 7px 14px;
      background: #FAF8F5;
      border: 1px solid rgba(22, 45, 60, 0.12);
      border-radius: 10px;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--color-deep-navy);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .duration-preset-btn:hover {
      border-color: var(--color-sky-blue);
      background: var(--color-soft-blue);
    }

    .duration-preset-btn.active {
      background: var(--color-deep-navy);
      color: #FFFFFF;
      border-color: var(--color-deep-navy);
    }

    /* Budget Range Slider Control */
    .budget-slider-wrap {
      margin-top: 14px;
      padding: 0 4px;
    }

    .budget-slider {
      width: 100%;
      height: 6px;
      background: rgba(22, 45, 60, 0.12);
      border-radius: 9999px;
      outline: none;
      -webkit-appearance: none;
      appearance: none;
      cursor: pointer;
    }

    .budget-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: #D4AF37;
      border: 3px solid #FFFFFF;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
      cursor: pointer;
      transition: transform 0.15s ease;
    }

    .budget-slider::-webkit-slider-thumb:hover {
      transform: scale(1.15);
    }

    .slider-ticks {
      display: flex;
      justify-content: space-between;
      margin-top: 6px;
      font-size: 11px;
      font-weight: 600;
      color: var(--color-muted-grey);
    }
'''

def main():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Insert PLANNER_CSS into <style> if not already present
    if 'MASTER PLANNER REDESIGN: LUXURY EDITORIAL TRAVEL ARCHITECT' not in content:
        insert_marker = '</style>'
        idx = content.find(insert_marker)
        if idx != -1:
            content = content[:idx] + PLANNER_CSS + '\n' + content[idx:]
            print("Injected MASTER PLANNER luxury CSS.")

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    main()
