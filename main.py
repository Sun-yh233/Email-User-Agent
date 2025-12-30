#!/usr/bin/env python3

import sys
from gui import run_gui


def main():
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