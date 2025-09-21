import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from structure_set import get_crystal_structure


class CellVisualizationWidget(QWidget):
    """3D visualization widget for displaying cell structure sketches"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 8), dpi=80)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Set up the 3D plot
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.setup_plot_style()

        # Store current cell type to detect changes
        self.current_cell_type = None
        # Store viewing angle
        self.saved_view_angle = None



    def setup_plot_style(self):
        """Configure the 3D plot appearance"""
        self.ax.set_facecolor('white')
        self.figure.patch.set_facecolor('white')

        # Remove axes for cleaner look
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_zticks([])

        # Set equal aspect ratio
        self.ax.set_xlabel('')
        self.ax.set_ylabel('')
        self.ax.set_zlabel('')

        # Initial view angle (only set once at startup)
        # self.ax.view_init(elev=20, azim=135)

    def parse_structure_from_set(self, cell_type, slider_value=4):
        """Parse structure data from structure_set.py"""
        try:
            # 获取结构数据字符串，传入slider值
            structure_data = get_crystal_structure(cell_type, slider_value)

            if "结构" in structure_data and "不存在" in structure_data:
                return None, None

            # 解析坐标
            points = []
            point_names = {}
            lines = structure_data.split('\n')

            # 提取坐标定义
            for line in lines:
                if '=' in line and '[' in line and ']' in line:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        name = parts[0].strip()
                        coord_str = parts[1].strip().strip('[]')
                        try:
                            coords = [float(x.strip()) for x in coord_str.split(',')]
                            if len(coords) == 3:
                                points.append(coords)
                                point_names[name] = len(points) - 1
                        except:
                            continue

            # 提取连接关系
            connections = []
            in_cylinders = False
            for line in lines:
                line = line.strip()
                if 'cylinders = [' in line:
                    in_cylinders = True
                    continue
                elif in_cylinders and ']' in line and '(' not in line:
                    break
                elif in_cylinders and '(' in line and ')' in line:
                    # 提取连接对
                    start = line.find('(')
                    end = line.find(')')
                    if start != -1 and end != -1:
                        pair_str = line[start+1:end]
                        parts = [p.strip() for p in pair_str.split(',')]
                        if len(parts) == 2:
                            point1, point2 = parts
                            if point1 in point_names and point2 in point_names:
                                connections.append([point_names[point1], point_names[point2]])

            if points and connections:
                return np.array(points), connections
            else:
                return None, None

        except Exception as e:
            print(f"Error parsing structure {cell_type}: {e}")
            return None, None

    def get_cell_structure(self, cell_type, slider_value=4):
        """Generate points and connections for different cell types"""

        # 首先尝试从structure_set动态获取
        points, connections = self.parse_structure_from_set(cell_type, slider_value)
        if points is not None and connections is not None:
            return points, connections

        # 如果structure_set中没有找到，使用默认的立方体结构
        if cell_type == "Cubic" or points is None:
            # 立方体结构 - 8个顶点
            points = np.array([
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # 底面
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # 顶面
            ])
            # 立方体的12条边
            connections = [
                [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
                [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
                [0, 4], [1, 5], [2, 6], [3, 7]   # 垂直边
            ]

        return points, connections

    def update_visualization(self, cell_type, slider_value=4, reset_view_angle=True):
        """Update the 3D visualization based on cell type and slider value"""
        # Check if cell type has changed
        cell_type_changed = (self.current_cell_type != cell_type)

        # Save current viewing angle if we're not resetting view
        if not reset_view_angle:
            try:
                # Get current view angles before clearing
                elev = self.ax.elev
                azim = self.ax.azim
                self.saved_view_angle = (elev, azim)
            except:
                # If we can't get angles, use default
                self.saved_view_angle = (20, 135)
        
        self.ax.clear() 
        self.setup_plot_style()

        # Get structure data
        points, connections = self.get_cell_structure(cell_type, slider_value)

        # Swap Y and Z coordinates for display
        display_points = points.copy()
        display_points[:, [1, 2]] = display_points[:, [2, 1]]  # Swap Y and Z columns

        # Plot points with swapped coordinates
        self.ax.scatter(display_points[:, 0], display_points[:, 1], display_points[:, 2],
                       c='red', s=60, alpha=0.8, edgecolors='black', linewidth=1)

        # Plot connections with swapped coordinates
        for connection in connections:
            start_point = display_points[connection[0]]
            end_point = display_points[connection[1]]

            self.ax.plot([start_point[0], end_point[0]],
                        [start_point[1], end_point[1]],
                        [start_point[2], end_point[2]],
                        'b-', linewidth=2, alpha=0.7)

        # Set equal aspect ratio and limits using display coordinates
        if len(display_points) > 0:
            x_range = np.max(display_points[:, 0]) - np.min(display_points[:, 0])
            y_range = np.max(display_points[:, 1]) - np.min(display_points[:, 1])
            z_range = np.max(display_points[:, 2]) - np.min(display_points[:, 2])
            max_range = max(x_range, y_range, z_range)

            if max_range == 0:
                max_range = 1

            center = (np.max(display_points, axis=0) + np.min(display_points, axis=0)) / 2

            # Add some padding to ensure nothing is truncated
            padding = max_range * 0.2

            self.ax.set_xlim(center[0] - max_range/2 - padding, center[0] + max_range/2 + padding)
            self.ax.set_ylim(center[1] - max_range/2 - padding, center[1] + max_range/2 + padding)
            self.ax.set_zlim(center[2] - max_range/2 - padding, center[2] + max_range/2 + padding)

        # Add title
        self.ax.set_title(f'{cell_type} Structure', fontsize=12, fontweight='bold')

        # Restore view angle based on reset_view_angle parameter
        if not reset_view_angle:
            # Preserve user's current view angle
            if hasattr(self, 'saved_view_angle') and self.saved_view_angle:
                self.ax.view_init(elev=self.saved_view_angle[0], azim=self.saved_view_angle[1])
            # If no saved angle, don't set any view - keep current
        else:
            # Reset to default view angle
            self.ax.view_init(elev=20, azim=135)

        # Update current cell type
        self.current_cell_type = cell_type

        # Use tight layout to prevent truncation
        self.figure.tight_layout()

        # Refresh the canvas
        self.canvas.draw()