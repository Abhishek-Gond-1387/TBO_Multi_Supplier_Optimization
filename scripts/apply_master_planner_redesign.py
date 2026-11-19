#!/usr/bin/env python3
"""
Applies the full Master Planner visual redesign to frontend/index.html and index.html:
- Injects ultra-luxury CSS into <style>
- Replaces #plan-journey with the new majestic layout:
  1. Cinematic Hero Section ("Your Journey, Your Way.")
  2. Floating Luxury Search Dock (Airbnb / Expedia style)
  3. AI Plain English Concierge card
  4. Destination Discovery Gallery with real photographs
  5. Elevated Planning Console (Step 1, Step 2, Step 3)
  6. Visual cards for Transit, Accommodation, Duration presets & Budget slider
- Adds JavaScript helper functions: selectDestinationEnclave, selectTransitCard, selectStayCard, selectDurationPreset, slider sync, and dock sync.
"""

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
      min-height: 480px;
      background: linear-gradient(180deg, rgba(14, 27, 36, 0.45) 0%, rgba(14, 27, 36, 0.90) 100%),
                  url('https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=2000&q=85') center center / cover no-repeat;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 80px 24px 130px;
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
      margin-bottom: 18px;
    }

    .planner-hero-title {
      font-family: var(--font-serif);
      font-size: clamp(38px, 5.5vw, 64px);
      font-weight: 600;
      line-height: 1.12;
      color: #FFFFFF;
      margin: 0 0 16px 0;
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
      margin: 0 auto 10px;
      font-weight: 400;
      text-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
    }

    /* 2. Floating Search Dock (Airbnb Style Capsule) */
    .planner-dock-container {
      max-width: 1200px;
      width: 94%;
      margin: -65px auto 44px;
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
      padding: 10px 16px;
      border-radius: 16px;
      cursor: pointer;
      transition: all 0.2s ease;
      position: relative;
    }

    .planner-dock-item:hover {
      background: rgba(42, 127, 186, 0.05);
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
      margin: 0 auto 52px;
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
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
      margin-top: 10px;
    }

    .pref-visual-card {
      background: #FAF8F5;
      border: 1.5px solid rgba(22, 45, 60, 0.1);
      border-radius: 16px;
      padding: 16px 14px;
      display: flex;
      flex-direction: column;
      gap: 6px;
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
      top: 10px;
      right: 12px;
      width: 20px;
      height: 20px;
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
      font-size: 24px;
      margin-bottom: 2px;
    }

    .pref-card-title {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--color-deep-navy);
      margin: 0;
    }

    .pref-card-sub {
      font-size: 11.5px;
      color: var(--color-muted-grey);
      line-height: 1.4;
      margin: 0;
    }

    /* Duration Quick Presets Row */
    .duration-presets-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }

    .duration-preset-btn {
      padding: 6px 14px;
      background: #FAF8F5;
      border: 1px solid rgba(22, 45, 60, 0.12);
      border-radius: 10px;
      font-size: 12px;
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

NEW_PLAN_JOURNEY_HTML = '''  <!-- ========================================================
       SECTION: REDESIGNED LUXURY MASTER PLANNER
       ======================================================== -->
  <section class="planner-engine-section" id="plan-journey">
    
    <!-- 1. Cinematic Hero Banner: "Your Journey, Your Way." -->
    <div class="planner-hero-banner">
      <div class="planner-hero-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F8D98C" stroke-width="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        <span>AI-Powered Multi-Supplier Architecture</span>
      </div>
      <h2 class="planner-hero-title">Your Journey, Your Way.</h2>
      <p class="planner-hero-sub">
        Design your bespoke pan-India voyage with real-time multi-supplier intelligence, handpicked heritage sanctuaries, and verified transparent pricing.
      </p>
    </div>

    <!-- 2. Floating Master Search Dock (Airbnb Style Capsule) -->
    <div class="planner-dock-container">
      <div class="planner-dock-bar">
        <!-- Segment 1: Where To? -->
        <div class="planner-dock-item" onclick="switchPlannerStep(1); document.getElementById('planDestInput')?.focus();">
          <div class="planner-dock-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            Where To?
          </div>
          <div class="planner-dock-val" id="dockDestVal">Jaipur, Rajasthan</div>
        </div>

        <!-- Segment 2: Who's Traveling? -->
        <div class="planner-dock-item" onclick="switchPlannerStep(1); document.getElementById('planAdultsVal')?.scrollIntoView({behavior:'smooth', block:'center'});">
          <div class="planner-dock-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            Who's Coming?
          </div>
          <div class="planner-dock-val" id="dockPaxVal">2 Adults • 1 Room</div>
        </div>

        <!-- Segment 3: Duration -->
        <div class="planner-dock-item" onclick="switchPlannerStep(1); document.getElementById('planDaysCount')?.focus();">
          <div class="planner-dock-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Duration
          </div>
          <div class="planner-dock-val" id="dockDurationVal">5 Days • Flexible ±3d</div>
        </div>

        <!-- Segment 4: Budget & Style -->
        <div class="planner-dock-item" onclick="switchPlannerStep(2); document.getElementById('planCustomBudgetInput')?.focus();">
          <div class="planner-dock-label">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Budget &amp; Style
          </div>
          <div class="planner-dock-val" id="dockBudgetVal">₹50,000 • Balanced</div>
        </div>

        <!-- CTA -->
        <button type="button" class="planner-dock-cta" id="btnDockExplore" onclick="document.getElementById('btnGenerateDynamicPlans')?.click();">
          <span>⚡ Plan My Trip</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
    </div>

    <!-- 3. Natural Language AI Assistant Box -->
    <div style="max-width: 1200px; margin: 0 auto 48px; padding: 0 24px;">
      <div class="ai-assistant-container" style="box-shadow: 0 16px 40px rgba(22, 45, 60, 0.08); border-radius: 20px;">
        <div class="ai-assistant-header">
          <div class="ai-assistant-title">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D4AF37" stroke-width="2.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            <span>Describe Your Dream Voyage in Plain English</span>
          </div>
          <span class="ai-assistant-badge">Intelligent Intent Parser</span>
        </div>
        <p style="font-size: 13.5px; color: var(--color-muted-grey); margin-bottom: 12px; line-height: 1.5;">
          Type or paste your travel plans freely (any party size, custom duration 1–60+ days, custom budget, must-see sights). Our AI engine extracts route parameters, calculates room &amp; vehicle sizing, and auto-populates your itinerary.
        </p>
        <textarea 
          id="aiPromptInput" 
          class="ai-assistant-textarea" 
          placeholder="e.g. Planning a 5-day cultural trip to Udaipur for 4 friends next month with a budget of ₹60,000. We prefer heritage hotels and private cabs."
        ></textarea>
        <div class="ai-prompt-chips">
          <span style="font-size: 11.5px; font-weight: 700; color: var(--color-muted-grey); align-self: center;">Try sample:</span>
          <button type="button" class="ai-prompt-chip" data-sample="Solo budget exploration in Jaipur for 2 days under ₹3,000 using express trains">Solo 2-Day Jaipur under ₹3k</button>
          <button type="button" class="ai-prompt-chip" data-sample="12 college friends visiting Goa for 5 days with a budget of ₹1.2 Lakh total, beach villas and party hubs">12 Friends Goa 5 Days (₹1.2L)</button>
          <button type="button" class="ai-prompt-chip" data-sample="Family vacation to Munnar Kerala with 4 adults and 2 children for 7 days, luxury tea garden resort and Innova cab">Family of 6 to Munnar (7 Days)</button>
          <button type="button" class="ai-prompt-chip" data-sample="Luxury anniversary getaway to Srinagar Kashmir for 2 adults, 5 days, 5-star palace, Dal lake houseboat, private chauffeur">Luxury Couple Kashmir (5 Days)</button>
          <button type="button" class="ai-prompt-chip" data-sample="Manali mountain trek for 4 friends, 4 days, ₹15,000 total budget, scenic views and adventure">4 Friends Manali Trek (₹15k)</button>
        </div>
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
          <button type="button" class="btn-primary-luxury" id="btnParseAiPrompt" style="padding: 12px 26px; font-size: 14px;">
            <span>✨ Parse &amp; Auto-Configure Itinerary</span>
          </button>
          <span id="aiParserStatus" style="font-size: 12px; color: var(--color-muted-grey);"></span>
        </div>
        <div id="aiIntentCard" class="ai-intent-card">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(42,127,186,0.15); padding-bottom: 8px;">
            <strong style="color: var(--color-primary-blue); font-size: 13.5px;">✓ AI Extracted Journey Parameters</strong>
            <span id="aiFeasibilityBadge" style="font-size: 11.5px; font-weight: 700;"></span>
          </div>
          <div class="ai-intent-grid" id="aiIntentGrid">
            <!-- Populated dynamically -->
          </div>
        </div>
      </div>
    </div>

    <!-- 4. Destination Discovery Gallery (High-Impact Visual Cards) -->
    <div class="dest-discovery-wrap">
      <div class="dest-discovery-header">
        <div>
          <div class="section-eyebrow">Instant Inspiration</div>
          <h3 style="font-family: var(--font-serif); font-size: 28px; color: var(--color-deep-navy); margin: 0;">Featured Enclaves Ready for Instant Planning</h3>
        </div>
        <p style="font-size: 13.5px; color: var(--color-muted-grey); margin: 0; max-width: 480px;">
          Click any enclave to load certified route coordinates, live weather, and audited regional suppliers directly into your planner.
        </p>
      </div>

      <div class="dest-grid-cards">
        <!-- Card 1: Jaipur -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Jaipur, Rajasthan', 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg/1200px-East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg/1200px-East_facade_Hawa_Mahal_Jaipur_from_ground_level_%28July_2022%29_-_img_01.jpg" alt="Jaipur Rajasthan">
            <span class="dest-card-badge">Royal Heritage</span>
            <span class="dest-card-price-pill">From ₹3,800 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Rajasthan, India</div>
              <h4 class="dest-card-title">Jaipur, The Pink City</h4>
              <p class="dest-card-desc">Centuries-old Rajput fortresses, Amber Palace courtyards, and astronomical observatories.</p>
            </div>
            <div class="dest-card-footer">
              <span>☀️ 28°C Sunny • Oct–Mar</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>

        <!-- Card 2: Srinagar -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Srinagar, Kashmir', 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Nigeen_Lake_Srinagar.jpg/1200px-Nigeen_Lake_Srinagar.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Nigeen_Lake_Srinagar.jpg/1200px-Nigeen_Lake_Srinagar.jpg" alt="Srinagar Kashmir">
            <span class="dest-card-badge">Alpine Serenity</span>
            <span class="dest-card-price-pill">From ₹4,500 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Jammu &amp; Kashmir</div>
              <h4 class="dest-card-title">Srinagar &amp; Dal Lake</h4>
              <p class="dest-card-desc">Carved cedarwood houseboats, Mughal pleasure gardens, and snow-draped Pir Panjal peaks.</p>
            </div>
            <div class="dest-card-footer">
              <span>🌤️ 16°C Crisp • Apr–Oct</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>

        <!-- Card 3: Munnar -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Munnar, Kerala', 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Tea_plantations_in_Munnar.jpg/1200px-Tea_plantations_in_Munnar.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Tea_plantations_in_Munnar.jpg/1200px-Tea_plantations_in_Munnar.jpg" alt="Munnar Kerala">
            <span class="dest-card-badge">Tea Sanctuaries</span>
            <span class="dest-card-price-pill">From ₹3,200 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Kerala Western Ghats</div>
              <h4 class="dest-card-title">Munnar Misty Hills</h4>
              <p class="dest-card-desc">Rolling emerald tea estates, spice plantations, and Ayurvedic wellness hideaways.</p>
            </div>
            <div class="dest-card-footer">
              <span>🌿 21°C Mist • Sep–May</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>

        <!-- Card 4: Goa -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Goa, India', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Dudhsagar_Falls_Goa_India.jpg/1200px-Dudhsagar_Falls_Goa_India.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Dudhsagar_Falls_Goa_India.jpg/1200px-Dudhsagar_Falls_Goa_India.jpg" alt="Goa India">
            <span class="dest-card-badge">Coastal &amp; Portuguese</span>
            <span class="dest-card-price-pill">From ₹2,900 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Goan Coastline</div>
              <h4 class="dest-card-title">Goa Sands &amp; Havelis</h4>
              <p class="dest-card-desc">Golden sandy beaches, 16th-century Latin quarters of Fontainhas, and seafood trails.</p>
            </div>
            <div class="dest-card-footer">
              <span>🌊 30°C Tropical • Nov–Feb</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>

        <!-- Card 5: Varanasi -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Varanasi, Uttar Pradesh', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Ahilya_Ghat_by_the_Ganges%2C_Varanasi.jpg/1200px-Ahilya_Ghat_by_the_Ganges%2C_Varanasi.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Ahilya_Ghat_by_the_Ganges%2C_Varanasi.jpg/1200px-Ahilya_Ghat_by_the_Ganges%2C_Varanasi.jpg" alt="Varanasi Ganges">
            <span class="dest-card-badge">Sacred Corridor</span>
            <span class="dest-card-price-pill">From ₹2,400 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Uttar Pradesh</div>
              <h4 class="dest-card-title">Varanasi Sacred Ghats</h4>
              <p class="dest-card-desc">Sunrise boat journeys on Mother Ganga, Dashashwamedh evening aarti, and silk weavers.</p>
            </div>
            <div class="dest-card-footer">
              <span>🪔 24°C Pleasant • Oct–Mar</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>

        <!-- Card 6: Leh Ladakh -->
        <div class="dest-card-luxury" onclick="selectDestinationEnclave('Leh, Ladakh', 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Leh_Palace_and_Namgyal_Tsemo_Monastery.jpg/1200px-Leh_Palace_and_Namgyal_Tsemo_Monastery.jpg')">
          <div class="dest-card-thumb-wrap">
            <img class="dest-card-thumb" src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Leh_Palace_and_Namgyal_Tsemo_Monastery.jpg/1200px-Leh_Palace_and_Namgyal_Tsemo_Monastery.jpg" alt="Leh Ladakh">
            <span class="dest-card-badge">High Altitude</span>
            <span class="dest-card-price-pill">From ₹5,200 / day</span>
          </div>
          <div class="dest-card-body">
            <div>
              <div class="dest-card-region">Ladakh Territory</div>
              <h4 class="dest-card-title">Leh &amp; Pangong Tso</h4>
              <p class="dest-card-desc">High-altitude Buddhist monasteries, Khardung La pass, and crystalline blue glacial lakes.</p>
            </div>
            <div class="dest-card-footer">
              <span>🏔️ 12°C Alpine • May–Sep</span>
              <button class="btn-card-select">Select Enclave &rarr;</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. Elevated Planning Console (Step 1, Step 2, Step 3) -->
    <div style="max-width: 1240px; margin: 0 auto; padding: 0 24px;">
      
      <!-- Luxury Progress Stepper -->
      <div class="luxury-stepper-wrap" role="tablist">
        <div class="luxury-stepper-track"></div>
        <div class="luxury-stepper-item active" id="stepIndicator1" onclick="switchPlannerStep(1)">
          <div class="luxury-stepper-circle">1</div>
          <span class="luxury-stepper-label">Route, Party &amp; Dates</span>
        </div>
        <div class="luxury-stepper-item" id="stepIndicator2" onclick="switchPlannerStep(2)">
          <div class="luxury-stepper-circle">2</div>
          <span class="luxury-stepper-label">Preferences &amp; Custom Budget</span>
        </div>
        <div class="luxury-stepper-item" id="stepIndicator3" onclick="switchPlannerStep(3)">
          <div class="luxury-stepper-circle">3</div>
          <span class="luxury-stepper-label">Verified Journey Plans</span>
        </div>
      </div>

      <div class="planner-card-elevated">
        <!-- Step 1 Panel: Destination, Party Size & Dates -->
        <div class="planner-step-panel active" id="plannerStep1">
          <!-- Origin & Destination -->
          <div class="planner-grid-2col" style="margin-bottom: 28px;">
            <div class="planner-field">
              <label class="planner-label" for="planOriginInput">Starting City / Origin</label>
              <div class="planner-input-wrap">
                <input 
                  type="text" 
                  class="planner-input" 
                  id="planOriginInput" 
                  placeholder="e.g. New Delhi, Mumbai, Bengaluru" 
                  value="New Delhi" 
                  autocomplete="off"
                >
              </div>
              <div class="planner-autocomplete-dropdown" id="planOriginDropdown"></div>
              <div class="quick-pill-row">
                <span class="quick-pill" onclick="setOrigin('New Delhi')">Delhi</span>
                <span class="quick-pill" onclick="setOrigin('Mumbai')">Mumbai</span>
                <span class="quick-pill" onclick="setOrigin('Bengaluru')">Bengaluru</span>
                <span class="quick-pill" onclick="setOrigin('Kolkata')">Kolkata</span>
                <span class="quick-pill" onclick="setOrigin('Chennai')">Chennai</span>
              </div>
            </div>

            <div class="planner-field">
              <label class="planner-label" for="planDestInput">Destination (Any Worldwide Enclave)</label>
              <div class="planner-input-wrap">
                <input 
                  type="text" 
                  class="planner-input" 
                  id="planDestInput" 
                  placeholder="e.g. Jaipur, Kashmir, Goa, Munnar, Leh" 
                  value="Jaipur, Rajasthan" 
                  autocomplete="off"
                >
              </div>
              <div class="planner-autocomplete-dropdown" id="planDestDropdown"></div>
              <div class="quick-pill-row">
                <span class="quick-pill" onclick="setDestination('Jaipur, Rajasthan')">Jaipur</span>
                <span class="quick-pill" onclick="setDestination('Srinagar, Kashmir')">Kashmir</span>
                <span class="quick-pill" onclick="setDestination('Goa, India')">Goa</span>
                <span class="quick-pill" onclick="setDestination('Munnar, Kerala')">Munnar</span>
                <span class="quick-pill" onclick="setDestination('Varanasi, Uttar Pradesh')">Varanasi</span>
                <span class="quick-pill" onclick="setDestination('Leh, Ladakh')">Leh</span>
              </div>
            </div>
          </div>

          <!-- Custom Party Size & Accommodation Allocation -->
          <div style="background: rgba(22,45,60,0.02); border: 1px solid rgba(22,45,60,0.08); border-radius: 18px; padding: 24px; margin-bottom: 28px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
              <div>
                <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-sky-blue);">Party Architecture &amp; Room Sizing</span>
                <h4 style="font-size: 16px; font-weight: 700; color: var(--color-deep-navy); margin: 2px 0 0;">Custom Travelers &amp; Dedicated Rooms</h4>
              </div>
              <div id="planVehiclePill" class="vehicle-capacity-pill">
                🚗 Assigned Vehicle: Sedan (1–3 Pax: Dzire / Etios)
              </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px; margin-bottom: 20px;">
              <!-- Adults -->
              <div>
                <label class="planner-label" style="font-size: 12px;">Adults (12+ yrs)</label>
                <div class="stepper-counter-group">
                  <button type="button" class="btn-step-count" onclick="changeCount('planAdults', -1)">&minus;</button>
                  <span class="step-count-display" id="planAdultsVal">2</span>
                  <button type="button" class="btn-step-count" onclick="changeCount('planAdults', 1)">+</button>
                  <input type="hidden" id="planAdults" value="2">
                </div>
              </div>

              <!-- Children -->
              <div>
                <label class="planner-label" style="font-size: 12px;">Children (2–12 yrs)</label>
                <div class="stepper-counter-group">
                  <button type="button" class="btn-step-count" onclick="changeCount('planChildren', -1)">&minus;</button>
                  <span class="step-count-display" id="planChildrenVal">0</span>
                  <button type="button" class="btn-step-count" onclick="changeCount('planChildren', 1)">+</button>
                  <input type="hidden" id="planChildren" value="0">
                </div>
              </div>

              <!-- Infants -->
              <div>
                <label class="planner-label" style="font-size: 12px;">Infants (&lt; 2 yrs)</label>
                <div class="stepper-counter-group">
                  <button type="button" class="btn-step-count" onclick="changeCount('planInfants', -1)">&minus;</button>
                  <span class="step-count-display" id="planInfantsVal">0</span>
                  <button type="button" class="btn-step-count" onclick="changeCount('planInfants', 1)">+</button>
                  <input type="hidden" id="planInfants" value="0">
                </div>
              </div>

              <!-- Rooms Required -->
              <div>
                <label class="planner-label" style="font-size: 12px;">Rooms Required</label>
                <div class="stepper-counter-group">
                  <button type="button" class="btn-step-count" onclick="changeCount('planRooms', -1)">&minus;</button>
                  <span class="step-count-display" id="planRoomsVal">1</span>
                  <button type="button" class="btn-step-count" onclick="changeCount('planRooms', 1)">+</button>
                  <input type="hidden" id="planRooms" value="1">
                </div>
              </div>
            </div>

            <!-- Room Sharing Preference & Special Requirements -->
            <div class="planner-grid-2col" style="margin-bottom: 12px;">
              <div class="planner-field">
                <label class="planner-label" for="planRoomSharing" style="font-size: 12px;">Room Sharing Preference</label>
                <select class="planner-select" id="planRoomSharing" onchange="recalcParty()">
                  <option value="DOUBLE" selected>Double Occupancy (Standard: 2 Adults / Room)</option>
                  <option value="SINGLE">Single Occupancy (1 Room per Adult)</option>
                  <option value="TRIPLE">Triple Sharing (Budget/Group: 3 Adults / Room)</option>
                  <option value="FAMILY_SUITE">Family Suite / Connected Inter-leading Rooms</option>
                </select>
              </div>

              <div class="planner-field">
                <label class="planner-label" style="font-size: 12px;">Special Group Considerations</label>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px;">
                  <label style="font-size: 12px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: var(--color-deep-navy);">
                    <input type="checkbox" id="specSenior"> 🧓 Senior / Accessible
                  </label>
                  <label style="font-size: 12px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: var(--color-deep-navy);">
                    <input type="checkbox" id="specPet"> 🐾 Pet Friendly
                  </label>
                  <label style="font-size: 12px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: var(--color-deep-navy);">
                    <input type="checkbox" id="specDiet"> 🥗 Pure Veg / Jain
                  </label>
                  <label style="font-size: 12px; display: inline-flex; align-items: center; gap: 4px; cursor: pointer; color: var(--color-deep-navy);">
                    <input type="checkbox" id="specChild"> 🍼 Crib / Child-Safe
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Custom Duration & Flexible Dates -->
          <div style="background: rgba(22,45,60,0.02); border: 1px solid rgba(22,45,60,0.08); border-radius: 18px; padding: 24px; margin-bottom: 28px;">
            <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-sky-blue);">Timeline &amp; Calendar Flexibility</span>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--color-deep-navy); margin: 2px 0 14px;">Custom Duration (1 to 60+ Days)</h4>

            <div class="planner-grid-3col">
              <div class="planner-field">
                <label class="planner-label" for="planStartDate">Departure Date</label>
                <input type="date" class="planner-input" id="planStartDate">
              </div>

              <div class="planner-field">
                <label class="planner-label" for="planDaysCount">Duration (Days)</label>
                <div class="stepper-counter-group">
                  <button type="button" class="btn-step-count" onclick="changeDays(-1)">&minus;</button>
                  <input type="number" id="planDaysCount" class="planner-input" style="text-align: center; font-weight: 800; max-width: 90px;" min="1" max="90" value="5">
                  <button type="button" class="btn-step-count" onclick="changeDays(1)">+</button>
                </div>
                <div class="duration-presets-row">
                  <button type="button" class="duration-preset-btn" onclick="selectDurationPreset(3)">3D Weekend</button>
                  <button type="button" class="duration-preset-btn active" onclick="selectDurationPreset(5)">5D Cultural</button>
                  <button type="button" class="duration-preset-btn" onclick="selectDurationPreset(7)">7D Circuit</button>
                  <button type="button" class="duration-preset-btn" onclick="selectDurationPreset(10)">10D Panorama</button>
                  <button type="button" class="duration-preset-btn" onclick="selectDurationPreset(14)">14D Immersion</button>
                </div>
              </div>

              <div class="planner-field">
                <label class="planner-label" for="planEndDate">Return Date (Auto-Calculated)</label>
                <input type="date" class="planner-input" id="planEndDate" readonly style="background: rgba(22,45,60,0.04);">
              </div>
            </div>

            <div style="margin-top: 14px;">
              <label style="font-size: 12.5px; display: inline-flex; align-items: center; gap: 6px; cursor: pointer; color: var(--color-deep-navy);">
                <input type="checkbox" id="planFlexibleDates" checked>
                <span><strong>Flexible Travel Dates (&plusmn;3 Days)</strong> &mdash; Unlock up to 25% lower airfares and off-peak boutique hotel rates.</span>
              </label>
            </div>
          </div>

          <!-- Visual Transportation Preference Cards -->
          <div class="planner-field" style="margin-bottom: 28px;">
            <label class="planner-label">Preferred Transportation Mode</label>
            <input type="hidden" id="planTransitMode" value="HIGH_SPEED_RAIL">
            <div class="pref-cards-grid" id="transitCardsGrid">
              <div class="pref-visual-card active" data-transit="HIGH_SPEED_RAIL" onclick="selectTransitCard('HIGH_SPEED_RAIL')">
                <div class="pref-card-icon">🚄</div>
                <h5 class="pref-card-title">Vande Bharat Express</h5>
                <p class="pref-card-sub">Executive AC chair car &bull; City-center to center speed</p>
              </div>

              <div class="pref-visual-card" data-transit="FLIGHT_EXPRESS" onclick="selectTransitCard('FLIGHT_EXPRESS')">
                <div class="pref-card-icon">✈️</div>
                <h5 class="pref-card-title">Express Flight + Chauffeur</h5>
                <p class="pref-card-sub">Commercial express flight &bull; Dedicated airport pickup</p>
              </div>

              <div class="pref-visual-card" data-transit="PRIVATE_CHAUFFEUR" onclick="selectTransitCard('PRIVATE_CHAUFFEUR')">
                <div class="pref-card-icon">🚗</div>
                <h5 class="pref-card-title">Private Intercity Cab</h5>
                <p class="pref-card-sub">Innova Crysta / Mercedes &bull; Door-to-door flexibility</p>
              </div>

              <div class="pref-visual-card" data-transit="SELF_DRIVE" onclick="selectTransitCard('SELF_DRIVE')">
                <div class="pref-card-icon">🚙</div>
                <h5 class="pref-card-title">Self-Drive Premium SUV</h5>
                <p class="pref-card-sub">Unlimited mileage &bull; GPS navigation &bull; Full assurance</p>
              </div>

              <div class="pref-visual-card" data-transit="HERITAGE_TRAIN" onclick="selectTransitCard('HERITAGE_TRAIN')">
                <div class="pref-card-icon">👑</div>
                <h5 class="pref-card-title">Heritage Luxury Train</h5>
                <p class="pref-card-sub">Palace on Wheels corridor &bull; Royal salon staterooms</p>
              </div>
            </div>
          </div>

          <div style="display: flex; justify-content: flex-end;">
            <button class="btn-primary-luxury" id="btnStep1Next" style="padding: 16px 36px; font-size: 15px;">
              <span>Continue to Preferences &amp; Budget &rarr;</span>
            </button>
          </div>
        </div>

        <!-- Step 2 Panel: Preferences & Custom Budget -->
        <div class="planner-step-panel" id="plannerStep2">
          <!-- Custom Budget Switcher & Feasibility Card -->
          <div style="background: rgba(22,45,60,0.02); border: 1px solid rgba(22,45,60,0.08); border-radius: 18px; padding: 24px; margin-bottom: 28px;">
            <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-sky-blue);">Financial Calibration</span>
            <h4 style="font-size: 16px; font-weight: 700; color: var(--color-deep-navy); margin: 2px 0 14px;">Custom Budget Configuration &amp; Real-Time Feasibility</h4>

            <div class="budget-mode-switcher">
              <button type="button" class="budget-mode-btn active" id="btnBudgetModeTotal" onclick="setBudgetMode('TOTAL')">Total Trip Budget</button>
              <button type="button" class="budget-mode-btn" id="btnBudgetModePerson" onclick="setBudgetMode('PER_PERSON')">Per Person</button>
              <button type="button" class="budget-mode-btn" id="btnBudgetModeDaily" onclick="setBudgetMode('PER_DAY')">Daily Average</button>
            </div>

            <div class="planner-grid-3col" style="margin-top: 14px;">
              <div class="planner-field">
                <label class="planner-label" for="planCustomBudgetInput" id="budgetInputLabel">Target Budget (Total Trip - INR ₹)</label>
                <input 
                  type="number" 
                  class="planner-input" 
                  id="planCustomBudgetInput" 
                  placeholder="e.g. 50000" 
                  value="50000"
                  min="500"
                  oninput="evalBudgetFeasibility(); syncBudgetSliderFromInput();"
                >
              </div>

              <div class="planner-field">
                <label class="planner-label" for="planCurrencySelect">Display Currency</label>
                <select class="planner-select" id="planCurrencySelect" onchange="syncCurrencySelection(this.value)">
                  <option value="INR" selected>INR (₹) - Indian Rupee</option>
                  <option value="USD">USD ($) - US Dollar</option>
                  <option value="EUR">EUR (€) - Euro</option>
                  <option value="GBP">GBP (£) - British Pound</option>
                  <option value="AED">AED (AED) - UAE Dirham</option>
                </select>
              </div>

              <div class="planner-field">
                <label class="planner-label" for="planPace">Travel Pacing</label>
                <select class="planner-select" id="planPace">
                  <option value="RELAXED">Relaxed (1-2 highlights daily + leisure)</option>
                  <option value="BALANCED" selected>Balanced (Curated sights + free evenings)</option>
                  <option value="PACKED">Intensive (Full-day immersive exploration)</option>
                </select>
              </div>
            </div>

            <!-- Modern Interactive Range Slider -->
            <div class="budget-slider-wrap">
              <input type="range" class="budget-slider" id="planBudgetSlider" min="5000" max="300000" step="2500" value="50000" oninput="syncBudgetInputFromSlider()">
              <div class="slider-ticks">
                <span>₹5,000 (Value)</span>
                <span>₹50,000</span>
                <span>₹1,50,000 (Comfortable)</span>
                <span>₹3,00,000+ (Signature Luxury)</span>
              </div>
            </div>

            <!-- Dynamic Feasibility Evaluation Box -->
            <div id="feasibilityCard" class="feasibility-card status-feasible" style="display: flex;">
              <!-- Populated by evalBudgetFeasibility() -->
            </div>
          </div>

          <!-- Visual Accommodation Standard Cards -->
          <div class="planner-field" style="margin-bottom: 28px;">
            <label class="planner-label">Preferred Accommodation Standard</label>
            <div class="chip-group" id="stayChips" style="display: none;">
              <button type="button" class="chip-btn" data-val="HERITAGE_PALACE">👑 5-Star Heritage Palace / Fort</button>
              <button type="button" class="chip-btn active" data-val="BOUTIQUE_LUXURY">✨ Boutique Luxury Sanctuary</button>
              <button type="button" class="chip-btn" data-val="PREMIUM_HOTEL">🏨 4-Star Premium Hotel</button>
              <button type="button" class="chip-btn" data-val="SAFARI_LODGE">🌿 Eco-Safari Wilderness Lodge</button>
              <button type="button" class="chip-btn" data-val="HOUSEBOAT_SANCTUARY">⛵ Houseboat / Lake Villa</button>
            </div>
            
            <div class="pref-cards-grid" id="stayCardsGrid">
              <div class="pref-visual-card" data-stay="HERITAGE_PALACE" onclick="selectStayCard('HERITAGE_PALACE')">
                <div class="pref-card-icon">👑</div>
                <h5 class="pref-card-title">5★ Heritage Palace &amp; Fort</h5>
                <p class="pref-card-sub">Taj &amp; Oberoi royal suites &bull; Historic architecture</p>
              </div>

              <div class="pref-visual-card active" data-stay="BOUTIQUE_LUXURY" onclick="selectStayCard('BOUTIQUE_LUXURY')">
                <div class="pref-card-icon">✨</div>
                <h5 class="pref-card-title">Boutique Luxury Sanctuary</h5>
                <p class="pref-card-sub">Handpicked private havelis &bull; High personalized service</p>
              </div>

              <div class="pref-visual-card" data-stay="PREMIUM_HOTEL" onclick="selectStayCard('PREMIUM_HOTEL')">
                <div class="pref-card-icon">🏨</div>
                <h5 class="pref-card-title">4★ Premium Hotel</h5>
                <p class="pref-card-sub">Contemporary comfort, pool &amp; central enclave location</p>
              </div>

              <div class="pref-visual-card" data-stay="SAFARI_LODGE" onclick="selectStayCard('SAFARI_LODGE')">
                <div class="pref-card-icon">🌿</div>
                <h5 class="pref-card-title">Eco-Wilderness Safari Lodge</h5>
                <p class="pref-card-sub">National parks, wildlife corridors &bull; Natural serenity</p>
              </div>

              <div class="pref-visual-card" data-stay="HOUSEBOAT_SANCTUARY" onclick="selectStayCard('HOUSEBOAT_SANCTUARY')">
                <div class="pref-card-icon">⛵</div>
                <h5 class="pref-card-title">Houseboat / Lake Villa</h5>
                <p class="pref-card-sub">Private cedarwood houseboat or backwaters sanctuary</p>
              </div>
            </div>
          </div>

          <!-- Curated Interests -->
          <div class="planner-field" style="margin-bottom: 24px;">
            <label class="planner-label">Travel Style &amp; Curated Interests (Select Multiple)</label>
            <div class="chip-group" id="interestChips">
              <button type="button" class="chip-btn active" data-val="CULTURAL_HERITAGE">🏛️ Cultural &amp; Heritage</button>
              <button type="button" class="chip-btn active" data-val="LOCAL_CUISINE">🍽️ Local Gastronomy</button>
              <button type="button" class="chip-btn" data-val="WILDLIFE_SAFARI">🐅 Wildlife &amp; National Parks</button>
              <button type="button" class="chip-btn" data-val="MOUNTAIN_EXPEDITIONS">🏔️ Mountain Expeditions</button>
              <button type="button" class="chip-btn" data-val="WELLNESS_AYURVEDA">🧘 Wellness &amp; Ayurveda</button>
              <button type="button" class="chip-btn" data-val="SPIRITUAL_SANCTUARY">🪔 Sacred Corridors</button>
              <button type="button" class="chip-btn" data-val="COASTAL_BEACHES">🌊 Coastal &amp; Beaches</button>
              <button type="button" class="chip-btn" data-val="ROMANCE_LUXURY">✨ Romance &amp; Honeymoon</button>
              <button type="button" class="chip-btn" data-val="PHOTOGRAPHY_ARTS">📷 Photography &amp; Arts</button>
              <button type="button" class="chip-btn" data-val="RURAL_HOMESTAYS">🏡 Village &amp; Eco-Living</button>
            </div>
          </div>

          <!-- Must-Visit Sights / Custom Activity Requests -->
          <div class="planner-field" style="margin-bottom: 28px;">
            <label class="planner-label" for="planCustomMustVisit">Must-See Attractions or Specific Requests (Optional)</label>
            <input 
              type="text" 
              class="planner-input" 
              id="planCustomMustVisit" 
              placeholder="e.g. Amber Fort sunrise elephant watch, scuba diving, private culinary workshop"
            >
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center;">
            <button class="btn-secondary-luxury" id="btnStep2Back">
              <span>&larr; Back to Route</span>
            </button>
            <button class="btn-primary-luxury" id="btnGenerateDynamicPlans" style="padding: 16px 40px; font-size: 15px;">
              <span>⚡ Generate Verified Travel Plans &rarr;</span>
            </button>
          </div>
        </div>

        <!-- Step 3 Panel: Dynamic 3-Tier Results -->
        <div class="planner-step-panel" id="plannerStep3">
          <!-- Authentic Destination Photo Showcase Banner -->
          <div class="dest-showcase-banner" id="destShowcaseBanner" style="display: none;">
            <img class="dest-showcase-img" id="destShowcaseImg" src="" alt="Destination Photograph">
            <div class="dest-showcase-overlay">
              <span class="dest-attribution-badge" id="destAttributionBadge">Wikimedia Commons</span>
              <h3 id="destShowcaseTitle" style="font-family: var(--font-serif); font-size: 26px; margin: 0 0 6px; color: #FFFFFF;">Destination</h3>
              <p id="destShowcaseDesc" style="font-size: 13px; color: rgba(255,255,255,0.9); margin: 0; max-width: 780px; line-height: 1.4;"></p>
            </div>
          </div>

          <!-- Dynamic Quote Meta Bar & In-Place Quick Adjustment -->
          <div class="quote-meta-bar" id="quoteMetaBar">
            <div>
              <div class="quote-route-title" id="quoteRouteTitle">New Delhi &rarr; Jaipur, Rajasthan</div>
              <div class="quote-route-sub" id="quoteRouteSub">5 Days &bull; 2 Adults &bull; 268 km via Express Rail &bull; Live Weather: 28°C Sunny</div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
              <span class="price-status-badge badge-live" id="quoteStatusBadge">
                <span class="badge-dot"></span> Live Verified
              </span>
              <button class="btn-secondary-luxury" id="btnModifyPlan" style="padding: 8px 16px; font-size: 12px;">
                Modify Parameters
              </button>
            </div>
          </div>

          <!-- Quick In-Place Adjustment Bar -->
          <div style="background: rgba(22,45,60,0.03); border: 1px solid rgba(22,45,60,0.08); border-radius: 14px; padding: 14px 20px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
            <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
              <span style="font-size: 12px; font-weight: 700; color: var(--color-deep-navy);">Quick Adjust:</span>
              <!-- Adjust Travelers -->
              <div style="display: flex; align-items: center; gap: 6px;">
                <button type="button" class="btn-step-count" style="width: 28px; height: 28px; font-size: 14px;" onclick="quickAdjustTravelers(-1)">&minus;</button>
                <span id="quickPaxDisplay" style="font-weight: 700; font-size: 13.5px; min-width: 75px; text-align: center;">2 Travelers</span>
                <button type="button" class="btn-step-count" style="width: 28px; height: 28px; font-size: 14px;" onclick="quickAdjustTravelers(1)">+</button>
              </div>

              <!-- Adjust Duration -->
              <div style="display: flex; align-items: center; gap: 6px;">
                <button type="button" class="btn-step-count" style="width: 28px; height: 28px; font-size: 14px;" onclick="quickAdjustDays(-1)">&minus;</button>
                <span id="quickDaysDisplay" style="font-weight: 700; font-size: 13.5px; min-width: 65px; text-align: center;">5 Days</span>
                <button type="button" class="btn-step-count" style="width: 28px; height: 28px; font-size: 14px;" onclick="quickAdjustDays(1)">+</button>
              </div>
            </div>

            <button type="button" class="btn-primary-luxury" id="btnQuickRecalculate" onclick="recalculateActiveJourney()" style="padding: 8px 18px; font-size: 12.5px;">
              <span>Recalculate Instantly &rarr;</span>
            </button>
          </div>

          <!-- 3-Tier Travel Options Grid -->
          <div class="plans-tier-grid" id="plansTierGrid">
            <!-- Rendered dynamically by JavaScript with rationales -->
          </div>

          <!-- Interactive Day-by-Day Timeline Drawer -->
          <div class="timeline-container" id="timelineContainer" style="margin-top: 36px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 8px;">
              <div>
                <div class="section-eyebrow" style="margin-bottom: 4px;">Dynamic Itinerary Schedule</div>
                <h3 style="font-family: var(--font-serif); font-size: 24px; color: var(--color-deep-navy); margin: 0;">Day-by-Day Timeline</h3>
              </div>
              <span style="font-size: 12.5px; color: var(--color-muted-grey); font-weight: 600;" id="timelineTierLabel">Showing: Balanced Heritage (Recommended)</span>
            </div>

            <div class="itinerary-timeline" id="itineraryTimelineSlots">
              <!-- Rendered dynamically by JavaScript with slot-edit buttons -->
            </div>
          </div>

          <!-- Price Breakdown Matrix Table -->
          <div style="margin-top: 40px;">
            <div class="section-eyebrow" style="margin-bottom: 4px;">Transparent Supplier Auditing</div>
            <h3 style="font-family: var(--font-serif); font-size: 24px; color: var(--color-deep-navy); margin-bottom: 16px;">Comprehensive Price Breakdown</h3>
            <div style="overflow-x: auto;">
              <table class="price-breakdown-table">
                <thead>
                  <tr>
                    <th>Expense Component</th>
                    <th>Plan A (Budget)</th>
                    <th>Plan B (Balanced - Recommended)</th>
                    <th>Plan C (Signature Luxury)</th>
                    <th>Pricing Methodology &amp; Source</th>
                  </tr>
                </thead>
                <tbody id="priceBreakdownBody">
                  <!-- Rendered dynamically by JavaScript -->
                </tbody>
              </table>
            </div>
          </div>

          <div style="margin-top: 32px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div style="font-size: 12px; color: var(--color-muted-grey);">
              Audited by TBO Multi-Supplier Engine &bull; Timestamp: <span id="quoteTimestamp">Live</span> &bull; Currency: <span id="quoteCurrencyCode">INR</span>
            </div>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
              <button class="btn-secondary-luxury" id="btnSaveToMyTrips">
                ★ Save to My Trips
              </button>
              <button class="btn-secondary-luxury" id="btnExportPlanSummary">
                Download Itinerary Summary
              </button>
              <button class="btn-primary-luxury" id="btnBookCertified" onclick="alert('Proceeding to TBO Certified Supplier Booking Engine with guaranteed normalized pricing.')">
                Book Verified Journey &rarr;
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
'''

NEW_JS_HELPERS = '''
    // ========================================================
    // MASTER PLANNER VISUAL REDESIGN INTERACTIVE HOOKS
    // ========================================================
    window.selectDestinationEnclave = function(destName, imgUrl) {
      setDestination(destName);
      updateDockSummary();
      const planConsole = document.querySelector('.planner-card-elevated') || document.getElementById('plannerStep1');
      if (planConsole) {
        planConsole.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    };

    window.selectTransitCard = function(mode) {
      const modeInput = document.getElementById('planTransitMode');
      if (modeInput) modeInput.value = mode;
      document.querySelectorAll('#transitCardsGrid .pref-visual-card').forEach(c => {
        if (c.getAttribute('data-transit') === mode) c.classList.add('active');
        else c.classList.remove('active');
      });
      updateDockSummary();
    };

    window.selectStayCard = function(stay) {
      document.querySelectorAll('#stayCardsGrid .pref-visual-card').forEach(c => {
        if (c.getAttribute('data-stay') === stay) c.classList.add('active');
        else c.classList.remove('active');
      });
      // Sync hidden chips
      document.querySelectorAll('#stayChips .chip-btn').forEach(b => {
        if (b.getAttribute('data-val') === stay) b.classList.add('active');
        else b.classList.remove('active');
      });
      updateDockSummary();
    };

    window.selectDurationPreset = function(days) {
      const daysInput = document.getElementById('planDaysCount');
      if (daysInput) daysInput.value = days;
      document.querySelectorAll('.duration-preset-btn').forEach(b => {
        if (b.textContent.startsWith(`${days}D`)) b.classList.add('active');
        else b.classList.remove('active');
      });
      syncDatesFromDays();
      evalBudgetFeasibility();
      updateDockSummary();
    };

    window.syncBudgetInputFromSlider = function() {
      const slider = document.getElementById('planBudgetSlider');
      const input = document.getElementById('planCustomBudgetInput');
      if (slider && input) {
        input.value = slider.value;
        evalBudgetFeasibility();
        updateDockSummary();
      }
    };

    window.syncBudgetSliderFromInput = function() {
      const slider = document.getElementById('planBudgetSlider');
      const input = document.getElementById('planCustomBudgetInput');
      if (slider && input) {
        slider.value = input.value;
        updateDockSummary();
      }
    };

    window.updateDockSummary = function() {
      const dest = document.getElementById('planDestInput')?.value || 'Jaipur, Rajasthan';
      const adults = document.getElementById('planAdults')?.value || '2';
      const rooms = document.getElementById('planRooms')?.value || '1';
      const days = document.getElementById('planDaysCount')?.value || '5';
      const budget = parseFloat(document.getElementById('planCustomBudgetInput')?.value || '50000');

      const destDock = document.getElementById('dockDestVal');
      const paxDock = document.getElementById('dockPaxVal');
      const durDock = document.getElementById('dockDurationVal');
      const budDock = document.getElementById('dockBudgetVal');

      if (destDock) destDock.textContent = dest.split(',')[0];
      if (paxDock) paxDock.textContent = `${adults} Adults • ${rooms} Room${parseInt(rooms,10) > 1 ? 's' : ''}`;
      if (durDock) durDock.textContent = `${days} Days • Flexible ±3d`;
      if (budDock) budDock.textContent = `₹${Math.round(budget).toLocaleString()} • Balanced`;
    };

    // Attach listener to update dock whenever destination or origin change
    document.getElementById('planDestInput')?.addEventListener('input', updateDockSummary);
    document.getElementById('planOriginInput')?.addEventListener('input', updateDockSummary);
    setTimeout(updateDockSummary, 500);
'''

def main():
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Inject PLANNER_CSS into <style>
    if 'MASTER PLANNER REDESIGN: LUXURY EDITORIAL TRAVEL ARCHITECT' not in html:
        style_end = '</style>'
        s_idx = html.find(style_end)
        if s_idx != -1:
            html = html[:s_idx] + PLANNER_CSS + '\n  ' + html[s_idx:]
            print("✓ Injected PLANNER_CSS into <style>")
    else:
        print("Notice: PLANNER_CSS already present in <style>")

    # 2. Replace #plan-journey
    start_tag = '<!-- ========================================================\n       SECTION: COMPLETELY DYNAMIC "PLAN YOUR JOURNEY" ENGINE'
    if start_tag not in html:
        start_tag = '<section class="planner-engine-section" id="plan-journey">'
    
    end_tag = '<!-- ========================================================\n       AI TRIP PLANNER MODAL (INTEGRATED WITH /api/v1/ai/plan-trip)'

    start_idx = html.find(start_tag)
    end_idx = html.find(end_tag)

    if start_idx == -1 or end_idx == -1:
        print("ERROR: Could not locate #plan-journey boundaries in HTML.")
        sys.exit(1)

    html = html[:start_idx] + NEW_PLAN_JOURNEY_HTML.strip() + '\n\n  ' + html[end_idx:]
    print("✓ Replaced #plan-journey with redesigned luxury layout")

    # 3. Add NEW_JS_HELPERS
    if 'MASTER PLANNER VISUAL REDESIGN INTERACTIVE HOOKS' not in html:
        js_end = '</script>\n</body>'
        js_idx = html.find(js_end)
        if js_idx != -1:
            html = html[:js_idx] + NEW_JS_HELPERS + '\n  ' + html[js_idx:]
            print("✓ Added NEW_JS_HELPERS into <script>")

    with open('frontend/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ Saved frontend/index.html")

    # Also sync to root index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✓ Synced root index.html")

if __name__ == '__main__':
    main()
