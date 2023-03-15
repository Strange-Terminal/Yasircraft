from ursina import *
import keyboard,math,random
from perlin_noise import*
from ursina.prefabs.first_person_controller import FirstPersonController as FPC

app = Ursina(development_mode=False, show_ursina_splash_screen=True)
play=True
Chunks=[]

shader=Shader(language=Shader.GLSL, name='lit_with_shadows_shader', vertex = '''#version 150
uniform struct {
  vec4 position;
  vec3 color;
  vec3 attenuation;
  vec3 spotDirection;
  float spotCosCutoff;
  float spotExponent;
  sampler2DShadow shadowMap;
  mat4 shadowViewMatrix;
} p3d_LightSource[1];

const float M_PI = 3.141592653589793;


uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

in vec4 vertex;
in vec3 normal;
in vec4 p3d_Color;

in vec2 p3d_MultiTexCoord0;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
out vec2 texcoords;


out vec3 vpos;
out vec3 norm;
out vec4 shad[1];
out vec4 vertex_color;

void main() {
  gl_Position = p3d_ModelViewProjectionMatrix * vertex;
  vpos = vec3(p3d_ModelViewMatrix * vertex);
  norm = normalize(p3d_NormalMatrix * normal);
  shad[0] = p3d_LightSource[0].shadowViewMatrix * vec4(vpos, 1);
  texcoords = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
  vertex_color = p3d_Color;
}

''',
fragment='''
#version 150
uniform struct {
  vec4 position;
  vec3 color;
  vec3 attenuation;
  vec3 spotDirection;
  float spotCosCutoff;
  float spotExponent;
  sampler2DShadow shadowMap;
  mat4 shadowViewMatrix;
} p3d_LightSource[1];

const float M_PI = 3.141592653589793;


uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;

uniform struct {
  vec4 ambient;
} p3d_LightModel;

uniform struct {
  vec4 ambient;
  vec4 diffuse;
  vec3 specular;
  float roughness;
} p3d_Material;

in vec3 vpos;
in vec3 norm;
in vec4 shad[1];
in vec4 vertex_color;

out vec4 p3d_FragColor;
uniform vec4 shadow_color;

void main() {
  p3d_FragColor = texture(p3d_Texture0, texcoords) * p3d_ColorScale * vertex_color;

  // float alpha = p3d_Material.roughness * p3d_Material.roughness;
  vec3 N = norm;

  for (int i = 0; i < p3d_LightSource.length(); ++i) {
    vec3 diff = p3d_LightSource[i].position.xyz - vpos * p3d_LightSource[i].position.w;
    vec3 L = normalize(diff);
    vec3 V = normalize(-vpos);
    vec3 H = normalize(L + V);

    float NdotL = clamp(dot(N, L), 0.001, 1.0);
    // float NdotV = clamp(abs(dot(N, V)), 0.001, 1.0);
    // float NdotH = clamp(dot(N, H), 0.0, 1.0);
    // float VdotH = clamp(dot(V, H), 0.0, 1.0);

    // Specular term
    // float reflectance = max(max(p3d_Material.specular.r, p3d_Material.specular.g), p3d_Material.specular.b);
    // float reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    // vec3 F = p3d_Material.specular + (vec3(reflectance90) - reflectance) * pow(clamp(1.0 - VdotH, 0.0, 1.0), 5.0);

    // Geometric occlusion term
    // float alpha2 = alpha * alpha;
    // float attenuationL = 2.0 * NdotL / (NdotL + sqrt(alpha2 + (1.0 - alpha2) * (NdotL * NdotL)));
    // float attenuationV = 2.0 * NdotV / (NdotV + sqrt(alpha2 + (1.0 - alpha2) * (NdotV * NdotV)));
    // float G = attenuationL * attenuationV;

    // Microfacet distribution term
    // float f = (NdotH * alpha2 - NdotH) * NdotH + 1.0;
    // float D = alpha2 / (M_PI * f * f);

    // Lambert, energy conserving
    // vec3 diffuseContrib = (1.0 - F) * p3d_Material.diffuse.rgb / M_PI;
    vec3 diffuseContrib = p3d_Material.diffuse.rgb / M_PI;

    // Cook-Torrance
    //vec3 specContrib = F * G * D / (4.0 * NdotL * NdotV);
    // vec3 specContrib = vec3(0.);

    // Obtain final intensity as reflectance (BRDF) scaled by the energy of the light (cosine law)
    // vec3 color = NdotL * p3d_LightSource[i].color * (diffuseContrib + specContrib);
    vec3 color =  NdotL * p3d_LightSource[i].color * diffuseContrib;
    const float bias = 0.001;

    vec4 shadowcoord = shad[i];
    shadowcoord.z += bias;

    vec3 converted_shadow_color = (vec3(1.,1.,1.) - shadow_color.rgb) * shadow_color.a;
    p3d_FragColor.rgb *= p3d_LightSource[i].color.rgb;
    p3d_FragColor.rgb += textureProj(p3d_LightSource[i].shadowMap, shadowcoord) * converted_shadow_color;
    p3d_FragColor.rgb += color - converted_shadow_color;
  }
}

''',
default_input = {
    'texture_scale': Vec2(1,1),
    'texture_offset': Vec2(0,0),
    'shadow_color' : Vec4(0, .5, 1, .25),
    }
)

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
					y =math.floor(y * 10.5)
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






player = FPC(positoin=(random.randint(0,WORLD_SIZE),0,random.randint(0,WORLD_SIZE)),speed=10,shader=shader.compile())
sky = Sky()

app.run()
