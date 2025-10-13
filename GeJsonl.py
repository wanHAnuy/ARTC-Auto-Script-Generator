import os
import json
import glob
import re
from pathlib import Path
try:
    import numpy as np
    from scipy.interpolate import interp1d, CubicSpline, UnivariateSpline
    SCIPY_AVAILABLE = True
except ImportError:
    try:
        import numpy as np
        SCIPY_AVAILABLE = False
        print("警告: scipy未安装，将使用线性插值替代样条插值")
    except ImportError:
        print("警告: numpy未安装，插值功能将不可用")
        SCIPY_AVAILABLE = False

# 参数设置
A = 50
B = 10 * A  # B = 50

def advanced_interpolation(displacement, force, target_points=B, method='cubic_spline',
                          noise_threshold=0.15):
    """
    高级插值函数，支持多种插值方法，并可以过滤噪声点

    Args:
        displacement: 原始位移数据
        force: 原始力数据
        target_points: 目标插值点数，默认100
        method: 插值方法 ('linear', 'cubic', 'cubic_spline', 'smooth_spline')
        noise_threshold: 噪声阈值，默认0.15（相对变化率大于15%视为噪声）

    Returns:
        tuple: (插值后的位移, 插值后的力, 插值信息)
    """

    if len(displacement) < 2 or len(force) < 2:
        return displacement, force, "数据点不足，无法插值"

    # 转换为numpy数组
    x_original = np.array(displacement)
    y_original = np.array(force)

    # 处理X值连续相同的情况：保留Y变化最小的点
    x_clean = []
    y_clean = []
    i = 0
    removed_duplicate_x = 0

    while i < len(displacement):
        current_x = displacement[i]
        current_y = force[i]

        # 查找所有X值相同的点
        j = i + 1
        same_x_indices = [i]
        while j < len(displacement) and abs(displacement[j] - current_x) < 1e-10:
            same_x_indices.append(j)
            j += 1

        # 如果有多个X值相同的点
        if len(same_x_indices) > 1:
            # 计算所有Y值的均值
            y_values = [force[idx] for idx in same_x_indices]
            y_mean = sum(y_values) / len(y_values)

            # 找到距离均值最近的点（Y变化最小）
            min_diff = float('inf')
            best_idx = same_x_indices[0]
            for idx in same_x_indices:
                diff = abs(force[idx] - y_mean)
                if diff < min_diff:
                    min_diff = diff
                    best_idx = idx

            # 只保留最稳定的点
            x_clean.append(displacement[best_idx])
            y_clean.append(force[best_idx])
            removed_duplicate_x += len(same_x_indices) - 1
        else:
            # 只有一个点，直接保留
            x_clean.append(current_x)
            y_clean.append(current_y)

        i = j

    if removed_duplicate_x > 0:
        print(f"  已移除 {removed_duplicate_x} 个X值重复的不稳定点")

    # 检测位移收敛并删除收敛后的数据
    x_final = []
    y_final = []
    removed_converged = 0

    if len(x_clean) >= 5:
        # 计算位移变化率
        disp_changes = []
        for i in range(1, len(x_clean)):
            change = abs(x_clean[i] - x_clean[i-1])
            disp_changes.append(change)

        # 计算均值（排除0值）
        non_zero_changes = [c for c in disp_changes if c > 1e-10]
        if len(non_zero_changes) > 0:
            mean_change = sum(non_zero_changes) / len(non_zero_changes)
            threshold = mean_change / A  # A倍均值的阈值

            # 检测连续4个点低于阈值
            cutoff_index = len(x_clean)  # 默认保留所有点
            for i in range(len(disp_changes) - 3):
                # 检查连续4个变化率是否都低于阈值
                if all(disp_changes[i+j] < threshold for j in range(4)):
                    cutoff_index = i + 1  # 在第一个低变化率点之前截断
                    break

            # 截断数据
            x_final = x_clean[:cutoff_index]
            y_final = y_clean[:cutoff_index]
            removed_converged = len(x_clean) - cutoff_index

            if removed_converged > 0:
                print(f"  检测到位移收敛，已移除 {removed_converged} 个收敛后的数据点")
        else:
            # 没有非零变化，保留所有数据
            x_final = x_clean
            y_final = y_clean
    else:
        # 数据点太少，不做收敛检测
        x_final = x_clean
        y_final = y_clean

    info = f"处理后数据: {len(displacement)} -> {len(x_final)} 点"
    return x_final, y_final, info

def smart_target_points(original_length, target=B):
    """
    智能确定目标插值点数 - 统一到100个点

    Args:
        original_length: 原始数据点数
        target: 目标点数 (默认100)

    Returns:
        int: 实际使用的插值点数
    """

    # 统一处理：无论原始点数多少，都处理到100个点
    if original_length < 2:
        return original_length  # 数据点太少，无法处理
    else:
        return target  # 统一到100个点

def parse_sample_name_for_sorting(sample_name):
    """
    解析样本名称以提取排序关键字

    样本名称格式: {结构名}_{size}_{ratio}_{slider}
    例如: BCC_5_0.5_5, Auxetic_5_0.3_8, FCCZ_4_0p5_4 (0p5表示0.5)

    Args:
        sample_name: 样本名称字符串

    Returns:
        tuple: (structure, size, ratio, slider) 用于排序
               如果解析失败，返回 (sample_name, float('inf'), float('inf'), float('inf'))
    """

    try:
        # 使用正则表达式解析样本名称
        # 匹配格式: 结构名_数字_小数_数字
        # 支持 0.5 和 0p5 两种格式
        pattern = r'^([A-Za-z_]+)_(\d+)_(\d*[p\.]?\d+)_(\d+)$'
        match = re.match(pattern, sample_name.strip())

        if match:
            structure = match.group(1)  # 结构名 (如 BCC, FCC, Auxetic)
            size = int(match.group(2))  # 尺寸 (如 5)
            ratio_str = match.group(3).replace('p', '.')  # 比例 (如 0.5, 0.3)，将 p 替换为 .
            ratio = float(ratio_str)
            slider = int(match.group(4))  # 滑块值 (如 0-8)

            return (structure, size, ratio, slider)
        else:
            # 如果格式不匹配，尝试更宽松的模式
            parts = sample_name.split('_')
            if len(parts) >= 4:
                try:
                    structure = parts[0]
                    size = int(parts[1])
                    ratio_str = parts[2].replace('p', '.')  # 将 p 替换为 .
                    ratio = float(ratio_str)
                    slider = int(parts[3])
                    return (structure, size, ratio, slider)
                except (ValueError, IndexError):
                    pass

            # 解析失败，返回默认值使其排在最后
            print(f"警告: 无法解析样本名称格式 '{sample_name}'，将排在最后")
            return (sample_name, float('inf'), float('inf'), float('inf'))

    except Exception as e:
        print(f"解析样本名称 '{sample_name}' 时出错: {str(e)}")
        return (sample_name, float('inf'), float('inf'), float('inf'))

def calculate_sea(displacement, force, volume):
    """
    计算SEA (Specific Energy Absorption)

    Args:
        displacement: 位移数据列表
        force: 力数据列表
        volume: 结构体积

    Returns:
        float: SEA值
    """
    if len(displacement) < 2 or len(force) < 2:
        return None

    try:
        # 找到峰值点
        peak_force = max(force)
        peak_index = force.index(peak_force)

        # 从峰值后找到谷值点（局部最小值）
        valley_index = peak_index
        if peak_index < len(force) - 1:
            # 在峰值后寻找谷值
            for i in range(peak_index + 1, len(force) - 1):
                # 找到一个局部最小值点（前后都比它大）
                if (force[i] <= force[i-1] and force[i] <= force[i+1]):
                    valley_index = i
                    break
            # 如果没找到局部最小值，使用峰值后的最小值点
            if valley_index == peak_index:
                min_force_after_peak = min(force[peak_index+1:])
                valley_index = force.index(min_force_after_peak, peak_index+1)

        # 截取从零到谷值的数据
        disp_to_valley = displacement[:valley_index+1]
        force_to_valley = force[:valley_index+1]

        # 使用梯形法则计算积分 (Total_Energy_Absorbed)
        total_energy_absorbed = 0.0
        for i in range(len(disp_to_valley)-1):
            # 梯形面积 = (f1 + f2) * (x2 - x1) / 2
            area = (force_to_valley[i] + force_to_valley[i+1]) * (disp_to_valley[i+1] - disp_to_valley[i]) / 2.0
            total_energy_absorbed += area

        # Structure_Mass = volume
        structure_mass = volume

        # SEA = Total_Energy_Absorbed / Structure_Mass
        sea_value = total_energy_absorbed / structure_mass
        return sea_value
    except Exception as e:
        print(f"计算SEA时出错: {str(e)}")
        return None

def sort_samples_by_hierarchy(sample_file_map):
    """
    根据层级规则对样本进行排序

    排序优先级:
    1. 结构名 (字母顺序)
    2. Size (数值大小)
    3. Ratio (数值大小)
    4. Slider (数值大小)

    Args:
        sample_file_map: 字典 {sample_name: (file_path, file_size)}

    Returns:
        list: 排序后的 [(sample_name, file_path, file_size), ...] 列表
    """

    # 创建包含排序关键字的列表
    items_with_keys = []
    for sample_name, (file_path, file_size) in sample_file_map.items():
        sort_key = parse_sample_name_for_sorting(sample_name)
        items_with_keys.append((sort_key, sample_name, file_path, file_size))

    # 按排序关键字排序
    # sort_key = (structure, size, ratio, slider)
    items_with_keys.sort(key=lambda x: x[0])

    # 返回排序后的样本列表，格式: [(sample_name, file_path, file_size), ...]
    sorted_samples = [(item[1], item[2], item[3]) for item in items_with_keys]

    return sorted_samples

# SEA计算函数已移除，在其他模块中实现

def parse_feature_data_advanced(content):
    """
    改进的feature_data解析函数
    """
    lines = content.strip().split('\n')

    # 提取样本名称（第一行）
    sample_name = lines[0].strip() if lines else ""

    # 提取强度、密度、SEA和体积（支持更多格式）
    strength = None
    density = None
    sea = None
    volume = None

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # 匹配强度（支持多种格式）
        strength_patterns = [
            r'strength[:\s]*([\d.e+-]+)',
            r'强度[:\s]*([\d.e+-]+)',
            r'stress[:\s]*([\d.e+-]+)'
        ]

        for pattern in strength_patterns:
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match and strength is None:
                try:
                    strength = float(match.group(1))
                    break
                except ValueError:
                    continue

        # 匹配SEA（支持多种格式）
        sea_patterns = [
            r'sea[:\s]*([\d.e+-]+)',
            r'specific energy absorption[:\s]*([\d.e+-]+)'
        ]

        for pattern in sea_patterns:
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match and sea is None:
                try:
                    sea = float(match.group(1))
                    break
                except ValueError:
                    continue

        # 匹配密度（支持多种格式）
        density_patterns = [
            r'density[:\s]*([\d.e+-]+)',
            r'密度[:\s]*([\d.e+-]+)',
            r'ρ[:\s]*([\d.e+-]+)'
        ]

        for pattern in density_patterns:
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match and density is None:
                try:
                    density = float(match.group(1))
                    break
                except ValueError:
                    continue

        # 匹配体积（支持多种格式）
        volume_patterns = [
            r'volume[:\s]*([\d.e+-]+)',
            r'体积[:\s]*([\d.e+-]+)'
        ]

        for pattern in volume_patterns:
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match and volume is None:
                try:
                    volume = float(match.group(1))
                    break
                except ValueError:
                    continue

    # 查找F_D curve数据（支持更多格式）
    fd_start_idx = None
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ["f_d curve", "force-displacement", "力-位移"]):
            fd_start_idx = i
            break

    displacement = []
    force = []

    # 如果找到了 "F_D curve" 标记
    if fd_start_idx is not None:
        data_started = False
        for line in lines[fd_start_idx + 1:]:
            line = line.strip()
            if not line:
                continue

            # 跳过表头行
            if any(keyword in line.lower() for keyword in ["x", "displacement", "force", "位移", "力"]):
                data_started = True
                continue

            if data_started and line:
                # 更robust的数据行匹配
                # 支持多种分隔符：空格、制表符、逗号
                parts = re.split(r'[,\s\t]+', line)
                if len(parts) >= 2:
                    try:
                        disp_val = float(parts[0])
                        force_val = float(parts[1])
                        displacement.append(disp_val)
                        force.append(force_val)
                    except ValueError:
                        continue
    else:
        # 如果没有找到 "F_D curve" 标记，直接查找数据表头
        # 查找包含 "X" 或 "_temp" 的表头行
        data_started = False
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # 检测表头行：包含 "X" 和其他列名（如 _temp_3）
            if not data_started:
                if "X" in line and ("temp" in line.lower() or "force" in line.lower()):
                    data_started = True
                    continue

            # 开始解析数据行
            if data_started:
                parts = re.split(r'[,\s\t]+', line_stripped)
                if len(parts) >= 2:
                    try:
                        disp_val = float(parts[0])
                        force_val = float(parts[1])
                        displacement.append(disp_val)
                        force.append(force_val)
                    except ValueError:
                        continue

    return {
        "sample_name": sample_name,
        "strength": strength,
        "sea": sea,
        "density": density,
        "volume": volume,
        "displacement": displacement,
        "force": force
    }

def extract_sample_name_from_path(file_path, root_path):
    """
    从文件路径中提取样本名称

    路径格式: root/BCC/4/0p4/0/static/feature_data.txt
    提取为: BCC_4_0p4_0

    Args:
        file_path: feature_data.txt的路径
        root_path: 根目录路径

    Returns:
        str: 样本名称
    """
    try:
        # 获取相对路径
        rel_path = file_path.relative_to(root_path)
        # 获取路径部分 (去掉最后的文件名和curve类型目录)
        # 例如: BCC/4/0p4/0/static/feature_data.txt -> BCC/4/0p4/0
        parts = rel_path.parts[:-2]  # 去掉 'static' 和 'feature_data.txt'
        # 组合为样本名称: BCC_4_0p4_0
        sample_name = '_'.join(parts)
        return sample_name
    except Exception as e:
        print(f"提取样本名称失败: {file_path}, 错误: {str(e)}")
        return None

def identify_curve_type(file_path):
    """
    识别曲线类型

    Args:
        file_path: feature_data.txt的路径

    Returns:
        str: 曲线类型 ('static_curve', 'static_X_curve', '50_curve', '500_curve', '50_X_curve', '500_X_curve')
             如果无法识别返回 None
    """
    # 获取包含feature_data.txt的目录名
    parent_dir = file_path.parent.name

    curve_type_map = {
        'static': 'static_curve',
        'X': 'static_X_curve',
        '50': '50_curve',
        '500': '500_curve',
        'X_50': '50_X_curve',
        'X_500': '500_X_curve'
    }

    return curve_type_map.get(parent_dir, None)

def collect_feature_data_to_json_advanced(root_folder, output_file="feature_data.json",
                                        encoding='utf-8', target_points=B,
                                        interpolation_method='cubic_spline'):
    """
    新版本的feature_data收集函数
    将同一样本的6种曲线类型整合到一起

    Args:
        root_folder: 根文件夹路径
        output_file: 输出JSON文件名
        encoding: 文件编码
        target_points: 目标插值点数
        interpolation_method: 插值方法
    """

    result = {}
    root_path = Path(root_folder)

    # 查找所有feature_data.txt文件
    all_feature_files = list(root_path.rglob("feature_data.txt"))
    print(f"找到 {len(all_feature_files)} 个feature_data.txt文件")

    # 按样本分组
    sample_curve_map = {}  # {sample_name: {curve_type: file_path}}

    print("正在扫描文件并按样本分组...")
    for feature_file in all_feature_files:
        try:
            # 提取样本名称
            sample_name = extract_sample_name_from_path(feature_file, root_path)
            if not sample_name:
                continue

            # 识别曲线类型
            curve_type = identify_curve_type(feature_file)
            if not curve_type:
                print(f"无法识别曲线类型: {feature_file.relative_to(root_path)}")
                continue

            # 添加到分组
            if sample_name not in sample_curve_map:
                sample_curve_map[sample_name] = {}

            sample_curve_map[sample_name][curve_type] = feature_file

        except Exception as e:
            print(f"扫描文件 {feature_file} 时出错: {str(e)}")

    print(f"扫描完成，发现 {len(sample_curve_map)} 个唯一样本")
    print("-" * 50)

    # 对样本进行排序
    print("正在对样本进行排序...")
    sorted_sample_names = sorted(sample_curve_map.keys(),
                                 key=lambda x: parse_sample_name_for_sorting(x))
    print(f"排序完成，共 {len(sorted_sample_names)} 个样本")

    # 显示排序后的前几个样本
    if sorted_sample_names:
        print("排序后的前几个样本:")
        for i, sample_name in enumerate(sorted_sample_names[:5]):
            curves = list(sample_curve_map[sample_name].keys())
            print(f"  {i+1}. {sample_name} (包含 {len(curves)} 种曲线: {', '.join(curves)})")
        if len(sorted_sample_names) > 5:
            print(f"  ... 还有 {len(sorted_sample_names) - 5} 个样本")
    print("-" * 50)

    # 处理每个样本
    print("开始处理样本数据...")
    for sample_name in sorted_sample_names:
        try:
            curve_files = sample_curve_map[sample_name]
            sample_data = {}
            density_value = None

            # 定义曲线类型的顺序
            curve_types = ['static_curve', 'static_X_curve', '50_curve', '500_curve', '50_X_curve', '500_X_curve']

            # 处理每种曲线类型
            for curve_type in curve_types:
                if curve_type in curve_files:
                    feature_file = curve_files[curve_type]

                    # 读取并解析文件
                    content = feature_file.read_text(encoding=encoding, errors='ignore')
                    parsed_data = parse_feature_data_advanced(content)

                    displacement = parsed_data["displacement"]
                    force = parsed_data["force"]

                    # 保存第一个文件的density
                    if density_value is None and parsed_data["density"] is not None:
                        density_value = parsed_data["density"]

                    # 处理X值重复的情况
                    if len(displacement) > 1:
                        disp_interp, force_interp, process_info = advanced_interpolation(
                            displacement, force, target_points, interpolation_method
                        )
                        print(f"{sample_name} - {curve_type}: {process_info}")
                    else:
                        disp_interp, force_interp = displacement, force
                        print(f"{sample_name} - {curve_type}: {len(displacement)} 点（数据不足）")

                    # 添加曲线数据
                    sample_data[curve_type] = {
                        "displacement": disp_interp,
                        "force": force_interp
                    }
                else:
                    # 曲线类型缺失，设为null
                    sample_data[curve_type] = None
                    print(f"{sample_name} - {curve_type}: 缺失")

            # 添加density到样本数据
            sample_data["density"] = density_value

            # 保存到结果
            result[sample_name] = sample_data
            print(f"已完成: {sample_name}")
            print("-" * 30)

        except Exception as e:
            print(f"处理样本 {sample_name} 时出错: {str(e)}")

    # 保存为JSON文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 自定义格式化以确保数组在同一行
            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            # 将数组格式化为单行
            import re
            # 匹配displacement和force数组，使其在一行显示
            for field in ["displacement", "force"]:
                pattern = rf'("{field}":\s*\[)\s*\n\s*(.*?)\s*\n\s*(\])'
                json_str = re.sub(pattern,
                                lambda m: m.group(1) + ' ' + re.sub(r'\s*\n\s*', ', ', m.group(2).strip()) + ' ' + m.group(3),
                                json_str, flags=re.DOTALL)
            # 清理可能产生的双逗号
            json_str = re.sub(r',\s*,', ',', json_str)
            f.write(json_str)
        print(f"\n成功保存到: {output_file}")
        print(f"总共处理了 {len(result)} 个样本")

        # 输出统计信息
        if result:
            print(f"\n=== 处理统计 ===")
            print(f"总样本数: {len(result)}")
            curve_stats = {ct: 0 for ct in ['static_curve', 'static_X_curve', '50_curve', '500_curve', '50_X_curve', '500_X_curve']}
            for sample_data in result.values():
                for curve_type in curve_stats.keys():
                    if sample_data.get(curve_type) is not None:
                        curve_stats[curve_type] += 1
            print("各曲线类型数量:")
            for curve_type, count in curve_stats.items():
                print(f"  {curve_type}: {count}")

    except Exception as e:
        print(f"保存JSON文件时出错: {str(e)}")

# 简化调用函数
def optimize_interpolation(folder_path=".", output_file="feature_data.json",
                          target_points=B, method='cubic_spline'):
    """
    优化插值的简化调用函数

    Args:
        folder_path: 文件夹路径
        output_file: 输出文件名
        target_points: 目标点数
        method: 插值方法 ('linear', 'cubic', 'cubic_spline', 'smooth_spline')
    """
    collect_feature_data_to_json_advanced(
        folder_path,
        output_file,
        target_points=target_points,
        interpolation_method=method
    )

# 使用示例
if __name__ == "__main__":
    print("=== 数据收集与清理器 ===")
    print("功能: 收集所有feature_data.txt中的数据")
    print("处理: 当X值连续相同时，保留Y值最接近均值的点")
    print("=" * 50)

    
    folder_path = "generate_script"

    print(f"\n开始处理...")
    print(f"输入路径: {os.path.abspath(folder_path)}")
    print(f"处理方式: X值重复去重（保留Y值最稳定的点）")
    print("=" * 50)

    # 处理所有数据（新格式：6种曲线整合到一起）
    print("\n收集所有样本数据...")
    print("-" * 50)
    optimize_interpolation(folder_path, "feature_data.json", B, 'cubic_spline')

    print("\n" + "=" * 50)
    print("\n✓ 全部完成！")
    print(f"  - 数据已保存到: feature_data.json")
    print(f"  - 已处理X值重复的数据点")