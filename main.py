#!/usr/bin/env python3
"""
主程序入口文件
运行此文件启动Qt界面应用程序
"""

import sys
import os

# 获取当前目录路径，兼容打包环境
def get_current_dir():
    """获取当前目录，兼容打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包环境：获取可执行文件所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境：获取脚本文件所在目录
        return os.path.dirname(os.path.abspath(__file__))

current_dir = get_current_dir()
sys.path.insert(0, current_dir)

# 使用新的FileTracker类替代全局变量
from file_tracker import file_tracker

# 向后兼容的包装函数
def add_generated_file(file_path):
    """添加生成的文件到追踪列表（向后兼容）"""
    return file_tracker.add(file_path)

def get_generated_files():
    """获取本次运行生成的文件列表（向后兼容）"""
    return file_tracker.get_all()

def clear_generated_files():
    """清空生成文件追踪列表（向后兼容）"""
    file_tracker.clear()

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QIcon
    from qt_interface import ModernInterface
    from structure_set import get_crystal_structure
    from PyQt5.QtCore import QTimer
    import ctypes
    import platform
    from datetime import datetime
except ImportError as e:
    print("错误: 无法导入必要的模块")
    print(f"详细错误: {e}")
    print("请确保已安装PyQt5: pip install PyQt5")
    sys.exit(1)


# 导入新的脚本生成器模块
from shell_script_generator import generate_shell_script

# 原来的321行函数已被重构到 shell_script_generator.py
# 现在直接使用新模块的实现，消除了70%的代码重复


def generate_batch_on_exit():
    """程序退出时生成批处理文件"""
    try:
        print("\n程序退出，正在生成批处理文件...")

        # 获取generate_script目录
        from config import Config
        generate_script_dir = os.path.join(current_dir, Config.GENERATE_SCRIPT_DIR)
        if not os.path.exists(generate_script_dir):
            print("未找到generate_script目录，跳过批处理文件生成")
            return

        # 使用本次运行生成的文件列表，而不是遍历所有文件
        python_files = get_generated_files()

        if not python_files:
            print("本次运行未生成任何Python脚本文件，跳过批处理文件生成")
            return

        # 过滤确保文件仍然存在，并且分离前处理和后处理脚本
        preprocess_files = [
            f for f in python_files
            if os.path.exists(f) and f.endswith('_preprocess.py')
        ]
        postprocess_files = [
            f for f in python_files
            if os.path.exists(f) and f.endswith('_postprocess.py')
        ]

        # 如果有拆分的前处理/后处理脚本，使用优化的批处理生成器
        if preprocess_files and postprocess_files:
            print(f"本次运行生成了 {len(preprocess_files)} 个前处理脚本和 {len(postprocess_files)} 个后处理脚本")
            print("生成优化的批处理脚本（最小化CAE license占用）...")

            import platform
            if platform.system() == "Windows":
                from batch_script_generator import generate_split_batch_script
                generate_split_batch_script(
                    sorted(preprocess_files),
                    sorted(postprocess_files),
                    generate_script_dir
                )
            else:
                # Linux/Unix系统生成.sh文件
                from batch_script_generator import generate_split_shell_script
                generate_split_shell_script(
                    sorted(preprocess_files),
                    sorted(postprocess_files),
                    generate_script_dir
                )
        else:
            # 向后兼容：处理旧的单体脚本
            existing_files = [f for f in python_files if os.path.exists(f)]
            if not existing_files:
                print("本次生成的文件已不存在，跳过批处理文件生成")
                return

            python_files = sorted(existing_files)
            print(f"本次运行生成了 {len(python_files)} 个Python脚本文件")

            # 检测操作系统并生成相应的脚本
            import platform
            if platform.system() == "Windows":
                generate_shell_script(python_files, generate_script_dir, "bat")
            else:
                # Linux/Unix系统只生成.sh文件
                generate_shell_script(python_files, generate_script_dir, "sh")

    except Exception as e:
        print(f"生成批处理文件时出错: {e}")


def main():
    """主函数 - 启动Qt应用程序"""
    try:
        # 清空上次运行的文件追踪列表
        clear_generated_files()
        print("已清空文件追踪列表，开始新会话")

        # 创建generate_script文件夹用于存放生成的文件
        from config import Config
        generate_script_dir = os.path.join(current_dir, Config.GENERATE_SCRIPT_DIR)
        if not os.path.exists(generate_script_dir):
            os.makedirs(generate_script_dir)
            print(f"已创建文件夹: {generate_script_dir}")

        # 创建Qt应用程序实例
        app = QApplication(sys.argv)

        # 设置应用程序属性
        app.setApplicationName("智能生成器")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("ARTC")

        # 设置应用程序图标
        icon_path = os.path.join(current_dir, "logo.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        # Windows特定: 设置任务栏图标
        if platform.system() == "Windows":
            try:
                # 设置应用程序ID，确保在任务栏显示正确的图标
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ARTC.ScriptGenerator.1.0")
            except:
                pass  # 如果设置失败，继续运行
        
        # 创建主窗口
        window = ModernInterface()

        # 设置定时器用于实时更新可视化
        def update_visualization():
            """定期检查并更新可视化"""
            if hasattr(window, 'visualization_widget'):
                current_cell_type = window.dropdowns.get("Cell type :", None)
                if current_cell_type:
                    selected_type = current_cell_type.currentText()
                    slider_value = window.slider.value() if window.slider.isEnabled() else 4
                    # 强制刷新可视化，确保使用最新的structure_set数据
                    window.visualization_widget.update_visualization(selected_type, slider_value)



        # 显示窗口
        window.show()

        # 初始化时更新可视化并强制刷新视角
        def force_refresh():
            update_visualization()
            # 强制重置视角
            if hasattr(window, 'visualization_widget') and hasattr(window.visualization_widget, 'ax'):
                window.visualization_widget.ax.view_init(elev=20, azim=135)
                window.visualization_widget.canvas.draw()

        QTimer.singleShot(Config.FORCE_REFRESH_DELAY, force_refresh)
        
        # 运行应用程序事件循环
        exit_code = app.exec_()

        # 程序退出时生成批处理文件
        generate_batch_on_exit()

        sys.exit(exit_code)
        
    except Exception as e:
        # 错误处理
        print(f"程序运行出错: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "错误", f"程序运行出错:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()