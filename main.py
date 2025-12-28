#!/usr/bin/env python3
"""
邮件用户代理主程序
Email User Agent Main Program

作者: Sun-yh233
许可证: MIT License
"""

import sys
from gui import run_gui


def main():
    """主函数"""
    print("=" * 60)
    print("邮件用户代理 (Email User Agent)")
    print("版本: 1.0")
    print("作者: Sun-yh233")
    print("=" * 60)
    print()
    print("正在启动图形界面...")
    print()
    
    try:
        run_gui()
    except KeyboardInterrupt:
        print("\n程序已退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
