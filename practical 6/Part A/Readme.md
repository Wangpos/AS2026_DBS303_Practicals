# Practical 6 – Part A: Securing Redis
### Authentication, Encryption (TLS), and Role-Based Access Control

| | |
|---|---|
| **Module** | DBS302 – NoSQL Database Management |
| **Date** | 4 May 2026 |

---

## 1. Aim

To configure and verify authentication, encryption, and role-based access control (RBAC) for Redis, and to perform a basic security audit of the configured database instance.

---

## 2. Objectives

- Enable password-based authentication and Access Control Lists (ACL) in Redis.
- Create multiple users with distinct permissions using Redis ACL rules.
- Enable TLS encryption for Redis connections using self-signed certificates.
- Test and verify that ACL restrictions and TLS are correctly enforced.
- Produce a security audit report documenting findings.

---

## 3. Theory

### 3.1 Authentication

Authentication is the process by which a client proves its identity to the database server before being permitted to execute any commands. In Redis, authentication is implemented through the Access Control List (ACL) system, which requires each connecting client to supply a valid username and password. Without authentication, any client that can reach the Redis port may issue arbitrary commands, including destructive operations such as `FLUSHALL`. Enabling authentication is therefore a foundational security requirement for any Redis deployment that is accessible over a network.

### 3.2 TLS Encryption

Transport Layer Security (TLS) is a cryptographic protocol that encrypts data in transit between a client and a server. When TLS is not in use, all Redis commands and responses — including passwords and sensitive data — are transmitted in plaintext and may be intercepted by a network attacker. By enabling TLS in Redis, all traffic is encrypted using asymmetric cryptography. A Certificate Authority (CA) issues a server certificate that clients use to verify the server's identity. For this laboratory exercise, a self-signed CA was generated using OpenSSL, which is appropriate for a controlled lab environment.

### 3.3 Role-Based Access Control (RBAC)

Role-Based Access Control is a security model in which permissions are assigned to roles rather than directly to individual users, and users are then assigned to those roles. In Redis, RBAC-like behaviour is achieved through ACL rules that specify, for each user: which commands may be executed, and which key patterns may be accessed. This principle of least privilege ensures that a compromised application user account cannot be used to access data or execute commands outside its intended scope. For example, an application user restricted to `session:*` keys cannot access configuration keys or administrative commands, even if its credentials are compromised.

---

## 4. Procedure

### 4.1 Step 0 – Environment Verification

Prior to configuration, the Redis installation was verified by checking the installed server version. The default Redis configuration file location on macOS (Homebrew) was also confirmed.

![ Figure 1: Redis version confirmed as 8.6.1 on macOS ](<img/redis-server --version.png>)
*Figure 1: Redis version confirmed as 8.6.1 on macOS*

![Figure 2: Default redis.conf location confirmed](img/ls_opt_homebrew_etc_redis_conf.png)
*Figure 2: Default redis.conf location at `/opt/homebrew/etc/redis.conf` confirmed*

---

### 4.2 Step 1 – Creating the Lab Directory and redis.conf

A dedicated lab directory (`~/redis-lab`) was created. A custom `redis.conf` file was written to define four ACL users with distinct permission sets. The default user was explicitly disabled to prevent unauthenticated access. The configuration was verified by printing the file contents to the terminal.

![Figure 3: Lab directory created and redis.conf written with ACL user definitions](<img/Step 1: Create Your Lab Folder & Config.png>)

![](img/Step_1__Create_Your_Lab_Folder___Config.png)
*Figure 3: Lab directory created and `redis.conf` written with ACL user definitions*

---

### 4.3 Step 2 – Starting Redis with the Custom Configuration

Any previously running Redis instance was terminated using `pkill`, and Redis was restarted with the custom configuration file. The startup log confirmed that the server initialised successfully, that the default user was disabled, and that the server was ready to accept TCP connections on port 6379.


![Figure 4: Redis restarted with custom config; startup log confirms default user disabled](<img/Stop any running Redis and start with your config.png>)
*Figure 4: Redis restarted with custom config; startup log confirms default user disabled*

![Figure 5: Admin user authenticated successfully with PONG response](<img/Verify it started.png>)
*Figure 5: Admin user authenticated successfully with PONG response*

---

### 4.4 Step 3 – Testing ACL Users (RBAC)

#### 4.4.1 Admin User

The admin user was granted full access (`~* +@all`). Upon connecting, the user was able to set and retrieve arbitrary keys, confirming unrestricted access consistent with an administrative role.

![Figure 6: Admin user connected successfully](<img/Step 2: Test ACL Users (RBAC) 🔑 Test admin user.png>)
*Figure 6: Admin user connected successfully*

![alt text](<img/whoami set mykey "hello" get mykey.png>)
*Figure 7: Admin user successfully executed SET and GET commands on arbitrary keys*

#### 4.4.2 Monitoring User (Read-Only)

The monitoring user was granted read permissions and access to informational commands only (`+@read +info +dbsize +lastsave`). When this user attempted to execute a `SET` command, the server returned a `NOPERM` error, confirming that write operations are correctly denied to read-only users.


![Figure 8: Monitoring user connected](<img/Test monitoring user (read-only).png>)
*Figure 8: Monitoring user connected*


![Figure 9: NOPERM error correctly returned when monitoring user attempted SET command](<img/Test monitoring user (read-only.png>)
*Figure 9: NOPERM error correctly returned when monitoring user attempted SET command*

#### 4.4.3 Anonymous Access Denied

A connection attempt was made without supplying any credentials. The server returned a `NOAUTH Authentication required` error, confirming that the default user is disabled and unauthenticated access is refused.

![Figure 10: Anonymous connection attempt correctly rejected with NOAUTH error](img/Test_anonymous_access__should_fail_.png)
*Figure 10: Anonymous connection attempt correctly rejected with NOAUTH error*

---

### 4.5 Step 4 – Generating TLS Certificates

Self-signed TLS certificates were generated using OpenSSL. A private Certificate Authority (CA) key and certificate were created first, followed by a server private key, a Certificate Signing Request (CSR), and finally a server certificate signed by the CA. The certificate subject was set with the organisation field `DBS302` and locality `Phuntsholing, Chukha, Bhutan (BT)`, consistent with the lab context.


![Figure 11: TLS certificate generation using OpenSSL](<img/Step 3: Generate TLS Certificates.png>)
*Figure 11: TLS certificate generation using OpenSSL — CA and server certificates created*

![Figure 12: TLS directory listing confirming generated certificate files](<img/Verify files exist.png>)
*Figure 12: TLS directory listing confirming `ca.crt`, `redis.crt`, `redis.key`, and supporting files*

---

### 4.6 Step 5 – Updating redis.conf for TLS

The `redis.conf` was updated to disable the plain TCP port (`port 0`) and enable TLS on port 6379. The paths to the CA certificate, server certificate, and server private key were specified. The `tls-auth-clients` directive was set to `no` for this lab, meaning clients are not required to present their own certificates (one-way TLS). Redis was restarted to apply the new configuration.

![Figure 13: Updated `redis.conf` showing TLS configuration directives](<img/Write new TLS-enabled config.png>)
*Figure 13: Updated `redis.conf` showing TLS configuration directives*

![Figure 14: Redis stopped and config updated for TLS](<img/Step 4: Update Config for TLS and Restart.png>)
*Figure 14: Redis stopped and config updated for TLS*

![Figure 15: Redis restarted with TLS — startup log confirms Ready to accept connections tls](<img/Start Redis with TLS config.png>)
*Figure 15: Redis restarted with TLS — startup log confirms "Ready to accept connections tls"*

---

### 4.7 Step 6 – Connecting via TLS

A client connection was established using `redis-cli` with the `--tls` flag and the `--cacert` parameter pointing to the CA certificate. The connection succeeded, and subsequent `SET` and `GET` operations on session-scoped keys returned the expected results, confirming that the encrypted channel was operational.

![Figure 16: redis-cli connected using TLS with app_user credentials](<img/Step 5: Connect with TLS.png>)
*Figure 16: `redis-cli` connected using TLS with `app_user` credentials*

![Figure 17: SET and GET operations successful over TLS connection](<img/Step 5: Connect with TLS inside the prompt who am i .png>)
*Figure 17: SET and GET operations successful over TLS connection*

---

### 4.8 Step 7 – Python Application Demo

A Python script (`redis_secure_demo.py`) was executed to demonstrate programmatic access to the secured Redis instance. The script connected as `app_user` over TLS using the `ssl_ca_certs` parameter, wrote a value to a session-scoped key, and retrieved it. The output confirmed both the authenticated identity and successful data round-trip over an encrypted connection.

![Figure 18: Python script output — "Connected as: app_user" and "Value: hello from python" over TLS](<img/redis_secure_demo py file output (connected as app_user).png>)
*Figure 18: Python script output — "Connected as: app_user" and "Value: hello from python" over TLS*

---

## 5. Observations

### 5.1 ACL and RBAC Test Results

The table below summarises the results of all ACL and RBAC tests performed during this practical.

| User | Operation | Expected Result | Actual Result | Status |
|---|---|---|---|:---:|
| `admin` | SET mykey / GET mykey | OK / "hello" | OK / "hello" | ✅ PASS |
| `admin` | SET arbitrary keys | Allowed | Allowed | ✅ PASS |
| `app_user` | SET session:user123 | OK | OK | ✅ PASS |
| `app_user` | SET otherkey (RBAC test) | NOPERM error | NOPERM error | ✅ PASS |
| `monitoring` | DBSIZE (read command) | (integer) 2 | (integer) 2 | ✅ PASS |
| `monitoring` | SET testkey (write test) | NOPERM error | NOPERM error | ✅ PASS |
| `anonymous` | PING (no credentials) | NOAUTH error | NOAUTH error | ✅ PASS |

### 5.2 TLS Test Results

| Security Check | Command / Action | Result | Status |
|---|---|---|:---:|
| TLS connection | `redis-cli --tls --cacert ca.crt` | Connected successfully | ✅ PASS |
| Auth over TLS | `rediss://app_user:...@127.0.0.1:6379` | Authenticated as app_user | ✅ PASS |
| Data over TLS | SET + GET session:user456 | Values stored and retrieved | ✅ PASS |
| Python TLS client | `python3 redis_secure_demo.py` | Connected as: app_user | ✅ PASS |
| Default user disabled | `redis-cli -p 6379 ping` | NOAUTH error returned | ✅ PASS |

---

## 6. Security Audit Summary

### 6.1 What Is Secure

- The default Redis user has been explicitly disabled, preventing any unauthenticated client from executing commands.
- Three distinct ACL users have been created, each with precisely scoped command permissions and key-pattern restrictions, implementing the principle of least privilege.
- The application user (`app_user`) is restricted to `session:*` keys, preventing lateral data access across key namespaces.
- The monitoring user has read-only access and cannot execute any write or administrative commands.
- TLS is enabled on port 6379 and plain TCP is disabled (`port 0`), ensuring all data in transit is encrypted.
- Server certificates are signed by a local CA, providing a verifiable chain of trust within the lab environment.

### 6.2 What Still Needs Improvement

- The certificates are self-signed and would not be trusted by external clients without explicit CA configuration. In a production environment, certificates from a recognised Certificate Authority should be used.
- Passwords are stored in plaintext within `redis.conf`. A secrets management solution (such as HashiCorp Vault or environment variable injection) should be used in production.
- `tls-auth-clients` is set to `no`, meaning clients are not required to present certificates. Enabling mutual TLS (mTLS) would provide stronger client authentication.
- The `whoami` command (`acl|whoami`) had to be explicitly granted to `app_user`, highlighting that fine-grained ACL tuning requires careful testing.
- No password rotation policy is currently in place. Credentials should be rotated periodically.

### 6.3 Recommendations

- Replace self-signed certificates with certificates from a trusted CA for any deployment accessible beyond the local machine.
- Enable mutual TLS (`tls-auth-clients yes`) and issue client certificates to further restrict which clients may connect.
- Store credentials in a secrets manager rather than embedding them in configuration files.
- Enable Redis logging and monitoring (e.g., via the monitoring user and an external alerting system) to detect suspicious access patterns.
- Periodically review ACL rules using `ACL LIST` as the admin user to ensure no unintended permissions have been introduced.

---

## 7. Conclusion

This practical demonstrated the successful implementation of three fundamental security mechanisms — authentication, role-based access control, and TLS encryption — on a Redis 8.6.1 instance running on macOS. By disabling the default user and defining purpose-specific ACL users with scoped permissions, the principle of least privilege was enforced across all client roles. The introduction of TLS, backed by a self-signed Certificate Authority, ensured that all data exchanged between client and server was encrypted in transit, mitigating the risk of credential or data interception. All security controls were verified through both positive tests (confirming permitted operations succeed) and negative tests (confirming prohibited operations are correctly denied). The practical thereby achieves the learning outcomes specified for DBS302, specifically LO8, which requires students to critique security measures in NoSQL databases and propose strategies for authentication, encryption, and access control implementation.

While the configuration is appropriate for a controlled laboratory environment, several improvements — including the use of production CA-signed certificates, mutual TLS, and secrets management — would be necessary before deploying a similarly configured Redis instance in a production context.

---

*DBS302 – NoSQL Database Management | Practical 6 Part A | 4 May 2026*