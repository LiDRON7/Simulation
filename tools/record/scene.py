"""scene.py OUT_DIR VIEWS: copy Simulation into OUT_DIR with recording cameras for the camera VIEWS (comma list).
Frames are saved inside drone_sim_dev at /film/<view>/ (record.sh bind-mounts that folder)."""
import math, pathlib, re, shutil, sys

src = pathlib.Path(__file__).resolve().parents[2]

# Fixed cameras: name -> (where it stands, what it looks at) in Gazebo's east/north/up. render.py uses these too.
FIXED = {'pad': ((3.5, -3.5, 0.4), (0, 0, 2.0)), 'tree': ((14, 9, 6), (5, 16, 4.5)),
         'crate': ((15, 7, 3.5), (10, 2, 1)), 'wide': ((-10, -6, 10), (6, 12, 2))}


def cam(name, rate, w=1280, h=720, fov=1.0, pose=''):
    return (f'<sensor name="{name}" type="camera">{pose}<always_on>1</always_on><update_rate>{rate}</update_rate>'
            f'<topic>film_{name}</topic><camera><horizontal_fov>{fov}</horizontal_fov>'
            f'<image><width>{w}</width><height>{h}</height></image><clip><near>0.05</near><far>300</far></clip>'
            f'<save enabled="true"><path>/film/{name}</path></save></camera></sensor>')


def look(name, at_from, at, rate=24, fov=1.0):
    (x, y, z), (tx, ty, tz) = at_from, at
    yaw = math.atan2(ty - y, tx - x)
    pitch = math.atan2(z - tz, math.hypot(tx - x, ty - y))  # positive pitch looks down in Gazebo
    return (f'<model name="film_{name}"><static>true</static><pose>{x} {y} {z} 0 {pitch:.3f} {yaw:.3f}</pose>'
            f'<link name="l">{cam(name, rate, fov=fov)}</link></model>')


def before_last(text, tag, extra):
    i = text.rfind(tag)
    return text[:i] + extra + text[i:]


if __name__ == '__main__':
    dst, views = pathlib.Path(sys.argv[1]), set(sys.argv[2].split(','))
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.git', 'recordings', '.record'))
    for drone in ('huntsman', 'widow'):
        f = dst / 'models' / drone / 'model.sdf'
        sdf = f.read_text()
        if 'onboard' in views:
            sdf = re.sub(r'(<sensor name="oakd_rgb" type="camera">\s*<camera>)',
                         r'\1<save enabled="true"><path>/film/onboard</path></save>', sdf, count=1)
        if 'chase' in views:  # behind and above the drone, fixed to it
            sdf = before_last(sdf, '</model>',
                              '<link name="film_chase_link"><pose relative_to="base_link">-2.4 0 0.9 0 0.3 0</pose>'
                              '<gravity>false</gravity><inertial><mass>0.0001</mass><inertia><ixx>1e-9</ixx>'
                              f'<iyy>1e-9</iyy><izz>1e-9</izz></inertia></inertial>{cam("chase", 24, fov=1.1)}</link>'
                              '<joint name="film_chase_joint" type="fixed"><parent>base_link</parent>'
                              '<child>film_chase_link</child></joint>')
        f.write_text(sdf)
    w = dst / 'worlds' / 'outdoor_field.sdf'
    extra = ''.join(look(n, *FIXED[n], rate=12 if n == 'wide' else 24, fov=1.2 if n == 'wide' else 1.0)
                    for n in FIXED if n in views)
    w.write_text(before_last(w.read_text(), '</world>', extra))
