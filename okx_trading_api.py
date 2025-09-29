#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OKX Trading API Handler
OKX交易API处理器
===================

功能:
- API认证和签名
- 下单、撤单、查询
- 风险管理
- 交易记录

作者: GitHub Copilot
版本: 1.0
"""

import base64
import hmac
import hashlib
import json
import time
import requests
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class OKXTradingAPI:
    """OKX交易API类"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        """初始化交易API"""
        # 先加载配置
        self.load_config(config_file)
        
        self.session = requests.Session()
        self.base_url = "https://www.okx.com" if not self.sandbox else "https://www.okx.com"
        
        # 交易状态
        self.last_trade_time = 0
        self.daily_trades = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        
        # 交易记录
        self.trade_history = []
        self.open_positions = {}
        
    def load_config(self, config_file: str):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.api_key = self.config['api_key']
            self.secret_key = self.config['secret_key']
            self.passphrase = self.config['passphrase']
            self.sandbox = self.config.get('sandbox', True)
            
            # 交易设置
            trading_settings = self.config.get('trading_settings', {})
            self.trade_amount_usdt = trading_settings.get('trade_amount_usdt', 100)
            self.min_trade_interval = trading_settings.get('min_trade_interval', 300)  # 5分钟
            self.max_trades_per_day = trading_settings.get('max_trades_per_day', 5)
            self.stop_loss_percent = trading_settings.get('stop_loss_percent', 5.0)
            self.take_profit_percent = trading_settings.get('take_profit_percent', 10.0)
            
            # 设置交易启用状态
            self.trading_enabled = self.config.get('trading_enabled', False)
            
            logger.info(f"Trading config loaded. Sandbox: {self.sandbox}, Trading enabled: {self.trading_enabled}")
            
        except Exception as e:
            logger.error(f"Failed to load trading config: {e}")
            raise
    
    def generate_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """生成API签名"""
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return signature
    
    def get_headers(self, method: str, request_path: str, body: str = '') -> Dict[str, str]:
        """获取请求头"""
        # 使用正确的ISO格式时间戳
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        signature = self.generate_signature(timestamp, method, request_path, body)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        if self.sandbox:
            headers['x-simulated-trading'] = '1'
            
        return headers
    
    def make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        body = json.dumps(params, separators=(',', ':')) if params else ''
        headers = self.get_headers(method, endpoint, body)
        
        try:
            logger.info(f"Making {method} request to {endpoint}")
            logger.info(f"Request body: {body}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            else:
                response = self.session.post(url, headers=headers, data=body)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # 检查OKX API响应码
            if result.get('code') != '0':
                logger.error(f"OKX API error: code={result.get('code')}, msg={result.get('msg')}")
                
            return result
            
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"code": "error", "msg": str(e)}
    
    def test_api_connection(self) -> Dict:
        """测试API连接"""
        try:
            # 首先测试公共API（不需要认证）
            public_test = self.make_request('GET', '/api/v5/public/time')
            if public_test.get('code') != '0':
                return {"success": False, "message": f"Public API failed: {public_test.get('msg')}"}
            
            # 测试私有API（需要认证）
            balance_test = self.get_account_balance()
            if balance_test.get('code') != '0':
                return {"success": False, "message": f"Private API failed: {balance_test.get('msg')}"}
            
            return {"success": True, "message": "API connection successful"}
            
        except Exception as e:
            return {"success": False, "message": f"Connection test failed: {str(e)}"}
    
    def get_account_balance(self) -> Dict:
        """获取账户余额"""
        return self.make_request('GET', '/api/v5/account/balance')
    
    def get_ticker(self, inst_id: str) -> Dict:
        """获取行情数据"""
        params = {'instId': inst_id}
        return self.make_request('GET', '/api/v5/market/ticker', params)
    
    def check_trading_conditions(self) -> bool:
        """检查交易条件"""
        current_time = time.time()
        
        # 检查是否启用交易
        if not self.trading_enabled:
            logger.info("Trading is disabled")
            return False
        
        # 检查交易间隔
        if current_time - self.last_trade_time < self.min_trade_interval:
            logger.info(f"Too soon to trade. Last trade: {self.last_trade_time}")
            return False
        
        # 重置每日交易计数
        if current_time > self.daily_reset_time + 86400:  # 24小时
            self.daily_trades = 0
            self.daily_reset_time = current_time
        
        # 检查每日交易次数
        if self.daily_trades >= self.max_trades_per_day:
            logger.info(f"Daily trade limit reached: {self.daily_trades}")
            return False
        
        return True
    
    def get_instrument_info(self, inst_id: str) -> Dict:
        """获取交易对信息"""
        params = {'instType': 'SPOT', 'instId': inst_id}
        return self.make_request('GET', '/api/v5/public/instruments', params)
    
    def calculate_trade_size(self, inst_id: str, current_price: float) -> float:
        """计算交易数量"""
        try:
            # 获取账户余额
            balance_response = self.get_account_balance()
            if balance_response.get('code') != '0':
                logger.error(f"Failed to get balance: {balance_response}")
                return 0
            
            # 查找USDT余额
            usdt_balance = 0
            for detail in balance_response.get('data', [{}])[0].get('details', []):
                if detail.get('ccy') == 'USDT':
                    usdt_balance = float(detail.get('availBal', 0))
                    break
            
            # 计算交易金额（不超过余额和设定金额）
            trade_amount = min(self.trade_amount_usdt, usdt_balance * 0.9)  # 90%的余额
            
            # OKX最小订单金额要求更新：
            # - 现货市价单：5 USDT（实盘）
            # - 模拟交易：可能要求更高，我们使用 50 USDT 确保成功
            min_order_amount = 50 if self.sandbox else 5
            if trade_amount < min_order_amount:
                logger.warning(f"Trade amount {trade_amount} below minimum order amount {min_order_amount} USDT")
                logger.warning(f"Available balance: {usdt_balance} USDT")
                logger.warning(f"Sandbox mode: {self.sandbox}")
                return 0
            
            # 获取交易对信息，检查最小下单量和最小订单金额
            inst_info = self.get_instrument_info(inst_id)
            if inst_info.get('code') == '0' and inst_info.get('data'):
                data = inst_info['data'][0]
                min_size = float(data.get('minSz', 0))
                lot_sz = data.get('lotSz', '1')
                
                # 检查最小市价订单金额（现货交易）
                max_mkt_amt = data.get('maxMktAmt', '')
                if max_mkt_amt:
                    # OKX现货市价单最小金额：实盘5 USDT，模拟环境可能更高
                    min_market_amount = 50 if self.sandbox else 5
                    if trade_amount < min_market_amount:
                        logger.warning(f"Trade amount {trade_amount} below minimum market order amount {min_market_amount} USDT (sandbox: {self.sandbox})")
                        return 0
                
                # 计算币种数量
                trade_size = trade_amount / current_price
                
                # 确保交易数量符合最小下单量要求
                if trade_size < min_size:
                    logger.warning(f"Trade size {trade_size} below minimum size {min_size} for {inst_id}")
                    # 尝试使用最小下单量
                    trade_size = min_size
                    trade_amount = trade_size * current_price
                    logger.info(f"Adjusted to minimum size: {trade_size}, amount: {trade_amount:.2f} USDT")
                
                # 根据lotSz调整精度
                if '.' in lot_sz:
                    decimal_places = len(lot_sz.split('.')[1])
                    trade_size = round(trade_size, decimal_places)
                else:
                    trade_size = int(trade_size)
                
                # 最终检查：确保调整后的金额仍然满足最小要求
                final_amount = trade_size * current_price
                if final_amount < min_order_amount:
                    logger.warning(f"Final order amount {final_amount:.2f} USDT still below minimum {min_order_amount} USDT")
                    return 0
                
                logger.info(f"Calculated trade size: {trade_size} for {final_amount:.2f} USDT at price {current_price}")
                return trade_size
            else:
                logger.error(f"Failed to get instrument info for {inst_id}")
                return 0
            
        except Exception as e:
            logger.error(f"Failed to calculate trade size: {e}")
            return 0
    
    def place_market_order(self, inst_id: str, side: str, size: float) -> Dict:
        """下市价单"""
        # 确保数量格式正确
        formatted_size = f"{size:.8f}".rstrip('0').rstrip('.')
        
        params = {
            'instId': inst_id,
            'tdMode': 'cash',  # 现货交易
            'side': side,      # buy 或 sell
            'ordType': 'market',
            'sz': formatted_size
        }
        
        logger.info(f"Placing {side} order: {formatted_size} {inst_id}")
        logger.info(f"Order parameters: {params}")
        
        result = self.make_request('POST', '/api/v5/trade/order', params)
        
        # 详细记录下单结果
        if result.get('code') == '0':
            logger.info(f"✅ Order placed successfully: {result}")
        else:
            logger.error(f"❌ Order failed: code={result.get('code')}, msg={result.get('msg')}")
            if result.get('data'):
                logger.error(f"Error details: {result['data']}")
        
        return result
    
    def place_limit_order(self, inst_id: str, side: str, size: float, price: float) -> Dict:
        """下限价单"""
        # 确保数量格式正确
        formatted_size = f"{size:.8f}".rstrip('0').rstrip('.')
        formatted_price = f"{price:.1f}"
        
        params = {
            'instId': inst_id,
            'tdMode': 'cash',  # 现货交易
            'side': side,      # buy 或 sell
            'ordType': 'limit',
            'sz': formatted_size,
            'px': formatted_price
        }
        
        logger.info(f"Placing {side} limit order: {formatted_size} {inst_id} at {formatted_price}")
        logger.info(f"Order parameters: {params}")
        
        result = self.make_request('POST', '/api/v5/trade/order', params)
        
        # 详细记录下单结果
        if result.get('code') == '0':
            logger.info(f"✅ Limit order placed successfully: {result}")
        else:
            logger.error(f"❌ Limit order failed: code={result.get('code')}, msg={result.get('msg')}")
            if result.get('data'):
                logger.error(f"Error details: {result['data']}")
        
        return result
    
    def place_market_order_as_limit(self, inst_id: str, side: str, size: float) -> Dict:
        """使用限价单模拟市价单（沙盒环境解决方案）"""
        try:
            # 获取当前价格
            ticker_response = self.make_request('GET', '/api/v5/market/ticker', {
                'instId': inst_id
            })
            
            if ticker_response.get('code') != '0':
                logger.error(f"Failed to get current price for {inst_id}")
                return ticker_response
            
            current_price = float(ticker_response['data'][0]['last'])
            
            # 买入时使用稍高的价格，卖出时使用稍低的价格，确保能成交
            # 沙盒环境对价格限制更严格，使用更小的溢价
            if side == 'buy':
                limit_price = current_price * 1.005  # 高出0.5%
            else:
                limit_price = current_price * 0.995  # 低于0.5%
            
            logger.info(f"Using limit order to simulate market order: {side} at {limit_price:.1f} (market: {current_price:.1f})")
            
            return self.place_limit_order(inst_id, side, size, limit_price)
            
        except Exception as e:
            logger.error(f"Failed to place market-like limit order: {e}")
            return {'code': 'error', 'msg': str(e)}
    
    def buy_signal_triggered(self, inst_id: str, current_price: float, signal_strength: int) -> Dict:
        """处理买入信号"""
        try:
            # 检查交易条件
            if not self.check_trading_conditions():
                return {"success": False, "message": "Trading conditions not met"}
            
            # 检查是否已持有该币种
            if inst_id in self.open_positions:
                logger.info(f"Already holding {inst_id}, skipping buy signal")
                return {"success": False, "message": "Already holding position"}
            
            # 计算交易数量
            trade_size = self.calculate_trade_size(inst_id, current_price)
            if trade_size <= 0:
                return {"success": False, "message": "Invalid trade size"}
            
            # 下买单 - 在沙盒环境使用限价单模拟市价单
            if self.sandbox:
                order_response = self.place_market_order_as_limit(inst_id, 'buy', trade_size)
            else:
                order_response = self.place_market_order(inst_id, 'buy', trade_size)
            
            if order_response.get('code') == '0':
                order_id = order_response['data'][0]['ordId']
                
                # 记录交易
                trade_record = {
                    'timestamp': time.time(),
                    'inst_id': inst_id,
                    'side': 'buy',
                    'size': trade_size,
                    'price': current_price,
                    'order_id': order_id,
                    'signal_strength': signal_strength
                }
                
                self.trade_history.append(trade_record)
                self.open_positions[inst_id] = trade_record
                self.last_trade_time = time.time()
                self.daily_trades += 1
                
                logger.info(f"✅ Buy order placed successfully: {inst_id} at {current_price}")
                return {"success": True, "order_id": order_id, "message": f"Bought {trade_size:.6f} {inst_id}"}
            
            else:
                error_msg = order_response.get('msg', 'Unknown error')
                logger.error(f"❌ Buy order failed: {error_msg}")
                return {"success": False, "message": f"Order failed: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Error in buy signal: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def sell_signal_triggered(self, inst_id: str, current_price: float, signal_strength: int) -> Dict:
        """处理卖出信号"""
        try:
            # 检查是否持有该币种
            if inst_id not in self.open_positions:
                logger.info(f"No position for {inst_id}, skipping sell signal")
                return {"success": False, "message": "No position to sell"}
            
            position = self.open_positions[inst_id]
            trade_size = position['size']
            
            # 下卖单 - 在沙盒环境使用限价单模拟市价单
            if self.sandbox:
                order_response = self.place_market_order_as_limit(inst_id, 'sell', trade_size)
            else:
                order_response = self.place_market_order(inst_id, 'sell', trade_size)
            
            if order_response.get('code') == '0':
                order_id = order_response['data'][0]['ordId']
                
                # 计算盈亏
                buy_price = position['price']
                profit_percent = ((current_price - buy_price) / buy_price) * 100
                
                # 记录交易
                trade_record = {
                    'timestamp': time.time(),
                    'inst_id': inst_id,
                    'side': 'sell',
                    'size': trade_size,
                    'price': current_price,
                    'order_id': order_id,
                    'signal_strength': signal_strength,
                    'profit_percent': profit_percent,
                    'buy_price': buy_price
                }
                
                self.trade_history.append(trade_record)
                del self.open_positions[inst_id]
                self.last_trade_time = time.time()
                self.daily_trades += 1
                
                logger.info(f"✅ Sell order placed successfully: {inst_id} at {current_price}, Profit: {profit_percent:.2f}%")
                return {
                    "success": True, 
                    "order_id": order_id, 
                    "message": f"Sold {trade_size:.6f} {inst_id}, Profit: {profit_percent:.2f}%",
                    "profit_percent": profit_percent
                }
            
            else:
                error_msg = order_response.get('msg', 'Unknown error')
                logger.error(f"❌ Sell order failed: {error_msg}")
                return {"success": False, "message": f"Order failed: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Error in sell signal: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    def check_stop_loss_take_profit(self, inst_id: str, current_price: float) -> Optional[Dict]:
        """检查止损止盈"""
        if inst_id not in self.open_positions:
            return None
            
        position = self.open_positions[inst_id]
        buy_price = position['price']
        
        # 计算当前盈亏百分比
        profit_percent = ((current_price - buy_price) / buy_price) * 100
        
        # 止损检查
        if profit_percent <= -self.stop_loss_percent:
            logger.warning(f"Stop loss triggered for {inst_id}: {profit_percent:.2f}%")
            return self.sell_signal_triggered(inst_id, current_price, 0)
        
        # 止盈检查
        if profit_percent >= self.take_profit_percent:
            logger.info(f"Take profit triggered for {inst_id}: {profit_percent:.2f}%")
            return self.sell_signal_triggered(inst_id, current_price, 0)
        
        return None
    
    def get_trading_status(self) -> Dict:
        """获取交易状态"""
        return {
            'trading_enabled': self.trading_enabled,
            'daily_trades': self.daily_trades,
            'max_trades_per_day': self.max_trades_per_day,
            'open_positions': len(self.open_positions),
            'positions': list(self.open_positions.keys()),
            'last_trade_time': self.last_trade_time,
            'trade_history_count': len(self.trade_history)
        }
    
    def enable_trading(self):
        """启用交易"""
        self.trading_enabled = True
        logger.info("🟢 Trading enabled")
    
    def disable_trading(self):
        """禁用交易"""
        self.trading_enabled = False
        logger.info("🔴 Trading disabled")
