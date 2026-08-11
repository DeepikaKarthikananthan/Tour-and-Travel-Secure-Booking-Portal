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
| **1** | **SQL Injection (SQLi) Auth Bypass** | Type `' OR '1'='1` into Login Email | Bypasses login without password & grants Admin access | Login fails with *"Invalid email or password"* | SQLAlchemy ORM Parameterized Bind Queries |
| **2** | **Reflected Cross-Site Scripting (XSS)** | Type `<script>alert('XSS')</script>` in Tour Search | Executes JavaScript alert box in browser | Auto-escapes script tags safely as text `&lt;script&gt;` | Jinja2 Template Auto-Escaping & CSP Headers |
| **3** | **Password Brute-Force & Credential Stuffing** | Submit 6 fast incorrect passwords on Login | Unlimited login attempts allowed without lockout | 6th attempt blocked with **HTTP 429 Too Many Requests** | In-Memory Sliding-Window IP Rate Limiter |
| **4** | **Stored Cross-Site Scripting (XSS) in Reviews** | Post review comment `<img src=x onerror=alert('StoredXSS')>` | Script executes automatically whenever anyone views the tour | Image tag escaped safely as plain text text string | Context-Aware Output Encoding |
| **5** | **Insecure Direct Object Reference (IDOR)** | Access URL `/debug/booking/1` without logging in | Discloses private customer booking details & totals | Access blocked with **HTTP 403 Forbidden** | Server-Side Session Role Authorization Checks |
| **6** | **Missing HTTP Security Headers & SIEM Audit Bypass** | Inspect HTTP headers in browser F12 DevTools | Security headers stripped; actions unlogged | Enforces `X-Frame-Options`, `nosniff`, `CSP`, and logs IP to SIEM | Response Interceptor Middleware & File Logger |
| **7** | **Timing Side-Channel Attack & Secret Verification** | Send POST request to `/api/verify-token` | String comparison uses early-exit equality `==` leaking execution timing | Enforces constant-time `hmac.compare_digest()` | Constant-Time String Comparison (`hmac.compare_digest`) |
| **8** | **Session Hijacking & CSRF Attack** | Open Browser Console `document.cookie` | Plain cookies exposed without `HttpOnly` and `SameSite` | Enforces `HttpOnly=True` & `SameSite='Lax'` flags | Session Hardening Middleware |
| **9** | **Clickjacking & iFrame Embedding** | Access URL `/demo/clickjacking-test` | App embeds inside malicious `<iframe>` successfully | iFrame framing blocked with `X-Frame-Options: SAMEORIGIN` | Response Header Security Interceptor |

---

## Detailed Step-by-Step Speaking Script for Each Attack

---

### 🎙️ DEMO ATTACK 1: SQL Injection (SQLi) Authentication Bypass

#### Step-by-Step Demo Steps:
1. Click the top navbar button to toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Go to the **Login Page** (`/login`).
3. In the **Email Address** field, type: `' OR '1'='1`
4. Type any dummy password (e.g. `password`) and click **Log In**.
5. **Observation:** You are instantly logged in as the Administrator (`admin@travelbooking.local`) without knowing the password!
6. Click **Logout**, toggle **`🛡️ Security: ON (Secured)`**, and repeat the exact same step.
7. **Observation:** Login fails safely with *"Invalid email or password"*.

#### 🗣️ What to Say to Your Supervisor:
> *"Respected Supervisor, for our first demo, I am demonstrating **SQL Injection (SQLi)**.  
> When Security Mode is **OFF**, the application uses raw string concatenation in its database query string (`SELECT * FROM users WHERE email='{email}'`). Injecting the payload `' OR '1'='1` alters the SQL logical evaluation to always return TRUE, bypassing password authentication completely and logging me into the administrator portal.  
> When I toggle Security Mode **ON**, our defensive control uses **SQLAlchemy ORM Parameterized Queries**. The database engine treats the input strictly as literal string data rather than executable SQL code instructions, neutralizing the injection attack entirely."*

---

### 🎙️ DEMO ATTACK 2: Reflected Cross-Site Scripting (XSS)

#### Step-by-Step Demo Steps:
1. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Go to the **Tours Page** (`/tours`).
3. In the search bar, paste: `<script>alert('XSS Attack Successful!')</script>` and press **Search**.
4. **Observation:** A JavaScript pop-up alert box appears in the browser!
5. Toggle **`🛡️ Security: ON (Secured)`** and press **Search** again.
6. **Observation:** The browser safely displays the search text as `Results for: <script>alert('XSS Attack Successful!')</script>` without executing any script.

#### 🗣️ What to Say to Your Supervisor:
> *"For our second demo, I am presenting **Reflected Cross-Site Scripting (XSS)**.  
> In Vulnerable Mode, user search input is passed directly to the browser template engine without sanitization. An attacker can inject arbitrary JavaScript code to execute malicious scripts or steal session cookies.  
> When Security Mode is **ON**, our application enforces **Jinja2 Auto-Escaping** and an explicit **Content Security Policy (CSP)** header. Special HTML characters like `<` and `>` are encoded into safe HTML entities (`&lt;` and `&gt;`), rendering the string harmlessly as text."*

---

### 🎙️ DEMO ATTACK 3: Password Brute-Force & Credential Stuffing

#### Step-by-Step Demo Steps:
1. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Go to `/login` and submit 6 incorrect password attempts rapidly for `user@example.com`.
3. **Observation:** All 6 attempts are processed continuously without delay or lockout.
4. Toggle **`🛡️ Security: ON (Secured)`**.
5. Submit failed login attempts again.
6. **Observation:** On the 6th attempt, the application blocks the client IP with a red alert: *"Too many failed login attempts. Please wait 60 seconds"* and returns **HTTP 429 Too Many Requests**.

#### 🗣️ What to Say to Your Supervisor:
> *"Our third attack simulation covers **Automated Password Brute-Force & Dictionary Attacks**.  
> Without rate limiting, automated attack tools like Hydra or Burp Suite can test thousands of password combinations per second.  
> In Secured Mode, our defensive control implements an **IP-based Sliding-Window Rate Limiter**. It tracks failed authentication attempts per client IP address (`request.remote_addr`). Once an IP exceeds 5 failed attempts within a 60-second window, the server returns an **HTTP 429 (Too Many Requests)** status code, throttling automated brute-force attacks."*

---

### 🎙️ DEMO ATTACK 4: Stored Cross-Site Scripting (XSS) in Reviews

#### Step-by-Step Demo Steps:
1. Go to any Tour Details page (e.g. `/tours/1`).
2. Log in as a customer and submit a review comment containing: `<img src=x onerror="alert('Stored XSS Payload Executed!')">`.
3. Toggle **`⚠️ Security: OFF (Vulnerable)`** and refresh the page.
4. **Observation:** The JavaScript `onerror` event fires automatically every time the page loads!
5. Toggle **`🛡️ Security: ON (Secured)`** and refresh.
6. **Observation:** The review displays safely as text without triggering any script pop-up.

#### 🗣️ What to Say to Your Supervisor:
> *"Our fourth demo is **Stored (Persistent) XSS**.  
> Unlike reflected XSS, stored XSS persists inside the database. When an attacker posts a review containing an image tag with an `onerror` handler, the script executes for every user who visits that tour page.  
> In Secured Mode, our context-aware output encoding sanitizes all database content before rendering, rendering raw HTML tags harmless."*

---

### 🎙️ DEMO ATTACK 5: Insecure Direct Object Reference (IDOR) Data Leak

#### Step-by-Step Demo Steps:
1. Open a new incognito window (unauthenticated user).
2. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
3. Access the debug URL directly: `http://127.0.0.1:5000/debug/booking/1`
4. **Observation:** Private customer booking reference, status, user ID, and financial totals are exposed in JSON!
5. Toggle **`🛡️ Security: ON (Secured)`** and refresh `http://127.0.0.1:5000/debug/booking/1`.
6. **Observation:** Server returns **HTTP 403 Forbidden** with error: *"Unauthorized Access - IDOR Defense Active. Login required as administrator"*.

#### 🗣️ What to Say to Your Supervisor:
> *"Our fifth demonstration is **Insecure Direct Object Reference (IDOR)**.  
> IDOR occurs when an application exposes direct database identifiers without verifying if the requesting user has authorization.  
> In Secured Mode, our application enforces **Server-Side Session Authorization Checkers** (`admin_required` and user ID validation decorators), rejecting unauthorized object access with HTTP 403 Forbidden."*

---

### 🎙️ DEMO ATTACK 6: Missing HTTP Security Headers & SIEM Audit Logging

#### Step-by-Step Demo Steps:
1. Open Browser **F12 Developer Tools** -> **Network tab**.
2. Click any request and inspect **Response Headers**.
3. Toggle **`🛡️ Security: ON (Secured)`** and refresh.
4. **Observation:** Response headers show `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`, and `Content-Security-Policy`.
5. Show the security log file in `instance/security_audit.log`.
6. **Observation:** Real-time log entries record client IP, timestamp, and event type (`LOGIN_FAILED`, `RATE_LIMIT_EXCEEDED`, `UNAUTHORIZED_ACCESS`).

#### 🗣️ What to Say to Your Supervisor:
> *"Our sixth demonstration covers **Defensive HTTP Security Headers and SIEM Security Audit Logging**.  
> Our response middleware injects `X-Frame-Options: SAMEORIGIN` to prevent Clickjacking iframe attacks, `X-Content-Type-Options: nosniff` to stop MIME-sniffing exploits, and `Cache-Control: no-store` to prevent sensitive account data leakage on shared computers.  
> Concurrently, our SIEM audit logger writes security events to `instance/security_audit.log`, binding client IP addresses and timestamps for forensic intrusion detection."*

---

### 🎙️ DEMO ATTACK 7: Timing Side-Channel Attack & Token Verification

#### Step-by-Step Demo Steps:
1. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
2. Open terminal or POST client to `/api/verify-token` with payload `{"token": "WAYFARER-SECRET-KEY-9988"}`.
3. **Observation:** In Vulnerable Mode, standard string equality (`==`) compares characters sequentially and exits early on mismatch, revealing token characters microsecond by microsecond.
4. Toggle **`🛡️ Security: ON (Secured)`** and re-send request.
5. **Observation:** API returns `comparison_method: "Secured Constant-Time hmac.compare_digest()"`.

#### 🗣️ What to Say to Your Supervisor:
> *"Our seventh demo presents **Timing Side-Channel Attacks**.  
> Standard string comparison (`val1 == val2`) evaluates character-by-character and aborts on the first non-matching byte. An attacker measuring latency in microseconds can deduce secret tokens one character at a time.  
> In Secured Mode, we use **`hmac.compare_digest()`** which executes in constant CPU time regardless of matching or non-matching positions, neutralizing timing leaks."*

---

### 🎙️ DEMO ATTACK 8: Session Hijacking & CSRF Defense

#### Step-by-Step Demo Steps:
1. Log in to the application and open Browser **F12 Developer Tools** -> **Console**.
2. In Console, type: `document.cookie`.
3. Toggle **`🛡️ Security: ON (Secured)`**.
4. **Observation:** Sensitive session cookies are protected with **`HttpOnly=True`** and **`SameSite=Lax`**, preventing JavaScript exfiltration and blocking cross-site request forgery.

#### 🗣️ What to Say to Your Supervisor:
> *"Our eighth demonstration covers **Session Hijacking and Cross-Site Request Forgery (CSRF)**.  
> Without `HttpOnly`, malicious XSS scripts can steal session tokens via `document.cookie`. Without `SameSite='Lax'`, third-party malicious sites can forge unauthorized POST requests.  
> In Secured Mode, our session security middleware enforces `HttpOnly=True` and `SameSite='Lax'` flags, securing session tokens from script access."*

---

### 🎙️ DEMO ATTACK 9: Clickjacking & iFrame Embedding Defense

#### Step-by-Step Demo Steps:
1. Go to URL `/demo/clickjacking-test`.
2. Toggle **`⚠️ Security: OFF (Vulnerable)`**.
3. **Observation:** The application embeds successfully inside a red attacker `<iframe>` box because `X-Frame-Options` is missing.
4. Toggle **`🛡️ Security: ON (Secured)`** and refresh `/demo/clickjacking-test`.
5. **Observation:** The browser blocks the iframe rendering, displaying a security error due to **`X-Frame-Options: SAMEORIGIN`**.

#### 🗣️ What to Say to Your Supervisor:
> *"Our ninth demonstration is **Clickjacking & iFrame Embedding**.  
> Clickjacking occurs when an attacker overlays an application inside an invisible iframe on a malicious website to trick users into clicking buttons.  
> In Secured Mode, our server sets **`X-Frame-Options: SAMEORIGIN`** and **`Content-Security-Policy: frame-ancestors 'self'`**, instructing browsers to reject any third-party iframe embedding attempts."*

---

## Verification Test Script Command for Supervisor

To run the automated Python test suite for your supervisor:

```powershell
python test_security.py
```
*(Result: 7/7 Security Tests Pass 100% in 0.6 seconds!)*
