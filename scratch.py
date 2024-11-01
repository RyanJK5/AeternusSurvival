import pygame
import pygame.gfxdraw
import math
import random

START_TIME = 0
TMR_SPEED = 60
GLOBAL_TIMER = None
OBJ_LIST = []
BULLET_EVENTS = []
DIM_GREY = (119, 136, 153)

INVINC_TIME = 1000
BLINK_TIME = 100

increasing_color = True
bullet_color = pygame.Color(255, 0, 0)

sine_pos = 0
offset = 0
pentagram_offset = 0
circle_2_offset = 0
slow_hell_offset = 0
precision_x = 0

pygame.init()
screen = pygame.display.set_mode((1000, 900), pygame.NOFRAME)
clock = pygame.time.Clock()
running = True

death_surface = pygame.Surface((screen.get_width(), screen.get_height()))
death_surface.set_alpha(100)

circular_beam_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
circular_beam_surface.set_alpha(100)


class Circle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

    def set_position(self, x, y):
        self.x = x
        self.y = y


class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2


class GameObject:

    def __init__(self, circ):
        OBJ_LIST.append(self)
        self.circ = circ
        self.color = None
        self.drawing = True
        self.width = 0
        self.time_since = 0

    def get_x(self):
        return self.circ.x

    def get_y(self):
        return self.circ.y

    def get_radius(self):
        return self.circ.radius

    def move(self, dx, dy):
        self.set_position(self.get_x() + dx, self.get_y() + dy)

    def set_position(self, x, y):
        self.circ.set_position(x, y)

    def kill(self):
        if self in OBJ_LIST:
            OBJ_LIST.remove(self)

    def update(self, dt):
        self.time_since += dt

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.get_x(), self.get_y()), self.get_radius(), self.width)

    def on_col(self):
        pass


class Player(GameObject):

    def __init__(self, circ):
        super().__init__(circ)
        self.color = "white"
        self.up = False
        self.down = False
        self.left = False
        self.right = False
        self.slowed = False
        self.speed = 5 * TMR_SPEED / 1000
        self.invinc = INVINC_TIME
        self.health = 1000

    def update(self, dt):
        global TMR_SPEED
        last_invinc = self.invinc
        self.invinc += dt
        if self.invinc < INVINC_TIME and self.invinc % BLINK_TIME < last_invinc % BLINK_TIME:
            self.drawing = not self.drawing
        if self.invinc > INVINC_TIME and not self.drawing:
            self.drawing = True

        speed = self.speed
        if (self.left or self.right) and (self.up or self.down):
            pass
            speed = math.sqrt(self.speed ** 2 / 2)
        if self.slowed:
            speed /= 2
        speed *= dt
        if self.left:
            self.move(-speed, 0)
        if self.right:
            self.move(speed, 0)
        if self.up:
            self.move(0, -speed)
        if self.down:
            self.move(0, speed)

    def move(self, dx, dy):
        bounds = self.circ
        if bounds.x + bounds.radius + dx > screen.get_width():
            bounds.x = screen.get_width() - bounds.radius
        elif bounds.x - bounds.radius + dx < 0:
            bounds.x = bounds.radius
        elif bounds.y + bounds.radius + dy > screen.get_height():
            bounds.y = screen.get_height() - bounds.radius
        elif bounds.y - bounds.radius + dy < 0:
            bounds.y = bounds.radius
        else:
            super().move(dx, dy)

    def on_col(self):
        if self.invinc < INVINC_TIME or self.health == 0:
            return
        self.invinc = 0
        self.health -= 1
        if self.health == 0:
            self.kill()


class Bullet(GameObject):
    def __init__(self):
        super().__init__(Circle(0, 0, 6))
        self.x_speed = 0
        self.y_speed = 0
        self.speed = TMR_SPEED / 1000
        self.increasing_color = True
        self.survive_off_screen = False

    def update(self, dt):
        self.move(self.x_speed * self.speed * dt, self.y_speed * self.speed * dt)
        if self.can_kill():
            self.kill()

    def can_kill(self):
        return not self.survive_off_screen and (self.get_x() + self.get_radius() < 0 or
               self.get_x() - self.get_radius() > screen.get_width() or
               self.get_y() + self.get_radius() < 0 or self.get_y() - self.get_radius() > screen.get_height())

    def draw(self):
        global bullet_color
        pygame.draw.circle(screen, bullet_color, (self.get_x(), self.get_y()), self.get_radius())

    def on_col(self):
        self.kill()

    def set_angle(self, theta):
        self.x_speed = math.cos(theta)
        self.y_speed = math.sin(theta)

    def set_target(self, x, y):
        dx = x - self.get_x()
        dy = y - self.get_y()
        self.set_angle(math.atan2(dy, dx))


class HomingBullet(Bullet):
    def __init__(self):
        super().__init__()
        self.homing_speed = -1
        self.homing_time = 0
        self.homing_lifespan = -1

    def update(self, dt):
        global player
        if self.homing_lifespan > 0:
            self.homing_time += dt
            if self.homing_time > self.homing_lifespan:
                self.homing_speed = 0

        if self.homing_speed < 0:
            self.set_target(player.get_x(), player.get_y())
        elif self.homing_speed > 0:
            next_x = self.get_x() + self.x_speed
            next_y = self.get_y() + self.y_speed
            theta = math.atan2(player.get_y() - next_y, player.get_x() - next_x)
            self.set_target(next_x + math.cos(theta) * self.homing_speed * dt,
                            next_y + math.sin(theta) * self.homing_speed * dt)
        super().update(dt)

    def can_kill(self):
        if self.homing_lifespan > 0 and self.homing_time < self.homing_lifespan:
            return False
        return super().can_kill()


class BouncingBullet(Bullet):
    def __init__(self):
        super().__init__()
        self.bounces_left = -1

    def update(self, dt):
        super().update(dt)
        if self.bounces_left != 0 and (
                self.get_x() - self.get_radius() < 0 or self.get_x() + self.get_radius() > screen.get_width()):
            self.bounces_left -= 1
            self.on_bounce(True)
        if self.bounces_left != 0 and (
                self.get_y() - self.get_radius() < 0 or self.get_y() + self.get_radius() > screen.get_height()):
            self.bounces_left -= 1
            self.on_bounce(False)

    def on_bounce(self, horizontal):
        if horizontal:
            self.x_speed *= -1
        else:
            self.y_speed *= -1


class HomingBouncingBullet(BouncingBullet, HomingBullet):
    def on_bounce(self, horizontal):
        self.set_target(player.get_x(), player.get_y())


class CircularBullet(Bullet):
    def __init__(self):
        super().__init__()
        self.theta = 0
        self.radius = 0
        self.radius_increment = 0
        self.rotating = True

    def update(self, dt):
        if self.rotating:
            self.radius += self.radius_increment * dt
            if self.radius <= 0:
                self.radius = 0.01
            self.theta += self.speed / self.radius * dt

            self.x_speed = -math.sin(self.theta)
            self.y_speed = math.cos(self.theta)

        super().update(dt)


class SinusoidalBullet(Bullet):
    def __init__(self):
        super().__init__()
        self.start_x = 0
        self.amplitude = 0
        self.frequency = 0

    def set_position(self, x, y):
        super().set_position(x, y)

    def update(self, dt):
        # derivative of Asin(Fx) + C
        self.y_speed = self.amplitude * self.frequency * math.cos(self.frequency * (self.circ.x - self.start_x))
        super().update(dt)

    def can_kill(self):
        return self.circ.x > screen.get_width()


class Beam(GameObject):
    def __init__(self, line):
        super().__init__(Circle(0, 0, 0))
        self.delay = 0
        self.lifespan = 0
        self.line = line
        self.color = DIM_GREY
        self.started_wait = False
        self.started_hold = False
        self.width = 2
        self.bursts = 1
        self.time_since = 0

    def start_delay(self, delay):
        self.delay = delay
        self.started_wait = True

    def draw(self):
        color = bullet_color
        if self.color == DIM_GREY:
            color = DIM_GREY
        pygame.draw.line(screen, color, (self.line.x1, self.line.y1), (self.line.x2, self.line.y2), self.width)

    def update(self, dt):
        self.time_since += dt
        if self.started_wait:
            if self.time_since >= self.delay:
                self.started_hold = True
                self.started_wait = False
                self.color = bullet_color
        if self.started_hold:
            if self.time_since >= self.delay + self.lifespan:
                self.started_hold = False
                self.bursts -= 1
                self.color = DIM_GREY
                if self.bursts <= 0:
                    self.kill()
                else:
                    self.started_wait = True
                    self.time_since = 0

    def intersects(self, circ):
        if not self.started_hold:
            return False

        line = self.line
        if line.x2 - line.x1 == 0:
            return circ.x - circ.radius < line.x1 < circ.x + circ.radius

        a = circ.x
        b = circ.y
        c = line.y1
        m = (line.y2 - line.y1) / (line.x2 - line.x1)
        r = circ.radius

        # discriminant of solution to the equation (x-a)^2 + (mx+b-c)^2 = r^2
        return -a * a * m * m + 2 * a * b * m - 2 * a * c * m - b * b + 2 * b * c - c * c + r * r * m * m + r * r >= 0


class CircularBeam(Beam):
    def __init__(self, circ):
        super().__init__(Line(0, 0, 0, 0))
        self.circ = circ
        self.damage_within = True
        self.radius_increment = 0

    def intersects(self, circ):
        if not self.started_hold:
            return False
        dist = math.dist((circ.x, circ.y), (self.circ.x, self.circ.y))
        if self.damage_within:
            return dist <= circ.radius + self.circ.radius
        else:
            return self.circ.radius - circ.radius <= dist <= circ.radius + self.circ.radius

    def draw(self):
        color = bullet_color
        if self.color == DIM_GREY:
            color = DIM_GREY
        if self.damage_within:
            pygame.draw.circle(circular_beam_surface, color, (self.get_x(), self.get_y()), self.get_radius())
        else:
            pygame.draw.circle(screen, color, (self.get_x(), self.get_y()), self.get_radius(), self.width)

    def update(self, dt):
        super().update(dt)
        self.circ.radius += self.radius_increment * dt


class MovingBeam(Beam):

    def __init__(self, line):
        super().__init__(line)
        self.speed = 0
        self.x_speed = 0
        self.y_speed = 0

    def update(self, dt):
        super().update(dt)
        self.line.x1 += self.x_speed * self.speed * dt
        self.line.x2 += self.x_speed * self.speed * dt
        self.line.y1 += self.y_speed * self.speed * dt
        self.line.y2 += self.y_speed * self.speed * dt


class ReverseCircularBeam(CircularBeam):
    def intersects(self, circ):
        if not self.started_hold:
            return False
        dist = math.dist((circ.x, circ.y), (self.circ.x, self.circ.y))
        return dist > self.circ.radius - circ.radius

    def draw(self):
        color = bullet_color
        if self.color == DIM_GREY:
            color = DIM_GREY
        circular_beam_surface.fill(color)
        pygame.draw.circle(circular_beam_surface, (0, 0, 0, 0), (self.get_x(), self.get_y()), self.get_radius())


class BulletEvent:
    def __init__(self, delay, event, lifespan=0):
        self.event = event
        self.delay = delay
        self.initial_delay = 0
        self.time_since = 0
        if lifespan != 0:
            self.lifespan = lifespan - START_TIME
        else:
            self.lifespan = 0
        self.first = True

        self.set_initial_delay(delay)

    def set_initial_delay(self, init_delay):
        self.initial_delay = init_delay - START_TIME
        if self.initial_delay < 0:
            self.initial_delay = self.delay

    def update(self, dt):
        if self.first:
            delay = self.initial_delay
        else:
            delay = self.delay

        last_time = self.time_since
        self.time_since += dt

        if self.time_since > self.lifespan and not self.lifespan == 0:
            self.kill()
        if delay == 0 or self.time_since % delay < last_time % delay:
            if self.first:
                self.first = False
            self.event()

    def kill(self):
        BULLET_EVENTS.remove(self)


def main():
    global circle_2_offset, sine_pos, offset, slow_hell_offset, pentagram_offset, player, START_TIME

    pentagram_offset = 0
    slow_hell_offset = 0
    offset = 0
    sine_pos = 0
    circle_2_offset = 0

    player = Player(Circle(0, 0, 6))
    player.set_position(screen.get_width() / 2, screen.get_height() / 2)

    pygame.mixer.music.load("sfx\\Aeternus.wav")
    pygame.mixer.music.play(-1, START_TIME / 1000)

    BULLET_EVENTS.append(BulletEvent(0, make_bullet_circle, 1))

    BULLET_EVENTS.append(BulletEvent(112.5, make_sine_bullets, 7425))

    BULLET_EVENTS.append(BulletEvent(60, change_bullet_color))

    BULLET_EVENTS.append(BulletEvent(900, make_beams, 8100))

    homing_event = BulletEvent(200, make_homing, 8000)
    homing_event.set_initial_delay(4000)
    BULLET_EVENTS.append(homing_event)

    BULLET_EVENTS.append(BulletEvent(8600, pentagram, 8600))

    circ_event = BulletEvent(50, make_circ_bullets, 12800)
    circ_event.set_initial_delay(9050)
    BULLET_EVENTS.append(circ_event)

    BULLET_EVENTS.append(BulletEvent(9050, make_bullet_circle, 9050))

    beam_event = BulletEvent(100, make_beam_through_player, 12600)
    beam_event.set_initial_delay(9050)
    BULLET_EVENTS.append(beam_event)

    beam_grid = BulletEvent(475, make_beam_grid, 18000)
    beam_grid.set_initial_delay(12600)
    BULLET_EVENTS.append(beam_grid)

    targeted_circles = BulletEvent(200, create_targeted_circle, 18000)
    targeted_circles.set_initial_delay(12500)
    BULLET_EVENTS.append(targeted_circles)

    suck_event = BulletEvent(18000, bullet_suck, 18100)
    suck_event.set_initial_delay(18000)
    BULLET_EVENTS.append(suck_event)

    beam_event_2 = BulletEvent(2500, make_bullet_circle, 26000)
    beam_event_2.set_initial_delay(19000)
    BULLET_EVENTS.append(beam_event_2)

    burst = BulletEvent(500, falling_bombs, 26000)
    burst.set_initial_delay(19000)
    BULLET_EVENTS.append(burst)

    slow_hell_event = BulletEvent(25, slow_hell, 35000)
    slow_hell_event.set_initial_delay(26000)
    BULLET_EVENTS.append(slow_hell_event)

    slow_burst_event = BulletEvent(1000, slow_burst, 35000)
    slow_burst_event.set_initial_delay(26000)
    BULLET_EVENTS.append(slow_burst_event)

    BULLET_EVENTS.append(BulletEvent(36000, outer_circle, 36100))

    homing_event_2 = BulletEvent(100, make_homing_2, 40000)
    homing_event_2.set_initial_delay(36000)
    BULLET_EVENTS.append(homing_event_2)

    bullet_circle_2 = BulletEvent(125, make_bullet_circle_2, 44000)
    bullet_circle_2.set_initial_delay(40000)
    BULLET_EVENTS.append(bullet_circle_2)

    pentagram_event_2 = BulletEvent(500, pentagram_2, 44000)
    pentagram_event_2.set_initial_delay(40000)
    BULLET_EVENTS.append(pentagram_event_2)

    BULLET_EVENTS.append(BulletEvent(44000, precision_blast, 44100))

    precision_section = BulletEvent(50, precision, 50000)
    precision_section.set_initial_delay(44000)
    BULLET_EVENTS.append(precision_section)

    global_loop()


def change_bullet_color():
    global increasing_color, bullet_color
    b = bullet_color.b
    r = bullet_color.r
    if increasing_color:
        b += 5
        r -= 3
    else:
        b -= 5
        r += 3
    if b <= 0 or b >= 255:
        increasing_color = not increasing_color
        return
    bullet_color.b = b
    bullet_color.r = r


def check_col(obj):
    col_obj = None
    for obj2 in OBJ_LIST:
        if obj == obj2:
            continue

        if isinstance(obj2, Beam) and obj2.intersects(obj.circ):
            col_obj = obj2
            break

        if not isinstance(obj2, Bullet):
            continue

        h1 = obj.circ
        h2 = obj2.circ
        dist = math.dist([h1.x, h1.y], [h2.x, h2.y])
        if dist <= h1.radius + h2.radius:
            col_obj = obj2
            break
    if not (col_obj is None):
        obj.on_col()
        col_obj.on_col()


def handle_keyboard(e):
    if e.key == pygame.K_SPACE and e.type == pygame.KEYDOWN:
        player.kill()
        on_death()
        main()
    elif e.key == pygame.K_LEFT:
        player.left = e.type == pygame.KEYDOWN
    elif e.key == pygame.K_RIGHT:
        player.right = e.type == pygame.KEYDOWN
    elif e.key == pygame.K_UP:
        player.up = e.type == pygame.KEYDOWN
    elif e.key == pygame.K_DOWN:
        player.down = e.type == pygame.KEYDOWN
    elif e.key == pygame.K_LSHIFT:
        player.slowed = e.type == pygame.KEYDOWN


def global_loop():
    total = 0
    dt = 0
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.KEYDOWN or e.type == pygame.KEYUP:
                handle_keyboard(e)
        for e in BULLET_EVENTS:
            e.update(dt)

        circular_beam_surface.fill((0,0,0,0))
        screen.fill((0, 0, 0))
        for obj in OBJ_LIST:
            if obj.drawing:
                obj.draw()
            obj.update(dt)
        screen.blit(circular_beam_surface, (0, 0))

        if player not in OBJ_LIST:
            death_surface.fill((255, 0, 0))
            screen.blit(death_surface, (0, 0))
            on_death()
        check_col(player)
        pygame.display.update()

        dt = clock.tick(TMR_SPEED)
        total += dt


def create_circle(circle, bullet_count, bullet_class):
    bullets = []
    for i in range(bullet_count):
        bullet = bullet_class()
        bullet.set_position(circle.x + math.cos(math.tau / bullet_count * i) * circle.radius,
                            circle.y + math.sin(math.tau / bullet_count * i) * circle.radius)
        bullets.append(bullet)
    return bullets


def make_homing():
    bullet = HomingBullet()
    bullet.set_position(random.random() * screen.get_width(), 0)
    bullet.homing_speed = 0.01 * TMR_SPEED / 1000
    bullet.speed = 7.5 * TMR_SPEED / 1000


def make_homing_2():
    global offset

    radius = 200

    bullet = HomingBullet()
    bullet.set_position(radius * math.sin(offset * math.pi / 6) + player.get_x(), radius * math.cos(offset * math.pi / 6) + player.get_y())
    bullet.set_target(player.get_x(), player.get_y())
    bullet.x_speed *= -1
    bullet.y_speed *= -1

    bullet.homing_lifespan = 2000
    bullet.homing_speed = 0.075 * TMR_SPEED / 1000
    bullet.speed = 6 * TMR_SPEED / 1000

    offset += 1


def create_pentagram(circ):
    global bullet_color

    beams = []
    angle = math.tau / 5
    offset = -math.pi / 10
    for i in range(1, 6):
        line_x1 = math.cos(angle * i + offset) * circ.radius + circ.x
        line_y1 = math.sin(angle * i + offset) * circ.radius + circ.y
        line_x2 = math.cos(angle * (i + 2) + offset) * circ.radius + circ.x
        line_y2 = math.sin(angle * (i + 2) + offset) * circ.radius + circ.y
        beam = Beam(Line(line_x1, line_y1, line_x2, line_y2))
        beam.lifespan = 200
        beam.start_delay(450)
        beam.width = 10
        beams.append(beam)
    # bullet_color = pygame.Color(255, 0, 0)

    beam2 = CircularBeam(circ)
    beam2.damage_within = False
    beam2.width = 10
    beam2.lifespan = 200
    beam2.start_delay(450)
    beams.append(beam2)
    return beams


def pentagram():
    circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 450)
    create_pentagram(circ)


def pentagram_2():
    global pentagram_offset
    circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 100 + pentagram_offset * 200)
    beams = create_pentagram(circ)
    for beam in beams:
        beam.lifespan = 4000 - pentagram_offset * 400
    pentagram_offset += 1


def clear_bullets():
    for i in range(len(OBJ_LIST)):
        if i >= len(OBJ_LIST):
            break
        if isinstance(OBJ_LIST[i], Bullet):
            OBJ_LIST.pop(i)
            i -= 1


def make_sine_bullets():
    global sine_pos
    bullet = SinusoidalBullet()
    bullet.amplitude = 50
    bullet.frequency = 0.01
    bullet.set_position(0, screen.get_height() / 10 * (sine_pos % 11))
    bullet.speed = 10 * TMR_SPEED / 1000
    bullet.set_target(screen.get_width(), bullet.circ.y)
    sine_pos += 1


def make_circ_bullets():
    bullet = BouncingBullet()
    bullet.speed = 10 * TMR_SPEED / 1000
    bullet.bounces_left = 1

    theta = random.random() * math.tau
    radius = 600

    bullet.circ.x = math.cos(theta) * radius + player.circ.x
    bullet.circ.y = math.sin(theta) * radius + player.circ.y
    bullet.set_target(player.circ.x, player.circ.y)


def make_beam_through_player():
    slope_factor = 2
    slope = random.random() * slope_factor - slope_factor / 2
    y_int = -slope * player.get_x() + player.get_y()

    line = Line(0, y_int, screen.get_width(), y_int + slope * screen.get_width())
    beam = Beam(line)
    beam.start_delay(500)
    beam.lifespan = 75


def make_beams():
    if len(OBJ_LIST) <= 1:
        return
    for i in range(5):
        line = Line(0, screen.get_height() * random.random(), screen.get_width(), screen.get_height() * random.random())
        beam = Beam(line)
        beam.start_delay(500)
        beam.lifespan = 75


def make_bullet_circle():
    circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 100)
    bullets = create_circle(circ, 20, BouncingBullet)
    for bullet in bullets:
        bullet.set_target(circ.x, circ.y)
        bullet.x_speed *= -1
        bullet.y_speed *= -1

        bullet.bounces_left = 2
        bullet.speed = 7.5 * TMR_SPEED / 1000


def make_beam_grid():
    global offset
    line_count = 6
    for i in range(line_count):
        x_pos = (i * screen.get_width() / line_count + offset) % screen.get_width()
        y_pos = (i * screen.get_height() / line_count + offset) % screen.get_height()
        beam = Beam(Line(0, y_pos, screen.get_width(), y_pos))
        beam.start_delay(400)
        beam.lifespan = 75
        beam2 = Beam(Line(x_pos, 0, x_pos, screen.get_height()))
        beam2.start_delay(400)
        beam2.lifespan = 75
    offset += 30


def create_targeted_circle():
    circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 50)
    bullet_count = 20
    for i in range(bullet_count):
        bullet = CircularBullet()
        bullet.theta = math.tau / bullet_count * i + offset
        bullet.radius = circ.radius
        bullet.set_position(circ.x + math.cos(bullet.theta) * circ.radius,
                            circ.y + math.sin(bullet.theta) * circ.radius)
        bullet.speed = 7.5 * (TMR_SPEED / 1000)
        bullet.radius_increment = 1


def falling_bombs():
    for i in range(5):
        circ = Circle(random.random() * screen.get_width(), random.random() * screen.get_height(), 150)
        bomb = CircularBeam(circ)
        bomb.lifespan = 200
        bomb.start_delay(1000)
        bomb.damage_within = True


def bullet_suck():
    for bullet in OBJ_LIST:
        try:
            bullet.rotating = False
            bullet.radius_increment = 0
            bullet.set_target(screen.get_width() / 2, screen.get_height() / 2)
            bullet.speed = 10 * TMR_SPEED / 1000
        except:
            pass


def bouncing_bullets():
    circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 10)

    count = 20
    bullets = create_circle(circ, count, HomingBouncingBullet)
    for i in range(count):
        bullet = bullets[i]
        bullet.bounces_left = 2
        bullet.speed = 5 * TMR_SPEED / 1000
        bullet.homing_speed = 0.005 * TMR_SPEED / 1000
        bullet.set_angle(i * math.tau / count)
        bullet.x_speed *= -1
        bullet.y_speed *= -1


def slow_hell():
    global slow_hell_offset
    bullet_count = 40
    for i in range(4):
        if i == 0:
            x_pos = slow_hell_offset * screen.get_width() / bullet_count
            y_pos = 0
        elif i == 1:
            x_pos = slow_hell_offset * screen.get_width() / bullet_count
            y_pos = screen.get_height() - 6
        elif i == 2:
            x_pos = 0
            y_pos = slow_hell_offset * screen.get_height() / bullet_count
        else:
            x_pos = screen.get_width() - 6
            y_pos = slow_hell_offset * screen.get_height() / bullet_count
        bullet = Bullet()
        bullet.speed = 2 * TMR_SPEED / 1000
        bullet.set_angle(slow_hell_offset * (math.pi / bullet_count + math.pi))
        bullet.set_position(x_pos, y_pos)
    slow_hell_offset += 1
    slow_hell_offset %= bullet_count


def slow_burst():
    circ = Circle(random.random() * (screen.get_width() - 10) + 10, random.random() * (screen.get_height() - 10) + 10, 10)
    bullets = create_circle(circ, 20, Bullet)
    for i in range(len(bullets)):
        bullet = bullets[i]
        bullet.speed = 2 * TMR_SPEED / 1000
        bullet.set_angle(i * (math.tau / len(bullets)))
        bullet.x_speed *= -1
        bullet.y_speed *= -1


def outer_circle():
    for i in range(10):
        circ = Circle(screen.get_width() / 2, screen.get_height() / 2, 200 * (i+1))
        reverse = CircularBeam(circ)
        reverse.lifespan = 200
        reverse.damage_within = False
        reverse.width = 10
        reverse.start_delay(500)
        reverse.radius_increment = -0.5
        reverse.bursts = 10
    for bullet in OBJ_LIST:
        if isinstance(bullet, Bullet):
            bullet.speed = -10 * TMR_SPEED / 1000
            bullet.set_target(player.get_x(), player.get_y())


def make_bullet_circle_2():
    global circle_2_offset

    circle = Circle(screen.get_width() / 2, screen.get_height() / 2, 100 + 50 * circle_2_offset)
    bullet_count = 20
    for i in range(bullet_count):
        theta = (circle_2_offset * math.pi / 6) + (math.tau / bullet_count * i)

        bullet = CircularBullet()
        bullet.radius = circle.radius
        bullet.theta = theta
        bullet.set_position(circle.x + math.cos(theta) * circle.radius,
                            circle.y + math.sin(theta) * circle.radius)
        bullet.speed = 7.5 * TMR_SPEED / 1000
        bullet.survive_off_screen = True
    circle_2_offset += 1


def precision_blast():
    global precision_x

    for bullet in OBJ_LIST:
        if isinstance(bullet, CircularBullet):
            bullet.rotating = False
            bullet.speed = -10 * TMR_SPEED / 1000
            bullet.set_target(player.get_x(), player.get_y())
    precision_x = player.get_x()

def precision():
    global offset, precision_x

    for i in range(2):
        if i == 0:
            x_pos = precision_x - player.circ.radius * 4
            beam_x = x_pos - 50
            x_speed = -1
        else:
            x_pos = precision_x + player.circ.radius * 4
            beam_x = x_pos + 50
            x_speed = 1
        x_pos += math.sin(offset * 0.2) * 50
        bullet = Bullet()
        bullet.set_position(x_pos, bullet.get_radius())
        bullet.y_speed = 1
        bullet.speed = 5 * TMR_SPEED / 1000

        beam = MovingBeam(Line(beam_x, 0, beam_x, screen.get_height()))
        beam.lifespan = 5000
        beam.start_delay(0)
        beam.speed = 10 * TMR_SPEED / 1000
        beam.x_speed = x_speed

    offset += 1

def on_death():
    pygame.mixer.music.stop()
    BULLET_EVENTS.clear()
    OBJ_LIST.clear()


player = Player(Circle(0, 0, 6))
main()
