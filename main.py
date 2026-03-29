import os
import json
import time
import hmac
import hashlib
import requests
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import threading
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

class BinanceFuturesAPI:
    """Binance合约API客户端"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """
        初始化Binance合约API客户端
        
        Args:
            api_key: Binance API密钥
            api_secret: Binance API密钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("请提供Binance API密钥或在.env文件中设置BINANCE_API_KEY和BINANCE_API_SECRET")
        
        # 设置API基础URL
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
            
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key
        })
    
    def _generate_signature(self, params: Dict) -> str:
        """生成API签名"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """发送API请求"""
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                # Binance API需要使用data参数而不是json参数
                response = self.session.post(url, data=params)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"响应内容: {e.response.text}")
            raise
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_balance(self) -> List[Dict]:
        """获取账户余额"""
        return self._make_request('GET', '/fapi/v2/balance', signed=True)
    
    def get_positions(self) -> List[Dict]:
        """获取持仓信息"""
        return self._make_request('GET', '/fapi/v2/positionRisk', signed=True)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """获取当前挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """获取订单历史"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/allOrders', params, signed=True)
    
    def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """获取交易历史"""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/userTrades', params, signed=True)
    
    def get_funding_rates(self) -> List[Dict]:
        """获取所有交易对的资金费率"""
        return self._make_request('GET', '/fapi/v1/premiumIndex', signed=False)
    
    def get_klines(self, symbol: str, interval: str = '1d', limit: int = 100) -> List[List]:
        """获取K线数据"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/klines', params, signed=False)
    
    def get_symbol_funding_rate(self, symbol: str) -> Dict:
        """获取指定交易对的资金费率"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/premiumIndex', params, signed=False)
    
    def get_top_long_short_position_ratio(self, symbol: str, period: str = '5m', limit: int = 10) -> List[Dict]:
        """获取大户持仓量多空比数据"""
        # 直接使用完整URL，不通过_make_request
        url = f"{self.base_url}/futures/data/topLongShortPositionRatio"
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取大户持仓多空比失败: {e}")
            return []
    
    def get_top_long_short_account_ratio(self, symbol: str, period: str = '5m', limit: int = 10) -> List[Dict]:
        """获取多空账户人数比数据"""
        # 直接使用完整URL，不通过_make_request
        url = f"{self.base_url}/futures/data/topLongShortAccountRatio"
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取账户多空比失败: {e}")
            return []

    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """设置杠杆倍数"""
        params = {
            'symbol': symbol,
            'leverage': str(leverage)  # Binance API需要字符串格式
        }
        
        try:
            return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
        except Exception as e:
            error_msg = str(e)
            if "-4028" in error_msg:
                logging.info(f"{symbol} 杠杆已经是目标倍数")
                return {"msg": "杠杆已经是目标倍数"}
            logging.error(f"设置杠杆失败: {e}")
            raise

    def change_margin_type(self, symbol: str, margin_type: str = 'CROSSED') -> Dict:
        """更改保证金模式"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        
        try:
            return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
        except Exception as e:
            error_msg = str(e)
            if "No need to change margin type" in error_msg or "-4046" in error_msg:
                logging.info(f"{symbol} 保证金类型已经是目标类型")
                return {"msg": "保证金类型已经是目标类型"}
            elif "-4168" in error_msg:
                logging.info(f"{symbol} 在多资产模式下自动使用全仓模式")
                return {"msg": "多资产模式下自动使用全仓模式"}
            logging.error(f"更改保证金模式失败: {e}")
            raise

    def get_symbol_info(self, symbol: str) -> Dict:
        """获取交易对信息"""
        try:
            exchange_info = self._make_request('GET', '/fapi/v1/exchangeInfo', signed=False)
            for s in exchange_info.get('symbols', []):
                if s.get('symbol') == symbol:
                    return s
            return None
        except Exception as e:
            logging.error(f"获取交易对信息失败: {e}")
            return None

    def get_position_mode(self) -> str:
        """获取持仓模式"""
        try:
            result = self._make_request('GET', '/fapi/v1/positionSide/dual', signed=True)
            return "hedge" if result.get('dualSidePosition') else "oneway"
        except Exception as e:
            logging.warning(f"获取持仓模式失败，默认使用单向模式: {e}")
            return "oneway"

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float = None, 
                   quoteOrderQty: float = None, price: float = None, time_in_force: str = 'GTC') -> Dict:
        """下单"""
        params = {
            'symbol': symbol,
            'side': side,  # BUY or SELL
            'type': order_type  # MARKET, LIMIT, etc.
        }
        
        # 检查持仓模式，如果是对冲模式需要指定positionSide
        position_mode = self.get_position_mode()
        if position_mode == "hedge":
            # 对冲模式下需要指定持仓方向
            if side == 'BUY':
                params['positionSide'] = 'LONG'
            else:  # SELL
                params['positionSide'] = 'SHORT'
            logging.info(f"对冲模式下设置 positionSide: {params['positionSide']}")
        
        # 如果使用按金额下单但没有quantity，需要计算quantity
        if quoteOrderQty and not quantity and order_type == 'MARKET':
            try:
                # 获取当前价格
                ticker = self._make_request('GET', '/fapi/v1/ticker/price', {'symbol': symbol}, signed=False)
                current_price = float(ticker.get('price', 0))
                
                # 获取交易对信息以确定精度
                symbol_info = self.get_symbol_info(symbol)
                if symbol_info:
                    # 获取数量精度
                    for f in symbol_info.get('filters', []):
                        if f.get('filterType') == 'LOT_SIZE':
                            step_size = float(f.get('stepSize', '0.001'))
                            break
                    else:
                        step_size = 0.001
                    
                    # 计算数量
                    calculated_quantity = quoteOrderQty / current_price
                    
                    # 获取最小数量要求
                    min_qty = 0
                    for f in symbol_info.get('filters', []):
                        if f.get('filterType') == 'MIN_NOTIONAL':
                            min_notional = float(f.get('notional', '0'))
                            min_qty = max(min_qty, min_notional / current_price)
                        elif f.get('filterType') == 'LOT_SIZE':
                            min_qty = max(min_qty, float(f.get('minQty', '0')))
                    
                    # 确保数量满足最小要求
                    if calculated_quantity < min_qty:
                        calculated_quantity = min_qty
                        logging.info(f"调整数量到最小值: {calculated_quantity}")
                    
                    # 向下舍入到步长精度
                    import math
                    calculated_quantity = math.floor(calculated_quantity / step_size) * step_size
                    
                    if calculated_quantity > 0:
                        # 确定小数位数
                        decimal_places = max(0, -int(math.log10(step_size)))
                        params['quantity'] = f"{calculated_quantity:.{decimal_places}f}"
                        logging.info(f"计算得出 {symbol} 数量: {params['quantity']}")
                    else:
                        logging.warning(f"计算的数量太小: {calculated_quantity}，回退使用 quoteOrderQty")
                        # 回退使用 quoteOrderQty，让交易所自己计算
                        params['quoteOrderQty'] = str(quoteOrderQty)
                        
            except Exception as e:
                logging.error(f"计算订单数量失败: {e}")
                # 如果计算失败，回退使用quoteOrderQty
                params['quoteOrderQty'] = str(quoteOrderQty)
        else:
            # Binance API需要字符串格式的数值
            if quantity:
                params['quantity'] = str(quantity)
            if quoteOrderQty:
                params['quoteOrderQty'] = str(quoteOrderQty)
                
        if price:
            params['price'] = str(price)
        if order_type == 'LIMIT':
            params['timeInForce'] = time_in_force
            
        try:
            return self._make_request('POST', '/fapi/v1/order', params, signed=True)
        except Exception as e:
            logging.error(f"下单失败: {e}")
            raise

    def get_position_info(self, symbol: str) -> Dict:
        """获取指定交易对的持仓信息"""
        positions = self.get_positions()
        for position in positions:
            if position.get('symbol') == symbol:
                return position
        return None

    def close_position(self, symbol: str, position_side: str = None) -> Dict:
        """平仓指定交易对的持仓"""
        try:
            # 获取当前持仓信息
            position = self.get_position_info(symbol)
            if not position:
                raise ValueError(f"未找到 {symbol} 的持仓信息")
            
            position_amt = float(position.get('positionAmt', 0))
            if abs(position_amt) == 0:
                raise ValueError(f"{symbol} 当前没有持仓")
            
            # 获取持仓模式
            position_mode = self.get_position_mode()
            
            # 确定平仓参数
            if position_amt > 0:  # 多头持仓，需要卖出平仓
                side = 'SELL'
                close_position_side = 'LONG' if position_mode == 'hedge' else None
                logging.info(f"📈 {symbol} 多头持仓平仓，执行卖出操作")
            else:  # 空头持仓，需要买入平仓
                side = 'BUY'
                close_position_side = 'SHORT' if position_mode == 'hedge' else None
                logging.info(f"📉 {symbol} 空头持仓平仓，执行买入操作（这是平仓，不是开新仓）")
            
            # 如果指定了position_side，使用指定的
            if position_side:
                close_position_side = position_side
            
            # 构建平仓订单参数
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': str(abs(position_amt))  # 使用绝对值
            }
            
            # 对冲模式下需要指定positionSide
            if position_mode == 'hedge' and close_position_side:
                params['positionSide'] = close_position_side
                logging.info(f"对冲模式下平仓设置 positionSide: {close_position_side}")
            
            logging.info(f"准备平仓 {symbol}: {side} {abs(position_amt)}")
            
            # 执行平仓订单
            result = self._make_request('POST', '/fapi/v1/order', params, signed=True)
            logging.info(f"平仓成功: {result}")
            
            return result
            
        except Exception as e:
            logging.error(f"平仓 {symbol} 失败: {e}")
            raise
    
    def debug_funding_rates(self, limit: int = 5) -> None:
        """调试函数：查看资金费率数据结构"""
        try:
            funding_rates = self.get_funding_rates()
            print(f"📊 获取到 {len(funding_rates) if funding_rates else 0} 个交易对的数据")
            
            if funding_rates and len(funding_rates) > 0:
                print("\n🔍 前几个交易对的数据结构:")
                for i, item in enumerate(funding_rates[:limit]):
                    print(f"\n--- 交易对 {i+1} ---")
                    print(f"完整数据: {item}")
                    if isinstance(item, dict):
                        print(f"symbol: {item.get('symbol', 'N/A')}")
                        print(f"lastFundingRate: {item.get('lastFundingRate', 'N/A')}")
                        print(f"markPrice: {item.get('markPrice', 'N/A')}")
                        print(f"nextFundingTime: {item.get('nextFundingTime', 'N/A')}")
            else:
                print("❌ 未获取到任何数据或数据为空")
                
        except Exception as e:
            print(f"❌ 调试资金费率数据失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")

    def get_server_time(self) -> int:
        """获取Binance服务器时间(毫秒)"""
        try:
            result = self._make_request('GET', '/fapi/v1/time', signed=False)
            return result.get('serverTime', int(time.time() * 1000))
        except Exception:
            return int(time.time() * 1000)

    def fast_close_position(self, symbol: str, quantity: float, direction: str, position_mode: str = 'oneway') -> Dict:
        """
        快速平仓 - 跳过持仓查询，直接下反向市价单
        用于资金费率套利的极速平仓场景

        Args:
            symbol: 交易对
            quantity: 持仓数量(正数)
            direction: 持仓方向 'LONG' 或 'SHORT'
            position_mode: 持仓模式 'hedge' 或 'oneway'
        """
        side = 'SELL' if direction == 'LONG' else 'BUY'

        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': str(quantity)
        }

        if position_mode == 'hedge':
            params['positionSide'] = direction  # 'LONG' or 'SHORT'

        return self._make_request('POST', '/fapi/v1/order', params, signed=True)

    def get_24hr_ticker(self) -> List[Dict]:
        """获取24小时价格变动统计"""
        return self._make_request('GET', '/fapi/v1/ticker/24hr', signed=False)

    def get_order_book(self, symbol: str, limit: int = 5) -> Dict:
        """获取订单簿深度数据，用于估算买卖价差和滑点"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/depth', params, signed=False)

    def get_funding_rate_history(self, symbol: str, limit: int = 5) -> List[Dict]:
        """获取历史资金费率，用于分析费率趋势"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/fundingRate', params, signed=False)

    def get_book_ticker(self, symbol: str = None) -> Dict:
        """获取最优挂单价格(最佳买卖价)，比order book更轻量"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/ticker/bookTicker', params, signed=False)

class AutoTradingBot:
    """
    资金费率套利机器人 v3.0 - 量化增强版

    核心优化:
    1. 净利润估算过滤 (funding_fee - taker_fee×2 - spread_cost > 0)
    2. 波动率风险过滤 (ATR/price 过高则跳过)
    3. 动态仓位管理 (按预期净利润比例分配)
    4. 多因子候选评分 (净利润 × 流动性 × 费率趋势)
    5. 完整P&L追踪
    6. 多采样时间同步
    7. 指数退避重试
    """

    # Binance taker fee (VIP0, 含BNB抵扣约0.036%)
    TAKER_FEE_RATE = 0.0004  # 0.04% 保守估计
    # 最大可接受的买卖价差占比
    MAX_SPREAD_RATIO = 0.001  # 0.1%
    # 波动率安全倍数: ATR/price 不能超过 funding_rate × 此倍数
    VOLATILITY_SAFETY_MULTIPLE = 3.0

    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """初始化资金费率套利机器人"""
        self.api = BinanceFuturesAPI(api_key, api_secret, testnet)
        self.running = False

        # 基础交易参数
        self.trade_amount = float(os.getenv('TRADE_AMOUNT', '100'))
        self.leverage = int(os.getenv('LEVERAGE', '20'))
        self.min_funding_rate = float(os.getenv('MIN_FUNDING_RATE', '0.0005'))
        self.open_before_seconds = float(os.getenv('OPEN_BEFORE_SECONDS', '2'))
        self.close_after_seconds = float(os.getenv('CLOSE_AFTER_SECONDS', '0.5'))
        self.pre_scan_minutes = float(os.getenv('PRE_SCAN_MINUTES', '3'))
        self.max_positions = int(os.getenv('MAX_POSITIONS', '5'))

        # v3.0 量化增强参数
        self.min_net_profit_rate = float(os.getenv('MIN_NET_PROFIT_RATE', '0.0001'))  # 最小净利润率 0.01%
        self.max_spread_ratio = float(os.getenv('MAX_SPREAD_RATIO', str(self.MAX_SPREAD_RATIO)))
        self.dynamic_sizing = os.getenv('DYNAMIC_SIZING', 'true').lower() == 'true'
        self.min_volume_usdt = float(os.getenv('MIN_VOLUME_USDT', '50000000'))  # 最小24h成交量

        # 止盈止损参数
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PCT', '5.0'))  # 止盈百分比
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PCT', '5.0'))  # 止损百分比
        self.tp_sl_check_interval = float(os.getenv('TP_SL_CHECK_INTERVAL', '1.0'))  # 检查间隔(秒)

        # 时间同步 (多采样)
        self.time_offset = 0
        self.time_sync_samples = 3

        # 持仓模式缓存
        self.position_mode = None

        # 本轮开仓记录
        self.round_positions = []

        # P&L追踪
        self.session_pnl = []  # [{round, timestamp, candidates, opened, funding_est, fees_est, net_est}, ...]
        self.round_counter = 0

        # 24h ticker 缓存 (每轮扫描时更新)
        self._ticker_cache = {}
        self._ticker_cache_time = 0

        # 黑名单设置
        self.load_blacklist()

        logging.info("=" * 60)
        logging.info("🧠 资金费率套利机器人 v3.0 (量化增强版) 初始化")
        logging.info(f"📋 策略: 结算前{self.open_before_seconds}秒开仓, 止盈{self.take_profit_pct}%/止损{self.stop_loss_pct}%平仓")
        logging.info(f"💰 每笔: {self.trade_amount} USDT, 杠杆: {self.leverage}x")
        logging.info(f"📊 最小费率: {self.min_funding_rate*100:.3f}%, 最小净利润率: {self.min_net_profit_rate*100:.4f}%")
        logging.info(f"📊 最大价差: {self.max_spread_ratio*100:.2f}%, 最小成交量: {self.min_volume_usdt/1e6:.0f}M USDT")
        logging.info(f"📊 动态仓位: {'开启' if self.dynamic_sizing else '关闭'}")

        if self.blacklist:
            logging.info(f"🚫 当前黑名单: {list(self.blacklist)}")
        logging.info("=" * 60)

    def setup_margin_modes(self, symbols: List[str] = None) -> Dict[str, bool]:
        """批量设置交易对为全仓模式"""
        if symbols is None:
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT',
                'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT', 'LINKUSDT', 'LTCUSDT'
            ]

        results = {}
        logging.info(f"开始为 {len(symbols)} 个交易对设置全仓模式...")

        for symbol in symbols:
            try:
                position = self.api.get_position_info(symbol)
                if position and abs(float(position.get('positionAmt', 0))) > 0:
                    results[symbol] = False
                    logging.warning(f"⚠️ {symbol} 有持仓，跳过")
                    continue

                self.api.change_margin_type(symbol, 'CROSSED')
                results[symbol] = True
                logging.info(f"✅ {symbol} 已设置为全仓模式")

            except Exception as e:
                error_msg = str(e)
                if "-4046" in error_msg or "No need to change margin type" in error_msg:
                    results[symbol] = True
                    logging.info(f"✅ {symbol} 已是全仓模式")
                elif "-4168" in error_msg:
                    results[symbol] = True
                    logging.info(f"✅ {symbol} 多资产模式自动全仓")
                else:
                    results[symbol] = False
                    logging.error(f"❌ {symbol} 设置失败: {e}")

        success_count = sum(results.values())
        logging.info(f"保证金模式设置完成: {success_count}/{len(symbols)} 成功")
        return results

    def load_blacklist(self):
        """从.env文件加载黑名单币种"""
        try:
            blacklist_str = os.getenv('BLACKLIST_SYMBOLS', '')
            if blacklist_str:
                blacklist_symbols = [s.strip().upper() for s in blacklist_str.split(',') if s.strip()]
                self.blacklist = set()
                for symbol in blacklist_symbols:
                    if not symbol.endswith('USDT'):
                        symbol = symbol + 'USDT'
                    self.blacklist.add(symbol)
                if self.blacklist:
                    logging.info(f"📋 加载黑名单: {list(self.blacklist)}")
            else:
                self.blacklist = set()
        except Exception as e:
            logging.error(f"加载黑名单失败: {e}")
            self.blacklist = set()

    def debug_blacklist(self):
        """调试黑名单设置"""
        blacklist_env = os.getenv('BLACKLIST_SYMBOLS', '')
        logging.info(f"🔍 BLACKLIST_SYMBOLS: '{blacklist_env}'")
        logging.info(f"🔍 解析后: {list(self.blacklist)}")
        return self.blacklist

    def get_usdt_balance(self) -> float:
        """获取USDT可用余额"""
        try:
            balance_data = self.api.get_balance()
            for balance in balance_data:
                if balance.get('asset') == 'USDT':
                    return float(balance.get('availableBalance', 0))
            return 0.0
        except Exception as e:
            logging.error(f"获取USDT余额失败: {e}")
            return 0.0

    def has_position(self, symbol: str) -> bool:
        """检查是否已有持仓"""
        try:
            positions = self.api.get_positions()
            if not positions:
                return False

            for position in positions:
                if position.get('symbol') == symbol:
                    position_amt = float(position.get('positionAmt', 0))
                    if abs(position_amt) > 0.0001:
                        side = "做空" if position_amt < 0 else "做多"
                        logging.info(f"🔍 {symbol} 已有持仓: {side} {abs(position_amt)}")
                        return True
            return False
        except Exception as e:
            logging.error(f"检查 {symbol} 持仓失败: {e}")
            return True  # 出错时保守处理

    # ============================================================
    # 资金费率套利核心方法
    # ============================================================

    def sync_server_time(self):
        """多采样时间同步，取延迟最低的样本以获得最精确偏移"""
        try:
            best_latency = float('inf')
            best_offset = 0

            for _ in range(self.time_sync_samples):
                local_before = int(time.time() * 1000)
                server_time = self.api.get_server_time()
                local_after = int(time.time() * 1000)

                latency = (local_after - local_before) / 2
                local_mid = (local_before + local_after) / 2
                offset = local_mid - server_time

                if latency < best_latency:
                    best_latency = latency
                    best_offset = offset

            self.time_offset = best_offset
            logging.info(f"⏱ 时间同步({self.time_sync_samples}采样): 偏移={self.time_offset:.0f}ms, 最佳延迟={best_latency:.0f}ms")
        except Exception as e:
            logging.error(f"时间同步失败: {e}")
            self.time_offset = 0

    def get_server_time_ms(self) -> int:
        """获取当前服务器时间(毫秒)，基于缓存偏移计算"""
        return int(time.time() * 1000 - self.time_offset)

    def get_upcoming_settlements(self) -> Dict[int, List[Dict]]:
        """
        获取即将到来的资金费率结算信息
        返回: {结算时间戳ms: [{symbol, rate}, ...]}
        """
        try:
            funding_rates = self.api.get_funding_rates()
            if not funding_rates:
                return {}

            settlements = {}
            now = self.get_server_time_ms()

            for data in funding_rates:
                symbol = data.get('symbol', '')
                if not symbol.endswith('USDT'):
                    continue
                if symbol in self.blacklist:
                    continue

                next_time = int(data.get('nextFundingTime', 0))
                rate = float(data.get('lastFundingRate', 0))

                if next_time <= now:
                    continue

                if next_time not in settlements:
                    settlements[next_time] = []

                settlements[next_time].append({
                    'symbol': symbol,
                    'rate': rate
                })

            return settlements
        except Exception as e:
            logging.error(f"获取结算时间失败: {e}")
            return {}

    # ============================================================
    # v3.0 量化增强方法
    # ============================================================

    def _refresh_ticker_cache(self):
        """刷新24h ticker缓存，避免重复请求"""
        now = time.time()
        if now - self._ticker_cache_time > 60:  # 60秒缓存
            try:
                tickers = self.api.get_24hr_ticker()
                self._ticker_cache = {t['symbol']: t for t in tickers if 'symbol' in t}
                self._ticker_cache_time = now
            except Exception as e:
                logging.warning(f"刷新ticker缓存失败: {e}")

    def estimate_spread_cost(self, symbol: str) -> float:
        """
        估算买卖价差成本 (占价格的比例)
        使用bookTicker获取最优买卖价，比完整order book更快
        """
        try:
            book = self.api.get_book_ticker(symbol)
            if not book:
                return self.max_spread_ratio  # 无数据时返回上限

            best_bid = float(book.get('bidPrice', 0))
            best_ask = float(book.get('askPrice', 0))

            if best_bid <= 0 or best_ask <= 0:
                return self.max_spread_ratio

            mid_price = (best_bid + best_ask) / 2
            spread_ratio = (best_ask - best_bid) / mid_price

            return spread_ratio
        except Exception:
            return self.max_spread_ratio

    def estimate_net_profit_rate(self, funding_rate: float, spread_ratio: float) -> float:
        """
        估算单次套利净利润率

        净利润 = |funding_rate| - 2×taker_fee - spread_cost
        - funding_rate: 资金费率 (正或负，取绝对值)
        - 2×taker_fee: 开仓+平仓各一次taker手续费
        - spread_cost: 买卖价差导致的滑点成本 (开仓+平仓各一半spread)
        """
        gross = abs(funding_rate)
        fees = 2 * self.TAKER_FEE_RATE
        slippage = spread_ratio  # 开+平各吃半个spread ≈ 一个完整spread
        net = gross - fees - slippage
        return net

    def get_funding_rate_trend(self, symbol: str) -> float:
        """
        获取资金费率趋势强度
        返回: >0 表示费率在加强(更偏离0), <0 表示在回归0
        用最近3期的绝对值斜率衡量
        """
        try:
            history = self.api.get_funding_rate_history(symbol, limit=4)
            if not history or len(history) < 2:
                return 0.0

            rates = [abs(float(h.get('fundingRate', 0))) for h in history]
            # 简单线性趋势: 最新 vs 平均
            if len(rates) >= 3:
                recent_avg = sum(rates[-2:]) / 2
                older_avg = sum(rates[:-2]) / max(len(rates) - 2, 1)
                return recent_avg - older_avg
            else:
                return rates[-1] - rates[0]
        except Exception:
            return 0.0

    def calculate_position_amount(self, candidate: Dict) -> float:
        """
        动态仓位计算 (Kelly-inspired)

        基础仓位 = trade_amount
        调整因子 = clamp(net_profit_rate / min_net_profit_rate, 0.5, 2.0)
        最终仓位 = 基础仓位 × 调整因子

        净利润率越高 → 仓位越大 (上限2x), 刚过阈值 → 减半仓位
        """
        if not self.dynamic_sizing:
            return self.trade_amount

        net_rate = candidate.get('net_profit_rate', 0)
        if net_rate <= 0:
            return self.trade_amount * 0.5  # 安全兜底

        # 信心因子: net_profit / min_threshold
        confidence = net_rate / self.min_net_profit_rate
        factor = max(0.5, min(2.0, confidence))

        amount = self.trade_amount * factor
        return round(amount, 2)

    def score_candidate(self, candidate: Dict) -> float:
        """
        多因子候选评分

        score = net_profit_rate × (1 + trend_bonus) × liquidity_factor

        - net_profit_rate: 核心收益指标 (已扣除费用)
        - trend_bonus: 费率趋势加成 (强化中 +20%, 回归中 -20%)
        - liquidity_factor: 流动性因子 (成交量越大越好，log scale)
        """
        net_rate = candidate.get('net_profit_rate', 0)

        # 趋势加成
        trend = candidate.get('rate_trend', 0)
        if trend > 0:
            trend_bonus = min(0.2, trend * 100)  # 最多+20%
        elif trend < 0:
            trend_bonus = max(-0.2, trend * 100)  # 最多-20%
        else:
            trend_bonus = 0

        # 流动性因子 (log scale, 以5000万为基准)
        volume = candidate.get('volume_24h', 0)
        if volume > 0:
            import math
            liquidity_factor = math.log10(max(volume, 1e6)) / math.log10(5e7)
            liquidity_factor = max(0.5, min(1.5, liquidity_factor))
        else:
            liquidity_factor = 0.5

        score = net_rate * (1 + trend_bonus) * liquidity_factor
        return score

    def scan_funding_candidates(self, settlement_time: int) -> List[Dict]:
        """
        v3.0 增强候选扫描 - 多因子过滤+评分

        过滤条件:
        1. nextFundingTime == settlement_time
        2. |lastFundingRate| >= min_funding_rate (粗筛)
        3. 不在黑名单 & 无当前持仓
        4. 24h成交量 >= min_volume_usdt (流动性)
        5. 买卖价差 <= max_spread_ratio (滑点控制)
        6. 净利润率 >= min_net_profit_rate (成本过滤)

        评分: score_candidate() 多因子排序
        """
        candidates = []

        try:
            funding_rates = self.api.get_funding_rates()
            if not funding_rates:
                return candidates

            # 刷新ticker缓存
            self._refresh_ticker_cache()

            # 第一轮: 粗筛
            rough_candidates = []
            for data in funding_rates:
                symbol = data.get('symbol', '')
                if not symbol.endswith('USDT'):
                    continue
                if symbol in self.blacklist:
                    continue

                next_time = int(data.get('nextFundingTime', 0))
                if next_time != settlement_time:
                    continue

                rate = float(data.get('lastFundingRate', 0))
                if abs(rate) < self.min_funding_rate:
                    continue

                # 成交量粗筛 (使用缓存)
                ticker = self._ticker_cache.get(symbol, {})
                volume_24h = float(ticker.get('quoteVolume', 0))
                if volume_24h < self.min_volume_usdt:
                    continue

                rough_candidates.append({
                    'symbol': symbol,
                    'rate': rate,
                    'direction': 'LONG' if rate < 0 else 'SHORT',
                    'volume_24h': volume_24h,
                    'mark_price': float(data.get('markPrice', 0)),
                })

            logging.info(f"🔍 粗筛通过: {len(rough_candidates)} 个候选 (费率≥{self.min_funding_rate*100:.3f}%, 成交量≥{self.min_volume_usdt/1e6:.0f}M)")

            # 按费率绝对值预排序，只深度分析前 max_positions×3 个
            rough_candidates.sort(key=lambda x: abs(x['rate']), reverse=True)
            to_analyze = rough_candidates[:self.max_positions * 3]

            # 第二轮: 深度分析 (价差、净利润、趋势)
            for c in to_analyze:
                symbol = c['symbol']

                # 检查持仓
                if self.has_position(symbol):
                    logging.info(f"⏭ {symbol} 已有持仓，跳过")
                    continue

                # 估算价差成本
                spread = self.estimate_spread_cost(symbol)
                if spread > self.max_spread_ratio:
                    logging.debug(f"⏭ {symbol} 价差过大: {spread*100:.3f}%")
                    continue

                # 估算净利润率
                net_rate = self.estimate_net_profit_rate(c['rate'], spread)
                if net_rate < self.min_net_profit_rate:
                    logging.debug(f"⏭ {symbol} 净利润率不足: {net_rate*100:.4f}%")
                    continue

                # 费率趋势
                rate_trend = self.get_funding_rate_trend(symbol)

                c['spread'] = spread
                c['net_profit_rate'] = net_rate
                c['rate_trend'] = rate_trend
                c['score'] = self.score_candidate(c)

                candidates.append(c)

            # 按综合评分排序
            candidates.sort(key=lambda x: x['score'], reverse=True)
            candidates = candidates[:self.max_positions]

            # 详细日志
            for c in candidates:
                emoji = '📈' if c['direction'] == 'LONG' else '📉'
                logging.info(
                    f"  {emoji} {c['symbol']}: {c['direction']}, "
                    f"费率={c['rate']*100:.4f}%, 净利润≈{c['net_profit_rate']*100:.4f}%, "
                    f"价差={c['spread']*100:.3f}%, 评分={c['score']:.6f}"
                )

            return candidates

        except Exception as e:
            logging.error(f"扫描候选失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return candidates

    def execute_open_position(self, candidate: Dict) -> bool:
        """
        开仓 - 支持动态仓位
        Args:
            candidate: 候选字典 (包含symbol, direction, net_profit_rate等)
        """
        symbol = candidate['symbol']
        direction = candidate['direction']

        try:
            # 设置杠杆
            try:
                self.api.set_leverage(symbol, self.leverage)
            except Exception:
                pass

            # 动态仓位计算
            amount = self.calculate_position_amount(candidate)

            side = 'BUY' if direction == 'LONG' else 'SELL'

            order_result = self.api.place_order(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quoteOrderQty=amount
            )

            executed_qty = float(order_result.get('executedQty', 0))
            avg_price = float(order_result.get('avgPrice', 0)) if order_result.get('avgPrice') else 0
            emoji = '📈' if direction == 'LONG' else '📉'
            logging.info(f"{emoji} {symbol} {direction} 开仓成功, 数量={executed_qty}, 金额={amount} USDT, 均价={avg_price}")

            self.round_positions.append({
                'symbol': symbol,
                'direction': direction,
                'quantity': executed_qty,
                'amount': amount,
                'avg_price': avg_price,
                'rate': candidate.get('rate', 0),
                'net_profit_rate': candidate.get('net_profit_rate', 0),
            })

            return True

        except Exception as e:
            logging.error(f"❌ {symbol} {direction} 开仓失败: {e}")
            return False

    def open_positions_parallel(self, candidates: List[Dict]):
        """并行开仓所有候选"""
        if not candidates:
            return

        threads = []
        for c in candidates:
            t = threading.Thread(
                target=self.execute_open_position,
                args=(c,)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        logging.info(f"🚀 开仓完成: 成功 {len(self.round_positions)}/{len(candidates)} 个")

    def monitor_tp_sl(self):
        """
        监控持仓盈亏，达到止盈或止损阈值时平仓

        逻辑:
        - 每隔 tp_sl_check_interval 秒查询一次持仓
        - 对每个持仓计算收益率 = unRealizedProfit / amount
        - 收益率 >= take_profit_pct% → 止盈平仓
        - 收益率 <= -stop_loss_pct% → 止损平仓
        - 所有持仓都平完后返回
        """
        if not self.round_positions:
            return

        logging.info(f"📊 进入止盈止损监控 (止盈: +{self.take_profit_pct}%, 止损: -{self.stop_loss_pct}%)")

        pending = list(self.round_positions)
        self.round_positions = []
        closed_positions = []

        while pending and self.running:
            try:
                positions_data = self.api.get_positions()
            except Exception as e:
                logging.error(f"查询持仓失败: {e}")
                time.sleep(self.tp_sl_check_interval)
                continue

            # 建立 symbol -> position_data 的映射
            pos_map = {}
            for p in positions_data:
                sym = p.get('symbol')
                amt = float(p.get('positionAmt', 0))
                if abs(amt) > 0.0001:
                    pos_map[sym] = p

            to_close = []
            still_pending = []

            for pos in pending:
                symbol = pos['symbol']
                live = pos_map.get(symbol)

                if not live:
                    # 持仓已不存在（可能被手动平了）
                    logging.info(f"ℹ️ {symbol} 持仓已不存在，跳过")
                    closed_positions.append(pos)
                    continue

                unrealized_pnl = float(live.get('unRealizedProfit', 0))
                entry_price = float(live.get('entryPrice', 0))
                mark_price = float(live.get('markPrice', 0))
                amount = pos.get('amount', self.trade_amount)

                # 计算收益率 (基于保证金, 即含杠杆的收益率)
                if amount > 0:
                    pnl_pct = (unrealized_pnl / amount) * 100
                else:
                    pnl_pct = 0

                if pnl_pct >= self.take_profit_pct:
                    logging.info(f"🎯 {symbol} 触发止盈! 收益率: {pnl_pct:+.2f}% >= +{self.take_profit_pct}% "
                                 f"(入场: {entry_price}, 当前: {mark_price}, 盈亏: {unrealized_pnl:+.4f} USDT)")
                    to_close.append(pos)
                elif pnl_pct <= -self.stop_loss_pct:
                    logging.info(f"🛑 {symbol} 触发止损! 收益率: {pnl_pct:+.2f}% <= -{self.stop_loss_pct}% "
                                 f"(入场: {entry_price}, 当前: {mark_price}, 盈亏: {unrealized_pnl:+.4f} USDT)")
                    to_close.append(pos)
                else:
                    logging.debug(f"📈 {symbol} 持仓中 收益率: {pnl_pct:+.2f}% "
                                  f"(入场: {entry_price}, 当前: {mark_price})")
                    still_pending.append(pos)

            # 并行平仓触发的持仓
            if to_close:
                failed = []

                def close_one(p):
                    try:
                        if p.get('quantity') and p['quantity'] > 0:
                            result = self.api.fast_close_position(
                                p['symbol'], p['quantity'],
                                p['direction'], self.position_mode
                            )
                            if result and result.get('avgPrice'):
                                p['close_price'] = float(result['avgPrice'])
                        else:
                            self.api.close_position(p['symbol'])
                        logging.info(f"✅ {p['symbol']} 平仓成功")
                    except Exception as e:
                        logging.error(f"❌ {p['symbol']} 平仓失败: {e}")
                        failed.append(p)

                threads = []
                for p in to_close:
                    t = threading.Thread(target=close_one, args=(p,))
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join(timeout=10)

                # 失败的放回 pending 等下一轮再检查
                for p in to_close:
                    if p not in failed:
                        closed_positions.append(p)
                still_pending.extend(failed)

            pending = still_pending

            if pending:
                time.sleep(self.tp_sl_check_interval)

        # 如果机器人停止但还有未平仓位，强制平仓
        if pending and not self.running:
            logging.warning(f"⚠️ 机器人停止，强制平仓剩余 {len(pending)} 个持仓")
            self.round_positions = pending
            self.close_positions_parallel()
            closed_positions.extend(pending)
        else:
            logging.info(f"📊 止盈止损监控结束, 共平仓 {len(closed_positions)} 个")

        # P&L追踪
        self._log_round_pnl(closed_positions)

    def close_positions_parallel(self):
        """并行平仓本轮所有持仓，带指数退避重试"""
        if not self.round_positions:
            return

        positions_to_close = list(self.round_positions)
        self.round_positions = []
        failed = []

        def close_one(pos):
            try:
                if pos.get('quantity') and pos['quantity'] > 0:
                    result = self.api.fast_close_position(
                        pos['symbol'], pos['quantity'],
                        pos['direction'], self.position_mode
                    )
                    # 记录平仓均价
                    if result and result.get('avgPrice'):
                        pos['close_price'] = float(result['avgPrice'])
                else:
                    self.api.close_position(pos['symbol'])
                logging.info(f"✅ {pos['symbol']} 平仓成功")
            except Exception as e:
                logging.error(f"❌ {pos['symbol']} 平仓失败: {e}")
                failed.append(pos)

        threads = []
        for pos in positions_to_close:
            t = threading.Thread(target=close_one, args=(pos,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        # 指数退避重试失败的平仓 (最多3次: 0.5s, 1s, 2s)
        retry_list = list(failed)
        failed.clear()
        for attempt in range(3):
            if not retry_list:
                break
            backoff = 0.5 * (2 ** attempt)
            time.sleep(backoff)
            still_failed = []
            for pos in retry_list:
                try:
                    logging.info(f"🔄 重试平仓 {pos['symbol']} (第{attempt+1}次, 退避{backoff:.1f}s)...")
                    self.api.close_position(pos['symbol'])
                    logging.info(f"✅ {pos['symbol']} 重试平仓成功")
                except Exception as e:
                    logging.error(f"❌ {pos['symbol']} 第{attempt+1}次重试失败: {e}")
                    still_failed.append(pos)
            retry_list = still_failed

        if retry_list:
            for pos in retry_list:
                logging.error(f"❌❌ {pos['symbol']} 3次重试均失败, 请手动平仓!")
            failed.extend(retry_list)

        success_count = len(positions_to_close) - len(failed)
        logging.info(f"🔻 平仓完成: {success_count}/{len(positions_to_close)} 成功")

        # P&L追踪
        self._log_round_pnl(positions_to_close)

    def _log_round_pnl(self, positions: List[Dict]):
        """
        记录本轮P&L估算

        预估P&L = Σ (|funding_rate| × amount - 2 × taker_fee × amount)
        注: 实际P&L需从交易所查询, 这里是估算用于实时监控
        """
        self.round_counter += 1
        total_funding_est = 0
        total_fees_est = 0
        total_amount = 0

        for pos in positions:
            amount = pos.get('amount', self.trade_amount)
            rate = abs(pos.get('rate', 0))
            funding_est = rate * amount * self.leverage
            fees_est = 2 * self.TAKER_FEE_RATE * amount * self.leverage
            total_funding_est += funding_est
            total_fees_est += fees_est
            total_amount += amount

        net_est = total_funding_est - total_fees_est

        record = {
            'round': self.round_counter,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'positions_count': len(positions),
            'total_amount': total_amount,
            'funding_est': round(total_funding_est, 4),
            'fees_est': round(total_fees_est, 4),
            'net_est': round(net_est, 4),
            'symbols': [p['symbol'] for p in positions],
        }
        self.session_pnl.append(record)

        # 累计统计
        cumulative_net = sum(r['net_est'] for r in self.session_pnl)
        total_rounds = len(self.session_pnl)

        logging.info(f"💰 本轮P&L估算: 资金费≈{total_funding_est:.4f}, 手续费≈{total_fees_est:.4f}, 净利≈{net_est:.4f} USDT")
        logging.info(f"📊 累计{total_rounds}轮: 估算净利≈{cumulative_net:.4f} USDT")

    def precise_sleep_until(self, target_ms: int):
        """精确等待到目标服务器时间，最后1秒用忙等待"""
        while True:
            now = self.get_server_time_ms()
            remaining = (target_ms - now) / 1000.0

            if remaining <= 0:
                return

            if remaining > 1.5:
                # 大段等待用sleep，每30秒检查一次停止信号
                sleep_time = min(remaining - 1.0, 30.0)
                time.sleep(sleep_time)
                if not self.running:
                    return
            elif remaining > 0.05:
                # 最后1.5秒用短sleep
                time.sleep(0.01)
            else:
                # 最后50ms忙等待
                pass

    def start_monitoring(self):
        """
        主循环 - 基于结算时间调度

        流程:
        1. 获取最近的结算时间
        2. 结算前3分钟: 预扫描候选
        3. 结算前2秒: 并行开仓
        4. 结算后0.5秒: 并行平仓
        5. 循环
        """
        self.running = True

        # 初始化: 同步时间 + 缓存持仓模式
        self.sync_server_time()
        self.position_mode = self.api.get_position_mode()
        logging.info(f"📋 持仓模式: {self.position_mode}")

        logging.info("=" * 60)
        logging.info("🧠 资金费率套利机器人 v3.0 (量化增强版) 启动")
        logging.info(f"📋 策略: 结算前{self.open_before_seconds}秒开仓 → 止盈{self.take_profit_pct}%/止损{self.stop_loss_pct}%平仓")
        logging.info(f"💰 每笔: {self.trade_amount} USDT, 杠杆: {self.leverage}x")
        logging.info(f"📊 最小费率: {self.min_funding_rate*100:.3f}%, 最小净利润: {self.min_net_profit_rate*100:.4f}%")
        logging.info(f"📊 最大持仓: {self.max_positions}个, 动态仓位: {'开启' if self.dynamic_sizing else '关闭'}")
        logging.info("=" * 60)

        while self.running:
            try:
                # 1. 获取所有即将到来的结算时间
                settlements = self.get_upcoming_settlements()
                if not settlements:
                    logging.warning("无法获取结算时间，60秒后重试")
                    time.sleep(60)
                    continue

                # 2. 找到最近的结算时间
                now = self.get_server_time_ms()
                future_times = sorted([t for t in settlements.keys() if t > now])

                if not future_times:
                    logging.info("当前无即将到来的结算，60秒后重试")
                    time.sleep(60)
                    continue

                next_settlement = future_times[0]
                settlement_dt = datetime.fromtimestamp(next_settlement / 1000)
                time_until = (next_settlement - now) / 1000
                symbol_count = len(settlements[next_settlement])

                logging.info(f"⏰ 下次结算: {settlement_dt.strftime('%Y-%m-%d %H:%M:%S')}, "
                             f"还有 {time_until:.0f}秒, 涉及 {symbol_count} 个交易对")

                # 3. 计算各时间节点
                pre_scan_time = next_settlement - int(self.pre_scan_minutes * 60 * 1000)
                open_time = next_settlement - int(self.open_before_seconds * 1000)
                close_time = next_settlement + int(self.close_after_seconds * 1000)

                # 4. 等待到预扫描时间
                wait_to_scan = (pre_scan_time - self.get_server_time_ms()) / 1000
                if wait_to_scan > 0:
                    logging.info(f"💤 等待 {wait_to_scan:.0f}秒 到预扫描时间 "
                                 f"({datetime.fromtimestamp(pre_scan_time/1000).strftime('%H:%M:%S')})...")
                    self.precise_sleep_until(pre_scan_time)

                if not self.running:
                    break

                # 5. 重新同步时间 + 预扫描候选
                self.sync_server_time()
                candidates = self.scan_funding_candidates(next_settlement)

                if not candidates:
                    logging.info("本轮无符合条件的套利候选")
                    # 等到结算后再继续
                    wait = (close_time - self.get_server_time_ms()) / 1000 + 5
                    if wait > 0:
                        time.sleep(min(wait, 300))
                    continue

                logging.info(f"🎯 找到 {len(candidates)} 个套利候选 (经量化过滤):")

                # 6. 检查余额
                balance = self.get_usdt_balance()
                needed = self.trade_amount * len(candidates)
                if balance < self.trade_amount:
                    logging.warning(f"⚠️ USDT余额不足: {balance:.2f}, 需要至少 {self.trade_amount:.2f}")
                    time.sleep(60)
                    continue
                elif balance < needed:
                    # 余额不够全部开仓，裁剪候选
                    max_count = int(balance / self.trade_amount)
                    candidates = candidates[:max_count]
                    logging.info(f"💰 余额 {balance:.2f} 不够全部开仓，裁剪为 {len(candidates)} 个")

                # 7. 精确等待到开仓时间(结算前2秒)
                logging.info(f"⏳ 等待开仓时间 "
                             f"({datetime.fromtimestamp(open_time/1000).strftime('%H:%M:%S.%f')[:-3]})...")
                self.precise_sleep_until(open_time)

                if not self.running:
                    break

                # 8. 并行开仓!
                open_start = time.time()
                logging.info("🚀🚀🚀 开仓!")
                self.open_positions_parallel(candidates)
                open_elapsed = (time.time() - open_start) * 1000
                logging.info(f"⚡ 开仓耗时: {open_elapsed:.0f}ms")

                # 9. 进入止盈止损监控 (替代原来的立即平仓)
                logging.info(f"📊 开仓完毕，进入止盈止损监控 (±{self.take_profit_pct}%)...")
                monitor_start = time.time()
                self.monitor_tp_sl()
                monitor_elapsed = time.time() - monitor_start
                logging.info(f"⏱️ 止盈止损监控持续: {monitor_elapsed:.1f}秒")

                logging.info("=" * 40)
                logging.info("✅ 本轮交易完成!")
                logging.info("=" * 40)

                # 等待一小段时间再进入下一轮
                time.sleep(10)

            except KeyboardInterrupt:
                logging.info("接收到停止信号")
                break
            except Exception as e:
                logging.error(f"主循环出错: {e}")
                import traceback
                logging.error(traceback.format_exc())
                time.sleep(60)

        # 确保退出前平仓残留持仓
        if self.round_positions:
            logging.warning("⚠️ 退出前清理残留持仓...")
            self.close_positions_parallel()

        logging.info("资金费率套利机器人已停止")

    def stop_monitoring(self):
        """停止机器人"""
        self.running = False
        logging.info("正在停止资金费率套利机器人...")

def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    计算指数移动平均线 (EMA)
    
    Args:
        prices: 价格数据列表
        period: EMA周期
        
    Returns:
        EMA值列表，长度为 len(prices) - period + 1
    """
    if len(prices) < period:
        return []
    
    ema_values = []
    multiplier = 2 / (period + 1)
    
    # 第一个EMA值使用简单移动平均
    sma = sum(prices[:period]) / period
    ema_values.append(sma)
    
    # 计算后续EMA值
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
        ema_values.append(ema)
    
    return ema_values

def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict:
    """
    计算MACD指标
    
    MACD指标包含：
    - MACD线：快线EMA(12) - 慢线EMA(26)
    - 信号线(慢线)：MACD线的EMA(9) 
    - 柱状图：MACD线 - 信号线
    
    Args:
        prices: 收盘价数据列表
        fast_period: 快线EMA周期，默认12
        slow_period: 慢线EMA周期，默认26  
        signal_period: 信号线EMA周期，默认9
        
    Returns:
        包含MACD线、信号线、柱状图的字典
    """
    # 检查数据充足性：需要 slow_period + signal_period - 1 个数据点
    required_length = slow_period + signal_period - 1
    if len(prices) < required_length:
        logging.debug(f"MACD计算数据不足：需要{required_length}个数据点，实际{len(prices)}个")
        return {'macd_line': None, 'signal_line': None, 'histogram': None}
    
    try:
        # 计算快线和慢线EMA
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        if not ema_fast or not ema_slow:
            logging.warning("EMA计算失败")
            return {'macd_line': None, 'signal_line': None, 'histogram': None}
        
        # 对齐数据长度：以慢线EMA为准（因为它开始得最晚）
        alignment_length = len(ema_slow)
        ema_fast_aligned = ema_fast[-alignment_length:]
        ema_slow_aligned = ema_slow
        
        # 计算MACD线 (快线EMA - 慢线EMA)
        macd_line = [fast - slow for fast, slow in zip(ema_fast_aligned, ema_slow_aligned)]
        
        # 计算信号线 (MACD线的EMA)
        signal_line = calculate_ema(macd_line, signal_period)
        
        if not signal_line:
            logging.warning("MACD信号线计算失败")
            return {'macd_line': None, 'signal_line': None, 'histogram': None}
        
        # 对齐MACD线和信号线
        macd_aligned = macd_line[-len(signal_line):]
        
        # 计算柱状图 (MACD线 - 信号线)
        histogram = [macd - signal for macd, signal in zip(macd_aligned, signal_line)]
        
        # 返回最新值
        result = {
            'macd_line': macd_aligned[-1] if macd_aligned else None,
            'signal_line': signal_line[-1] if signal_line else None,
            'histogram': histogram[-1] if histogram else None
        }
        
        logging.debug(f"MACD计算成功: MACD={result['macd_line']:.6f}, 信号线={result['signal_line']:.6f}")
        return result
        
    except Exception as e:
        logging.error(f"计算MACD时出错: {e}")
        return {'macd_line': None, 'signal_line': None, 'histogram': None}

def get_macd_signal_line(api, symbol: str) -> Optional[float]:
    """
    获取指定交易对的MACD信号线值（慢线）
    
    信号线大于0表示趋势偏多，适合做多
    
    Args:
        api: Binance API实例
        symbol: 交易对符号
        
    Returns:
        MACD信号线值，None表示计算失败
    """
    try:
        # 获取日线K线数据，需要足够的数据点计算MACD
        # 最少需要：26(慢线EMA) + 9(信号线EMA) - 1 = 34个数据点
        # 为了确保计算稳定，获取更多数据
        klines = api.get_klines(symbol, interval='1d', limit=100)
        
        if not klines:
            logging.warning(f"{symbol} 无法获取K线数据")
            return None
            
        if len(klines) < 35:
            logging.warning(f"{symbol} K线数据不足: {len(klines)} < 35")
            return None
        
        # 验证K线数据完整性
        for i, kline in enumerate(klines):
            if len(kline) < 5:
                logging.error(f"{symbol} K线数据格式错误，索引{i}")
                return None
        
        # 提取收盘价
        close_prices = []
        for kline in klines:
            try:
                close_price = float(kline[4])
                if close_price <= 0:
                    logging.error(f"{symbol} 发现无效的收盘价: {close_price}")
                    return None
                close_prices.append(close_price)
            except (ValueError, IndexError) as e:
                logging.error(f"{symbol} 解析收盘价失败: {e}")
                return None
        
        # 计算MACD
        macd_data = calculate_macd(close_prices)
        signal_line = macd_data.get('signal_line')
        
        if signal_line is not None:
            logging.debug(f"{symbol} MACD信号线: {signal_line:.6f}")
        else:
            logging.warning(f"{symbol} MACD信号线计算失败")
            
        return signal_line
        
    except Exception as e:
        logging.error(f"获取{symbol} MACD数据失败: {e}")
        return None

class BinanceAccountMonitor:
    """Binance账户监控器"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api = BinanceFuturesAPI(api_key, api_secret, testnet)
    
    def print_account_summary(self):
        """打印账户概要信息"""
        try:
            print("=" * 60)
            print("🏦 BINANCE 合约账户信息")
            print("=" * 60)
            
            # 获取账户信息
            account_info = self.api.get_account_info()
            
            print(f"📊 账户状态: {'正常' if account_info.get('canTrade') else '受限'}")
            print(f"💰 总权益: {float(account_info.get('totalWalletBalance', 0)):.4f} USDT")
            print(f"💎 可用余额: {float(account_info.get('availableBalance', 0)):.4f} USDT")
            print(f"🔒 保证金余额: {float(account_info.get('totalMarginBalance', 0)):.4f} USDT")
            print(f"📈 未实现盈亏: {float(account_info.get('totalUnrealizedProfit', 0)):.4f} USDT")
            print(f"⚡ 维持保证金率: {float(account_info.get('totalMaintMargin', 0)):.4f} USDT")
            
        except Exception as e:
            print(f"❌ 获取账户信息失败: {e}")
    
    def print_balance_details(self):
        """打印余额详情"""
        try:
            print("\n" + "=" * 60)
            print("💰 余额详情")
            print("=" * 60)
            
            balances = self.api.get_balance()
            
            for balance in balances:
                asset = balance.get('asset', 'N/A')
                wallet_balance = float(balance.get('walletBalance', 0))
                available_balance = float(balance.get('availableBalance', 0))
                
                if wallet_balance > 0:
                    print(f"🪙 {asset}:")
                    print(f"   钱包余额: {wallet_balance:.6f}")
                    print(f"   可用余额: {available_balance:.6f}")
                    print()
                    
        except Exception as e:
            print(f"❌ 获取余额信息失败: {e}")
    
    def print_positions(self):
        """打印持仓信息"""
        try:
            print("\n" + "=" * 60)
            print("📍 持仓信息")
            print("=" * 60)
            
            positions = self.api.get_positions()
            active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]
            
            if not active_positions:
                print("📭 当前无持仓")
                return
            
            for position in active_positions:
                symbol = position.get('symbol', 'N/A')
                side = "多头 🟢" if float(position.get('positionAmt', 0)) > 0 else "空头 🔴"
                size = abs(float(position.get('positionAmt', 0)))
                entry_price = float(position.get('entryPrice', 0))
                mark_price = float(position.get('markPrice', 0))
                unrealized_pnl = float(position.get('unRealizedProfit', 0))
                percentage = float(position.get('percentage', 0))
                
                print(f"🎯 {symbol} ({side})")
                print(f"   持仓数量: {size:.6f}")
                print(f"   开仓价格: {entry_price:.6f}")
                print(f"   标记价格: {mark_price:.6f}")
                print(f"   未实现盈亏: {unrealized_pnl:.4f} USDT ({percentage:.2f}%)")
                print()
                
        except Exception as e:
            print(f"❌ 获取持仓信息失败: {e}")
    
    def print_open_orders(self):
        """打印当前挂单"""
        try:
            print("\n" + "=" * 60)
            print("📋 当前挂单")
            print("=" * 60)
            
            orders = self.api.get_open_orders()
            
            if not orders:
                print("📭 当前无挂单")
                return
            
            for order in orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'N/A')
                quantity = float(order.get('origQty', 0))
                price = float(order.get('price', 0))
                stop_price = float(order.get('stopPrice', 0))
                time_created = datetime.fromtimestamp(order.get('time', 0) / 1000)
                
                side_emoji = "🟢" if side == "BUY" else "🔴"
                
                print(f"📄 {symbol} {side_emoji} {side} - {order_type}")
                print(f"   数量: {quantity:.6f}")
                if price > 0:
                    print(f"   价格: {price:.6f}")
                if stop_price > 0:
                    print(f"   止损价格: {stop_price:.6f}")
                print(f"   创建时间: {time_created.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
        except Exception as e:
            print(f"❌ 获取挂单信息失败: {e}")
    
    def print_recent_trades(self, limit: int = 10):
        """打印最近交易"""
        try:
            print("\n" + "=" * 60)
            print(f"📈 最近{limit}笔交易")
            print("=" * 60)
            
            trades = self.api.get_trade_history(limit=limit)
            
            if not trades:
                print("📭 暂无交易记录")
                return
            
            # 按时间倒序排列
            trades.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            for trade in trades[:limit]:
                symbol = trade.get('symbol', 'N/A')
                side = trade.get('side', 'N/A')
                quantity = float(trade.get('qty', 0))
                price = float(trade.get('price', 0))
                commission = float(trade.get('commission', 0))
                realized_pnl = float(trade.get('realizedPnl', 0))
                time_executed = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                
                side_emoji = "🟢" if side == "BUY" else "🔴"
                pnl_emoji = "💰" if realized_pnl > 0 else "💸" if realized_pnl < 0 else "➖"
                
                print(f"💱 {symbol} {side_emoji} {side}")
                print(f"   数量: {quantity:.6f} @ {price:.6f}")
                print(f"   手续费: {commission:.6f}")
                print(f"   已实现盈亏: {pnl_emoji} {realized_pnl:.4f} USDT")
                print(f"   时间: {time_executed.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
        except Exception as e:
            print(f"❌ 获取交易历史失败: {e}")
    
    def print_negative_funding_rates(self, threshold: float = -0.001):
        """打印负资金费率的交易对"""
        try:
            print("\n" + "=" * 60)
            print(f"💸 负资金费率监控 (< {threshold})")
            print("=" * 60)
            
            # 获取所有交易对的资金费率数据
            funding_rates = self.api.get_funding_rates()
            
            if not funding_rates:
                print("❌ 无法获取资金费率数据")
                return
            
            # 筛选出资金费率小于阈值的交易对
            negative_rates = []
            total_symbols = 0
            
            for rate_info in funding_rates:
                if not isinstance(rate_info, dict):
                    continue
                    
                symbol = rate_info.get('symbol', '')
                if not symbol:
                    continue
                    
                total_symbols += 1
                
                # 检查lastFundingRate字段
                if 'lastFundingRate' in rate_info:
                    try:
                        funding_rate = float(rate_info.get('lastFundingRate', 0))
                        
                        # 只处理USDT永续合约
                        if symbol.endswith('USDT') and funding_rate < threshold:
                            negative_rates.append({
                                'symbol': symbol,
                                'funding_rate': funding_rate,
                                'funding_time': rate_info.get('nextFundingTime', 0),
                                'mark_price': float(rate_info.get('markPrice', 0))
                            })
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  {symbol} 资金费率数据格式错误: {e}")
                        continue
            
            print(f"📊 总共检查了 {total_symbols} 个交易对")
            
            if not negative_rates:
                print(f"📭 当前无资金费率小于 {threshold} 的USDT永续合约")
                return
            
            # 按资金费率从小到大排序
            negative_rates.sort(key=lambda x: x['funding_rate'])
            
            print(f"🔍 发现 {len(negative_rates)} 个符合条件的交易对:")
            print()
            
            for rate_data in negative_rates:
                symbol = rate_data['symbol']
                funding_rate = rate_data['funding_rate']
                mark_price = rate_data['mark_price']
                funding_time = rate_data['funding_time']
                
                # 计算下次资金费率时间
                next_funding = None
                if funding_time and funding_time > 0:
                    try:
                        next_funding = datetime.fromtimestamp(funding_time / 1000)
                    except (ValueError, OSError):
                        pass
                
                # 计算资金费率百分比
                rate_percentage = funding_rate * 100
                
                # 去掉USDT后缀显示
                display_symbol = symbol.replace('USDT', '')
                
                print(f"💰 {display_symbol}")
                print(f"   📊 资金费率: {rate_percentage:.4f}% ({funding_rate:.6f})")
                print(f"   💲 标记价格: {mark_price:.6f}")
                if next_funding:
                    print(f"   ⏰ 下次结算: {next_funding.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 获取多空比数据
                try:
                    account_ratio_data = self.api.get_top_long_short_account_ratio(symbol, period='5m', limit=1)
                    if account_ratio_data and len(account_ratio_data) > 0:
                        long_short_ratio = float(account_ratio_data[-1].get('longShortRatio', 0))
                        
                        # 计算多头和空头百分比
                        total = long_short_ratio + 1
                        long_percent = (long_short_ratio / total) * 100
                        short_percent = (1 / total) * 100
                        
                        # 判断风险
                        risk_indicator = ""
                        if long_short_ratio < 0.6:
                            risk_indicator = " ⚠️ 轧空风险"
                        elif long_short_ratio > 1.67:
                            risk_indicator = " ⚠️ 砸盘风险"
                        
                        print(f"   👥 多空比: {long_percent:.1f}%多 / {short_percent:.1f}%空 (比值:{long_short_ratio:.3f}){risk_indicator}")
                    else:
                        print(f"   👥 多空比: 数据获取失败")
                except Exception as e:
                    print(f"   👥 多空比: 获取失败 ({e})")
                
                # 获取MACD慢线值
                try:
                    macd_signal = get_macd_signal_line(self.api, symbol)
                    if macd_signal is not None:
                        signal_indicator = "📈 看涨" if macd_signal > 0 else "📉 看跌"
                        print(f"   📊 MACD慢线: {macd_signal:.6f} {signal_indicator}")
                    else:
                        print(f"   📊 MACD慢线: 数据获取失败")
                except Exception as e:
                    print(f"   📊 MACD慢线: 获取失败 ({e})")
                
                print()
                
        except Exception as e:
            print(f"❌ 获取资金费率失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
    
    def print_long_short_ratios(self, symbols: List[str] = None):
        """打印多空比数据"""
        try:
            print("\n" + "=" * 60)
            print("📊 多空比数据")
            print("=" * 60)
            
            # 如果没有指定symbols，获取当前持仓的交易对
            if not symbols:
                positions = self.api.get_positions()
                symbols = []
                for pos in positions:
                    if float(pos.get('positionAmt', 0)) != 0:
                        symbols.append(pos.get('symbol', ''))
                
                # 如果没有持仓，使用一些热门交易对
                if not symbols:
                    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
            
            if not symbols:
                print("📭 没有可查询的交易对")
                return
            
            print(f"🔍 查询 {len(symbols)} 个交易对的多空比数据:")
            print()
            
            for symbol in symbols[:10]:  # 限制最多显示10个
                try:
                    # 获取账户多空人数比
                    account_ratio_data = self.api.get_top_long_short_account_ratio(symbol, period='5m', limit=5)
                    
                    # 获取大户持仓多空比
                    position_ratio_data = self.api.get_top_long_short_position_ratio(symbol, period='5m', limit=5)
                    
                    display_symbol = symbol.replace('USDT', '')
                    
                    print(f"💱 {display_symbol}")
                    
                    # 显示账户多空人数比
                    if account_ratio_data and len(account_ratio_data) > 0:
                        latest_account = account_ratio_data[-1]
                        long_short_ratio = float(latest_account.get('longShortRatio', 0))
                        timestamp = int(latest_account.get('timestamp', 0))
                        
                        # 计算多头和空头百分比
                        total = long_short_ratio + 1
                        long_percent = (long_short_ratio / total) * 100
                        short_percent = (1 / total) * 100
                        
                        # 判断风险
                        risk_indicator = ""
                        if long_short_ratio < 0.6:
                            risk_indicator = " ⚠️ 轧空风险"
                        elif long_short_ratio > 1.67:
                            risk_indicator = " ⚠️ 砸盘风险"
                        
                        update_time = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S')
                        print(f"   👥 账户人数比: {long_percent:.1f}%多 / {short_percent:.1f}%空{risk_indicator}")
                        print(f"   📈 多空比值: {long_short_ratio:.3f} ({update_time})")
                    
                    # 显示大户持仓多空比
                    if position_ratio_data and len(position_ratio_data) > 0:
                        latest_position = position_ratio_data[-1]
                        long_short_ratio = float(latest_position.get('longShortRatio', 0))
                        
                        # 计算多头和空头百分比
                        total = long_short_ratio + 1
                        long_percent = (long_short_ratio / total) * 100
                        short_percent = (1 / total) * 100
                        
                        print(f"   🐋 大户持仓比: {long_percent:.1f}%多 / {short_percent:.1f}%空")
                        print(f"   📊 持仓比值: {long_short_ratio:.3f}")
                    
                    print()
                    
                except Exception as e:
                    print(f"   ❌ 获取 {symbol} 多空比数据失败: {e}")
                    print()
                    
        except Exception as e:
            print(f"❌ 获取多空比数据失败: {e}")
    
    def get_extreme_long_short_ratios(self, threshold_low: float = 0.6, threshold_high: float = 1.67):
        """获取极端多空比的交易对"""
        try:
            print("\n" + "=" * 60)
            print(f"⚠️  极端多空比监控 (< {threshold_low} 或 > {threshold_high})")
            print("=" * 60)
            
            # 获取前50名热门交易对
            ticker_data = self.api.get_24hr_ticker()
            if not ticker_data:
                print("❌ 无法获取交易对数据")
                return
            
            # 按交易量排序，取前20名USDT交易对
            usdt_tickers = [t for t in ticker_data if t.get('symbol', '').endswith('USDT')]
            sorted_tickers = sorted(usdt_tickers, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
            top_symbols = [t['symbol'] for t in sorted_tickers[:20]]
            
            extreme_ratios = []
            
            for symbol in top_symbols:
                try:
                    # 获取账户多空人数比
                    account_ratio_data = self.api.get_top_long_short_account_ratio(symbol, period='5m', limit=1)
                    
                    if account_ratio_data and len(account_ratio_data) > 0:
                        long_short_ratio = float(account_ratio_data[-1].get('longShortRatio', 0))
                        
                        if long_short_ratio < threshold_low or long_short_ratio > threshold_high:
                            # 计算多头和空头百分比
                            total = long_short_ratio + 1
                            long_percent = (long_short_ratio / total) * 100
                            short_percent = (1 / total) * 100
                            
                            risk_type = ""
                            if long_short_ratio < threshold_low:
                                risk_type = "轧空风险"
                            else:
                                risk_type = "砸盘风险"
                            
                            extreme_ratios.append({
                                'symbol': symbol.replace('USDT', ''),
                                'ratio': long_short_ratio,
                                'long_percent': long_percent,
                                'short_percent': short_percent,
                                'risk_type': risk_type
                            })
                            
                except Exception as e:
                    continue
            
            if not extreme_ratios:
                print("📭 当前无极端多空比交易对")
                return
            
            # 按风险程度排序
            extreme_ratios.sort(key=lambda x: abs(x['ratio'] - 1.0), reverse=True)
            
            print(f"🔍 发现 {len(extreme_ratios)} 个极端多空比交易对:")
            print()
            
            for data in extreme_ratios:
                symbol = data['symbol']
                ratio = data['ratio']
                long_percent = data['long_percent']
                short_percent = data['short_percent']
                risk_type = data['risk_type']
                
                risk_emoji = "🔴" if "砸盘" in risk_type else "🟡"
                
                print(f"{risk_emoji} {symbol}")
                print(f"   👥 账户分布: {long_percent:.1f}%多 / {short_percent:.1f}%空")
                print(f"   ⚠️  风险类型: {risk_type}")
                print(f"   📊 多空比值: {ratio:.3f}")
                print()
                
        except Exception as e:
            print(f"❌ 获取极端多空比数据失败: {e}")
    
    def monitor_account(self, refresh_interval: int = 120):
        """持续监控账户"""
        print("🔄 开始监控账户，按 Ctrl+C 停止...")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')  # 清屏
                
                print(f"🕐 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.print_account_summary()
                self.print_positions()
                self.print_open_orders()
                self.print_negative_funding_rates()
                self.get_extreme_long_short_ratios()
                
                print(f"\n⏰ {refresh_interval}秒后刷新...")
                time.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\n👋 监控已停止")

def main():
    """主函数"""
    print("🚀 Binance合约账户查询和自动化交易工具")
    print("请确保已在.env文件中设置API密钥")
    
    try:
        # 初始化监控器
        monitor = BinanceAccountMonitor()
        
        while True:
            print("\n" + "=" * 60)
            print("📋 请选择操作:")
            print("1. 📊 查看账户概要")
            print("2. 💰 查看余额详情")
            print("3. 📍 查看持仓信息")
            print("4. 📋 查看当前挂单")
            print("5. 📈 查看最近交易")
            print("6. 💸 查看负资金费率")
            print("7. 📊 查看多空比数据")
            print("8. ⚠️  查看极端多空比")
            print("9. 🔄 开始实时监控")
            print("10. 🔧 调试资金费率数据")
            print("11. 🤖 启动自动化交易机器人")
            print("12. 📴 平仓操作")
            print("0. 🚪 退出程序")
            print("=" * 60)
            
            choice = input("请输入选项 (0-12): ").strip()
            
            if choice == '1':
                monitor.print_account_summary()
            elif choice == '2':
                monitor.print_balance_details()
            elif choice == '3':
                monitor.print_positions()
            elif choice == '4':
                monitor.print_open_orders()
            elif choice == '5':
                limit = input("请输入要查看的交易数量 (默认10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                monitor.print_recent_trades(limit)
            elif choice == '6':
                threshold = input("请输入资金费率阈值 (默认-0.001): ").strip()
                threshold = float(threshold) if threshold.replace('-', '').replace('.', '').isdigit() else -0.001
                monitor.print_negative_funding_rates(threshold)
            elif choice == '7':
                symbols_input = input("请输入交易对(多个用逗号分隔，回车查看持仓相关): ").strip()
                symbols = [s.strip().upper() for s in symbols_input.split(',')] if symbols_input else None
                # 确保交易对以USDT结尾
                if symbols:
                    symbols = [s if s.endswith('USDT') else s + 'USDT' for s in symbols]
                monitor.print_long_short_ratios(symbols)
            elif choice == '8':
                threshold_low = input("请输入轧空风险阈值 (默认0.6): ").strip()
                threshold_high = input("请输入砸盘风险阈值 (默认1.67): ").strip()
                threshold_low = float(threshold_low) if threshold_low.replace('.', '').isdigit() else 0.6
                threshold_high = float(threshold_high) if threshold_high.replace('.', '').isdigit() else 1.67
                monitor.get_extreme_long_short_ratios(threshold_low, threshold_high)
            elif choice == '9':
                interval = input("请输入刷新间隔(秒，默认120): ").strip()
                interval = int(interval) if interval.isdigit() else 120
                monitor.monitor_account(interval)
            elif choice == '10':
                limit = input("请输入要查看的调试数据数量 (默认5): ").strip()
                limit = int(limit) if limit.isdigit() else 5
                monitor.api.debug_funding_rates(limit)
            elif choice == '11':
                print("\n🤖 资金费率套利机器人")
                print("=" * 40)
                print("📋 交易策略: 快进快出吃资金费")
                print("🕐 结算前2秒: 开仓(负费率做多/正费率做空)")
                print("🕐 结算后0.5秒: 极速平仓")
                print("💰 收益来源: 资金费率结算收入 - 手续费")
                print()
                print("⚠️  警告: 将使用真实资金进行交易!")
                print("确保您已经:")
                print("1. 在.env文件中设置了API密钥")
                print("2. 理解资金费率套利策略")
                print("3. 设置了合适的交易金额和杠杆")

                confirm = input("\n是否确认启动? (输入 'YES' 确认): ").strip()
                if confirm == 'YES':
                    trade_amount = input("请输入每笔交易金额(USDT，默认100): ").strip()
                    trade_amount = float(trade_amount) if trade_amount.replace('.', '').isdigit() else 100

                    leverage = input("请输入杠杆倍数(默认20): ").strip()
                    leverage = int(leverage) if leverage.isdigit() else 20

                    min_rate = input("请输入最小费率阈值(默认0.0005即0.05%): ").strip()
                    min_rate = float(min_rate) if min_rate.replace('.', '').isdigit() else 0.0005

                    max_pos = input("请输入最大同时持仓数(默认5): ").strip()
                    max_pos = int(max_pos) if max_pos.isdigit() else 5

                    print(f"\n🤖 正在启动资金费率套利机器人...")
                    print(f"每笔金额: {trade_amount} USDT")
                    print(f"杠杆倍数: {leverage}x")
                    print(f"最小费率: {min_rate*100:.3f}%")
                    print(f"最大持仓: {max_pos}个")
                    print("按 Ctrl+C 停止机器人\n")

                    try:
                        bot = AutoTradingBot()
                        bot.trade_amount = trade_amount
                        bot.leverage = leverage
                        bot.min_funding_rate = min_rate
                        bot.max_positions = max_pos

                        bot.start_monitoring()

                    except KeyboardInterrupt:
                        print("\n🛑 资金费率套利机器人已停止")
                    except Exception as e:
                        print(f"❌ 机器人出错: {e}")
                        logging.error(f"机器人出错: {e}")
                else:
                    print("❌ 已取消启动")
            elif choice == '12':
                print("\n📴 平仓操作")
                print("=" * 40)
                
                # 先检查是否有持仓
                positions = monitor.api.get_positions()
                active_positions = [p for p in positions if abs(float(p.get('positionAmt', 0))) > 0]
                
                if not active_positions:
                    print("📭 当前没有任何持仓")
                else:
                    print(f"🎯 当前有 {len(active_positions)} 个持仓:")
                    print()
                    
                    for i, position in enumerate(active_positions, 1):
                        symbol = position.get('symbol', 'Unknown')
                        position_amt = float(position.get('positionAmt', 0))
                        entry_price = float(position.get('entryPrice', 0))
                        mark_price = float(position.get('markPrice', 0))
                        pnl = float(position.get('unRealizedProfit', 0))
                        position_side = position.get('positionSide', 'BOTH')
                        
                        direction = "🟢 多头" if position_amt > 0 else "🔴 空头"
                        
                        print(f"{i}. {symbol}")
                        print(f"   方向: {direction} ({position_side})")
                        print(f"   数量: {position_amt}")
                        print(f"   开仓价: {entry_price}")
                        print(f"   标记价: {mark_price}")
                        print(f"   未实现盈亏: {pnl:.4f} USDT")
                        print()
                    
                    # 用户选择要平仓的持仓
                    choice_input = input(f"请选择要平仓的持仓 (1-{len(active_positions)}, 0取消): ").strip()
                    
                    if choice_input.isdigit() and 1 <= int(choice_input) <= len(active_positions):
                        selected_position = active_positions[int(choice_input) - 1]
                        symbol = selected_position.get('symbol')
                        position_amt = float(selected_position.get('positionAmt', 0))
                        pnl = float(selected_position.get('unRealizedProfit', 0))
                        
                        direction = "🟢 多头" if position_amt > 0 else "🔴 空头"
                        
                        print(f"\n⚠️  即将平仓 {symbol} {direction} 持仓")
                        print(f"数量: {abs(position_amt)}")
                        print(f"预估盈亏: {pnl:.4f} USDT")
                        
                        confirm = input("\n是否确认平仓? (y/N): ").strip().lower()
                        if confirm in ['y', 'yes']:
                            try:
                                print(f"\n🚀 开始平仓 {symbol}...")
                                result = monitor.api.close_position(symbol)
                                
                                print("\n✅ 平仓成功!")
                                print(f"订单ID: {result.get('orderId', 'Unknown')}")
                                print(f"订单状态: {result.get('status', 'Unknown')}")
                                print(f"成交数量: {result.get('executedQty', 'Unknown')}")
                                
                            except Exception as e:
                                print(f"❌ 平仓失败: {e}")
                        else:
                            print("❌ 取消平仓操作")
                    elif choice_input == '0':
                        print("❌ 取消平仓操作")
                    else:
                        print("❌ 无效选择")
            elif choice == '0':
                print("👋 再见!")
                break
            else:
                print("❌ 无效选项，请重新选择")
                
            if choice not in ['9', '11']:
                input("\n按Enter键继续...")
                
    except Exception as e:
        print(f"❌ 程序运行错误: {e}")

if __name__ == "__main__":
    main()
