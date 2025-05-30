# Visual Style Guide: Achieving a Realistic Look

This guide outlines the visual principles and techniques employed in the 3D Circuit Simulator to achieve a "hyperrealistic" aesthetic. These can serve as a reference when adapting the project's look or for styling new physics visualizations.

## 1. Overall Philosophy: Grounded Realism

-   **Inspiration from Physical Objects:** The primary goal is to make components look like their real-world counterparts. This often involves looking at reference images (e.g., Duracell battery, Edison bulb, common electronic parts).
-   **Subtlety over Exaggeration:** Realism often comes from subtle details in lighting, material response, and geometry rather than overly dramatic effects.
-   **Cohesion:** While individual components are detailed, they should look like they belong in the same scene, under the same lighting conditions.

## 2. Lighting Strategy (`sceneConfig.js`)

Good lighting is crucial for realism. The strategy involves a combination of light types:

-   **`THREE.HemisphereLight`:** Provides soft, natural ambient illumination by simulating light from the sky and bounced light from the ground. This lifts overall brightness and prevents overly dark, unlit areas.
    -   *Example:* `new THREE.HemisphereLight(0xffffff, 0x444444, 0.8);` (White sky, dark gray ground, moderate intensity).
-   **`THREE.AmbientLight`:** A subtle, omnidirectional light that ensures even base illumination, further preventing pitch-black shadows. Used at a low intensity in conjunction with HemisphereLight.
    -   *Example:* `new THREE.AmbientLight(0xffffff, 0.2);`
-   **`THREE.DirectionalLight`:** Simulates strong, parallel light sources like the sun or focused studio lights. Key for creating highlights and casting shadows.
    -   **Primary Key Light:** One strong directional light to define the main highlights and cast prominent shadows (`directionalLight1`).
        -   `castShadow = true` is essential.
        -   Shadow map size (`shadow.mapSize`) affects shadow quality (e.g., `1024x1024` or `2048x2048`).
        -   Adjusting `shadow.camera.near`, `far`, `left`, `right`, `top`, `bottom` helps optimize shadow rendering for the scene extent.
    -   **Fill/Rim Light:** Secondary directional lights (`directionalLight2`) with lower intensity can be used to fill in shadows softly or create rim highlights, adding depth.
-   **`THREE.PointLight` (Component-Specific):** Used for the bulb's illumination. Point lights emit light in all directions from a single point.
    -   `castShadow = true` can be enabled if the light source is strong enough and central to an effect.
    -   `intensity` and `distance` are key parameters.

## 3. Material Definitions (PBR - `componentFactory.js`)

The project heavily relies on `THREE.MeshStandardMaterial` for Physically Based Rendering (PBR), which aims to simulate how light interacts with materials in a physically plausible way.

-   **Key PBR Properties:**
    -   `color`: The base albedo color of the material.
    -   `metalness`: (0.0 for non-metals, 1.0 for metals). Intermediate values are rare for pure materials but can be used for corroded or coated metals.
    -   `roughness`: (0.0 for perfectly smooth/mirror-like, 1.0 for completely diffuse/matte). This is one of the most impactful properties for realism. Most real-world surfaces have some roughness.
    -   `emissive`: Color of light emitted by the material (e.g., bulb filament).
    -   `emissiveIntensity`: Multiplier for the emissive color.
    -   `transparent`: Boolean, set to `true` for materials like glass.
    -   `opacity`: (0.0 for fully transparent, 1.0 for fully opaque). Used when `transparent` is `true`.
    -   `side`: `THREE.FrontSide` (default), `THREE.BackSide`, or `THREE.DoubleSide`. `DoubleSide` is useful for thin objects like unclosed glass envelopes or if backfaces need to be seen.

-   **Examples of Material Setups:**
    -   **Metals (e.g., `batteryTerminalMaterial`, `copperMaterial`):** `metalness: 1.0`. `roughness` is varied to show shininess (lower roughness) or a more matte/brushed look (higher roughness).
    -   **Plastics (e.g., `bakeliteSwitchMaterial`, `redPlasticMaterial`):** `metalness: 0.0` or very low (e.g., `0.05`). `roughness` defines the sheen (e.g., `0.4` for semi-gloss, `0.7` for more matte).
    -   **Glass (e.g., `vintageGlassMaterial`):** `transparent: true`, low `roughness` (e.g., `0.05-0.1`), `opacity` adjusted for desired clarity (e.g., `0.25-0.35`). `color` can tint the glass.
    -   **Ceramics (e.g., `resistorCeramicMaterial`):** `metalness: 0.0`, higher `roughness` (e.g., `0.6-0.8`) for a matte, diffuse appearance.

## 4. Color Palette

-   **Reference Real Objects:** Colors are chosen to mimic the typical appearance of the components being modeled (e.g., beige for resistors, black/copper for Duracell, brass for vintage bulb bases).
-   **Avoid Pure Black/White (for non-emissive parts):** Pure black (`0x000000`) can look flat and absorb too much light. Very dark grays (e.g., `0x121212`) are often better. Pure white (`0xffffff`) can sometimes blow out highlights unless the material is very rough.
-   **Subtle Variations:** For complex objects, using slightly different shades or materials for sub-parts adds realism (e.g., battery terminals vs. body).

## 5. Geometric Detail (`componentFactory.js`)

While materials and lighting are key, geometric detail grounds the realism:

-   **Adequate Segmentation:** Cylinders, spheres, and lathes should have enough segments to appear smooth (e.g., `32` or `64` segments for cylinders/lathes, `16` or `32` for spheres, depending on size and proximity to camera).
-   **Bevels/Chamfers (Conceptual):** Though not heavily implemented with complex geometry in this project due to procedural constraints, the idea of softening hard edges makes objects look less CG. Simple additions like thin discs or adjusted profiles in `LatheGeometry` can simulate this.
-   **Distinct Sub-Parts:** Building components from multiple, clearly defined sub-meshes (e.g., battery body, terminals, label; switch base, contacts, lever, handle, ferrule) enhances detail.
-   **Specific Shapes:** Using `LatheGeometry` (resistor body, bulb envelope) or `TubeGeometry` (complex bulb filament) allows for more organic and specific shapes than basic primitives alone.

## 6. Renderer Settings (`sceneConfig.js`)

-   `renderer.shadowMap.enabled = true;`
-   `renderer.shadowMap.type = THREE.PCFSoftShadowMap;` (Softer, more realistic shadow edges).
-   `renderer.toneMapping = THREE.ACESFilmicToneMapping;` (Helps handle high dynamic range, compresses highlights and shadows for a more filmic and balanced look, preventing blown-out whites and crushed blacks).
-   `renderer.outputColorSpace = THREE.SRGBColorSpace;` (Ensures colors are displayed correctly, matching how they were defined).
-   `antialias: true` (In `WebGLRenderer` constructor for smoother edges).

## 7. Tips for Applying to New Visualizations

-   **Start with Lighting:** A good neutral lighting setup (like the one in `sceneConfig.js`) is a great starting point.
-   **Iterate on Materials:** For each new physical entity, create a `MeshStandardMaterial`. Find reference images of what you want it to look like. Adjust `color`, `metalness`, and `roughness` first. Then tweak other properties if needed.
-   **Don't Neglect Geometry:** Even simple shapes look better with adequate smoothness and considered proportions.
-   **Use PBR Thinking:** Think about how light would interact with the surface in reality. Is it a painted surface, raw metal, dusty, polished, wet?
-   **Subtlety is Key:** Often, small adjustments to roughness or slight color variations make a bigger impact on realism than drastic changes. 