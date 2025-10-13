from abaqus import *
from abaqusConstants import *
import numpy as np
from math import acos, degrees
from numpy.linalg import norm
from numpy import cross, dot
import regionToolset

# 圆柱体半径
radius = 0.3
cell_size = 5
# 定义关键点坐标
A  = [-2.5,  2.5,  2.5]
B  = [ 2.5,  2.5,  2.5]
C  = [ 2.5, -2.5,  2.5]
D  = [-2.5, -2.5,  2.5]
A_ = [-2.5,  2.5, -2.5]
B_ = [ 2.5,  2.5, -2.5]
C_ = [ 2.5, -2.5, -2.5]
D_ = [-2.5, -2.5, -2.5]
O  = [ 0, 0, 0]

# 定义圆柱体连接
cylinders = [
    (O, A), (O, B), (O, C), (O, D),
    (O, A_), (O, B_), (O, C_), (O, D_),
    (B, C), (D, A),
    (B_, C_), (D_, A_)
]

model = mdb.models['Model-1']
assembly = model.rootAssembly
inst_list = []

# 创建圆柱体
for i, (start, end) in enumerate(cylinders):
    start = np.array(start)
    end = np.array(end)
    vec = end - start
    length = norm(vec)
    direction = vec / length

    sketch = model.ConstrainedSketch(name='circleSketch-%02d' % (i+1), sheetSize=20.0)
    sketch.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(radius, 0.0))

    part_name = 'Cyl-%02d' % (i+1)
    part = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    part.BaseSolidExtrude(sketch=sketch, depth=length)

    inst_name = 'Inst-%02d' % (i+1)
    assembly.Instance(name=inst_name, part=part, dependent=ON)
    assembly.translate(instanceList=(inst_name,), vector=tuple(start))

    z_axis = np.array([0, 0, 1])
    rot_axis = cross(z_axis, direction)
    dot_product = dot(z_axis, direction)

    if norm(rot_axis) < 1e-6:
        if dot_product < 0:
            assembly.rotate(instanceList=(inst_name,),
                            axisPoint=tuple(start),
                            axisDirection=(1, 0, 0),
                            angle=180)
    else:
        angle = degrees(acos(dot_product))
        assembly.rotate(instanceList=(inst_name,),
                        axisPoint=tuple(start),
                        axisDirection=tuple(rot_axis),
                        angle=angle)

    inst_list.append(assembly.instances[inst_name])

# 合并几何体
merged_part = assembly.InstanceFromBooleanMerge(
    name='MergedStructure',
    instances=inst_list,
    keepIntersections=OFF,
    originalInstances=DELETE,
    domain=GEOMETRY
)

# 获取合并后的零件
p = model.parts['MergedStructure']

# 创建基准轴
datum_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
up_edge_id = datum_axis.id

# 创建顶部切割平面 (Z = +2.5位置)
datum_top = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=3)
datum_top_id = datum_top.id

# 创建顶部切割草图
t1 = p.MakeSketchTransform(sketchPlane=p.datums[datum_top_id], 
                          sketchUpEdge=p.datums[up_edge_id], 
                          sketchPlaneSide=SIDE1, 
                          sketchOrientation=RIGHT, 
                          origin=(0.0, 0.0, 2.5))

s1 = model.ConstrainedSketch(name='cutTopSketch', sheetSize=20.0, transform=t1)
s1.setPrimaryObject(option=SUPERIMPOSE)
p.projectReferencesOntoSketch(sketch=s1, filter=COPLANAR_EDGES)

# 创建切割用的矩形
s1.rectangle(point1=(-2.5, -2.5), point2=(2.5, 2.5))
s1.rectangle(point1=(-5.0, -5.0), point2=(5.0, 5.0))

# 执行顶部切割
# 修正后的顶部切割
p.CutExtrude(sketchPlane=p.datums[datum_top_id], 
            sketchUpEdge=p.datums[up_edge_id], 
            sketchPlaneSide=SIDE1, 
            sketchOrientation=RIGHT, 
            sketch=s1, 
            depth=6,  # 向下切割2.5单位
            flipExtrudeDirection=OFF)

s1.unsetPrimaryObject()
del model.sketches['cutTopSketch']

# 创建侧面切割平面 (Y = +2.5位置)
datum_side = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=3)
datum_side_id = datum_side.id

# 创建侧面基准轴
datum_axis2 = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
side_edge_id = datum_axis2.id

# 创建侧面切割草图
t2 = p.MakeSketchTransform(sketchPlane=p.datums[datum_side_id], 
                          sketchUpEdge=p.datums[side_edge_id], 
                          sketchPlaneSide=SIDE1, 
                          sketchOrientation=RIGHT, 
                          origin=(0.0, 2.5, 0.0))

s2 = model.ConstrainedSketch(name='cutSideSketch', sheetSize=20.0, transform=t2)
s2.setPrimaryObject(option=SUPERIMPOSE)
p.projectReferencesOntoSketch(sketch=s2, filter=COPLANAR_EDGES)

# 复制之前的矩形形状
s2.rectangle(point1=(-2.5, -2.5), point2=(2.5, 2.5))
s2.rectangle(point1=(-5.0, -5.0), point2=(5.0, 5.0))

# 执行侧面切割
p.CutExtrude(sketchPlane=p.datums[datum_side_id], 
            sketchUpEdge=p.datums[side_edge_id], 
            sketchPlaneSide=SIDE1, 
            sketchOrientation=RIGHT, 
            sketch=s2, 
            depth=6,  # 向内切割2.5单位
            flipExtrudeDirection=OFF)

s2.unsetPrimaryObject()
del model.sketches['cutSideSketch']

# 创建刚性板
s3 = model.ConstrainedSketch(name='rigidPlateSketch', sheetSize=20.0)
s3.setPrimaryObject(option=STANDALONE)
s3.Line(point1=(-3.0, 0.0), point2=(3.0, 0.0))
s3.HorizontalConstraint(entity=s3.geometry[2], addUndoState=False)

rigid_part = model.Part(name='RigidPlate', 
                       dimensionality=THREE_D, 
                       type=DISCRETE_RIGID_SURFACE)

rigid_part.BaseShellExtrude(sketch=s3, depth=6.0)
s3.unsetPrimaryObject()
del model.sketches['rigidPlateSketch']

# 创建刚性板实例
assembly.DatumCsysByDefault(CARTESIAN)
assembly.Instance(name='RigidPlate-1', part=rigid_part, dependent=ON)
assembly.translate(instanceList=('RigidPlate-1',), vector=(0.0, -2.5, -3.0))

assembly.Instance(name='RigidPlate-2', part=rigid_part, dependent=ON)
assembly.translate(instanceList=('RigidPlate-2',), vector=(0.0, 2.5, -3.0))

# 创建材料
material = model.Material(name='Material-1')
material.Elastic(table=((933.5, 0.3),))
material.Plastic(scaleStress=None, table=((16.552, 0.0), (20.193, 0.00269), (21.535, 0.005)))
material.Density(table=((1.2e-09,),))
material.DuctileDamageInitiation(table=((0.95, 0.333, 0.003),))
material.ductileDamageInitiation.DamageEvolution(type=DISPLACEMENT, table=((0.1,),))

# 创建截面
model.HomogeneousSolidSection(name='Section-1', material='Material-1', thickness=None)
model.HomogeneousShellSection(name='Section-2', 
                             preIntegrate=OFF, 
                             material='Material-1', 
                             thicknessType=UNIFORM, 
                             thickness=0.05, 
                             thicknessField='', 
                             nodalThicknessField='', 
                             idealization=NO_IDEALIZATION, 
                             poissonDefinition=DEFAULT, 
                             thicknessModulus=None, 
                             temperature=GRADIENT, 
                             useDensity=OFF, 
                             integrationRule=SIMPSON, 
                             numIntPts=5)

# 为刚性板分配截面属性
rigid_part = model.parts['RigidPlate']
f = rigid_part.faces
faces = f.getSequenceFromMask(mask=('[#1]',),)
region = regionToolset.Region(faces=faces)
rigid_part.SectionAssignment(region=region, 
                            sectionName='Section-2', 
                            offset=0.0, 
                            offsetType=MIDDLE_SURFACE, 
                            offsetField='', 
                            thicknessAssignment=FROM_SECTION)

# 为主结构分配截面属性
main_part = model.parts['MergedStructure']
c = main_part.cells
cells = c.getSequenceFromMask(mask=('[#1]',),)
region = regionToolset.Region(cells=cells)
main_part.SectionAssignment(region=region, 
                           sectionName='Section-1', 
                           offset=0.0, 
                           offsetType=MIDDLE_SURFACE, 
                           offsetField='', 
                           thicknessAssignment=FROM_SECTION)

# 重新生成装配体
assembly.regenerate()

print("Model creation completed successfully!")



# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import __main__
import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import optimization
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior


def Macro1():

    # === 刚体板参考点 + 质量 ===
    p = mdb.models['Model-1'].parts['RigidPlate']
    v, e, d, n = p.vertices, p.edges, p.datums, p.nodes
    p.ReferencePoint(point=v[1])
    r = p.referencePoints
    refPoints = (r[3], )
    region = p.Set(referencePoints=refPoints, name='RefPlateSet')
    mdb.models['Model-1'].parts['RigidPlate'].engineeringFeatures.PointMassInertia(
        name='Inertia-1', region=region, mass=8.45e-07, alpha=0.0, 
        composite=0.0)

    a = mdb.models['Model-1'].rootAssembly
    a.regenerate()

    # === 分析步 ===
    # mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial', 
    #     initialInc=0.01, minInc=1e-06, nlgeom=ON,maxNumInc=300, )
    # === 关键修改：分析步设置 ===
    mdb.models['Model-1'].StaticStep(
        name='Step-1',
        previous='Initial',
        initialInc=0.02,         # 源代码：0.01 → 增大初始增量，避免过小步长
        minInc=5e-07,           # 源代码：1e-08 → 提高最小增量下限，防止死循环
        maxInc=0.02,            # 源代码：0.01 → 增大最大增量
        maxNumInc=500,          # 源代码：300 → 增加最大步数，应对复杂变形
        nlgeom=ON,
        stabilizationMethod=DAMPING_FACTOR,
        stabilizationMagnitude=0.0004,  # 源代码：0.0002 → 增大阻尼，抑制振荡
        continueDampingFactors=False,
        adaptiveDampingRatio=0.05       # 新增：自适应阻尼
    )

    # === 定义反射点集 ===
    # 自动选择Y最大面上X、Z都最大的顶点
    v1 = a.instances['MergedStructure-1'].vertices
    max_y = -999999.0

    # 第一步：找到最大Y坐标
    for v in v1:
        coord = v.pointOn[0]
        if coord[1] > max_y:
            max_y = coord[1]

    # 第二步：筛选Y坐标接近最大值的所有顶点（容差0.01）
    top_verts = []
    for v in v1:
        coord = v.pointOn[0]
        if abs(coord[1] - max_y) < 0.01:
            top_verts.append(v)

    # 第三步：在这些顶点中找到X和Z都最大的
    if top_verts:
        max_x = max([v.pointOn[0][0] for v in top_verts])
        max_z = max([v.pointOn[0][2] for v in top_verts])

        # 找到同时满足X和Z最大的顶点（容差0.01）
        target_vert = None
        for v in top_verts:
            coord = v.pointOn[0]
            if abs(coord[0] - max_x) < 0.01 and abs(coord[2] - max_z) < 0.01:
                target_vert = v
                break

        if target_vert:
            # 使用findAt通过坐标重新获取vertex（返回Abaqus序列对象）
            coord = target_vert.pointOn[0]
            verts1 = v1.findAt((coord,))
            a.Set(vertices=(verts1,), name='Reflection')
            print("Selected Reflection vertex at: (%f, %f, %f)" % coord)
        else:
            # 兜底：选择第一个顶部顶点
            coord = top_verts[0].pointOn[0]
            verts1 = v1.findAt((coord,))
            a.Set(vertices=(verts1,), name='Reflection')
            print("Fallback: Selected first top vertex at: (%f, %f, %f)" % coord)
    else:
        raise ValueError("Cannot find top vertices in MergedStructure-1")

    # BotReflection
    r1 = a.instances['RigidPlate-1'].referencePoints
    refPoints1 = (r1[3], )
    a.Set(referencePoints=refPoints1, name='BotReflection')

    # TopReflection
    r1 = a.instances['RigidPlate-2'].referencePoints
    refPoints1 = (r1[3], )
    a.Set(referencePoints=refPoints1, name='TopReflection')

    # === 输出请求 ===
    regionDef = a.sets['Reflection']
    mdb.models['Model-1'].HistoryOutputRequest(name='H-Output-2', 
        createStepName='Step-1', variables=('U1', 'U2', 'RF1','RF2'), 
        region=regionDef, sectionPoints=DEFAULT, rebar=EXCLUDE)

    regionDef = a.sets['BotReflection']
    mdb.models['Model-1'].HistoryOutputRequest(name='H-Output-3', 
        createStepName='Step-1', variables=('U1', 'U2', 'RF1','RF2'), 
        region=regionDef, sectionPoints=DEFAULT, rebar=EXCLUDE)

    regionDef = a.sets['TopReflection']
    mdb.models['Model-1'].HistoryOutputRequest(name='H-Output-4', 
        createStepName='Step-1', variables=('U1', 'U2', 'RF1','RF2'), 
        region=regionDef, sectionPoints=DEFAULT, rebar=EXCLUDE)

    # === Rigid body 约束 ===
    region2 = a.sets['TopReflection']
    r1 = a.instances['RigidPlate-2'].referencePoints
    refPoints1 = (r1[3], )
    region1 = regionToolset.Region(referencePoints=refPoints1)
    mdb.models['Model-1'].RigidBody(name='Constraint-1', refPointRegion=region1, 
        bodyRegion=region2)

    region2 = a.sets['BotReflection']
    r1 = a.instances['RigidPlate-1'].referencePoints
    refPoints1 = (r1[3], )
    region1 = regionToolset.Region(referencePoints=refPoints1)
    mdb.models['Model-1'].RigidBody(name='Constraint-2', refPointRegion=region1, 
        bodyRegion=region2)

    # === 接触属性 ===
    mdb.models['Model-1'].ContactProperty('IntProp-1')
    mdb.models['Model-1'].interactionProperties['IntProp-1'].TangentialBehavior(
        formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, 
        pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, 
        table=((0.15, ), ), shearStressLimit=None, maximumElasticSlip=FRACTION, 
        fraction=0.005, elasticSlipStiffness=None)
    mdb.models['Model-1'].interactionProperties['IntProp-1'].NormalBehavior(
        pressureOverclosure=HARD, allowSeparation=ON, 
        constraintEnforcementMethod=DEFAULT)

    # === 接触对 ===
    s1 = a.instances['RigidPlate-2'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
    region1 = a.Surface(side1Faces=side1Faces1, name='m_Surf-1')

    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#2901000 ]', ), )
    region2 = a.Surface(side1Faces=side1Faces1, name='s_Surf-1')
    mdb.models['Model-1'].SurfaceToSurfaceContactStd(name='Int-1', 
        createStepName='Step-1', main=region1, secondary=region2, 
        sliding=FINITE, thickness=ON, interactionProperty='IntProp-1', 
        adjustMethod=NONE, initialClearance=OMIT, datumAxis=None, 
        clearanceRegion=None)

    s1 = a.instances['RigidPlate-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
    region1 = a.Surface(side1Faces=side1Faces1, name='m_Surf-3')

    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#4040c0 ]', ), )
    region2 = a.Surface(side1Faces=side1Faces1, name='s_Surf-3')
    mdb.models['Model-1'].SurfaceToSurfaceContactStd(name='Int-2', 
        createStepName='Step-1', main=region1, secondary=region2, 
        sliding=FINITE, thickness=ON, interactionProperty='IntProp-1', 
        adjustMethod=NONE, initialClearance=OMIT, datumAxis=None, 
        clearanceRegion=None)
    
    mdb.models['Model-1'].interactions['Int-1'].move('Step-1', 'Initial')
    mdb.models['Model-1'].interactions['Int-2'].move('Step-1', 'Initial')
    session.viewports['Viewport: 1'].assemblyDisplay.setValues(step='Step-1')

    a = mdb.models['Model-1'].rootAssembly
    a.regenerate()
    session.viewports['Viewport: 1'].assemblyDisplay.setValues(loads=OFF, bcs=OFF, 
        predefinedFields=OFF, connectors=OFF)
    a = mdb.models['Model-1'].rootAssembly
    s1 = a.instances['RigidPlate-1'].faces
    side2Faces1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
    a.Surface(side2Faces=side2Faces1, name='m_Surf-3')

    # === 约束条件 ===
    f1 = a.instances['RigidPlate-1'].faces
    faces1 = f1.getSequenceFromMask(mask=('[#1 ]', ), )
    region = a.Set(faces=faces1, name='Set-8')
    mdb.models['Model-1'].EncastreBC(name='BC-1', createStepName='Step-1', 
        region=region, localCsys=None)

    region = a.sets['TopReflection']
    mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Step-1', 
        region=region, u1=0.0, u2=-0.5, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0, 
        amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', 
        localCsys=None)
    mdb.models['Model-1'].TabularAmplitude(name='Amp-1', timeSpan=STEP, 
        smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (0.6, 1.0)))
    mdb.models['Model-1'].boundaryConditions['BC-2'].setValuesInStep(
        stepName='Step-1', amplitude='Amp-1')


    a = mdb.models['Model-1'].rootAssembly
    session.viewports['Viewport: 1'].setValues(displayedObject=a)
    session.viewports['Viewport: 1'].assemblyDisplay.setValues(loads=ON, bcs=ON, 
        predefinedFields=ON, connectors=ON, optimizationTasks=OFF, 
        geometricRestrictions=OFF, stopConditions=OFF)
    mdb.models['Model-1'].boundaryConditions['BC-2'].suppress()
    del mdb.models['Model-1'].boundaryConditions['BC-2']
    mdb.models['Model-1'].boundaryConditions['BC-1'].move('Step-1', 'Initial')
    a = mdb.models['Model-1'].rootAssembly
    r1 = a.instances['RigidPlate-2'].referencePoints
    refPoints1=(r1[3], )
    region = a.Set(referencePoints=refPoints1, name='Set-7')
    mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Initial', 
        region=region, u1=SET, u2=UNSET, u3=SET, ur1=SET, ur2=SET, ur3=SET, 
        amplitude=UNSET, distributionType=UNIFORM, fieldName='', 
        localCsys=None)
    session.viewports['Viewport: 1'].assemblyDisplay.setValues(step='Step-1')
    mdb.models['Model-1'].boundaryConditions['BC-2'].setValuesInStep(
        stepName='Step-1', u2=-0.5, amplitude='Amp-1')
    
    a = mdb.models['Model-1'].rootAssembly
    f1 = a.instances['RigidPlate-2'].faces
    faces1 = f1.getSequenceFromMask(mask=('[#1 ]', ), )
    region2=a.Set(faces=faces1, name='b_Set-8')
    a = mdb.models['Model-1'].rootAssembly
    r1 = a.instances['RigidPlate-2'].referencePoints
    refPoints1=(r1[3], )
    region1=regionToolset.Region(referencePoints=refPoints1)
    mdb.models['Model-1'].constraints['Constraint-1'].setValues(
        refPointRegion=region1, bodyRegion=region2)
    a = mdb.models['Model-1'].rootAssembly
    f1 = a.instances['RigidPlate-1'].faces
    faces1 = f1.getSequenceFromMask(mask=('[#1 ]', ), )
    region2=a.Set(faces=faces1, name='b_Set-9')
    a = mdb.models['Model-1'].rootAssembly
    r1 = a.instances['RigidPlate-1'].referencePoints
    refPoints1=(r1[3], )
    region1=regionToolset.Region(referencePoints=refPoints1)
    mdb.models['Model-1'].constraints['Constraint-2'].setValues(
        refPointRegion=region1, bodyRegion=region2)

    
    # === 网格划分 ===
    a.regenerate()
    p = mdb.models['Model-1'].parts['MergedStructure']
    c = p.cells
    pickedRegions = c.getSequenceFromMask(mask=('[#1 ]', ), )
    p.setMeshControls(regions=pickedRegions, elemShape=TET, technique=FREE)
    elemType1 = mesh.ElemType(elemCode=C3D20R)
    elemType2 = mesh.ElemType(elemCode=C3D15)
    elemType3 = mesh.ElemType(elemCode=C3D10)
    cells = c.getSequenceFromMask(mask=('[#1 ]', ), )
    pickedRegions = (cells, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))
    p.seedPart(size=0.2, deviationFactor=0.1, minSizeFactor=0.1)

    p = mdb.models['Model-1'].parts['MergedStructure']
    p.generateMesh()
    p = mdb.models['Model-1'].parts['RigidPlate']
    p.seedPart(size=0.6, deviationFactor=0.1, minSizeFactor=0.1)
    p.generateMesh()

Macro1()

def Macro2():
    # === Model Setup and Step Definition ===
    a = mdb.models['Model-1'].rootAssembly
    a.regenerate()

    # Delete existing interactions (if any)
    del mdb.models['Model-1'].interactions['Int-1']
    del mdb.models['Model-1'].interactions['Int-2']

    # Delete existing step and create new explicit dynamics step
    del mdb.models['Model-1'].steps['Step-1']
    mdb.models['Model-1'].ExplicitDynamicsStep(
        name='Step-1', 
        previous='Initial',
        timePeriod=0.015,  # Total time period: 0.01 seconds
        massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, 100.0, 0.0, None, 0, 0, 0.0, 0.0, 0, None), ),
        improvedDtMethod=ON
    )

    # === Constraint Definition: Tie Constraint ===
    # Tie RigidPlate-1 (main) to MergedStructure-1 (secondary)
    a = mdb.models['Model-1'].rootAssembly
    s1 = a.instances['RigidPlate-1'].faces
    side2Faces1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
    region1 = regionToolset.Region(side2Faces=side2Faces1)

    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#4040c0 ]', ), )
    region2 = regionToolset.Region(side1Faces=side1Faces1)

    mdb.models['Model-1'].Tie(
        name='Constraint-3',
        main=region1,
        secondary=region2,
        positionToleranceMethod=COMPUTED,
        adjust=ON,
        tieRotations=ON,
        thickness=ON
    )

    # === Contact Interactions Definition ===
    # Define surface-to-surface contact between RigidPlate-2 and MergedStructure-1

    # Contact Int-1
    s1 = a.instances['RigidPlate-2'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1 ]', ), )
    region1 = regionToolset.Region(side1Faces=side1Faces1)

    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#4040c0 ]', ), )
    # 10000
    region2 = regionToolset.Region(side1Faces=side1Faces1)

    mdb.models['Model-1'].SurfaceToSurfaceContactExp(
        name='Int-1',
        createStepName='Initial',
        main=region1,
        secondary=region2,
        mechanicalConstraint=PENALTY,
        sliding=FINITE,
        interactionProperty='IntProp-1',
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )

    # Contact Int-2
    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1000 ]', ), )
    region2 = regionToolset.Region(side1Faces=side1Faces1)

    mdb.models['Model-1'].SurfaceToSurfaceContactExp(
        name='Int-2',
        createStepName='Initial',
        main=region1,  # Same RigidPlate-2 face as before
        secondary=region2,
        mechanicalConstraint=PENALTY,
        sliding=FINITE,
        interactionProperty='IntProp-1',
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )

    # Contact Int-3
    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1000 ]', ), )
    # 2000000
    region2 = regionToolset.Region(side1Faces=side1Faces1)

    mdb.models['Model-1'].SurfaceToSurfaceContactExp(
        name='Int-3',
        createStepName='Initial',
        main=region1,  # Same RigidPlate-2 face
        secondary=region2,
        mechanicalConstraint=PENALTY,
        sliding=FINITE,
        interactionProperty='IntProp-1',
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )

    # Contact Int-4
    s1 = a.instances['MergedStructure-1'].faces
    side1Faces1 = s1.getSequenceFromMask(mask=('[#1000 ]', ), )
    
    # 80000
    region2 = regionToolset.Region(side1Faces=side1Faces1)

    mdb.models['Model-1'].SurfaceToSurfaceContactExp(
        name='Int-4',
        createStepName='Initial',
        main=region1,  # Same RigidPlate-2 face
        secondary=region2,
        mechanicalConstraint=PENALTY,
        sliding=FINITE,
        interactionProperty='IntProp-1',
        initialClearance=OMIT,
        datumAxis=None,
        clearanceRegion=None
    )

    # === Boundary Conditions ===
    # Update BC-1: Fix RigidPlate-1 reference point
    r1 = a.instances['RigidPlate-1'].referencePoints
    refPoints1 = (r1[3], )
    region = regionToolset.Region(referencePoints=refPoints1)
    mdb.models['Model-1'].boundaryConditions['BC-1'].setValues(region=region)

    # Update BC-2: Fix U2 in Initial step
    mdb.models['Model-1'].boundaryConditions['BC-2'].setValues(u2=SET)

    # Free U2 in Step-1
    mdb.models['Model-1'].boundaryConditions['BC-2'].setValuesInStep(
        stepName='Step-1',
        u2=FREED
    )

    # === Predefined Field: Initial Velocity ===
    # Apply initial velocity to RigidPlate-2
    r1 = a.instances['RigidPlate-2'].referencePoints
    refPoints1 = (r1[3], )
    region = regionToolset.Region(referencePoints=refPoints1)

    mdb.models['Model-1'].Velocity(
        name='Predefined Field-1',
        region=region,
        field='',
        distributionType=MAGNITUDE,
        velocity2=-10.0,  # Velocity in Y direction: -10.0
        omega=0.0
    )

    # === Mesh Settings ===
    # Set element type for MergedStructure
    p = mdb.models['Model-1'].parts['MergedStructure']
    elemType1 = mesh.ElemType(elemCode=UNKNOWN_HEX, elemLibrary=EXPLICIT)
    elemType2 = mesh.ElemType(elemCode=UNKNOWN_WEDGE, elemLibrary=EXPLICIT)
    elemType3 = mesh.ElemType(
        elemCode=C3D10M,
        elemLibrary=EXPLICIT,
        secondOrderAccuracy=OFF,
        distortionControl=DEFAULT
    )

    c = p.cells
    cells = c.getSequenceFromMask(mask=('[#1 ]', ), )
    pickedRegions = (cells, )
    p.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2, elemType3))

    # Delete section assignment for RigidPlate (making it rigid)
    p = mdb.models['Model-1'].parts['RigidPlate']
    del mdb.models['Model-1'].parts['RigidPlate'].sectionAssignments[0]

    # Regenerate assembly after modifications
    a1 = mdb.models['Model-1'].rootAssembly
    a1.regenerate()

    # === History Output Requests ===
    # Output for Reflection set
    regionDef = mdb.models['Model-1'].rootAssembly.sets['Reflection']
    mdb.models['Model-1'].HistoryOutputRequest(
        name='H-Output-2',
        createStepName='Step-1',
        variables=('U1', 'U2', 'RF1','RF2'),  # Reaction forces and displacements
        region=regionDef,
        sectionPoints=DEFAULT,
        rebar=EXCLUDE
    )

    # Output for TopReflection set
    regionDef = mdb.models['Model-1'].rootAssembly.sets['TopReflection']
    mdb.models['Model-1'].HistoryOutputRequest(
        name='H-Output-3',
        createStepName='Step-1',
        variables=('RF1','RF2'),
        region=regionDef,
        sectionPoints=DEFAULT,
        rebar=EXCLUDE
    )

    # Output for BotReflection set
    regionDef = mdb.models['Model-1'].rootAssembly.sets['BotReflection']
    mdb.models['Model-1'].HistoryOutputRequest(
        name='H-Output-4',
        createStepName='Step-1',
        variables=('RF1','RF2'),  # Reaction forces only
        region=regionDef,
        sectionPoints=DEFAULT,
        rebar=EXCLUDE
    )



Macro2()
mdb.models['Model-1'].Interaction(name='Int-5', 
    objectToCopy=mdb.models['Model-1'].interactions['Int-4'], 
    toStepName='Initial')

def Macro2():
    # 先获取面的mask值
    a = mdb.models['Model-1'].rootAssembly
    instance = a.instances['MergedStructure-1']
    faces = instance.faces

    top_faces = []    # 法向量(0,1,0)
    bottom_faces = [] # 法向量(0,-1,0)

    # 关键修复：使用face对象而不是索引，因为mask的bit位置和索引可能不对应
    for face in faces:
        try:
            normal = face.getNormal()
            # 允许0.01的误差
            if (abs(normal[0]) < 0.01 and
                abs(normal[1] - 1.0) < 0.01 and
                abs(normal[2]) < 0.01):
                top_faces.append(face)

            elif (abs(normal[0]) < 0.01 and
                  abs(normal[1] + 1.0) < 0.01 and
                  abs(normal[2]) < 0.01):
                bottom_faces.append(face)
        except:
            pass

    print("找到%d个顶面，%d个底面" % (len(top_faces), len(bottom_faces)))

    # 检查是否找到顶面，如果没有则提前退出
    if not top_faces:
        print("WARNING: No top faces detected, skipping interaction setup")
        # 删除所有预创建的Int-1到Int-5
        for i in range(1, 6):
            try:
                del mdb.models['Model-1'].interactions['Int-%d' % i]
            except:
                pass
        return

    # 处理顶面 - 根据数量决定分配策略
    if len(top_faces) == 5:
        # 5个顶面：分别赋给Int-1到Int-5
        for idx, face in enumerate(top_faces):
            s1 = a.instances['MergedStructure-1'].faces
            try:
                # 使用findAt通过面的中心点重新获取face
                face_center = face.pointOn[0]
                found_face = s1.findAt((face_center,))
                region2 = a.Surface(side1Faces=(found_face,), name='s_Surf-%d' % (idx+5))
            except Exception as e:
                print("ERROR: Failed to create surface for face %d: %s" % (idx, str(e)))
                continue

            int_name = 'Int-%d' % (idx+1)
            mdb.models['Model-1'].interactions[int_name].setValues(
                secondary=region2,
                mechanicalConstraint=PENALTY,
                sliding=FINITE,
                interactionProperty='IntProp-1',
                initialClearance=OMIT,
                datumAxis=None,
                clearanceRegion=None)
            
    elif len(top_faces) == 1:
        # 1个顶面：只赋给Int-1，删除其余
        s1 = a.instances['MergedStructure-1'].faces
        try:
            # 使用findAt通过面的中心点重新获取face
            face_center = top_faces[0].pointOn[0]
            found_face = s1.findAt((face_center,))
            region2 = a.Surface(side1Faces=(found_face,), name='s_Surf-9')
        except Exception as e:
            print("ERROR: Failed to create surface for single top face: %s" % str(e))
            return

        mdb.models['Model-1'].interactions['Int-1'].setValues(
            secondary=region2,
            mechanicalConstraint=PENALTY,
            sliding=FINITE,
            interactionProperty='IntProp-1',
            initialClearance=OMIT,
            datumAxis=None,
            clearanceRegion=None)
        
        # 删除Int-2到Int-5
        for i in range(2, 6):
            int_name = 'Int-%d' % i
            try:
                mdb.models['Model-1'].interactions[int_name].suppress()
                mdb.models['Model-1'].interactions[int_name].resume()
                del mdb.models['Model-1'].interactions[int_name]
            except:
                pass
            
    else:
        # 其他情况：将顶面依次赋给Int-1, Int-2, Int-3...，删除未赋值的
        for idx, face in enumerate(top_faces):
            if idx < 5:  # 最多分配到Int-5
                s1 = a.instances['MergedStructure-1'].faces
                try:
                    # 使用findAt通过面的中心点重新获取face
                    face_center = face.pointOn[0]
                    found_face = s1.findAt((face_center,))
                    region2 = a.Surface(side1Faces=(found_face,), name='s_Surf-%d' % (idx+5))
                except Exception as e:
                    print("ERROR: Failed to create surface for face %d: %s" % (idx, str(e)))
                    continue

                int_name = 'Int-%d' % (idx+1)
                mdb.models['Model-1'].interactions[int_name].setValues(
                    secondary=region2,
                    mechanicalConstraint=PENALTY,
                    sliding=FINITE,
                    interactionProperty='IntProp-1',
                    initialClearance=OMIT,
                    datumAxis=None,
                    clearanceRegion=None)
        
        # 删除未赋值的交互作用
        for i in range(len(top_faces)+1, 6):
            int_name = 'Int-%d' % i
            try:
                mdb.models['Model-1'].interactions[int_name].suppress()
                mdb.models['Model-1'].interactions[int_name].resume()
                del mdb.models['Model-1'].interactions[int_name]
            except:
                pass

    # 处理底面 - 赋给Constraint-3
    if bottom_faces:
        s1 = a.instances['MergedStructure-1'].faces
        try:
            # 使用findAt逐个重新获取每个底面
            found_faces = []
            for face in bottom_faces:
                face_center = face.pointOn[0]
                found_face = s1.findAt((face_center,))
                found_faces.append(found_face)
            region2 = a.Surface(side1Faces=tuple(found_faces), name='s_Surf-10')
            mdb.models['Model-1'].constraints['Constraint-3'].setValues(secondary=region2)
        except Exception as e:
            print("ERROR: Failed to create surface for bottom faces: %s" % str(e))

Macro2()

# mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(frequency=3)

# 解放自由度 改变方向增加tie约束改变int的  Penalty

