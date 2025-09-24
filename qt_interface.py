import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                           QWidget, QComboBox, QLabel, QPushButton, QFrame, QGridLayout, QSplitter, QCheckBox, QSlider, QMenuBar, QAction)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QIcon
from visualization_widget import CellVisualizationWidget
from script_generator import generate_abaqus_script
# 避免循环导入，在需要时动态导入


class ModernInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Generator")
        self.setGeometry(100, 100, 1500, 800)
        # 设置窗口图标
        self.set_window_icon()

        # 主题设置
        self.current_theme = "space"  # 默认太空灰主题

        # 设置文件路径
        self.settings_file = os.path.join(os.path.dirname(__file__), "ui_settings.json")

        self.setStyleSheet(self.get_stylesheet())
        self.init_ui()

        # 加载上次保存的设置
        self.load_settings()

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 处理 PyInstaller 打包后的资源文件路径
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                icon_path = os.path.join(sys._MEIPASS, 'logo.ico')
            else:
                # 开发环境
                icon_path = os.path.join(os.path.dirname(__file__), 'logo.ico')

            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Failed to set window icon: {e}")
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 创建标题和主题按钮的水平布局
        title_layout = QHBoxLayout()

        title_label = QLabel("Smart Generator")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)

        # 创建主题切换按钮容器
        theme_buttons_widget = QWidget()
        theme_buttons_layout = QHBoxLayout(theme_buttons_widget)
        theme_buttons_layout.setContentsMargins(0, 0, 0, 0)
        theme_buttons_layout.setSpacing(10)

        # 森林绿主题按钮
        self.forest_btn = QPushButton()
        self.forest_btn.setObjectName("forest_theme_btn")
        self.forest_btn.setFixedSize(40, 40)
        self.forest_btn.clicked.connect(lambda: self.change_theme('forest'))
        self.forest_btn.setToolTip("森林绿主题")

        # 日落紫主题按钮
        self.sunset_btn = QPushButton()
        self.sunset_btn.setObjectName("sunset_theme_btn")
        self.sunset_btn.setFixedSize(40, 40)
        self.sunset_btn.clicked.connect(lambda: self.change_theme('sunset'))
        self.sunset_btn.setToolTip("日落紫主题")

        # 太空灰主题按钮
        self.space_btn = QPushButton()
        self.space_btn.setObjectName("space_theme_btn")
        self.space_btn.setFixedSize(40, 40)
        self.space_btn.clicked.connect(lambda: self.change_theme('space'))
        self.space_btn.setToolTip("太空灰主题")

        theme_buttons_layout.addWidget(self.forest_btn)
        theme_buttons_layout.addWidget(self.sunset_btn)
        theme_buttons_layout.addWidget(self.space_btn)

        # 添加到标题布局
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(theme_buttons_widget)

        main_layout.addLayout(title_layout)

        # Create horizontal splitter for controls and visualization
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #bdc3c7; }")

        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        form_frame = QFrame()
        form_frame.setObjectName("form_frame")
        form_layout = QGridLayout(form_frame)
        form_layout.setSpacing(20)
        form_layout.setVerticalSpacing(25)
        
        dropdown_configs = [
            ("Cell type :", [
            "Cubic",
            "BCC",
            "BCCZ",
            "Octet_truss",
            "AFCC",
            "Truncated_cube",
            "FCC",
            "FCCZ",
            "Tetrahedron_base",
            "Iso_truss",
            "G7",
            "FBCCZ",
            "FBCCXYZ",
            "Cuboctahedron_Z",
            "Diamond",
            "Rhombic",
            "Kelvin",
            "Auxetic",
            "Octahedron",
            "Truncated_Octoctahedron",
            # "Cubic_Rosette_self_create"
            ]),
            ("Speed:", ["10", "100", "1000"]),
            ("Directions:", ["X", "Z"]),
            ("Cell size:", ["5", "7", "9","11","13"]),
            ("Strut radius:", ["0.5", "0.45", "0.4", "0.35", "0.3"])
        ]
        
        self.dropdowns = {}
        self.checkboxes = {}
        self.checkbox_labels = {}  # Store label references for Speed and Direction
        self.slider = None
        self.slider_checkbox = None

        # 连续运行相关变量
        self.is_batch_running = False
        self.current_batch_index = 0
        self.batch_timer = None
        self.batch_parent_dir = None

        for i, (label_text, options) in enumerate(dropdown_configs):
            label = QLabel(label_text)
            label.setObjectName("field_label")

            # Store references to Speed and Direction labels and set initial gray color
            if label_text in ["Speed:", "Directions:"]:
                self.checkbox_labels[label_text] = label
                label.setStyleSheet("color: #95a5a6; font-size: 27px; font-weight: 600; padding: 8px 0;")

            dropdown = QComboBox()
            dropdown.setObjectName("dropdown")
            dropdown.addItems(options)
            dropdown.setCurrentIndex(0)

            # Connect cell type dropdown to visualization update
            if label_text == "Cell type :":
                dropdown.currentTextChanged.connect(self.on_cell_type_changed)

            form_layout.addWidget(label, i, 0)
            form_layout.addWidget(dropdown, i, 1)

            # Add checkbox for Speed and Directions
            if label_text in ["Speed:", "Directions:"]:
                checkbox = QCheckBox()
                checkbox.setObjectName("checkbox")
                checkbox.setChecked(False)  # Default unchecked
                # Connect checkbox signal for mutual exclusion and label color update
                checkbox.toggled.connect(lambda checked, label=label_text: self.on_speed_direction_checkbox_changed(checked, label))
                form_layout.addWidget(checkbox, i, 2)
                self.checkboxes[label_text] = checkbox

            self.dropdowns[label_text] = dropdown

        # Add slider control at the bottom
        slider_row = len(dropdown_configs)
        slider_label = QLabel("Transform:")
        slider_label.setObjectName("field_label")

        # Create slider with 9 steps (0-8), default value at middle (4)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setObjectName("slider")
        self.slider.setMinimum(0)
        self.slider.setMaximum(8)
        self.slider.setValue(4)  # Middle value
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)

        # Store reference to slider label for styling updates
        self.slider_label = slider_label

        # Create checkbox for slider
        self.slider_checkbox = QCheckBox()
        self.slider_checkbox.setObjectName("checkbox")
        self.slider_checkbox.setChecked(False)

        # Connect slider checkbox to button style updates
        self.slider_checkbox.toggled.connect(self.update_button_style)

        # Add slider components to form layout
        form_layout.addWidget(slider_label, slider_row, 0)
        form_layout.addWidget(self.slider, slider_row, 1)
        form_layout.addWidget(self.slider_checkbox, slider_row, 2)

        # Connect cell type change to slider state update
        if "Cell type :" in self.dropdowns:
            self.dropdowns["Cell type :"].currentTextChanged.connect(self.update_slider_state)

        # Connect slider value change to visualization update
        self.slider.valueChanged.connect(self.on_slider_changed)

        # Store slider values for each cell type to maintain state
        self.slider_values = {}

        # Initialize slider state based on current cell type
        self.update_slider_state()

        left_layout.addWidget(form_frame)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.generate_button = QPushButton("Generate Script")
        self.generate_button.setObjectName("generate_button")
        self.generate_button.clicked.connect(self.generate_config)
        
        button_layout.addWidget(self.generate_button)

        # 添加间距
        button_layout.addSpacing(20)

        # 添加主题色三角按钮
        self.triangle_button = QPushButton("")
        self.triangle_button.setObjectName("triangle_button")
        self.triangle_button.setFixedSize(60, 60)  # 稍微增大尺寸
        self.triangle_button.setToolTip("批量生成脚本")  # 添加工具提示
        self.triangle_button.clicked.connect(self.on_triangle_button_clicked)
        # 初始化按钮样式
        self.update_triangle_button_style()

        button_layout.addWidget(self.triangle_button)
        button_layout.addStretch()

        left_layout.addLayout(button_layout)
        left_layout.addStretch()

        # Right panel for visualization
        self.visualization_widget = CellVisualizationWidget()

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.visualization_widget)
        splitter.setSizes([1000, 500])  # Set initial sizes - give more space to visualization

        main_layout.addWidget(splitter)

        # Initialize visualization with default cubic display
        QTimer.singleShot(100, self.init_default_visualization)

        # 初始化主题按钮状态
        QTimer.singleShot(200, self.update_theme_button_states)

    def save_settings(self):
        """保存当前UI设置到JSON文件"""
        try:
            settings = {
                "theme": self.current_theme,
                "dropdowns": {},
                "checkboxes": {},
                "slider_value": self.slider.value() if self.slider else 4,
                "slider_checkbox": self.slider_checkbox.isChecked() if self.slider_checkbox else False,
                "slider_values": getattr(self, 'slider_values', {})
            }

            # 保存下拉框的当前选择
            for label_text, dropdown in self.dropdowns.items():
                settings["dropdowns"][label_text] = dropdown.currentText()

            # 保存复选框状态
            for label_text, checkbox in self.checkboxes.items():
                settings["checkboxes"][label_text] = checkbox.isChecked()

            # 写入JSON文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            print(f"设置已保存到: {self.settings_file}")

        except Exception as e:
            print(f"保存设置失败: {str(e)}")

    def load_settings(self):
        """从JSON文件加载UI设置"""
        try:
            if not os.path.exists(self.settings_file):
                print("设置文件不存在，使用默认设置")
                return

            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # 恢复主题
            if "theme" in settings:
                self.current_theme = settings["theme"]
                self.setStyleSheet(self.get_stylesheet())

            # 恢复下拉框选择
            if "dropdowns" in settings:
                for label_text, value in settings["dropdowns"].items():
                    if label_text in self.dropdowns:
                        dropdown = self.dropdowns[label_text]
                        index = dropdown.findText(value)
                        if index >= 0:
                            dropdown.setCurrentIndex(index)

            # 恢复复选框状态
            if "checkboxes" in settings:
                for label_text, checked in settings["checkboxes"].items():
                    if label_text in self.checkboxes:
                        self.checkboxes[label_text].setChecked(checked)

            # 恢复滑块值
            if "slider_value" in settings and self.slider:
                self.slider.setValue(settings["slider_value"])

            # 恢复滑块复选框状态
            if "slider_checkbox" in settings and self.slider_checkbox:
                self.slider_checkbox.setChecked(settings["slider_checkbox"])

            # 恢复滑块值字典
            if "slider_values" in settings:
                self.slider_values = settings["slider_values"]


            print(f"设置已从 {self.settings_file} 加载")

            # 更新相关UI状态
            QTimer.singleShot(300, self.update_ui_after_load)

        except Exception as e:
            print(f"加载设置失败: {str(e)}")

    def update_ui_after_load(self):
        """加载设置后更新UI状态"""
        try:
            # 更新主题按钮状态
            self.update_theme_button_states()

            # 更新Speed和Direction标签颜色
            self.update_checkbox_labels()

            # 更新滑块状态
            self.update_slider_state()

            # 如果slider checkbox被选中，更新按钮样式
            if hasattr(self, 'slider_checkbox') and self.slider_checkbox.isChecked():
                self.update_button_style(True)

            # 更新可视化
            if hasattr(self, 'visualization_widget'):
                current_cell_type = self.dropdowns.get("Cell type :", None)
                if current_cell_type:
                    cell_type = current_cell_type.currentText()
                    slider_value = self.slider.value() if self.slider.isEnabled() else 4
                    self.visualization_widget.update_visualization(cell_type, slider_value)

        except Exception as e:
            print(f"更新UI状态失败: {str(e)}")

    def update_checkbox_labels(self):
        """更新复选框标签颜色"""
        for label_text in ["Speed:", "Directions:"]:
            if label_text in self.checkbox_labels:
                checkbox = self.checkboxes.get(label_text)
                if checkbox and checkbox.isChecked():
                    # Checkbox is checked - set label color to appropriate theme color
                    if self.current_theme == "forest":
                        color = "#e8f5e8"
                    elif self.current_theme == "sunset":
                        color = "#fff3e0"
                    elif self.current_theme == "space":
                        color = "#ecf0f1"
                    else:
                        color = "#2c3e50"
                    self.checkbox_labels[label_text].setStyleSheet(f"color: {color}; font-size: 27px; font-weight: 600; padding: 8px 0;")
                else:
                    # Checkbox is unchecked - set label color to gray
                    self.checkbox_labels[label_text].setStyleSheet("color: #95a5a6; font-size: 27px; font-weight: 600; padding: 8px 0;")

    def closeEvent(self, event):
        """窗口关闭时保存设置"""
        self.save_settings()
        event.accept()


    def change_theme(self, theme_name):
        """切换主题"""
        self.current_theme = theme_name
        self.setStyleSheet(self.get_stylesheet())
        self.update_theme_button_states()
        # 更新三角按钮样式
        if hasattr(self, 'triangle_button'):
            self.update_triangle_button_style()

        # 更新按钮样式（如果slider checkbox被选中）
        if hasattr(self, 'slider_checkbox') and self.slider_checkbox.isChecked():
            self.update_button_style(True)

    def update_theme_button_states(self):
        """更新主题按钮的状态"""
        # 重置所有按钮状态
        if hasattr(self, 'forest_btn'):
            self.forest_btn.setProperty("active", self.current_theme == "forest")
            self.forest_btn.style().unpolish(self.forest_btn)
            self.forest_btn.style().polish(self.forest_btn)

        if hasattr(self, 'sunset_btn'):
            self.sunset_btn.setProperty("active", self.current_theme == "sunset")
            self.sunset_btn.style().unpolish(self.sunset_btn)
            self.sunset_btn.style().polish(self.sunset_btn)

        if hasattr(self, 'space_btn'):
            self.space_btn.setProperty("active", self.current_theme == "space")
            self.space_btn.style().unpolish(self.space_btn)
            self.space_btn.style().polish(self.space_btn)

    def init_default_visualization(self):
        """Initialize the visualization with default cubic display"""
        if hasattr(self, 'visualization_widget'):
            # Get the default cell type (should be "Cubic")
            default_cell_type = "Cubic"
            default_slider_value = 4  # Default slider value
            self.visualization_widget.update_visualization(default_cell_type, default_slider_value)

    def generate_config(self):
        # 检查是否是连续运行模式
        if self.slider_checkbox and self.slider_checkbox.isChecked() and self.slider.isEnabled():
            self.start_batch_generation()
        else:
            self.generate_single_config()

    def start_batch_generation(self):
        """开始连续运行模式，slider值从0到8依次变化"""
        if self.is_batch_running:
            return  # 如果已经在运行，则忽略

        self.is_batch_running = True
        self.current_batch_index = 0

        # 禁用按钮防止重复点击
        self.generate_button.setEnabled(False)

        # 开始第一次生成
        self.generate_batch_step()


    def generate_batch_step(self):
        """执行连续运行的单步操作"""
        if not self.is_batch_running or self.current_batch_index > 8:
            self.finish_batch_generation()
            return

        # 设置当前slider值
        self.slider.setValue(self.current_batch_index)

        # 更新按钮文本显示当前进度
        self.generate_button.setText(f"running... {self.current_batch_index + 1}/9")

        # 生成当前配置的脚本
        self.generate_single_config_for_batch()

        # 准备下一步
        self.current_batch_index += 1

        # 使用定时器延迟执行下一步，给用户看到进度
        if not self.batch_timer:
            self.batch_timer = QTimer()
            self.batch_timer.setSingleShot(True)
            self.batch_timer.timeout.connect(self.generate_batch_step)

        self.batch_timer.start(500)  # 500ms延迟

    def generate_single_config_for_batch(self):
        """为连续运行模式生成单个配置的脚本"""
        try:
            # 收集UI配置
            config = {}
            for label_text, dropdown in self.dropdowns.items():
                config[label_text.replace(":", "").strip()] = dropdown.currentText()

            # 收集复选框状态
            checkbox_config = {}
            for label_text, checkbox in self.checkboxes.items():
                checkbox_config[label_text.replace(":", "").strip()] = checkbox.isChecked()

            # 提取关键参数
            cell_type = config.get('Cell type', 'Cubic')
            cell_size = config.get('Cell size', '5')
            cell_radius = config.get('Strut radius', '0.5')

            # 使用当前slider值
            slider_value = self.current_batch_index

            print(f"连续运行第 {self.current_batch_index + 1}/9 步:")
            print(f"Cell type: {cell_type}, Slider value: {slider_value}")

            # 确定速度和方向设置
            speed_value = None
            direction_value = None

            if checkbox_config.get('Speed', False):
                speed_value = config.get('Speed', 'low')
            if checkbox_config.get('Directions', False):
                direction_value = config.get('Directions', 'X')

            # 生成脚本（批量模式）
            success, message, filename = generate_abaqus_script(
                cell_type=cell_type,
                cell_size=float(cell_size),
                cell_radius=float(cell_radius),
                slider=slider_value,
                speed_value=speed_value,
                direction_value=direction_value,
                batch_mode=True,
                batch_parent_dir=self.batch_parent_dir
            )

            if success:
                print(f"第 {self.current_batch_index + 1} 步生成成功: {filename}")
            else:
                print(f"第 {self.current_batch_index + 1} 步生成失败: {message}")

        except Exception as e:
            print(f"连续运行第 {self.current_batch_index + 1} 步出错: {str(e)}")

    def finish_batch_generation(self):
        """完成连续运行"""
        self.is_batch_running = False
        self.current_batch_index = 0
        self.batch_parent_dir = None

        # 显示完成状态
        self.generate_button.setText("Down!")

        # 1秒后重置按钮
        QTimer.singleShot(1000, self.reset_button)

    def generate_single_config(self):
        """单次生成配置（原有逻辑）"""
        try:
            # 收集UI配置
            config = {}
            for label_text, dropdown in self.dropdowns.items():
                config[label_text.replace(":", "").strip()] = dropdown.currentText()

            # 收集复选框状态
            checkbox_config = {}
            for label_text, checkbox in self.checkboxes.items():
                checkbox_config[label_text.replace(":", "").strip()] = checkbox.isChecked()

            # 提取关键参数
            cell_type = config.get('Cell type', 'Cubic')
            cell_size = config.get('Cell size', '5')
            cell_radius = config.get('Strut radius', '0.5')

            # 获取slider值
            slider_value = self.slider.value() if self.slider and self.slider.isEnabled() else 4

            print("生成的配置:")
            for key, value in config.items():
                print(f"{key}: {value}")
            for key, value in checkbox_config.items():
                print(f"{key} (选中): {value}")
            print(f"Slider value: {slider_value}")

            # 更新按钮状态
            self.generate_button.setText("waiting...")
            self.generate_button.setEnabled(False)

            # 确定速度和方向设置
            speed_value = None
            direction_value = None

            if checkbox_config.get('Speed', False):
                speed_value = config.get('Speed', 'low')
            if checkbox_config.get('Directions', False):
                direction_value = config.get('Directions', 'X')

            # 生成脚本
            success, message, filename = generate_abaqus_script(
                cell_type=cell_type,
                cell_size=float(cell_size),
                cell_radius=float(cell_radius),
                slider=slider_value,
                speed_value=speed_value,
                direction_value=direction_value
            )

            if success:
                self.generate_button.setText(f"Down! {filename}")
                print(f"脚本生成成功: {filename}")
            else:
                self.generate_button.setText("生成失败!")
                print(f"脚本生成失败: {message}")

        except Exception as e:
            self.generate_button.setText("生成出错!")
            print(f"生成脚本时出错: {str(e)}")

        # 0.3秒后重置按钮
        QTimer.singleShot(300, self.reset_button)
    
    def reset_button(self):
        # 重置按钮状态，但不干扰正在进行的连续运行
        if not self.is_batch_running:
            self.generate_button.setText("Generate Script")
            self.generate_button.setEnabled(True)

    def on_triangle_button_clicked(self):
        """红色三角按钮点击事件处理 - 批量生成脚本"""
        print("开始批量生成脚本...")

        # 动态导入避免循环依赖
        try:
            import main
            clear_generated_files = main.clear_generated_files
            generate_shell_script = main.generate_shell_script
            get_generated_files = main.get_generated_files
        except ImportError as e:
            print(f"无法导入main模块: {e}")
            return

        # 定义Cell Type分组
        cell_type_groups = [
            ("Group 1-4", ["Cubic", "BCC", "BCCZ", "Octet_truss"]),
            ("Group 5-7", ["AFCC", "Truncated_cube", "FCC"]),
            ("Group 8-10", ["FCCZ", "Tetrahedron_base", "Iso_truss"]),
            ("Group 11-13", ["G7", "FBCCZ", "FBCCXYZ"]),
            ("Group 14-16", ["Cuboctahedron_Z", "Diamond", "Rhombic"]),
            ("Group 17-20", ["Kelvin", "Auxetic", "Octahedron", "Truncated_Octoctahedron"])
        ]

        # 无slider功能的cell types
        no_slider_types = ["Cubic", "Octahedron"]

        try:
            # 禁用按钮防止重复点击
            self.triangle_button.setEnabled(False)

            total_groups = len(cell_type_groups)
            current_group = 0

            for group_name, cell_types in cell_type_groups:
                current_group += 1
                print(f"\n=== 处理 {group_name} ({current_group}/{total_groups}) ===")

                # 清空文件追踪列表
                clear_generated_files()

                for cell_type in cell_types:
                    print(f"正在处理 Cell Type: {cell_type}")

                    # 设置当前cell type
                    if "Cell type :" in self.dropdowns:
                        dropdown = self.dropdowns["Cell type :"]
                        index = dropdown.findText(cell_type)
                        if index >= 0:
                            dropdown.setCurrentIndex(index)

                    if cell_type in no_slider_types:
                        # 只生成1个脚本
                        self._generate_single_script(cell_type, 4)  # 使用默认slider值4
                    else:
                        # 生成9个脚本 (slider值 0-8)
                        for slider_value in range(9):
                            self._generate_single_script(cell_type, slider_value)

                # 生成当前组的批处理脚本
                python_files = get_generated_files()
                if python_files:
                    print(f"{group_name} 共生成 {len(python_files)} 个脚本文件")

                    # 获取输出目录
                    if python_files:
                        output_dir = os.path.dirname(python_files[0])

                        # 检测操作系统并生成相应的脚本
                        import platform
                        if platform.system() == "Windows":
                            generate_shell_script(python_files, output_dir, "bat")
                        else:
                            generate_shell_script(python_files, output_dir, "sh")
                            generate_shell_script(python_files, output_dir, "bat")

                        print(f"{group_name} 批处理脚本生成完成")
                else:
                    print(f"警告: {group_name} 未生成任何脚本文件")

            print("\n=== 所有批处理脚本生成完成! ===")

            # 生成主控制脚本
            self.generate_master_control_script()

            # 清理历史文件追踪
            clear_generated_files()
            print("已清理文件追踪历史")

        except Exception as e:
            print(f"批量生成脚本时出错: {str(e)}")
        finally:
            # 显示完成星星特效
            self.show_completion_star()
            # 重新启用按钮
            self.triangle_button.setEnabled(True)

    def _generate_single_script(self, cell_type, slider_value):
        """生成单个脚本的辅助函数"""
        try:
            # 收集当前配置
            config = {}
            for label_text, dropdown in self.dropdowns.items():
                config[label_text.replace(":", "").strip()] = dropdown.currentText()

            # 收集复选框状态
            checkbox_config = {}
            for label_text, checkbox in self.checkboxes.items():
                checkbox_config[label_text.replace(":", "").strip()] = checkbox.isChecked()

            # 使用传入的参数覆盖cell_type
            config['Cell type'] = cell_type

            # 提取参数
            cell_size = config.get('Cell size', '5')
            cell_radius = config.get('Strut radius', '0.5')

            # 确定速度和方向设置
            speed_value = None
            direction_value = None
            if checkbox_config.get('Speed', False):
                speed_value = config.get('Speed', '10')
            if checkbox_config.get('Directions', False):
                direction_value = config.get('Directions', 'X')

            # 生成脚本
            success, message, filename = generate_abaqus_script(
                cell_type=cell_type,
                cell_size=float(cell_size),
                cell_radius=float(cell_radius),
                slider=slider_value,
                speed_value=speed_value,
                direction_value=direction_value
            )

            if success:
                print(f"  ✓ 生成成功: {filename}")
            else:
                print(f"  ✗ 生成失败: {message}")

            return success

        except Exception as e:
            print(f"  ✗ 生成脚本时出错: {str(e)}")
            return False

    def on_speed_direction_checkbox_changed(self, checked, label):
        """Handle mutual exclusion between Speed and Directions checkboxes and update label colors"""
        if checked:
            # If this checkbox is being checked, uncheck the other one
            for other_label, other_checkbox in self.checkboxes.items():
                if other_label != label and other_label in ["Speed:", "Directions:"]:
                    other_checkbox.setChecked(False)

        # Update label colors based on checkbox states
        for label_text in ["Speed:", "Directions:"]:
            if label_text in self.checkbox_labels:
                checkbox = self.checkboxes.get(label_text)
                if checkbox and checkbox.isChecked():
                    # Checkbox is checked - set label color to appropriate theme color
                    if self.current_theme == "forest":
                        color = "#e8f5e8"
                    elif self.current_theme == "sunset":
                        color = "#fff3e0"
                    elif self.current_theme == "space":
                        color = "#ecf0f1"
                    else:
                        color = "#2c3e50"
                    self.checkbox_labels[label_text].setStyleSheet(f"color: {color}; font-size: 27px; font-weight: 600; padding: 8px 0;")
                else:
                    # Checkbox is unchecked - set label color to gray
                    self.checkbox_labels[label_text].setStyleSheet("color: #95a5a6; font-size: 27px; font-weight: 600; padding: 8px 0;")

    def on_cell_type_changed(self, cell_type):
        """Update visualization when cell type changes"""
        if hasattr(self, 'visualization_widget'):
            slider_value = self.slider.value() if self.slider.isEnabled() else 4
            self.visualization_widget.update_visualization(cell_type, slider_value)

    def on_slider_changed(self, value):
        """Update visualization when slider value changes"""
        if hasattr(self, 'visualization_widget'):
            current_cell_type = self.dropdowns.get("Cell type :", None)
            if current_cell_type and self.slider.isEnabled():
                cell_type = current_cell_type.currentText()
                self.visualization_widget.update_visualization(cell_type, value, reset_view_angle=False)

    def update_slider_state(self):
        """Update slider enabled state based on cell type"""
        if hasattr(self, 'slider') and self.slider is not None:
            current_cell_type = self.dropdowns.get("Cell type :", None)
            if current_cell_type:
                previous_cell_type = getattr(self, 'previous_cell_type', None)
                cell_type = current_cell_type.currentText()

                # Save current slider value for the previous cell type
                if previous_cell_type and hasattr(self, 'slider_values'):
                    self.slider_values[previous_cell_type] = self.slider.value()

                # Disable slider for specific cell types
                disabled_types = ["Cubic", "Octahedron"]
                should_disable = cell_type in disabled_types

                # Restore slider value for the current cell type (if previously saved)
                if not should_disable and hasattr(self, 'slider_values'):
                    if cell_type in self.slider_values:
                        # Temporarily disconnect to avoid triggering updates during restoration
                        self.slider.valueChanged.disconnect(self.on_slider_changed)
                        self.slider.setValue(self.slider_values[cell_type])
                        self.slider.valueChanged.connect(self.on_slider_changed)
                    else:
                        # Set default value for new cell type
                        self.slider_values[cell_type] = 4

                # Update slider and checkbox states
                self.slider.setEnabled(not should_disable)
                if hasattr(self, 'slider_checkbox') and self.slider_checkbox is not None:
                    if should_disable:
                        # For disabled cell types, set checkbox to off and disable it
                        self.slider_checkbox.setChecked(False)
                        self.slider_checkbox.setEnabled(False)
                    else:
                        # For enabled cell types, enable checkbox but don't change its state
                        self.slider_checkbox.setEnabled(True)

                # Update label color based on state
                if hasattr(self, 'slider_label') and self.slider_label is not None:
                    if should_disable:
                        self.slider_label.setStyleSheet("color: #95a5a6; font-size: 27px; font-weight: 600; padding: 8px 0;")
                    else:
                        self.slider_label.setStyleSheet("color: #2c3e50; font-size: 27px; font-weight: 600; padding: 8px 0;")

                # Store current cell type for next time
                self.previous_cell_type = cell_type

    def update_triangle_button_style(self):
        """更新三角按钮样式以匹配当前主题"""
        if self.current_theme == "forest":
            # 绿色主题
            style = """
                #triangle_button {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4caf50, stop:0.5 #2e7d32, stop:1 #1b5e20);
                    color: white;
                    border: 2px solid #66bb6a;
                    border-radius: 30px;
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #66bb6a, stop:0.5 #43a047, stop:1 #2e7d32);
                    border: 2px solid #81c784;
                    transform: scale(1.05);
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2e7d32, stop:0.5 #1b5e20, stop:1 #0d4b0b);
                    border: 2px solid #4caf50;
                    transform: scale(0.95);
                }
            """
        elif self.current_theme == "sunset":
            # 紫红色主题
            style = """
                #triangle_button {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ff4444, stop:0.5 #cc0000, stop:1 #990000);
                    color: white;
                    border: 2px solid #ff6666;
                    border-radius: 30px;
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ff6666, stop:0.5 #dd2222, stop:1 #aa1111);
                    border: 2px solid #ff8888;
                    transform: scale(1.05);
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #cc2222, stop:0.5 #990000, stop:1 #660000);
                    border: 2px solid #cc4444;
                    transform: scale(0.95);
                }
            """
        else:  # space theme
            # 蓝色主题
            style = """
                #triangle_button {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #3498db, stop:0.5 #2980b9, stop:1 #1f5f8a);
                    color: white;
                    border: 2px solid #5dade2;
                    border-radius: 30px;
                    font-size: 24px;
                    font-weight: bold;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #5dade2, stop:0.5 #3498db, stop:1 #2980b9);
                    border: 2px solid #85c1e9;
                    transform: scale(1.05);
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2980b9, stop:0.5 #1f5f8a, stop:1 #154d6b);
                    border: 2px solid #3498db;
                    transform: scale(0.95);
                }
            """

        self.triangle_button.setStyleSheet(style)

    def show_completion_star(self):
        """显示完成星星特效"""
        # 显示星星
        self.triangle_button.setText("🌟")

        # 设置星星样式
        star_style = """
            #triangle_button {
                background: qlinear-gradient(45deg, #ffd700, #ffed4e, #ffd700);
                color: #333;
                border: 3px solid #ffd700;
                border-radius: 30px;
                font-size: 32px;
                font-weight: bold;
                text-align: center;
                box-shadow: 0 0 15px #ffd700;
            }
        """
        self.triangle_button.setStyleSheet(star_style)

        # 3秒后恢复正常样式
        QTimer.singleShot(3000, self.restore_triangle_button_style)

    def restore_triangle_button_style(self):
        """恢复三角按钮正常样式"""
        self.triangle_button.setText("")
        self.update_triangle_button_style()

    def generate_master_control_script(self):
        """生成主控制脚本用于并行计算"""
        try:
            from datetime import datetime

            # 获取输出目录（使用generate_script文件夹）
            output_dir = os.path.join(os.path.dirname(__file__), "generate_script")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 生成Linux并行脚本
            self.create_linux_parallel_script(output_dir, timestamp)

            # 生成Windows并行脚本
            self.create_windows_parallel_script(output_dir, timestamp)

            print(f"主控制脚本已生成在: {output_dir}")

        except Exception as e:
            print(f"生成主控制脚本时出错: {str(e)}")

    def create_linux_parallel_script(self, output_dir, timestamp):
        """创建Linux并行执行脚本"""
        # tmux版本
        tmux_script_path = os.path.join(output_dir, f"run_parallel_tmux_{timestamp}.sh")
        tmux_content = """#!/bin/bash
# 并行执行批处理脚本 - tmux版本
echo "启动并行计算 - 使用tmux多窗格监控"

# 检查tmux是否安装
if ! command -v tmux &> /dev/null; then
    echo "错误: tmux未安装，请先安装tmux或使用简单并行版本"
    exit 1
fi

# 查找所有批处理脚本
batch_files=($(ls run_all_scripts_*.sh 2>/dev/null))

if [ ${#batch_files[@]} -eq 0 ]; then
    echo "未找到批处理脚本文件"
    exit 1
fi

echo "找到 ${#batch_files[@]} 个批处理脚本"

# 创建tmux会话
session_name="abaqus_parallel_$(date +%s)"
tmux new-session -d -s "$session_name"

# 根据脚本数量创建窗格
for i in $(seq 1 $((${#batch_files[@]} - 1))); do
    if [ $i -eq 1 ] || [ $i -eq 3 ] || [ $i -eq 5 ]; then
        tmux split-window -h
    else
        tmux split-window -v
    fi
    if [ $i -gt 1 ]; then
        tmux select-pane -t $(($i - 1))
    fi
done

# 在每个窗格中运行批处理脚本
for i in "${!batch_files[@]}"; do
    echo "启动窗格 $i: ${batch_files[$i]}"
    tmux send-keys -t "$i" "cd $(pwd) && chmod +x ${batch_files[$i]} && ./${batch_files[$i]}" Enter
done

echo "所有任务已启动"
echo "使用以下命令监控进度:"
echo "  tmux attach-session -t $session_name"
echo "使用 Ctrl+B 然后 D 来分离会话"
echo "使用以下命令终止所有任务:"
echo "  tmux kill-session -t $session_name"
"""

        # 简单并行版本
        simple_script_path = os.path.join(output_dir, f"run_parallel_simple_{timestamp}.sh")
        simple_content = """#!/bin/bash
# 并行执行批处理脚本 - 简单版本
echo "启动并行计算 - 带日志监控"

# 创建日志目录
log_dir="./logs/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$log_dir"
echo "日志将保存到: $log_dir"

# 查找所有批处理脚本
batch_files=($(ls run_all_scripts_*.sh 2>/dev/null))

if [ ${#batch_files[@]} -eq 0 ]; then
    echo "未找到批处理脚本文件"
    exit 1
fi

echo "找到 ${#batch_files[@]} 个批处理脚本，开始并行执行..."

# 启动所有批处理脚本
pids=()
for i in "${!batch_files[@]}"; do
    script="${batch_files[$i]}"
    log_file="$log_dir/batch_$(($i + 1)).log"
    echo "启动 $script -> $log_file"

    chmod +x "$script"
    ./"$script" > "$log_file" 2>&1 &
    pids+=($!)
done

# 监控进度
echo ""
echo "监控任务进度 (Ctrl+C 停止监控，不会停止后台任务)..."
while true; do
    running=0
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            running=$((running + 1))
        fi
    done

    if [ $running -eq 0 ]; then
        echo "所有任务已完成！"
        break
    fi

    echo "$(date '+%H:%M:%S') - 运行中的任务: $running/${#batch_files[@]}"
    sleep 10
done

echo ""
echo "所有批处理任务已完成"
echo "日志文件位置: $log_dir"
echo "检查各任务完成情况:"
for i in "${!batch_files[@]}"; do
    log_file="$log_dir/batch_$(($i + 1)).log"
    if [ -f "$log_file" ]; then
        echo "  批次 $(($i + 1)): $(tail -n 1 "$log_file" | grep -o 'completed\\|failed\\|ERROR' || echo '进行中')"
    fi
done
"""

        # 写入脚本文件
        with open(tmux_script_path, 'w', encoding='utf-8') as f:
            f.write(tmux_content)

        with open(simple_script_path, 'w', encoding='utf-8') as f:
            f.write(simple_content)

        # 设置执行权限
        import stat
        os.chmod(tmux_script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        os.chmod(simple_script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        print(f"Linux并行脚本已生成:")
        print(f"  tmux版本: {os.path.basename(tmux_script_path)}")
        print(f"  简单版本: {os.path.basename(simple_script_path)}")

    def create_windows_parallel_script(self, output_dir, timestamp):
        """创建Windows并行执行脚本"""
        script_path = os.path.join(output_dir, f"run_parallel_{timestamp}.bat")

        content = """@echo off
setlocal enabledelayedexpansion

echo 启动并行计算 - Windows版本

rem 创建日志目录
set "log_dir=logs\\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "log_dir=%log_dir: =0%"
mkdir "%log_dir%" 2>nul
echo 日志将保存到: %log_dir%

rem 查找所有批处理脚本
set batch_count=0
for %%f in (run_all_scripts_*.bat) do (
    set /a batch_count+=1
    set "batch_file[!batch_count!]=%%f"
)

if %batch_count%==0 (
    echo 未找到批处理脚本文件
    pause
    exit /b 1
)

echo 找到 %batch_count% 个批处理脚本，开始并行执行...

rem 启动所有批处理脚本
for /l %%i in (1,1,%batch_count%) do (
    set "script=!batch_file[%%i]!"
    set "log_file=%log_dir%\\batch_%%i.log"
    echo 启动 !script! -^> !log_file!
    start "Batch_%%i" /min cmd /c "!script! > !log_file! 2>&1"
)

echo.
echo 所有任务已启动，正在监控进度...
echo 使用任务管理器可以查看 cmd.exe 进程状态
echo.

rem 简单监控（检查窗口）
:monitor
timeout /t 10 >nul
set running=0

rem 检查是否还有批处理进程在运行
tasklist /fi "windowtitle eq Batch_*" 2>nul | find /i "cmd.exe" >nul
if %errorlevel%==0 (
    echo %time% - 还有批处理任务在运行中...
    goto monitor
)

echo.
echo 所有批处理任务已完成！
echo 日志文件位置: %log_dir%
echo.
echo 检查各任务完成情况:
for /l %%i in (1,1,%batch_count%) do (
    set "log_file=%log_dir%\\batch_%%i.log"
    if exist "!log_file!" (
        echo   批次 %%i: 检查日志文件 !log_file!
    )
)

echo.
echo 按任意键退出...
pause
"""

        # 写入脚本文件
        with open(script_path, 'w', encoding='ascii', errors='ignore') as f:
            f.write(content)

        print(f"Windows并行脚本已生成: {os.path.basename(script_path)}")

    def update_button_style(self, checked):
        """Update generate button style when slider checkbox state changes"""
        if checked:
            # When checkbox is checked (slider on), set button to special continuous mode style
            if self.current_theme == "forest":
                style = """
                    #generate_button {
                        background: #d32f2f;
                        color: #ffffff;
                        border: none;
                        padding: 20px 60px;
                        font-size: 27px;
                        font-weight: 600;
                        border-radius: 25px;
                        min-width: 220px;
                        min-height: 25px;
                    }
                """
            elif self.current_theme == "sunset":
                style = """
                    #generate_button {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #ff4500, stop:1 #ff6347);
                        color: #ffffff;
                        border: 2px solid #ff1493;
                        padding: 20px 60px;
                        font-size: 27px;
                        font-weight: bold;
                        border-radius: 30px;
                        min-width: 220px;
                        min-height: 25px;
                    }
                """
            else:  # space theme
                style = """
                    #generate_button {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #e74c3c, stop:1 #c0392b);
                        color: #ecf0f1;
                        border: 2px solid #e74c3c;
                        padding: 20px 60px;
                        font-size: 27px;
                        font-weight: bold;
                        border-radius: 30px;
                        min-width: 220px;
                        min-height: 25px;
                    }
                """
            self.generate_button.setStyleSheet(style)
        else:
            # When checkbox is unchecked (slider off), restore default style
            self.generate_button.setStyleSheet("")
    
    def get_sunset_stylesheet(self):
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d1b69, stop:0.3 #4a0e4e, stop:0.7 #ff4500, stop:1 #ff6347);
            }

            #forest_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4caf50, stop:1 #2e7d32);
                border: 2px solid #e91e63;
                border-radius: 20px;
            }

            #forest_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
            }

            #forest_theme_btn[active="true"] {
                border: 3px solid #ff8a80;
            }

            #sunset_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff7043, stop:1 #8e24aa);
                border: 2px solid #ff1493;
                border-radius: 20px;
            }

            #sunset_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff8a65, stop:1 #ab47bc);
                border-color: #ff4081;
            }

            #sunset_theme_btn[active="true"] {
                border: 3px solid #ff8a80;
            }

            #space_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2c3e50);
                border: 2px solid #e91e63;
                border-radius: 20px;
            }

            #space_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5dade2, stop:1 #34495e);
            }

            #space_theme_btn[active="true"] {
                border: 3px solid #ff8a80;
            }

            #title {
                font-size: 48px;
                font-weight: bold;
                color: #fff3e0;
                padding: 30px;
                margin-bottom: 15px;
            }

            #form_frame {
                background: rgba(45, 27, 105, 0.2);
                border: 2px solid #ff7043;
                border-radius: 20px;
                padding: 40px;
                margin: 15px;
            }

            #field_label {
                font-size: 27px;
                font-weight: 600;
                color: #fff3e0;
                padding: 8px 0;
            }

            #dropdown {
                padding: 16px 20px;
                border: 2px solid #ff7043;
                border-radius: 10px;
                background: rgba(74, 14, 78, 0.8);
                font-size: 27px;
                color: #fff3e0;
                min-width: 280px;
                min-height: 20px;
            }

            #dropdown:hover {
                border-color: #ff4081;
                background: rgba(74, 14, 78, 0.9);
            }

            #dropdown QAbstractItemView {
                border: 1px solid #ff4081;
                background: #4a0e4e;
                selection-background-color: #ff7043;
                selection-color: #fff3e0;
                border-radius: 5px;
                padding: 5px;
            }

            #generate_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff7043, stop:1 #8e24aa);
                color: #fff3e0;
                border: 2px solid #ff1493;
                padding: 20px 60px;
                font-size: 27px;
                font-weight: bold;
                border-radius: 30px;
                min-width: 220px;
                min-height: 25px;
            }

            #generate_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8a65, stop:1 #ab47bc);
            }

            #checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ff7043;
                border-radius: 4px;
                background: rgba(74, 14, 78, 0.8);
            }

            #checkbox::indicator:checked {
                background: #ff4081;
                border-color: #ff1493;
            }

            #slider::groove:horizontal {
                border: none;
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a0e4e, stop:1 #2d1b69);
                border-radius: 5px;
            }

            #slider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff7043, stop:1 #8e24aa);
                border: 2px solid #fff3e0;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 13px;
            }

            #slider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff7043, stop:1 #8e24aa);
                border-radius: 5px;
            }
        """

    def get_forest_stylesheet(self):
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d5016, stop:0.5 #4a7c59, stop:1 #2d5016);
            }

            #forest_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4caf50, stop:1 #2e7d32);
                border: 2px solid #1b5e20;
                border-radius: 20px;
            }

            #forest_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
            }

            #forest_theme_btn[active="true"] {
                border: 3px solid #81c784;
            }

            #sunset_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff7043, stop:1 #8e24aa);
                border: 2px solid #6a1b9a;
                border-radius: 20px;
            }

            #sunset_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff8a65, stop:1 #ab47bc);
            }

            #sunset_theme_btn[active="true"] {
                border: 3px solid #81c784;
            }

            #space_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2c3e50);
                border: 2px solid #6a1b9a;
                border-radius: 20px;
            }

            #space_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5dade2, stop:1 #34495e);
            }

            #space_theme_btn[active="true"] {
                border: 3px solid #81c784;
            }

            #title {
                font-size: 48px;
                font-weight: bold;
                color: #e8f5e8;
                padding: 30px;
                margin-bottom: 15px;
            }

            #form_frame {
                background: rgba(46, 125, 50, 0.15);
                border: 2px solid #4caf50;
                border-radius: 20px;
                padding: 40px;
                margin: 15px;
            }

            #field_label {
                font-size: 27px;
                font-weight: 600;
                color: #e8f5e8;
                padding: 8px 0;
            }

            #dropdown {
                padding: 16px 20px;
                border: 2px solid #66bb6a;
                border-radius: 10px;
                background: rgba(27, 94, 32, 0.8);
                font-size: 27px;
                color: #e8f5e8;
                min-width: 280px;
                min-height: 20px;
            }

            #dropdown:hover {
                border-color: #4caf50;
                background: rgba(27, 94, 32, 0.9);
            }

            #dropdown QAbstractItemView {
                border: 1px solid #4caf50;
                background: #1b5e20;
                selection-background-color: #4caf50;
                selection-color: #e8f5e8;
                border-radius: 5px;
                padding: 5px;
            }

            #generate_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50, stop:1 #2e7d32);
                color: #e8f5e8;
                border: 2px solid #1b5e20;
                padding: 20px 60px;
                font-size: 27px;
                font-weight: bold;
                border-radius: 25px;
                min-width: 220px;
                min-height: 25px;
            }

            #generate_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #66bb6a, stop:1 #43a047);
            }

            #checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #66bb6a;
                border-radius: 4px;
                background: rgba(27, 94, 32, 0.8);
            }

            #checkbox::indicator:checked {
                background: #4caf50;
                border-color: #2e7d32;
            }

            #slider::groove:horizontal {
                border: none;
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1b5e20, stop:1 #2e7d32);
                border-radius: 5px;
            }

            #slider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4caf50, stop:1 #2e7d32);
                border: 2px solid #e8f5e8;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 13px;
            }

            #slider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50, stop:1 #2e7d32);
                border-radius: 5px;
            }
        """

    def get_space_stylesheet(self):
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:0.5 #34495e, stop:1 #2c3e50);
            }

            #cyberpunk_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff00ff, stop:1 #00ffff);
                border: 2px solid #7f8c8d;
                border-radius: 20px;
            }

            #cyberpunk_theme_btn:hover {
                border-color: #bdc3c7;
            }

            #cyberpunk_theme_btn[active="true"] {
                border: 3px solid #3498db;
            }

            #minimal_theme_btn {
                background: #ffffff;
                border: 2px solid #7f8c8d;
                border-radius: 20px;
            }

            #minimal_theme_btn:hover {
                border-color: #bdc3c7;
            }

            #minimal_theme_btn[active="true"] {
                border: 3px solid #3498db;
            }

            #space_theme_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2c3e50);
                border: 2px solid #3498db;
                border-radius: 20px;
            }

            #space_theme_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5dade2, stop:1 #34495e);
            }

            #space_theme_btn[active="true"] {
                border: 3px solid #ecf0f1;
            }

            QMenuBar {
                background-color: rgba(52, 73, 94, 0.9);
                color: #ecf0f1;
                border-bottom: 2px solid #3498db;
                font-size: 14px;
                font-weight: bold;
            }

            QMenuBar::item {
                background: transparent;
                padding: 8px 16px;
            }

            QMenuBar::item:selected {
                background: rgba(52, 152, 219, 0.3);
            }

            QMenu {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #3498db;
                font-size: 12px;
            }

            QMenu::item:selected {
                background-color: rgba(52, 152, 219, 0.3);
            }

            #title {
                font-size: 48px;
                font-weight: bold;
                color: #ecf0f1;
                padding: 30px;
                margin-bottom: 15px;
            }

            #form_frame {
                background: rgba(52, 73, 94, 0.8);
                border: 2px solid #3498db;
                border-radius: 20px;
                padding: 40px;
                margin: 15px;
            }

            #field_label {
                font-size: 27px;
                font-weight: 600;
                color: #ecf0f1;
                padding: 8px 0;
            }

            #dropdown {
                padding: 16px 20px;
                border: 2px solid #7f8c8d;
                border-radius: 10px;
                background: rgba(44, 62, 80, 0.9);
                font-size: 27px;
                color: #ecf0f1;
                min-width: 280px;
                min-height: 20px;
            }

            #dropdown:hover {
                border-color: #3498db;
                background: rgba(44, 62, 80, 1.0);
            }

            #dropdown QAbstractItemView {
                border: 1px solid #3498db;
                background: #2c3e50;
                selection-background-color: #3498db;
                selection-color: #ecf0f1;
                border-radius: 5px;
                padding: 5px;
            }

            #generate_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                color: #ecf0f1;
                border: 2px solid #2980b9;
                padding: 20px 60px;
                font-size: 27px;
                font-weight: bold;
                border-radius: 30px;
                min-width: 220px;
                min-height: 25px;
            }

            #generate_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5dade2, stop:1 #3498db);
            }

            #checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #7f8c8d;
                border-radius: 4px;
                background: rgba(44, 62, 80, 0.9);
            }

            #checkbox::indicator:checked {
                background: #3498db;
                border-color: #2980b9;
            }

            #slider::groove:horizontal {
                border: none;
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #34495e, stop:1 #2c3e50);
                border-radius: 5px;
            }

            #slider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: 2px solid #ecf0f1;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 13px;
            }

            #slider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 5px;
            }
        """

    def get_stylesheet(self):
        if self.current_theme == "forest":
            return self.get_forest_stylesheet()
        elif self.current_theme == "sunset":
            return self.get_sunset_stylesheet()
        elif self.current_theme == "space":
            return self.get_space_stylesheet()
        else:
            return self.get_space_stylesheet()  # 默认太空灰

    def get_original_stylesheet(self):
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            
            #title {
                font-size: 48px;
                font-weight: bold;
                color: white;
                padding: 30px;
                margin-bottom: 15px;
            }
            
            #form_frame {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                margin: 15px;
            }
            
            #field_label {
                font-size: 27px;
                font-weight: 600;
                color: #2c3e50;
                padding: 8px 0;
            }
            
            #dropdown {
                padding: 16px 20px;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background: white;
                font-size: 27px;
                color: #2c3e50;
                min-width: 280px;
                min-height: 20px;
            }
            
            #dropdown:hover {
                border-color: #3498db;
                background: #f8f9fa;
            }
            
            #dropdown:focus {
                border-color: #2980b9;
                outline: none;
            }
            
            #dropdown::drop-down {
                border: none;
                width: 30px;
            }
            
            #dropdown::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #7f8c8d;
                margin-right: 5px;
            }
            
            #dropdown QAbstractItemView {
                border: 1px solid #bdc3c7;
                background: white;
                selection-background-color: #3498db;
                selection-color: white;
                border-radius: 5px;
                padding: 5px;
            }
            
            #generate_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                padding: 20px 60px;
                font-size: 27px;
                font-weight: bold;
                border-radius: 30px;
                min-width: 220px;
                min-height: 25px;
            }
            
            #generate_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            
            #generate_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3d8b40, stop:1 #2e7031);
            }
            
            #generate_button:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }

            #checkbox {
                spacing: 8px;
                min-width: 20px;
                min-height: 20px;
            }

            #checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background: white;
            }

            #checkbox::indicator:hover {
                border-color: #3498db;
            }

            #checkbox::indicator:checked {
                background: #3498db;
                border-color: #2980b9;
                image: none;
            }

            #checkbox::indicator:checked:hover {
                background: #2980b9;
            }

            #slider {
                min-height: 30px;
                min-width: 280px;
                background: transparent;
            }

            /* Normal state - 浅紫色主题，无边框 */
            #slider::groove:horizontal {
                border: none;
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f3e5f5, stop:1 #e1bee7);
                border-radius: 5px;
            }

            #slider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ce93d8, stop:1 #ba68c8);
                border: none;
                width: 22px;
                height: 22px;
                margin: -8px 0;
                border-radius: 13px;
            }

            #slider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ba68c8, stop:1 #ab47bc);
            }

            #slider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a1b9a, stop:1 #4a148c);
            }

            #slider:focus::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6a1b9a, stop:1 #4a148c);
            }

            #slider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ce93d8, stop:1 #ba68c8);
                border-radius: 5px;
            }

            #slider:focus::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e24aa, stop:1 #6a1b9a);
                border-radius: 5px;
            }

            /* Disabled state - 完全灰色主题 */
            #slider:disabled {
                opacity: 0.7;
            }

            #slider:disabled::groove:horizontal {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
                color: #7f8c8d;
            }

            #slider:disabled::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
                border: none;
            }

            #slider:disabled::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
            }

            #slider:disabled::add-page:horizontal {
                background: #ecf0f1;
            }
        """


if __name__ == "__main__":
    pass