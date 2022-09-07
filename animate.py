import csv

from math import radians
from random import uniform
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

from libs import StanleyController, CarDescription, generate_cubic_spline
from kinematic_model import KinematicBicycleModel

class Simulation:

    def __init__(self):

        fps = 50.0

        self.dt = 1/fps
        self.map_size_x = 70
        self.map_size_y = 40
        self.frames = 2500
        self.loop = False

class Path:

    def __init__(self):

        # Get path to waypoints.csv
        with open('data/waypoints.csv', newline='') as f:
            rows = list(csv.reader(f, delimiter=','))

        ds = 0.05
        x, y = [[float(i) for i in row] for row in zip(*rows[1:])]
        self.px, self.py, self.pyaw, _ = generate_cubic_spline(x, y, ds)

class Car:

    def __init__(self, init_x, init_y, init_yaw, px, py, pyaw, dt):

        # Model parameters
        self.x = init_x
        self.y = init_y
        self.yaw = init_yaw
        self.v = 0.0
        self.delta = 0.0
        self.omega = 0.0
        self.wheelbase = 2.96
        self.max_steer = radians(33)
        self.dt = dt
        self.c_r = 0.01
        self.c_a = 2.0

        # Tracker parameters
        self.px = px
        self.py = py
        self.pyaw = pyaw
        self.k = 8.0
        self.ksoft = 1.0
        self.kyaw = 0.01
        self.ksteer = 0.0
        self.crosstrack_error = None
        self.target_id = None

        # Description parameters
        self.overall_length = 4.97
        self.overall_width = 1.964
        self.tyre_diameter = 0.4826
        self.tyre_width = 0.265
        self.axle_track = 1.7
        self.rear_overhang = 0.5 * (self.overall_length - self.wheelbase)
        self.colour = 'black'

        self.tracker = StanleyController(self.k, self.ksoft, self.kyaw, self.ksteer, self.max_steer, self.wheelbase, self.px, self.py, self.pyaw)
        self.kbm = KinematicBicycleModel(self.wheelbase, self.max_steer, self.dt, self.c_r, self.c_a)

    def drive(self):
        
        throttle = uniform(150, 200)
        self.delta, self.target_id, self.crosstrack_error = self.tracker.stanley_control(self.x, self.y, self.yaw, self.v, self.delta)
        self.x, self.y, self.yaw, self.v, _, _ = self.kbm.kinematic_model(self.x, self.y, self.yaw, self.v, throttle, self.delta)

        print(f"Cross-track term: {self.crosstrack_error}{' '*10}", end="\r")

class CarPlotter(CarDescription):
    car = None
    target = None
    car_outline = None
    plt_front_right_wheel = None
    plt_front_left_wheel = None
    plt_rear_right_wheel = None
    plt_rear_left_wheel = None
    rear_axle = None
    annotation = None


    def __init__(self,car, ax):
        super().__init__(car.overall_length, car.overall_width, car.rear_overhang, car.tyre_diameter, car.tyre_width, car.axle_track, car.wheelbase)
        empty              = ([], [])
        self.target,            = ax.plot(*empty, '+r')
        self.car_outline,       = ax.plot(*empty, color=car.colour)
        self.plt_front_right_wheel, = ax.plot(*empty, color=car.colour)
        self.plt_rear_right_wheel,  = ax.plot(*empty, color=car.colour)
        self.plt_front_left_wheel,  = ax.plot(*empty, color=car.colour)
        self.plt_rear_left_wheel,   = ax.plot(*empty, color=car.colour)
        self.rear_axle,         = ax.plot(car.x, car.y, '+', color=car.colour, markersize=2)
        self.annotation         = ax.annotate(f'{car.x:.1f}, {car.y:.1f}', xy=(car.x, car.y + 5), color='black', annotation_clip=False)
        self.car                = car
        return

def animate(frame, ax, sim, path, fargs):

    car               = fargs.car
    car_outline       = fargs.car_outline
    front_right_wheel = fargs.plt_front_right_wheel
    front_left_wheel  = fargs.plt_front_left_wheel
    rear_right_wheel  = fargs.plt_rear_right_wheel
    rear_left_wheel   = fargs.plt_rear_left_wheel
    rear_axle         = fargs.rear_axle
    annotation        = fargs.annotation
    target            = fargs.target

    # Camera tracks car
    ax.set_xlim(car.x - sim.map_size_x, car.x + sim.map_size_x)
    ax.set_ylim(car.y - sim.map_size_y, car.y + sim.map_size_y)

    # Drive and draw car
    car.drive()
    outline_plot, fr_plot, rr_plot, fl_plot, rl_plot = fargs.plot_car(car.x, car.y, car.yaw, car.delta)
    car_outline.set_data(*outline_plot)
    front_right_wheel.set_data(*fr_plot)
    rear_right_wheel.set_data(*rr_plot)
    front_left_wheel.set_data(*fl_plot)
    rear_left_wheel.set_data(*rl_plot)
    rear_axle.set_data(car.x, car.y)

    # Show car's target
    target.set_data(path.px[car.target_id], path.py[car.target_id])

    # Annotate car's coordinate above car
    annotation.set_text(f'{car.x:.1f}, {car.y:.1f}')
    annotation.set_position((car.x, car.y + 5))

    plt.title(f'{sim.dt*frame:.2f}s', loc='right')
    plt.xlabel(f'Speed: {car.v:.2f} m/s', loc='left')
    # plt.savefig(f'image/visualisation_{frame:03}.png', dpi=300)

    return car_outline, front_right_wheel, rear_right_wheel, front_left_wheel, rear_left_wheel, rear_axle, target,

def main():
    
    sim  = Simulation()
    path = Path()
    car  = Car(path.px[0], path.py[0], path.pyaw[0], path.px, path.py, path.pyaw, sim.dt)

    interval = sim.dt * 10**3

    fig = plt.figure()
    ax = plt.axes()
    ax.set_aspect('equal')

    road = plt.Circle((0, 0), 50, color='gray', fill=False, linewidth=30)
    ax.add_patch(road)
    ax.plot(path.px, path.py, '--', color='gold')

    car_description = CarPlotter(car, ax)
    fargs = [
        ax,
        sim,
        path,
        car_description
    ]

    _ = FuncAnimation(fig, animate, frames=sim.frames, init_func=lambda: None, fargs=fargs, interval=interval, repeat=sim.loop)
    # anim.save('animation.gif', writer='imagemagick', fps=50)
    
    plt.grid()
    plt.show()

if __name__ == '__main__':
    main()
