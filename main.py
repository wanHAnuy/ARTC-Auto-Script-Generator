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

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtGui import QIcon
    from qt_interface import ModernInterface
    from structure_set import get_crystal_structure
    from PyQt5.QtCore import QTimer
    import ctypes
    import platform
except ImportError as e:
    print("错误: 无法导入必要的模块")
    print(f"详细错误: {e}")
    print("请确保已安装PyQt5: pip install PyQt5")
    sys.exit(1)


def main():
    """主函数 - 启动Qt应用程序"""
    try:
        # 创建generate_script文件夹用于存放生成的文件
        generate_script_dir = os.path.join(current_dir, "generate_script")
        if not os.path.exists(generate_script_dir):
            os.makedirs(generate_script_dir)
            print(f"已创建文件夹: {generate_script_dir}")

            # 创建批量执行器脚本
            from script_generator import AbaqusScriptGenerator
            generator = AbaqusScriptGenerator()
            generator.create_batch_executor(generate_script_dir)

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

        # # 初始化时立即更新一次可视化，并强制刷新视角
        def force_refresh():
            update_visualization()
            # 强制重置视角
            if hasattr(window, 'visualization_widget') and hasattr(window.visualization_widget, 'ax'):
                window.visualization_widget.ax.view_init(elev=20, azim=135)
                window.visualization_widget.canvas.draw()

        QTimer.singleShot(1000, force_refresh)  # 延迟1秒确保界面完全加载
        
        # 运行应用程序事件循环
        sys.exit(app.exec_())
        
    except Exception as e:
        # 错误处理
        print(f"程序运行出错: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "错误", f"程序运行出错:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()