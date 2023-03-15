#ömer bu kod benim tamamı
#Yasir 6/B Derbent İmam Hatib Ortaokulu

from ursina import *
import keyboard,math,random
from perlin_noise import*
from ursina.prefabs.first_person_controller import FirstPersonController as FPC

app = Ursina(development_mode=False, show_ursina_splash_screen=True)
play=True
Chunks=[]

CHUNK_SIZE = 5  # Chunk boyutu
WORLD_SIZE = 12800  # Dünya boyutu
NUM_CHUNKS = WORLD_SIZE // CHUNK_SIZE  # Toplam chunk sayısı
ACTIVE_CHUNK_RADIUS = 1  # Aktif chunk yarıçapı

noise = PerlinNoise (octaves=3,seed=2134)

window.fps_counter.enabled = True
window.exit_button.visible = True


class Block(Button):
	def __init__(self, position = (0,0,0)):
		super().__init__(
			parent = scene,
			position = position,
			model = 'block',
			origin_y = 0.5,
			texture ="grass_block.png",
			color = color.color(0,0,random.uniform(0.9,1)),
			scale = 0.5)

	def input(self,key):
		if self.hovered:
			if key == 'left mouse down':Block(position = self.position + mouse.normal)
			if key == 'right mouse down':destroy(self)


class Chunk:
	
	def __init__(self, position):
		self.player_chunk_x = int(player.position[0]) // CHUNK_SIZE
		self.player_chunk_z = int(player.position[2]) // CHUNK_SIZE
		self.position = position
		self.blocks = []
		self.entity = Entity(parent=scene, position=self.position)
		for x in range(self.position[0], self.position[0] + CHUNK_SIZE):
			for z in range(self.position[2], self.position[2] + CHUNK_SIZE):
					y=noise([x * .02,z * .02])
					y =math.floor(y * 7.5)
					self.blocks.append(Block((x,y,z)))


                    
	
	def destroy(self):
		self.entity.disable()
		for block in self.blocks:
			block.disable()
	



chunks = [[None for z in range(NUM_CHUNKS)] for x in range(NUM_CHUNKS)]

def update():
	get_active_chunks()
	if keyboard.is_pressed("r"):
		player.set_position((0,0,0))

def get_active_chunks():
	active_chunks = []
	player_chunk_x = int(player.position[0]) // CHUNK_SIZE
	player_chunk_z = int(player.position[2]) // CHUNK_SIZE
	for x in range(player_chunk_x - ACTIVE_CHUNK_RADIUS, player_chunk_x + ACTIVE_CHUNK_RADIUS + 1):
		for z in range(player_chunk_z - ACTIVE_CHUNK_RADIUS, player_chunk_z + ACTIVE_CHUNK_RADIUS + 1):
			
				chunk = chunks[x][z]
				if chunk is None:
					chunk = Chunk(position=(x * CHUNK_SIZE, 0, z * CHUNK_SIZE))
					chunks[x][z] = chunk
				active_chunks.append(chunk)
	
	return active_chunks






player = FPC(positoin=(random.randint(0,WORLD_SIZE),0,random.randint(0,WORLD_SIZE)),speed=10)
sky = Sky()

app.run()
