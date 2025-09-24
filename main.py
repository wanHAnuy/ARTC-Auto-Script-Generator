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

# 全局变量：追踪本次运行期间生成的文件
generated_files_this_session = []

def add_generated_file(file_path):
    """添加生成的文件到追踪列表"""
    global generated_files_this_session
    if file_path and os.path.exists(file_path) and file_path.endswith('.py'):
        if file_path not in generated_files_this_session:
            generated_files_this_session.append(file_path)
            print(f"已添加到追踪列表: {os.path.basename(file_path)}")

def get_generated_files():
    """获取本次运行生成的文件列表"""
    global generated_files_this_session
    return generated_files_this_session.copy()

def clear_generated_files():
    """清空生成文件追踪列表"""
    global generated_files_this_session
    generated_files_this_session.clear()
sys.path.insert(0, current_dir)

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


def generate_shell_script(python_files, output_dir, script_type="sh"):
    """生成shell脚本文件 (Linux .sh 或 Windows .bat)"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if script_type == "sh":
            # Linux shell script
            script_filename = f"run_all_scripts_{timestamp}.sh"
            script_path = os.path.join(output_dir, script_filename)

            # 生成shell脚本内容
            shell_content = [
                "#!/bin/bash",
                "echo 'Abaqus Batch Script Executor - Auto Generated on Exit'",
                "echo '" + "="*60 + "'",
                "",
                "# Set up Abaqus environment - modify path as needed",
                "# Common Abaqus installation paths:",
                "# export PATH=\"/usr/local/SIMULIA/Commands:$PATH\"",
                "# export PATH=\"/opt/SIMULIA/Commands:$PATH\"",
                "# export PATH=\"/apps/abaqus/Commands:$PATH\"",
                "",
                "# Check if abaqus command is available",
                "if ! command -v abaqus &> /dev/null; then",
                "    echo 'WARNING: abaqus command not found in PATH'",
                "    echo 'Please ensure Abaqus is properly installed and PATH is set'",
                "    echo 'You may need to source the Abaqus environment script'",
                "    echo 'Example: source /usr/local/SIMULIA/Commands/abaqus_v6.env'",
                "    echo 'Or add Abaqus Commands directory to PATH'",
                "    echo",
                "fi",
                ""
            ]

            for i, script_file in enumerate(python_files, 1):
                script_name = os.path.basename(script_file)
                script_dir = os.path.dirname(script_file)
                feature_data_path = os.path.join(script_dir, "feature_data.txt").replace('\\', '/')
                shell_content.extend([
                    f"echo '[{i}/{len(python_files)}] Executing script: {script_name}'",
                    f"echo 'Script path: {script_file}'",
                    f"echo 'Command: timeout 1 abaqus cae noGUI=\"{script_file}\"'",
                    "echo '" + "="*60 + "'",
                    f"# Check if feature_data.txt exists and is not empty",
                    f"if [ -s \"{feature_data_path}\" ]; then",
                    f"    echo 'feature_data.txt already exists and is not empty, skipping script execution'",
                    f"    echo 'Script {script_name} appears to be already completed'",
                    f"else",
                    f"    # Run script with timeout and retry if needed",
                    f"    retry_count=0",
                    f"    max_retries=3",
                    f"    while [ $retry_count -lt $max_retries ]; do",
                    f"        echo \"Attempt $((retry_count + 1)) of $max_retries: Running script {script_name}...\"",
                    f"        timeout 1 abaqus cae noGUI=\"{script_file}\"",
                    f"        exit_code=$?",
                    f"        ",
                    f"        # Check if feature_data.txt was generated and is not empty",
                    f"        if [ -s \"{feature_data_path}\" ]; then",
                    f"            echo 'Success: feature_data.txt generated successfully'",
                    f"            break",
                    f"        elif [ $exit_code -eq 124 ]; then",
                    f"            echo 'Script timed out after 1 second'",
                    f"        elif [ $exit_code -ne 0 ]; then",
                    f"            echo \"Script failed with exit code $exit_code\"",
                    f"        else",
                    f"            echo 'Script completed but no valid feature_data.txt found'",
                    f"        fi",
                    f"        ",
                    f"        retry_count=$((retry_count + 1))",
                    f"        if [ $retry_count -lt $max_retries ]; then",
                    f"            echo 'Retrying in 2 seconds...'",
                    f"            sleep 2",
                    f"        fi",
                    f"    done",
                    f"    ",
                    f"    if [ $retry_count -eq $max_retries ] && [ ! -s \"{feature_data_path}\" ]; then",
                    f"        echo 'ERROR: Failed to generate valid feature_data.txt after $max_retries attempts'",
                    f"    fi",
                    f"fi",
                    "echo"
                ])

            shell_content.extend([
                "echo '" + "="*60 + "'",
                "echo 'All scripts execution completed!'",
                "read -p 'Press Enter to continue...'"
            ])

            # 写入shell脚本文件
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(shell_content))

            # 设置执行权限
            import stat
            os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

            print(f"Shell脚本已生成: {script_filename}")
            print(f"文件路径: {script_path}")
            print("在Linux中可执行: chmod +x script.sh && ./script.sh")

        else:  # bat
            # Windows batch script (original logic)
            script_filename = f"run_all_scripts_{timestamp}.bat"
            script_path = os.path.join(output_dir, script_filename)

            batch_content = [
                "@echo off",
                "setlocal enabledelayedexpansion",
                "echo Abaqus Batch Script Executor - Auto Generated on Exit",
                "echo " + "="*60,
                ""
            ]

            for i, script_file in enumerate(python_files, 1):
                script_name = os.path.basename(script_file)
                script_dir = os.path.dirname(script_file)
                feature_data_path = os.path.join(script_dir, "feature_data.txt")
                batch_content.extend([
                    f"echo [{i}/{len(python_files)}] Executing script: {script_name}",
                    f"echo Script path: {script_file}",
                    f"echo Command: timeout 1 abaqus cae noGUI=\"{script_file}\"",
                    "echo " + "="*60,
                    f"rem Check if feature_data.txt exists and is not empty",
                    f"if exist \"{feature_data_path}\" (",
                    f"    for %%i in (\"{feature_data_path}\") do set size=%%~zi",
                    f"    if !size! gtr 0 (",
                    f"        echo feature_data.txt already exists and is not empty, skipping script execution",
                    f"        echo Script {script_name} appears to be already completed",
                    f"        goto :next{i}",
                    f"    )",
                    f")",
                    f"rem Run script with timeout and retry if needed",
                    f"set retry_count=0",
                    f"set max_retries=3",
                    f":retry_loop{i}",
                    f"set /a attempt=!retry_count!+1",
                    f"echo Attempt !attempt! of !max_retries!: Running script {script_name}...",
                    f"timeout 1 abaqus cae noGUI=\"{script_file}\"",
                    f"set exit_code=!errorlevel!",
                    f"",
                    f"rem Check if feature_data.txt was generated and is not empty",
                    f"if exist \"{feature_data_path}\" (",
                    f"    for %%i in (\"{feature_data_path}\") do set size=%%~zi",
                    f"    if !size! gtr 0 (",
                    f"        echo Success: feature_data.txt generated successfully",
                    f"        goto :next{i}",
                    f"    )",
                    f")",
                    f"",
                    f"if !exit_code! equ 1 (",
                    f"    echo Script timed out after 1 second",
                    f") else if !exit_code! neq 0 (",
                    f"    echo Script failed with exit code !exit_code!",
                    f") else (",
                    f"    echo Script completed but no valid feature_data.txt found",
                    f")",
                    f"",
                    f"set /a retry_count+=1",
                    f"if !retry_count! lss !max_retries! (",
                    f"    echo Retrying in 2 seconds...",
                    f"    timeout /t 2 >nul",
                    f"    goto :retry_loop{i}",
                    f")",
                    f"",
                    f"echo ERROR: Failed to generate valid feature_data.txt after !max_retries! attempts",
                    f":next{i}",
                    "echo."
                ])

            batch_content.extend([
                "echo " + "="*60,
                "echo All scripts execution completed!",
                "pause"
            ])

            with open(script_path, 'w', encoding='ascii', errors='ignore') as f:
                f.write('\n'.join(batch_content))

            print(f"批处理文件已生成: {script_filename}")
            print(f"文件路径: {script_path}")
            print("可在Abaqus Command中执行此批处理文件")

        return script_path

    except Exception as e:
        print(f"生成脚本文件时出错: {e}")
        return None


def generate_batch_on_exit():
    """程序退出时生成批处理文件"""
    try:
        print("\n程序退出，正在生成批处理文件...")

        # 获取generate_script目录
        generate_script_dir = os.path.join(current_dir, "generate_script")
        if not os.path.exists(generate_script_dir):
            print("未找到generate_script目录，跳过批处理文件生成")
            return

        # 使用本次运行生成的文件列表，而不是遍历所有文件
        python_files = get_generated_files()

        if not python_files:
            print("本次运行未生成任何Python脚本文件，跳过批处理文件生成")
            return

        # 过滤确保文件仍然存在
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
            # Linux/Unix系统同时生成.sh和.bat文件
            generate_shell_script(python_files, generate_script_dir, "sh")
            generate_shell_script(python_files, generate_script_dir, "bat")  # 也生成bat以备跨平台使用

    except Exception as e:
        print(f"生成批处理文件时出错: {e}")


def main():
    """主函数 - 启动Qt应用程序"""
    try:
        # 清空上次运行的文件追踪列表
        clear_generated_files()
        print("已清空文件追踪列表，开始新会话")

        # 创建generate_script文件夹用于存放生成的文件
        generate_script_dir = os.path.join(current_dir, "generate_script")
        if not os.path.exists(generate_script_dir):
            os.makedirs(generate_script_dir)
            print(f"已创建文件夹: {generate_script_dir}")

            # 创建批量执行器脚本 - 已禁用，只生成bat文件
            # from script_generator import AbaqusScriptGenerator
            # generator = AbaqusScriptGenerator()
            # generator.create_batch_executor(generate_script_dir)

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