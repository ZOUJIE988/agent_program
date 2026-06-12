# # 临时测试脚本
import redis
# 直接查看 Redis
r = redis.Redis(host='localhost', port=6379, db=0,decode_responses=True)
keys = r.keys("request_cache:*")
for key in keys:
    print(f"Key: {key}")
    print(f"Value: {r.get(key)}")
