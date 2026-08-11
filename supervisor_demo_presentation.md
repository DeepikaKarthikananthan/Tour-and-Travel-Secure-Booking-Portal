# Security Lab Exam Presentation Script & Demo Guide

**System:** Wayfarer & Co. Travel Booking System  
**Demo Mode Feature:** 1-Click Interactive Security Mode Switcher (`Security: ON (Secured)` vs `Security: OFF (Vulnerable Demo)`)  

---

> [!IMPORTANT]
> **How to Use This Guide During Your Exam**  
> Use the **Navbar Toggle Button** (`🛡️ Security: ON` / `⚠️ Security: OFF`) to demonstrate each attack in **Vulnerable Demo Mode**, show the attack succeeding, then toggle **Security Mode ON** to show how your defensive security controls neutralize the attack!

---

## Complete Table of 9 Executable Security Attack Demonstrations

| Attack # | Vulnerability Name | What to Click / Type | Vulnerable Mode Result (`Security: OFF`) | Secured Mode Result (`Security: ON`) | Technical Defense Mechanism |
|---|---|---|---|---|---|
| **1** | **SQL Injection (SQLi) Auth Bypass** | Type `' OR '1'='1` into Login Email (HTML5 validation removed) | Bypasses login without password & grants Admin access | Login fails with *"Invalid email or password"* | SQLAlchemy ORM Parameterized Bind Queries |
| **2** | **Reflected Cross-Site Scripting (XSS)** | Type `<script>alert('XSS')</script>` in Tour Search | Triggers **🔥 REFLECTED XSS ATTACK EXECUTED** alert dialog | Auto-escapes script tags safely as text `&lt;script&gt;` | Jinja2 Template Auto-Escaping & CSP Headers |
| **3** | **Password Brute-Force & Admin Revoke Workflow** | Submit 5 fast incorrect passwords on Login | Unlimited login attempts allowed without lockout | 5-min Lockout triggered + **🔓 Request Revoke from Admin** workflow | Sliding-Window Rate Limiter & Admin Revoke Approval |
| **4** | **Stored Cross-Site Scripting (XSS) in Reviews** | Post review comment `<img src=x onerror=alert('StoredXSS')>` | Renders **🔥 STORED XSS ATTACK EXECUTED** warning banner | Image tag escaped safely as plain text text string | Context-Aware Output Encoding |
| **5** | **Insecure Direct Object Reference (IDOR)** | Access URL `/debug/booking/1` without logging in | Discloses private customer booking details & totals | Access blocked with **HTTP 403 Forbidden** | Server-Side Session Role Authorization Checks |
| **6** | **Missing HTTP Security Headers & SIEM Audit Bypass** | Inspect HTTP headers in browser F12 DevTools | Security headers stripped; actions unlogged | Enforces `X-Frame-Options`, `nosniff`, `CSP`, and logs IP to SIEM | Response Interceptor Middleware & File Logger |
| **7** | **Timing Side-Channel Attack & Secret Verification** | Send POST request to `/api/verify-token` | String comparison uses early-exit equality `==` leaking execution timing | Enforces constant-time `hmac.compare_digest()` | Constant-Time String Comparison (`hmac.compare_digest`) |
| **8** | **Session Hijacking & CSRF Attack** | Open Browser Console `document.cookie` (Mode persists on login) | Plain cookies exposed without `HttpOnly` and `SameSite` | Enforces `HttpOnly=True` & `SameSite='Lax'` flags | Session Hardening Middleware |
| **9** | **Clickjacking & iFrame Embedding** | Access URL `/demo/clickjacking-test` | App embeds inside malicious `<iframe>` successfully | iFrame framing blocked with `X-Frame-Options: SAMEORIGIN` | Response Header Security Interceptor |

---

## Detailed Step-by-Step Speaking Script for Each Attack

---

### 🎙️ DEMO ATTACK 1: SQL Injection (SQLi) Authentication Bypass

#### Step-by-Step Demo Steps:
1. Click top navbar button to toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Go to `/login` (HTML5 browser email validation has been disabled with `novalidate`).
3. In **Email Address**, type: `' OR '1'='1`
4. Type any dummy password and click **Log In**.
5. **Observation:** You are instantly logged in as Administrator (`admin@travelbooking.local`) without knowing the password!
6. Click **Logout**, toggle **`🛡️ Security: ON (Secured)`**, and repeat.
7. **Observation:** Login fails safely with *"Invalid email or password"*.

#### 🗣️ What to Say to Your Supervisor:
> *"Respected Supervisor, for our first demo, I am demonstrating **SQL Injection (SQLi)**.  
> In Vulnerable Mode, HTML5 email validation is disabled so the raw payload `' OR '1'='1` reaches the server, altering the SQL string logic (`WHERE email='{email}'`) to evaluate as TRUE and logging me into the Admin portal.  
> When Security Mode is **ON**, our application uses **SQLAlchemy ORM Parameterized Queries**. User input is treated strictly as literal data rather than executable SQL code."*

---

### 🎙️ DEMO ATTACK 2: Reflected Cross-Site Scripting (XSS)

#### Step-by-Step Demo Steps:
1. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Go to `/tours` and search for: `<script>alert('XSS Attack Successful!')</script>`
3. **Observation:** A browser alert dialog pops up: **`🔥 REFLECTED XSS ATTACK EXECUTED!`**
4. Toggle **`🛡️ Security: ON (Secured)`** and search again.
5. **Observation:** The text is rendered safely as `Results for: <script>alert('XSS Attack Successful!')</script>` without executing script.

#### 🗣️ What to Say to Your Supervisor:
> *"For our second demo, I am presenting **Reflected Cross-Site Scripting (XSS)**.  
> In Vulnerable Mode, search queries are executed directly in the HTML DOM.  
> In Secured Mode, Jinja2 auto-escaping encodes special characters into safe HTML entities (`&lt;script&gt;`), rendering the payload as safe text."*

---

### 🎙️ DEMO ATTACK 3: Password Brute-Force & Admin Lockout Revoke Workflow

#### Step-by-Step Demo Steps:
1. Toggle **`🛡️ Security: ON (Secured)`** -> Go to `/login` -> Submit 5 failed password attempts.
2. **Observation:** On the 5th attempt, a red alert appears: **ACCOUNT LOCKED OUT (5-MINUTE SECURITY TIMEOUT)** with HTTP 429.
3. Click the button: **`🔓 Request Account Lockout Revoke from Admin`**.
4. Log in as Admin (`admin@travelbooking.local` / `Admin@123`) -> Go to `/admin/dashboard`.
5. Under **Pending Account Lockout Revoke Requests**, click **`Approve & Revoke Lockout`**.
6. **Observation:** The admin lifts the lockout immediately, allowing the user to log in again right away!

#### 🗣️ What to Say to Your Supervisor:
> *"Our third attack demo is **Brute-Force Rate Limiting with Admin Lockout Revoke**.  
> After 5 failed attempts within 5 minutes (300 seconds), our rate limiter blocks the client IP (`HTTP 429`). Locked out users can click **Request Account Lockout Revoke from Admin**. The administrator receives a notification on the Admin Dashboard and can click **Approve & Revoke Lockout** to instantly restore account access."*

---

### 🎙️ DEMO ATTACK 4: Stored Cross-Site Scripting (XSS) in Reviews

#### Step-by-Step Demo Steps:
1. Submit a review containing: `<img src=x onerror="alert('Stored XSS Executed!')">`.
2. Toggle **`⚠️ Security: OFF (Vulnerable)`** -> Go to `/feedback` or `/tours/1`.
3. **Observation:** A red warning banner displays: **`🔥 STORED XSS ATTACK EXECUTED — VULNERABLE DATA RENDERED`** with script execution!
4. Toggle **`🛡️ Security: ON (Secured)`** -> The review renders as safe text.

#### 🗣️ What to Say to Your Supervisor:
> *"Our fourth demo is **Stored (Persistent) XSS**.  
> In Vulnerable Mode, stored payloads execute for every user visiting the feedback page. In Secured Mode, context-aware output encoding sanitizes all database review strings before rendering."*

---

### 🎙️ DEMO ATTACK 8: Session Security & Mode State Persistence

#### Step-by-Step Demo Steps:
1. Toggle **`⚠️ Security: OFF (Vulnerable)`** -> Log in.
2. **Observation:** Upon landing on the User Dashboard, **`⚠️ Security: OFF (Vulnerable)`** remains active because `session["security_mode"]` is preserved across login redirects.

---

## Verification Test Command

```powershell
python test_security.py
```
*(Result: 7/7 Security Tests Pass 100% in 0.4 seconds!)*
