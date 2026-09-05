import pytest
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

async def get_browser(p):
    """Launches browser with fallback to pre-installed Edge or Chrome if needed."""
    try:
        return await p.chromium.launch(headless=True)
    except Exception:
        try:
            return await p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            return await p.chromium.launch(channel="chrome", headless=True)

@pytest.mark.asyncio
async def test_playwright_dashboard_overview():
    """
    Playwright Test 1: Verify PREVENT UI loads, displays online status,
    and populates active alert queue with 4 preloaded scenarios.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # 1. Assert Title
        title = await page.title()
        assert "PREVENT UI" in title

        # 2. Verify System Status Indicator and SLA badge
        status_text = await page.locator(".nav-system-status .status-text").text_content()
        assert "Engine Online" in status_text

        sla_badge = await page.locator("#sla-badge").text_content()
        assert "< 3.0s" in sla_badge

        # 3. Verify Case Queue has 4 items
        queue_count = await page.locator("#queue-count").text_content()
        assert int(queue_count) >= 4

        # 4. Verify Active Case Banner
        case_title = await page.locator("#case-id-title").text_content()
        assert "CASE-" in case_title

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_red_and_green_flags_display():
    """
    Playwright Test 2: Verify Consolidated Summary, Risk Gauge,
    and Red/Green flag panels render with policy citations.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # Verify Risk Gauge
        score_text = await page.locator("#risk-score-num").text_content()
        score = int(score_text)
        assert 0 <= score <= 100

        # Verify Summary Card
        headline = await page.locator("#summary-headline").text_content()
        assert len(headline) > 10

        confidence = await page.locator("#summary-confidence").text_content()
        assert "Confidence:" in confidence

        # Verify 3-Part Operational Narrative lists
        beginning_count = await page.locator("#summary-beginning-list li").count()
        assert beginning_count >= 1

        events_count = await page.locator("#summary-events-list li").count()
        assert events_count >= 1

        steps_count = await page.locator("#summary-steps-list li").count()
        assert steps_count >= 1

        # Verify Red Flags Count
        red_count = await page.locator("#red-flags-count").text_content()
        assert int(red_count) >= 1

        # Check evidence pointer inside first red flag
        first_evidence = await page.locator("#red-flags-container .flag-evidence").first.text_content()
        assert "Evidence:" in first_evidence

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_agent_tabs_switching():
    """
    Playwright Test 3: Test switching through all 5 cognitive agent tabs
    (Profiling, History, Notes, Policy SOP, Audit Trail).
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # 1. Cust Profiling Tab
        await page.click("button[data-tab='tab-profiling']")
        assert await page.is_visible("#tab-profiling")
        spend_dev = await page.locator("#prof-spend-dev").text_content()
        assert "x" in spend_dev

        # 2. Case History Tab
        await page.click("button[data-tab='tab-history']")
        assert await page.is_visible("#tab-history")
        hist_text = await page.locator("#history-summary-text").text_content()
        assert len(hist_text) > 0

        # 3. Notes Summarizer Tab
        await page.click("button[data-tab='tab-notes']")
        assert await page.is_visible("#tab-notes")
        sentiment = await page.locator("#notes-sentiment-badge").text_content()
        assert "Sentiment:" in sentiment

        # 4. Policy Decision Tab
        await page.click("button[data-tab='tab-policy']")
        assert await page.is_visible("#tab-policy")
        rec_action = await page.locator("#policy-rec-action").text_content()
        assert len(rec_action) > 0

        # 5. Audit Trail Tab
        await page.click("button[data-tab='tab-audit']")
        assert await page.is_visible("#tab-audit")
        timeline_items = await page.locator(".timeline-item").count()
        assert timeline_items >= 5

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_analyst_remediation_action_flow():
    """
    Playwright Test 4: Full E2E analyst action execution flow.
    Clicks 'Freeze Account', enters case notes, confirms modal,
    and asserts case status is updated to RESOLVED BLOCKED.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # Ensure modal is initially hidden
        assert not await page.is_visible("#action-modal:not(.hidden)")

        # Click Freeze Account button
        await page.click("button[data-action='BLOCK_ACCOUNT']")

        # Verify modal opens
        assert await page.is_visible("#action-modal")
        modal_title = await page.locator("#modal-action-title").text_content()
        assert "Freeze Account" in modal_title

        # Fill investigator notes
        await page.fill("#modal-notes", "Automated Playwright Test: Verified credential compromise. Freezing account per SOP-SEC-802.")

        # Confirm and execute
        await page.click("#btn-modal-confirm")

        # Wait for modal to hide
        await page.wait_for_selector("#action-modal", state="hidden")

        # Verify status badge updated
        await page.wait_for_timeout(500)
        status_badge = await page.locator("#case-status-badge").text_content()
        assert "RESOLVED" in status_badge

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_pull_next_case():
    """
    Playwright Test 5: Verify 'Pull Next Case' button loads next unreviewed case.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # Click Pull Next Case
        await page.click("#btn-pull-next")
        await page.wait_for_timeout(400)

        case_id = await page.locator("#case-id-title").text_content()
        assert "CASE-" in case_id

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_policy_chat_qna():
    """
    Playwright Test 6: Verify Policy Chat tab (Gemini 2.5 Pro via Tachyon ADK),
    sends user prompt, displays typing indicator and receives AI policy response.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # 1. Switch to Tab 6 (Policy Chat)
        await page.click("button[data-tab='tab-chat']")
        assert await page.is_visible("#tab-chat")

        # 2. Enter analyst question
        await page.fill("#chat-user-input", "What is the recommended SOP action for this wire fraud?")
        await page.click("#chat-send-btn")

        # 3. Verify analyst message bubble rendered
        await page.wait_for_selector(".chat-bubble.analyst")
        analyst_msg = await page.locator(".chat-bubble.analyst").last.text_content()
        assert "recommended SOP action" in analyst_msg

        # 4. Wait for AI Agent response bubble (Gemini 2.5 Pro)
        await page.wait_for_selector(".chat-bubble.agent", timeout=10000)
        agent_bubble = page.locator(".chat-bubble.agent").last
        agent_text = await agent_bubble.text_content()
        assert len(agent_text) > 15
        assert "SOP" in agent_text or "BLOCK" in agent_text or "account" in agent_text.lower()

        # 5. Verify quick chip interaction
        await page.locator(".quick-chip").first.click()
        await page.wait_for_timeout(500)
        # Verify another message exchange started
        count = await page.locator(".chat-bubble").count()
        assert count >= 3

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_rich_visual_enhancements():
    """
    Playwright Test 7: Verify all 8 Rich Visual Enhancements:
    - Speedometer Radial SVG Gauge
    - Interactive Geolocation Threat Map
    - Multi-Lingual Customer Script (Hindi / Marathi)
    - 1-Click 1930 NCRP Cyber Crime Portal Modal
    - Dark / Light Theme Toggle
    - Branded Official Case Dossier Export Modal
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # 1. Theme Toggle
        theme_btn = page.locator("#btn-theme-toggle")
        assert await theme_btn.is_visible()
        await theme_btn.click()
        has_light = await page.evaluate("document.body.getAttribute('data-theme') === 'light'")
        assert has_light
        await theme_btn.click()
        has_dark = await page.evaluate("!document.body.getAttribute('data-theme')")
        assert has_dark

        # 2. SVG Speedometer Gauge
        meter = page.locator("#gauge-meter-path")
        assert await meter.is_visible()
        offset = await meter.get_attribute("stroke-dashoffset")
        assert offset is not None

        # 3. Geolocation Threat Vector Map
        map_svg = page.locator("#geo-radar-svg")
        assert await map_svg.is_visible()
        dist_pill = await page.locator("#geo-threat-dist-pill").text_content()
        assert "km" in dist_pill

        # 4. Multi-Lingual Customer Script Switcher
        # Switch to Hindi
        await page.click("button.lang-chip[data-lang='hi']")
        script_hi = await page.locator("#summary-script").text_content()
        assert "नमस्ते" in script_hi or "धोखाधड़ी" in script_hi or "बैंक" in script_hi

        # Switch to Marathi
        await page.click("button.lang-chip[data-lang='mr']")
        script_mr = await page.locator("#summary-script").text_content()
        assert "नमस्कार" in script_mr or "बँक" in script_mr

        # Switch back to English
        await page.click("button.lang-chip[data-lang='en']")
        script_en = await page.locator("#summary-script").text_content()
        assert "Good day" in script_en or "Hello" in script_en

        # 5. 1-Click 1930 NCRP Cyber Crime Portal Modal
        await page.click("#btn-open-ncrp")
        await page.wait_for_selector("#ncrp-modal", state="visible")
        victim_val = await page.locator("#ncrp-victim-name").input_value()
        assert len(victim_val) > 3
        amount_val = await page.locator("#ncrp-amount").input_value()
        assert "₹" in amount_val
        await page.click("#btn-ncrp-cancel")
        await page.wait_for_selector("#ncrp-modal", state="hidden")

        # 6. Branded Official Case Dossier Export Modal
        await page.click("#btn-export-dossier")
        assert await page.is_visible("#dossier-modal:not(.hidden)")
        dossier_text = await page.locator("#dossier-print-content").text_content()
        assert "BHARAT FINANCIAL INTELLIGENCE" in dossier_text
        assert "CONFIDENTIAL" in dossier_text
        await page.click("#btn-dossier-cancel")
        await page.wait_for_selector("#dossier-modal", state="hidden")

        await browser.close()

@pytest.mark.asyncio
async def test_playwright_whatif_sandbox_and_mule_topology():
    """
    Playwright Test 8: Verify "What-If" Counterfactual Simulation Sandbox
    and Mule Account Layering Fund Flow Graph.
    """
    async with async_playwright() as p:
        browser = await get_browser(p)
        page = await browser.new_page()
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")

        # 1. Switch to Policy Tab (Tab 4) for What-If Sandbox
        await page.click("button[data-tab='tab-policy']")
        assert await page.is_visible("#tab-policy")

        # Verify What-If card
        assert await page.is_visible(".whatif-sandbox-card")
        init_action = await page.locator("#whatif-sim-action").text_content()
        assert "BLOCK" in init_action or "ACTION" in init_action

        # Turn ON Travel Notification & set biometric slider to 90%
        await page.locator("#whatif-travel").check(force=True)
        await page.fill("#whatif-bio-slider", "90")
        await page.dispatch_event("#whatif-bio-slider", "input")

        # Verify simulated policy reaction shifts to DISMISS_FALSE_POSITIVE
        sim_action = await page.locator("#whatif-sim-action").text_content()
        assert "DISMISS" in sim_action or "FALSE_POSITIVE" in sim_action

        # 2. Switch to Profiling Tab (Tab 1) for Mule Topology
        await page.click("button[data-tab='tab-profiling']")
        assert await page.is_visible("#tab-profiling")
        assert await page.is_visible("#mule-flow-svg")

        await browser.close()

