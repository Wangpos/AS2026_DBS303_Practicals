# DBS302 — Practical 6: Part B
## MongoDB Authentication & Access Control

| Field | Details |
|-------|---------|
| **Student Name** | Tshering Wangpo Dorji |
| **Course** | DBS302 — Database Systems |
| **Practical** | Practical 6 — Part B |
| **Date** | 4 May 2026 |
| **MongoDB Version** | 7.0.8 |
| **mongosh Version** | 2.8.2 |

---

## Objective

Configure MongoDB with role-based access control (RBAC) and authentication. This involves setting up a MongoDB instance without authentication, creating an administrator user, enabling authentication via a configuration file, and verifying that unauthenticated access is correctly blocked while authenticated access is permitted.

---

## Environment

| Component | Details |
|-----------|---------|
| OS | macOS (Apple Silicon — aarch64) |
| MongoDB | v7.0.8 |
| mongosh | v2.8.2 |
| Data Directory | `~/mongo-lab/data` |
| TLS Directory | `~/mongo-lab/tls` |
| Config File | `~/mongo-lab/mongod.conf` |
| Bind Address | `127.0.0.1` (localhost only) |
| Port | `27017` |

---

## Step-by-Step Procedure

### Step 1 — Stop MongoDB and Wipe Data Directory

Any running MongoDB instance was stopped using `pkill mongod`. The data directory was wiped clean to ensure a fresh start, free from any previously stored data that could interfere with authentication setup.

```bash
pkill mongod 2>/dev/null
sleep 2
rm -rf ~/mongo-lab/data/*
ls ~/mongo-lab/data/
```

**Expected:** Empty output (no files listed)

![Step 1 — Stop MongoDB and Wipe Clean](img/Step_1__Stop_MongoDB_and_Wipe_Clean.png)

---

### Step 2 — Start MongoDB Without Authentication

MongoDB was started without authentication to allow creation of the initial admin user. The `--fork` flag runs the process in the background. The log was verified to confirm the server was listening on port 27017.

```bash
mongod --dbpath ~/mongo-lab/data \
       --bind_ip 127.0.0.1 \
       --port 27017 \
       --fork \
       --logpath ~/mongo-lab/mongod.log
sleep 2
tail -3 ~/mongo-lab/mongod.log
```

**Expected:** `Waiting for connections` on port 27017

![Step 2 — Start MongoDB Without Auth](img/Step_2__Start_MongoDB_WITHOUT_Auth.png)

---

### Step 3 — Create the Root Administrator User

Connected to the MongoDB shell and switched to the `admin` database. A root administrator user `rootAdmin` was created with three roles: `userAdminAnyDatabase`, `dbAdminAnyDatabase`, and `readWriteAnyDatabase`.

```bash
mongosh --host 127.0.0.1 --port 27017
```

```js
use admin

db.createUser({
  user: "rootAdmin",
  pwd: "rootStrongPwd",
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "dbAdminAnyDatabase", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})
```

**Expected:** `{ ok: 1 }`

![Step 3 — Create Root Admin User](img/Step_3__Create_the_Root_Admin_User_Inside_mongosh_.png)

---

### Step 4 — Write Configuration File with Authentication Enabled

A `mongod.conf` file was created specifying the data directory, localhost binding, and `authorization: "enabled"`. Single-quoted `'EOF'` was used to prevent `$HOME` from being expanded incorrectly.

```bash
cat > ~/mongo-lab/mongod.conf << 'EOF'
storage:
  dbPath: /Users/tsheringwangpodorji/mongo-lab/data

net:
  port: 27017
  bindIp: 127.0.0.1

security:
  authorization: "enabled"
EOF

cat ~/mongo-lab/mongod.conf
```

**Expected:** Config printed with the correct absolute path and `authorization: "enabled"`

![Step 4 — Write Config File](img/Step_4__Write_the_Config_File_with_Auth_Enabled.png)

---

### Step 5 — Restart MongoDB with Authentication Enabled

The running instance was stopped and restarted using the new config file. The log confirmed the server started successfully with auth applied.

```bash
pkill mongod 2>/dev/null
sleep 2
mongod --config ~/mongo-lab/mongod.conf \
       --fork \
       --logpath ~/mongo-lab/mongod.log
sleep 2
tail -3 ~/mongo-lab/mongod.log
```

**Expected:** `Waiting for connections` on port 27017

![Step 5 — Restart MongoDB with Auth](img/Step_5__Restart_MongoDB_WITH_Auth.png)

---

### Step 6 — Test Authenticated Access (Should Succeed)

Connected using `rootAdmin` credentials. `connectionStatus` confirmed the user was authenticated with all three assigned roles.

```bash
mongosh --host 127.0.0.1 --port 27017 \
  -u rootAdmin -p rootStrongPwd \
  --authenticationDatabase admin
```

```js
db.runCommand({ connectionStatus: 1 })
```

**Expected:**
```
authenticatedUsers: [ { user: 'rootAdmin', db: 'admin' } ]
ok: 1
```

![Step 6 — Test With Credentials](img/Step_6__Test_WITH_Credentials.png)

---

### Step 7 — Test Unauthenticated Access (Should Fail)

Connected without any credentials and ran `show dbs`. The expected `Unauthorized` error was returned, confirming that authentication is correctly enforced.

```bash
mongosh --host 127.0.0.1 --port 27017
```

```js
show dbs
```

**Expected:**
```
MongoServerError[Unauthorized]: Command listDatabases requires authentication
```

![Step 7 — Test Without Credentials](img/Step_7__Test_WITHOUT_Credentials.png)

---

## Results Summary

| # | Step | Expected Outcome | Result |
|---|------|-----------------|--------|
| 1 | Wipe data directory | Empty directory | ✅ Pass |
| 2 | Start MongoDB without auth | Server listening on 27017 | ✅ Pass |
| 3 | Create rootAdmin user | `{ ok: 1 }` | ✅ Pass |
| 4 | Write mongod.conf with auth | Config file verified | ✅ Pass |
| 5 | Restart with auth config | Server starts cleanly | ✅ Pass |
| 6 | Login with credentials | rootAdmin authenticated | ✅ Pass |
| 7 | Login without credentials | Unauthorized error | ✅ Pass |

---

## Conclusion

This practical successfully demonstrated the configuration of MongoDB authentication and role-based access control. All seven steps produced the expected outcomes.

The final two tests confirmed that the security configuration is working correctly — authenticated users can connect and operate normally, while unauthenticated attempts are blocked with a clear `Unauthorized` error.

**Key lesson learned:** It is critical to wipe the data directory before enabling authentication. Without this step, MongoDB loads existing data files from a previous unauthenticated session and ignores the new security configuration, making authentication appear non-functional even when the config file is correct.
