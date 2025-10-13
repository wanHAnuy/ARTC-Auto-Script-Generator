#!/usr/bin/env python3
"""
配置文件 - 集中管理所有硬编码的配置参数
"""
import os


class Config:
    """应用配置类"""

    # ========== 文件和路径配置 ==========
    FEATURE_FILE_MIN_SIZE = int(os.getenv('MIN_FILE_SIZE', 2000))  # 特征文件最小大小(字节)
    GENERATE_SCRIPT_DIR = "generate_script"  # 生成脚本的目录名
    LOG_DIR = os.getenv('LOG_DIR', "logs")  # PBS/SLURM 日志文件目录

    BASE_SCRIPT_PATH = os.getenv('BASE_SCRIPT_PATH', "/home/haoyu.wang/ARTC_Database_final/generate_script")  # 集群上脚本基础路径

    # ========== 集群调度系统类型 ==========
    SCHEDULER_TYPE = os.getenv('SCHEDULER_TYPE', "PBS")  # 调度系统类型: PBS 或 SLURM

    # ========== PBS 集群配置 ==========
    PBS_QUEUE = os.getenv('PBS_QUEUE', "qintel_wfly")  # PBS队列名
    PBS_NODES = int(os.getenv('PBS_NODES', 1))  # 节点数
    PBS_NCPUS = int(os.getenv('PBS_NCPUS', 8))  # CPU核心数
    PBS_MEMORY = os.getenv('PBS_MEM', "64gb")  # 内存大小
    PBS_WALLTIME = os.getenv('PBS_WALLTIME', "168:00:00")  # 作业时间限制

    # ========== SLURM 集群配置 ==========
    SLURM_TIME_LIMIT = os.getenv('SLURM_TIME', "72:00:00")  # 作业时间限制
    SLURM_PARTITION = os.getenv('SLURM_PARTITION', "default")  # 分区名
    SLURM_NODES = int(os.getenv('SLURM_NODES', 1))  # 节点数
    SLURM_NTASKS = int(os.getenv('SLURM_NTASKS', 1))  # 任务数
    SLURM_CPUS_PER_TASK = int(os.getenv('SLURM_CPUS', 8))  # 每个任务的CPU数
    SLURM_MEMORY = os.getenv('SLURM_MEM', "64G")  # 内存大小

    # ========== Abaqus 配置 ==========
    ABAQUS_MODULE = os.getenv('ABAQUS_MODULE', "abaqus")  # Abaqus模块名
    ABAQUS_COMMAND = os.getenv('ABAQUS_CMD', "abaqus cae noGUI")  # Abaqus执行命令

    # ========== 脚本生成配置 ==========
    BASE_CELL_SIZE = float(os.getenv('BASE_CELL_SIZE', 5.0))  # 基础晶胞尺寸
    DEFAULT_SLIDER_VALUE = int(os.getenv('DEFAULT_SLIDER', 4))  # 默认滑块值
    SLIDER_RANGE = (0, 9)  # 滑块范围

    # ========== 数据处理配置 ==========
    INTERPOLATION_POINTS = int(os.getenv('INTERP_POINTS', 100))  # 插值点数
    MIN_DATA_FILE_SIZE = int(os.getenv('MIN_DATA_SIZE', 1000))  # 最小数据文件大小

    # ========== UI 配置 ==========
    VISUALIZATION_UPDATE_INTERVAL = int(os.getenv('VIS_UPDATE_MS', 1000))  # 可视化更新间隔(毫秒)
    FORCE_REFRESH_DELAY = int(os.getenv('REFRESH_DELAY_MS', 1000))  # 强制刷新延迟(毫秒)

    # ========== 日志配置 ==========
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # 日志级别
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')  # 日志文件

    # ========== 无slider功能的cell types ==========
    NO_SLIDER_CELL_TYPES = ["Cubic", "Octahedron"]

    # ========== Cell Type 分组 ==========
    CELL_TYPE_GROUPS = [
        ("Group 1", ["Cubic", "BCC", "BCCZ", "Octet_truss", "AFCC", "Truncated_cube", "FCC",
                     "FCCZ", "Tetrahedron_base", "Iso_truss", "G7", "FBCCZ", "FBCCXYZ",
                     "Cuboctahedron_Z", "Diamond", "Rhombic", "Kelvin", "Auxetic",
                     "Octahedron", "Truncated_Octoctahedron"])
    ]

    @classmethod
    def get_pbs_header(cls):
        """获取PBS作业头部配置"""
        return {
            'queue': cls.PBS_QUEUE,
            'nodes': cls.PBS_NODES,
            'ncpus': cls.PBS_NCPUS,
            'memory': cls.PBS_MEMORY,
            'walltime': cls.PBS_WALLTIME
        }

    @classmethod
    def get_slurm_header(cls):
        """获取SLURM作业头部配置"""
        return {
            'time': cls.SLURM_TIME_LIMIT,
            'partition': cls.SLURM_PARTITION,
            'nodes': cls.SLURM_NODES,
            'ntasks': cls.SLURM_NTASKS,
            'cpus_per_task': cls.SLURM_CPUS_PER_TASK,
            'memory': cls.SLURM_MEMORY
        }

    @classmethod
    def validate(cls):
        """验证配置参数"""
        assert cls.FEATURE_FILE_MIN_SIZE > 0, "FEATURE_FILE_MIN_SIZE must be positive"
        assert cls.BASE_CELL_SIZE > 0, "BASE_CELL_SIZE must be positive"

        if cls.SCHEDULER_TYPE == "PBS":
            assert cls.PBS_NODES > 0, "PBS_NODES must be positive"
            assert cls.PBS_NCPUS > 0, "PBS_NCPUS must be positive"
        elif cls.SCHEDULER_TYPE == "SLURM":
            assert cls.SLURM_NODES > 0, "SLURM_NODES must be positive"
            assert cls.SLURM_CPUS_PER_TASK > 0, "SLURM_CPUS_PER_TASK must be positive"

        return True


# 在导入时验证配置
Config.validate()
