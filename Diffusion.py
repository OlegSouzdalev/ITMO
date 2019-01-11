from graphics import *
import random
import math
import time

BOX_P1 = Point(100, 100)
BOX_P2 = Point(400, 400)	
RADIUS = 10

def create_coordinates(radius, frame_width, frame_height, offset_x, offset_y):
	coords = []
	
	for x in range(radius + offset_x, offset_x + frame_width - radius + 1, radius * 2):
		for y in range(radius + offset_y, offset_y + frame_height - radius + 1, radius * 2):
			coords.append((x, y))
	
	return coords

def create_mol(window, coords, color):
	global SPEED
	
	coord = coords.pop(random.randint(0, len(coords) - 1))
	pt = Point(coord[0], coord[1])
	
	circle = Circle(pt, RADIUS)
	circle.setFill(color)
	circle.draw(window)
	x = random.uniform(-1, 1)
	vect = Point( x * SPEED, math.sqrt(1 - x**2) * random.choice([1, -1]) * SPEED)
	mol = [circle, vect, color]
	return mol

def create_many_mol(num, window):
	molecules = []
	
	frame_width = int(BOX_P2.getX() - BOX_P1.getX()) // 2
	frame_height = int(BOX_P2.getY() - BOX_P1.getY())
	
	offset_y = int(BOX_P1.getY())
	offset_x_blue = int(BOX_P1.getX())
	offset_x_red = offset_x_blue + frame_width

	blue_coords = create_coordinates(RADIUS, frame_width, frame_height, offset_x_blue, offset_y)
	red_coords = create_coordinates(RADIUS, frame_width, frame_height, offset_x_red, offset_y)

	mols_per_chamber = num // 2

	for i in range(mols_per_chamber):
		molecules.append(create_mol(window, blue_coords, "blue"))
	for i in range(mols_per_chamber):
		molecules.append(create_mol(window, red_coords, "red"))
	return molecules

def coll_adjust_position(mol_1, mol_2):
	dC = Point(mol_2[0].getCenter().getX() - mol_1[0].getCenter().getX(), mol_2[0].getCenter().getY() - mol_1[0].getCenter().getY())
	dV = Point(mol_2[1].getX() - mol_1[1].getX(), mol_2[1].getY() - mol_1[1].getY())
	dot_product = dC.getX() * dV.getX() + dC.getY() * dV.getY()
	dC_squared = dC.getX() ** 2 + dC.getY() ** 2
	dV_squared = dV.getX() ** 2 + dV.getY() ** 2
	
	t = (dot_product + math.sqrt(dot_product ** 2 + dV_squared * (4 * RADIUS ** 2 - dC_squared))) / dV_squared
	
	mol_1[0].move(-t * mol_1[1].getX(), -t * mol_1[1].getY())
	mol_2[0].move(-t * mol_2[1].getX(), -t * mol_2[1].getY())
			
def adjust_position(rect, mol, coord_edge, is_wall_vertical, is_door_closed):
	# Move back to ensure we start from a point where the centre hasn't crossed the wall.
	mol[0].move(-mol[1].getX(), -mol[1].getY())
	
	# velocity_coord is the trajectory's component that is perpendicular to the wall at coord_edge.
	# Tests performed before calling adjust_position ensure that velocity_coord is oriented so as to exit the chamber.
	(circle_coord, velocity_coord) = ((mol[0].getCenter().getX(), mol[1].getX()) if is_wall_vertical
		                              else (mol[0].getCenter().getY(), mol[1].getY()))

	# Distance of circle to wall at time of impact.
	# If approaching from lower coords, this distance is subtracted from the wall's coordinate, and vice versa.
	signed_distance = -mol[0].getRadius() if velocity_coord >= 0 else mol[0].getRadius()
	# Compute time to get to point of impact.
	t = 1.0 / velocity_coord * (coord_edge - circle_coord + signed_distance) if velocity_coord > 0 else 0
	
	# If we get a point outside the chamber it's not a real point of impact.
	# A spurious point of impact can be found when the circle more deeply impacts another wall (in a corner) 
	# or velocity_coord is much smaller than velocity's other coordinate (i.e. velocity close to vertical or close to horizontal).
	# Then, we trust that handling the other collision will do a better job of finding the impact point.
	if check_excursion(rect, mol, coord_edge, is_wall_vertical, is_door_closed, t):
		# undo move
		mol[0].move(mol[1].getX(), mol[1].getY())
		return
	
	# Move to point of impact.
	mol[0].move(t * mol[1].getX(), t * mol[1].getY())

	assert not excursion(rect, mol, is_door_closed)

def check_excursion(rect, mol, wall_coord, is_wall_vertical, is_door_closed, time_to_collision):
	# Assumptions: this function is exclusively called from adjust_position; 
	#              the circle's center hasn't crossed wall_coord
	computed_impact_point = Point(mol[0].getCenter().getX() + mol[1].getX() * time_to_collision,
								 mol[0].getCenter().getY() + mol[1].getY() * time_to_collision)
	
	# If we're adjusting for a vertical wall we check for excursion through a horizontal wall, and vice versa.
	return (is_wall_vertical and ((computed_impact_point.getY() <= rect.getP1().getY() or computed_impact_point.getY() >= rect.getP2().getY())
	                               or (is_door_closed and ((mol[2] == 'red' and computed_impact_point.getX() < rect.getCenter().getX())
								                            or (mol[2] == 'blue' and computed_impact_point.getX() > rect.getCenter().getX()))))) \
		or (not is_wall_vertical and (computed_impact_point.getX() <= rect.getP1().getX() or computed_impact_point.getX() >= rect.getP2().getX()))
		
def excursion(chamber, molecule, is_door_closed):
	molX = molecule[0].getCenter().getX()
	molY = molecule[0].getCenter().getY()
	
	return molX < chamber.getP1().getX() or molX > chamber.getP2().getX() or molY < chamber.getP1().getY() or molY > chamber.getP2().getY() or \
		(is_door_closed and ((molecule[2] == "blue" and molX > molecule[0].getCenter().getX()) or (molecule[2] == "red" and molX < molecule[0].getCenter().getX())))
		
def zone_color(zones, molecules, update_count):
	for zone in zones:
		for mol in molecules:
			if zone[0].getP1().getX() <= mol[0].getCenter().getX() < zone[0].getP2().getX() and mol[2] == "blue":
				zone[1] += 1
			elif zone[0].getP1().getX() <= mol[0].getCenter().getX() < zone[0].getP2().getX() and mol[2] == "red":
				zone[2] += 1
				
	if update_count % 5 != 0:
		return
	
	for zone in zones:	
		if zone[1] + zone[2] == 0:
			zone[0].setFill(color_rgb(255, 255, 255))		
			continue
			
		majority_margin  = max(zone[1], zone[2]) / (zone[1] + zone[2]) - 0.5
		dimmed_color_level = 255 - int(majority_margin * 510)
		if zone[1] > zone[2]:
			zone[0].setFill(color_rgb(dimmed_color_level, 0, 255))
		else:
			zone[0].setFill(color_rgb(255, 0, dimmed_color_level))
		
		zone[1] = 0
		zone[2] = 0
		
def inside_button(button, point):
	dx = abs(point.getX() - button.getCenter().getX())
	dy = abs(point.getY() - button.getCenter().getY())
	
	distance = math.sqrt(dx ** 2 + dy ** 2)
	
	return distance <= button.getRadius()

		
def start():
	global SPEED
	
	WINWIDTH = 500  # give a name to the window width 
	WINHEIGHT = 500 #    and height
	win = GraphWin('Face', WINWIDTH, WINHEIGHT) # give title and dimensions 
	win.setCoords(0, 0, WINWIDTH, WINHEIGHT) # make right side up coordinates! 
	
	rect = Rectangle(BOX_P1, BOX_P2) 
	rect.draw(win)
	
	color_rect = Rectangle(Point(100, 20), Point(400, 80))
	color_rect.setOutline("white")
	color_rect.draw(win)
	
	zone_number = 6
	zone_width = (rect.getP2().getX() - rect.getP1().getX()) / zone_number
	zone_list = []
	
	for i in range(zone_number):
		zone = Rectangle(Point(100 + (i * zone_width), 20), Point(100 + ((i + 1) * zone_width), 80))
		zone.setOutline("white")
		zone_list.append([zone,0,0])
		zone.draw(win)
		
	x_door = 250
	door = Line(Point(x_door, 400), Point(x_door, 100))
	door.draw(win)
	
	button = Circle(Point(455, 455), 40)
	button.setFill("blue")
	button.draw(win)
	start = Text(Point(455,455), 'START')
	start.setTextColor("white")
	start.draw(win)

	Text(Point(WINWIDTH/1.5, 450),'Temperature (up to 450 K):').draw(win) # label for the Entry
	entry1 = Entry(Point(WINWIDTH/1.5, 430),10)
	entry1.draw(win)
	
	Text(Point(WINWIDTH/3, 450),'Number of Molecules:').draw(win) # label for the Entry
	entry2 = Entry(Point(WINWIDTH/3, 430),10)
	entry2.draw(win)
	while (win.getKey() != 'Return'):
		pass
	
	SPEED = RADIUS * int(entry1.getText()) // 500
	
	molecules = create_many_mol(int(entry2.getText()), win)
	update_count = -1
	x = 0
	while True:
	
		# Perform move and handle collisions with walls.
		for mol in molecules:
			mol[0].move(mol[1].getX(), mol[1].getY())	

			if mol[1].getX() > 0 and abs(mol[0].getCenter().getX() - rect.getP2().getX()) <= mol[0].getRadius(): #right side
				adjust_position(rect, mol, rect.getP2().getX(), True, x == 0)
				mol[1] = Point(-mol[1].getX(), mol[1].getY())
				
			elif mol[1].getX() < 0 and abs(mol[0].getCenter().getX() - rect.getP1().getX()) <= mol[0].getRadius(): #left side
				adjust_position(rect, mol, rect.getP1().getX(), True, x == 0)
				mol[1] = Point(-mol[1].getX(), mol[1].getY())

			elif x < 1 and abs(mol[0].getCenter().getX() - rect.getCenter().getX()) <= mol[0].getRadius(): #door
					adjust_position(rect, mol, rect.getCenter().getX(), True, True)
					mol[1] = Point(-mol[1].getX(), mol[1].getY())
				
			if mol[1].getY() > 0 and abs(mol[0].getCenter().getY() - rect.getP2().getY()) <= mol[0].getRadius(): #upper side
				adjust_position(rect, mol, rect.getP2().getY(), False, x == 0)
				mol[1] = Point(mol[1].getX(), -mol[1].getY())
				
			elif mol[1].getY() < 0 and abs(mol[0].getCenter().getY() - rect.getP1().getX()) <= mol[0].getRadius(): #lower side
				adjust_position(rect, mol, rect.getP1().getY(), False, x == 0)
				mol[1] = Point(mol[1].getX(), -mol[1].getY())
			
		
		# Handle molecule-to-molecule collisions.
		for i in range(len(molecules)):
			for j in range(i + 1, len(molecules)):
				if abs(molecules[j][0].getCenter().getX() - molecules[i][0].getCenter().getX()) <= 2 * RADIUS and (molecules[j][0].getCenter().getY() - molecules[i][0].getCenter().getY()) <= 2 * RADIUS:
					if (molecules[j][0].getCenter().getX() - molecules[i][0].getCenter().getX())**2 + (molecules[j][0].getCenter().getY() - molecules[i][0].getCenter().getY())**2 <= 4 * RADIUS ** 2:
						###coll_adjust_position(molecules[i], molecules[j])
						molecules[i][1], molecules[j][1] = molecules[j][1], molecules[i][1]
		
		update_count += 1
		zone_color(zone_list, molecules, update_count)
		
		clicked = win.checkMouse()
		if clicked and inside_button(button, clicked):
			door.undraw()
			x += 1
			
		time.sleep(0.05)
		
start()
