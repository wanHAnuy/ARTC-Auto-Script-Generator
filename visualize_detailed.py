import matplotlib.pyplot as plt
import numpy as np
import json

# 读取 feature_data.json
print("读取 feature_data.json...")
with open('feature_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取第一个样本
first_sample_name = list(data.keys())[1]
sample_data = data[first_sample_name]

print(f"\n{'='*70}")
print(f"样本名称: {first_sample_name}")
print(f"密度 (Density): {sample_data.get('density')}")
print(f"{'='*70}")

# 定义6种曲线类型
curve_types = ['static_curve', 'static_X_curve', '50_curve', '500_curve', '50_X_curve', '500_X_curve']
curve_titles = [
    'Static Curve (Y-direction)',
    'Static X Curve (X-direction)',
    '50 mm/s Speed Curve (Y-direction)',
    '500 mm/s Speed Curve (Y-direction)',
    '50 mm/s Speed X Curve (X-direction)',
    '500 mm/s Speed X Curve (X-direction)'
]

# 创建 3x2 的子图布局
fig, axes = plt.subplots(3, 2, figsize=(18, 20))
fig.suptitle(f'Force-Displacement Analysis: {first_sample_name}\nDensity: {sample_data.get("density"):.6f}',
             fontsize=18, fontweight='bold', y=0.996)

# 颜色方案
colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e', '#9467bd', '#8c564b']

# 统计信息收集
stats_summary = []

# 绘制每种曲线
for idx, (curve_type, title, color) in enumerate(zip(curve_types, curve_titles, colors)):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]

    # 获取曲线数据
    curve_data = sample_data.get(curve_type)

    if curve_data and curve_data is not None:
        displacement = curve_data.get('displacement', [])
        force = curve_data.get('force', [])

        if displacement and force and len(displacement) > 0:
            # 绘制力-位移曲线
            ax.plot(displacement, force, color=color, linewidth=2.5, label='F-D Curve')

            # 计算统计信息
            max_force = max(force)
            max_idx = force.index(max_force)
            max_disp = displacement[max_idx]
            min_force = min(force)
            avg_force = np.mean(force)

            # 标注峰值
            ax.plot(max_disp, max_force, 'ro', markersize=10, label=f'Peak: {max_force:.2f}N')
            ax.annotate(f'Peak Force\n{max_force:.3f} N',
                       xy=(max_disp, max_force),
                       xytext=(15, 15), textcoords='offset points',
                       fontsize=8, color='red', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8, edgecolor='red', linewidth=2),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2))

            # 标注起点和终点
            ax.plot(displacement[0], force[0], 'go', markersize=8, label=f'Start')
            ax.plot(displacement[-1], force[-1], 'bs', markersize=8, label=f'End')

            # 添加统计文本框
            stats_text = f'Points: {len(displacement)}\n'
            stats_text += f'Disp Range: [{min(displacement):.4f}, {max(displacement):.4f}]\n'
            stats_text += f'Force Range: [{min_force:.3f}, {max_force:.3f}]\n'
            stats_text += f'Avg Force: {avg_force:.3f}'

            ax.text(0.02, 0.98, stats_text,
                   transform=ax.transAxes,
                   fontsize=9,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            # 保存统计信息
            stats_summary.append({
                'type': title,
                'points': len(displacement),
                'disp_range': (min(displacement), max(displacement)),
                'force_range': (min_force, max_force),
                'peak_force': max_force,
                'peak_disp': max_disp,
                'avg_force': avg_force
            })

            # 打印控制台信息
            print(f"\n{title}:")
            print(f"  数据点数: {len(displacement)}")
            print(f"  位移范围: [{min(displacement):.6f}, {max(displacement):.6f}] mm")
            print(f"  力范围: [{min_force:.4f}, {max_force:.4f}] N")
            print(f"  峰值力: {max_force:.4f} N @ 位移 {max_disp:.6f} mm")
            print(f"  平均力: {avg_force:.4f} N")

        else:
            ax.text(0.5, 0.5, 'No Data\n(Empty Arrays)', ha='center', va='center',
                   fontsize=8, color='gray', transform=ax.transAxes,
                   bbox=dict(boxstyle='round,pad=1', facecolor='lightgray', alpha=0.5))
            print(f"\n{title}: 无数据（空数组）")
            stats_summary.append({'type': title, 'status': 'Empty'})
    else:
        ax.text(0.5, 0.5, 'NULL\n(Missing Data)', ha='center', va='center',
               fontsize=8, color='red', transform=ax.transAxes,
               bbox=dict(boxstyle='round,pad=1', facecolor='mistyrose', alpha=0.5))
        print(f"\n{title}: NULL (缺失)")
        stats_summary.append({'type': title, 'status': 'NULL'})

    # 设置标签和标题
    ax.set_xlabel('Displacement (mm)', fontsize=8, fontweight='bold')
    ax.set_ylabel('Force (N)', fontsize=8, fontweight='bold')
    ax.set_title(title, fontsize=8, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8)
    if curve_data and displacement and force and len(displacement) > 0:
        ax.legend(loc='best', fontsize=6, framealpha=0.9)

plt.tight_layout()

# 保存图片
output_filename = f'{first_sample_name}_detailed_curves.png'
plt.savefig(output_filename, dpi=300, bbox_inches='tight')

print(f"\n{'='*70}")
print(f"图表已保存为: {output_filename}")
print(f"{'='*70}")

# 打印汇总统计
print(f"\n{'='*70}")
print("统计汇总:")
print(f"{'='*70}")
for stat in stats_summary:
    if 'status' in stat:
        print(f"{stat['type']}: {stat['status']}")
    else:
        print(f"{stat['type']}:")
        print(f"  峰值力: {stat['peak_force']:.4f} N")

plt.show()
