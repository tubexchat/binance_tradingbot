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

    def get_24hr_ticker(self) -> List[Dict]:
        """获取24小时价格变动统计"""
        return self._make_request('GET', '/fapi/v1/ticker/24hr', signed=False)

class AutoTradingBot:
    """自动化交易机器人"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        """初始化自动化交易机器人"""
        self.api = BinanceFuturesAPI(api_key, api_secret, testnet)
        self.running = False
        
        # 交易参数（按README.md要求设置）
        self.trade_amount = 100  # 每次交易金额(USDT)
        self.leverage = 20  # 杠杆倍数
        self.funding_rate_min = -0.02  # 资金费率下限(-2%)
        self.funding_rate_max = -0.001  # 资金费率上限(-0.1%)
        self.min_volume_usdt = 60000000  # 最小24小时交易量(6000万USDT)
        self.monitor_interval = 300  # 监控间隔(5分钟)
        self.position_check_interval = 300  # 持仓检查间隔(5分钟)
        self.position_monitor_thread = None  # 持仓监控线程
        
        # 做多候选列表
        self.long_candidates = set()
        
        # 黑名单设置
        self.load_blacklist()
        
        logging.info("自动化交易机器人初始化完成 - 基于负资金费率+MACD+多空比做多策略")
        
        # 显示当前黑名单状态
        if self.blacklist:
            logging.info(f"🚫 当前黑名单: {list(self.blacklist)}")
        else:
            logging.info("📝 当前未设置黑名单")

    def setup_margin_modes(self, symbols: List[str] = None) -> Dict[str, bool]:
        """
        批量设置交易对为全仓模式（仅在没有持仓时执行）
        
        Args:
            symbols: 要设置的交易对列表，如果为None则设置常用交易对
            
        Returns:
            Dict[str, bool]: 每个交易对的设置结果
        """
        if symbols is None:
            # 默认设置一些主要的交易对
            symbols = [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'XRPUSDT',
                'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT', 'LINKUSDT', 'LTCUSDT'
            ]
        
        results = {}
        logging.info(f"开始为 {len(symbols)} 个交易对设置全仓模式...")
        
        for symbol in symbols:
            try:
                # 先检查是否有持仓
                position = self.api.get_position_info(symbol)
                if position and abs(float(position.get('positionAmt', 0))) > 0:
                    results[symbol] = False
                    logging.warning(f"⚠️ {symbol} 有持仓，跳过保证金模式设置")
                    continue
                
                # 尝试设置全仓模式
                result = self.api.change_margin_type(symbol, 'CROSSED')
                results[symbol] = True
                logging.info(f"✅ {symbol} 已设置为全仓模式")
                
            except Exception as e:
                error_msg = str(e)
                if "-4046" in error_msg or "No need to change margin type" in error_msg:
                    results[symbol] = True
                    logging.info(f"✅ {symbol} 已是全仓模式")
                elif "-4168" in error_msg:
                    results[symbol] = True
                    logging.info(f"✅ {symbol} 在多资产模式下自动使用全仓模式")
                else:
                    results[symbol] = False
                    logging.error(f"❌ {symbol} 设置全仓模式失败: {e}")
        
        success_count = sum(results.values())
        total_count = len(symbols)
        logging.info(f"保证金模式设置完成: {success_count}/{total_count} 个交易对成功")
        
        return results

    def load_blacklist(self):
        """从.env文件加载黑名单币种"""
        try:
            blacklist_str = os.getenv('BLACKLIST_SYMBOLS', '')
            if blacklist_str:
                # 支持逗号分隔的币种列表
                blacklist_symbols = [symbol.strip().upper() for symbol in blacklist_str.split(',') if symbol.strip()]
                # 确保都以USDT结尾
                self.blacklist = set()
                for symbol in blacklist_symbols:
                    if not symbol.endswith('USDT'):
                        symbol = symbol + 'USDT'
                    self.blacklist.add(symbol)
                
                if self.blacklist:
                    logging.info(f"📋 加载黑名单币种: {list(self.blacklist)}")
                else:
                    logging.info("📋 未设置黑名单币种")
            else:
                self.blacklist = set()
                logging.info("📋 未设置黑名单币种")
                
        except Exception as e:
            logging.error(f"加载黑名单配置失败: {e}")
            self.blacklist = set()
    
    def debug_blacklist(self):
        """调试黑名单设置"""
        blacklist_env = os.getenv('BLACKLIST_SYMBOLS', '')
        logging.info(f"🔍 环境变量 BLACKLIST_SYMBOLS: '{blacklist_env}'")
        logging.info(f"🔍 解析后的黑名单: {list(self.blacklist)}")
        
        # 测试特定币种是否在黑名单中
        test_symbols = ['LEVERUSDT', 'SKATEUSDT', 'BTCUSDT']
        for symbol in test_symbols:
            in_blacklist = symbol in self.blacklist
            logging.info(f"🔍 {symbol} 是否在黑名单: {in_blacklist}")
        
        return self.blacklist

    def get_long_candidates(self) -> List[str]:
        """
        获取做多候选合约列表
        筛选条件：
        1. 不在黑名单中
        2. 资金费率 < -0.1%
        3. 24小时交易量大于6000万USDT
        4. MACD日级慢线大于0
        5. 多空比小于1
        6. 24小时涨幅大于0
        """
        candidates = []
        
        try:
            # 获取所有合约的资金费率
            logging.info("开始筛选做多候选合约...")
            funding_rates = self.api.get_funding_rates()
            if not funding_rates:
                logging.warning("未能获取资金费率数据")
                return candidates
            
            # 获取24小时交易统计
            ticker_24hr = self.api.get_24hr_ticker()
            if not ticker_24hr:
                logging.warning("未能获取24小时交易统计")
                return candidates
            
            # 创建交易量映射表和涨幅映射表
            volume_map = {}
            price_change_map = {}
            for ticker in ticker_24hr:
                symbol = ticker.get('symbol', '')
                quote_volume = float(ticker.get('quoteVolume', 0))
                price_change_percent = float(ticker.get('priceChangePercent', 0))
                volume_map[symbol] = quote_volume
                price_change_map[symbol] = price_change_percent
            
            # 筛选符合条件的合约
            for data in funding_rates:
                try:
                    symbol = data.get('symbol', '')
                    if not symbol.endswith('USDT'):
                        continue
                    
                    # 筛选条件0：检查黑名单
                    if symbol in self.blacklist:
                        logging.info(f"❌ {symbol} 在黑名单中，跳过做多")
                        continue
                    
                    funding_rate = float(data.get('lastFundingRate', 0))
                    
                    # 筛选条件1：剔除资金费率为0的合约
                    if funding_rate == 0:
                        continue
                    
                    # 筛选条件2：负资金费率（资金费率 < -0.1%）
                    if funding_rate >= -0.001:  # -0.1%
                        continue
                    
                    # 筛选条件3：24小时交易量大于6000万USDT
                    quote_volume = volume_map.get(symbol, 0)
                    if quote_volume < self.min_volume_usdt:
                        continue
                    
                    # 筛选条件4：MACD日级慢线大于0
                    macd_signal = get_macd_signal_line(self.api, symbol)
                    if macd_signal is None or macd_signal <= 0:
                        continue
                    
                    # 筛选条件5：多空比小于1
                    try:
                        long_short_ratio_data = self.api.get_top_long_short_account_ratio(symbol, period='5m', limit=1)
                        if not long_short_ratio_data or len(long_short_ratio_data) == 0:
                            logging.debug(f"{symbol} 未能获取多空比数据，跳过")
                            continue
                        
                        long_short_ratio = float(long_short_ratio_data[-1].get('longShortRatio', 1))
                        if long_short_ratio >= 1:
                            logging.debug(f"{symbol} 多空比 {long_short_ratio:.3f} >= 1，跳过做多")
                            continue
                    except Exception as e:
                        logging.debug(f"{symbol} 获取多空比失败: {e}，跳过")
                        continue
                    
                    # 筛选条件6：24小时涨幅大于0
                    price_change_percent = price_change_map.get(symbol, 0)
                    if price_change_percent <= 0:
                        logging.debug(f"{symbol} 24h涨幅 {price_change_percent:.3f}% <= 0，跳过做多")
                        continue
                    
                    candidates.append(symbol)
                    logging.info(f"✅ 做多候选: {symbol}, 资金费率: {funding_rate:.6f}, 24h成交量: {quote_volume/1e8:.2f}亿USDT, MACD慢线: {macd_signal:.6f}, 多空比: {long_short_ratio:.3f}, 24h涨幅: {price_change_percent:.3f}%")
                    
                except Exception as e:
                    logging.error(f"处理合约 {symbol} 时出错: {e}")
                    continue
            
            logging.info(f"筛选完成，共找到 {len(candidates)} 个做多候选合约")
            return candidates
            
        except Exception as e:
            logging.error(f"获取做多候选合约失败: {e}")
            return candidates

    def get_usdt_balance(self) -> float:
        """获取USDT余额"""
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
        """检查是否已有持仓（增强版，更严格的检查）"""
        try:
            # 直接获取所有持仓，而不是依赖get_position_info
            positions = self.api.get_positions()
            if not positions:
                logging.debug(f"未获取到任何持仓信息")
                return False
            
            for position in positions:
                if position.get('symbol') == symbol:
                    position_amt = float(position.get('positionAmt', 0))
                    if abs(position_amt) > 0:
                        # 记录持仓详情
                        side = "做空" if position_amt < 0 else "做多"
                        logging.info(f"🔍 {symbol} 已有持仓: {side} {abs(position_amt)}")
                        
                        # 额外检查：确保持仓量超过最小交易单位
                        if abs(position_amt) > 0.0001:  # 增加最小持仓量检查
                            return True
                        else:
                            logging.warning(f"⚠️ {symbol} 持仓量过小: {position_amt}, 可能是精度问题")
                            return False
            
            logging.debug(f"🔍 {symbol} 无持仓")
            return False
        except Exception as e:
            logging.error(f"检查 {symbol} 持仓失败: {e}")
            # 出错时保守处理，返回True以避免重复下单
            return True

    def execute_buy_order(self, symbol: str) -> bool:
        """执行买入订单（做多）"""
        try:
            # 黑名单安全检查：再次确认不在黑名单中
            if symbol in self.blacklist:
                logging.warning(f"🚫 {symbol} 在黑名单中，禁止做多操作")
                return False
            
            # 安全检查：再次确认是否已有持仓
            if self.has_position(symbol):
                logging.warning(f"🚫 {symbol} 已有持仓，取消做多操作")
                return False
            
            # 检查余额
            balance = self.get_usdt_balance()
            if balance < self.trade_amount:
                logging.warning(f"USDT余额不足: {balance} < {self.trade_amount}")
                return False
            
            # 设置杠杆倍数
            try:
                self.api.set_leverage(symbol, self.leverage)
                logging.info(f"✅ {symbol} 杠杆设置为 {self.leverage}x")
            except Exception as e:
                logging.warning(f"设置杠杆可能失败: {e}")
            
            # 注意：保证金模式应在机器人启动前手动设置为全仓模式
            # 如果有持仓，币安不允许程序化更改保证金模式
            # 请确保所有交易对都已设置为全仓(CROSSED)模式
            
            # 下市价买单（做多）
            order_result = self.api.place_order(
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quoteOrderQty=self.trade_amount
            )
            
            logging.info(f"📈 成功做多 {symbol}: {order_result}")
            
            # 等待一小段时间让订单生效
            import time
            time.sleep(2)
            
            # 验证持仓是否已经建立
            if self.has_position(symbol):
                logging.info(f"✅ {symbol} 做多订单已确认，持仓已建立")
            else:
                logging.warning(f"⚠️ {symbol} 做多订单已执行，但未检测到持仓（可能需要更多时间同步）")
            
            return True
            
        except Exception as e:
            logging.error(f"执行 {symbol} 做多订单失败: {e}")
            return False

    def check_and_close_positions(self):
        """检查并平仓（新策略：资金费率>-0.1%时自动平仓）"""
        try:
            logging.info("开始检查需要平仓的持仓...")
            
            # 获取所有持仓
            positions = self.api.get_positions()
            if not positions:
                logging.debug("未获取到持仓信息")
                return
            
            # 过滤有效持仓
            active_positions = []
            for position in positions:
                position_amt = float(position.get('positionAmt', 0))
                if abs(position_amt) > 0:
                    active_positions.append(position)
            
            if not active_positions:
                logging.debug("当前没有持仓")
                return
            
            logging.info(f"当前有 {len(active_positions)} 个持仓")
            
            # 检查每个持仓的资金费率
            for position in active_positions:
                try:
                    symbol = position.get('symbol', '')
                    position_amt = float(position.get('positionAmt', 0))
                    unrealized_pnl = float(position.get('unRealizedProfit', 0))
                    
                    logging.info(f"{symbol} 持仓量: {position_amt}, 未实现盈亏: {unrealized_pnl:.4f} USDT")
                    
                    # 📝 只平仓多头仓位，跳过空头仓位
                    if position_amt < 0:
                        logging.info(f"🔴 {symbol} 为空头仓位，跳过平仓操作")
                        continue
                    
                    # 获取当前资金费率
                    try:
                        funding_data = self.api.get_symbol_funding_rate(symbol)
                        if not funding_data:
                            logging.warning(f"无法获取 {symbol} 的资金费率数据")
                            continue
                        
                        funding_rate = float(funding_data.get('lastFundingRate', 0))
                        logging.info(f"{symbol} 当前资金费率: {funding_rate:.6f}")
                        
                        # 平仓条件：资金费率 > -0.1%
                        if funding_rate > -0.001:  # -0.1%
                            logging.warning(f"🚨 {symbol} 资金费率上升至 ({funding_rate:.6f} > -0.1%)，准备平仓")
                            
                            # 检查是否在黑名单中
                            if symbol in self.blacklist:
                                logging.warning(f"🚨 {symbol} 在黑名单中且资金费率转正，强制平仓")
                            
                            try:
                                result = self.api.close_position(symbol)
                                logging.info(f"✅ 成功平仓 {symbol}: {result}")
                                
                                # 记录平仓信息
                                logging.info(f"📊 平仓详情 - 交易对: {symbol}, 持仓量: {position_amt}, 未实现盈亏: {unrealized_pnl:.4f} USDT, 平仓原因: 资金费率上升至 ({funding_rate:.6f} > -0.1%)")
                                
                            except Exception as e:
                                logging.error(f"❌ 平仓 {symbol} 失败: {e}")
                        else:
                            logging.debug(f"{symbol} 资金费率仍低于阈值 ({funding_rate:.6f} <= -0.1%)，保持持仓")
                            
                    except Exception as e:
                        logging.error(f"获取 {symbol} 资金费率失败: {e}")
                        continue
                        
                except Exception as e:
                    logging.error(f"处理持仓 {symbol} 时出错: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"检查平仓条件失败: {e}")

    def scan_and_trade(self):
        """扫描并执行做多交易（基于负资金费率+MACD+多空比策略）"""
        try:
            logging.info("开始基于负资金费率+MACD+多空比策略扫描做多交易机会...")
            
            # 获取做多候选合约
            current_candidates = self.get_long_candidates()
            if not current_candidates:
                logging.info("本轮扫描未发现符合条件的做多候选合约")
                self.long_candidates = set()
                return
            
            # 更新候选列表
            self.long_candidates = set(current_candidates)
            logging.info(f"当前做多候选列表: {list(self.long_candidates)}")
            
            # 检查每个候选合约的持仓情况
            for symbol in current_candidates:
                try:
                    # 如果已有持仓，跳过
                    if self.has_position(symbol):
                        logging.info(f"⚠️ {symbol} 已有持仓，跳过做多操作")
                        continue
                    
                    # 执行做多
                    if self.execute_buy_order(symbol):
                        logging.info(f"✅ 成功做多 {symbol}")
                        # 为了避免过度交易，每次只执行一个交易
                        return
                    else:
                        logging.warning(f"❌ {symbol} 做多失败")
                        
                except Exception as e:
                    logging.error(f"处理做多合约 {symbol} 时出错: {e}")
                    continue
                    
            logging.info("本轮扫描完成，未执行新的做多交易")
                    
        except Exception as e:
            logging.error(f"扫描和交易过程失败: {e}")

    def position_monitor_loop(self):
        """持仓监控循环 - 独立线程运行"""
        logging.info(f"🔍 持仓监控线程启动，检查间隔: {self.position_check_interval}秒")
        
        while self.running:
            try:
                # 每5分钟检查一次持仓情况
                self.check_and_close_positions()
                
                if self.running:  # 检查是否仍在运行
                    time.sleep(self.position_check_interval)
                    
            except Exception as e:
                logging.error(f"持仓监控出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
                
        logging.info("持仓监控线程已停止")

    def start_monitoring(self):
        """开始监控"""
        self.running = True
        logging.info(f"🤖 自动化交易机器人开始运行，监控间隔: {self.monitor_interval}秒")
        
        # 启动独立的持仓监控线程
        self.position_monitor_thread = threading.Thread(target=self.position_monitor_loop, daemon=True)
        self.position_monitor_thread.start()
        logging.info("✅ 持仓监控线程已启动")
        
        while self.running:
            try:
                self.scan_and_trade()
                
                if self.running:  # 检查是否仍在运行
                    logging.info(f"⏰ 等待 {self.monitor_interval} 秒后进行下次扫描...")
                    time.sleep(self.monitor_interval)
                    
            except KeyboardInterrupt:
                logging.info("接收到停止信号")
                break
            except Exception as e:
                logging.error(f"监控过程出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
                
        logging.info("自动化交易机器人已停止")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        logging.info("正在停止自动化交易机器人...")
        
        # 等待持仓监控线程结束
        if self.position_monitor_thread and self.position_monitor_thread.is_alive():
            logging.info("等待持仓监控线程结束...")
            self.position_monitor_thread.join(timeout=5)
            if self.position_monitor_thread.is_alive():
                logging.warning("持仓监控线程未能在5秒内结束")
            else:
                logging.info("持仓监控线程已结束")
        
        logging.info("自动化交易机器人已完全停止")

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
                print("\n🤖 自动化交易机器人")
                print("=" * 40)
                print("📋 交易策略:")
                print("🟢 做多信号: 资金费率<-0.1% + MACD慢线>0 + 多空比<1")
                print()
                print("⚠️  警告: 自动化交易机器人将使用真实资金进行交易!")
                print("确保您已经:")
                print("1. 在.env文件中设置了具有交易权限的API密钥")
                print("2. 理解交易风险和策略逻辑")
                print("3. 设置了合适的交易金额和杠杆")
                
                confirm = input("\n是否确认启动自动化交易机器人? (输入 'YES' 确认): ").strip()
                if confirm == 'YES':
                    # 获取用户自定义参数
                    trade_amount = input("请输入每次交易金额(USDT，默认30): ").strip()
                    trade_amount = float(trade_amount) if trade_amount.replace('.', '').isdigit() else 30
                    
                    leverage = input("请输入杠杆倍数(默认2): ").strip()
                    leverage = int(leverage) if leverage.isdigit() else 2
                    
                    funding_threshold = input("请输入资金费率阈值(默认-0.001): ").strip()
                    funding_threshold = float(funding_threshold) if funding_threshold.replace('-', '').replace('.', '').isdigit() else -0.001
                    
                    monitor_interval = input("请输入监控间隔(秒，默认300): ").strip()
                    monitor_interval = int(monitor_interval) if monitor_interval.isdigit() else 300
                    
                    print("\n🤖 正在启动自动化交易机器人...")
                    print(f"交易金额: {trade_amount} USDT")
                    print(f"杠杆倍数: {leverage}x")
                    print(f"资金费率阈值: {funding_threshold}")
                    print(f"监控间隔: {monitor_interval}秒")
                    print("按 Ctrl+C 停止机器人\n")
                    
                    try:
                        # 初始化自动化交易机器人
                        bot = AutoTradingBot()
                        bot.trade_amount = trade_amount
                        bot.leverage = leverage
                        # 注意：新策略不再需要funding_rate_threshold，直接使用负资金费率
                        bot.monitor_interval = monitor_interval
                        
                        # 开始监控
                        bot.start_monitoring()
                        
                    except KeyboardInterrupt:
                        print("\n🛑 自动化交易机器人已停止")
                    except Exception as e:
                        print(f"❌ 自动化交易机器人出错: {e}")
                        logging.error(f"自动化交易机器人出错: {e}")
                else:
                    print("❌ 已取消启动自动化交易机器人")
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
