#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微服务架构 - API网关
负责请求路由、认证、限流等
"""

from flask import Flask, request, jsonify
import requests
import time
import jwt
import redis
from functools import wraps

app = Flask(__name__)

# 配置
SECRET_KEY = "your-secret-key"
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# 服务注册表
SERVICES = {
    'converter': 'http://converter-service:5001',
    'downloader': 'http://downloader-service:5002',
    'storage': 'http://storage-service:5003',
    'analytics': 'http://analytics-service:5004'
}

# Redis连接
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(self, key, limit=100, window=3600):
        """检查是否允许请求"""
        current = int(time.time())
        pipe = self.redis.pipeline()
        
        # 清理过期的计数
        pipe.zremrangebyscore(key, 0, current - window)
        # 添加当前请求
        pipe.zadd(key, {str(current): current})
        # 获取窗口内的请求数
        pipe.zcard(key)
        # 设置过期时间
        pipe.expire(key, window)
        
        results = pipe.execute()
        return results[2] <= limit

rate_limiter = RateLimiter(redis_client)

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        
        try:
            # 移除 "Bearer " 前缀
            token = token.replace('Bearer ', '')
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = payload
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def rate_limit(limit=100, window=3600):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 获取客户端IP
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            key = f"rate_limit:{client_ip}"
            
            if not rate_limiter.is_allowed(key, limit, window):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': limit,
                    'window': window
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

@app.route('/api/auth/login', methods=['POST'])
@rate_limit(limit=10, window=300)  # 5分钟内最多10次登录尝试
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 这里应该验证用户名和密码
    if username == 'admin' and password == 'password':
        token = jwt.encode({
            'user_id': 1,
            'username': username,
            'exp': int(time.time()) + 3600  # 1小时过期
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/converter/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(limit=50, window=3600)
def proxy_converter(endpoint):
    """代理转换服务请求"""
    return proxy_request('converter', endpoint)

@app.route('/api/downloader/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(limit=30, window=3600)
def proxy_downloader(endpoint):
    """代理下载服务请求"""
    return proxy_request('downloader', endpoint)

@app.route('/api/storage/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(limit=100, window=3600)
def proxy_storage(endpoint):
    """代理存储服务请求"""
    return proxy_request('storage', endpoint)

@app.route('/api/analytics/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
@rate_limit(limit=200, window=3600)
def proxy_analytics(endpoint):
    """代理分析服务请求"""
    return proxy_request('analytics', endpoint)

def proxy_request(service_name, endpoint):
    """通用请求代理"""
    service_url = SERVICES.get(service_name)
    if not service_url:
        return jsonify({'error': 'Service not found'}), 404
    
    url = f"{service_url}/{endpoint}"
    
    # 准备请求参数
    kwargs = {
        'method': request.method,
        'url': url,
        'params': request.args,
        'headers': {k: v for k, v in request.headers if k.lower() != 'host'},
        'timeout': 30
    }
    
    # 添加请求体（如果有）
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.is_json:
            kwargs['json'] = request.get_json()
        else:
            kwargs['data'] = request.get_data()
    
    try:
        response = requests.request(**kwargs)
        
        # 记录请求日志
        log_request(service_name, endpoint, response.status_code)
        
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Service unavailable: {str(e)}'}), 503

def log_request(service, endpoint, status_code):
    """记录请求日志"""
    log_data = {
        'timestamp': int(time.time()),
        'service': service,
        'endpoint': endpoint,
        'status_code': status_code,
        'user_id': getattr(request, 'user', {}).get('user_id', 'anonymous')
    }
    
    # 发送到分析服务
    try:
        requests.post(
            f"{SERVICES['analytics']}/log",
            json=log_data,
            timeout=5
        )
    except:
        pass  # 忽略日志失败

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'services': check_services_health()
    })

def check_services_health():
    """检查所有服务健康状态"""
    health_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            health_status[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except:
            health_status[service_name] = {
                'status': 'unavailable',
                'response_time': None
            }
    
    return health_status

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 API网关已启动")
    print("📍 访问: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
