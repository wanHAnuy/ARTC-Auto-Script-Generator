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
        self._file_tracker_callback = None  # 文件追踪回调函数

    def set_file_tracker_callback(self, callback):
        """设置文件追踪回调函数"""
        self._file_tracker_callback = callback

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

            # 将生成的文件添加到追踪列表
            if hasattr(self, '_file_tracker_callback') and self._file_tracker_callback:
                try:
                    self._file_tracker_callback(filepath)
                except Exception as e:
                    print(f"Warning: 无法添加文件到追踪列表: {e}")

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

        # 第5层: clean_cell_type_size_radius_slider (不包含suffix，避免与文件名冲突)
        level5 = f"{clean_cell_type}_{size_str}_{radius_str}_{slider}"

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

        
        # 8. 替换velocity2参数（当使用动态模板时）
        if speed_value is not None:
            content = self._replace_velocity_parameters(content, speed_value)

        # 9. 替换direction参数（当使用direction模板时）
        if direction_value is not None:
            content = self._replace_direction_parameters(content, direction_value)

        # 10. 设置作业文件保存路径到脚本文件同级目录
        # content = self._set_job_directory(content, output_dir)

        # 11. 追加作业设置、提交和等待语句
        content = self._append_job_settings(content, output_dir, cell_size, speed_value, direction_value)

        return content

    def _determine_script_type(self, speed_value, direction_value):
        """确定脚本类型"""
        if direction_value is not None:
            return "direction"
        elif speed_value is not None:
            return "speed"
        else:
            return "static"

    def _get_output_variable_names(self, script_type):
        """根据脚本类型获取对应的outputVariableName"""
        output_variables = {
            "static": {
                "force": "Reaction force: RF2 PI: RIGIDPLATE-2 Node 122 in NSET TOPREFLECTION",
                "displacement": "Spatial displacement: U2 PI: RIGIDPLATE-2 Node 122 in NSET TOPREFLECTION"
            },
            "speed": {
                "force": "Reaction force: RF3 PI: RIGIDPLATE-1 Node 122 in NSET BOTREFLECTION",
                "displacement": "Spatial displacement: U2 PI: MERGEDSTRUCTURE-1 Node 149 in NSET REFLECTION"
            },
            "direction": {
                "force": "Reaction force: RF2 PI: RIGIDPLATE-2 Node 122 in NSET TOPREFLECTION",
                "displacement": "Spatial displacement: U2 PI: RIGIDPLATE-2 Node 122 in NSET TOPREFLECTION"
            },
        }
        return output_variables.get(script_type, output_variables["static"])

    def _append_job_settings(self, content, output_dir, cell_size, speed_value=None, direction_value=None):
        """在 content 末尾追加 Job 设置、提交和等待语句"""
        import os
        job_name = os.path.basename(output_dir).replace('.', 'p')

        # 生成odb文件路径：与脚本文件路径一致，只是后缀改为.odb
        odb_path = os.path.join(output_dir, f"{job_name}.odb")

        # 确定脚本类型并获取对应的outputVariableName
        script_type = self._determine_script_type(speed_value, direction_value)
        output_vars = self._get_output_variable_names(script_type)

        addition = f"""

a = mdb.models['Model-1'].rootAssembly
a.regenerate()

os.chdir(r"{output_dir}")

mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(numIntervals=60)

mdb.Job(name='{job_name}', model='Model-1', description='', type=ANALYSIS,
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=ON,
    modelPrint=ON, contactPrint=ON, historyPrint=ON, userSubroutine='',
    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=0, numCpus=8,
    numDomains=8, numGPUs=0)

mdb.jobs['{job_name}'].submit(consistencyChecking=OFF)
mdb.jobs['{job_name}'].waitForCompletion()


import xyPlot
import os

odb_filename = r'{odb_path}'
odb = session.openOdb(name=odb_filename)

# 提取数据
xy_force = xyPlot.XYDataFromHistory(odb=odb,
    outputVariableName='{output_vars["force"]}',
    steps=('Step-1', ), suppressQuery=True)

xy_disp = xyPlot.XYDataFromHistory(odb=odb,
    outputVariableName='{output_vars["displacement"]}',
    steps=('Step-1', ), suppressQuery=True)

xy_combined = combine(abs(xy_disp),abs(xy_force))

model = mdb.models['Model-1']
part  = model.parts['MergedStructure']

# 计算几何体积
volume = part.getVolume()
print("MergedStructure 体积 =", volume)

# 计算密度 = 体积/size的三次方
cell_size = {cell_size}
density = volume / (cell_size ** 3)
print("密度 (density) =", density)

# 提取xy_combined数据进行SEA/Strength计算
displacement_data = []
force_data = []
for i in range(len(xy_combined)):
    displacement_data.append(xy_combined[i][0])
    force_data.append(xy_combined[i][1])

# 计算strength/SEA
speed_enabled = {repr(speed_value)} is not None
if speed_enabled:
    # 计算SEA = Total_Energy_Absorbed / Structure_Mass
    # Total_Energy_Absorbed是在displacement达到最大值之前F对D的积分
    max_displacement = max(displacement_data)

    # 找到达到最大displacement的索引
    max_disp_index = displacement_data.index(max_displacement)

    # 截取到最大displacement的数据
    disp_to_max = displacement_data[:max_disp_index+1]
    force_to_max = force_data[:max_disp_index+1]

    # 使用梯形法则计算积分 (Total_Energy_Absorbed)
    total_energy_absorbed = 0.0
    for i in range(len(disp_to_max)-1):
        # 梯形面积 = (f1 + f2) * (x2 - x1) / 2
        area = (force_to_max[i] + force_to_max[i+1]) * (disp_to_max[i+1] - disp_to_max[i]) / 2.0
        total_energy_absorbed += area

    # Structure_Mass = 1.2e-09 * volume
    structure_mass = 1.2e-09 * volume

    # SEA = Total_Energy_Absorbed / Structure_Mass
    sea_value = total_energy_absorbed / structure_mass
    feature_value = "SEA: " + str(sea_value)
    print("SEA =", sea_value)
else:
    # 计算strength (max value point of xy_combined)
    strength_value = max(force_data)
    feature_value = "Strength: " + str(strength_value)
    print("Strength =", strength_value)

# 保存为txt文件，按照新格式输出
with open('feature_data.txt', 'w') as f:
    f.write("{job_name}\\n")
    f.write(feature_value + "\\n")
    f.write("density: " + str(density) + "\\n")
    f.write("F_D curve:\\n")

# 然后追加xy_combined数据
session.writeXYReport(fileName='feature_data.txt', xyData=(xy_combined, ), appendMode=ON)


# 关闭ODB
odb.close()

"""
        return content.rstrip() + addition



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

    # 尝试设置文件追踪回调
    try:
        import sys
        # 尝试多种可能的模块名称
        main_module = None
        for module_name in ['main', '__main__']:
            if module_name in sys.modules:
                main_module = sys.modules[module_name]
                if hasattr(main_module, 'add_generated_file'):
                    generator.set_file_tracker_callback(main_module.add_generated_file)
                    break
    except Exception:
        pass  # 静默失败，不影响脚本生成

    return generator.generate_script(cell_type, cell_size, cell_radius, slider, output_dir, speed_value, direction_value, batch_mode, batch_parent_dir)


if __name__ == "__main__":
    pass