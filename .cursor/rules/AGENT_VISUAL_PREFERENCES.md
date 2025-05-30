# Agent Visual Preferences for 3D Physics Simulations

This document outlines preferred visual styles, parameters, and techniques to guide an AI assistant (like Gemini in Cursor) in creating or modifying 3D physics simulations to match the aesthetic established in the "Realistic 3D Circuit" project.

**Core Objective:** Achieve a grounded, "hyperrealistic" look inspired by physical objects, emphasizing PBR materials, detailed geometry, and thoughtful lighting.

## 1. Renderer Configuration (`sceneConfig.js`)

When setting up the `THREE.WebGLRenderer`:

-   **Antialiasing:** `antialias: true` (Default)
-   **Shadows:**
    -   `renderer.shadowMap.enabled = true`
    -   `renderer.shadowMap.type = THREE.PCFSoftShadowMap`
-   **Color & Tone:**
    -   `renderer.toneMapping = THREE.ACESFilmicToneMapping`
    -   `renderer.outputColorSpace = THREE.SRGBColorSpace`

## 2. Lighting Strategy (`sceneConfig.js`)

Prioritize a balanced, multi-light setup:

-   **Ambient Lighting:**
    -   `THREE.HemisphereLight`: Primary ambient. Example: `new THREE.HemisphereLight(0xffffff, 0x444444, 0.8)`
    -   `THREE.AmbientLight`: Secondary, low intensity. Example: `new THREE.AmbientLight(0xffffff, 0.2)`
-   **Directional Lighting (Key & Fill):**
    -   **Key Light:** One main `THREE.DirectionalLight` for primary highlights and shadows.
        -   `castShadow = true`
        -   `shadow.mapSize.width = 1024` (or `2048` for higher quality)
        -   `shadow.mapSize.height = 1024` (or `2048`)
        -   Optimize `shadow.camera` frustum if possible.
        -   Example intensity: `0.7` to `0.8`.
    -   **Fill Light:** At least one other `THREE.DirectionalLight` from a different angle, lower intensity (e.g., `0.3` to `0.4`), `castShadow = false` usually.
-   **Component-Specific Lights:** For elements like bulbs that emit light, add a `THREE.PointLight` parented to the emissive part.
    -   Example: `new THREE.PointLight(0xffdd66, /*intensity controlled by state*/, 5)`
    -   `castShadow = true` can be used if impactful and performance allows.

## 3. Material Definitions (`componentFactory.js` - PBR Focus)

Always prefer `THREE.MeshStandardMaterial`.

-   **General Principles:**
    -   Refer to real-world objects or provided images for color, metalness, roughness.
    -   `metalness`: Strictly `1.0` for pure metals, `0.0` for pure non-metals. Slight deviations (e.g., `0.05` for some plastics) are acceptable if they enhance appearance.
    -   `roughness`: This is a key parameter for realism. Avoid pure `0.0` (perfect mirror) or pure `1.0` (perfectly Lambertian) unless specifically matching a material like that. Most objects have values between `0.1` and `0.8`.

-   **Specific Material Starting Points (Examples from Circuit Project):**
    -   **General Metal (Silver/Steel):** `{ color: 0xb0b0b0, metalness: 1.0, roughness: 0.25 - 0.4 }`
    -   **Copper/Brass:** `{ color: 0xb87333 /* or similar */, metalness: 1.0 /* or ~0.8 for brass */, roughness: 0.3 - 0.4 }`
    -   **Darkened/Aged Metal:** `{ color: 0x505050, metalness: 1.0, roughness: 0.35 - 0.5 }`
    -   **General Plastic (Matte to Semi-Gloss):** `{ color: /* specific */, metalness: 0.05, roughness: 0.4 - 0.7 }`
        -   *Bakelite (Dark Brown):* `{ color: 0x4A3B31, metalness: 0.05, roughness: 0.45 }`
    -   **Glass (Clear/Tinted):** `{ color: /* e.g., 0xffffff or 0xE8D5A2 for vintage */, metalness: 0.0, roughness: 0.05 - 0.15, transparent: true, opacity: 0.2 - 0.4, side: THREE.DoubleSide /* if thin */ }`
    -   **Ceramic (Matte):** `{ color: /* e.g., 0xD2B48C for resistor */, metalness: 0.0, roughness: 0.6 - 0.8 }`
    -   **Emissive Parts (Bulb Filament):** `{ color: 0xffcc33, emissive: /* state-controlled hex */, emissiveIntensity: /* state-controlled, e.g., 1.0-2.0 */, metalness: 0.2, roughness: 0.5 }`

## 4. Geometric Detailing (`componentFactory.js`)

Strive for detail that matches real-world counterparts or provided references.

-   **Adequate Segmentation:** Use sufficient segments for curved surfaces to appear smooth (e.g., `32-64` for cylinders/lathes, `16-32` for spheres).
-   **Compound Objects:** Build complex components from multiple, distinct sub-meshes rather than trying to make one monolithic geometry.
-   **Utilize Advanced Geometries:**
    -   `THREE.LatheGeometry`: Preferred for radially symmetric shapes with custom profiles (e.g., bulb envelopes, bulbous resistor bodies).
    -   `THREE.TubeGeometry` (with `CatmullRomCurve3`): Preferred for complex, smooth paths like filaments or wires that aren't simple cylinders.
-   **Subtle Additions:** Small details like ferrules, distinct terminals, base plates, or simulated threads significantly enhance realism.

## 5. Color Palette & Texturing

-   **Color:** Base colors on physical references. Avoid overly saturated or neon colors unless specifically requested. For non-emissive dark parts, prefer very dark grays over pure `0x000000`.
-   **Texturing (If Applicable/Requested):** If actual image textures are to be used (user provides assets):
    -   Use `THREE.TextureLoader`.
    -   Apply to `material.map` (albedo/color), `material.normalMap`, `material.roughnessMap`, `material.metalnessMap` as appropriate.
    -   Set `texture.wrapS`, `texture.wrapT` (e.g., `THREE.RepeatWrapping`) and `texture.repeat` if tiling is needed.

## 6. Animated Elements (e.g., Electron Flow)

-   **Particle Appearance:** Small spheres (`THREE.SphereGeometry`) with an emissive material.
    -   Example: `{ color: 0x00ffff, emissive: 0x00ffff, emissiveIntensity: 2, metalness: 0.1, roughness: 0.4 }`
    -   Particle size: `0.03` to `0.04` (relative to scene scale).
-   **Path Following:** Particles should follow `THREE.CatmullRomCurve3` paths for smooth trajectories.
-   **Visual Offset:** For clarity, paths for illustrative particles (like electrons) can be slightly offset (e.g., `+0.04` in Y) from the surface of the wires/components they represent, while still anchoring at connection points.

## 7. Iterative Refinement

-   Always present changes for user review.
-   Be prepared to iterate on material properties, lighting intensities, and geometric details based on feedback (e.g., "make it shinier," "change this color," "add more detail here").
-   If the user provides a visual reference (image), prioritize matching that reference closely. 