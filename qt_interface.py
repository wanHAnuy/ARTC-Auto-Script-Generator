import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                           QWidget, QComboBox, QLabel, QPushButton, QFrame, QGridLayout, QSplitter, QCheckBox, QSlider, QMenuBar, QAction, QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QIcon, QPixmap
from visualization_widget import CellVisualizationWidget
from script_generator import generate_abaqus_script
from config import Config
# 导入批量管理器
try:
    from batch_manager import BatchJobManager
except ImportError:
    BatchJobManager = None
# 避免循环导入，在需要时动态导入


class ModernInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Generator")

        # # 检测操作系统并设置适当的窗口大小
        # import platform
        # if platform.system() == "Linux":
        #     # Linux系统缩小50%
        #     self.setGeometry(100, 100, 750, 400)
        # else:
        #     # Windows和其他系统保持原尺寸
        self.setGeometry(100, 100, 1500, 800)
        # 设置窗口图标
        self.set_window_icon()

        # 主题设置
        self.current_theme = "space"  # 默认太空灰主题

        # 设置文件路径
        self.settings_file = os.path.join(os.path.dirname(__file__), "ui_settings.json")

        # 初始化批量管理器
        self.batch_manager = BatchJobManager() if BatchJobManager else None

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
            ("Speed:", ["50", "500"]),
            ("Directions:", ["X", "X_50","X_500"]),
            ("Cell size:", ["4", "5", "6"]),
            ("Strut radius:", ["0.5", "0.4", "0.3"])
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
                "slider_values": getattr(self, 'slider_values', {}),
                "batch_enabled": getattr(self, 'batch_checkbox', None) and self.batch_checkbox.isChecked() if hasattr(self, 'batch_checkbox') else False,
                "batch_config": getattr(self, 'batch_config', {})
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


            # 恢复批量设置
            if "batch_enabled" in settings and hasattr(self, 'batch_checkbox') and self.batch_checkbox:
                self.batch_checkbox.setChecked(settings["batch_enabled"])
                if hasattr(self, 'batch_config_button') and self.batch_config_button:
                    self.batch_config_button.setEnabled(settings["batch_enabled"])

            if "batch_config" in settings:
                self.batch_config = settings["batch_config"]

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
        """单次生成配置"""
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
            get_generated_files = main.get_generated_files
            from shell_script_generator import generate_shell_script
            from config import Config
            from datetime import datetime
        except ImportError as e:
            print(f"无法导入必要模块: {e}")
            return

        # 使用配置文件中的分组和设置
        cell_type_groups = Config.CELL_TYPE_GROUPS
        no_slider_types = Config.NO_SLIDER_CELL_TYPES

        try:
            # 禁用按钮防止重复点击，并设置运行状态样式
            self.triangle_button.setEnabled(False)
            # 设置深红色运行状态
            running_style = """
                #triangle_button {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #8b0000, stop:0.5 #660000, stop:1 #440000);
                    color: white;
                    border: 2px solid #660000;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: center;
                }
            """
            self.triangle_button.setStyleSheet(running_style)

            # 创建带时间戳的任务文件夹
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            generate_script_root = os.path.join(os.path.dirname(__file__), "generate_script")
            task_dir = os.path.join(generate_script_root, f"task_{timestamp}")
            os.makedirs(task_dir, exist_ok=True)
            print(f"创建任务文件夹: {task_dir}")

            # 保存任务目录供后续使用
            self.current_task_dir = task_dir

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
                        # 生成3个脚本 (slider值 0-2)
                        for slider_value in range(9):
                            self._generate_single_script(cell_type, slider_value)

                # 生成当前组的批处理脚本到task文件夹
                python_files = get_generated_files()
                if python_files:
                    print(f"{group_name} 共生成 {len(python_files)} 个脚本文件")

                    # 获取配置参数用于命名
                    cell_size = self.dropdowns.get("Cell size:", None)
                    strut_radius = self.dropdowns.get("Strut radius:", None)
                    speed_checkbox = self.checkboxes.get("Speed:", None)
                    direction_checkbox = self.checkboxes.get("Directions:", None)

                    config_parts = []
                    if cell_size:
                        config_parts.append(cell_size.currentText())
                    if strut_radius:
                        config_parts.append(strut_radius.currentText())

                    # 判断是static/speed/direction
                    if speed_checkbox and speed_checkbox.isChecked():
                        if direction_checkbox and direction_checkbox.isChecked():
                            config_parts.append("dir")
                        else:
                            config_parts.append("speed")
                    else:
                        config_parts.append("static")

                    config_name = "_".join(config_parts)

                    # 使用task文件夹作为输出目录
                    import platform
                    if platform.system() == "Windows":
                        generate_shell_script(python_files, task_dir, "bat", config_name=config_name)
                    else:
                        # Linux系统只生成.sh文件，不生成.bat文件
                        generate_shell_script(python_files, task_dir, "sh", config_name=config_name)

                    print(f"{group_name} 批处理脚本生成完成")
                else:
                    print(f"警告: {group_name} 未生成任何脚本文件")

            print("\n=== 所有批处理脚本生成完成! ===")

            # 生成主控制脚本到task文件夹
            self.generate_master_control_script()

            # 生成PBS脚本到task文件夹
            self.generate_pbs_script()

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

                
                    # self.slider_label.setStyleSheet("color: #fffff; font-size: 27px; font-weight: 600; padding: 8px 0;")

                # Store current cell type for next time
                self.previous_cell_type = cell_type

    def create_batch_controls(self, form_layout, start_row):

        # 批量生成选项
        batch_label = QLabel("Batch Mode:")
        batch_label.setObjectName("input_label")

        self.batch_checkbox = QCheckBox()
        self.batch_checkbox.setObjectName("batch_checkbox")
        self.batch_checkbox.toggled.connect(self.on_batch_toggle)

        # 批量配置按钮
        self.batch_config_button = QPushButton("Batch Config")
        self.batch_config_button.setObjectName("batch_config_button")
        self.batch_config_button.clicked.connect(self.show_batch_config)
        self.batch_config_button.setEnabled(False)

        form_layout.addWidget(batch_label, start_row + 1, 0)
        form_layout.addWidget(self.batch_config_button, start_row + 1, 1)
        form_layout.addWidget(self.batch_checkbox, start_row + 1, 2)

        return start_row + 2


    def on_batch_toggle(self, checked):
        """批量模式切换处理"""
        self.batch_config_button.setEnabled(checked)

        if checked:
            print("批量模式已启用")
        else:
            print("批量模式已禁用")


    def show_batch_config(self):
        """显示批量配置对话框"""
        try:
            from batch_config_dialog import BatchConfigDialog

            if not hasattr(self, 'batch_config'):
                self.batch_config = {}

            dialog = BatchConfigDialog(self.batch_config, self)
            if dialog.exec_() == dialog.Accepted:
                self.batch_config = dialog.get_config()
                print("批量配置已更新:", self.batch_config)
        except ImportError:
            # 如果没有配置对话框，显示简单的消息
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "批量配置",
                                  "批量配置功能需要额外的配置对话框模块。\n请手动设置参数组合。")

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
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #66bb6a, stop:0.5 #43a047, stop:1 #2e7d32);
                    border: 2px solid #81c784;
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2e7d32, stop:0.5 #1b5e20, stop:1 #0d4b0b);
                    border: 2px solid #4caf50;
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
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ff6666, stop:0.5 #dd2222, stop:1 #aa1111);
                    border: 2px solid #ff8888;
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #cc2222, stop:0.5 #990000, stop:1 #660000);
                    border: 2px solid #cc4444;
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
                }
                #triangle_button:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #5dade2, stop:0.5 #3498db, stop:1 #2980b9);
                    border: 2px solid #85c1e9;
                }
                #triangle_button:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2980b9, stop:0.5 #1f5f8a, stop:1 #154d6b);
                    border: 2px solid #3498db;
                }
            """

        self.triangle_button.setStyleSheet(style)

    def show_completion_star(self):
        """显示完成图标特效"""
        # 不显示图片，只显示✓符号
        self.triangle_button.setText("✓")

        # 设置完成样式
        star_style = """
            #triangle_button {
                background: qlinear-gradient(45deg, #ffd700, #ffed4e, #ffd700);
                color: #333;
                border: 3px solid #ffd700;
                border-radius: 30px;
                font-size: 32px;
                font-weight: bold;
                text-align: center;
            }
        """
        self.triangle_button.setStyleSheet(star_style)

        # 3秒后恢复正常样式
        QTimer.singleShot(3000, self.restore_triangle_button_style)

    def restore_triangle_button_style(self):
        """恢复三角按钮正常样式"""
        self.triangle_button.setText("")
        self.triangle_button.setIcon(QIcon())  # 清除图标
        self.update_triangle_button_style()

    def generate_master_control_script(self):
        """生成主控制脚本用于并行计算"""
        try:
            from datetime import datetime
            import glob

            # 使用task文件夹作为输出目录
            if not hasattr(self, 'current_task_dir'):
                print("错误: 未找到任务文件夹")
                return

            output_dir = self.current_task_dir
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 查找所有生成的批处理脚本
            script_pattern = os.path.join(output_dir, "run_all_scripts_*_*.sh")
            batch_scripts = glob.glob(script_pattern)
            batch_scripts.sort()  # 按文件名排序

            if not batch_scripts:
                print("未找到批处理脚本文件，请先运行triangle_button生成脚本")
                return

            # 生成主控制脚本
            master_script_name = f"master_control_{timestamp}.sh"
            master_script_path = os.path.join(output_dir, master_script_name)

            # 创建主控制脚本内容
            script_content = [
                "#!/bin/bash",
                "# 主控制脚本 - 并行执行批处理脚本（许可证优化版本）",
                f"# 自动生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "# 显示Logo",
                "clear",
                'echo "================================================================="',
                'echo "     _____ _____ ____  _____ ____  _______   ____ _____  _   _ "',
                'echo "    |  ___| ____/ ___||_   _|  _ \\|  ___\\ \\ / /  ___|| \\ | |"',
                'echo "    | |_  | |__ \\___ \\  | | | |_) | |_   \\ V /| |__  |  \\| |"',
                'echo "    |  _| |  __| ___) | | | |  _ <|  _|   | | |  __| | . \\` |"',
                'echo "    |_|   |____||____/  |_| |_| \\_\\_|     |_| |____||_|\\  |_|"',
                'echo "                                                              "',
                'echo "            Smart Generator - License Optimized Parallel     "',
                'echo "================================================================="',
                'echo "启动并行计算 - 许可证优化版本"',
                "",
                "# 确保在正确的目录中执行",
                'script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
                'cd "$script_dir"',
                'echo "执行目录: $script_dir"',
                "",
                "# Abaqus环境设置 - 根据需要取消注释",
                "# module load abaqus",
                "",
                "# 创建错误日志目录",
                'log_dir="./logs"',
                'mkdir -p "$log_dir"',
                'echo "错误日志将保存到: $log_dir"',
                "",
                "# 批处理脚本列表"
            ]

            # 添加脚本文件列表
            script_content.append("batch_files=(")
            for script in batch_scripts:
                script_name = os.path.basename(script)
                script_content.append(f'    "{script_name}"')
            script_content.append(")")

            script_content.extend([
                "",
                'if [ ${#batch_files[@]} -eq 0 ]; then',
                '    echo "未找到批处理脚本文件"',
                '    exit 1',
                'fi',
                "",
                'echo "找到 ${#batch_files[@]} 个批处理脚本，开始并行执行（许可证优化）..."',
                "",
                "# 启动所有批处理脚本（添加延迟和进程隔离）",
                "pids=()",
                'for i in "${!batch_files[@]}"; do',
                '    script="${batch_files[$i]}"',
                '    log_file="$log_dir/group$(($i + 1))_errors.log"',
                '    echo "启动 $script -> $log_file (延迟 $((i * 10)) 秒)"',
                "",
                '    chmod +x "$script"',
                '    # 错峰启动避免许可证冲突',
                '    sleep $((i * 10))',
                '    # 使用setsid创建独立进程组，模拟独立终端',
                '    setsid ./"$script" > "$log_file" 2>&1 &',
                '    pids+=($!)',
                'done',
                "",
                "# 监控进度",
                'echo ""',
                'echo "监控任务进度 (Ctrl+C 停止监控，不会停止后台任务)..."',
                'echo "按 \'l\' 查看实时日志，按 \'q\' 退出日志查看"',
                'echo ""'
            ])

            # 添加与原脚本相同的监控函数
            script_content.extend([
                "",
                "# 事件驱动监控函数",
                "monitor_progress() {",
                "    local last_check_time=$(date +%s)",
                "    declare -A last_log_sizes",
                "",
                "    # 初始化日志文件大小记录",
                '    for i in "${!batch_files[@]}"; do',
                '        log_file="$log_dir/group$(($i + 1))_errors.log"',
                '        if [ -f "$log_file" ]; then',
                '            last_log_sizes[$i]=$(wc -c < "$log_file" 2>/dev/null || echo 0)',
                "        else",
                "            last_log_sizes[$i]=0",
                "        fi",
                "    done",
                "",
                "    while true; do",
                "        running=0",
                "        has_changes=false",
                "        current_time=$(date +%s)",
                "",
                "        # 检查是否有日志文件变化或足够时间过去（最少3秒强制刷新一次）",
                '        for i in "${!batch_files[@]}"; do',
                '            log_file="$log_dir/group$(($i + 1))_errors.log"',
                '            if [ -f "$log_file" ]; then',
                '                current_size=$(wc -c < "$log_file" 2>/dev/null || echo 0)',
                '                if [ "$current_size" != "${last_log_sizes[$i]}" ]; then',
                "                    has_changes=true",
                "                    last_log_sizes[$i]=$current_size",
                "                fi",
                "            fi",
                "        done",
                "",
                "        # 检查进程状态",
                '        for pid in "${pids[@]}"; do',
                '            if kill -0 "$pid" 2>/dev/null; then',
                "                running=$((running + 1))",
                "            fi",
                "        done",
                "",
                "        if [ $running -eq 0 ]; then",
                '            echo "$(date \'+%H:%M:%S\') - 所有任务已完成！"',
                "            break",
                "        fi",
                "",
                "        # 只有当有变化或超过强制刷新间隔时才显示状态",
                '        if [ "$has_changes" = true ] || [ $((current_time - last_check_time)) -ge 30 ]; then',
                "            last_check_time=$current_time",
                "",
                "            # 显示各任务详细状态",
                '            echo "$(date \'+%H:%M:%S\') - 任务状态更新:"',
                '            for i in "${!batch_files[@]}"; do',
                '                script="${batch_files[$i]}"',
                '                log_file="$log_dir/group$(($i + 1))_errors.log"',
                '                pid="${pids[$i]}"',
                "",
                '                if kill -0 "$pid" 2>/dev/null; then',
                '                    status="运行中"',
                '                    if command -v ps >/dev/null 2>&1; then',
                '                        runtime=$(ps -p $pid -o etime= 2>/dev/null | tr -d \' \' || echo "未知")',
                '                        resource_info="(运行时间:${runtime})"',
                "                    else",
                '                        resource_info=""',
                "                    fi",
                '                    if [ -f "$log_file" ]; then',
                '                        latest_logs=$(tail -n 3 "$log_file" 2>/dev/null | tr \'\\n\' \' | \' | sed \'s/ | $//\')',
                '                        if [ -n "$latest_logs" ]; then',
                '                            log_info="$latest_logs"',
                "                        else",
                '                            log_info="日志: 生成中..."',
                "                        fi",
                "                    else",
                '                        log_info="日志: 等待中..."',
                "                    fi",
                "                else",
                '                    status="已完成"',
                '                    resource_info=""',
                '                    if [ -f "$log_file" ]; then',
                '                        if grep -q "SUCCESS:" "$log_file" 2>/dev/null; then',
                '                            success_count=$(grep -c "SUCCESS:" "$log_file" 2>/dev/null)',
                '                            log_info="| 状态: 成功完成 (${success_count}个脚本)"',
                '                        elif grep -q "FAILED:" "$log_file" 2>/dev/null; then',
                '                            failed_count=$(grep -c "FAILED:" "$log_file" 2>/dev/null)',
                '                            log_info="| 状态: 发现失败 (${failed_count}个脚本)"',
                '                        elif grep -q "PARTIAL:" "$log_file" 2>/dev/null; then',
                '                            partial_count=$(grep -c "PARTIAL:" "$log_file" 2>/dev/null)',
                '                            log_info="| 状态: 部分完成 (${partial_count}个脚本数据不足)"',
                "                        else",
                '                            log_info="| 状态: 运行中或已结束"',
                "                        fi",
                "                    else",
                '                        log_info="| 状态: 无日志"',
                "                    fi",
                "                fi",
                "",
                '                echo "  Group $(($i + 1)): $status $resource_info"',
                '                if [ -n "$log_info" ]; then',
                '                    echo "       $log_info"',
                "                fi",
                '                echo ""',
                "            done",
                "",
                '            completion_percent=$(( (${#batch_files[@]} - running) * 100 / ${#batch_files[@]} ))',
                '            echo "进度: ${completion_percent}% (运行中: $running/${#batch_files[@]})"',
                '            echo "----------------------------------------"',
                "        fi",
                "",
                "        # 短暂等待以降低CPU使用率",
                "        sleep 1",
                "    done",
                "}",
                "",
                "# 启动监控",
                "monitor_progress",
                "",
                'echo ""',
                'echo "所有批处理任务已完成"',
                'echo "日志文件位置: $log_dir"',
                "",
                "# 生成并行执行总结报告",
                'summary_file="$log_dir/parallel_summary.log"',
                'echo "Parallel Execution Summary Report (License Optimized)" > "$summary_file"',
                'echo "=====================================================" >> "$summary_file"',
                'echo "Execution completed at: $(date)" >> "$summary_file"',
                'echo "Total parallel batches: ${#batch_files[@]}" >> "$summary_file"',
                'echo "License optimization: Staggered start + Process isolation" >> "$summary_file"',
                'echo "Log directory: $log_dir" >> "$summary_file"',
                'echo "" >> "$summary_file"',
                "",
                'echo "检查各任务完成情况:"',
                "completed_count=0",
                "error_count=0",
                'for i in "${!batch_files[@]}"; do',
                '    log_file="$log_dir/group$(($i + 1))_errors.log"',
                "    batch_num=$(($i + 1))",
                "",
                '    if [ -f "$log_file" ]; then',
                '        if grep -q "SUCCESS:" "$log_file" 2>/dev/null; then',
                "            completed_count=$((completed_count + 1))",
                '            success_count=$(grep -c "SUCCESS:" "$log_file" 2>/dev/null)',
                '            echo "  Group $batch_num: 成功完成 (${success_count}个脚本) - 日志: $log_file"',
                '            echo "Group $batch_num: SUCCESS" >> "$summary_file"',
                '        elif grep -q "FAILED:" "$log_file" 2>/dev/null; then',
                "            error_count=$((error_count + 1))",
                '            failed_count=$(grep -c "FAILED:" "$log_file" 2>/dev/null)',
                '            echo "  Group $batch_num: 发现失败 (${failed_count}个脚本) - 日志: $log_file"',
                '            echo "Group $batch_num: ERROR" >> "$summary_file"',
                "        else",
                '            echo "  Group $batch_num: 状态未知 - 日志: $log_file"',
                '            echo "Group $batch_num: UNKNOWN" >> "$summary_file"',
                "        fi",
                "    else",
                '        echo "  Group $batch_num: 无日志文件"',
                '        echo "Group $batch_num: NO_LOG" >> "$summary_file"',
                "    fi",
                "done",
                "",
                'echo "" >> "$summary_file"',
                'echo "Summary:" >> "$summary_file"',
                'echo "  Completed: $completed_count" >> "$summary_file"',
                'echo "  Errors: $error_count" >> "$summary_file"',
                'echo "  Total: ${#batch_files[@]}" >> "$summary_file"',
                "",
                'echo ""',
                'echo "总结: 成功=$completed_count, 错误=$error_count, 总计=${#batch_files[@]}"',
                'echo "详细报告已保存到: $summary_file"'
            ])

            # 写入主控制脚本文件
            with open(master_script_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(script_content))

            # 设置执行权限
            import stat
            os.chmod(master_script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

            print(f"主控制脚本已生成: {master_script_path}")
            print(f"找到 {len(batch_scripts)} 个批处理脚本:")
            for i, script in enumerate(batch_scripts):
                print(f"  Group {i+1}: {os.path.basename(script)}")
            print(f"\n执行命令: ./{master_script_name}")
            print("特性: 错峰启动(10秒间隔) + 进程隔离，确保许可证使用受控")

        except Exception as e:
            print(f"生成主控制脚本时出错: {str(e)}")

    def generate_pbs_script(self):
        """生成PBS脚本文件"""
        try:
            from datetime import datetime
            import glob

            # 使用task文件夹作为输出目录
            if not hasattr(self, 'current_task_dir'):
                print("错误: 未找到任务文件夹")
                return

            output_dir = self.current_task_dir
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 查找最新生成的run_all脚本
            run_all_pattern = os.path.join(output_dir, "run_all_*.sh")
            run_all_scripts = glob.glob(run_all_pattern)

            if not run_all_scripts:
                print("未找到run_all脚本文件，无法生成PBS脚本")
                return

            # 选择最新的run_all脚本
            run_all_scripts.sort()
            latest_run_all_script = run_all_scripts[-1]
            run_all_script_name = os.path.basename(latest_run_all_script)

            # 生成PBS脚本名称 (使用run_all脚本的配置名称)
            config_name = run_all_script_name.replace("run_all_", "").replace(".sh", "")
            pbs_script_name = f"pbs_submit_{config_name}.pbs"
            pbs_script_path = os.path.join(output_dir, pbs_script_name)

            # 获取task文件夹的名称(例如: task_20250930_123456)
            task_folder_name = os.path.basename(output_dir)

            # 获取generate_script的绝对路径
            generate_script_dir = os.path.dirname(output_dir)

            # 创建logs目录
            logs_dir = os.path.join(output_dir, "logs")
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
                print(f"已创建日志目录: {logs_dir}")

            # 创建PBS脚本内容
            pbs_content = [
                "#!/bin/bash",
                f"#PBS -N abaqus_{config_name}",
                "#PBS -P as_mae_kzhou",
                "#PBS -q qintel_wfly",
                "#PBS -l walltime=168:00:00",
                "#PBS -l select=1:ncpus=8:mem=64gb",
                "#PBS -j oe",
                f"#PBS -o {Config.BASE_SCRIPT_PATH}/{task_folder_name}/logs/run_all_{config_name}.log",
                "",
                "cd $PBS_O_WORKDIR",
                "",
                "# Setup real-time logging",
                f"LOGDIR=\"{Config.BASE_SCRIPT_PATH}/{task_folder_name}/logs\"",
                "mkdir -p $LOGDIR",
                f"REALTIME_LOG=\"$LOGDIR/realtime_{config_name}_$PBS_JOBID.log\"",
                "",
                "# Execute with real-time output",
                f'bash "{Config.BASE_SCRIPT_PATH}/{task_folder_name}/{run_all_script_name}" 2>&1 | tee "$REALTIME_LOG" &',
                "wait",
                'echo "Abaqus tasks finished."'
            ]

            # 写入PBS脚本文件
            with open(pbs_script_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(pbs_content))

            # 设置执行权限
            import stat
            os.chmod(pbs_script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

            print(f"PBS脚本已生成: {pbs_script_path}")
            print(f"关联的run_all脚本: {run_all_script_name}")
            print(f"提交命令: qsub {pbs_script_name}")

        except Exception as e:
            print(f"生成PBS脚本时出错: {str(e)}")



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

            #batch_config_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff7043, stop:1 #8e24aa);
                color: #fce4ec;
                border: 2px solid #6a1b9a;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: normal;
                font-size: 11px;
                min-width: 80px;
                max-height: 24px;
            }

            #batch_config_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8a65, stop:1 #ab47bc);
                border-color: #8e24aa;
            }

            #batch_config_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e64a19, stop:1 #6a1b9a);
            }

            #batch_config_button:disabled {
                background: #757575;
                color: #bdbdbd;
                border-color: #424242;
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

            #batch_config_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4caf50, stop:1 #2e7d32);
                color: #e8f5e8;
                border: 2px solid #1b5e20;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: normal;
                font-size: 11px;
                min-width: 80px;
                max-height: 24px;
            }

            #batch_config_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
                border-color: #2e7d32;
            }

            #batch_config_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #388e3c, stop:1 #1b5e20);
            }

            #batch_config_button:disabled {
                background: #757575;
                color: #bdbdbd;
                border-color: #424242;
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

            #batch_config_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2c3e50);
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: normal;
                font-size: 11px;
                min-width: 80px;
                max-height: 24px;
            }

            #batch_config_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #34495e);
                border-color: #3498db;
            }

            #batch_config_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #2c3e50);
            }

            #batch_config_button:disabled {
                background: #757575;
                color: #bdbdbd;
                border-color: #424242;
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
            height: 25px;
            background: transparent;
        }

        #slider::groove:horizontal {
            border: none;
            height: 8px;
            background: rgba(255, 255, 255, 100);
            border-radius: 4px;
        }

        #slider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:1 #e0e0e0);
            border: 2px solid #cccccc;
            width: 20px;
            height: 20px;
            margin: -8px 0;
            border-radius: 12px;
        }

        #slider::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f0f0f0, stop:1 #d0d0d0);
            border: 2px solid #aaaaaa;
        }

        #slider::handle:horizontal:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #e0e0e0, stop:1 #c0c0c0);
            border: 2px solid #888888;
        }

        #slider::sub-page:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #9c27b0, stop:1 #7b1fa2);
            border-radius: 4px;
        }

        #slider::add-page:horizontal {
            background: rgba(255, 255, 255, 100);
            border-radius: 4px;
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
            background: rgba(189, 195, 199, 100);
            border-radius: 4px;
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