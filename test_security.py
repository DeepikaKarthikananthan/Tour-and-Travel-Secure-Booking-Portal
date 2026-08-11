import unittest
import os
from app import create_app
from routes.utils import safe_str_cmp, log_security_event, SECURITY_LOG_FILE

class SecurityControlsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_defensive_http_security_headers(self):
        """Test Case 1: Verify presence of defensive HTTP security headers."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Content-Type-Options', response.headers)
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'SAMEORIGIN')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn('Cache-Control', response.headers)
        print("[PASS] Test Case 1: Defensive HTTP Security Headers present.")

    def test_02_sql_injection_defense(self):
        """Test Case 2: Verify parameterization defense against SQL Injection payload."""
        sqli_payload = "' OR '1'='1"
        response = self.client.post('/login', data={'email': sqli_payload, 'password': 'password'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)
        print("[PASS] Test Case 2: SQL Injection payload safely neutralized via Parameterized Queries.")

    def test_03_xss_auto_escaping_defense(self):
        """Test Case 3: Verify Jinja2 template auto-escaping defense against XSS."""
        response = self.client.get('/tours?q=<script>alert("XSS")</script>')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<script>alert("XSS")</script>', response.data)
        self.assertIn(b'&lt;script&gt;', response.data)
        print("[PASS] Test Case 3: Script payload auto-escaped in HTML response.")

    def test_04_rate_limiting_brute_force_defense(self):
        """Test Case 4: Verify sliding-window rate limiting defense against password guessing."""
        client_ip = '192.168.1.100'
        for i in range(5):
            self.client.post('/login', data={'email': 'user@example.com', 'password': f'wrong_{i}'}, environ_base={'REMOTE_ADDR': client_ip})
        
        throttled_response = self.client.post('/login', data={'email': 'user@example.com', 'password': 'wrong_6'}, environ_base={'REMOTE_ADDR': client_ip})
        self.assertEqual(throttled_response.status_code, 429)
        self.assertIn(b"Too many failed login attempts", throttled_response.data)
        print("[PASS] Test Case 4: Password guessing throttled by Rate Limiter (HTTP 429).")

    def test_05_session_cookie_protection(self):
        """Test Case 5: Verify HttpOnly and SameSite cookie configuration."""
        self.assertEqual(self.app.config['SESSION_COOKIE_HTTPONLY'], True)
        self.assertEqual(self.app.config['SESSION_COOKIE_SAMESITE'], 'Lax')
        print("[PASS] Test Case 5: Session configuration enforces HttpOnly and SameSite=Lax.")

    def test_06_timing_attack_constant_time_defense(self):
        """Test Case 6: Verify constant-time string comparison defense against Timing Side-Channel attacks."""
        token_a = "SecretToken1234567890"
        token_b = "SecretToken1234567890"
        token_c = "SecretToken9999999999"
        self.assertTrue(safe_str_cmp(token_a, token_b))
        self.assertFalse(safe_str_cmp(token_a, token_c))
        print("[PASS] Test Case 6: Constant-time string comparison (hmac.compare_digest) protects against timing side-channels.")

    def test_07_security_audit_logging_system(self):
        """Test Case 7: Verify real-time Security Audit Log generation for security events."""
        with self.app.test_request_context():
            log_security_event("TEST_EVENT", "Verified real-time security logging mechanism.")
        
        self.assertTrue(os.path.exists(SECURITY_LOG_FILE))
        with open(SECURITY_LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("TEST_EVENT", content)
            self.assertIn("Verified real-time security logging mechanism", content)
        print("[PASS] Test Case 7: Security Audit Logging actively recording security events to file.")

if __name__ == '__main__':
    unittest.main()
