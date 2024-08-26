import pygame
import neat
import time
import os
import random

# Set window dimensions
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Bird generations
GEN = 0

# Scale and store images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# Fonts
pygame.font.init()
STAT_FOUNT = pygame.font.SysFont("comicsans", 50)


class Bird:
    # Constants
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    # Initialization of bird
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    # Jump action of bird
    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    # Movement of bird
    def move(self):
        self.tick_count += 1

        # Create arc motion for bird flight
        # Define displacement variable, velocity * time(seconds) + 1.5 * time(seconds)^2
        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        # Set terminal velocity
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        # Add displacement to current y position
        self.y = self.y + d

        # Set tilt actions of bird
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
        
    # Draw game visuals
    def draw(self, win):
        self.img_count += 1

        # Check what image to show based on current img_count
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # When bird is tilted downwards, show second image(wings not flapping)
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Rotate bird image around center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    # Collision checking
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    # Initialization of Pipe
    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    # Randomize pipe heights
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # Move pipes
    def move(self):
        self.x -= self.VEL

    # Draw pipes
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Pixel collision checking with bird and pipe using masks
    def collide(self, bird):
        # Define masks
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Define offset, how far away the two top lefthand corners are from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Check if bird collides with top or bottom pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    # Initialization of base
    def __init__(self, y):
        self.y = y
        # Create two copies of base image next to each other
        self.x1 = 0
        self.x2 = self.WIDTH

    # Base movement
    def move(self):
        # Move images with velocity
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # Check if image is completely off the screen, if it is cycle it back
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # Draw base
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

# Draw window for game
def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

        text = STAT_FOUNT.render("Score: " + str(score), 1, (255, 255, 255))
        win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    pygame.display.update()

# Main loop
def main(genomes, config):
    nets = []
    ge = []
    birds = []
    
    # Setting up neural network for genome
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(700)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True

    # Running game
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        # If the length of birds > 0 and the length of pipes > 1, get the first bird
        # If we have passed the pipe, change the pipe to be the second pipe in the list
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        # Move birds
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                # If bird collides with pipe, decrease fitness score and remove bird
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        # If the bird makes it through the pipe, add 1 to score and add 5 to fitness
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        # If bird hits the ground, remove bird
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
                
        base.move()
        draw_window(win, birds, pipes, base, score)

# Running neat AI
def run(config_path):
    # Set path for configuration file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Define population
    p = neat.Population(config)

    # Add stats reporter
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Calls main function 50 times and passes it all genomes and config file
    winner = p.run(main, 50)

# Get path to configuration file
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)

