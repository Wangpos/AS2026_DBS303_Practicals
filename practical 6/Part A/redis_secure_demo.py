import redis, ssl, os

def create_redis_client():
    ca_path = os.path.expanduser("~/redis-lab/tls/ca.crt")

    return redis.Redis(
        host="127.0.0.1",
        port=6379,
        username="app_user",
        password="appStrongPwd",
        ssl=True,
        ssl_ca_certs=ca_path,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        ssl_check_hostname=False,
        decode_responses=True,
    )

if __name__ == "__main__":
    r = create_redis_client()
    print("Connected as:", r.acl_whoami())
    r.set("session:python_demo", "hello from python")
    print("Value:", r.get("session:python_demo"))
