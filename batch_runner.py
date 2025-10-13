# -*- coding: utf-8 -*-
"""
批量作业调度器
优化的两阶段执行策略，最小化CAE license占用并避免ODB堆积

使用方法:
1. 使用UI生成多个前处理和后处理脚本
2. 运行此脚本: python batch_runner.py
3. 执行策略：
   Phase 1: 批量运行所有前处理（连续执行，快速释放CAE）
   Phase 2: 逐个提交求解并后处理（求解完立即处理ODB，避免堆积）
"""

import subprocess
import os
import time
from glob import glob
import sys

def find_all_jobs(base_dir="generate_script"):
    """查找所有作业（前处理脚本）"""
    preprocess_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('_preprocess.py'):
                preprocess_files.append(os.path.join(root, file))

    jobs = []
    for pf in preprocess_files:
        postprocess_file = pf.replace('_preprocess.py', '_postprocess.py')
        if os.path.exists(postprocess_file):
            jobs.append({
                'preprocess': pf,
                'postprocess': postprocess_file,
                'dir': os.path.dirname(pf),
                'job_name': os.path.basename(pf).replace('_preprocess.py', '')
            })

    return jobs


def run_batch_preprocessing(jobs):
    """Phase 1: 批量运行所有前处理脚本"""
    print("\n" + "=" * 80)
    print("Phase 1: 批量运行前处理脚本（生成.inp文件）")
    print("=" * 80)

    if not jobs:
        print("没有作业需要处理")
        return []

    print(f"找到 {len(jobs)} 个前处理脚本\n")

    successful_jobs = []
    for i, job in enumerate(jobs, 1):
        job_name = job['job_name']
        script_dir = job['dir']
        preprocess_script = os.path.basename(job['preprocess'])

        print(f"[{i}/{len(jobs)}] 运行前处理: {job_name}")
        try:
            result = subprocess.call(
                ['abaqus', 'cae', f'noGUI={preprocess_script}'],
                cwd=script_dir
            )

            if result == 0:
                inp_file = os.path.join(script_dir, f"{job_name}.inp")
                if os.path.exists(inp_file):
                    print(f"✓ 前处理成功")
                    successful_jobs.append(job)
                else:
                    print(f"✗ 前处理完成但未找到.inp文件")
            else:
                print(f"✗ 前处理失败 (错误码: {result})")

        except Exception as e:
            print(f"✗ 前处理出错: {e}")

    print(f"\n成功完成 {len(successful_jobs)}/{len(jobs)} 个前处理")
    return successful_jobs


def run_solve_and_postprocess(job, job_index, total_jobs, check_interval=30):
    """Phase 2: 提交求解器 → 等待完成 → 立即后处理"""
    job_name = job['job_name']
    script_dir = job['dir']

    print("\n" + "=" * 80)
    print(f"[{job_index}/{total_jobs}] 处理任务: {job_name}")
    print("=" * 80)

    # 提交求解器
    print(f"\n提交求解器...")
    try:
        solver_process = subprocess.Popen(
            ['abaqus', f'job={job_name}', f'input={job_name}.inp', 'cpus=8', 'interactive'],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✓ 已提交求解器 (PID: {solver_process.pid})")
    except Exception as e:
        print(f"✗ 求解器提交失败: {e}")
        return False

    # 等待求解完成
    print(f"等待求解完成 (检查间隔: {check_interval}秒)...")
    start_time = time.time()

    while True:
        time.sleep(check_interval)

        lck_file = os.path.join(script_dir, f"{job_name}.lck")
        odb_file = os.path.join(script_dir, f"{job_name}.odb")

        # 如果ODB存在且.lck不存在，说明计算完成
        if os.path.exists(odb_file) and not os.path.exists(lck_file):
            elapsed = time.time() - start_time
            print(f"✓ 求解完成 (用时: {elapsed/60:.1f}分钟)")
            break

        # 检查进程是否异常退出
        if solver_process.poll() is not None and not os.path.exists(odb_file):
            print(f"✗ 求解器异常退出 (退出码: {solver_process.poll()})")
            return False

        elapsed = time.time() - start_time
        print(f"  求解中... (已用时: {elapsed/60:.1f}分钟)")

    # 立即运行后处理（处理ODB，避免堆积）
    print(f"\n运行后处理...")
    try:
        postprocess_script = os.path.basename(job['postprocess'])
        result = subprocess.call(
            ['abaqus', 'cae', f'noGUI={postprocess_script}'],
            cwd=script_dir
        )

        if result == 0:
            print(f"✓ 后处理完成")
        else:
            print(f"✗ 后处理失败 (错误码: {result})")
            return False

    except Exception as e:
        print(f"✗ 后处理出错: {e}")
        return False

    total_time = time.time() - start_time
    print(f"✓ 任务完成 (总用时: {total_time/60:.1f}分钟)")
    return True


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   Abaqus 批量作业调度器 - 两阶段执行，避免ODB堆积           ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # 检查是否有generate_script目录
    if not os.path.exists("generate_script"):
        print("错误: 未找到 generate_script 目录")
        print("请先使用UI生成脚本后再运行此调度器")
        return

    try:
        overall_start = time.time()

        # 查找所有作业
        all_jobs = find_all_jobs()

        if not all_jobs:
            print("未找到任何作业脚本！")
            return

        print(f"\n找到 {len(all_jobs)} 个作业")
        print("执行策略: Phase 1批量前处理 → Phase 2逐个求解并后处理")

        # Phase 1: 批量运行所有前处理
        successful_jobs = run_batch_preprocessing(all_jobs)

        if not successful_jobs:
            print("\n所有前处理均失败，退出")
            return

        # Phase 2: 逐个提交求解器并后处理
        print("\n" + "=" * 80)
        print("Phase 2: 逐个求解并后处理（避免ODB堆积）")
        print("=" * 80)

        success_count = 0
        failed_jobs = []

        for i, job in enumerate(successful_jobs, 1):
            if run_solve_and_postprocess(job, i, len(successful_jobs)):
                success_count += 1
            else:
                failed_jobs.append(job['job_name'])

        # 总结
        overall_time = time.time() - overall_start
        print("\n" + "=" * 80)
        print(f"所有任务完成！")
        print(f"成功: {success_count}/{len(successful_jobs)}")
        if failed_jobs:
            print(f"失败任务: {', '.join(failed_jobs)}")
        print(f"总用时: {overall_time/60:.1f}分钟")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
