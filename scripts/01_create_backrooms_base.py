import bpy
import math
from mathutils import Vector

# ============================================================
# REC: LEVEL 0
# 01_create_backrooms_base.py
# ------------------------------------------------------------
# 미로형 백룸 기본 세트 생성 스크립트
#
# 반영 사항:
# - 벽 중심의 미로형 백룸 구조
# - 테스트 렌더가 너무 어둡지 않도록 조명/노출 보정
# - Blender 4.4.1 AgX 컬러 매니지먼트 대응
# - 구조 확인용 Debug Overview 카메라 추가
# ============================================================


# ============================================================
# 기본 설정값
# ============================================================

FLOOR_SIZE_X = 42.0
FLOOR_SIZE_Y = 48.0

WALL_HEIGHT = 3.05
WALL_THICKNESS = 0.18

CEILING_HEIGHT = WALL_HEIGHT
CEILING_THICKNESS = 0.08

FLOOR_THICKNESS = 0.08


# ============================================================
# 공통 유틸리티
# ============================================================

def clear_scene():
    """현재 씬의 모든 오브젝트와 기존 프로젝트 컬렉션을 정리한다."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    target_collections = [
        "ENV_Backrooms_Maze",
        "LIGHT_Mesh_Fixtures",
        "LIGHT_Area",
        "PROPS_Odd_Objects",
        "CAMERAS",
    ]

    for col_name in target_collections:
        col = bpy.data.collections.get(col_name)
        if col:
            bpy.data.collections.remove(col)


def create_collection(name):
    """새 컬렉션을 생성한다."""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def link_to_collection(obj, target_collection):
    """오브젝트를 지정 컬렉션으로 이동한다."""
    for col in list(obj.users_collection):
        col.objects.unlink(obj)

    target_collection.objects.link(obj)


def create_cube(name, location, scale, material=None, collection=None):
    """
    큐브를 생성한다.
    scale 값은 실제 dimensions 기준으로 사용한다.
    """
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)

    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if material is not None:
        obj.data.materials.append(material)

    if collection is not None:
        link_to_collection(obj, collection)

    return obj


def add_bevel(obj, amount=0.02, segments=1):
    """오브젝트 모서리에 작은 베벨과 Weighted Normal을 추가한다."""
    bevel = obj.modifiers.new(name="Small_Bevel", type="BEVEL")
    bevel.width = amount
    bevel.segments = segments

    obj.modifiers.new(name="Weighted_Normal", type="WEIGHTED_NORMAL")
    return obj


def look_at(obj, target):
    """오브젝트가 target 좌표를 바라보도록 회전한다."""
    obj_location = Vector(obj.location)
    target_location = Vector(target)
    direction = target_location - obj_location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


# ============================================================
# 머티리얼 생성
# ============================================================

def create_basic_material(
    name,
    base_color,
    roughness=0.75,
    emission=False,
    emission_strength=1.0
):
    """기본 Principled BSDF 머티리얼을 생성한다."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = base_color

        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness

        if emission:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = base_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def create_materials():
    """1차 백룸 세트용 기본 머티리얼을 생성한다."""
    materials = {}

    materials["wall"] = create_basic_material(
        "M_Backrooms_Yellow_Wall_Base",
        (0.74, 0.62, 0.32, 1.0),
        roughness=0.92
    )

    materials["floor"] = create_basic_material(
        "M_Damp_Carpet_Base",
        (0.42, 0.34, 0.18, 1.0),
        roughness=0.96
    )

    materials["ceiling"] = create_basic_material(
        "M_Ceiling_Tile_Base",
        (0.66, 0.63, 0.51, 1.0),
        roughness=0.88
    )

    materials["light_cover"] = create_basic_material(
        "M_Fluorescent_Light_Cover",
        (0.86, 0.89, 0.78, 1.0),
        roughness=0.35,
        emission=True,
        emission_strength=1.5
    )

    materials["dark"] = create_basic_material(
        "M_Deep_Dark",
        (0.015, 0.012, 0.01, 1.0),
        roughness=0.9
    )

    materials["chair"] = create_basic_material(
        "M_Old_Wood_Chair",
        (0.31, 0.23, 0.14, 1.0),
        roughness=0.85
    )

    materials["mattress"] = create_basic_material(
        "M_Stained_Mattress",
        (0.72, 0.69, 0.58, 1.0),
        roughness=0.95
    )

    materials["metal"] = create_basic_material(
        "M_Dull_Metal",
        (0.35, 0.35, 0.32, 1.0),
        roughness=0.68
    )

    return materials


# ============================================================
# 바닥 / 천장 / 벽 생성
# ============================================================

def create_floor_and_ceiling(materials, collection):
    """바닥과 낮은 천장을 생성한다."""
    create_cube(
        "Floor_Damp_Carpet",
        location=(0, 0, -FLOOR_THICKNESS / 2),
        scale=(FLOOR_SIZE_X, FLOOR_SIZE_Y, FLOOR_THICKNESS),
        material=materials["floor"],
        collection=collection
    )

    create_cube(
        "Ceiling_Low_Tiles",
        location=(0, 0, CEILING_HEIGHT + CEILING_THICKNESS / 2),
        scale=(FLOOR_SIZE_X, FLOOR_SIZE_Y, CEILING_THICKNESS),
        material=materials["ceiling"],
        collection=collection
    )


def create_wall_x(name, x, y, length, materials, collection):
    """X축 방향 벽을 생성한다."""
    wall = create_cube(
        name,
        location=(x, y, WALL_HEIGHT / 2),
        scale=(length, WALL_THICKNESS, WALL_HEIGHT),
        material=materials["wall"],
        collection=collection
    )
    add_bevel(wall, amount=0.008, segments=1)
    return wall


def create_wall_y(name, x, y, length, materials, collection):
    """Y축 방향 벽을 생성한다."""
    wall = create_cube(
        name,
        location=(x, y, WALL_HEIGHT / 2),
        scale=(WALL_THICKNESS, length, WALL_HEIGHT),
        material=materials["wall"],
        collection=collection
    )
    add_bevel(wall, amount=0.008, segments=1)
    return wall


def create_outer_walls(materials, collection):
    """공간을 둘러싸는 외곽 벽을 생성한다."""
    half_x = FLOOR_SIZE_X / 2
    half_y = FLOOR_SIZE_Y / 2

    create_wall_x("Outer_Wall_North", 0, half_y, FLOOR_SIZE_X, materials, collection)
    create_wall_x("Outer_Wall_South", 0, -half_y, FLOOR_SIZE_X, materials, collection)
    create_wall_y("Outer_Wall_East", half_x, 0, FLOOR_SIZE_Y, materials, collection)
    create_wall_y("Outer_Wall_West", -half_x, 0, FLOOR_SIZE_Y, materials, collection)


def create_maze_walls(materials, collection):
    """
    내부 미로형 벽을 생성한다.
    직선 복도, 막다른 길, 시야를 끊는 벽, 애매한 빈 공간이 섞이도록 구성한다.
    """
    wall_data = [
        # 시작 구역 주변
        ("X", -8, -17, 12),
        ("Y", -4, -20, 7),
        ("X", 5, -14, 12),
        ("Y", 4, -18, 7),

        # 남서쪽 막다른 길과 우회 통로
        ("Y", -15, -12, 13),
        ("X", -10, -7, 10),
        ("Y", -5, -4, 8),
        ("X", -13, 1, 9),
        ("X", -17, -2, 7),

        # 중앙 미로
        ("X", 4, -6, 16),
        ("Y", 12, -2, 13),
        ("X", 6, 5, 12),
        ("Y", 0, 8, 10),
        ("X", -7, 12, 14),
        ("Y", -14, 9, 13),
        ("X", 0, 1, 7),
        ("Y", 4, 4, 6),

        # 동쪽 긴 복도와 시야 차단 벽
        ("Y", 17, -10, 18),
        ("X", 13, -1, 8),
        ("Y", 8, -12, 9),
        ("X", 15, -16, 10),
        ("Y", 20, 5, 16),
        ("X", 12, 7, 7),

        # 북쪽 불규칙 구역
        ("X", 7, 16, 17),
        ("Y", -2, 18, 9),
        ("X", -10, 20, 10),
        ("Y", -18, 15, 10),
        ("Y", -6, 17, 5),
        ("X", -17, 8, 6),

        # 엔딩 구역
        ("X", 14, 10, 12),
        ("X", 2, 23, 18),
        ("Y", 11, 19, 8),
        ("Y", 18, 18, 9),
    ]

    for index, data in enumerate(wall_data):
        axis, x, y, length = data
        name = f"Maze_Wall_{index:02d}_{axis}"

        if axis == "X":
            create_wall_x(name, x, y, length, materials, collection)
        else:
            create_wall_y(name, x, y, length, materials, collection)


# ============================================================
# 형광등 생성
# ============================================================

def create_fluorescent_light(
    name,
    location,
    rotation_z,
    materials,
    mesh_collection,
    light_collection,
    power=600
):
    """형광등 커버 메시와 Area Light를 생성한다."""
    x, y, z = location

    fixture = create_cube(
        name + "_Fixture",
        location=(x, y, z),
        scale=(2.2, 0.22, 0.08),
        material=materials["light_cover"],
        collection=mesh_collection
    )
    fixture.rotation_euler[2] = rotation_z
    add_bevel(fixture, amount=0.025, segments=2)

    bpy.ops.object.light_add(type="AREA", location=(x, y, z - 0.16))
    light = bpy.context.object
    light.name = name + "_AreaLight"
    light.data.energy = power
    light.data.size = 2.4

    # 테스트 렌더에서 밝기가 확보되도록 기본 방향을 유지한다.
    light.rotation_euler[0] = 0
    light.rotation_euler[1] = 0
    light.rotation_euler[2] = rotation_z

    link_to_collection(light, light_collection)

    return fixture, light


def create_lights(materials, mesh_collection, light_collection):
    """복도 흐름에 따라 형광등을 배치한다."""
    light_data = [
        # 시작 지점 근처
        (-15, -19, 0, 680),
        (-8, -15, 90, 600),
        (1, -17, 0, 620),
        (10, -15, 90, 560),

        # 중앙 미로
        (17, -10, 90, 540),
        (15, -3, 0, 420),
        (8, 2, 90, 580),
        (-2, 4, 0, 640),
        (-10, 7, 90, 520),

        # 북쪽 / 엔딩 방향
        (-16, 13, 0, 480),
        (-6, 17, 90, 400),
        (6, 15, 0, 580),
        (15, 12, 90, 480),
        (16, 20, 0, 380),
    ]

    for index, data in enumerate(light_data):
        x, y, rot_deg, power = data
        create_fluorescent_light(
            name=f"Fluorescent_{index:02d}",
            location=(x, y, CEILING_HEIGHT - 0.12),
            rotation_z=math.radians(rot_deg),
            materials=materials,
            mesh_collection=mesh_collection,
            light_collection=light_collection,
            power=power
        )

    # 테스트 렌더 구조 확인용 약한 보조광
    bpy.ops.object.light_add(type="AREA", location=(-14.0, -19.5, 2.4))
    fill = bpy.context.object
    fill.name = "Temporary_Start_Area_Fill"
    fill.data.energy = 130
    fill.data.size = 4.0
    link_to_collection(fill, light_collection)


# ============================================================
# 이상한 사물 생성
# ============================================================

def create_simple_chair(name, location, rotation_z, materials, collection, flipped=False):
    """큐브 조합으로 간단한 의자를 생성한다."""
    x, y, z = location
    parts = []

    seat = create_cube(
        name + "_Seat",
        location=(x, y, z + 0.45),
        scale=(0.7, 0.65, 0.10),
        material=materials["chair"],
        collection=collection
    )
    parts.append(seat)

    back = create_cube(
        name + "_Back",
        location=(x, y + 0.28, z + 0.85),
        scale=(0.7, 0.08, 0.75),
        material=materials["chair"],
        collection=collection
    )
    parts.append(back)

    leg_offsets = [
        (-0.27, -0.23),
        (0.27, -0.23),
        (-0.27, 0.23),
        (0.27, 0.23),
    ]

    for i, offset in enumerate(leg_offsets):
        lx, ly = offset
        leg = create_cube(
            f"{name}_Leg_{i}",
            location=(x + lx, y + ly, z + 0.22),
            scale=(0.08, 0.08, 0.45),
            material=materials["chair"],
            collection=collection
        )
        parts.append(leg)

    for part in parts:
        part.rotation_euler[2] = rotation_z
        add_bevel(part, amount=0.012, segments=1)

        if flipped:
            part.rotation_euler[0] = math.radians(92)
            part.location.z += 0.12

    return parts


def create_mattress(name, location, rotation_z, materials, collection):
    """낡은 매트리스와 얼룩을 생성한다."""
    x, y, z = location

    mattress = create_cube(
        name,
        location=(x, y, z + 0.12),
        scale=(2.1, 1.15, 0.24),
        material=materials["mattress"],
        collection=collection
    )
    mattress.rotation_euler[2] = rotation_z
    add_bevel(mattress, amount=0.08, segments=5)

    stain_data = [
        (-0.35, 0.10, 0.45, 0.25, 8),
        (0.45, -0.25, 0.35, 0.18, -12),
    ]

    for i, data in enumerate(stain_data):
        sx, sy, scx, scy, rot = data
        stain = create_cube(
            f"{name}_Stain_{i}",
            location=(x + sx, y + sy, z + 0.255),
            scale=(scx, scy, 0.01),
            material=materials["dark"],
            collection=collection
        )
        stain.rotation_euler[2] = rotation_z + math.radians(rot)

    return mattress


def create_door_frame(name, location, rotation_z, materials, collection):
    """실제 문 없이 존재하는 의미 없는 문틀을 생성한다."""
    x, y, z = location

    left = create_cube(
        name + "_Left",
        location=(x - 0.55, y, z + 1.05),
        scale=(0.12, 0.16, 2.1),
        material=materials["metal"],
        collection=collection
    )

    right = create_cube(
        name + "_Right",
        location=(x + 0.55, y, z + 1.05),
        scale=(0.12, 0.16, 2.1),
        material=materials["metal"],
        collection=collection
    )

    top = create_cube(
        name + "_Top",
        location=(x, y, z + 2.08),
        scale=(1.22, 0.16, 0.12),
        material=materials["metal"],
        collection=collection
    )

    parts = [left, right, top]

    for part in parts:
        part.rotation_euler[2] = rotation_z
        add_bevel(part, amount=0.018, segments=1)

    return parts


def create_fallen_light(name, location, rotation_z, materials, collection):
    """바닥에 떨어진 형광등과 케이블을 생성한다."""
    x, y, z = location

    body = create_cube(
        name + "_Body",
        location=(x, y, z + 0.08),
        scale=(2.1, 0.18, 0.10),
        material=materials["light_cover"],
        collection=collection
    )
    body.rotation_euler[2] = rotation_z
    body.rotation_euler[0] = math.radians(4)
    add_bevel(body, amount=0.025, segments=2)

    cable = create_cube(
        name + "_Cable",
        location=(x - 0.9, y - 0.25, z + 0.035),
        scale=(1.2, 0.035, 0.035),
        material=materials["dark"],
        collection=collection
    )
    cable.rotation_euler[2] = rotation_z + math.radians(18)

    return body, cable


def create_small_table(name, location, rotation_z, materials, collection):
    """벽에 너무 가깝게 붙어 있는 작은 테이블을 생성한다."""
    x, y, z = location
    parts = []

    top = create_cube(
        name + "_Top",
        location=(x, y, z + 0.55),
        scale=(0.9, 0.6, 0.08),
        material=materials["chair"],
        collection=collection
    )
    parts.append(top)

    for i, offset in enumerate([
        (-0.35, -0.22),
        (0.35, -0.22),
        (-0.35, 0.22),
        (0.35, 0.22),
    ]):
        lx, ly = offset
        leg = create_cube(
            f"{name}_Leg_{i}",
            location=(x + lx, y + ly, z + 0.27),
            scale=(0.06, 0.06, 0.55),
            material=materials["chair"],
            collection=collection
        )
        parts.append(leg)

    for part in parts:
        part.rotation_euler[2] = rotation_z
        add_bevel(part, amount=0.012, segments=1)

    return parts


def create_dark_end_gap(materials, collection):
    """엔딩 구역용 검은 틈 placeholder를 생성한다."""
    gap = create_cube(
        "Ending_Dark_Gap_Placeholder",
        location=(18.9, 18.8, 1.3),
        scale=(0.08, 1.4, 2.2),
        material=materials["dark"],
        collection=collection
    )
    add_bevel(gap, amount=0.01, segments=1)
    return gap


def create_props(materials, collection):
    """백룸 내부에 이상하게 배치된 사물을 생성한다."""
    create_simple_chair(
        "Chair_Facing_Wall",
        location=(-17.2, -5.5, 0),
        rotation_z=math.radians(90),
        materials=materials,
        collection=collection,
        flipped=False
    )

    create_simple_chair(
        "Chair_Flipped",
        location=(13.5, -18.3, 0),
        rotation_z=math.radians(-25),
        materials=materials,
        collection=collection,
        flipped=True
    )

    create_mattress(
        "Old_Mattress",
        location=(-8.5, 15.8, 0),
        rotation_z=math.radians(12),
        materials=materials,
        collection=collection
    )

    create_door_frame(
        "Meaningless_Door_Frame",
        location=(17.8, 6.5, 0),
        rotation_z=math.radians(90),
        materials=materials,
        collection=collection
    )

    create_fallen_light(
        "Fallen_Fluorescent",
        location=(2.5, 8.2, 0),
        rotation_z=math.radians(-12),
        materials=materials,
        collection=collection
    )

    create_small_table(
        "Too_Close_Table",
        location=(-1.5, -2.0, 0),
        rotation_z=math.radians(6),
        materials=materials,
        collection=collection
    )

    create_dark_end_gap(materials, collection)


# ============================================================
# 카메라 / 렌더 세팅
# ============================================================

def create_camera(camera_collection):
    """시작 카메라와 구조 확인용 디버그 카메라를 생성한다."""

    # 실제 영상용 시작 카메라
    # 이전 구도에 가까운 사선형 시작 구도
    bpy.ops.object.camera_add(location=(-14.0, -20.5, 1.62))
    camera = bpy.context.object
    camera.name = "CAM_Handheld_Start"

    # 미로 안쪽 복도를 사선으로 바라보는 구도
    look_at(camera, (-7.5, -14.0, 1.45))

    camera.data.lens = 20
    camera.data.sensor_width = 32

    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 7.0
    camera.data.dof.aperture_fstop = 6.5

    camera.data.clip_start = 0.05
    camera.data.clip_end = 200

    link_to_collection(camera, camera_collection)
    bpy.context.scene.camera = camera

    # 구조 확인용 탑뷰 카메라
    bpy.ops.object.camera_add(location=(0, -3, 38))
    overview_camera = bpy.context.object
    overview_camera.name = "CAM_Debug_Overview"
    look_at(overview_camera, (0, 0, 0))
    overview_camera.data.lens = 28
    overview_camera.data.clip_end = 300
    link_to_collection(overview_camera, camera_collection)

    return camera


def set_color_management(scene):
    """
    Blender 버전별 컬러 매니지먼트 호환 처리.
    Blender 4.4.1에서는 Filmic이 없을 수 있으므로 AgX를 우선 적용한다.
    """
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        try:
            scene.view_settings.view_transform = "Filmic"
        except TypeError:
            scene.view_settings.view_transform = "sRGB"

    try:
        scene.view_settings.look = "Medium High Contrast"
    except TypeError:
        try:
            scene.view_settings.look = "High Contrast"
        except TypeError:
            scene.view_settings.look = "None"

    # 테스트 렌더 확인을 위해 이전보다 밝게 설정
    scene.view_settings.exposure = 0.25
    scene.view_settings.gamma = 1.0


def set_render_settings():
    """렌더 엔진, 해상도, 컬러 매니지먼트, 월드 배경을 설정한다."""
    scene = bpy.context.scene

    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError:
            pass

    scene.frame_start = 1
    scene.frame_end = 120
    scene.frame_set(1)

    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 24

    set_color_management(scene)

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.03, 0.028, 0.022)

    if hasattr(scene, "eevee"):
        eevee = scene.eevee

        if hasattr(eevee, "use_gtao"):
            eevee.use_gtao = True

        if hasattr(eevee, "gtao_distance"):
            eevee.gtao_distance = 3

        if hasattr(eevee, "gtao_factor"):
            eevee.gtao_factor = 1.5

        if hasattr(eevee, "use_bloom"):
            eevee.use_bloom = True

        if hasattr(eevee, "bloom_intensity"):
            eevee.bloom_intensity = 0.08


# ============================================================
# 메인 실행
# ============================================================

def main():
    clear_scene()

    env_collection = create_collection("ENV_Backrooms_Maze")
    light_mesh_collection = create_collection("LIGHT_Mesh_Fixtures")
    light_collection = create_collection("LIGHT_Area")
    prop_collection = create_collection("PROPS_Odd_Objects")
    camera_collection = create_collection("CAMERAS")

    materials = create_materials()

    create_floor_and_ceiling(materials, env_collection)
    create_outer_walls(materials, env_collection)
    create_maze_walls(materials, env_collection)

    create_lights(materials, light_mesh_collection, light_collection)
    create_props(materials, prop_collection)

    create_camera(camera_collection)
    set_render_settings()

    print("REC: LEVEL 0 - Maze Backrooms base scene generated successfully.")


if __name__ == "__main__":
    main()