#!/usr/bin/env python3
"""
Binance合约账户查询工具 - 快速设置脚本
"""

import os
import sys
import subprocess

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def install_dependencies():
    """安装依赖包"""
    print("📦 正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装成功")
    except subprocess.CalledProcessError:
        print("❌ 依赖包安装失败")
        sys.exit(1)

def setup_config():
    """设置配置文件"""
    if not os.path.exists(".env"):
        if os.path.exists("config_template.env"):
            print("📝 正在创建配置文件...")
            with open("config_template.env", "r", encoding="utf-8") as src:
                with open(".env", "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            print("✅ 配置文件已创建: .env")
            print("⚠️  请编辑 .env 文件，填入你的Binance API密钥")
        else:
            print("❌ 找不到配置模板文件")
    else:
        print("✅ 配置文件已存在: .env")

def main():
    """主函数"""
    print("🚀 Binance合约账户查询工具 - 快速设置")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 安装依赖
    install_dependencies()
    
    # 设置配置文件
    setup_config()
    
    print("\n" + "=" * 50)
    print("🎉 设置完成！")
    print("\n📋 接下来的步骤:")
    print("1. 编辑 .env 文件，填入你的Binance API密钥")
    print("2. 运行 python main.py 启动程序")
    print("\n🔗 获取API密钥: https://www.binance.com/zh-CN/my/settings/api-management")
    print("⚠️  重要: 只开启'读取'权限，不要开启交易权限！")

if __name__ == "__main__":
    main() 