export const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const fragmentShader = `
uniform float uTime;
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uIntensity;
uniform float uSpeed;
uniform int uQuality;

varying vec2 vUv;

#define PI 3.14159265359

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
    mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
    f.y
  );
}

float fbm(vec2 p, int octaves) {
  float value = 0.0;
  float amplitude = 0.5;
  float frequency = 1.0;
  for (int i = 0; i < 6; i++) {
    if (i >= octaves) break;
    value += amplitude * noise(p * frequency);
    frequency *= 2.02;
    amplitude *= 0.5;
  }
  return value;
}

vec3 auroraColor(float intensity, float hue) {
  vec3 base = vec3(0.005, 0.01, 0.025);
  vec3 cyan = vec3(0.0, 0.8, 0.9);
  vec3 emerald = vec3(0.0, 0.9, 0.6);
  vec3 violet = vec3(0.6, 0.2, 0.8);
  vec3 rose = vec3(1.0, 0.3, 0.5);
  
  float h = hue * 6.28;
  vec3 color = mix(cyan, emerald, sin(h * 0.5) * 0.5 + 0.5);
  color = mix(color, violet, sin(h * 0.3 + 1.0) * 0.5 + 0.5);
  color = mix(color, rose, sin(h * 0.7 + 2.0) * 0.5 + 0.5);
  
  return base + color * intensity * 0.8;
}

vec3 renderAurora(vec2 uv, float time, float intensity, float speed) {
  vec3 color = vec3(0.0);
  float layers = float(uQuality > 1 ? 5 : uQuality > 0 ? 3 : 2);
  
  for (int i = 0; i < 5; i++) {
    if (float(i) >= layers) break;
    
    float layerDepth = float(i) / max(layers - 1.0, 1.0);
    float layerSpeed = speed * (0.3 + layerDepth * 0.7);
    float layerScale = 1.5 + layerDepth * 2.5;
    
    vec2 p = uv * layerScale;
    p.y += time * layerSpeed * 0.15;
    p.x += sin(p.y * 2.0 + time * layerSpeed * 0.5 + float(i) * 1.3) * 0.3;
    
    float wave = sin(p.y * 3.0 + time * layerSpeed * 0.8 + float(i) * 2.1);
    wave += sin(p.x * 1.5 - time * layerSpeed * 0.4 + float(i) * 1.7) * 0.5;
    wave += fbm(p * 1.5 + vec2(time * layerSpeed * 0.2, 0.0), 3) * 0.5;
    
    float band = smoothstep(0.3, 0.6, wave) * smoothstep(1.0, 0.7, wave);
    band = pow(band, 1.5 - layerDepth * 0.5);
    
    float hue = (time * 0.02 + layerDepth * 0.3 + float(i) * 0.15);
    vec3 layerColor = auroraColor(intensity * (0.5 + layerDepth * 0.5), hue);
    
    color += layerColor * band * (1.0 - layerDepth * 0.3);
  }
  
  return color;
}

vec3 renderStars(vec2 uv, float time) {
  vec3 color = vec3(0.0);
  vec2 grid = uv * 50.0;
  vec2 cell = floor(grid);
  vec2 local = fract(grid) - 0.5;
  
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      vec2 id = cell + vec2(float(x), float(y));
      float starHash = hash(id);
      if (starHash > 0.96) {
        vec2 starPos = vec2(hash(id + 1.0), hash(id + 2.0)) - 0.5 + vec2(float(x), float(y));
        float dist = distance(local, starPos);
        float size = hash(id + 3.0) * 0.01 + 0.005;
        float twinkle = sin(time * 2.0 + starHash * 50.0) * 0.5 + 0.5;
        float brightness = smoothstep(size, 0.0, dist) * twinkle * 2.0;
        color += vec3(1.0, 0.95, 0.9) * brightness;
      }
    }
  }
  
  return color;
}

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution.xy) / min(uResolution.x, uResolution.y);
  float time = uTime * uSpeed;
  
  vec2 mouseInfluence = (uMouse - 0.5) * 0.3;
  uv += mouseInfluence * 0.2;
  
  vec3 bgColor = vec3(0.005, 0.01, 0.025);
  vec3 aurora = renderAurora(uv, time, uIntensity, uSpeed);
  vec3 stars = renderStars(uv, time);
  
  float vignette = 1.0 - smoothstep(0.5, 1.5, length(uv));
  bgColor *= 0.5 + vignette * 0.5;
  
  vec3 finalColor = bgColor + aurora + stars * 0.3;
  finalColor = pow(max(finalColor, 0.0), vec3(0.9));
  
  gl_FragColor = vec4(finalColor, 1.0);
}
`;