import { useEffect, useRef } from 'react';

type Quality = 'HIGH' | 'MEDIUM' | 'LOW';

const vertexShader = `
attribute vec2 a_position;
varying vec2 v_uv;
void main() {
  v_uv = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;

const fragmentShader = `
precision mediump float;
varying vec2 v_uv;
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_pointer;
uniform float u_scroll;
uniform float u_quality;

float hash21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
  vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);
  return mix(mix(hash21(i), hash21(i+vec2(1.0,0.0)), f.x), mix(hash21(i+vec2(0.0,1.0)), hash21(i+vec2(1.0,1.0)), f.x), f.y);
}
float fbm(vec2 p) {
  float value = 0.0; float amplitude = 0.5;
  for (int i=0; i<4; i++) { value += amplitude * noise(p); p = p * 2.02 + 4.7; amplitude *= 0.5; }
  return value;
}
float segmentDistance(vec2 point, vec2 start, vec2 end) {
  vec2 direction = end - start;
  float amount = clamp(dot(point - start, direction) / max(dot(direction, direction), 0.0001), 0.0, 1.0);
  return distance(point, start + direction * amount);
}
float networkField(vec2 point, float scale, float drift) {
  vec2 grid = point * scale + vec2(drift, drift * 0.35);
  vec2 cell = floor(grid);
  vec2 local = fract(grid) - 0.5;
  float lines = 0.0;
  float nodes = 0.0;
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      vec2 id = cell + vec2(float(x), float(y));
      vec2 origin = vec2(hash21(id), hash21(id + 19.7)) - 0.5 + vec2(float(x), float(y));
      nodes += exp(-distance(local, origin) * 34.0);
      vec2 rightId = id + vec2(1.0, 0.0);
      vec2 right = vec2(hash21(rightId), hash21(rightId + 19.7)) - 0.5 + vec2(float(x + 1), float(y));
      vec2 downId = id + vec2(0.0, 1.0);
      vec2 down = vec2(hash21(downId), hash21(downId + 19.7)) - 0.5 + vec2(float(x), float(y + 1));
      lines += exp(-segmentDistance(local, origin, right) * 70.0);
      lines += exp(-segmentDistance(local, origin, down) * 70.0);
    }
  }
  return lines * 0.34 + nodes * 0.9;
}
float stars(vec2 point, float scale, vec2 drift) {
  vec2 grid = point * scale + drift;
  vec2 cell = floor(grid);
  vec2 local = fract(grid) - 0.5;
  float result = 0.0;
  for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) {
    vec2 id = cell + vec2(float(x), float(y));
    vec2 star = vec2(hash21(id), hash21(id + 41.2)) - 0.5 + vec2(float(x), float(y));
    float size = step(0.82, hash21(id + 8.4));
    result += exp(-distance(local, star) * 90.0) * size;
  }
  return result;
}
vec3 palette(float warm, float cool, float glow) {
  vec3 navy = vec3(0.008, 0.025, 0.105);
  vec3 blue = vec3(0.015, 0.20, 0.52);
  vec3 cyan = vec3(0.05, 0.60, 0.90);
  vec3 magenta = vec3(0.72, 0.035, 0.30);
  vec3 orange = vec3(1.0, 0.20, 0.025);
  vec3 pink = vec3(1.0, 0.30, 0.34);
  vec3 color = mix(navy, blue, cool);
  color += cyan * cool * cool * 0.55;
  color += mix(magenta, orange, warm) * glow;
  color += pink * glow * glow * 0.32;
  return color;
}
void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  vec2 pointer = u_pointer * vec2(0.18, 0.12);
  float time = u_time * 0.00022;
  vec2 p = uv + pointer;
  vec3 color = vec3(0.003, 0.006, 0.028);
  float total = 0.0;
  float layers = u_quality > 1.5 ? 13.0 : u_quality > 0.5 ? 10.0 : 7.0;
  for (int layer=0; layer<16; layer++) {
    if (float(layer) >= layers) break;
    float depth = float(layer) / layers;
    float perspective = mix(1.28, 0.58, depth);
    vec2 q = p * perspective;
    q.y += depth * 0.15 + u_scroll * (0.12 + depth * 0.20);
    q.x += sin(depth * 6.0 + time * 2.0) * 0.06;
    float flow = fbm(q * 1.25 + vec2(time * 0.5, -time * 0.35) + depth);
    q += vec2(flow - 0.5) * vec2(0.28, 0.17);
    float spine = sin(q.y * 2.0 + sin(q.x * 2.4 + time) * 1.5 + depth * 4.0) * 0.22;
    float spine2 = sin(q.y * 3.2 - q.x * 1.7 - time * 0.8 + depth) * 0.08;
    float fold = abs(q.x - spine - spine2 + 0.18 * sin(depth * 8.0 + q.y * 1.5));
    float ribbon = exp(-fold * fold * (6.0 + 7.0 * (1.0-depth)));
    float innerFold = exp(-abs(fold - 0.13) * 34.0);
    float edge = exp(-abs(fold - 0.27) * 42.0);
    float ridge = smoothstep(0.10, 0.62, ribbon) * (0.72 + 0.28 * sin(q.y * 5.0 + q.x * 3.0 + time * 2.0));
    float shade = smoothstep(0.0, 0.32, ribbon) * (0.65 + 0.35 * fbm(q * 3.0 + depth));
    float warm = smoothstep(-0.65, 0.7, sin(q.y * 1.7 + q.x * 1.2 + depth * 5.0 + time));
    float cool = smoothstep(0.1, 0.9, 1.0 - depth) * (0.35 + 0.65 * smoothstep(0.0, 0.65, abs(q.y)));
    vec3 surface = palette(warm, cool, ridge * 0.55 + innerFold * 0.48);
    surface += vec3(1.0, 0.12, 0.015) * edge * warm * 0.8;
    surface *= shade;
    float alpha = ribbon * (0.10 + (1.0-depth) * 0.12);
    color = mix(color, color + surface, alpha);
    color += surface * edge * 0.035;
    total += alpha;
  }
  float centralGlow = exp(-length(p * vec2(0.72, 1.05) + vec2(0.08, 0.03)) * 2.5);
  color += vec3(1.0, 0.08, 0.16) * centralGlow * 0.34;
  color += vec3(0.04, 0.28, 0.72) * (1.0 - smoothstep(0.0, 1.5, length(uv))) * 0.32;
  float networkBack = networkField(uv * 0.72 + vec2(u_pointer.x * 0.18, u_pointer.y * 0.12), 4.2, time * 0.22);
  float networkFront = networkField(uv * 1.18 + vec2(-u_pointer.x * 0.30, -u_pointer.y * 0.20), 6.0, -time * 0.38);
  vec3 networkLight = vec3(0.38, 0.58, 0.92) * networkBack * 0.16 + vec3(0.78, 0.88, 1.0) * networkFront * 0.25;
  color += networkLight * smoothstep(1.75, 0.35, length(uv)) * smoothstep(-0.1, 0.7, uv.x);
  float starLayer = stars(uv * vec2(0.72, 0.92), 15.0, vec2(time * 0.015, -time * 0.008));
  color += vec3(0.72, 0.84, 1.0) * starLayer * 0.34;
  vec2 portal = uv - vec2(0.22, 0.92);
  float portalGlow = exp(-length(portal * vec2(0.82, 1.55)) * 3.4);
  float portalRing = exp(-abs(length(portal * vec2(0.82, 1.55)) - 0.34) * 34.0);
  color += vec3(0.34, 0.12, 1.0) * portalGlow * 0.75;
  color += vec3(0.92, 0.70, 1.0) * portalRing * 0.82;
  for (int ring = 0; ring < 4; ring++) {
    float radius = 0.50 + float(ring) * 0.16;
    float orbit = exp(-abs(length((uv - vec2(0.42, 0.04)) * vec2(1.0, 0.58)) - radius) * 90.0);
    color += vec3(0.22, 0.32, 0.68) * orbit * 0.22;
  }
  float vignette = smoothstep(1.55, 0.25, length(uv));
  color *= 0.86 + vignette * 0.62;
  color = pow(max(color, 0.0), vec3(0.88));
  gl_FragColor = vec4(color, 1.0);
}`;

function compile(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) throw new Error('Unable to allocate WebGL shader');
  gl.shaderSource(shader, source); gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) || 'WebGL shader failed');
  return shader;
}
function createProgram(gl: WebGLRenderingContext) {
  const shaderProgram = gl.createProgram();
  if (!shaderProgram) throw new Error('Unable to allocate WebGL program');
  gl.attachShader(shaderProgram, compile(gl, gl.VERTEX_SHADER, vertexShader));
  gl.attachShader(shaderProgram, compile(gl, gl.FRAGMENT_SHADER, fragmentShader));
  gl.linkProgram(shaderProgram);
  if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(shaderProgram) || 'WebGL program failed');
  return shaderProgram;
}
function chooseQuality(): Quality {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return 'LOW';
  if (window.innerWidth < 700 || (navigator.hardwareConcurrency || 4) < 4) return 'LOW';
  if (window.innerWidth < 1100) return 'MEDIUM';
  return 'HIGH';
}

export default function NetworkScene() {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const gl = element.getContext('webgl', { alpha: true, antialias: false, powerPreference: 'low-power' });
    if (!gl) return;
    const selected = chooseQuality();
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const qualityValue = selected === 'HIGH' ? 2 : selected === 'MEDIUM' ? 1 : 0;
    const shaderProgram = createProgram(gl);
    const buffer = gl.createBuffer();
    if (!buffer) return;
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    const position = gl.getAttribLocation(shaderProgram, 'a_position');
    const uniforms = { resolution: gl.getUniformLocation(shaderProgram, 'u_resolution'), time: gl.getUniformLocation(shaderProgram, 'u_time'), pointer: gl.getUniformLocation(shaderProgram, 'u_pointer'), scroll: gl.getUniformLocation(shaderProgram, 'u_scroll'), quality: gl.getUniformLocation(shaderProgram, 'u_quality') };
    const pointer = { x: 0, y: 0, targetX: 0, targetY: 0 };
    let scroll = 0; let frame = 0; let running = true;
    const resize = () => { const ratio = Math.min(window.devicePixelRatio || 1, selected === 'HIGH' ? 1.35 : 1); element.width = Math.floor(innerWidth * ratio); element.height = Math.floor(innerHeight * ratio); element.style.width = `${innerWidth}px`; element.style.height = `${innerHeight}px`; gl.viewport(0, 0, element.width, element.height); };
    const move = (event: PointerEvent) => { pointer.targetX = event.clientX / innerWidth - 0.5; pointer.targetY = event.clientY / innerHeight - 0.5; };
    const scrollMove = () => { scroll = Math.max(-0.25, Math.min(0.25, scrollY / Math.max(1, document.body.scrollHeight) - 0.12)); };
    const draw = (time: number) => { if (!running) return; pointer.x += (pointer.targetX - pointer.x) * 0.035; pointer.y += (pointer.targetY - pointer.y) * 0.035; gl.clear(gl.COLOR_BUFFER_BIT); gl.useProgram(shaderProgram); gl.bindBuffer(gl.ARRAY_BUFFER, buffer); gl.enableVertexAttribArray(position); gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0); gl.uniform2f(uniforms.resolution, element.width, element.height); gl.uniform1f(uniforms.time, reduced ? 0 : time); gl.uniform2f(uniforms.pointer, reduced ? 0 : pointer.x, reduced ? 0 : pointer.y); gl.uniform1f(uniforms.scroll, reduced ? 0 : scroll); gl.uniform1f(uniforms.quality, qualityValue); gl.drawArrays(gl.TRIANGLES, 0, 6); if (!reduced) frame = requestAnimationFrame(draw); };
    const visibility = () => { running = !document.hidden; if (running && !reduced) frame = requestAnimationFrame(draw); };
    gl.disable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.clearColor(0.0, 0.0, 0.0, 0.0);
    resize(); scrollMove(); addEventListener('resize', resize); addEventListener('pointermove', move, { passive: true }); addEventListener('scroll', scrollMove, { passive: true }); document.addEventListener('visibilitychange', visibility); draw(0);
    return () => { cancelAnimationFrame(frame); removeEventListener('resize', resize); removeEventListener('pointermove', move); removeEventListener('scroll', scrollMove); document.removeEventListener('visibilitychange', visibility); gl.deleteBuffer(buffer); gl.deleteProgram(shaderProgram); };
  }, []);
  return <canvas ref={canvas} className="network" aria-hidden="true" style={{ pointerEvents: 'none', zIndex: 0, opacity: 0.92 }} />;
}
