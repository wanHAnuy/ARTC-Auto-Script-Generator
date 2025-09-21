"""
Abaqus Script Generator
根据UI参数生成定制化的Abaqus脚本
"""

import os
import sys
import re
from structure_set import get_crystal_structure
# from macro_integration import MacroIntegrator


class AbaqusScriptGenerator:
    def __init__(self):
        self.base_template_file_static = 'strut_FCCZ_static.py'
        self.base_template_file_dynamic = 'strut_FCCZ_Dynamic.py'
        self.base_template_file_direction = 'strut_FCCZ_direction.py'
        self.base_cell_size = 5.0  # 原始模板的单元尺寸
        # self.macro_integrator = MacroIntegrator()  # 宏集成器

    def generate_script(self, cell_type, cell_size, cell_radius, slider=4, output_dir=None, speed_value=None, direction_value=None, batch_mode=False, batch_parent_dir=None):
        """
        生成定制化的Abaqus脚本

        参数:
        - cell_type: 晶体结构类型 (如 'BCC', 'FCC', 'FCCZ' 等)
        - cell_size: 单元尺寸 (如 3, 4, 5)
        - cell_radius: 杆件半径 (如 0.3, 0.4, 0.5)
        - slider: 滑块值 (0-8)，用于控制BCC/BCCZ结构中O原子的位置
        - output_dir: 输出目录
        - speed_value: 速度值 (当Speed复选框选中时)
        - direction_value: 方向值 (当Direction复选框选中时)
        - batch_mode: 是否为批量模式
        - batch_parent_dir: 批量模式的父文件夹路径

        返回:
        - (success: bool, message: str, filename: str)
        """

        try:
            # 统一的文件夹创建逻辑
            output_dir = self._create_output_directory(cell_type, cell_size, cell_radius, slider, speed_value, direction_value, batch_mode, batch_parent_dir, output_dir)

            # 设置当前结构名称，用于结构感知检测
            self._current_structure_name = cell_type

            # 1. 验证参数
            if not self._validate_parameters(cell_type, cell_size, cell_radius):
                return False, "参数验证失败", ""

            # 2. 读取基础模板
            template_content = self._read_template(speed_value, direction_value)
            if not template_content:
                return False, "无法读取模板文件", ""

            # 3. 获取结构几何定义
            structure_data = self._get_structure_data(cell_type, slider)
            if not structure_data:
                return False, f"不支持的结构类型: {cell_type}", ""

            # 4. 生成脚本内容
            script_content = self._generate_script_content(
                template_content, structure_data, cell_size, cell_radius, slider, speed_value, direction_value, output_dir
            )

            # 5. 生成文件名和保存
            filename = self._generate_filename(cell_type, cell_size, cell_radius, slider, speed_value, direction_value)
            filepath = os.path.join(output_dir, filename)

            # 使用UTF-8编码并添加BOM以确保兼容性
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write(script_content)

            return True, f"脚本生成成功: {filename}", filename

        except Exception as e:
            return False, f"生成脚本时出错: {str(e)}", ""

    def _create_output_directory(self, cell_type, cell_size, cell_radius, slider, speed_value, direction_value, batch_mode, batch_parent_dir, output_dir):
        """
        统一的文件夹创建逻辑 - 层级结构
        创建层级结构: clean_cell_type -> clean_cell_type_suffix -> clean_cell_type_size_suffix -> clean_cell_type_size_radius_suffix -> clean_cell_type_size_radius_slider_suffix
        """
        # 获取基础目录
        if batch_mode and batch_parent_dir:
            base_output_dir = batch_parent_dir
        else:
            if output_dir is None:
                if getattr(sys, 'frozen', False):
                    # 打包环境：获取可执行文件所在目录
                    current_dir = os.path.dirname(sys.executable)
                else:
                    # 开发环境：获取脚本文件所在目录
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                base_output_dir = os.path.join(current_dir, "generate_script")
            else:
                base_output_dir = output_dir

        # 构建层级路径
        target_output_dir = self._build_hierarchical_path(base_output_dir, cell_type, cell_size, cell_radius, slider, speed_value, direction_value)

        # 确保目录存在
        if not os.path.exists(target_output_dir):
            os.makedirs(target_output_dir)

        return target_output_dir

    def _build_hierarchical_path(self, base_dir, cell_type, cell_size, cell_radius, slider, speed_value, direction_value):
        """
        构建层级路径结构
        """
        # 清理cell_type，移除特殊字符
        clean_cell_type = re.sub(r'[^\w-]', '', cell_type)

        # 处理数值，移除不必要的小数点
        size_str = str(int(float(cell_size))) if float(cell_size).is_integer() else str(cell_size)
        radius_str = str(cell_radius).rstrip('0').rstrip('.')

        # 确定后缀
        if speed_value is not None:
            suffix = speed_value
        elif direction_value is not None:
            suffix = direction_value
        else:
            suffix = "static"

        # 构建层级路径
        # 第1层: clean_cell_type
        level1 = clean_cell_type

        # 第2层: clean_cell_type_suffix
        level2 = f"{clean_cell_type}_{suffix}"

        # 第3层: clean_cell_type_size_suffix
        level3 = f"{clean_cell_type}_{size_str}_{suffix}"

        # 第4层: clean_cell_type_size_radius_suffix
        level4 = f"{clean_cell_type}_{size_str}_{radius_str}_{suffix}"

        # 第5层: clean_cell_type_size_radius_slider_suffix
        level5 = f"{clean_cell_type}_{size_str}_{radius_str}_{slider}_{suffix}"

        # 组装完整路径
        full_path = os.path.join(base_dir, level1, level2, level3, level4, level5)

        return full_path

    def _validate_parameters(self, cell_type, cell_size, cell_radius):
        """验证输入参数"""
        try:
            # 验证cell_size和cell_radius是数值
            float(cell_size)
            float(cell_radius)

            # 验证cell_type是字符串且不为空
            if not isinstance(cell_type, str) or not cell_type.strip():
                return False

            return True
        except (ValueError, TypeError):
            return False

    def _read_template(self, speed_value=None, direction_value=None):
        """读取基础模板文件，只有在对应功能被选中时才使用特定模板"""
        try:
            print(f"=== 模板选择调试信息 ===")
            print(f"speed_value: {speed_value}")
            print(f"direction_value: {direction_value}")

            # 根据复选框是否被选中来选择模板文件
            if direction_value is not None:
                # Direction复选框被选中
                template_file = self.base_template_file_direction
                print(f"Direction复选框已选中，使用方向模板: {template_file}")
            elif speed_value is not None:
                # Speed复选框被选中
                template_file = self.base_template_file_dynamic
                print(f"Speed复选框已选中，使用动态模板: {template_file}")
            else:
                # 没有复选框被选中，使用默认静态模板
                template_file = self.base_template_file_static
                print(f"使用默认静态模板: {template_file}")

            # 处理 PyInstaller 打包后的资源文件路径
            if getattr(sys, 'frozen', False):
                # 打包后的环境
                bundle_dir = sys._MEIPASS
                template_path = os.path.join(bundle_dir, template_file)
            else:
                # 开发环境
                template_path = os.path.join(os.path.dirname(__file__), template_file)

            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError as e:
            print(f"模板文件未找到: {template_path}")
            print(f"错误详情: {e}")
            return None
        except Exception as e:
            print(f"读取模板文件出错: {e}")
            print(f"模板路径: {template_path}")
            return None

    def _get_structure_data(self, cell_type, slider=4):
        """获取结构几何数据"""
        try:
            # 使用structure_set.py中的函数获取结构定义，传递slider参数
            structure_output = get_crystal_structure(cell_type, slider)

            # 检查是否是错误消息
            if isinstance(structure_output, str) and "不存在" in structure_output:
                return None

            # 解析字符串格式的输出
            return self._parse_structure_output(structure_output)
        except Exception as e:
            print(f"Error in _get_structure_data: {e}")
            return None

    def _parse_structure_output(self, structure_output):
        """解析结构输出，提取坐标和连接定义"""
        lines = structure_output.split('\n')
        coords = []
        cylinders = []

        in_cylinders_section = False

        for line in lines:
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 检测cylinders部分开始
            if 'cylinders = [' in line:
                in_cylinders_section = True
                continue

            # cylinders部分结束
            if in_cylinders_section and line == ']':
                in_cylinders_section = False
                continue

            # 处理坐标定义
            if '=' in line and not in_cylinders_section and 'cylinders' not in line:
                coords.append(line)

            # 处理cylinders连接
            elif in_cylinders_section:
                # 移除末尾的逗号并添加到列表
                cylinder_line = line.rstrip(',').strip()
                if cylinder_line:
                    cylinders.append(cylinder_line)

        return {'coords': coords, 'cylinders': cylinders}

    def _generate_script_content(self, template_content, structure_data, cell_size, cell_radius, slider=4, speed_value=None, direction_value=None, output_dir=None):
        """生成最终的脚本内容"""
        content = template_content

        # 1. 替换半径参数
        content = self._replace_radius(content, cell_radius)

        # 2. 替换坐标定义
        content = self._replace_coordinates(content, structure_data['coords'], cell_size)

        # 3. 替换cylinders连接
        content = self._replace_cylinders(content, structure_data['cylinders'])

        # 4. 替换切割参数（新增）
        content = self._replace_cutting_parameters(content, cell_size, cell_radius)

        # 5. 替换钢板尺寸和位置（新增）
        content = self._replace_steel_plate_dimensions(content, cell_size)

        # 6. 生成上下刚体识别代码
        rigid_body_code = self._generate_rigid_body_detection(structure_data, cell_size)
        content = self._insert_rigid_body_detection(content, rigid_body_code)

        # 7. 集成宏功能（新增）
        content = self._integrate_macro_functionality(content, cell_size, cell_radius, slider, speed_value, direction_value)

        # 8. 替换velocity2参数（当使用动态模板时）
        if speed_value is not None:
            content = self._replace_velocity_parameters(content, speed_value)

        # 9. 替换direction参数（当使用direction模板时）
        if direction_value is not None:
            content = self._replace_direction_parameters(content, direction_value)

        # 10. 设置作业文件保存路径到脚本文件同级目录
        content = self._set_job_directory(content, output_dir)

        return content

    def _set_job_directory(self, content, output_dir=None):
        """设置作业文件保存路径到脚本文件同级目录"""
        try:
            # 使用脚本文件的输出目录作为作业文件保存路径
            if output_dir:
                job_directory = output_dir.replace('\\', '/')
            else:
                # 如果没有指定输出目录，使用默认的generate_script根目录
                if getattr(sys, 'frozen', False):
                    # 打包环境：获取可执行文件所在目录
                    current_dir = os.path.dirname(sys.executable)
                else:
                    # 开发环境：获取脚本文件所在目录
                    current_dir = os.path.dirname(os.path.abspath(__file__))

                job_directory = os.path.join(current_dir, "generate_script").replace('\\', '/')

            # 查找现有的setValues调用并替换，如果没有则在submit前添加
            import re

            # 先尝试替换现有的setValues调用
            pattern = r"mdb\.jobs\['Job-1'\]\.setValues\([^)]*directory\s*=\s*['\"][^'\"]*['\"][^)]*\)"
            replacement = f"mdb.jobs['Job-1'].setValues(directory='{job_directory}')"

            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
            else:
                # 如果没有现有的setValues调用，在submit前添加新的
                submit_pattern = r"(mdb\.jobs\['Job-1'\]\.submit\(consistencyChecking=OFF\))"
                submit_replacement = f"mdb.jobs['Job-1'].setValues(directory='{job_directory}')\n\\1"

                if re.search(submit_pattern, content):
                    content = re.sub(submit_pattern, submit_replacement, content)
                else:
                    # 如果连submit都没有，在文件末尾添加
                    content += f"\nmdb.jobs['Job-1'].setValues(directory='{job_directory}')\nmdb.jobs['Job-1'].submit(consistencyChecking=OFF)\n"

            print(f"设置作业文件保存目录: {job_directory}")
            return content

        except Exception as e:
            print(f"设置作业目录时出错: {str(e)}")
            return content

    def _replace_velocity_parameters(self, content, speed_value):
        """替换velocity2参数，根据speed_value调整速度值"""
        try:
            # 将speed_value转换为数值，然后取负值作为velocity2
            speed_num = float(speed_value)
            velocity2_value = -speed_num

            print(f"\n=== 速度参数替换调试信息 ===")
            print(f"Speed值: {speed_value}")
            print(f"Velocity2值: {velocity2_value}")

            # 替换velocity2参数
            # 匹配模式：velocity2=-10.0, 或 velocity2=-10.0,  # 注释
            pattern = r'velocity2=-?\d+\.?\d*'
            replacement = f'velocity2={velocity2_value}'

            content = re.sub(pattern, replacement, content)

            print(f"已将velocity2替换为: {velocity2_value}")

            return content

        except (ValueError, TypeError) as e:
            print(f"Warning: 无法转换speed_value到数值: {speed_value}, 错误: {e}")
            return content

    def _replace_direction_parameters(self, content, direction_value):
        """根据direction复选框的值更改direction脚本最后的内容"""
        try:
            print(f"\n=== 方向参数替换调试信息 ===")
            print(f"Direction值: {direction_value}")

            # 如果是Z方向，不做修改
            if direction_value == "Z":
                print("Direction为Z，保持原有参数")
                return content

            # 如果是X方向，修改脚本最后的参数
            elif direction_value == "X":
                print("Direction为X，修改脚本最后的参数")

                # 替换第一个setValuesInStep中的参数：u1=0.0, u2=0.0, u3=-0.5 -> u1=-0.5, u2=0.0, u3=0.0
                pattern1 = r"stepName='Step-1',u1=0\.0,\s*u2=0\.0,\s*u3=-0\.5"
                replacement1 = "stepName='Step-1',u1=-0.5, u2=0.0, u3=0.0"
                content = re.sub(pattern1, replacement1, content)

                # 替换setValues中的参数：u1=SET,u2=SET, u3=UNSET -> u1=UNSET,u2=SET, u3=SET
                pattern2 = r"setValues\(u1=SET,u2=SET,\s*u3=UNSET\)"
                replacement2 = "setValues(u1=UNSET,u2=SET, u3=SET)"
                content = re.sub(pattern2, replacement2, content)

                print("已将方向参数替换为X方向设置")
                return content

            else:
                print(f"Warning: 未知的direction值: {direction_value}")
                return content

        except Exception as e:
            print(f"Warning: 方向参数替换出错: {e}")
            return content


    def _replace_radius(self, content, cell_radius):
        """替换半径参数"""
        # 查找并替换radius = xxx这一行
        pattern = r'radius = [\d.]+\s*$'
        replacement = f'radius = {cell_radius}'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        return content

    def _replace_coordinates(self, content, coords, cell_size):
        """替换坐标定义并进行缩放"""
        # 计算缩放因子
        scale_factor = float(cell_size) / self.base_cell_size

        print(f"\n=== 坐标缩放调试信息 ===")
        print(f"目标单元尺寸: {cell_size}")
        print(f"基础单元尺寸: {self.base_cell_size}")
        print(f"缩放因子: {scale_factor}")
        print(f"原始坐标数量: {len(coords)}")

        # 找到坐标定义的开始和结束位置
        start_pattern = r'# 定义关键点坐标\s*\n'
        end_pattern = r'\n\s*# 定义圆柱体连接'

        # 生成缩放后的坐标
        scaled_coords = []
        for i, coord in enumerate(coords):
            scaled_coord = self._scale_coordinate_line(coord, scale_factor)
            scaled_coords.append(scaled_coord)
            # 只打印前几个坐标以避免过多输出
            if i < 5:
                print(f"坐标{i+1}: {coord.strip()} -> {scaled_coord.strip()}")

        # 构建新的坐标部分
        new_coords_section = "# 定义关键点坐标\n" + '\n'.join(scaled_coords) + '\n'

        # 替换内容
        match = re.search(start_pattern + r'(.*?)' + end_pattern, content, re.DOTALL)
        if match:
            content = content[:match.start()] + new_coords_section + '\n# 定义圆柱体连接' + content[match.end():]

        return content

    def _scale_coordinate_line(self, coord_line, scale_factor):
        """缩放单个坐标行"""
        # 使用正则表达式找到坐标数组中的数字并缩放
        def scale_number(match):
            number = float(match.group())
            scaled = number * scale_factor
            # 改进的数值格式化，保持精度
            # 使用4位小数精度，然后移除尾随零
            formatted = f"{scaled:.4f}".rstrip('0').rstrip('.')
            # 如果结果为空（如0.0000），返回'0'
            return formatted if formatted else '0'

        # 匹配方括号内的数字（包括负数），但不匹配变量名中的数字
        # 使用更精确的正则表达式，只匹配 = [ 和 ] 之间的数字
        pattern = r'(=\s*\[)([^\]]+)(\])'

        def replace_coordinates(match):
            prefix = match.group(1)  # '= ['
            coords_str = match.group(2)  # 坐标字符串
            suffix = match.group(3)  # ']'

            # 在坐标字符串中替换数字
            number_pattern = r'-?\d+\.?\d*'
            scaled_coords = re.sub(number_pattern, scale_number, coords_str)

            return prefix + scaled_coords + suffix

        scaled_line = re.sub(pattern, replace_coordinates, coord_line)
        return scaled_line

    def _replace_cylinders(self, content, cylinders):
        """替换cylinders连接定义"""
        # 找到cylinders定义的开始和结束位置
        start_pattern = r'cylinders = \['
        end_pattern = r'\]'

        # 构建新的cylinders部分
        cylinders_lines = []
        for i, cylinder in enumerate(cylinders):
            if i == len(cylinders) - 1:
                cylinders_lines.append(f'    {cylinder}')
            else:
                cylinders_lines.append(f'    {cylinder},')

        new_cylinders_section = 'cylinders = [\n' + '\n'.join(cylinders_lines) + '\n]'

        # 查找并替换cylinders部分
        # 使用更精确的正则表达式匹配整个cylinders数组
        pattern = r'cylinders = \[([^\]]*(?:\[[^\]]*\][^\]]*)*)?\]'
        content = re.sub(pattern, new_cylinders_section, content, flags=re.DOTALL)

        return content

    def _replace_cutting_parameters(self, content, cell_size, cell_radius):
        """替换切割相关的参数，使用新的位置计算方式"""
        cell_size_float = float(cell_size)
        cell_radius_float = float(cell_radius)

        # 新的切割位置计算方式
        # 切割开始位置：size/2 + 2*max(radius_value)
        cutting_start_position = cell_size_float / 2 + 2 * cell_radius_float

        # 切割结束位置：-size
        cutting_end_position = -cell_size_float

        # 计算切割深度（从开始位置到结束位置的距离）
        cutting_depth = cutting_start_position - cutting_end_position

        # 半尺寸用于设置矩形和变换原点
        half_size = cell_size_float / 2

        print(f"\n=== 切割参数新计算方式调试信息 ===")
        print(f"单元尺寸: {cell_size_float}")
        print(f"圆柱半径: {cell_radius_float}")
        print(f"切割开始位置: {cutting_start_position} (size/2 + 2*radius)")
        print(f"切割结束位置: {cutting_end_position} (-size)")
        print(f"切割深度: {cutting_depth}")
        print(f"半尺寸: {half_size}")

        # 替换切割平面offset值（使用新的切割开始位置）
        content = re.sub(r'offset=3(?=\))', f'offset={cutting_start_position}', content)

        # 替换切割深度值（使用新计算的深度）
        content = re.sub(r'depth=6(?=,)', f'depth={cutting_depth}', content)

        # 替换变换原点中的坐标值
        # 顶部切割的origin坐标（使用半尺寸）
        content = re.sub(r'origin=\(0\.0, 0\.0, 2\.5\)',
                        f'origin=(0.0, 0.0, {half_size})', content)

        # 侧面切割的origin坐标（使用半尺寸）
        content = re.sub(r'origin=\(0\.0, 2\.5, 0\.0\)',
                        f'origin=(0.0, {half_size}, 0.0)', content)

        # 替换切割矩形的尺寸
        # 内部矩形 (-2.5, -2.5) to (2.5, 2.5) 使用半尺寸
        content = re.sub(r'point1=\(-2\.5, -2\.5\)',
                        f'point1=(-{half_size}, -{half_size})', content)
        content = re.sub(r'point2=\(2\.5, 2\.5\)',
                        f'point2=({half_size}, {half_size})', content)

        # 外部矩形 (-5.0, -5.0) to (5.0, 5.0) - 使用双倍尺寸
        outer_size = cell_size_float
        content = re.sub(r'point1=\(-5\.0, -5\.0\)',
                        f'point1=(-{outer_size}, -{outer_size})', content)
        content = re.sub(r'point2=\(5\.0, 5\.0\)',
                        f'point2=({outer_size}, {outer_size})', content)

        return content

    def _replace_steel_plate_dimensions(self, content, cell_size):
        """替换钢板尺寸和位置，使其与cell_size成比例缩放"""
        # 计算缩放因子
        scale_factor = float(cell_size) / self.base_cell_size

        # 基础模板的钢板参数
        base_plate_length = 6.0    # 刚性板长度
        base_plate_width = 6.0     # 刚性板宽度（extrude depth）
        base_half_size = 2.5       # 原始模板的半尺寸
        base_offset = 3.0          # 刚性板与结构的距离

        # 计算缩放后的参数
        scaled_plate_length = base_plate_length * scale_factor
        scaled_plate_width = base_plate_width * scale_factor
        scaled_half_size = base_half_size * scale_factor
        scaled_offset = base_offset * scale_factor

        print(f"\n=== 钢板参数缩放调试信息 ===")
        print(f"刚性板长度: {base_plate_length} -> {scaled_plate_length}")
        print(f"刚性板宽度: {base_plate_width} -> {scaled_plate_width}")
        print(f"板位置偏移: {base_offset} -> {scaled_offset}")

        # 替换刚性板的线段长度 (-3.0, 0.0) to (3.0, 0.0)
        content = re.sub(r'point1=\(-3\.0, 0\.0\)',
                        f'point1=(-{scaled_offset}, 0.0)', content)
        content = re.sub(r'point2=\(3\.0, 0\.0\)',
                        f'point2=({scaled_offset}, 0.0)', content)

        # 替换刚性板的挤出深度
        content = re.sub(r'depth=6\.0(?=\))', f'depth={scaled_plate_width}', content)

        # 替换刚性板的位置 vector
        # RigidPlate-1: (0.0, -2.5, -3.0)
        content = re.sub(r'vector=\(0\.0, -2\.5, -3\.0\)',
                        f'vector=(0.0, -{scaled_half_size}, -{scaled_offset})', content)

        # RigidPlate-2: (0.0, 2.5, -3.0)
        content = re.sub(r'vector=\(0\.0, 2\.5, -3\.0\)',
                        f'vector=(0.0, {scaled_half_size}, -{scaled_offset})', content)

        return content

    def _generate_rigid_body_detection(self, structure_data, cell_size):
        """生成上下刚体识别代码（简化版）"""
        try:
            # 尝试获取结构名称
            structure_name = getattr(self, '_current_structure_name', 'Unknown')

            # 计算上下刚体的Z坐标位置
            cell_size_float = float(cell_size)
            top_rigid_z = cell_size_float / 2      # 顶部刚体位置
            bottom_rigid_z = -cell_size_float / 2  # 底部刚体位置

            # 生成简化的刚体识别代码
            rigid_body_code = f"""
    # === 上下刚体识别 ===
    def identify_rigid_bodies():
        '''
        识别结构的上下刚体区域
        顶部刚体Z坐标: {top_rigid_z}
        底部刚体Z坐标: {bottom_rigid_z}
        结构类型: {structure_name}
        '''
        print("=== 上下刚体识别 ===")
        print(f"结构类型: {structure_name}")
        print(f"单元尺寸: {cell_size_float}")
        print(f"顶部刚体Z坐标: {top_rigid_z}")
        print(f"底部刚体Z坐标: {bottom_rigid_z}")

        # 这里可以添加具体的刚体识别逻辑
        # 当前版本仅输出识别信息

        return {{"top_z": {top_rigid_z}, "bottom_z": {bottom_rigid_z}}}

    # 执行刚体识别
    rigid_body_info = identify_rigid_bodies()
"""
            return rigid_body_code

        except Exception as e:
            print(f"Warning: Rigid body detection failed ({e})")
            return ""



    def _insert_rigid_body_detection(self, content, rigid_body_code):
        """将上下刚体识别代码插入到适当位置"""
        # 在Macro1()函数内，接触定义之前插入
        # 寻找"# === 接触属性 ==="的位置
        contact_pattern = r'(\s*# === 接触属性 ===)'

        # 如果找到接触属性标记，在其前面插入
        if re.search(contact_pattern, content):
            replacement = rigid_body_code + r'\1'
            content = re.sub(contact_pattern, replacement, content, count=1)
        else:
            # 如果没找到，在第一个ContactProperty定义前插入
            contact_property_pattern = r'(\s*mdb\.models\[\'Model-1\'\]\.ContactProperty\(\'IntProp-1\'\))'
            if re.search(contact_property_pattern, content):
                replacement = rigid_body_code + r'\1'
                content = re.sub(contact_property_pattern, replacement, content, count=1)

        return content

    def _integrate_macro_functionality(self, content, cell_size=None, cell_radius=None, slider=4, speed_value=None, direction_value=None):
        """集成宏功能到脚本中"""
        try:
            # 获取当前结构类型
            structure_type = getattr(self, '_current_structure_name', 'Unknown')

            # 如果结构类型未知或不支持，跳过宏集成
            # if structure_type == 'Unknown' or not self.macro_integrator.is_structure_supported(structure_type):
            #     print(f"Warning: Structure type '{structure_type}' not supported for macro integration")
            #     return content

            # 根据GUI选项更新MacroIntegrator设置
            # gui_speed_on = speed_value is not None
            # direction_enabled = direction_value is not None
            # self.macro_integrator.update_gui_options(gui_speed_on=gui_speed_on, direction_enabled=direction_enabled)

            # 获取对应的宏内容（传入条件判断所需的参数）
            # macro_content = self.macro_integrator.get_macro_content(structure_type, cell_size, cell_radius, slider)

            # 宏集成功能已禁用，直接返回原内容
            return content

            # if not macro_content:
            #     print(f"Warning: No macro content found for structure type '{structure_type}'")
            #     return content

            # # 在脚本末尾添加宏功能 - 简化版本
            # separator = f"\n\n# Macro functions for {structure_type} structure\n"

            # # 拼接内容
            # integrated_content = content + separator + macro_content

            # print(f"Successfully integrated macro functionality for {structure_type} structure")
            # return integrated_content

        except Exception as e:
            print(f"Warning: Error integrating macro functionality: {e}")
            return content

    def _generate_filename(self, cell_type, cell_size, cell_radius, slider, speed_value=None, direction_value=None):
        """生成文件名"""
        # 清理cell_type，移除特殊字符
        clean_cell_type = re.sub(r'[^\w-]', '', cell_type)

        # 处理数值，移除不必要的小数点
        size_str = str(int(float(cell_size))) if float(cell_size).is_integer() else str(cell_size)
        radius_str = str(cell_radius).rstrip('0').rstrip('.')

        # 确定后缀
        if speed_value is not None:
            suffix = f"_{speed_value}"
        elif direction_value is not None:
            suffix = f"_{direction_value}"
        else:
            suffix = "_static"

        return f"{clean_cell_type}_{size_str}_{radius_str}_{slider}{suffix}.py"

    def create_batch_executor(self, output_dir):
        """创建批量执行器脚本"""
        executor_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abaqus脚本批量执行器
自动遍历当前目录及所有子目录下的.py文件并执行
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def find_all_python_scripts(root_dir):
    """查找所有Python脚本文件"""
    python_files = []

    # 遍历所有子目录
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py') and file != 'run_all_scripts.py':  # 排除自身
                file_path = os.path.join(root, file)
                python_files.append(file_path)

    return sorted(python_files)

def execute_abaqus_script(script_path):
    """执行单个Abaqus脚本"""
    print(f"\\n{'='*60}")
    print(f"正在执行: {script_path}")
    print(f"{'='*60}")

    try:
        # 切换到脚本所在目录
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)

        # 使用Abaqus CAE执行脚本
        cmd = f'abaqus cae noGUI={script_name}'

        print(f"执行命令: {cmd}")
        print(f"工作目录: {script_dir}")

        # 执行命令
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )

        if result.returncode == 0:
            print(f"✓ 执行成功: {script_path}")
            return True
        else:
            print(f"✗ 执行失败: {script_path}")
            print(f"错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ 执行超时: {script_path}")
        return False
    except Exception as e:
        print(f"✗ 执行出错: {script_path}")
        print(f"错误信息: {str(e)}")
        return False

def main():
    """主函数"""
    print("Abaqus脚本批量执行器")
    print("="*60)

    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"搜索目录: {current_dir}")

    # 查找所有Python脚本
    python_scripts = find_all_python_scripts(current_dir)

    if not python_scripts:
        print("未找到任何Python脚本文件")
        return

    print(f"\\n找到 {len(python_scripts)} 个Python脚本文件:")
    for i, script in enumerate(python_scripts, 1):
        rel_path = os.path.relpath(script, current_dir)
        print(f"  {i}. {rel_path}")

    # 询问用户是否继续
    response = input(f"\\n是否执行所有 {len(python_scripts)} 个脚本? (y/N): ")
    if response.lower() not in ['y', 'yes', '是']:
        print("执行已取消")
        return

    # 执行统计
    success_count = 0
    failed_count = 0
    start_time = time.time()

    # 逐个执行脚本
    for i, script_path in enumerate(python_scripts, 1):
        rel_path = os.path.relpath(script_path, current_dir)
        print(f"\\n[{i}/{len(python_scripts)}] 执行脚本: {rel_path}")

        if execute_abaqus_script(script_path):
            success_count += 1
        else:
            failed_count += 1

        # 脚本间间隔
        if i < len(python_scripts):
            print("等待5秒后执行下一个脚本...")
            time.sleep(5)

    # 执行总结
    end_time = time.time()
    total_time = end_time - start_time

    print(f"\\n{'='*60}")
    print("执行完成!")
    print(f"总脚本数: {len(python_scripts)}")
    print(f"成功执行: {success_count}")
    print(f"执行失败: {failed_count}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
'''

        # 保存执行器脚本
        executor_path = os.path.join(output_dir, "run_all_scripts.py")
        with open(executor_path, 'w', encoding='utf-8') as f:
            f.write(executor_content)

        print(f"已创建批量执行器脚本: {executor_path}")
        return executor_path


def generate_abaqus_script(cell_type, cell_size, cell_radius, slider=4, output_dir=None, speed_value=None, direction_value=None, batch_mode=False, batch_parent_dir=None):
    """
    便捷函数：生成Abaqus脚本

    参数:
    - cell_type: 晶体结构类型
    - cell_size: 单元尺寸
    - cell_radius: 杆件半径
    - slider: 滑块值 (0-8)，用于控制BCC/BCCZ结构中O原子的位置
    - output_dir: 输出目录
    - speed_value: 速度值 (当Speed复选框选中时)
    - direction_value: 方向值 (当Direction复选框选中时)
    - batch_mode: 是否为批量模式
    - batch_parent_dir: 批量模式的父文件夹路径

    返回:
    - (success: bool, message: str, filename: str)
    """
    generator = AbaqusScriptGenerator()
    return generator.generate_script(cell_type, cell_size, cell_radius, slider, output_dir, speed_value, direction_value, batch_mode, batch_parent_dir)


if __name__ == "__main__":
    pass